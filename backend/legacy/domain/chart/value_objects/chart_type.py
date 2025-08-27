"""
图表类型值对象
"""

from enum import Enum


class ChartType(str, Enum):
    """
    图表类型枚举
    
    定义支持的图表类型
    """
    CANDLESTICK = "candlestick"  # K线图
    LINE = "line"               # 线图
    AREA = "area"               # 面积图
    OHLC = "ohlc"              # OHLC柱状图
    RENKO = "renko"            # 砖形图
    POINT_FIGURE = "point_figure"  # 点数图
    KAGI = "kagi"              # 卡吉图
    
    @classmethod
    def get_default(cls) -> 'ChartType':
        """获取默认图表类型"""
        return cls.CANDLESTICK
    
    @classmethod
    def get_all_types(cls) -> list:
        """获取所有图表类型"""
        return list(cls)
    
    def is_price_based(self) -> bool:
        """是否基于价格的图表类型"""
        return self in [
            ChartType.CANDLESTICK,
            ChartType.LINE,
            ChartType.AREA,
            ChartType.OHLC
        ]
    
    def requires_ohlc(self) -> bool:
        """是否需要OHLC数据"""
        return self in [
            ChartType.CANDLESTICK,
            ChartType.OHLC,
            ChartType.RENKO,
            ChartType.POINT_FIGURE,
            ChartType.KAGI
        ]
    
    def supports_volume(self) -> bool:
        """是否支持成交量显示"""
        return self in [
            ChartType.CANDLESTICK,
            ChartType.OHLC,
            ChartType.LINE,
            ChartType.AREA
        ]
