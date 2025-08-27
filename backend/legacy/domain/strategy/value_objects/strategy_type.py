"""
策略类型值对象
"""

from enum import Enum


class StrategyType(str, Enum):
    """策略类型"""
    CTA = "cta"
    PORTFOLIO = "portfolio"
    SPREAD = "spread"
    OPTION = "option"
    SCRIPT = "script"
    CUSTOM = "custom"
