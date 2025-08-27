"""
交易相关枚举定义
================

定义交易系统相关的统一枚举
"""

from enum import Enum


class ExchangeType(Enum):
    """交易所类型枚举"""
    SHFE = "SHFE"       # 上海期货交易所
    CFFEX = "CFFEX"     # 中国金融期货交易所
    DCE = "DCE"         # 大连商品交易所
    CZCE = "CZCE"       # 郑州商品交易所
    INE = "INE"         # 上海国际能源交易中心
    SSE = "SSE"         # 上海证券交易所
    SZSE = "SZSE"       # 深圳证券交易所
    SGE = "SGE"         # 上海黄金交易所
    
    def __str__(self):
        return self.value

    @property
    def is_futures(self) -> bool:
        """判断是否为期货交易所"""
        return self in [
            ExchangeType.SHFE,
            ExchangeType.CFFEX,
            ExchangeType.DCE,
            ExchangeType.CZCE,
            ExchangeType.INE
        ]

    @property
    def is_stock(self) -> bool:
        """判断是否为股票交易所"""
        return self in [ExchangeType.SSE, ExchangeType.SZSE]


class StrategyStatus(Enum):
    """策略状态枚举"""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    PAUSED = "paused"
    ERROR = "error"

    def __str__(self):
        return self.value

    @property
    def is_active(self) -> bool:
        """判断策略是否活跃"""
        return self in [
            StrategyStatus.STARTING,
            StrategyStatus.RUNNING,
            StrategyStatus.PAUSED
        ]

    @property
    def can_trade(self) -> bool:
        """判断策略是否可以交易"""
        return self == StrategyStatus.RUNNING


class GatewayStatus(Enum):
    """网关状态枚举"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTING = "disconnecting"
    ERROR = "error"

    def __str__(self):
        return self.value

    @property
    def is_available(self) -> bool:
        """判断网关是否可用"""
        return self == GatewayStatus.CONNECTED

    @property
    def is_connecting_state(self) -> bool:
        """判断是否为连接中状态"""
        return self in [
            GatewayStatus.CONNECTING,
            GatewayStatus.DISCONNECTING
        ]


class MarketDataType(Enum):
    """市场数据类型枚举"""
    TICK = "tick"
    BAR_1M = "1m"
    BAR_5M = "5m"
    BAR_15M = "15m"
    BAR_30M = "30m"
    BAR_1H = "1h"
    BAR_2H = "2h"
    BAR_4H = "4h"
    BAR_1D = "1d"

    def __str__(self):
        return self.value

    @property
    def is_tick_data(self) -> bool:
        """判断是否为Tick数据"""
        return self == MarketDataType.TICK

    @property
    def is_bar_data(self) -> bool:
        """判断是否为K线数据"""
        return not self.is_tick_data

    @property
    def minutes(self) -> int:
        """获取时间周期对应的分钟数"""
        minutes_map = {
            MarketDataType.TICK: 0,
            MarketDataType.BAR_1M: 1,
            MarketDataType.BAR_5M: 5,
            MarketDataType.BAR_15M: 15,
            MarketDataType.BAR_30M: 30,
            MarketDataType.BAR_1H: 60,
            MarketDataType.BAR_2H: 120,
            MarketDataType.BAR_4H: 240,
            MarketDataType.BAR_1D: 1440
        }
        return minutes_map.get(self, 0)
