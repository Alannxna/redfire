"""
基础设施层

提供依赖注入、配置管理、缓存、监控、日志等基础设施服务
"""

from .dependency_container import DependencyContainer, ServiceScope
from .config_manager import ConfigManager, get_config_manager, get_config
from .cache_manager import CacheManager, get_cache_manager, cached
from .monitoring import MonitorService, MonitorServiceConfig
from .logging import LogManager, get_logger, configure_logging
from .service_registry import ServiceRegistry, get_service_registry

__all__ = [
    # 依赖注入
    "DependencyContainer",
    "ServiceScope",
    
    # 配置管理
    "ConfigManager",
    "get_config_manager",
    "get_config",
    
    # 缓存管理
    "CacheManager", 
    "get_cache_manager",
    "cached",
    
    # 监控服务
    "MonitorService",
    "MonitorServiceConfig",
    
    # 日志服务
    "LogManager",
    "get_logger",
    "configure_logging",
    
    # 服务注册
    "ServiceRegistry",
    "get_service_registry"
]
