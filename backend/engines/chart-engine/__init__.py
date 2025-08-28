"""
RedFire Chart Engine
专业量化交易图表引擎

基于vnpy-core的Web图表解决方案，提供高性能、高并发的专业图表服务
"""

__version__ = "1.0.0"
__author__ = "RedFire Team"

# 导出主要组件
try:
    from .src.core.chart_engine import ChartEngine
    from .src.core.data_manager import ChartDataManager
    from .src.core.renderer import WebChartRenderer
    from .src.core.calculator import IndicatorCalculator
    from .src.api.chart_api import ChartEngineAPI
    from .src.api.websocket_handler import ChartWebSocketHandler
    
    __all__ = [
        "ChartEngine",
        "ChartDataManager", 
        "WebChartRenderer",
        "IndicatorCalculator",
        "ChartEngineAPI",
        "ChartWebSocketHandler"
    ]
    
except ImportError as e:
    # 在开发环境中，可能出现循环导入，这是正常的
    import warnings
    warnings.warn(f"Chart Engine导入警告: {e}", ImportWarning)
    __all__ = []
