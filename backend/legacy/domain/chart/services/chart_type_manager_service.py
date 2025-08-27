"""
图表类型管理器领域服务
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

from ..value_objects.chart_type import ChartType
from ..value_objects.interval import Interval
from ..entities.bar_data_entity import BarData

logger = logging.getLogger(__name__)


class ChartRenderMode(str, Enum):
    """图表渲染模式"""
    REAL_TIME = "real_time"      # 实时模式
    HISTORICAL = "historical"    # 历史模式
    REPLAY = "replay"           # 回放模式


@dataclass
class ChartDisplayConfig:
    """图表显示配置"""
    show_volume: bool = True
    show_grid: bool = True
    show_crosshair: bool = True
    show_legend: bool = True
    theme: str = "light"  # light, dark
    color_scheme: Dict[str, str] = None
    
    def __post_init__(self):
        if self.color_scheme is None:
            self.color_scheme = {
                "bullish": "#26a69a",     # 阳线颜色
                "bearish": "#ef5350",     # 阴线颜色
                "volume": "#42a5f5",      # 成交量颜色
                "grid": "#e0e0e0",        # 网格颜色
                "background": "#ffffff",   # 背景颜色
                "text": "#333333"         # 文字颜色
            }


@dataclass
class ChartTypeCapabilities:
    """图表类型能力描述"""
    supports_ohlc: bool
    supports_volume: bool
    supports_indicators: bool
    requires_tick_data: bool
    min_data_points: int
    description: str


class ChartTypeManagerService:
    """
    图表类型管理器领域服务
    
    负责管理不同类型图表的配置、渲染和验证
    """
    
    def __init__(self):
        self.chart_capabilities = self._initialize_capabilities()
        self.default_configs = self._initialize_default_configs()
    
    def get_chart_capabilities(self, chart_type: ChartType) -> ChartTypeCapabilities:
        """获取图表类型的能力描述"""
        return self.chart_capabilities.get(chart_type, self._get_default_capabilities())
    
    def validate_chart_creation(
        self, 
        chart_type: ChartType, 
        interval: Interval,
        data_count: int
    ) -> Dict[str, Any]:
        """
        验证图表创建参数
        
        Args:
            chart_type: 图表类型
            interval: 时间周期
            data_count: 数据数量
            
        Returns:
            Dict[str, Any]: 验证结果
        """
        capabilities = self.get_chart_capabilities(chart_type)
        
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        # 检查最小数据点要求
        if data_count < capabilities.min_data_points:
            validation_result["errors"].append(
                f"数据点数量不足，至少需要{capabilities.min_data_points}个，当前{data_count}个"
            )
            validation_result["valid"] = False
        
        # 检查时间周期兼容性
        if not self._is_interval_compatible(chart_type, interval):
            validation_result["warnings"].append(
                f"时间周期{interval.value}可能不适合{chart_type.value}图表类型"
            )
        
        return validation_result
    
    def get_recommended_config(
        self, 
        chart_type: ChartType, 
        symbol: str,
        interval: Interval
    ) -> ChartDisplayConfig:
        """
        获取推荐的图表配置
        
        Args:
            chart_type: 图表类型
            symbol: 交易品种
            interval: 时间周期
            
        Returns:
            ChartDisplayConfig: 推荐配置
        """
        base_config = self.default_configs.get(chart_type, ChartDisplayConfig())
        
        # 根据品种类型调整配置
        if symbol.endswith('.SH') or symbol.endswith('.SZ'):
            # A股市场
            base_config.color_scheme["bullish"] = "#ff4757"  # 红涨
            base_config.color_scheme["bearish"] = "#2ed573"  # 绿跌
        
        # 根据时间周期调整
        if interval in [Interval.SECOND_1, Interval.SECOND_5, Interval.SECOND_15]:
            base_config.show_volume = False  # 短周期通常不显示成交量
        
        return base_config
    
    def convert_chart_data(
        self, 
        bars: List[BarData], 
        chart_type: ChartType
    ) -> List[Dict[str, Any]]:
        """
        根据图表类型转换数据格式
        
        Args:
            bars: K线数据
            chart_type: 图表类型
            
        Returns:
            List[Dict[str, Any]]: 转换后的数据
        """
        capabilities = self.get_chart_capabilities(chart_type)
        
        converted_data = []
        
        for bar in bars:
            data_point = {
                "timestamp": bar.datetime.isoformat(),
                "time": int(bar.datetime.timestamp() * 1000)  # 毫秒时间戳
            }
            
            if chart_type == ChartType.CANDLESTICK or chart_type == ChartType.OHLC:
                if capabilities.supports_ohlc:
                    data_point.update({
                        "open": float(bar.open_price),
                        "high": float(bar.high_price),
                        "low": float(bar.low_price),
                        "close": float(bar.close_price)
                    })
                    
            elif chart_type == ChartType.LINE:
                data_point["value"] = float(bar.close_price)
                
            elif chart_type == ChartType.AREA:
                data_point["value"] = float(bar.close_price)
                
            elif chart_type == ChartType.RENKO:
                # 砖形图需要特殊处理
                data_point = self._convert_to_renko(bar, data_point)
                
            elif chart_type == ChartType.POINT_FIGURE:
                # 点数图需要特殊处理
                data_point = self._convert_to_point_figure(bar, data_point)
                
            elif chart_type == ChartType.KAGI:
                # 卡吉图需要特殊处理
                data_point = self._convert_to_kagi(bar, data_point)
            
            # 添加成交量信息
            if capabilities.supports_volume:
                data_point["volume"] = float(bar.volume)
            
            converted_data.append(data_point)
        
        return converted_data
    
    def get_supported_intervals(self, chart_type: ChartType) -> List[Interval]:
        """获取图表类型支持的时间周期"""
        if chart_type in [ChartType.RENKO, ChartType.POINT_FIGURE, ChartType.KAGI]:
            # 价格驱动的图表类型不依赖固定时间周期
            return [Interval.TICK]
        
        # 其他图表类型支持所有标准时间周期
        return list(Interval)
    
    def _initialize_capabilities(self) -> Dict[ChartType, ChartTypeCapabilities]:
        """初始化图表类型能力"""
        return {
            ChartType.CANDLESTICK: ChartTypeCapabilities(
                supports_ohlc=True,
                supports_volume=True,
                supports_indicators=True,
                requires_tick_data=False,
                min_data_points=1,
                description="蜡烛图，显示开高低收四个价格"
            ),
            ChartType.LINE: ChartTypeCapabilities(
                supports_ohlc=False,
                supports_volume=True,
                supports_indicators=True,
                requires_tick_data=False,
                min_data_points=2,
                description="线图，仅显示收盘价连线"
            ),
            ChartType.AREA: ChartTypeCapabilities(
                supports_ohlc=False,
                supports_volume=True,
                supports_indicators=True,
                requires_tick_data=False,
                min_data_points=2,
                description="面积图，收盘价连线下方填充"
            ),
            ChartType.OHLC: ChartTypeCapabilities(
                supports_ohlc=True,
                supports_volume=True,
                supports_indicators=True,
                requires_tick_data=False,
                min_data_points=1,
                description="OHLC柱状图，显示开高低收"
            ),
            ChartType.RENKO: ChartTypeCapabilities(
                supports_ohlc=True,
                supports_volume=False,
                supports_indicators=False,
                requires_tick_data=True,
                min_data_points=10,
                description="砖形图，根据价格变动绘制砖块"
            ),
            ChartType.POINT_FIGURE: ChartTypeCapabilities(
                supports_ohlc=False,
                supports_volume=False,
                supports_indicators=False,
                requires_tick_data=True,
                min_data_points=20,
                description="点数图，使用X和O标记价格趋势"
            ),
            ChartType.KAGI: ChartTypeCapabilities(
                supports_ohlc=False,
                supports_volume=False,
                supports_indicators=False,
                requires_tick_data=True,
                min_data_points=15,
                description="卡吉图，显示价格趋势转换"
            )
        }
    
    def _initialize_default_configs(self) -> Dict[ChartType, ChartDisplayConfig]:
        """初始化默认配置"""
        return {
            ChartType.CANDLESTICK: ChartDisplayConfig(
                show_volume=True,
                show_grid=True,
                show_crosshair=True,
                show_legend=True,
                theme="light"
            ),
            ChartType.LINE: ChartDisplayConfig(
                show_volume=False,
                show_grid=True,
                show_crosshair=True,
                show_legend=False,
                theme="light"
            ),
            ChartType.AREA: ChartDisplayConfig(
                show_volume=False,
                show_grid=True,
                show_crosshair=True,
                show_legend=False,
                theme="light"
            ),
            ChartType.OHLC: ChartDisplayConfig(
                show_volume=True,
                show_grid=True,
                show_crosshair=True,
                show_legend=True,
                theme="light"
            )
        }
    
    def _get_default_capabilities(self) -> ChartTypeCapabilities:
        """获取默认能力描述"""
        return ChartTypeCapabilities(
            supports_ohlc=True,
            supports_volume=True,
            supports_indicators=True,
            requires_tick_data=False,
            min_data_points=1,
            description="默认图表类型"
        )
    
    def _is_interval_compatible(self, chart_type: ChartType, interval: Interval) -> bool:
        """检查时间周期与图表类型的兼容性"""
        if chart_type in [ChartType.RENKO, ChartType.POINT_FIGURE, ChartType.KAGI]:
            return interval == Interval.TICK
        
        # 其他图表类型与所有标准时间周期兼容
        return True
    
    def _convert_to_renko(self, bar: BarData, data_point: Dict[str, Any]) -> Dict[str, Any]:
        """转换为砖形图数据"""
        # 砖形图转换逻辑（简化版）
        data_point.update({
            "brick_size": 1.0,  # 砖块大小，需要根据历史数据动态计算
            "direction": "up" if bar.close_price > bar.open_price else "down",
            "price": float(bar.close_price)
        })
        return data_point
    
    def _convert_to_point_figure(self, bar: BarData, data_point: Dict[str, Any]) -> Dict[str, Any]:
        """转换为点数图数据"""
        # 点数图转换逻辑（简化版）
        data_point.update({
            "box_size": 1.0,  # 方格大小
            "reversal_amount": 3,  # 反转数量
            "symbol": "X" if bar.close_price > bar.open_price else "O",
            "price": float(bar.close_price)
        })
        return data_point
    
    def _convert_to_kagi(self, bar: BarData, data_point: Dict[str, Any]) -> Dict[str, Any]:
        """转换为卡吉图数据"""
        # 卡吉图转换逻辑（简化版）
        data_point.update({
            "reversal_amount": 2.0,  # 反转金额
            "line_type": "yang" if bar.close_price > bar.open_price else "yin",
            "price": float(bar.close_price)
        })
        return data_point
