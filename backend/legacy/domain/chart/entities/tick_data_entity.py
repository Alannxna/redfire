"""
Tick数据实体
"""

from typing import Optional
from datetime import datetime
from dataclasses import dataclass
from decimal import Decimal


@dataclass
class TickData:
    """
    Tick数据实体
    
    表示市场的最小价格变动单位数据
    """
    symbol: str
    datetime: datetime
    last_price: Decimal
    volume: Decimal
    turnover: Optional[Decimal] = None
    open_interest: Optional[Decimal] = None
    
    # 买卖盘信息
    bid_price_1: Optional[Decimal] = None
    bid_volume_1: Optional[Decimal] = None
    ask_price_1: Optional[Decimal] = None
    ask_volume_1: Optional[Decimal] = None
    
    # 更多档位的买卖盘（可选）
    bid_price_2: Optional[Decimal] = None
    bid_volume_2: Optional[Decimal] = None
    ask_price_2: Optional[Decimal] = None
    ask_volume_2: Optional[Decimal] = None
    
    bid_price_3: Optional[Decimal] = None
    bid_volume_3: Optional[Decimal] = None
    ask_price_3: Optional[Decimal] = None
    ask_volume_3: Optional[Decimal] = None
    
    bid_price_4: Optional[Decimal] = None
    bid_volume_4: Optional[Decimal] = None
    ask_price_4: Optional[Decimal] = None
    ask_volume_4: Optional[Decimal] = None
    
    bid_price_5: Optional[Decimal] = None
    bid_volume_5: Optional[Decimal] = None
    ask_price_5: Optional[Decimal] = None
    ask_volume_5: Optional[Decimal] = None
    
    def __post_init__(self):
        """验证数据完整性"""
        if self.volume < 0:
            raise ValueError("成交量不能为负数")
        
        if self.last_price <= 0:
            raise ValueError("最新价必须大于0")
    
    @property
    def spread(self) -> Optional[Decimal]:
        """买卖价差"""
        if self.bid_price_1 and self.ask_price_1:
            return self.ask_price_1 - self.bid_price_1
        return None
    
    @property
    def mid_price(self) -> Optional[Decimal]:
        """中间价"""
        if self.bid_price_1 and self.ask_price_1:
            return (self.bid_price_1 + self.ask_price_1) / 2
        return None
    
    @property
    def has_orderbook(self) -> bool:
        """是否包含委托单信息"""
        return self.bid_price_1 is not None and self.ask_price_1 is not None
    
    def get_total_bid_volume(self) -> Decimal:
        """获取总买单量"""
        total = Decimal('0')
        for i in range(1, 6):
            volume = getattr(self, f'bid_volume_{i}', None)
            if volume:
                total += volume
        return total
    
    def get_total_ask_volume(self) -> Decimal:
        """获取总卖单量"""
        total = Decimal('0')
        for i in range(1, 6):
            volume = getattr(self, f'ask_volume_{i}', None)
            if volume:
                total += volume
        return total
    
    def dict(self) -> dict:
        """转换为字典"""
        return {
            'symbol': self.symbol,
            'datetime': self.datetime.isoformat(),
            'last_price': float(self.last_price),
            'volume': float(self.volume),
            'turnover': float(self.turnover) if self.turnover else None,
            'open_interest': float(self.open_interest) if self.open_interest else None,
            'bid_price_1': float(self.bid_price_1) if self.bid_price_1 else None,
            'bid_volume_1': float(self.bid_volume_1) if self.bid_volume_1 else None,
            'ask_price_1': float(self.ask_price_1) if self.ask_price_1 else None,
            'ask_volume_1': float(self.ask_volume_1) if self.ask_volume_1 else None,
            'spread': float(self.spread) if self.spread else None,
            'mid_price': float(self.mid_price) if self.mid_price else None
        }
