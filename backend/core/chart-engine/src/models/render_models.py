"""
图表渲染模型
定义图表渲染相关的数据结构
"""

from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional
from datetime import datetime
import json


@dataclass 
class CandleRenderData:
    """K线渲染数据"""
    datetime: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    
    # 渲染属性
    x: Optional[float] = None
    y_open: Optional[float] = None
    y_high: Optional[float] = None
    y_low: Optional[float] = None
    y_close: Optional[float] = None
    
    # 颜色属性
    color: Optional[str] = None
    is_rising: Optional[bool] = None
    
    def __post_init__(self):
        """后处理初始化"""
        if self.is_rising is None:
            self.is_rising = self.close >= self.open
        
        if self.color is None:
            self.color = "#00C851" if self.is_rising else "#FF4444"


@dataclass
class LineRenderData:
    """线条渲染数据"""
    name: str
    points: List[Dict[str, float]]  # [{"x": timestamp, "y": value}, ...]
    color: str = "#1f77b4"
    width: float = 1.0
    style: str = "solid"  # solid, dashed, dotted
    
    def add_point(self, x: float, y: float) -> None:
        """添加点"""
        self.points.append({"x": x, "y": y})


@dataclass
class AreaRenderData:
    """面积图渲染数据"""
    name: str
    points: List[Dict[str, float]]
    fill_color: str = "#1f77b4"
    fill_opacity: float = 0.3
    border_color: str = "#1f77b4"
    border_width: float = 1.0
    
    def add_point(self, x: float, y: float) -> None:
        """添加点"""
        self.points.append({"x": x, "y": y})


@dataclass
class VolumeRenderData:
    """成交量渲染数据"""
    datetime: datetime
    volume: float
    color: str
    
    # 渲染属性
    x: Optional[float] = None
    height: Optional[float] = None
    width: Optional[float] = None


@dataclass
class AxisConfig:
    """坐标轴配置"""
    type: str  # "time", "linear", "log"
    position: str  # "left", "right", "top", "bottom"
    label: str = ""
    show_grid: bool = True
    grid_color: str = "#E0E0E0"
    grid_style: str = "solid"
    
    # 刻度配置
    tick_count: int = 5
    tick_format: str = "auto"
    
    # 范围配置
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    auto_range: bool = True


@dataclass
class LegendConfig:
    """图例配置"""
    show: bool = True
    position: str = "top-right"  # top-left, top-right, bottom-left, bottom-right
    orientation: str = "vertical"  # horizontal, vertical
    
    # 样式配置
    background_color: str = "rgba(255, 255, 255, 0.9)"
    border_color: str = "#CCCCCC"
    border_width: float = 1.0
    padding: int = 8


@dataclass
class ChartRenderData:
    """完整的图表渲染数据"""
    chart_id: str
    chart_type: str
    
    # 数据
    candles: List[CandleRenderData] = None
    lines: List[LineRenderData] = None
    areas: List[AreaRenderData] = None
    volumes: List[VolumeRenderData] = None
    
    # 配置
    x_axis: AxisConfig = None
    y_axis: AxisConfig = None
    legend: LegendConfig = None
    
    # 视图配置
    width: int = 800
    height: int = 400
    margin: Dict[str, int] = None
    
    # 主题配置
    background_color: str = "#FFFFFF"
    grid_color: str = "#E0E0E0"
    
    def __post_init__(self):
        """后处理初始化"""
        if self.candles is None:
            self.candles = []
        if self.lines is None:
            self.lines = []
        if self.areas is None:
            self.areas = []
        if self.volumes is None:
            self.volumes = []
        
        if self.x_axis is None:
            self.x_axis = AxisConfig(type="time", position="bottom", label="时间")
        if self.y_axis is None:
            self.y_axis = AxisConfig(type="linear", position="right", label="价格")
        if self.legend is None:
            self.legend = LegendConfig()
        
        if self.margin is None:
            self.margin = {"top": 20, "right": 60, "bottom": 40, "left": 60}
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)
    
    def to_json(self) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.to_dict(), default=str, ensure_ascii=False)


@dataclass
class ChartTheme:
    """图表主题配置"""
    name: str
    
    # 背景颜色
    background_color: str = "#FFFFFF"
    grid_color: str = "#E0E0E0"
    border_color: str = "#CCCCCC"
    
    # K线颜色
    candle_up_color: str = "#00C851"
    candle_down_color: str = "#FF4444"
    candle_border_color: str = "#000000"
    
    # 线条颜色
    line_colors: List[str] = None
    
    # 文字颜色
    text_color: str = "#333333"
    axis_text_color: str = "#666666"
    
    # 字体配置
    font_family: str = "Arial, sans-serif"
    font_size: int = 12
    
    def __post_init__(self):
        """后处理初始化"""
        if self.line_colors is None:
            self.line_colors = [
                "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
                "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"
            ]


# 预定义主题
class ChartThemes:
    """预定义图表主题"""
    
    LIGHT = ChartTheme(
        name="light",
        background_color="#FFFFFF",
        grid_color="#E0E0E0",
        text_color="#333333"
    )
    
    DARK = ChartTheme(
        name="dark", 
        background_color="#1E1E1E",
        grid_color="#404040",
        border_color="#606060",
        candle_up_color="#00FF88",
        candle_down_color="#FF6666",
        text_color="#FFFFFF",
        axis_text_color="#CCCCCC"
    )
    
    PROFESSIONAL = ChartTheme(
        name="professional",
        background_color="#0A0E1A",
        grid_color="#1A1A2E",
        border_color="#2A2A4A",
        candle_up_color="#26A69A",
        candle_down_color="#EF5350",
        text_color="#E8E8E8",
        axis_text_color="#A0A0A0"
    )


@dataclass 
class RenderViewport:
    """渲染视口"""
    x: float
    y: float
    width: float
    height: float
    
    # 缩放和平移
    zoom: float = 1.0
    pan_x: float = 0.0
    pan_y: float = 0.0
    
    def contains_point(self, x: float, y: float) -> bool:
        """检查点是否在视口内"""
        return (self.x <= x <= self.x + self.width and 
                self.y <= y <= self.y + self.height)


@dataclass
class RenderContext:
    """渲染上下文"""
    viewport: RenderViewport
    theme: ChartTheme
    dpi_scale: float = 1.0
    
    # 渲染选项
    enable_animations: bool = True
    enable_interactions: bool = True
    enable_crosshair: bool = True
    
    # 性能选项
    max_visible_candles: int = 1000
    enable_level_of_detail: bool = True


@dataclass
class RenderConfig:
    """渲染配置"""
    width: int = 800
    height: int = 400
    theme: ChartTheme = None
    enable_animations: bool = True
    enable_interactions: bool = True
    
    def __post_init__(self):
        if self.theme is None:
            self.theme = ChartThemes.LIGHT


@dataclass  
class CanvasConfig:
    """Canvas配置"""
    width: int = 800
    height: int = 400
    dpi_scale: float = 1.0
    background_color: str = "#FFFFFF"
    

# RenderData别名
RenderData = ChartRenderData

# ColorScheme别名
ColorScheme = ChartTheme
