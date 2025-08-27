"""
图表仓储接口
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..entities.chart_entity import Chart
from ..value_objects.chart_type import ChartType
from ..value_objects.interval import Interval


class ChartRepository(ABC):
    """
    图表仓储接口
    
    定义图表数据的持久化操作
    """
    
    @abstractmethod
    async def save(self, chart: Chart) -> Chart:
        """保存图表"""
        pass
    
    @abstractmethod
    async def find_by_id(self, chart_id: str) -> Optional[Chart]:
        """根据ID查找图表"""
        pass
    
    @abstractmethod
    async def find_by_symbol(self, symbol: str) -> List[Chart]:
        """根据交易品种查找图表"""
        pass
    
    @abstractmethod
    async def find_by_symbol_and_interval(
        self, 
        symbol: str, 
        interval: Interval
    ) -> Optional[Chart]:
        """根据交易品种和时间周期查找图表"""
        pass
    
    @abstractmethod
    async def find_active_charts(self) -> List[Chart]:
        """查找所有激活的图表"""
        pass
    
    @abstractmethod
    async def find_charts_with_subscribers(self) -> List[Chart]:
        """查找有订阅者的图表"""
        pass
    
    @abstractmethod
    async def update(self, chart: Chart) -> Chart:
        """更新图表"""
        pass
    
    @abstractmethod
    async def delete(self, chart_id: str) -> bool:
        """删除图表"""
        pass
    
    @abstractmethod
    async def exists(self, chart_id: str) -> bool:
        """检查图表是否存在"""
        pass
    
    @abstractmethod
    async def count_by_symbol(self, symbol: str) -> int:
        """统计指定交易品种的图表数量"""
        pass
    
    @abstractmethod
    async def find_charts_created_after(self, created_after: datetime) -> List[Chart]:
        """查找指定时间后创建的图表"""
        pass
    
    @abstractmethod
    async def find_charts_by_type(self, chart_type: ChartType) -> List[Chart]:
        """根据图表类型查找图表"""
        pass
