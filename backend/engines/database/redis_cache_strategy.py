"""
Redis缓存策略实现
===============

为RedFire量化交易平台提供高效的Redis缓存解决方案
包括多级缓存、缓存预热、失效策略等
"""

import json
import pickle
import hashlib
from typing import Any, Optional, Dict, List, Union, Callable, TypeVar
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from functools import wraps
import asyncio
import logging

try:
    import redis
    import redis.asyncio as aioredis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

logger = logging.getLogger(__name__)

T = TypeVar('T')


@dataclass
class CacheConfig:
    """缓存配置"""
    ttl: int = 3600  # 默认1小时过期
    max_size: int = 1000  # 最大缓存条目数
    serialize_method: str = "json"  # json, pickle
    key_prefix: str = "redfire"
    version: int = 1
    compress: bool = False
    
    # 缓存策略
    cache_null: bool = False  # 是否缓存空值
    null_ttl: int = 300  # 空值缓存时间（5分钟）
    
    # 预热配置
    preload: bool = False
    preload_keys: List[str] = field(default_factory=list)


class CacheKey:
    """缓存键管理"""
    
    @staticmethod
    def build_key(prefix: str, namespace: str, key: str, version: int = 1) -> str:
        """构建缓存键"""
        return f"{prefix}:{namespace}:v{version}:{key}"
    
    @staticmethod
    def hash_key(data: Any) -> str:
        """生成数据哈希键"""
        if isinstance(data, (dict, list)):
            data_str = json.dumps(data, sort_keys=True, ensure_ascii=False)
        else:
            data_str = str(data)
        
        return hashlib.md5(data_str.encode('utf-8')).hexdigest()[:16]
    
    @staticmethod
    def extract_namespace(key: str) -> Optional[str]:
        """从键中提取命名空间"""
        parts = key.split(':')
        return parts[1] if len(parts) >= 2 else None


class CacheSerializer:
    """缓存序列化器"""
    
    @staticmethod
    def serialize(data: Any, method: str = "json") -> bytes:
        """序列化数据"""
        if method == "json":
            return json.dumps(data, ensure_ascii=False, default=str).encode('utf-8')
        elif method == "pickle":
            return pickle.dumps(data)
        else:
            raise ValueError(f"不支持的序列化方法: {method}")
    
    @staticmethod
    def deserialize(data: bytes, method: str = "json") -> Any:
        """反序列化数据"""
        if method == "json":
            return json.loads(data.decode('utf-8'))
        elif method == "pickle":
            return pickle.loads(data)
        else:
            raise ValueError(f"不支持的反序列化方法: {method}")


class RedisCacheManager:
    """Redis缓存管理器"""
    
    def __init__(self, redis_client: redis.Redis, config: CacheConfig):
        self.redis = redis_client
        self.config = config
        self._stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
            "errors": 0
        }
    
    def _build_key(self, namespace: str, key: str) -> str:
        """构建完整的缓存键"""
        return CacheKey.build_key(
            self.config.key_prefix,
            namespace,
            key,
            self.config.version
        )
    
    def get(self, namespace: str, key: str) -> Optional[Any]:
        """获取缓存数据"""
        try:
            cache_key = self._build_key(namespace, key)
            data = self.redis.get(cache_key)
            
            if data is None:
                self._stats["misses"] += 1
                return None
            
            # 反序列化数据
            result = CacheSerializer.deserialize(data, self.config.serialize_method)
            self._stats["hits"] += 1
            
            logger.debug(f"缓存命中: {cache_key}")
            return result
            
        except Exception as e:
            logger.error(f"获取缓存失败 {namespace}:{key}: {e}")
            self._stats["errors"] += 1
            return None
    
    def set(self, namespace: str, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """设置缓存数据"""
        try:
            # 检查是否缓存空值
            if value is None and not self.config.cache_null:
                return False
            
            cache_key = self._build_key(namespace, key)
            ttl = ttl or (self.config.null_ttl if value is None else self.config.ttl)
            
            # 序列化数据
            data = CacheSerializer.serialize(value, self.config.serialize_method)
            
            # 设置缓存
            result = self.redis.setex(cache_key, ttl, data)
            
            if result:
                self._stats["sets"] += 1
                logger.debug(f"缓存设置成功: {cache_key}, TTL: {ttl}")
            
            return result
            
        except Exception as e:
            logger.error(f"设置缓存失败 {namespace}:{key}: {e}")
            self._stats["errors"] += 1
            return False
    
    def delete(self, namespace: str, key: str) -> bool:
        """删除缓存数据"""
        try:
            cache_key = self._build_key(namespace, key)
            result = self.redis.delete(cache_key)
            
            if result:
                self._stats["deletes"] += 1
                logger.debug(f"缓存删除成功: {cache_key}")
            
            return bool(result)
            
        except Exception as e:
            logger.error(f"删除缓存失败 {namespace}:{key}: {e}")
            self._stats["errors"] += 1
            return False
    
    def exists(self, namespace: str, key: str) -> bool:
        """检查缓存是否存在"""
        try:
            cache_key = self._build_key(namespace, key)
            return bool(self.redis.exists(cache_key))
        except Exception as e:
            logger.error(f"检查缓存存在性失败 {namespace}:{key}: {e}")
            return False
    
    def expire(self, namespace: str, key: str, ttl: int) -> bool:
        """设置缓存过期时间"""
        try:
            cache_key = self._build_key(namespace, key)
            return bool(self.redis.expire(cache_key, ttl))
        except Exception as e:
            logger.error(f"设置缓存过期时间失败 {namespace}:{key}: {e}")
            return False
    
    def clear_namespace(self, namespace: str) -> int:
        """清空命名空间下的所有缓存"""
        try:
            pattern = self._build_key(namespace, "*")
            keys = self.redis.keys(pattern)
            
            if keys:
                deleted = self.redis.delete(*keys)
                self._stats["deletes"] += deleted
                logger.info(f"清空命名空间 {namespace}: 删除 {deleted} 个缓存")
                return deleted
            
            return 0
            
        except Exception as e:
            logger.error(f"清空命名空间失败 {namespace}: {e}")
            self._stats["errors"] += 1
            return 0
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        total_requests = self._stats["hits"] + self._stats["misses"]
        hit_rate = (self._stats["hits"] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "hits": self._stats["hits"],
            "misses": self._stats["misses"],
            "hit_rate": f"{hit_rate:.2f}%",
            "sets": self._stats["sets"],
            "deletes": self._stats["deletes"],
            "errors": self._stats["errors"],
            "total_requests": total_requests
        }
    
    def reset_stats(self):
        """重置统计信息"""
        for key in self._stats:
            self._stats[key] = 0


class AsyncRedisCacheManager:
    """异步Redis缓存管理器"""
    
    def __init__(self, redis_client, config: CacheConfig):
        self.redis = redis_client
        self.config = config
        self._stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
            "errors": 0
        }
    
    def _build_key(self, namespace: str, key: str) -> str:
        """构建完整的缓存键"""
        return CacheKey.build_key(
            self.config.key_prefix,
            namespace,
            key,
            self.config.version
        )
    
    async def get(self, namespace: str, key: str) -> Optional[Any]:
        """异步获取缓存数据"""
        try:
            cache_key = self._build_key(namespace, key)
            data = await self.redis.get(cache_key)
            
            if data is None:
                self._stats["misses"] += 1
                return None
            
            # 反序列化数据
            result = CacheSerializer.deserialize(data, self.config.serialize_method)
            self._stats["hits"] += 1
            
            logger.debug(f"异步缓存命中: {cache_key}")
            return result
            
        except Exception as e:
            logger.error(f"异步获取缓存失败 {namespace}:{key}: {e}")
            self._stats["errors"] += 1
            return None
    
    async def set(self, namespace: str, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """异步设置缓存数据"""
        try:
            # 检查是否缓存空值
            if value is None and not self.config.cache_null:
                return False
            
            cache_key = self._build_key(namespace, key)
            ttl = ttl or (self.config.null_ttl if value is None else self.config.ttl)
            
            # 序列化数据
            data = CacheSerializer.serialize(value, self.config.serialize_method)
            
            # 设置缓存
            result = await self.redis.setex(cache_key, ttl, data)
            
            if result:
                self._stats["sets"] += 1
                logger.debug(f"异步缓存设置成功: {cache_key}, TTL: {ttl}")
            
            return result
            
        except Exception as e:
            logger.error(f"异步设置缓存失败 {namespace}:{key}: {e}")
            self._stats["errors"] += 1
            return False
    
    async def delete(self, namespace: str, key: str) -> bool:
        """异步删除缓存数据"""
        try:
            cache_key = self._build_key(namespace, key)
            result = await self.redis.delete(cache_key)
            
            if result:
                self._stats["deletes"] += 1
                logger.debug(f"异步缓存删除成功: {cache_key}")
            
            return bool(result)
            
        except Exception as e:
            logger.error(f"异步删除缓存失败 {namespace}:{key}: {e}")
            self._stats["errors"] += 1
            return False
    
    async def clear_namespace(self, namespace: str) -> int:
        """异步清空命名空间下的所有缓存"""
        try:
            pattern = self._build_key(namespace, "*")
            keys = await self.redis.keys(pattern)
            
            if keys:
                deleted = await self.redis.delete(*keys)
                self._stats["deletes"] += deleted
                logger.info(f"异步清空命名空间 {namespace}: 删除 {deleted} 个缓存")
                return deleted
            
            return 0
            
        except Exception as e:
            logger.error(f"异步清空命名空间失败 {namespace}: {e}")
            self._stats["errors"] += 1
            return 0


class CacheDecorator:
    """缓存装饰器"""
    
    def __init__(self, cache_manager: Union[RedisCacheManager, AsyncRedisCacheManager], 
                 namespace: str, ttl: Optional[int] = None):
        self.cache_manager = cache_manager
        self.namespace = namespace
        self.ttl = ttl
    
    def __call__(self, func: Callable) -> Callable:
        """装饰器实现"""
        if asyncio.iscoroutinefunction(func):
            return self._async_wrapper(func)
        else:
            return self._sync_wrapper(func)
    
    def _sync_wrapper(self, func: Callable) -> Callable:
        """同步函数装饰器"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = CacheKey.hash_key((args, kwargs))
            
            # 尝试从缓存获取
            cached_result = self.cache_manager.get(self.namespace, cache_key)
            if cached_result is not None:
                return cached_result
            
            # 执行原函数
            result = func(*args, **kwargs)
            
            # 缓存结果
            self.cache_manager.set(self.namespace, cache_key, result, self.ttl)
            
            return result
        
        return wrapper
    
    def _async_wrapper(self, func: Callable) -> Callable:
        """异步函数装饰器"""
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = CacheKey.hash_key((args, kwargs))
            
            # 尝试从缓存获取
            cached_result = await self.cache_manager.get(self.namespace, cache_key)
            if cached_result is not None:
                return cached_result
            
            # 执行原函数
            result = await func(*args, **kwargs)
            
            # 缓存结果
            await self.cache_manager.set(self.namespace, cache_key, result, self.ttl)
            
            return result
        
        return wrapper


# 预定义的缓存配置
CACHE_CONFIGS = {
    "user_data": CacheConfig(
        ttl=1800,  # 30分钟
        serialize_method="json",
        key_prefix="redfire:user"
    ),
    "market_data": CacheConfig(
        ttl=60,  # 1分钟
        serialize_method="pickle",
        key_prefix="redfire:market"
    ),
    "strategy_data": CacheConfig(
        ttl=3600,  # 1小时
        serialize_method="pickle",
        key_prefix="redfire:strategy"
    ),
    "trading_signals": CacheConfig(
        ttl=300,  # 5分钟
        serialize_method="json",
        key_prefix="redfire:signals"
    ),
    "system_config": CacheConfig(
        ttl=7200,  # 2小时
        serialize_method="json",
        key_prefix="redfire:config"
    )
}


class CacheFactory:
    """缓存工厂"""
    
    @staticmethod
    def create_cache_manager(redis_client: redis.Redis, 
                           config_name: str = "default") -> RedisCacheManager:
        """创建同步缓存管理器"""
        config = CACHE_CONFIGS.get(config_name, CacheConfig())
        return RedisCacheManager(redis_client, config)
    
    @staticmethod
    def create_async_cache_manager(redis_client, 
                                 config_name: str = "default") -> AsyncRedisCacheManager:
        """创建异步缓存管理器"""
        config = CACHE_CONFIGS.get(config_name, CacheConfig())
        return AsyncRedisCacheManager(redis_client, config)
    
    @staticmethod
    def create_cache_decorator(cache_manager: Union[RedisCacheManager, AsyncRedisCacheManager],
                             namespace: str, ttl: Optional[int] = None) -> CacheDecorator:
        """创建缓存装饰器"""
        return CacheDecorator(cache_manager, namespace, ttl)


# 全局缓存管理器实例
_cache_managers: Dict[str, Union[RedisCacheManager, AsyncRedisCacheManager]] = {}


def get_cache_manager(config_name: str = "default") -> RedisCacheManager:
    """获取缓存管理器"""
    if config_name not in _cache_managers:
        from .optimized_config import get_optimized_redis_config
        
        redis_config = get_optimized_redis_config()
        redis_client = redis.Redis(**redis_config.get_connection_kwargs())
        
        _cache_managers[config_name] = CacheFactory.create_cache_manager(
            redis_client, config_name
        )
    
    return _cache_managers[config_name]


# 便捷装饰器
def cache(namespace: str, ttl: Optional[int] = None, config_name: str = "default"):
    """缓存装饰器快捷方式"""
    cache_manager = get_cache_manager(config_name)
    return CacheDecorator(cache_manager, namespace, ttl)
