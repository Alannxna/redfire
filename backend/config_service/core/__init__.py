# 🔧 RedFire配置管理服务 - 核心组件包

"""
核心组件包

包含配置管理的核心逻辑：
- 配置管理器
- 文件监听
- 热重载
- 缓存管理
"""

from .config_manager import (
    # 配置管理器类
    ExternalConfigManager,
    
    # 全局实例
    config_manager,
    
    # 便捷函数
    initialize_config,
    get_config,
    get_database_config,
    get_redis_config,
    get_vnpy_config,
    get_security_config,
    get_monitoring_config,
    get_api_gateway_config,
    reload_config
)

__all__ = [
    # 配置管理器类
    "ExternalConfigManager",
    
    # 全局实例
    "config_manager",
    
    # 便捷函数
    "initialize_config",
    "get_config",
    "get_database_config",
    "get_redis_config",
    "get_vnpy_config", 
    "get_security_config",
    "get_monitoring_config",
    "get_api_gateway_config",
    "reload_config"
]
