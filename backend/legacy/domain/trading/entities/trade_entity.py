"""
Trade Entity
===========

成交实体，表示交易系统中的成交信息。
"""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, Any
from dataclasses import dataclass, field

from ..enums import Direction, Offset, TradeStatus
from ..constants import AMOUNT_PRECISION


@dataclass
class Trade:
    """成交实体"""
    
    # 基础信息
    trade_id: str = field(default_factory=lambda: f"TRADE_{uuid.uuid4().hex[:8]}")
    order_id: str = ""
    symbol: str = ""
    exchange: str = ""
    product: str = ""
    
    # 交易信息
    direction: Direction = Direction.LONG
    offset: Offset = Offset.OPEN
    volume: int = 0
    price: Decimal = Decimal("0")
    
    # 状态信息
    status: TradeStatus = TradeStatus.PENDING
    
    # 时间信息
    trade_time: datetime = field(default_factory=datetime.now)
    create_time: datetime = field(default_factory=datetime.now)
    update_time: datetime = field(default_factory=datetime.now)
    
    # 费用信息
    commission: Decimal = Decimal("0")
    slippage: Decimal = Decimal("0")
    
    # 扩展信息
    gateway_name: str = ""
    strategy_name: str = ""
    user_id: str = ""
    remark: str = ""
    
    def __post_init__(self):
        """初始化后处理"""
        self.update_time = datetime.now()
    
    def get_amount(self) -> Decimal:
        """获取成交金额"""
        return self.price * self.volume
    
    def get_total_cost(self) -> Decimal:
        """获取总成本（包含费用）"""
        return self.get_amount() + self.commission + self.slippage
    
    def confirm(self) -> bool:
        """确认成交"""
        if self.status != TradeStatus.PENDING:
            return False
        
        self.status = TradeStatus.CONFIRMED
        self.update_time = datetime.now()
        return True
    
    def cancel(self) -> bool:
        """取消成交"""
        if self.status != TradeStatus.PENDING:
            return False
        
        self.status = TradeStatus.CANCELLED
        self.update_time = datetime.now()
        return True
    
    def reject(self, reason: str = "") -> bool:
        """拒绝成交"""
        if self.status != TradeStatus.PENDING:
            return False
        
        self.status = TradeStatus.REJECTED
        self.remark = reason
        self.update_time = datetime.now()
        return True
    
    def is_confirmed(self) -> bool:
        """检查是否已确认"""
        return self.status == TradeStatus.CONFIRMED
    
    def is_cancelled(self) -> bool:
        """检查是否已取消"""
        return self.status == TradeStatus.CANCELLED
    
    def is_rejected(self) -> bool:
        """检查是否已拒绝"""
        return self.status == TradeStatus.REJECTED
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "trade_id": self.trade_id,
            "order_id": self.order_id,
            "symbol": self.symbol,
            "exchange": self.exchange,
            "product": self.product,
            "direction": self.direction.value,
            "offset": self.offset.value,
            "volume": self.volume,
            "price": float(self.price),
            "status": self.status.value,
            "trade_time": self.trade_time.isoformat(),
            "create_time": self.create_time.isoformat(),
            "update_time": self.update_time.isoformat(),
            "commission": float(self.commission),
            "slippage": float(self.slippage),
            "gateway_name": self.gateway_name,
            "strategy_name": self.strategy_name,
            "user_id": self.user_id,
            "remark": self.remark,
            "amount": float(self.get_amount()),
            "total_cost": float(self.get_total_cost())
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Trade':
        """从字典创建成交"""
        # 处理枚举类型
        if 'direction' in data and isinstance(data['direction'], str):
            data['direction'] = Direction(data['direction'])
        
        if 'offset' in data and isinstance(data['offset'], str):
            data['offset'] = Offset(data['offset'])
        
        if 'status' in data and isinstance(data['status'], str):
            data['status'] = TradeStatus(data['status'])
        
        # 处理时间类型
        if 'trade_time' in data and isinstance(data['trade_time'], str):
            data['trade_time'] = datetime.fromisoformat(data['trade_time'])
        
        if 'create_time' in data and isinstance(data['create_time'], str):
            data['create_time'] = datetime.fromisoformat(data['create_time'])
        
        if 'update_time' in data and isinstance(data['update_time'], str):
            data['update_time'] = datetime.fromisoformat(data['update_time'])
        
        # 处理Decimal类型
        if 'price' in data:
            data['price'] = Decimal(str(data['price']))
        
        if 'commission' in data:
            data['commission'] = Decimal(str(data['commission']))
        
        if 'slippage' in data:
            data['slippage'] = Decimal(str(data['slippage']))
        
        return cls(**data)
