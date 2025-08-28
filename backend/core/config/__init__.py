"""
统一配置管理模块
==================

提供统一的配置管理架构，支持多环境、分层配置和热重载
"""

from .base_config import BaseConfig
from .app_config import AppConfig
from .config_manager import CoreConfigManager
from .environment_config import EnvironmentConfig, DevelopmentConfig, ProductionConfig

# 全局配置管理器实例
_config_manager = None

def get_config_manager() -> CoreConfigManager:
    """获取全局配置管理器实例"""
    global _config_manager
    if _config_manager is None:
        _config_manager = CoreConfigManager()
    return _config_manager

def get_app_config() -> AppConfig:
    """获取应用配置"""
    return get_config_manager().get_app_config()

__all__ = [
    'BaseConfig',
    'AppConfig', 
    'CoreConfigManager',
    'EnvironmentConfig',
    'DevelopmentConfig',
    'ProductionConfig',
    'get_config_manager',
    'get_app_config'
]
