"""
配置缓存模块
============

提供统一的配置缓存管理功能
"""

from .global_cache_manager import (
    global_cache_manager,
    CacheType,
    CacheStats,
    cache_get,
    cache_set,
    cache_clear,
    cache_exists,
    get_cache_stats
)

__all__ = [
    'global_cache_manager',
    'CacheType',
    'CacheStats',
    'cache_get',
    'cache_set', 
    'cache_clear',
    'cache_exists',
    'get_cache_stats'
]
