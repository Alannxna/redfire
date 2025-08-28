"""
配置标准模块
============

配置标准和规范定义
"""

from .path_standards import (
    ConfigPathStandard,
    get_standard_config_path,
    validate_config_path
)

__all__ = [
    'ConfigPathStandard',
    'get_standard_config_path',
    'validate_config_path'
]
