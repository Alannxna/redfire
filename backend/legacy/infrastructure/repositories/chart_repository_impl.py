"""
图表仓储实现
"""

import json
from typing import List, Optional, Dict, Any
from datetime import datetime

from src.domain.chart.entities.chart_entity import Chart
from src.domain.chart.value_objects.chart_type import ChartType
from src.domain.chart.value_objects.interval import Interval
from src.domain.chart.repositories.chart_repository import ChartRepository


class InMemoryChartRepository(ChartRepository):
    """
    内存图表仓储实现（用于演示）
    
    实际生产环境应该使用数据库实现
    """
    
    def __init__(self):
        self._charts: Dict[str, Chart] = {}
    
    async def save(self, chart: Chart) -> Chart:
        """保存图表"""
        self._charts[chart.chart_id] = chart
        return chart
    
    async def find_by_id(self, chart_id: str) -> Optional[Chart]:
        """根据ID查找图表"""
        return self._charts.get(chart_id)
    
    async def find_by_symbol(self, symbol: str) -> List[Chart]:
        """根据交易品种查找图表"""
        return [chart for chart in self._charts.values() if chart.symbol == symbol]
    
    async def find_by_symbol_and_interval(
        self, 
        symbol: str, 
        interval: Interval
    ) -> Optional[Chart]:
        """根据交易品种和时间周期查找图表"""
        for chart in self._charts.values():
            if chart.symbol == symbol and chart.interval == interval:
                return chart
        return None
    
    async def find_active_charts(self) -> List[Chart]:
        """查找所有激活的图表"""
        return [chart for chart in self._charts.values() if chart.is_active]
    
    async def find_charts_with_subscribers(self) -> List[Chart]:
        """查找有订阅者的图表"""
        return [chart for chart in self._charts.values() if chart.subscriber_count > 0]
    
    async def update(self, chart: Chart) -> Chart:
        """更新图表"""
        if chart.chart_id in self._charts:
            self._charts[chart.chart_id] = chart
        return chart
    
    async def delete(self, chart_id: str) -> bool:
        """删除图表"""
        if chart_id in self._charts:
            del self._charts[chart_id]
            return True
        return False
    
    async def exists(self, chart_id: str) -> bool:
        """检查图表是否存在"""
        return chart_id in self._charts
    
    async def count_by_symbol(self, symbol: str) -> int:
        """统计指定交易品种的图表数量"""
        return len([chart for chart in self._charts.values() if chart.symbol == symbol])
    
    async def find_charts_created_after(self, created_after: datetime) -> List[Chart]:
        """查找指定时间后创建的图表"""
        return [
            chart for chart in self._charts.values() 
            if chart.created_at > created_after
        ]
    
    async def find_charts_by_type(self, chart_type: ChartType) -> List[Chart]:
        """根据图表类型查找图表"""
        return [chart for chart in self._charts.values() if chart.chart_type == chart_type]
