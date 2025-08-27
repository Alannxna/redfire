"""
Contract Entity
==============

合约实体，表示交易系统中的合约信息。
"""

import uuid
from datetime import datetime, time
from decimal import Decimal
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field

from ..enums import Product, Exchange
from ..constants import PRICE_PRECISION, VOLUME_PRECISION


@dataclass
class Contract:
    """合约实体"""
    
    # 基础信息
    contract_id: str = field(default_factory=lambda: f"CONTRACT_{uuid.uuid4().hex[:8]}")
    symbol: str = ""
    exchange: Exchange = Exchange.SSE
    product: Product = Product.EQUITY
    
    # 合约规格
    name: str = ""
    size: int = 1
    price_tick: Decimal = Decimal("0.01")
    min_volume: int = 1
    max_volume: int = 999999999
    
    # 交易时间
    trading_hours: List[Dict[str, time]] = field(default_factory=list)
    trading_days: List[str] = field(default_factory=list)
    
    # 费用信息
    commission_rate: Decimal = Decimal("0.0003")
    margin_rate: Decimal = Decimal("1.0")
    slippage: Decimal = Decimal("0.0001")
    
    # 状态信息
    is_active: bool = True
    is_trading: bool = False
    
    # 时间信息
    create_time: datetime = field(default_factory=datetime.now)
    update_time: datetime = field(default_factory=datetime.now)
    
    # 扩展信息
    description: str = ""
    underlying: str = ""
    expiry_date: Optional[datetime] = None
    strike_price: Optional[Decimal] = None
    option_type: str = ""
    
    def __post_init__(self):
        """初始化后处理"""
        self.update_time = datetime.now()
        
        # 设置默认交易时间
        if not self.trading_hours:
            self.trading_hours = [
                {"start": time(9, 30), "end": time(11, 30)},
                {"start": time(13, 0), "end": time(15, 0)}
            ]
        
        # 设置默认交易日期
        if not self.trading_days:
            self.trading_days = ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY"]
    
    @property
    def is_option(self) -> bool:
        """是否为期权合约"""
        return self.product == Product.OPTION
    
    @property
    def is_futures(self) -> bool:
        """是否为期货合约"""
        return self.product == Product.FUTURES
    
    @property
    def is_equity(self) -> bool:
        """是否为股票合约"""
        return self.product == Product.EQUITY
    
    def is_trading_time(self, current_time: Optional[datetime] = None) -> bool:
        """检查当前是否为交易时间"""
        if not self.is_active or not self.is_trading:
            return False
        
        if current_time is None:
            current_time = datetime.now()
        
        # 检查是否为交易日
        weekday = current_time.strftime("%A").upper()
        if weekday not in self.trading_days:
            return False
        
        # 检查是否为交易时间
        current_time_only = current_time.time()
        for trading_period in self.trading_hours:
            start_time = trading_period["start"]
            end_time = trading_period["end"]
            
            if start_time <= current_time_only <= end_time:
                return True
        
        return False
    
    def get_next_trading_time(self, current_time: Optional[datetime] = None) -> Optional[datetime]:
        """获取下一个交易时间"""
        if current_time is None:
            current_time = datetime.now()
        
        # 如果当前是交易时间，返回当前时间
        if self.is_trading_time(current_time):
            return current_time
        
        # 查找下一个交易时间
        current_date = current_time.date()
        current_time_only = current_time.time()
        
        for i in range(7):  # 最多查找7天
            check_date = current_date + datetime.timedelta(days=i)
            weekday = check_date.strftime("%A").upper()
            
            if weekday in self.trading_days:
                for trading_period in self.trading_hours:
                    start_time = trading_period["start"]
                    
                    # 如果是同一天，检查是否在当天还有交易时间
                    if check_date == current_date and start_time <= current_time_only:
                        continue
                    
                    # 返回下一个交易时间
                    return datetime.combine(check_date, start_time)
        
        return None
    
    def calculate_commission(self, volume: int, price: Decimal) -> Decimal:
        """计算手续费"""
        amount = volume * price
        return amount * self.commission_rate
    
    def calculate_margin(self, volume: int, price: Decimal) -> Decimal:
        """计算保证金"""
        amount = volume * price
        return amount * self.margin_rate
    
    def validate_price(self, price: Decimal) -> bool:
        """验证价格是否有效"""
        if price <= 0:
            return False
        
        # 检查价格精度
        price_str = str(price)
        if '.' in price_str:
            decimal_places = len(price_str.split('.')[1])
            if decimal_places > PRICE_PRECISION:
                return False
        
        # 检查是否为价格tick的整数倍
        remainder = price % self.price_tick
        if remainder != 0:
            return False
        
        return True
    
    def validate_volume(self, volume: int) -> bool:
        """验证数量是否有效"""
        if volume < self.min_volume or volume > self.max_volume:
            return False
        
        # 检查数量精度
        if volume % self.size != 0:
            return False
        
        return True
    
    def get_contract_info(self) -> Dict[str, Any]:
        """获取合约信息"""
        return {
            "contract_id": self.contract_id,
            "symbol": self.symbol,
            "exchange": self.exchange.value,
            "product": self.product.value,
            "name": self.name,
            "size": self.size,
            "price_tick": float(self.price_tick),
            "min_volume": self.min_volume,
            "max_volume": self.max_volume,
            "commission_rate": float(self.commission_rate),
            "margin_rate": float(self.margin_rate),
            "slippage": float(self.slippage),
            "is_active": self.is_active,
            "is_trading": self.is_trading,
            "is_option": self.is_option,
            "is_futures": self.is_futures,
            "is_equity": self.is_equity,
            "description": self.description,
            "underlying": self.underlying,
            "expiry_date": self.expiry_date.isoformat() if self.expiry_date else None,
            "strike_price": float(self.strike_price) if self.strike_price else None,
            "option_type": self.option_type
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "contract_id": self.contract_id,
            "symbol": self.symbol,
            "exchange": self.exchange.value,
            "product": self.product.value,
            "name": self.name,
            "size": self.size,
            "price_tick": float(self.price_tick),
            "min_volume": self.min_volume,
            "max_volume": self.max_volume,
            "trading_hours": self.trading_hours,
            "trading_days": self.trading_days,
            "commission_rate": float(self.commission_rate),
            "margin_rate": float(self.margin_rate),
            "slippage": float(self.slippage),
            "is_active": self.is_active,
            "is_trading": self.is_trading,
            "create_time": self.create_time.isoformat(),
            "update_time": self.update_time.isoformat(),
            "description": self.description,
            "underlying": self.underlying,
            "expiry_date": self.expiry_date.isoformat() if self.expiry_date else None,
            "strike_price": float(self.strike_price) if self.strike_price else None,
            "option_type": self.option_type
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Contract':
        """从字典创建合约"""
        # 处理枚举类型
        if 'exchange' in data and isinstance(data['exchange'], str):
            data['exchange'] = Exchange(data['exchange'])
        
        if 'product' in data and isinstance(data['product'], str):
            data['product'] = Product(data['product'])
        
        # 处理时间类型
        if 'create_time' in data and isinstance(data['create_time'], str):
            data['create_time'] = datetime.fromisoformat(data['create_time'])
        
        if 'update_time' in data and isinstance(data['update_time'], str):
            data['update_time'] = datetime.fromisoformat(data['update_time'])
        
        if 'expiry_date' in data and isinstance(data['expiry_date'], str):
            data['expiry_date'] = datetime.fromisoformat(data['expiry_date'])
        
        # 处理Decimal类型
        if 'price_tick' in data:
            data['price_tick'] = Decimal(str(data['price_tick']))
        
        if 'commission_rate' in data:
            data['commission_rate'] = Decimal(str(data['commission_rate']))
        
        if 'margin_rate' in data:
            data['margin_rate'] = Decimal(str(data['margin_rate']))
        
        if 'slippage' in data:
            data['slippage'] = Decimal(str(data['slippage']))
        
        if 'strike_price' in data and data['strike_price'] is not None:
            data['strike_price'] = Decimal(str(data['strike_price']))
        
        return cls(**data)
