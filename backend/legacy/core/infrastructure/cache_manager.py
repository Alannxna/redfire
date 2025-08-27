"""
缓存管理器

提供统一的缓存服务，支持内存缓存、Redis缓存等多种缓存后端
"""

import asyncio
import time
import json
import hashlib
from typing import Any, Optional, Dict, Union, Callable, Awaitable
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

from ..common.exceptions import InfrastructureException


class CacheBackendType(Enum):
    """缓存后端类型"""
    MEMORY = "memory"
    REDIS = "redis"
    MEMCACHED = "memcached"


@dataclass
class CacheItem:
    """缓存项"""
    value: Any
    expire_time: Optional[float] = None
    created_at: float = None
    access_count: int = 0
    last_access: float = None
    
    def __post_init__(self):
        current_time = time.time()
        if self.created_at is None:
            self.created_at = current_time
        if self.last_access is None:
            self.last_access = current_time
    
    def is_expired(self) -> bool:
        """检查是否过期"""
        if self.expire_time is None:
            return False
        return time.time() > self.expire_time
    
    def touch(self):
        """更新访问时间"""
        self.last_access = time.time()
        self.access_count += 1


class CacheBackend(ABC):
    """缓存后端抽象类"""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """设置缓存值"""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """删除缓存项"""
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """检查键是否存在"""
        pass
    
    @abstractmethod
    async def clear(self) -> bool:
        """清空所有缓存"""
        pass
    
    @abstractmethod
    async def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        pass


class MemoryCacheBackend(CacheBackend):
    """内存缓存后端"""
    
    def __init__(self, max_size: int = 1000, cleanup_interval: int = 300):
        self.max_size = max_size
        self.cleanup_interval = cleanup_interval
        self.cache: Dict[str, CacheItem] = {}
        self.stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0,
            'evictions': 0
        }
        self._cleanup_task: Optional[asyncio.Task] = None
        self._start_cleanup_task()
    
    def _start_cleanup_task(self):
        """启动清理任务"""
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._cleanup_expired())
    
    async def _cleanup_expired(self):
        """清理过期项"""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)
                expired_keys = []
                
                for key, item in self.cache.items():
                    if item.is_expired():
                        expired_keys.append(key)
                
                for key in expired_keys:
                    del self.cache[key]
                    
                # 如果超过最大大小，删除最旧的项
                if len(self.cache) > self.max_size:
                    sorted_items = sorted(
                        self.cache.items(),
                        key=lambda x: x[1].last_access
                    )
                    
                    to_remove = len(self.cache) - self.max_size
                    for i in range(to_remove):
                        key = sorted_items[i][0]
                        del self.cache[key]
                        self.stats['evictions'] += 1
                        
            except asyncio.CancelledError:
                break
            except Exception:
                # 忽略清理错误
                pass
    
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        item = self.cache.get(key)
        if item is None:
            self.stats['misses'] += 1
            return None
        
        if item.is_expired():
            del self.cache[key]
            self.stats['misses'] += 1
            return None
        
        item.touch()
        self.stats['hits'] += 1
        return item.value
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """设置缓存值"""
        expire_time = None
        if ttl is not None:
            expire_time = time.time() + ttl
        
        item = CacheItem(value=value, expire_time=expire_time)
        self.cache[key] = item
        self.stats['sets'] += 1
        return True
    
    async def delete(self, key: str) -> bool:
        """删除缓存项"""
        if key in self.cache:
            del self.cache[key]
            self.stats['deletes'] += 1
            return True
        return False
    
    async def exists(self, key: str) -> bool:
        """检查键是否存在"""
        item = self.cache.get(key)
        if item is None:
            return False
        
        if item.is_expired():
            del self.cache[key]
            return False
        
        return True
    
    async def clear(self) -> bool:
        """清空所有缓存"""
        self.cache.clear()
        return True
    
    async def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        return {
            **self.stats,
            'size': len(self.cache),
            'max_size': self.max_size
        }
    
    def stop(self):
        """停止后端"""
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()


class RedisCacheBackend(CacheBackend):
    """Redis缓存后端"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0", 
                 key_prefix: str = "vnpy:"):
        self.redis_url = redis_url
        self.key_prefix = key_prefix
        self.redis_client = None
        self.stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0
        }
    
    async def _ensure_connection(self):
        """确保Redis连接"""
        if self.redis_client is None:
            try:
                import aioredis
                self.redis_client = await aioredis.from_url(self.redis_url)
            except ImportError:
                raise InfrastructureException("aioredis not installed")
    
    def _make_key(self, key: str) -> str:
        """生成完整的键名"""
        return f"{self.key_prefix}{key}"
    
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        await self._ensure_connection()
        
        try:
            redis_key = self._make_key(key)
            value = await self.redis_client.get(redis_key)
            
            if value is None:
                self.stats['misses'] += 1
                return None
            
            self.stats['hits'] += 1
            return json.loads(value)
            
        except Exception as e:
            raise InfrastructureException(f"Redis get failed: {e}")
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """设置缓存值"""
        await self._ensure_connection()
        
        try:
            redis_key = self._make_key(key)
            json_value = json.dumps(value, default=str)
            
            if ttl is not None:
                await self.redis_client.setex(redis_key, ttl, json_value)
            else:
                await self.redis_client.set(redis_key, json_value)
            
            self.stats['sets'] += 1
            return True
            
        except Exception as e:
            raise InfrastructureException(f"Redis set failed: {e}")
    
    async def delete(self, key: str) -> bool:
        """删除缓存项"""
        await self._ensure_connection()
        
        try:
            redis_key = self._make_key(key)
            result = await self.redis_client.delete(redis_key)
            
            if result > 0:
                self.stats['deletes'] += 1
                return True
            return False
            
        except Exception as e:
            raise InfrastructureException(f"Redis delete failed: {e}")
    
    async def exists(self, key: str) -> bool:
        """检查键是否存在"""
        await self._ensure_connection()
        
        try:
            redis_key = self._make_key(key)
            return bool(await self.redis_client.exists(redis_key))
            
        except Exception as e:
            raise InfrastructureException(f"Redis exists failed: {e}")
    
    async def clear(self) -> bool:
        """清空所有缓存"""
        await self._ensure_connection()
        
        try:
            pattern = f"{self.key_prefix}*"
            keys = await self.redis_client.keys(pattern)
            
            if keys:
                await self.redis_client.delete(*keys)
            
            return True
            
        except Exception as e:
            raise InfrastructureException(f"Redis clear failed: {e}")
    
    async def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        await self._ensure_connection()
        
        try:
            info = await self.redis_client.info('memory')
            pattern = f"{self.key_prefix}*"
            keys_count = len(await self.redis_client.keys(pattern))
            
            return {
                **self.stats,
                'size': keys_count,
                'memory_usage': info.get('used_memory', 0),
                'memory_usage_human': info.get('used_memory_human', '0B')
            }
            
        except Exception:
            return self.stats


class CacheManager:
    """缓存管理器
    
    提供统一的缓存接口，支持多种缓存后端
    """
    
    def __init__(self, backend: Optional[CacheBackend] = None, 
                 default_ttl: Optional[int] = None):
        self.backend = backend or MemoryCacheBackend()
        self.default_ttl = default_ttl
        self._decorators_cache = {}
    
    async def get(self, key: str, default: Any = None) -> Any:
        """获取缓存值"""
        value = await self.backend.get(key)
        return value if value is not None else default
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """设置缓存值"""
        if ttl is None:
            ttl = self.default_ttl
        return await self.backend.set(key, value, ttl)
    
    async def delete(self, key: str) -> bool:
        """删除缓存项"""
        return await self.backend.delete(key)
    
    async def exists(self, key: str) -> bool:
        """检查键是否存在"""
        return await self.backend.exists(key)
    
    async def clear(self) -> bool:
        """清空所有缓存"""
        return await self.backend.clear()
    
    async def get_or_set(self, key: str, factory: Callable[[], Union[Any, Awaitable[Any]]], 
                        ttl: Optional[int] = None) -> Any:
        """获取缓存值，如果不存在则通过工厂函数创建"""
        value = await self.get(key)
        if value is not None:
            return value
        
        # 调用工厂函数
        if asyncio.iscoroutinefunction(factory):
            value = await factory()
        else:
            value = factory()
        
        await self.set(key, value, ttl)
        return value
    
    async def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        return await self.backend.get_stats()
    
    def make_key(self, *parts) -> str:
        """生成缓存键"""
        key_parts = []
        for part in parts:
            if isinstance(part, (dict, list)):
                # 对复杂对象生成哈希
                json_str = json.dumps(part, sort_keys=True, default=str)
                hash_value = hashlib.md5(json_str.encode()).hexdigest()[:8]
                key_parts.append(hash_value)
            else:
                key_parts.append(str(part))
        
        return ":".join(key_parts)
    
    def cached(self, ttl: Optional[int] = None, key_prefix: str = ""):
        """缓存装饰器"""
        def decorator(func: Callable):
            async def wrapper(*args, **kwargs):
                # 生成缓存键
                key_parts = [key_prefix or func.__name__]
                key_parts.extend(str(arg) for arg in args)
                key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
                cache_key = self.make_key(*key_parts)
                
                # 尝试从缓存获取
                cached_value = await self.get(cache_key)
                if cached_value is not None:
                    return cached_value
                
                # 执行函数
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)
                
                # 存入缓存
                await self.set(cache_key, result, ttl)
                return result
            
            return wrapper
        return decorator
    
    async def invalidate_pattern(self, pattern: str):
        """根据模式失效缓存（仅支持某些后端）"""
        if hasattr(self.backend, 'invalidate_pattern'):
            await self.backend.invalidate_pattern(pattern)
        else:
            # 对于不支持模式匹配的后端，暂时不处理
            pass
    
    def stop(self):
        """停止缓存管理器"""
        if hasattr(self.backend, 'stop'):
            self.backend.stop()


# 全局缓存管理器实例
_global_cache_manager: Optional[CacheManager] = None


def get_cache_manager() -> CacheManager:
    """获取全局缓存管理器"""
    global _global_cache_manager
    if _global_cache_manager is None:
        _global_cache_manager = CacheManager()
    return _global_cache_manager


def set_cache_manager(cache_manager: CacheManager):
    """设置全局缓存管理器"""
    global _global_cache_manager
    _global_cache_manager = cache_manager


# 便捷函数
async def get_cache(key: str, default: Any = None) -> Any:
    """获取缓存值的便捷函数"""
    return await get_cache_manager().get(key, default)


async def set_cache(key: str, value: Any, ttl: Optional[int] = None) -> bool:
    """设置缓存值的便捷函数"""
    return await get_cache_manager().set(key, value, ttl)


async def delete_cache(key: str) -> bool:
    """删除缓存的便捷函数"""
    return await get_cache_manager().delete(key)


def cached(ttl: Optional[int] = None, key_prefix: str = ""):
    """缓存装饰器的便捷函数"""
    return get_cache_manager().cached(ttl, key_prefix)
