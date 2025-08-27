"""
状态枚举 - 包括订单状态、成交状态、持仓状态等
"""

from enum import Enum
from typing import Dict


class Status(Enum):
    """通用状态枚举基类"""
    pass


class OrderStatus(Status):
    """订单状态枚举"""
    
    SUBMITTING = "SUBMITTING"      # 提交中
    NOTTRADED = "NOTTRADED"        # 未成交
    PARTTRADED = "PARTTRADED"      # 部分成交
    ALLTRADED = "ALLTRADED"        # 全部成交
    CANCELLED = "CANCELLED"        # 已撤销
    REJECTED = "REJECTED"          # 已拒绝
    
    @property
    def chinese_name(self) -> str:
        """获取中文名称"""
        return self._chinese_mapping()[self]
    
    @classmethod
    def _chinese_mapping(cls) -> Dict["OrderStatus", str]:
        """中文名称映射"""
        return {
            cls.SUBMITTING: "提交中",
            cls.NOTTRADED: "未成交",
            cls.PARTTRADED: "部分成交",
            cls.ALLTRADED: "全部成交",
            cls.CANCELLED: "已撤销",
            cls.REJECTED: "已拒绝",
        }
    
    @classmethod
    def from_string(cls, value: str) -> "OrderStatus":
        """从字符串创建OrderStatus对象"""
        value = value.upper()
        for status in cls:
            if status.value == value:
                return status
        raise ValueError(f"Invalid order status: {value}")
    
    def __str__(self) -> str:
        return self.value
    
    def __repr__(self) -> str:
        return f"OrderStatus.{self.name}"
    
    @property
    def is_active(self) -> bool:
        """订单是否活跃（可交易）"""
        return self in (OrderStatus.SUBMITTING, OrderStatus.NOTTRADED, OrderStatus.PARTTRADED)
    
    @property
    def is_finished(self) -> bool:
        """订单是否已结束"""
        return self in (OrderStatus.ALLTRADED, OrderStatus.CANCELLED, OrderStatus.REJECTED)
    
    @property
    def is_traded(self) -> bool:
        """订单是否有成交"""
        return self in (OrderStatus.PARTTRADED, OrderStatus.ALLTRADED)


class TradeStatus(Status):
    """成交状态枚举"""
    
    TRADED = "TRADED"              # 已成交
    CANCELLED = "CANCELLED"        # 已撤销
    
    @property
    def chinese_name(self) -> str:
        """获取中文名称"""
        return self._chinese_mapping()[self]
    
    @classmethod
    def _chinese_mapping(cls) -> Dict["TradeStatus", str]:
        """中文名称映射"""
        return {
            cls.TRADED: "已成交",
            cls.CANCELLED: "已撤销",
        }
    
    @classmethod
    def from_string(cls, value: str) -> "TradeStatus":
        """从字符串创建TradeStatus对象"""
        value = value.upper()
        for status in cls:
            if status.value == value:
                return status
        raise ValueError(f"Invalid trade status: {value}")
    
    def __str__(self) -> str:
        return self.value
    
    def __repr__(self) -> str:
        return f"TradeStatus.{self.name}"


class PositionStatus(Status):
    """持仓状态枚举"""
    
    OPEN = "OPEN"                  # 开仓
    CLOSED = "CLOSED"              # 已平仓
    
    @property
    def chinese_name(self) -> str:
        """获取中文名称"""
        return self._chinese_mapping()[self]
    
    @classmethod
    def _chinese_mapping(cls) -> Dict["PositionStatus", str]:
        """中文名称映射"""
        return {
            cls.OPEN: "持仓中",
            cls.CLOSED: "已平仓",
        }
    
    @classmethod
    def from_string(cls, value: str) -> "PositionStatus":
        """从字符串创建PositionStatus对象"""
        value = value.upper()
        for status in cls:
            if status.value == value:
                return status
        raise ValueError(f"Invalid position status: {value}")
    
    def __str__(self) -> str:
        return self.value
    
    def __repr__(self) -> str:
        return f"PositionStatus.{self.name}"
    
    @property
    def is_open(self) -> bool:
        """是否为开仓状态"""
        return self == PositionStatus.OPEN
    
    @property
    def is_closed(self) -> bool:
        """是否为平仓状态"""
        return self == PositionStatus.CLOSED
