"""
Position Entity
==============

持仓实体，表示交易系统中的持仓信息。
"""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, Any
from dataclasses import dataclass, field

from ..enums import PositionStatus
from ..constants import AMOUNT_PRECISION


@dataclass
class Position:
    """持仓实体"""
    
    # 基础信息
    position_id: str = field(default_factory=lambda: f"POS_{uuid.uuid4().hex[:8]}")
    symbol: str = ""
    exchange: str = ""
    product: str = ""
    user_id: str = ""
    
    # 持仓信息
    long_volume: int = 0
    short_volume: int = 0
    long_avg_price: Decimal = Decimal("0")
    short_avg_price: Decimal = Decimal("0")
    
    # 盈亏信息
    unrealized_pnl: Decimal = Decimal("0")
    realized_pnl: Decimal = Decimal("0")
    daily_pnl: Decimal = Decimal("0")
    total_pnl: Decimal = Decimal("0")
    
    # 状态信息
    status: PositionStatus = PositionStatus.ACTIVE
    
    # 时间信息
    create_time: datetime = field(default_factory=datetime.now)
    update_time: datetime = field(default_factory=datetime.now)
    last_trade_time: Optional[datetime] = None
    
    # 扩展信息
    gateway_name: str = ""
    strategy_name: str = ""
    remark: str = ""
    
    def __post_init__(self):
        """初始化后处理"""
        self.update_time = datetime.now()
    
    @property
    def net_volume(self) -> int:
        """净持仓数量"""
        return self.long_volume - self.short_volume
    
    @property
    def is_long(self) -> bool:
        """是否多头持仓"""
        return self.long_volume > self.short_volume
    
    @property
    def is_short(self) -> bool:
        """是否空头持仓"""
        return self.short_volume > self.long_volume
    
    @property
    def is_flat(self) -> bool:
        """是否平仓"""
        return self.long_volume == self.short_volume
    
    @property
    def total_volume(self) -> int:
        """总持仓数量"""
        return self.long_volume + self.short_volume
    
    def calculate_pnl(self, current_price: Optional[Decimal] = None) -> None:
        """计算盈亏"""
        if current_price is None:
            # 如果没有当前价格，使用平均价格计算
            current_price = self.long_avg_price if self.is_long else self.short_avg_price
        
        if current_price is None:
            return
        
        # 计算未实现盈亏
        if self.is_long:
            self.unrealized_pnl = (current_price - self.long_avg_price) * self.long_volume
        elif self.is_short:
            self.unrealized_pnl = (self.short_avg_price - current_price) * self.short_volume
        else:
            self.unrealized_pnl = Decimal("0")
        
        # 总盈亏 = 未实现盈亏 + 已实现盈亏
        self.total_pnl = self.unrealized_pnl + self.realized_pnl
        
        # 更新每日盈亏（这里简化处理，实际应该按日期计算）
        self.daily_pnl = self.total_pnl
    
    def update_position(
        self,
        direction: str,
        volume: int,
        price: Decimal,
        is_open: bool = True
    ) -> None:
        """更新持仓"""
        if is_open:
            # 开仓
            if direction == "LONG":
                old_volume = self.long_volume
                old_price = self.long_avg_price
                self.long_volume += volume
                
                if old_volume == 0:
                    self.long_avg_price = price
                else:
                    total_amount = old_volume * old_price + volume * price
                    self.long_avg_price = total_amount / self.long_volume
            else:  # SHORT
                old_volume = self.short_volume
                old_price = self.short_avg_price
                self.short_volume += volume
                
                if old_volume == 0:
                    self.short_avg_price = price
                else:
                    total_amount = old_volume * old_price + volume * price
                    self.short_avg_price = total_amount / self.short_volume
        else:
            # 平仓
            if direction == "LONG":
                # 平多仓
                if self.short_volume >= volume:
                    self.short_volume -= volume
                    # 计算已实现盈亏
                    realized_pnl = (self.short_avg_price - price) * volume
                    self.realized_pnl += realized_pnl
                else:
                    # 平仓数量超过持仓数量
                    remaining_volume = volume - self.short_volume
                    self.short_volume = 0
                    # 计算已实现盈亏
                    realized_pnl = (self.short_avg_price - price) * (volume - remaining_volume)
                    self.realized_pnl += realized_pnl
                    
                    # 剩余数量转为开多仓
                    old_volume = self.long_volume
                    old_price = self.long_avg_price
                    self.long_volume += remaining_volume
                    
                    if old_volume == 0:
                        self.long_avg_price = price
                    else:
                        total_amount = old_volume * old_price + remaining_volume * price
                        self.long_avg_price = total_amount / self.long_volume
            else:  # SHORT
                # 平空仓
                if self.long_volume >= volume:
                    self.long_volume -= volume
                    # 计算已实现盈亏
                    realized_pnl = (price - self.long_avg_price) * volume
                    self.realized_pnl += realized_pnl
                else:
                    # 平仓数量超过持仓数量
                    remaining_volume = volume - self.long_volume
                    self.long_volume = 0
                    # 计算已实现盈亏
                    realized_pnl = (price - self.long_avg_price) * (volume - remaining_volume)
                    self.realized_pnl += realized_pnl
                    
                    # 剩余数量转为开空仓
                    old_volume = self.short_volume
                    old_price = self.short_avg_price
                    self.short_volume += remaining_volume
                    
                    if old_volume == 0:
                        self.short_avg_price = price
                    else:
                        total_amount = old_volume * old_price + remaining_volume * price
                        self.short_avg_price = total_amount / self.short_volume
        
        # 更新时间和状态
        self.update_time = datetime.now()
        self.last_trade_time = datetime.now()
        
        # 重新计算盈亏
        self.calculate_pnl()
    
    def reset_daily_pnl(self) -> None:
        """重置每日盈亏"""
        self.daily_pnl = Decimal("0")
    
    def close_position(self) -> None:
        """平仓"""
        self.long_volume = 0
        self.short_volume = 0
        self.long_avg_price = Decimal("0")
        self.short_avg_price = Decimal("0")
        self.unrealized_pnl = Decimal("0")
        self.status = PositionStatus.CLOSED
        self.update_time = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "position_id": self.position_id,
            "symbol": self.symbol,
            "exchange": self.exchange,
            "product": self.product,
            "user_id": self.user_id,
            "long_volume": self.long_volume,
            "short_volume": self.short_volume,
            "long_avg_price": float(self.long_avg_price),
            "short_avg_price": float(self.short_avg_price),
            "net_volume": self.net_volume,
            "total_volume": self.total_volume,
            "is_long": self.is_long,
            "is_short": self.is_short,
            "is_flat": self.is_flat,
            "unrealized_pnl": float(self.unrealized_pnl),
            "realized_pnl": float(self.realized_pnl),
            "daily_pnl": float(self.daily_pnl),
            "total_pnl": float(self.total_pnl),
            "status": self.status.value,
            "create_time": self.create_time.isoformat(),
            "update_time": self.update_time.isoformat(),
            "last_trade_time": self.last_trade_time.isoformat() if self.last_trade_time else None,
            "gateway_name": self.gateway_name,
            "strategy_name": self.strategy_name,
            "remark": self.remark
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Position':
        """从字典创建持仓"""
        # 处理枚举类型
        if 'status' in data and isinstance(data['status'], str):
            data['status'] = PositionStatus(data['status'])
        
        # 处理时间类型
        if 'create_time' in data and isinstance(data['create_time'], str):
            data['create_time'] = datetime.fromisoformat(data['create_time'])
        
        if 'update_time' in data and isinstance(data['update_time'], str):
            data['update_time'] = datetime.fromisoformat(data['update_time'])
        
        if 'last_trade_time' in data and isinstance(data['last_trade_time'], str):
            data['last_trade_time'] = datetime.fromisoformat(data['last_trade_time'])
        
        # 处理Decimal类型
        if 'long_avg_price' in data:
            data['long_avg_price'] = Decimal(str(data['long_avg_price']))
        
        if 'short_avg_price' in data:
            data['short_avg_price'] = Decimal(str(data['short_avg_price']))
        
        if 'unrealized_pnl' in data:
            data['unrealized_pnl'] = Decimal(str(data['unrealized_pnl']))
        
        if 'realized_pnl' in data:
            data['realized_pnl'] = Decimal(str(data['realized_pnl']))
        
        if 'daily_pnl' in data:
            data['daily_pnl'] = Decimal(str(data['daily_pnl']))
        
        if 'total_pnl' in data:
            data['total_pnl'] = Decimal(str(data['total_pnl']))
        
        return cls(**data)
