"""
订单状态和类型枚举
==================

定义订单相关的统一枚举
"""

from enum import Enum


class OrderStatus(Enum):
    """订单状态枚举"""
    SUBMITTING = "submitting"
    SUBMITTED = "submitted"
    PARTIAL_FILLED = "partial_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    ERROR = "error"

    def __str__(self):
        return self.value

    @property
    def is_active(self) -> bool:
        """判断订单是否活跃（未完成）"""
        return self in [
            OrderStatus.SUBMITTING,
            OrderStatus.SUBMITTED,
            OrderStatus.PARTIAL_FILLED
        ]

    @property
    def is_finished(self) -> bool:
        """判断订单是否已完成"""
        return self in [
            OrderStatus.FILLED,
            OrderStatus.CANCELLED,
            OrderStatus.REJECTED,
            OrderStatus.ERROR
        ]

    @property
    def is_successful(self) -> bool:
        """判断订单是否成功"""
        return self in [OrderStatus.FILLED, OrderStatus.PARTIAL_FILLED]


class OrderType(Enum):
    """订单类型枚举"""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"
    FAK = "fak"  # Fill and Kill
    FOK = "fok"  # Fill or Kill

    def __str__(self):
        return self.value

    @property
    def requires_price(self) -> bool:
        """判断订单类型是否需要价格"""
        return self in [
            OrderType.LIMIT,
            OrderType.STOP,
            OrderType.STOP_LIMIT
        ]

    @property
    def is_market_order(self) -> bool:
        """判断是否为市价单"""
        return self == OrderType.MARKET


class Direction(Enum):
    """交易方向枚举"""
    LONG = "long"
    SHORT = "short"

    def __str__(self):
        return self.value

    @property
    def opposite(self) -> 'Direction':
        """获取相反方向"""
        return Direction.SHORT if self == Direction.LONG else Direction.LONG

    @property
    def multiplier(self) -> int:
        """获取方向乘数（用于计算）"""
        return 1 if self == Direction.LONG else -1
