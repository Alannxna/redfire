"""
价格类型枚举
"""

from enum import Enum
from typing import Dict


class PriceType(Enum):
    """价格类型枚举"""
    
    LIMIT = "LIMIT"                # 限价
    MARKET = "MARKET"              # 市价
    STOP = "STOP"                  # 止损价
    BEST = "BEST"                  # 最优价
    LAST = "LAST"                  # 最新价
    ASK = "ASK"                    # 卖一价
    BID = "BID"                    # 买一价
    MIDPOINT = "MIDPOINT"          # 中间价
    VWAP = "VWAP"                  # 成交量加权平均价
    TWAP = "TWAP"                  # 时间加权平均价
    
    @property
    def chinese_name(self) -> str:
        """获取中文名称"""
        return self._chinese_mapping()[self]
    
    @classmethod
    def _chinese_mapping(cls) -> Dict["PriceType", str]:
        """中文名称映射"""
        return {
            cls.LIMIT: "限价",
            cls.MARKET: "市价",
            cls.STOP: "止损价",
            cls.BEST: "最优价",
            cls.LAST: "最新价",
            cls.ASK: "卖一价",
            cls.BID: "买一价",
            cls.MIDPOINT: "中间价",
            cls.VWAP: "成交量加权平均价",
            cls.TWAP: "时间加权平均价",
        }
    
    @classmethod
    def from_string(cls, value: str) -> "PriceType":
        """从字符串创建PriceType对象"""
        value = value.upper()
        for price_type in cls:
            if price_type.value == value:
                return price_type
        raise ValueError(f"Invalid price type: {value}")
    
    def __str__(self) -> str:
        return self.value
    
    def __repr__(self) -> str:
        return f"PriceType.{self.name}"
    
    @property
    def requires_explicit_price(self) -> bool:
        """是否需要显式指定价格"""
        return self in (PriceType.LIMIT, PriceType.STOP)
    
    @property
    def is_market_price(self) -> bool:
        """是否为市场价格类型"""
        return self in (PriceType.MARKET, PriceType.BEST, PriceType.ASK, PriceType.BID)
    
    @property
    def is_reference_price(self) -> bool:
        """是否为参考价格类型"""
        return self in (PriceType.LAST, PriceType.MIDPOINT, PriceType.VWAP, PriceType.TWAP)
    
    @property
    def is_algorithmic_price(self) -> bool:
        """是否为算法价格类型"""
        return self in (PriceType.VWAP, PriceType.TWAP)
    
    @property
    def execution_urgency(self) -> int:
        """获取执行紧急程度 (1-10, 10最紧急)"""
        urgency_mapping = {
            PriceType.MARKET: 10,      # 市价最紧急
            PriceType.BEST: 9,         # 最优价很紧急
            PriceType.ASK: 8,          # 卖一价较紧急
            PriceType.BID: 8,          # 买一价较紧急
            PriceType.LAST: 6,         # 最新价中等
            PriceType.MIDPOINT: 5,     # 中间价中等
            PriceType.LIMIT: 3,        # 限价较慢
            PriceType.STOP: 7,         # 止损价较紧急
            PriceType.VWAP: 4,         # VWAP较慢
            PriceType.TWAP: 2,         # TWAP最慢
        }
        return urgency_mapping.get(self, 5)
