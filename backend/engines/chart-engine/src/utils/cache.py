"""
高性能缓存工具 - 支持TTL和LRU策略
"""

import time
import threading
from typing import Any, Dict, Optional, List
from collections import OrderedDict


class CacheItem:
    """缓存项"""
    
    def __init__(self, value: Any, ttl: Optional[int] = None):
        self.value = value
        self.created_at = time.time()
        self.ttl = ttl
        self.access_count = 0
        self.last_access = self.created_at
    
    def is_expired(self) -> bool:
        """检查是否过期"""
        if self.ttl is None:
            return False
        return time.time() - self.created_at > self.ttl
    
    def access(self) -> Any:
        """访问缓存项"""
        self.access_count += 1
        self.last_access = time.time()
        return self.value


class LRUCache:
    """
    LRU缓存实现
    
    特性:
    1. LRU淘汰策略
    2. TTL过期策略
    3. 线程安全
    4. 命中率统计
    """
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self._cache: OrderedDict[str, CacheItem] = OrderedDict()
        self._lock = threading.RLock()
        
        # 统计信息
        self._hits = 0
        self._misses = 0
        self._evictions = 0
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        with self._lock:
            if key not in self._cache:
                self._misses += 1
                return None
            
            item = self._cache[key]
            
            # 检查过期
            if item.is_expired():
                del self._cache[key]
                self._misses += 1
                return None
            
            # 移动到末尾 (LRU)
            self._cache.move_to_end(key)
            self._hits += 1
            
            return item.access()
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """设置缓存值"""
        with self._lock:
            # 如果key已存在，更新值
            if key in self._cache:
                self._cache[key] = CacheItem(value, ttl)
                self._cache.move_to_end(key)
                return
            
            # 检查容量限制
            while len(self._cache) >= self.max_size:
                # 移除最老的项
                oldest_key = next(iter(self._cache))
                del self._cache[oldest_key]
                self._evictions += 1
            
            # 添加新项
            self._cache[key] = CacheItem(value, ttl)
    
    def delete(self, key: str) -> bool:
        """删除缓存项"""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    def clear(self) -> None:
        """清空缓存"""
        with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0
            self._evictions = 0
    
    def cleanup(self) -> int:
        """清理过期项"""
        with self._lock:
            expired_keys = []
            
            for key, item in self._cache.items():
                if item.is_expired():
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self._cache[key]
            
            return len(expired_keys)
    
    def size(self) -> int:
        """获取缓存大小"""
        with self._lock:
            return len(self._cache)
    
    def keys(self) -> List[str]:
        """获取所有键"""
        with self._lock:
            return list(self._cache.keys())
    
    def get_hit_rate(self) -> float:
        """获取命中率"""
        with self._lock:
            total = self._hits + self._misses
            if total == 0:
                return 0.0
            return self._hits / total
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self._lock:
            total_requests = self._hits + self._misses
            return {
                "size": len(self._cache),
                "max_size": self.max_size,
                "hits": self._hits,
                "misses": self._misses,
                "evictions": self._evictions,
                "hit_rate": self.get_hit_rate(),
                "total_requests": total_requests
            }
