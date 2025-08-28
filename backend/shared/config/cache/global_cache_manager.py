"""
全局配置缓存管理器
================

统一管理所有配置模块的缓存，解决多缓存不一致问题
"""

import logging
import threading
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from enum import Enum
from ..utils.config_utils import ConfigCache

logger = logging.getLogger(__name__)


class CacheType(Enum):
    """缓存类型枚举"""
    CONFIG_LOADER = "config_loader"          # 配置加载器缓存
    CONFIG_MANAGER = "config_manager"        # 配置管理器缓存
    SERVICE_CONFIG = "service_config"        # 服务配置缓存
    SHARED_CONFIG = "shared_config"          # 共享配置缓存


@dataclass
class CacheStats:
    """缓存统计信息"""
    cache_type: CacheType
    hit_count: int = 0
    miss_count: int = 0
    total_requests: int = 0
    cache_size: int = 0
    
    @property
    def hit_rate(self) -> float:
        """缓存命中率"""
        if self.total_requests == 0:
            return 0.0
        return self.hit_count / self.total_requests


@dataclass 
class CacheConfig:
    """缓存配置"""
    max_size: int = 100
    ttl_seconds: Optional[int] = 300  # 5分钟
    enable_stats: bool = True
    auto_cleanup: bool = True


class GlobalConfigCacheManager:
    """
    全局配置缓存管理器
    
    特性:
    - 统一缓存管理接口
    - 缓存命名空间隔离
    - 统计信息收集
    - 缓存一致性保证
    - 内存限制和清理
    """
    
    _instance: Optional['GlobalConfigCacheManager'] = None
    _lock = threading.Lock()
    
    def __new__(cls) -> 'GlobalConfigCacheManager':
        """单例模式"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """初始化全局缓存管理器"""
        if hasattr(self, '_initialized') and self._initialized:
            return
            
        self._caches: Dict[CacheType, ConfigCache] = {}
        self._stats: Dict[CacheType, CacheStats] = {}
        self._configs: Dict[CacheType, CacheConfig] = {}
        self._lock = threading.RLock()
        self._change_listeners: List[Callable[[CacheType, str, Any], None]] = []
        
        # 初始化默认缓存类型
        self._init_default_caches()
        self._initialized = True
        
        logger.info("🚀 全局配置缓存管理器初始化完成")
    
    def _init_default_caches(self):
        """初始化默认缓存类型"""
        default_configs = {
            CacheType.CONFIG_LOADER: CacheConfig(max_size=50, ttl_seconds=300),
            CacheType.CONFIG_MANAGER: CacheConfig(max_size=100, ttl_seconds=600),
            CacheType.SERVICE_CONFIG: CacheConfig(max_size=200, ttl_seconds=1800),
            CacheType.SHARED_CONFIG: CacheConfig(max_size=75, ttl_seconds=900),
        }
        
        for cache_type, config in default_configs.items():
            self.register_cache(cache_type, config)
    
    def register_cache(self, cache_type: CacheType, 
                      config: Optional[CacheConfig] = None) -> ConfigCache:
        """
        注册缓存类型
        
        Args:
            cache_type: 缓存类型
            config: 缓存配置
            
        Returns:
            配置缓存实例
        """
        with self._lock:
            if config is None:
                config = CacheConfig()
            
            cache = ConfigCache(
                max_size=config.max_size,
                ttl_seconds=config.ttl_seconds
            )
            
            self._caches[cache_type] = cache
            self._configs[cache_type] = config
            self._stats[cache_type] = CacheStats(cache_type=cache_type)
            
            logger.info(f"📋 注册缓存类型: {cache_type.value}")
            return cache
    
    def get_cache(self, cache_type: CacheType) -> Optional[ConfigCache]:
        """
        获取指定类型的缓存
        
        Args:
            cache_type: 缓存类型
            
        Returns:
            配置缓存实例，如果不存在则返回None
        """
        return self._caches.get(cache_type)
    
    def get(self, cache_type: CacheType, key: str, default: Any = None) -> Any:
        """
        从指定缓存类型获取值
        
        Args:
            cache_type: 缓存类型
            key: 缓存键
            default: 默认值
            
        Returns:
            缓存值或默认值
        """
        with self._lock:
            cache = self._caches.get(cache_type)
            if not cache:
                logger.warning(f"缓存类型不存在: {cache_type.value}")
                return default
            
            value = cache.get(key, default)
            
            # 更新统计信息
            if cache_type in self._stats:
                stats = self._stats[cache_type]
                stats.total_requests += 1
                if value != default:
                    stats.hit_count += 1
                else:
                    stats.miss_count += 1
            
            return value
    
    def set(self, cache_type: CacheType, key: str, value: Any) -> None:
        """
        向指定缓存类型设置值
        
        Args:
            cache_type: 缓存类型
            key: 缓存键
            value: 缓存值
        """
        with self._lock:
            cache = self._caches.get(cache_type)
            if not cache:
                logger.warning(f"缓存类型不存在: {cache_type.value}")
                return
            
            cache.set(key, value)
            
            # 更新缓存大小统计
            if cache_type in self._stats:
                self._stats[cache_type].cache_size = len(cache._cache)
            
            # 通知变更监听器
            self._notify_change_listeners(cache_type, key, value)
    
    def delete(self, cache_type: CacheType, key: str) -> bool:
        """
        从指定缓存类型删除值
        
        Args:
            cache_type: 缓存类型
            key: 缓存键
            
        Returns:
            是否删除成功
        """
        with self._lock:
            cache = self._caches.get(cache_type)
            if not cache:
                return False
            
            # ConfigCache 当前没有 delete 方法，先设为 None 再清理
            if key in cache._cache:
                del cache._cache[key]
                if key in cache._timestamps:
                    del cache._timestamps[key]
                
                # 更新统计信息
                if cache_type in self._stats:
                    self._stats[cache_type].cache_size = len(cache._cache)
                
                return True
            
            return False
    
    def clear(self, cache_type: Optional[CacheType] = None) -> None:
        """
        清空缓存
        
        Args:
            cache_type: 要清空的缓存类型，None表示清空所有缓存
        """
        with self._lock:
            if cache_type:
                cache = self._caches.get(cache_type)
                if cache:
                    cache.clear()
                    if cache_type in self._stats:
                        self._stats[cache_type].cache_size = 0
                    logger.info(f"🧹 清空缓存: {cache_type.value}")
            else:
                for cache in self._caches.values():
                    cache.clear()
                for stats in self._stats.values():
                    stats.cache_size = 0
                logger.info("🧹 清空所有缓存")
    
    def get_stats(self, cache_type: Optional[CacheType] = None) -> Dict[CacheType, CacheStats]:
        """
        获取缓存统计信息
        
        Args:
            cache_type: 要获取统计信息的缓存类型，None表示获取所有统计信息
            
        Returns:
            缓存统计信息字典
        """
        with self._lock:
            if cache_type:
                return {cache_type: self._stats.get(cache_type, CacheStats(cache_type))}
            else:
                return self._stats.copy()
    
    def get_total_memory_usage(self) -> Dict[str, Any]:
        """
        获取总内存使用情况
        
        Returns:
            内存使用统计信息
        """
        with self._lock:
            total_items = sum(len(cache._cache) for cache in self._caches.values())
            
            cache_sizes = {}
            for cache_type, cache in self._caches.items():
                cache_sizes[cache_type.value] = len(cache._cache)
            
            return {
                "total_caches": len(self._caches),
                "total_items": total_items,
                "cache_sizes": cache_sizes,
                "stats": {
                    cache_type.value: {
                        "hit_rate": stats.hit_rate,
                        "total_requests": stats.total_requests,
                        "cache_size": stats.cache_size
                    }
                    for cache_type, stats in self._stats.items()
                }
            }
    
    def add_change_listener(self, listener: Callable[[CacheType, str, Any], None]) -> None:
        """
        添加缓存变更监听器
        
        Args:
            listener: 监听器函数，接收 (cache_type, key, value) 参数
        """
        with self._lock:
            self._change_listeners.append(listener)
    
    def remove_change_listener(self, listener: Callable[[CacheType, str, Any], None]) -> None:
        """
        移除缓存变更监听器
        
        Args:
            listener: 要移除的监听器函数
        """
        with self._lock:
            if listener in self._change_listeners:
                self._change_listeners.remove(listener)
    
    def _notify_change_listeners(self, cache_type: CacheType, key: str, value: Any) -> None:
        """通知缓存变更监听器"""
        for listener in self._change_listeners:
            try:
                listener(cache_type, key, value)
            except Exception as e:
                logger.error(f"缓存变更监听器执行失败: {e}")
    
    def optimize_memory(self) -> Dict[str, int]:
        """
        优化内存使用
        
        Returns:
            优化统计信息
        """
        with self._lock:
            cleaned_items = 0
            
            for cache_type, cache in self._caches.items():
                before_size = len(cache._cache)
                cache._cleanup_expired()  # 清理过期项
                after_size = len(cache._cache)
                
                cleaned_count = before_size - after_size
                cleaned_items += cleaned_count
                
                # 更新统计信息
                if cache_type in self._stats:
                    self._stats[cache_type].cache_size = after_size
                
                if cleaned_count > 0:
                    logger.info(f"🧼 缓存 {cache_type.value} 清理了 {cleaned_count} 个过期项")
            
            return {
                "cleaned_items": cleaned_items,
                "total_caches": len(self._caches),
                "current_total_items": sum(len(cache._cache) for cache in self._caches.values())
            }


# 全局实例
global_cache_manager = GlobalConfigCacheManager()


# 便捷函数
def get_cache(cache_type: CacheType) -> Optional[ConfigCache]:
    """获取指定类型的缓存"""
    return global_cache_manager.get_cache(cache_type)


def cache_get(cache_type: CacheType, key: str, default: Any = None) -> Any:
    """从缓存获取值"""
    return global_cache_manager.get(cache_type, key, default)


def cache_set(cache_type: CacheType, key: str, value: Any) -> None:
    """向缓存设置值"""
    return global_cache_manager.set(cache_type, key, value)


def cache_clear(cache_type: Optional[CacheType] = None) -> None:
    """清空缓存"""
    return global_cache_manager.clear(cache_type)


def cache_exists(cache_type: CacheType, key: str) -> bool:
    """检查缓存项是否存在"""
    return global_cache_manager.exists(cache_type, key)


def get_cache_stats() -> Dict[CacheType, CacheStats]:
    """获取缓存统计信息"""
    return global_cache_manager.get_stats()


def optimize_cache_memory() -> Dict[str, int]:
    """优化缓存内存使用"""
    return global_cache_manager.optimize_memory()
