"""
Order Entity
===========

订单实体，表示交易系统中的订单信息。
"""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, Any
from dataclasses import dataclass, field

from ..enums import Direction, Offset, OrderStatus, OrderType, PriceType
from ..constants import MIN_VOLUME, MAX_VOLUME, MIN_PRICE, MAX_PRICE


@dataclass
class Order:
    """订单实体"""
    
    # 基础信息
    order_id: str = field(default_factory=lambda: f"ORDER_{uuid.uuid4().hex[:8]}")
    symbol: str = ""
    exchange: str = ""
    product: str = ""
    
    # 交易信息
    direction: Direction = Direction.LONG
    offset: Offset = Offset.OPEN
    order_type: OrderType = OrderType.LIMIT
    price_type: PriceType = PriceType.LIMIT
    
    # 数量和价格
    volume: int = 0
    price: Optional[Decimal] = None
    stop_price: Optional[Decimal] = None
    
    # 状态信息
    status: OrderStatus = OrderStatus.SUBMITTING
    submitted_volume: int = 0
    traded_volume: int = 0
    remaining_volume: int = 0
    
    # 时间信息
    create_time: datetime = field(default_factory=datetime.now)
    submit_time: Optional[datetime] = None
    cancel_time: Optional[datetime] = None
    update_time: datetime = field(default_factory=datetime.now)
    
    # 费用信息
    commission: Decimal = Decimal("0")
    slippage: Decimal = Decimal("0")
    
    # 扩展信息
    gateway_name: str = ""
    strategy_name: str = ""
    user_id: str = ""
    remark: str = ""
    
    # 内部状态
    _is_validated: bool = False
    _validation_errors: list[str] = field(default_factory=list)
    
    def __post_init__(self):
        """初始化后处理"""
        self.remaining_volume = self.volume
        self._validate_order()
    
    def _validate_order(self) -> bool:
        """验证订单有效性"""
        self._validation_errors.clear()
        
        # 验证基础信息
        if not self.symbol:
            self._validation_errors.append("交易品种不能为空")
        
        if not self.exchange:
            self._validation_errors.append("交易所不能为空")
        
        # 验证数量
        if self.volume < MIN_VOLUME:
            self._validation_errors.append(f"交易数量不能小于{MIN_VOLUME}")
        
        if self.volume > MAX_VOLUME:
            self._validation_errors.append(f"交易数量不能大于{MAX_VOLUME}")
        
        # 验证价格
        if self.order_type in [OrderType.LIMIT, OrderType.STOP_LIMIT]:
            if self.price is None:
                self._validation_errors.append("限价单必须指定价格")
            elif self.price < MIN_PRICE:
                self._validation_errors.append(f"价格不能小于{MIN_PRICE}")
            elif self.price > MAX_PRICE:
                self._validation_errors.append(f"价格不能大于{MAX_PRICE}")
        
        # 验证止损单
        if self.order_type in [OrderType.STOP, OrderType.STOP_LIMIT]:
            if self.stop_price is None:
                self._validation_errors.append("止损单必须指定止损价格")
        
        # 验证开平标志
        if self.direction == Direction.NET and self.offset != Offset.OPEN:
            self._validation_errors.append("净持仓方向只能开仓")
        
        self._is_validated = len(self._validation_errors) == 0
        return self._is_validated
    
    def is_valid(self) -> bool:
        """检查订单是否有效"""
        return self._is_validated
    
    def get_validation_errors(self) -> list[str]:
        """获取验证错误信息"""
        return self._validation_errors.copy()
    
    def submit(self) -> bool:
        """提交订单"""
        if not self.is_valid():
            return False
        
        if self.status != OrderStatus.SUBMITTING:
            return False
        
        self.status = OrderStatus.SUBMITTED
        self.submit_time = datetime.now()
        self.update_time = datetime.now()
        return True
    
    def cancel(self) -> bool:
        """撤销订单"""
        if self.status not in [OrderStatus.SUBMITTED, OrderStatus.PARTTRADED]:
            return False
        
        self.status = OrderStatus.CANCELLED
        self.cancel_time = datetime.now()
        self.update_time = datetime.now()
        return True
    
    def update_trade(self, trade_volume: int, trade_price: Decimal) -> bool:
        """更新成交信息"""
        if trade_volume <= 0:
            return False
        
        if trade_volume > self.remaining_volume:
            return False
        
        self.traded_volume += trade_volume
        self.remaining_volume -= trade_volume
        self.update_time = datetime.now()
        
        # 更新状态
        if self.remaining_volume == 0:
            self.status = OrderStatus.ALLTRADED
        elif self.traded_volume > 0:
            self.status = OrderStatus.PARTTRADED
        
        return True
    
    def reject(self, reason: str = "") -> bool:
        """拒绝订单"""
        if self.status != OrderStatus.SUBMITTING:
            return False
        
        self.status = OrderStatus.REJECTED
        self.remark = reason
        self.update_time = datetime.now()
        return True
    
    def get_total_amount(self) -> Decimal:
        """获取订单总金额"""
        if self.price is None:
            return Decimal("0")
        return self.price * self.volume
    
    def get_traded_amount(self) -> Decimal:
        """获取已成交金额"""
        if self.price is None:
            return Decimal("0")
        return self.price * self.traded_volume
    
    def get_remaining_amount(self) -> Decimal:
        """获取剩余金额"""
        if self.price is None:
            return Decimal("0")
        return self.price * self.remaining_volume
    
    def is_active(self) -> bool:
        """检查订单是否活跃"""
        return self.status in [OrderStatus.SUBMITTED, OrderStatus.PARTTRADED]
    
    def is_finished(self) -> bool:
        """检查订单是否完成"""
        return self.status in [OrderStatus.ALLTRADED, OrderStatus.CANCELLED, OrderStatus.REJECTED, OrderStatus.EXPIRED]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "order_id": self.order_id,
            "symbol": self.symbol,
            "exchange": self.exchange,
            "product": self.product,
            "direction": self.direction.value,
            "offset": self.offset.value,
            "order_type": self.order_type.value,
            "price_type": self.price_type.value,
            "volume": self.volume,
            "price": float(self.price) if self.price else None,
            "stop_price": float(self.stop_price) if self.stop_price else None,
            "status": self.status.value,
            "submitted_volume": self.submitted_volume,
            "traded_volume": self.traded_volume,
            "remaining_volume": self.remaining_volume,
            "create_time": self.create_time.isoformat(),
            "submit_time": self.submit_time.isoformat() if self.submit_time else None,
            "cancel_time": self.cancel_time.isoformat() if self.cancel_time else None,
            "update_time": self.update_time.isoformat(),
            "commission": float(self.commission),
            "slippage": float(self.slippage),
            "gateway_name": self.gateway_name,
            "strategy_name": self.strategy_name,
            "user_id": self.user_id,
            "remark": self.remark,
            "is_valid": self.is_valid(),
            "validation_errors": self._validation_errors
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Order':
        """从字典创建订单"""
        # 处理枚举类型
        if 'direction' in data and isinstance(data['direction'], str):
            data['direction'] = Direction(data['direction'])
        
        if 'offset' in data and isinstance(data['offset'], str):
            data['offset'] = Offset(data['offset'])
        
        if 'order_type' in data and isinstance(data['order_type'], str):
            data['order_type'] = OrderType(data['order_type'])
        
        if 'price_type' in data and isinstance(data['price_type'], str):
            data['price_type'] = PriceType(data['price_type'])
        
        if 'status' in data and isinstance(data['status'], str):
            data['status'] = OrderStatus(data['status'])
        
        # 处理时间类型
        if 'create_time' in data and isinstance(data['create_time'], str):
            data['create_time'] = datetime.fromisoformat(data['create_time'])
        
        if 'submit_time' in data and isinstance(data['submit_time'], str):
            data['submit_time'] = datetime.fromisoformat(data['submit_time'])
        
        if 'cancel_time' in data and isinstance(data['cancel_time'], str):
            data['cancel_time'] = datetime.fromisoformat(data['cancel_time'])
        
        if 'update_time' in data and isinstance(data['update_time'], str):
            data['update_time'] = datetime.fromisoformat(data['update_time'])
        
        # 处理Decimal类型
        if 'price' in data and data['price'] is not None:
            data['price'] = Decimal(str(data['price']))
        
        if 'stop_price' in data and data['stop_price'] is not None:
            data['stop_price'] = Decimal(str(data['stop_price']))
        
        if 'commission' in data:
            data['commission'] = Decimal(str(data['commission']))
        
        if 'slippage' in data:
            data['slippage'] = Decimal(str(data['slippage']))
        
        return cls(**data)
