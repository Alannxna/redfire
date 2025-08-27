"""
指标类型值对象
"""

from enum import Enum
from typing import List, Dict, Any


class IndicatorType(str, Enum):
    """
    技术指标类型枚举
    
    定义支持的技术指标类型
    """
    # 趋势指标
    MA = "ma"                    # 移动平均线
    EMA = "ema"                  # 指数移动平均线
    SMA = "sma"                  # 简单移动平均线
    WMA = "wma"                  # 加权移动平均线
    TEMA = "tema"                # 三重指数移动平均线
    VWMA = "vwma"               # 成交量加权移动平均线
    
    # 震荡指标
    RSI = "rsi"                  # 相对强弱指数
    MACD = "macd"               # MACD指标
    KDJ = "kdj"                 # KDJ指标
    STOCH = "stoch"             # 随机指标
    WR = "wr"                   # 威廉指标
    CCI = "cci"                 # 商品通道指数
    
    # 成交量指标
    VOL = "vol"                 # 成交量
    OBV = "obv"                 # 能量潮
    AD = "ad"                   # 累积/派发线
    CMF = "cmf"                 # 蔡金资金流量
    
    # 波动率指标
    BOLL = "boll"               # 布林带
    ATR = "atr"                 # 平均真实波幅
    KELTNER = "keltner"         # 肯特纳通道
    
    # 支撑阻力指标
    PIVOT = "pivot"             # 枢轴点
    FIBONACCI = "fibonacci"      # 斐波那契回撤
    
    @classmethod
    def get_trend_indicators(cls) -> List['IndicatorType']:
        """获取趋势指标"""
        return [cls.MA, cls.EMA, cls.SMA, cls.WMA, cls.TEMA, cls.VWMA]
    
    @classmethod
    def get_oscillator_indicators(cls) -> List['IndicatorType']:
        """获取震荡指标"""
        return [cls.RSI, cls.MACD, cls.KDJ, cls.STOCH, cls.WR, cls.CCI]
    
    @classmethod
    def get_volume_indicators(cls) -> List['IndicatorType']:
        """获取成交量指标"""
        return [cls.VOL, cls.OBV, cls.AD, cls.CMF]
    
    @classmethod
    def get_volatility_indicators(cls) -> List['IndicatorType']:
        """获取波动率指标"""
        return [cls.BOLL, cls.ATR, cls.KELTNER]
    
    def get_default_parameters(self) -> Dict[str, Any]:
        """获取默认参数"""
        defaults = {
            self.MA: {"period": 20},
            self.EMA: {"period": 20},
            self.SMA: {"period": 20},
            self.WMA: {"period": 20},
            self.TEMA: {"period": 20},
            self.VWMA: {"period": 20},
            self.RSI: {"period": 14},
            self.MACD: {"fast": 12, "slow": 26, "signal": 9},
            self.KDJ: {"n": 9, "m1": 3, "m2": 3},
            self.STOCH: {"k_period": 14, "d_period": 3},
            self.WR: {"period": 14},
            self.CCI: {"period": 20},
            self.VOL: {},
            self.OBV: {},
            self.AD: {},
            self.CMF: {"period": 20},
            self.BOLL: {"period": 20, "std": 2},
            self.ATR: {"period": 14},
            self.KELTNER: {"period": 20, "atr_period": 10, "multiplier": 2},
            self.PIVOT: {},
            self.FIBONACCI: {"levels": [0.236, 0.382, 0.5, 0.618, 0.786]}
        }
        return defaults.get(self, {})
    
    def requires_volume(self) -> bool:
        """是否需要成交量数据"""
        return self in [self.VWMA, self.VOL, self.OBV, self.AD, self.CMF]
    
    def is_overlay(self) -> bool:
        """是否为叠加指标（显示在主图上）"""
        return self in [
            self.MA, self.EMA, self.SMA, self.WMA, self.TEMA, self.VWMA,
            self.BOLL, self.KELTNER, self.PIVOT, self.FIBONACCI
        ]
    
    def is_subplot(self) -> bool:
        """是否为子图指标"""
        return not self.is_overlay()
