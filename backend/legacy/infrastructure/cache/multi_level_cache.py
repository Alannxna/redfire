"""
Multi-Level Cache System
========================

多级缓存系统，实现L1内存缓存、L2 Redis缓存、L3持久化缓存。
支持缓存预热、LRU淘汰、TTL过期管理等功能。
"""

import logging
import time
import json
import pickle
import hashlib
from typing import Any, Dict, List, Optional, Union, Tuple
from datetime import datetime, timedelta
from collections import OrderedDict
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import threading

try:
    import redis
    import redis.asyncio as aioredis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

logger = logging.getLogger(__name__)


class CacheLevel(Enum):
    """缓存级别"""
    L1_MEMORY = "L1_MEMORY"
    L2_REDIS = "L2_REDIS"
    L3_PERSISTENT = "L3_PERSISTENT"


class EvictionPolicy(Enum):
    """淘汰策略"""
    LRU = "LRU"
    LFU = "LFU"
    TTL = "TTL"
    FIFO = "FIFO"


@dataclass
class CacheItem:
    """缓存项"""
    key: str
    value: Any
    create_time: datetime = field(default_factory=datetime.now)
    access_time: datetime = field(default_factory=datetime.now)
    access_count: int = 0
    ttl: Optional[int] = None  # 秒
    size: int = 0
    
    def __post_init__(self):
        """计算缓存项大小"""
        try:
            if isinstance(self.value, (str, bytes)):
                self.size = len(self.value)
            else:
                # 估算对象大小
                self.size = len(str(self.value))
        except:
            self.size = 64  # 默认大小
    
    def is_expired(self) -> bool:
        """检查是否过期"""
        if self.ttl is None:
            return False
        return (datetime.now() - self.create_time).total_seconds() > self.ttl
    
    def touch(self) -> None:
        """更新访问信息"""
        self.access_time = datetime.now()
        self.access_count += 1


@dataclass
class CacheStats:
    """缓存统计"""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    size: int = 0
    item_count: int = 0
    last_reset: datetime = field(default_factory=datetime.now)
    
    @property
    def hit_rate(self) -> float:
        """命中率"""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "hits": self.hits,
            "misses": self.misses,
            "evictions": self.evictions,
            "size": self.size,
            "item_count": self.item_count,
            "hit_rate": self.hit_rate,
            "last_reset": self.last_reset.isoformat()
        }


class L1MemoryCache:
    """L1内存缓存"""
    
    def __init__(
        self,
        max_size: int = 1000,
        max_memory: int = 100 * 1024 * 1024,  # 100MB
        eviction_policy: EvictionPolicy = EvictionPolicy.LRU,
        default_ttl: Optional[int] = None
    ):
        self.max_size = max_size
        self.max_memory = max_memory
        self.eviction_policy = eviction_policy
        self.default_ttl = default_ttl
        
        self._cache: OrderedDict[str, CacheItem] = OrderedDict()
        self._lock = threading.RLock()
        self._stats = CacheStats()
    
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        with self._lock:
            item = self._cache.get(key)
            if item is None:
                self._stats.misses += 1
                return None
            
            if item.is_expired():
                del self._cache[key]
                self._stats.misses += 1
                self._stats.evictions += 1
                return None
            
            item.touch()
            
            # 更新LRU顺序
            if self.eviction_policy == EvictionPolicy.LRU:
                self._cache.move_to_end(key)
            
            self._stats.hits += 1
            return item.value
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """设置缓存值"""
        try:
            with self._lock:
                ttl = ttl or self.default_ttl
                item = CacheItem(key=key, value=value, ttl=ttl)
                
                # 检查是否需要淘汰
                await self._ensure_capacity(item.size)
                
                self._cache[key] = item
                
                # 更新统计
                self._stats.item_count = len(self._cache)
                self._stats.size = sum(item.size for item in self._cache.values())
                
                return True
                
        except Exception as e:
            logger.error(f"L1缓存设置失败: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """删除缓存值"""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                self._stats.item_count = len(self._cache)
                self._stats.size = sum(item.size for item in self._cache.values())
                return True
            return False
    
    async def clear(self) -> None:
        """清空缓存"""
        with self._lock:
            self._cache.clear()
            self._stats = CacheStats()
    
    async def _ensure_capacity(self, new_item_size: int) -> None:
        """确保缓存容量"""
        # 检查数量限制
        while len(self._cache) >= self.max_size:
            await self._evict_one()
        
        # 检查内存限制
        current_size = sum(item.size for item in self._cache.values())
        while current_size + new_item_size > self.max_memory and self._cache:
            await self._evict_one()
            current_size = sum(item.size for item in self._cache.values())
    
    async def _evict_one(self) -> None:
        """淘汰一个缓存项"""
        if not self._cache:
            return
        
        if self.eviction_policy == EvictionPolicy.LRU:
            # 移除最少使用的（最早的）
            key, _ = self._cache.popitem(last=False)
        elif self.eviction_policy == EvictionPolicy.LFU:
            # 移除使用频率最低的
            min_item = min(self._cache.values(), key=lambda x: x.access_count)
            key = min_item.key
            del self._cache[key]
        elif self.eviction_policy == EvictionPolicy.TTL:
            # 移除最早过期的
            expired_items = [
                (k, v) for k, v in self._cache.items() if v.is_expired()
            ]
            if expired_items:
                key = expired_items[0][0]
                del self._cache[key]
            else:
                # 如果没有过期项，使用LRU
                key, _ = self._cache.popitem(last=False)
        elif self.eviction_policy == EvictionPolicy.FIFO:
            # 移除最早添加的
            key, _ = self._cache.popitem(last=False)
        
        self._stats.evictions += 1
    
    def get_stats(self) -> CacheStats:
        """获取统计信息"""
        with self._lock:
            self._stats.item_count = len(self._cache)
            self._stats.size = sum(item.size for item in self._cache.values())
            return self._stats


class L2RedisCache:
    """L2 Redis缓存"""
    
    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        db: int = 0,
        key_prefix: str = "redfire:",
        default_ttl: Optional[int] = 3600,
        serializer: str = "json"
    ):
        self.redis_url = redis_url
        self.db = db
        self.key_prefix = key_prefix
        self.default_ttl = default_ttl
        self.serializer = serializer
        
        self._redis: Optional[aioredis.Redis] = None
        self._stats = CacheStats()
        
        if not REDIS_AVAILABLE:
            logger.warning("Redis未安装，L2缓存将被禁用")
    
    async def connect(self) -> bool:
        """连接Redis"""
        if not REDIS_AVAILABLE:
            return False
        
        try:
            self._redis = aioredis.from_url(
                self.redis_url,
                db=self.db,
                decode_responses=True
            )
            
            # 测试连接
            await self._redis.ping()
            logger.info("Redis连接成功")
            return True
            
        except Exception as e:
            logger.error(f"Redis连接失败: {e}")
            return False
    
    async def disconnect(self) -> None:
        """断开连接"""
        if self._redis:
            await self._redis.close()
            self._redis = None
    
    def _get_full_key(self, key: str) -> str:
        """获取完整键名"""
        return f"{self.key_prefix}{key}"
    
    def _serialize(self, value: Any) -> str:
        """序列化值"""
        try:
            if self.serializer == "json":
                return json.dumps(value, default=str)
            elif self.serializer == "pickle":
                return pickle.dumps(value).hex()
            else:
                return str(value)
        except Exception as e:
            logger.error(f"序列化失败: {e}")
            return str(value)
    
    def _deserialize(self, value: str) -> Any:
        """反序列化值"""
        try:
            if self.serializer == "json":
                return json.loads(value)
            elif self.serializer == "pickle":
                return pickle.loads(bytes.fromhex(value))
            else:
                return value
        except Exception as e:
            logger.error(f"反序列化失败: {e}")
            return value
    
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        if not self._redis:
            self._stats.misses += 1
            return None
        
        try:
            full_key = self._get_full_key(key)
            value = await self._redis.get(full_key)
            
            if value is None:
                self._stats.misses += 1
                return None
            
            self._stats.hits += 1
            return self._deserialize(value)
            
        except Exception as e:
            logger.error(f"Redis获取失败: {e}")
            self._stats.misses += 1
            return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """设置缓存值"""
        if not self._redis:
            return False
        
        try:
            full_key = self._get_full_key(key)
            serialized_value = self._serialize(value)
            ttl = ttl or self.default_ttl
            
            if ttl:
                await self._redis.setex(full_key, ttl, serialized_value)
            else:
                await self._redis.set(full_key, serialized_value)
            
            return True
            
        except Exception as e:
            logger.error(f"Redis设置失败: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """删除缓存值"""
        if not self._redis:
            return False
        
        try:
            full_key = self._get_full_key(key)
            result = await self._redis.delete(full_key)
            return result > 0
            
        except Exception as e:
            logger.error(f"Redis删除失败: {e}")
            return False
    
    async def clear(self) -> None:
        """清空缓存"""
        if not self._redis:
            return
        
        try:
            pattern = f"{self.key_prefix}*"
            keys = await self._redis.keys(pattern)
            if keys:
                await self._redis.delete(*keys)
            
        except Exception as e:
            logger.error(f"Redis清空失败: {e}")
    
    async def get_info(self) -> Dict[str, Any]:
        """获取Redis信息"""
        if not self._redis:
            return {}
        
        try:
            info = await self._redis.info()
            return {
                "redis_version": info.get("redis_version"),
                "used_memory": info.get("used_memory"),
                "used_memory_human": info.get("used_memory_human"),
                "connected_clients": info.get("connected_clients"),
                "total_commands_processed": info.get("total_commands_processed"),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0)
            }
            
        except Exception as e:
            logger.error(f"获取Redis信息失败: {e}")
            return {}
    
    def get_stats(self) -> CacheStats:
        """获取统计信息"""
        return self._stats


class L3PersistentCache:
    """L3持久化缓存"""
    
    def __init__(
        self,
        cache_dir: str = "cache",
        max_files: int = 10000,
        default_ttl: Optional[int] = 86400  # 24小时
    ):
        self.cache_dir = cache_dir
        self.max_files = max_files
        self.default_ttl = default_ttl
        
        self._stats = CacheStats()
        self._ensure_cache_dir()
    
    def _ensure_cache_dir(self) -> None:
        """确保缓存目录存在"""
        import os
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir, exist_ok=True)
    
    def _get_file_path(self, key: str) -> str:
        """获取文件路径"""
        import os
        # 使用MD5哈希避免文件名过长或包含特殊字符
        hash_key = hashlib.md5(key.encode()).hexdigest()
        return os.path.join(self.cache_dir, f"{hash_key}.cache")
    
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        try:
            import os
            file_path = self._get_file_path(key)
            
            if not os.path.exists(file_path):
                self._stats.misses += 1
                return None
            
            # 检查TTL
            if self.default_ttl:
                file_mtime = os.path.getmtime(file_path)
                if time.time() - file_mtime > self.default_ttl:
                    os.remove(file_path)
                    self._stats.misses += 1
                    self._stats.evictions += 1
                    return None
            
            with open(file_path, 'rb') as f:
                data = pickle.load(f)
            
            self._stats.hits += 1
            return data
            
        except Exception as e:
            logger.error(f"L3缓存获取失败: {e}")
            self._stats.misses += 1
            return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """设置缓存值"""
        try:
            import os
            
            # 检查文件数量限制
            await self._ensure_file_capacity()
            
            file_path = self._get_file_path(key)
            
            with open(file_path, 'wb') as f:
                pickle.dump(value, f)
            
            return True
            
        except Exception as e:
            logger.error(f"L3缓存设置失败: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """删除缓存值"""
        try:
            import os
            file_path = self._get_file_path(key)
            
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
            
        except Exception as e:
            logger.error(f"L3缓存删除失败: {e}")
            return False
    
    async def clear(self) -> None:
        """清空缓存"""
        try:
            import os
            import glob
            
            cache_files = glob.glob(os.path.join(self.cache_dir, "*.cache"))
            for file_path in cache_files:
                os.remove(file_path)
            
        except Exception as e:
            logger.error(f"L3缓存清空失败: {e}")
    
    async def _ensure_file_capacity(self) -> None:
        """确保文件容量"""
        try:
            import os
            import glob
            
            cache_files = glob.glob(os.path.join(self.cache_dir, "*.cache"))
            
            if len(cache_files) >= self.max_files:
                # 按修改时间排序，删除最旧的文件
                cache_files.sort(key=lambda x: os.path.getmtime(x))
                files_to_remove = cache_files[:len(cache_files) - self.max_files + 100]
                
                for file_path in files_to_remove:
                    os.remove(file_path)
                    self._stats.evictions += 1
            
        except Exception as e:
            logger.error(f"L3缓存容量管理失败: {e}")
    
    def get_stats(self) -> CacheStats:
        """获取统计信息"""
        try:
            import os
            import glob
            
            cache_files = glob.glob(os.path.join(self.cache_dir, "*.cache"))
            
            self._stats.item_count = len(cache_files)
            self._stats.size = sum(
                os.path.getsize(f) for f in cache_files if os.path.exists(f)
            )
            
        except Exception as e:
            logger.error(f"L3缓存统计失败: {e}")
        
        return self._stats


class MultiLevelCache:
    """多级缓存系统"""
    
    def __init__(
        self,
        l1_config: Optional[Dict[str, Any]] = None,
        l2_config: Optional[Dict[str, Any]] = None,
        l3_config: Optional[Dict[str, Any]] = None,
        write_through: bool = True,
        read_through: bool = True
    ):
        self.write_through = write_through
        self.read_through = read_through
        
        # 初始化各级缓存
        l1_config = l1_config or {}
        self.l1_cache = L1MemoryCache(**l1_config)
        
        l2_config = l2_config or {}
        self.l2_cache = L2RedisCache(**l2_config)
        
        l3_config = l3_config or {}
        self.l3_cache = L3PersistentCache(**l3_config)
        
        self._enabled_levels = [CacheLevel.L1_MEMORY, CacheLevel.L2_REDIS, CacheLevel.L3_PERSISTENT]
        self._warmup_keys: List[str] = []
    
    async def initialize(self) -> None:
        """初始化缓存系统"""
        try:
            # 连接Redis
            redis_connected = await self.l2_cache.connect()
            if not redis_connected:
                logger.warning("L2 Redis缓存不可用")
                self._enabled_levels.remove(CacheLevel.L2_REDIS)
            
            logger.info(f"多级缓存系统初始化完成，启用级别: {[level.value for level in self._enabled_levels]}")
            
        except Exception as e:
            logger.error(f"多级缓存初始化失败: {e}")
            raise
    
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存值，按级别依次查找"""
        try:
            # L1缓存
            if CacheLevel.L1_MEMORY in self._enabled_levels:
                value = await self.l1_cache.get(key)
                if value is not None:
                    return value
            
            # L2缓存
            if CacheLevel.L2_REDIS in self._enabled_levels:
                value = await self.l2_cache.get(key)
                if value is not None:
                    # 回写到L1
                    if CacheLevel.L1_MEMORY in self._enabled_levels:
                        await self.l1_cache.set(key, value)
                    return value
            
            # L3缓存
            if CacheLevel.L3_PERSISTENT in self._enabled_levels:
                value = await self.l3_cache.get(key)
                if value is not None:
                    # 回写到L1和L2
                    if CacheLevel.L1_MEMORY in self._enabled_levels:
                        await self.l1_cache.set(key, value)
                    if CacheLevel.L2_REDIS in self._enabled_levels:
                        await self.l2_cache.set(key, value)
                    return value
            
            return None
            
        except Exception as e:
            logger.error(f"多级缓存获取失败: {e}")
            return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        levels: Optional[List[CacheLevel]] = None
    ) -> bool:
        """设置缓存值"""
        try:
            levels = levels or self._enabled_levels
            success = True
            
            # 写入各级缓存
            if CacheLevel.L1_MEMORY in levels and CacheLevel.L1_MEMORY in self._enabled_levels:
                result = await self.l1_cache.set(key, value, ttl)
                success = success and result
            
            if CacheLevel.L2_REDIS in levels and CacheLevel.L2_REDIS in self._enabled_levels:
                result = await self.l2_cache.set(key, value, ttl)
                success = success and result
            
            if CacheLevel.L3_PERSISTENT in levels and CacheLevel.L3_PERSISTENT in self._enabled_levels:
                result = await self.l3_cache.set(key, value, ttl)
                success = success and result
            
            return success
            
        except Exception as e:
            logger.error(f"多级缓存设置失败: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """删除缓存值"""
        try:
            success = True
            
            # 从各级缓存删除
            if CacheLevel.L1_MEMORY in self._enabled_levels:
                result = await self.l1_cache.delete(key)
                success = success and result
            
            if CacheLevel.L2_REDIS in self._enabled_levels:
                result = await self.l2_cache.delete(key)
                success = success and result
            
            if CacheLevel.L3_PERSISTENT in self._enabled_levels:
                result = await self.l3_cache.delete(key)
                success = success and result
            
            return success
            
        except Exception as e:
            logger.error(f"多级缓存删除失败: {e}")
            return False
    
    async def clear(self, levels: Optional[List[CacheLevel]] = None) -> None:
        """清空缓存"""
        try:
            levels = levels or self._enabled_levels
            
            if CacheLevel.L1_MEMORY in levels:
                await self.l1_cache.clear()
            
            if CacheLevel.L2_REDIS in levels:
                await self.l2_cache.clear()
            
            if CacheLevel.L3_PERSISTENT in levels:
                await self.l3_cache.clear()
            
        except Exception as e:
            logger.error(f"多级缓存清空失败: {e}")
    
    async def warmup(self, keys: List[str], data_loader = None) -> None:
        """缓存预热"""
        try:
            if not data_loader:
                logger.warning("缓存预热需要提供数据加载器")
                return
            
            logger.info(f"开始缓存预热，键数量: {len(keys)}")
            
            for key in keys:
                # 检查是否已存在
                value = await self.get(key)
                if value is None:
                    # 加载数据
                    try:
                        if asyncio.iscoroutinefunction(data_loader):
                            value = await data_loader(key)
                        else:
                            value = data_loader(key)
                        
                        if value is not None:
                            await self.set(key, value)
                    except Exception as e:
                        logger.error(f"预热键 {key} 失败: {e}")
            
            logger.info("缓存预热完成")
            
        except Exception as e:
            logger.error(f"缓存预热失败: {e}")
    
    async def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        try:
            stats = {
                "enabled_levels": [level.value for level in self._enabled_levels],
                "l1_stats": self.l1_cache.get_stats().to_dict(),
                "l2_stats": self.l2_cache.get_stats().to_dict(),
                "l3_stats": self.l3_cache.get_stats().to_dict(),
                "timestamp": datetime.now().isoformat()
            }
            
            # 添加Redis信息
            if CacheLevel.L2_REDIS in self._enabled_levels:
                redis_info = await self.l2_cache.get_info()
                stats["redis_info"] = redis_info
            
            # 计算总体统计
            total_hits = stats["l1_stats"]["hits"] + stats["l2_stats"]["hits"] + stats["l3_stats"]["hits"]
            total_misses = stats["l1_stats"]["misses"] + stats["l2_stats"]["misses"] + stats["l3_stats"]["misses"]
            
            stats["total_stats"] = {
                "hits": total_hits,
                "misses": total_misses,
                "hit_rate": total_hits / (total_hits + total_misses) if (total_hits + total_misses) > 0 else 0.0
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"获取缓存统计失败: {e}")
            return {"error": str(e)}
    
    async def shutdown(self) -> None:
        """关闭缓存系统"""
        try:
            await self.l2_cache.disconnect()
            logger.info("多级缓存系统已关闭")
            
        except Exception as e:
            logger.error(f"缓存系统关闭失败: {e}")


# 全局缓存实例
_cache_instance: Optional[MultiLevelCache] = None


async def get_cache() -> MultiLevelCache:
    """获取全局缓存实例"""
    global _cache_instance
    
    if _cache_instance is None:
        _cache_instance = MultiLevelCache()
        await _cache_instance.initialize()
    
    return _cache_instance


def cache_decorator(
    key_func=None,
    ttl: Optional[int] = None,
    levels: Optional[List[CacheLevel]] = None
):
    """缓存装饰器"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            cache = await get_cache()
            
            # 生成缓存键
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            # 尝试从缓存获取
            result = await cache.get(cache_key)
            if result is not None:
                return result
            
            # 调用原函数
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            
            # 存入缓存
            if result is not None:
                await cache.set(cache_key, result, ttl, levels)
            
            return result
        
        return wrapper
    return decorator
