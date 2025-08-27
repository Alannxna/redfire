"""
Trading Domain Module
=====================

交易领域模块，包含交易相关的核心业务逻辑、实体、服务和仓储。

主要组件：
- entities: 交易实体（订单、成交、持仓等）
- enums: 交易枚举（方向、状态、类型等）
- services: 交易领域服务
- repositories: 交易数据访问接口
- value_objects: 交易值对象
- events: 交易事件
- specifications: 交易业务规则
"""

from .enums import (
    Direction,
    Offset,
    OrderStatus,
    TradeStatus,
    PositionStatus,
    Product,
    Exchange,
    OrderType,
    PriceType
)

from .constants import (
    PRICE_PRECISION,
    VOLUME_PRECISION,
    AMOUNT_PRECISION,
    MIN_VOLUME,
    MAX_VOLUME,
    MIN_PRICE,
    MAX_PRICE,
    TRADING_DAY_START,
    TRADING_DAY_END,
    NIGHT_TRADING_START,
    NIGHT_TRADING_END,
    DEFAULT_COMMISSION_RATE,
    DEFAULT_SLIPPAGE,
    DEFAULT_MAX_POSITION_RATIO,
    DEFAULT_STOP_LOSS_RATIO,
    DEFAULT_TAKE_PROFIT_RATIO
)

__all__ = [
    # Enums
    'Direction',
    'Offset', 
    'OrderStatus',
    'TradeStatus',
    'PositionStatus',
    'Product',
    'Exchange',
    'OrderType',
    'PriceType',
    
    # Constants
    'PRICE_PRECISION',
    'VOLUME_PRECISION',
    'AMOUNT_PRECISION',
    'MIN_VOLUME',
    'MAX_VOLUME',
    'MIN_PRICE',
    'MAX_PRICE',
    'TRADING_DAY_START',
    'TRADING_DAY_END',
    'NIGHT_TRADING_START',
    'NIGHT_TRADING_END',
    'DEFAULT_COMMISSION_RATE',
    'DEFAULT_SLIPPAGE',
    'DEFAULT_MAX_POSITION_RATIO',
    'DEFAULT_STOP_LOSS_RATIO',
    'DEFAULT_TAKE_PROFIT_RATIO'
]
