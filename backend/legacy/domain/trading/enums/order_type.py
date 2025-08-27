"""
订单类型枚举
"""

from enum import Enum
from typing import Dict


class OrderType(Enum):
    """订单类型枚举"""
    
    LIMIT = "LIMIT"                # 限价单
    MARKET = "MARKET"              # 市价单
    STOP = "STOP"                  # 止损单
    STOP_LIMIT = "STOP_LIMIT"      # 止损限价单
    FAK = "FAK"                    # Fill and Kill (部成即撤)
    FOK = "FOK"                    # Fill or Kill (全成或撤)
    IOC = "IOC"                    # Immediate or Cancel (立即成交或撤销)
    GTC = "GTC"                    # Good Till Cancel (取消前有效)
    GTD = "GTD"                    # Good Till Date (指定日期前有效)
    
    @property
    def chinese_name(self) -> str:
        """获取中文名称"""
        return self._chinese_mapping()[self]
    
    @classmethod
    def _chinese_mapping(cls) -> Dict["OrderType", str]:
        """中文名称映射"""
        return {
            cls.LIMIT: "限价单",
            cls.MARKET: "市价单",
            cls.STOP: "止损单",
            cls.STOP_LIMIT: "止损限价单",
            cls.FAK: "部成即撤",
            cls.FOK: "全成或撤",
            cls.IOC: "立即成交或撤销",
            cls.GTC: "取消前有效",
            cls.GTD: "指定日期前有效",
        }
    
    @classmethod
    def from_string(cls, value: str) -> "OrderType":
        """从字符串创建OrderType对象"""
        value = value.upper()
        for order_type in cls:
            if order_type.value == value:
                return order_type
        raise ValueError(f"Invalid order type: {value}")
    
    def __str__(self) -> str:
        return self.value
    
    def __repr__(self) -> str:
        return f"OrderType.{self.name}"
    
    @property
    def is_market_order(self) -> bool:
        """是否为市价单"""
        return self == OrderType.MARKET
    
    @property
    def is_limit_order(self) -> bool:
        """是否为限价单"""
        return self in (OrderType.LIMIT, OrderType.STOP_LIMIT)
    
    @property
    def is_stop_order(self) -> bool:
        """是否为止损单"""
        return self in (OrderType.STOP, OrderType.STOP_LIMIT)
    
    @property
    def is_immediate_order(self) -> bool:
        """是否为立即执行订单"""
        return self in (OrderType.MARKET, OrderType.FAK, OrderType.FOK, OrderType.IOC)
    
    @property
    def requires_price(self) -> bool:
        """是否需要指定价格"""
        return self in (OrderType.LIMIT, OrderType.STOP_LIMIT)
    
    @property
    def requires_stop_price(self) -> bool:
        """是否需要指定止损价格"""
        return self in (OrderType.STOP, OrderType.STOP_LIMIT)
    
    @property
    def allows_partial_fill(self) -> bool:
        """是否允许部分成交"""
        return self not in (OrderType.FOK,)  # FOK必须全部成交
    
    @property
    def time_in_force(self) -> str:
        """获取订单时效类型"""
        if self in (OrderType.FAK, OrderType.IOC):
            return "IOC"
        elif self == OrderType.FOK:
            return "FOK"
        elif self == OrderType.GTC:
            return "GTC"
        elif self == OrderType.GTD:
            return "GTD"
        else:
            return "DAY"  # 默认当日有效
