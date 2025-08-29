"""
图表核心数据模型

基于vnpy-core数据结构设计，适配Web图表引擎需求
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Union
import json


class ChartType(str, Enum):
    """图表类型 - 基于vnpy-core图表类型"""
    CANDLESTICK = "candlestick"       # K线图 (主要)
    LINE = "line"                     # 分时线
    AREA = "area"                     # 面积图
    HEIKIN_ASHI = "heikin_ashi"      # 平均K线
    RENKO = "renko"                   # 砖型图
    POINT_FIGURE = "point_figure"     # 点数图
    VOLUME = "volume"                 # 成交量
    INDICATOR = "indicator"           # 技术指标


class Interval(str, Enum):
    """时间周期 - 与vnpy-core保持一致"""
    SECOND_1 = "1s"
    SECOND_5 = "5s" 
    SECOND_15 = "15s"
    SECOND_30 = "30s"
    MINUTE_1 = "1m"
    MINUTE_5 = "5m"
    MINUTE_15 = "15m"
    MINUTE_30 = "30m"
    HOUR_1 = "1h"
    HOUR_4 = "4h"
    DAILY = "1d"
    WEEKLY = "1w"


class IndicatorType(str, Enum):
    """技术指标类型"""
    MA = "ma"                         # 移动平均线
    EMA = "ema"                       # 指数移动平均线
    MACD = "macd"                     # MACD
    RSI = "rsi"                       # 相对强弱指数
    BOLL = "boll"                     # 布林带
    KDJ = "kdj"                       # KDJ随机指标
    VOLUME = "volume"                 # 成交量
    ATR = "atr"                       # 平均真实波幅
    CCI = "cci"                       # 顺势指标
    OBV = "obv"                       # 能量潮


@dataclass
class BarData:
    """K线数据 - 基于vnpy-core BarData"""
    symbol: str
    datetime: datetime
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    volume: float
    open_interest: float = 0.0
    turnover: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "symbol": self.symbol,
            "datetime": self.datetime.isoformat(),
            "open": self.open_price,
            "high": self.high_price,
            "low": self.low_price,
            "close": self.close_price,
            "volume": self.volume,
            "open_interest": self.open_interest,
            "turnover": self.turnover
        }


@dataclass
class IndicatorConfig:
    """技术指标配置"""
    type: IndicatorType
    name: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    color: str = "#3498db"
    line_width: int = 2
    visible: bool = True
    
    def __post_init__(self):
        """设置默认参数"""
        if not self.parameters:
            self.parameters = self._get_default_parameters()
    
    def _get_default_parameters(self) -> Dict[str, Any]:
        """获取默认参数"""
        defaults = {
            IndicatorType.MA: {"period": 20},
            IndicatorType.EMA: {"period": 20},
            IndicatorType.MACD: {"fast": 12, "slow": 26, "signal": 9},
            IndicatorType.RSI: {"period": 14},
            IndicatorType.BOLL: {"period": 20, "std": 2.0},
            IndicatorType.KDJ: {"period": 14, "k": 3, "d": 3},
            IndicatorType.ATR: {"period": 14},
            IndicatorType.CCI: {"period": 14},
        }
        return defaults.get(self.type, {})


@dataclass 
class ChartConfig:
    """图表配置"""
    # 基础配置
    title: str = ""
    show_volume: bool = True
    show_crosshair: bool = True
    show_toolbar: bool = True
    
    # 显示配置
    max_bars: int = 1000
    decimal_places: int = 2
    auto_scale: bool = True
    show_grid: bool = True
    
    # 技术指标
    indicators: List[IndicatorConfig] = field(default_factory=list)
    
    # 主图配置
    main_chart_height: int = 400
    sub_chart_height: int = 100
    
    # 颜色配置
    up_color: str = "#26a69a"         # 涨 (绿色)
    down_color: str = "#ef5350"       # 跌 (红色)
    background_color: str = "#1e1e1e" # 背景色
    grid_color: str = "#333333"       # 网格色
    text_color: str = "#ffffff"       # 文字色
    
    # 实时更新配置
    auto_update: bool = True
    update_interval: int = 1000       # 毫秒
    
    def add_indicator(self, indicator: IndicatorConfig) -> None:
        """添加技术指标"""
        self.indicators.append(indicator)
    
    def remove_indicator(self, indicator_name: str) -> None:
        """移除技术指标"""
        self.indicators = [ind for ind in self.indicators if ind.name != indicator_name]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "title": self.title,
            "show_volume": self.show_volume,
            "show_crosshair": self.show_crosshair,
            "show_toolbar": self.show_toolbar,
            "max_bars": self.max_bars,
            "decimal_places": self.decimal_places,
            "auto_scale": self.auto_scale,
            "show_grid": self.show_grid,
            "indicators": [
                {
                    "type": ind.type.value,
                    "name": ind.name,
                    "parameters": ind.parameters,
                    "color": ind.color,
                    "line_width": ind.line_width,
                    "visible": ind.visible
                }
                for ind in self.indicators
            ],
            "main_chart_height": self.main_chart_height,
            "sub_chart_height": self.sub_chart_height,
            "colors": {
                "up": self.up_color,
                "down": self.down_color,
                "background": self.background_color,
                "grid": self.grid_color,
                "text": self.text_color
            },
            "auto_update": self.auto_update,
            "update_interval": self.update_interval
        }


@dataclass
class ChartUpdateEvent:
    """图表更新事件"""
    chart_id: str
    bar_data: BarData
    indicators: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "chart_id": self.chart_id,
            "bar_data": self.bar_data.to_dict(),
            "indicators": self.indicators,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class SubscriptionInfo:
    """订阅信息"""
    chart_id: str
    subscriber_id: str
    initial_data: List[BarData]
    config: ChartConfig
    subscribed_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "chart_id": self.chart_id,
            "subscriber_id": self.subscriber_id,
            "initial_data": [bar.to_dict() for bar in self.initial_data],
            "config": self.config.to_dict(),
            "subscribed_at": self.subscribed_at.isoformat()
        }


@dataclass
class IndicatorData:
    """技术指标数据"""
    name: str
    type: IndicatorType
    values: Dict[str, List[float]]    # 指标值 {"ma": [1.1, 1.2, ...], "signal": [...]}
    timestamps: List[datetime]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "type": self.type.value,
            "values": self.values,
            "timestamps": [ts.isoformat() for ts in self.timestamps]
        }


@dataclass
class ChartSnapshot:
    """图表快照 - 用于缓存和序列化"""
    chart_id: str
    symbol: str
    chart_type: ChartType
    interval: Interval
    bars: List[BarData]
    indicators: List[IndicatorData]
    config: ChartConfig
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "chart_id": self.chart_id,
            "symbol": self.symbol,
            "chart_type": self.chart_type.value,
            "interval": self.interval.value,
            "bars": [bar.to_dict() for bar in self.bars],
            "indicators": [ind.to_dict() for ind in self.indicators],
            "config": self.config.to_dict(),
            "created_at": self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChartSnapshot':
        """从字典创建"""
        return cls(
            chart_id=data["chart_id"],
            symbol=data["symbol"],
            chart_type=ChartType(data["chart_type"]),
            interval=Interval(data["interval"]),
            bars=[
                BarData(
                    symbol=bar["symbol"],
                    datetime=datetime.fromisoformat(bar["datetime"]),
                    open_price=bar["open"],
                    high_price=bar["high"],
                    low_price=bar["low"],
                    close_price=bar["close"],
                    volume=bar["volume"],
                    open_interest=bar.get("open_interest", 0.0),
                    turnover=bar.get("turnover", 0.0)
                )
                for bar in data["bars"]
            ],
            indicators=[
                IndicatorData(
                    name=ind["name"],
                    type=IndicatorType(ind["type"]),
                    values=ind["values"],
                    timestamps=[datetime.fromisoformat(ts) for ts in ind["timestamps"]]
                )
                for ind in data["indicators"]
            ],
            config=ChartConfig(**data["config"]),
            created_at=datetime.fromisoformat(data["created_at"])
        )
