"""
图表配置值对象
"""

from typing import Dict, Any, List
from dataclasses import dataclass
from enum import Enum


class TimeFormat(str, Enum):
    """时间格式"""
    FORMAT_24H = "24h"
    FORMAT_12H = "12h"


class PriceScale(str, Enum):
    """价格刻度"""
    LINEAR = "linear"
    LOGARITHMIC = "logarithmic"


@dataclass(frozen=True)
class ChartConfig:
    """
    图表配置值对象
    
    包含图表显示的所有配置选项
    """
    # 显示配置
    width: int = 800
    height: int = 600
    theme: str = "light"
    
    # 数据配置
    max_bars: int = 1000
    auto_scale: bool = True
    price_scale: PriceScale = PriceScale.LINEAR
    
    # 时间配置
    time_format: TimeFormat = TimeFormat.FORMAT_24H
    show_timezone: bool = True
    
    # 图表样式
    show_grid: bool = True
    show_crosshair: bool = True
    show_volume: bool = True
    show_last_value_line: bool = True
    
    # 颜色配置
    background_color: str = "#ffffff"
    grid_color: str = "#e1e1e1"
    up_color: str = "#26a69a"
    down_color: str = "#ef5350"
    
    # 交互配置
    enable_zoom: bool = True
    enable_pan: bool = True
    enable_selection: bool = True
    
    # 指标配置
    default_indicators: List[str] = None
    
    def __post_init__(self):
        if self.default_indicators is None:
            object.__setattr__(self, 'default_indicators', [])
    
    def with_size(self, width: int, height: int) -> 'ChartConfig':
        """创建新的配置对象，修改尺寸"""
        return ChartConfig(
            width=width,
            height=height,
            theme=self.theme,
            max_bars=self.max_bars,
            auto_scale=self.auto_scale,
            price_scale=self.price_scale,
            time_format=self.time_format,
            show_timezone=self.show_timezone,
            show_grid=self.show_grid,
            show_crosshair=self.show_crosshair,
            show_volume=self.show_volume,
            show_last_value_line=self.show_last_value_line,
            background_color=self.background_color,
            grid_color=self.grid_color,
            up_color=self.up_color,
            down_color=self.down_color,
            enable_zoom=self.enable_zoom,
            enable_pan=self.enable_pan,
            enable_selection=self.enable_selection,
            default_indicators=self.default_indicators.copy()
        )
    
    def with_theme(self, theme: str) -> 'ChartConfig':
        """创建新的配置对象，修改主题"""
        colors = self._get_theme_colors(theme)
        return ChartConfig(
            width=self.width,
            height=self.height,
            theme=theme,
            max_bars=self.max_bars,
            auto_scale=self.auto_scale,
            price_scale=self.price_scale,
            time_format=self.time_format,
            show_timezone=self.show_timezone,
            show_grid=self.show_grid,
            show_crosshair=self.show_crosshair,
            show_volume=self.show_volume,
            show_last_value_line=self.show_last_value_line,
            background_color=colors.get("background", self.background_color),
            grid_color=colors.get("grid", self.grid_color),
            up_color=colors.get("up", self.up_color),
            down_color=colors.get("down", self.down_color),
            enable_zoom=self.enable_zoom,
            enable_pan=self.enable_pan,
            enable_selection=self.enable_selection,
            default_indicators=self.default_indicators.copy()
        )
    
    def _get_theme_colors(self, theme: str) -> Dict[str, str]:
        """获取主题颜色配置"""
        themes = {
            "light": {
                "background": "#ffffff",
                "grid": "#e1e1e1",
                "up": "#26a69a",
                "down": "#ef5350"
            },
            "dark": {
                "background": "#1e1e1e",
                "grid": "#333333",
                "up": "#4caf50",
                "down": "#f44336"
            }
        }
        return themes.get(theme, themes["light"])
