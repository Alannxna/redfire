"""
交易引擎适配器模块

提供与各种外部交易系统的集成适配器，包括：
- VnPy官方引擎适配器
- 其他第三方交易系统适配器
"""

from .vnpy_adapter import VnPyEngineAdapter, VnPyConfig, VnPyIntegrationMode

__all__ = [
    'VnPyEngineAdapter',
    'VnPyConfig', 
    'VnPyIntegrationMode'
]
