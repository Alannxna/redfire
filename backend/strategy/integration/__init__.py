"""
量化策略系统集成模块

提供策略系统的一键集成和配置功能
"""

from .strategy_integration import StrategySystem, setup_strategy_system, create_sample_strategy

__all__ = [
    "StrategySystem",
    "setup_strategy_system", 
    "create_sample_strategy"
]
