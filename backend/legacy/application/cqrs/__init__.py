"""
CQRS模块
========

提供完整的CQRS架构支持，包括命令查询总线、处理器自动注册和配置管理
"""

# 标准库导入

# 应用层内部导入
from .cqrs_configuration_manager import (
    CQRSConfigurationManager,
    CQRSHandlerRegistry,
    CQRSAutoDiscovery,
    CQRSModuleInfo,
    get_cqrs_manager,
    set_cqrs_manager,
    initialize_cqrs
)

__all__ = [
    "CQRSConfigurationManager",
    "CQRSHandlerRegistry", 
    "CQRSAutoDiscovery",
    "CQRSModuleInfo",
    "get_cqrs_manager",
    "set_cqrs_manager", 
    "initialize_cqrs"
]
