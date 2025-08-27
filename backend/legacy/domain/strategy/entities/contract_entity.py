"""
交易合约实体
定义交易合约的核心属性和行为
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from datetime import datetime, time
from enum import Enum
import uuid


class ContractType(str, Enum):
    """合约类型"""
    FUTURES = "futures"      # 期货
    OPTIONS = "options"      # 期权
    STOCK = "stock"          # 股票
    FOREX = "forex"          # 外汇
    CRYPTO = "crypto"        # 加密货币
    INDEX = "index"          # 指数
    ETF = "etf"              # ETF
    BOND = "bond"            # 债券
    COMMODITY = "commodity"  # 商品


class Exchange(str, Enum):
    """交易所"""
    SHFE = "SHFE"        # 上期所
    DCE = "DCE"          # 大商所
    CZCE = "CZCE"        # 郑商所
    CFFEX = "CFFEX"      # 中金所
    SSE = "SSE"          # 上交所
    SZSE = "SZSE"        # 深交所
    HKEX = "HKEX"        # 港交所
    NYSE = "NYSE"        # 纽交所
    NASDAQ = "NASDAQ"     # 纳斯达克
    CME = "CME"          # 芝加哥商品交易所
    ICE = "ICE"          # 洲际交易所
    LME = "LME"          # 伦敦金属交易所
    BINANCE = "BINANCE"   # 币安
    OANDA = "OANDA"      # OANDA


@dataclass
class TradingHours:
    """交易时间"""
    start_time: time
    end_time: time
    break_start: Optional[time] = None
    break_end: Optional[time] = None
    timezone: str = "UTC"
    
    def is_trading_time(self, current_time: time = None) -> bool:
        """判断是否为交易时间"""
        if current_time is None:
            current_time = datetime.now().time()
        
        # 检查是否在主要交易时间内
        if self.start_time <= current_time <= self.end_time:
            # 如果有午休时间，需要排除
            if self.break_start and self.break_end:
                if self.break_start <= current_time <= self.break_end:
                    return False
            return True
        
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "start_time": self.start_time.strftime("%H:%M:%S"),
            "end_time": self.end_time.strftime("%H:%M:%S"),
            "break_start": self.break_start.strftime("%H:%M:%S") if self.break_start else None,
            "break_end": self.break_end.strftime("%H:%M:%S") if self.break_end else None,
            "timezone": self.timezone
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TradingHours':
        """从字典创建"""
        # 处理时间字段
        for time_field in ['start_time', 'end_time', 'break_start', 'break_end']:
            if time_field in data and data[time_field]:
                data[time_field] = datetime.strptime(data[time_field], "%H:%M:%S").time()
        
        return cls(**data)


@dataclass
class PriceInfo:
    """价格信息"""
    last_price: float = 0.0
    bid_price: float = 0.0
    ask_price: float = 0.0
    high_price: float = 0.0
    low_price: float = 0.0
    open_price: float = 0.0
    close_price: float = 0.0
    settlement_price: float = 0.0
    pre_settlement_price: float = 0.0
    limit_up: float = 0.0
    limit_down: float = 0.0
    timestamp: Optional[datetime] = None
    
    def update_price(self, price_data: Dict[str, Any]):
        """更新价格信息"""
        for key, value in price_data.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.timestamp = datetime.now()
    
    def get_spread(self) -> float:
        """获取买卖价差"""
        if self.bid_price > 0 and self.ask_price > 0:
            return self.ask_price - self.bid_price
        return 0.0
    
    def get_mid_price(self) -> float:
        """获取中间价"""
        if self.bid_price > 0 and self.ask_price > 0:
            return (self.bid_price + self.ask_price) / 2
        return self.last_price
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "last_price": self.last_price,
            "bid_price": self.bid_price,
            "ask_price": self.ask_price,
            "high_price": self.high_price,
            "low_price": self.low_price,
            "open_price": self.open_price,
            "close_price": self.close_price,
            "settlement_price": self.settlement_price,
            "pre_settlement_price": self.pre_settlement_price,
            "limit_up": self.limit_up,
            "limit_down": self.limit_down,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None
        }


@dataclass
class VolumeInfo:
    """成交量信息"""
    volume: int = 0
    open_interest: int = 0
    turnover: float = 0.0
    timestamp: Optional[datetime] = None
    
    def update_volume(self, volume_data: Dict[str, Any]):
        """更新成交量信息"""
        for key, value in volume_data.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "volume": self.volume,
            "open_interest": self.open_interest,
            "turnover": self.turnover,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None
        }


@dataclass
class TradingContract:
    """交易合约实体"""
    
    contract_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    symbol: str = ""
    exchange: Exchange = Exchange.SHFE
    contract_type: ContractType = ContractType.FUTURES
    
    # 合约规格
    size: float = 1.0  # 合约乘数
    price_tick: float = 0.01  # 最小价格变动单位
    min_volume: float = 1.0  # 最小交易数量
    max_volume: Optional[float] = None  # 最大交易数量
    
    # 交易时间
    trading_hours: TradingHours = field(default_factory=lambda: TradingHours(
        start_time=time(9, 0, 0),
        end_time=time(15, 0, 0)
    ))
    
    # 价格信息
    price_info: PriceInfo = field(default_factory=PriceInfo)
    
    # 成交量信息
    volume_info: VolumeInfo = field(default_factory=VolumeInfo)
    
    # 合约信息
    contract_month: Optional[str] = None  # 合约月份
    delivery_date: Optional[datetime] = None  # 交割日期
    expiry_date: Optional[datetime] = None  # 到期日期
    
    # 元数据
    name: Optional[str] = None
    description: Optional[str] = None
    underlying: Optional[str] = None  # 标的资产
    currency: str = "CNY"
    
    # 状态信息
    is_active: bool = True
    is_trading: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def get_contract_value(self, price: float) -> float:
        """获取合约价值"""
        return price * self.size
    
    def get_tick_value(self) -> float:
        """获取最小价格变动价值"""
        return self.price_tick * self.size
    
    def is_trading_time(self) -> bool:
        """判断当前是否为交易时间"""
        return self.trading_hours.is_trading_time()
    
    def update_market_data(self, market_data: Dict[str, Any]):
        """更新市场数据"""
        # 更新价格信息
        if 'price' in market_data:
            self.price_info.update_price(market_data['price'])
        
        # 更新成交量信息
        if 'volume' in market_data:
            self.volume_info.update_volume(market_data['volume'])
        
        self.updated_at = datetime.now()
    
    def get_market_status(self) -> str:
        """获取市场状态"""
        if not self.is_active:
            return "inactive"
        
        if not self.is_trading:
            return "closed"
        
        if self.is_trading_time():
            return "trading"
        else:
            return "closed"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "contract_id": self.contract_id,
            "symbol": self.symbol,
            "exchange": self.exchange.value,
            "contract_type": self.contract_type.value,
            "size": self.size,
            "price_tick": self.price_tick,
            "min_volume": self.min_volume,
            "max_volume": self.max_volume,
            "trading_hours": self.trading_hours.to_dict(),
            "price_info": self.price_info.to_dict(),
            "volume_info": self.volume_info.to_dict(),
            "contract_month": self.contract_month,
            "delivery_date": self.delivery_date.isoformat() if self.delivery_date else None,
            "expiry_date": self.expiry_date.isoformat() if self.expiry_date else None,
            "name": self.name,
            "description": self.description,
            "underlying": self.underlying,
            "currency": self.currency,
            "is_active": self.is_active,
            "is_trading": self.is_trading,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TradingContract':
        """从字典创建"""
        # 处理枚举类型
        if 'exchange' in data and isinstance(data['exchange'], str):
            data['exchange'] = Exchange(data['exchange'])
        
        if 'contract_type' in data and isinstance(data['contract_type'], str):
            data['contract_type'] = ContractType(data['contract_type'])
        
        # 处理交易时间
        if 'trading_hours' in data:
            data['trading_hours'] = TradingHours.from_dict(data['trading_hours'])
        
        # 处理价格信息
        if 'price_info' in data:
            data['price_info'] = PriceInfo(**data['price_info'])
        
        # 处理成交量信息
        if 'volume_info' in data:
            data['volume_info'] = VolumeInfo(**data['volume_info'])
        
        # 处理时间字段
        for time_field in ['created_at', 'updated_at', 'delivery_date', 'expiry_date']:
            if time_field in data and data[time_field]:
                data[time_field] = datetime.fromisoformat(data[time_field])
        
        return cls(**data)
    
    def __post_init__(self):
        """初始化后处理"""
        if not self.contract_id:
            self.contract_id = str(uuid.uuid4())
        
        if not self.created_at:
            self.created_at = datetime.now()
        
        if not self.updated_at:
            self.updated_at = datetime.now()
