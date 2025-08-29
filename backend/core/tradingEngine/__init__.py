"""
交易引擎模块 (Trading Engine Module)

本模块提供了完整的交易引擎功能，包括：
- 主交易引擎 (MainTradingEngine)
- 事件交易引擎 (EventTradingEngine) 
- 基础交易引擎 (BaseTradingEngine)
- 基础交易应用 (BaseTradingApp)
- 引擎管理器 (EngineManager)
- 插件管理器 (PluginManager)

从 vnpy-core 迁移而来，采用更清晰的命名规范和架构设计。
"""

from .mainEngine import MainTradingEngine
from .eventEngine import EventTradingEngine
from .baseEngine import BaseTradingEngine
from .appBase import BaseTradingApp
from .engineManager import EngineManager
from .pluginManager import PluginManager

__all__ = [
    'MainTradingEngine',
    'EventTradingEngine', 
    'BaseTradingEngine',
    'BaseTradingApp',
    'EngineManager',
    'PluginManager'
]

__version__ = '1.0.0'
__author__ = 'RedFire Team'
