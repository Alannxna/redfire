"""
共享配置模块
===========

提供统一的配置加载和管理功能

主要组件:
- config_loader: 配置加载器和相关功能
- utils: 配置处理工具和实用函数
- cache: 配置缓存管理
- standards: 配置标准和规范
"""

# 主要配置加载器
from .config_loader import (
    SharedConfigLoader,
    ConfigSource,
    ConfigLoadResult,
    ConfigLoaderError,
    get_config_loader,
    load_config,
    load_app_config,
    load_database_config,
    LegacyConfigAdapter,
    create_legacy_adapter
)

# 配置工具
from .utils import (
    ConfigTypeConverter,
    ConfigFileLoader,
    ConfigEnvLoader,
    ConfigMerger,
    ConfigValidator,
    ConfigCache,
    ConfigError
)

# 缓存管理
from .cache import (
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
    # 配置加载器
    'SharedConfigLoader',
    'ConfigSource', 
    'ConfigLoadResult',
    'ConfigLoaderError',
    'get_config_loader',
    'load_config',
    'load_app_config', 
    'load_database_config',
    'LegacyConfigAdapter',
    'create_legacy_adapter',
    
    # 配置工具
    'ConfigTypeConverter',
    'ConfigFileLoader', 
    'ConfigEnvLoader',
    'ConfigMerger',
    'ConfigValidator',
    'ConfigCache',
    'ConfigError',
    
    # 缓存管理
    'global_cache_manager',
    'CacheType',
    'CacheStats',
    'cache_get',
    'cache_set', 
    'cache_clear',
    'cache_exists',
    'get_cache_stats'
]
