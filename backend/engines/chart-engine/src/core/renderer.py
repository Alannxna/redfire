"""
Web图表渲染器 - 基于vnpy-core图表渲染逻辑的Web优化版本

将vnpy的PyQt图表渲染能力转换为Web Canvas/WebGL渲染
"""

import logging
import json
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
import numpy as np

from ..models.chart_models import (
    BarData, ChartType, ChartConfig, IndicatorData
)
from ..utils.performance import PerformanceMonitor

logger = logging.getLogger(__name__)


@dataclass
class RenderPoint:
    """渲染点数据"""
    x: float
    y: float
    color: str = "#ffffff"
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CandleRenderData:
    """蜡烛图渲染数据"""
    x: float
    open: float
    high: float
    low: float
    close: float
    color: str
    volume: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class LineRenderData:
    """线条渲染数据"""
    points: List[RenderPoint]
    color: str = "#3498db"
    width: int = 2
    name: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "points": [p.to_dict() for p in self.points],
            "color": self.color,
            "width": self.width,
            "name": self.name
        }


@dataclass
class ChartRenderData:
    """图表渲染数据"""
    chart_id: str
    chart_type: ChartType
    candles: List[CandleRenderData] = None
    lines: List[LineRenderData] = None
    volume_bars: List[Dict[str, Any]] = None
    x_axis: Dict[str, Any] = None
    y_axis: Dict[str, Any] = None
    viewport: Dict[str, Any] = None
    config: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        result = {
            "chart_id": self.chart_id,
            "chart_type": self.chart_type.value,
            "config": self.config or {}
        }
        
        if self.candles:
            result["candles"] = [c.to_dict() for c in self.candles]
        
        if self.lines:
            result["lines"] = [l.to_dict() for l in self.lines]
        
        if self.volume_bars:
            result["volume_bars"] = self.volume_bars
        
        if self.x_axis:
            result["x_axis"] = self.x_axis
        
        if self.y_axis:
            result["y_axis"] = self.y_axis
        
        if self.viewport:
            result["viewport"] = self.viewport
        
        return result


class ChartRenderer:
    """
    单个图表渲染器
    
    基于vnpy-core的图表渲染逻辑，适配Web环境
    """
    
    def __init__(self, chart_id: str, chart_type: ChartType, config: ChartConfig):
        self.chart_id = chart_id
        self.chart_type = chart_type
        self.config = config
        
        # 渲染配置
        self.canvas_width = 800
        self.canvas_height = 600
        self.margin = {"left": 60, "right": 60, "top": 40, "bottom": 60}
        
        # 数据范围缓存
        self._price_range: Optional[Tuple[float, float]] = None
        self._volume_range: Optional[Tuple[float, float]] = None
        self._time_range: Optional[Tuple[datetime, datetime]] = None
        
        # 性能监控
        self.performance_monitor = PerformanceMonitor()
        
        logger.debug(f"图表渲染器创建: {chart_id} ({chart_type.value})")
    
    def prepare_render_data(
        self,
        bars: List[BarData],
        indicators: Dict[str, IndicatorData],
        viewport: Optional[Dict[str, Any]] = None
    ) -> ChartRenderData:
        """准备渲染数据 - 基于vnpy-core的数据处理逻辑"""
        try:
            with self.performance_monitor.timer(f"render_prepare_{self.chart_id}"):
                # 计算数据范围
                self._calculate_data_ranges(bars)
                
                # 创建渲染数据对象
                render_data = ChartRenderData(
                    chart_id=self.chart_id,
                    chart_type=self.chart_type
                )
                
                # 准备K线数据
                if self.chart_type == ChartType.CANDLESTICK:
                    render_data.candles = self._prepare_candle_data(bars)
                elif self.chart_type == ChartType.LINE:
                    render_data.lines = [self._prepare_line_data(bars, "close")]
                elif self.chart_type == ChartType.AREA:
                    render_data.lines = [self._prepare_area_data(bars)]
                
                # 准备成交量数据
                if self.config.show_volume:
                    render_data.volume_bars = self._prepare_volume_data(bars)
                
                # 准备技术指标数据
                if indicators:
                    indicator_lines = self._prepare_indicator_data(indicators)
                    if render_data.lines:
                        render_data.lines.extend(indicator_lines)
                    else:
                        render_data.lines = indicator_lines
                
                # 准备坐标轴
                render_data.x_axis = self._prepare_x_axis(bars)
                render_data.y_axis = self._prepare_y_axis()
                
                # 准备视口
                render_data.viewport = viewport or self._get_default_viewport()
                
                # 渲染配置
                render_data.config = self.config.to_dict()
                
                return render_data
                
        except Exception as e:
            logger.error(f"准备渲染数据失败: {e}")
            raise
    
    def _calculate_data_ranges(self, bars: List[BarData]) -> None:
        """计算数据范围 - 基于vnpy-core的范围计算"""
        if not bars:
            return
        
        # 价格范围
        highs = [bar.high_price for bar in bars]
        lows = [bar.low_price for bar in bars]
        self._price_range = (min(lows), max(highs))
        
        # 成交量范围
        volumes = [bar.volume for bar in bars]
        self._volume_range = (min(volumes), max(volumes))
        
        # 时间范围
        times = [bar.datetime for bar in bars]
        self._time_range = (min(times), max(times))
    
    def _prepare_candle_data(self, bars: List[BarData]) -> List[CandleRenderData]:
        """准备K线数据 - 基于vnpy-core的蜡烛图绘制逻辑"""
        candles = []
        
        for i, bar in enumerate(bars):
            # 确定颜色 (涨绿跌红)
            color = self.config.up_color if bar.close_price >= bar.open_price else self.config.down_color
            
            candle = CandleRenderData(
                x=float(i),  # 使用索引作为x坐标
                open=bar.open_price,
                high=bar.high_price,
                low=bar.low_price,
                close=bar.close_price,
                color=color,
                volume=bar.volume
            )
            candles.append(candle)
        
        return candles
    
    def _prepare_line_data(self, bars: List[BarData], price_type: str = "close") -> LineRenderData:
        """准备线条数据"""
        points = []
        
        for i, bar in enumerate(bars):
            price = getattr(bar, f"{price_type}_price", bar.close_price)
            point = RenderPoint(x=float(i), y=price)
            points.append(point)
        
        return LineRenderData(
            points=points,
            color=self.config.up_color,
            name=f"{price_type.upper()} Line"
        )
    
    def _prepare_area_data(self, bars: List[BarData]) -> LineRenderData:
        """准备面积图数据"""
        points = []
        
        for i, bar in enumerate(bars):
            point = RenderPoint(x=float(i), y=bar.close_price)
            points.append(point)
        
        return LineRenderData(
            points=points,
            color=self.config.up_color,
            name="Area Chart"
        )
    
    def _prepare_volume_data(self, bars: List[BarData]) -> List[Dict[str, Any]]:
        """准备成交量数据"""
        volume_bars = []
        
        for i, bar in enumerate(bars):
            # 成交量柱颜色与K线颜色一致
            color = self.config.up_color if bar.close_price >= bar.open_price else self.config.down_color
            
            volume_bar = {
                "x": float(i),
                "volume": bar.volume,
                "color": color
            }
            volume_bars.append(volume_bar)
        
        return volume_bars
    
    def _prepare_indicator_data(self, indicators: Dict[str, IndicatorData]) -> List[LineRenderData]:
        """准备技术指标数据"""
        lines = []
        
        for name, indicator in indicators.items():
            # 为每个指标数据创建线条
            for value_name, values in indicator.values.items():
                if not values:
                    continue
                
                points = []
                for i, value in enumerate(values):
                    if value is not None and not np.isnan(value):
                        point = RenderPoint(x=float(i), y=float(value))
                        points.append(point)
                
                if points:
                    line = LineRenderData(
                        points=points,
                        color=self._get_indicator_color(name, value_name),
                        name=f"{name}_{value_name}"
                    )
                    lines.append(line)
        
        return lines
    
    def _prepare_x_axis(self, bars: List[BarData]) -> Dict[str, Any]:
        """准备X轴数据"""
        if not bars:
            return {}
        
        # 时间标签
        time_labels = []
        label_positions = []
        
        # 选择合适的时间间隔显示标签
        total_bars = len(bars)
        step = max(1, total_bars // 10)  # 最多显示10个标签
        
        for i in range(0, total_bars, step):
            if i < len(bars):
                label_positions.append(float(i))
                time_labels.append(bars[i].datetime.strftime("%H:%M"))
        
        return {
            "type": "time",
            "labels": time_labels,
            "positions": label_positions,
            "range": [0, float(total_bars - 1)] if total_bars > 0 else [0, 1]
        }
    
    def _prepare_y_axis(self) -> Dict[str, Any]:
        """准备Y轴数据"""
        if not self._price_range:
            return {}
        
        min_price, max_price = self._price_range
        
        # 价格标签
        price_step = (max_price - min_price) / 8  # 8个价格档位
        price_labels = []
        label_positions = []
        
        for i in range(9):  # 0-8, 共9个标签
            price = min_price + i * price_step
            price_labels.append(f"{price:.{self.config.decimal_places}f}")
            label_positions.append(price)
        
        return {
            "type": "price",
            "labels": price_labels,
            "positions": label_positions,
            "range": [min_price, max_price]
        }
    
    def _get_default_viewport(self) -> Dict[str, Any]:
        """获取默认视口"""
        return {
            "x_min": 0,
            "x_max": self.config.max_bars,
            "y_min": self._price_range[0] if self._price_range else 0,
            "y_max": self._price_range[1] if self._price_range else 100,
            "auto_scale": self.config.auto_scale
        }
    
    def _get_indicator_color(self, indicator_name: str, value_name: str) -> str:
        """获取指标颜色"""
        # 预定义的指标颜色方案
        color_map = {
            "ma": {"ma": "#FF6B6B"},
            "ema": {"ema": "#4ECDC4"},
            "macd": {"macd": "#45B7D1", "signal": "#96CEB4", "histogram": "#FFEAA7"},
            "rsi": {"rsi": "#DDA0DD"},
            "boll": {"upper": "#FFB347", "middle": "#98D8C8", "lower": "#F7DC6F"},
            "kdj": {"k": "#AED6F1", "d": "#F8C471", "j": "#D5A6BD"}
        }
        
        if indicator_name in color_map and value_name in color_map[indicator_name]:
            return color_map[indicator_name][value_name]
        
        # 默认颜色
        return "#3498db"


class WebChartRenderer:
    """
    Web图表渲染器管理器
    
    管理多个图表渲染器，提供统一的渲染接口
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.renderers: Dict[str, ChartRenderer] = {}
        self.performance_monitor = PerformanceMonitor()
        
        logger.info("Web图表渲染器初始化完成")
    
    async def start(self) -> None:
        """启动渲染器"""
        logger.info("Web图表渲染器启动成功")
    
    async def stop(self) -> None:
        """停止渲染器"""
        self.renderers.clear()
        logger.info("Web图表渲染器已停止")
    
    async def create_chart_renderer(
        self,
        chart_id: str,
        chart_type: ChartType,
        config: Optional[ChartConfig] = None
    ) -> None:
        """创建图表渲染器"""
        try:
            if chart_id in self.renderers:
                logger.warning(f"图表渲染器 {chart_id} 已存在")
                return
            
            renderer = ChartRenderer(
                chart_id=chart_id,
                chart_type=chart_type,
                config=config or ChartConfig()
            )
            
            self.renderers[chart_id] = renderer
            
            logger.info(f"图表渲染器创建成功: {chart_id}")
            
        except Exception as e:
            logger.error(f"创建图表渲染器失败: {e}")
            raise
    
    async def delete_chart_renderer(self, chart_id: str) -> None:
        """删除图表渲染器"""
        try:
            if chart_id in self.renderers:
                del self.renderers[chart_id]
                logger.info(f"图表渲染器删除成功: {chart_id}")
            
        except Exception as e:
            logger.error(f"删除图表渲染器失败: {e}")
            raise
    
    async def prepare_render_data(
        self,
        chart_id: str,
        bars: List[BarData],
        indicators: Dict[str, IndicatorData],
        config: Optional[ChartConfig] = None
    ) -> Dict[str, Any]:
        """准备渲染数据"""
        try:
            if chart_id not in self.renderers:
                raise ValueError(f"图表渲染器 {chart_id} 不存在")
            
            renderer = self.renderers[chart_id]
            
            # 如果提供了新配置，更新渲染器配置
            if config:
                renderer.config = config
            
            # 准备渲染数据
            render_data = renderer.prepare_render_data(bars, indicators)
            
            # 记录性能指标
            self.performance_monitor.increment_counter(f"render_requests_{chart_id}")
            
            return render_data.to_dict()
            
        except Exception as e:
            logger.error(f"准备渲染数据失败: {e}")
            raise
    
    def get_renderer_status(self) -> Dict[str, Any]:
        """获取渲染器状态"""
        return {
            "renderers_count": len(self.renderers),
            "performance": self.performance_monitor.get_metrics(),
            "config": self.config
        }
