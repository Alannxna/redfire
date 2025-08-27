"""
交易方向枚举
"""

from enum import Enum
from typing import Dict


class Direction(Enum):
    """交易方向枚举"""
    
    BUY = "BUY"      # 买入
    SELL = "SELL"    # 卖出
    
    @property
    def chinese_name(self) -> str:
        """获取中文名称"""
        return self._chinese_mapping()[self]
    
    @classmethod
    def _chinese_mapping(cls) -> Dict["Direction", str]:
        """中文名称映射"""
        return {
            cls.BUY: "买入",
            cls.SELL: "卖出",
        }
    
    @classmethod
    def from_string(cls, value: str) -> "Direction":
        """从字符串创建Direction对象"""
        value = value.upper()
        for direction in cls:
            if direction.value == value:
                return direction
        raise ValueError(f"Invalid direction: {value}")
    
    def __str__(self) -> str:
        return self.value
    
    def __repr__(self) -> str:
        return f"Direction.{self.name}"
    
    @property
    def is_buy(self) -> bool:
        """是否为买入方向"""
        return self == Direction.BUY
    
    @property
    def is_sell(self) -> bool:
        """是否为卖出方向"""
        return self == Direction.SELL
    
    @property
    def opposite(self) -> "Direction":
        """获取相反方向"""
        if self == Direction.BUY:
            return Direction.SELL
        return Direction.BUY
