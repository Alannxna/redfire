"""
量化策略示例

提供各种类型的策略示例，帮助用户快速上手策略开发。
"""

from .simple_ma_strategy import SimpleMAStrategy, create_simple_ma_strategy

__all__ = [
    "SimpleMAStrategy",
    "create_simple_ma_strategy"
]
