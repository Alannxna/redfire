"""
K线数据实体
"""

from typing import Optional
from datetime import datetime
from dataclasses import dataclass
from decimal import Decimal


@dataclass
class BarData:
    """
    K线数据实体
    
    表示单个时间周期的价格数据
    """
    symbol: str
    datetime: datetime
    open_price: Decimal
    high_price: Decimal
    low_price: Decimal
    close_price: Decimal
    volume: Decimal
    turnover: Optional[Decimal] = None
    open_interest: Optional[Decimal] = None
    
    def __post_init__(self):
        """验证数据完整性"""
        if self.high_price < max(self.open_price, self.close_price):
            raise ValueError("最高价不能低于开盘价或收盘价")
        
        if self.low_price > min(self.open_price, self.close_price):
            raise ValueError("最低价不能高于开盘价或收盘价")
        
        if self.volume < 0:
            raise ValueError("成交量不能为负数")
    
    @property
    def price_change(self) -> Decimal:
        """价格变化"""
        return self.close_price - self.open_price
    
    @property
    def price_change_pct(self) -> Decimal:
        """价格变化百分比"""
        if self.open_price == 0:
            return Decimal('0')
        return (self.price_change / self.open_price) * 100
    
    @property
    def is_bullish(self) -> bool:
        """是否为阳线"""
        return self.close_price > self.open_price
    
    @property
    def is_bearish(self) -> bool:
        """是否为阴线"""
        return self.close_price < self.open_price
    
    @property
    def is_doji(self) -> bool:
        """是否为十字星"""
        return self.close_price == self.open_price
    
    @property
    def body_size(self) -> Decimal:
        """实体大小"""
        return abs(self.close_price - self.open_price)
    
    @property
    def upper_shadow(self) -> Decimal:
        """上影线长度"""
        return self.high_price - max(self.open_price, self.close_price)
    
    @property
    def lower_shadow(self) -> Decimal:
        """下影线长度"""
        return min(self.open_price, self.close_price) - self.low_price
    
    @classmethod
    def create(
        cls,
        symbol: str,
        datetime: datetime,
        open_price: float,
        high_price: float,
        low_price: float,
        close_price: float,
        volume: float,
        turnover: Optional[float] = None,
        open_interest: Optional[float] = None
    ) -> 'BarData':
        """创建K线数据实例"""
        return cls(
            symbol=symbol,
            datetime=datetime,
            open_price=Decimal(str(open_price)),
            high_price=Decimal(str(high_price)),
            low_price=Decimal(str(low_price)),
            close_price=Decimal(str(close_price)),
            volume=Decimal(str(volume)),
            turnover=Decimal(str(turnover)) if turnover is not None else None,
            open_interest=Decimal(str(open_interest)) if open_interest is not None else None
        )