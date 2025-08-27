"""
RedFire 量化策略模块

企业级量化策略开发框架，提供：
- 统一的策略开发基类和接口
- 高性能策略执行引擎
- 专业回测和模拟交易引擎
- 智能风险管理系统
- 实时绩效分析和监控
- 策略生命周期管理
"""

from .core.strategy_base import BaseStrategy, StrategyState, StrategyType
from .core.strategy_engine import StrategyEngine, StrategyManager
from .core.backtest_engine import BacktestEngine
from .core.risk_manager import RiskManager
from .core.performance_analyzer import PerformanceAnalyzer
from .integration.strategy_integration import setup_strategy_system

__version__ = "1.0.0"
__author__ = "RedFire Team"

__all__ = [
    "BaseStrategy",
    "StrategyState", 
    "StrategyType",
    "StrategyEngine",
    "StrategyManager",
    "BacktestEngine",
    "RiskManager",
    "PerformanceAnalyzer",
    "setup_strategy_system",
]
