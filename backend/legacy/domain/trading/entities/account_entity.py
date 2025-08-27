"""
Account Entity
=============

账户实体，表示交易系统中的账户信息。
"""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field

from ..constants import AMOUNT_PRECISION


@dataclass
class Account:
    """账户实体"""
    
    # 基础信息
    account_id: str = field(default_factory=lambda: f"ACCOUNT_{uuid.uuid4().hex[:8]}")
    user_id: str = ""
    account_name: str = ""
    account_type: str = "TRADING"  # TRADING, MARGIN, FUTURES
    
    # 资金信息
    balance: Decimal = Decimal("0")           # 账户余额
    available: Decimal = Decimal("0")         # 可用资金
    frozen: Decimal = Decimal("0")            # 冻结资金
    margin: Decimal = Decimal("0")            # 保证金
    risk_degree: Decimal = Decimal("0")       # 风险度
    
    # 盈亏信息
    daily_pnl: Decimal = Decimal("0")         # 当日盈亏
    total_pnl: Decimal = Decimal("0")         # 总盈亏
    realized_pnl: Decimal = Decimal("0")      # 已实现盈亏
    unrealized_pnl: Decimal = Decimal("0")    # 未实现盈亏
    
    # 持仓信息
    total_position_value: Decimal = Decimal("0")  # 总持仓市值
    total_market_value: Decimal = Decimal("0")    # 总市值
    
    # 状态信息
    is_active: bool = True
    is_trading: bool = False
    risk_level: str = "NORMAL"  # NORMAL, WARNING, DANGER
    
    # 时间信息
    create_time: datetime = field(default_factory=datetime.now)
    update_time: datetime = field(default_factory=datetime.now)
    last_trade_time: Optional[datetime] = None
    
    # 扩展信息
    broker: str = ""
    gateway_name: str = ""
    remark: str = ""
    
    def __post_init__(self):
        """初始化后处理"""
        self.update_time = datetime.now()
    
    @property
    def net_asset(self) -> Decimal:
        """净资产 = 余额 + 持仓市值"""
        return self.balance + self.total_position_value
    
    @property
    def margin_ratio(self) -> Decimal:
        """保证金比例 = 保证金 / 净资产"""
        if self.net_asset == 0:
            return Decimal("0")
        return self.margin / self.net_asset
    
    @property
    def position_ratio(self) -> Decimal:
        """持仓比例 = 持仓市值 / 净资产"""
        if self.net_asset == 0:
            return Decimal("0")
        return self.total_position_value / self.net_asset
    
    @property
    def available_ratio(self) -> Decimal:
        """可用资金比例 = 可用资金 / 净资产"""
        if self.net_asset == 0:
            return Decimal("0")
        return self.available / self.net_asset
    
    def can_trade(self, amount: Decimal) -> bool:
        """检查是否可以交易指定金额"""
        return self.is_active and self.is_trading and self.available >= amount
    
    def can_margin_trade(self, amount: Decimal, margin_required: Decimal) -> bool:
        """检查是否可以保证金交易"""
        if not self.can_trade(amount):
            return False
        
        # 检查可用资金
        if self.available < amount:
            return False
        
        # 检查保证金
        if self.available - amount < margin_required:
            return False
        
        return True
    
    def freeze_funds(self, amount: Decimal) -> bool:
        """冻结资金"""
        if amount <= 0 or amount > self.available:
            return False
        
        self.available -= amount
        self.frozen += amount
        self.update_time = datetime.now()
        return True
    
    def unfreeze_funds(self, amount: Decimal) -> bool:
        """解冻资金"""
        if amount <= 0 or amount > self.frozen:
            return False
        
        self.frozen -= amount
        self.available += amount
        self.update_time = datetime.now()
        return True
    
    def deduct_funds(self, amount: Decimal) -> bool:
        """扣除资金"""
        if amount <= 0 or amount > self.available:
            return False
        
        self.available -= amount
        self.balance -= amount
        self.update_time = datetime.now()
        return True
    
    def add_funds(self, amount: Decimal) -> bool:
        """增加资金"""
        if amount <= 0:
            return False
        
        self.available += amount
        self.balance += amount
        self.update_time = datetime.now()
        return True
    
    def update_pnl(self, pnl: Decimal, is_realized: bool = False) -> None:
        """更新盈亏"""
        if is_realized:
            self.realized_pnl += pnl
        else:
            self.unrealized_pnl += pnl
        
        self.total_pnl = self.realized_pnl + self.unrealized_pnl
        self.daily_pnl += pnl
        self.update_time = datetime.now()
    
    def update_position_value(self, position_value: Decimal) -> None:
        """更新持仓市值"""
        self.total_position_value = position_value
        self.total_market_value = self.balance + position_value
        self.update_time = datetime.now()
    
    def calculate_risk_degree(self) -> Decimal:
        """计算风险度"""
        if self.net_asset == 0:
            return Decimal("0")
        
        # 风险度 = (保证金 + 持仓市值) / 净资产
        risk_degree = (self.margin + self.total_position_value) / self.net_asset
        self.risk_degree = risk_degree
        
        # 更新风险等级
        if risk_degree >= Decimal("0.8"):
            self.risk_level = "DANGER"
        elif risk_degree >= Decimal("0.6"):
            self.risk_level = "WARNING"
        else:
            self.risk_level = "NORMAL"
        
        return risk_degree
    
    def reset_daily_pnl(self) -> None:
        """重置每日盈亏"""
        self.daily_pnl = Decimal("0")
        self.update_time = datetime.now()
    
    def get_account_summary(self) -> Dict[str, Any]:
        """获取账户摘要"""
        return {
            "account_id": self.account_id,
            "user_id": self.user_id,
            "account_name": self.account_name,
            "account_type": self.account_type,
            "balance": float(self.balance),
            "available": float(self.available),
            "frozen": float(self.frozen),
            "margin": float(self.margin),
            "net_asset": float(self.net_asset),
            "total_position_value": float(self.total_position_value),
            "total_market_value": float(self.total_market_value),
            "daily_pnl": float(self.daily_pnl),
            "total_pnl": float(self.total_pnl),
            "realized_pnl": float(self.realized_pnl),
            "unrealized_pnl": float(self.unrealized_pnl),
            "margin_ratio": float(self.margin_ratio),
            "position_ratio": float(self.position_ratio),
            "available_ratio": float(self.available_ratio),
            "risk_degree": float(self.risk_degree),
            "risk_level": self.risk_level,
            "is_active": self.is_active,
            "is_trading": self.is_trading,
            "can_trade": self.is_active and self.is_trading
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "account_id": self.account_id,
            "user_id": self.user_id,
            "account_name": self.account_name,
            "account_type": self.account_type,
            "balance": float(self.balance),
            "available": float(self.available),
            "frozen": float(self.frozen),
            "margin": float(self.margin),
            "risk_degree": float(self.risk_degree),
            "daily_pnl": float(self.daily_pnl),
            "total_pnl": float(self.total_pnl),
            "realized_pnl": float(self.realized_pnl),
            "unrealized_pnl": float(self.unrealized_pnl),
            "total_position_value": float(self.total_position_value),
            "total_market_value": float(self.total_market_value),
            "is_active": self.is_active,
            "is_trading": self.is_trading,
            "risk_level": self.risk_level,
            "create_time": self.create_time.isoformat(),
            "update_time": self.update_time.isoformat(),
            "last_trade_time": self.last_trade_time.isoformat() if self.last_trade_time else None,
            "broker": self.broker,
            "gateway_name": self.gateway_name,
            "remark": self.remark
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Account':
        """从字典创建账户"""
        # 处理时间类型
        if 'create_time' in data and isinstance(data['create_time'], str):
            data['create_time'] = datetime.fromisoformat(data['create_time'])
        
        if 'update_time' in data and isinstance(data['update_time'], str):
            data['update_time'] = datetime.fromisoformat(data['update_time'])
        
        if 'last_trade_time' in data and isinstance(data['last_trade_time'], str):
            data['last_trade_time'] = datetime.fromisoformat(data['last_trade_time'])
        
        # 处理Decimal类型
        if 'balance' in data:
            data['balance'] = Decimal(str(data['balance']))
        
        if 'available' in data:
            data['available'] = Decimal(str(data['available']))
        
        if 'frozen' in data:
            data['frozen'] = Decimal(str(data['frozen']))
        
        if 'margin' in data:
            data['margin'] = Decimal(str(data['margin']))
        
        if 'risk_degree' in data:
            data['risk_degree'] = Decimal(str(data['risk_degree']))
        
        if 'daily_pnl' in data:
            data['daily_pnl'] = Decimal(str(data['daily_pnl']))
        
        if 'total_pnl' in data:
            data['total_pnl'] = Decimal(str(data['total_pnl']))
        
        if 'realized_pnl' in data:
            data['realized_pnl'] = Decimal(str(data['realized_pnl']))
        
        if 'unrealized_pnl' in data:
            data['unrealized_pnl'] = Decimal(str(data['unrealized_pnl']))
        
        if 'total_position_value' in data:
            data['total_position_value'] = Decimal(str(data['total_position_value']))
        
        if 'total_market_value' in data:
            data['total_market_value'] = Decimal(str(data['total_market_value']))
        
        return cls(**data)
