"""
指标仓储接口
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..entities.indicator_entity import Indicator, IndicatorStatus
from ..value_objects.indicator_type import IndicatorType


class IndicatorRepository(ABC):
    """
    指标仓储接口
    
    定义技术指标的持久化操作
    """
    
    @abstractmethod
    async def save(self, indicator: Indicator) -> Indicator:
        """保存指标"""
        pass
    
    @abstractmethod
    async def find_by_id(self, indicator_id: str) -> Optional[Indicator]:
        """根据ID查找指标"""
        pass
    
    @abstractmethod
    async def find_by_chart_id(self, chart_id: str) -> List[Indicator]:
        """根据图表ID查找指标"""
        pass
    
    @abstractmethod
    async def find_by_type(self, indicator_type: IndicatorType) -> List[Indicator]:
        """根据指标类型查找指标"""
        pass
    
    @abstractmethod
    async def find_by_status(self, status: IndicatorStatus) -> List[Indicator]:
        """根据状态查找指标"""
        pass
    
    @abstractmethod
    async def find_active_indicators(self) -> List[Indicator]:
        """查找所有激活的指标"""
        pass
    
    @abstractmethod
    async def update(self, indicator: Indicator) -> Indicator:
        """更新指标"""
        pass
    
    @abstractmethod
    async def delete(self, indicator_id: str) -> bool:
        """删除指标"""
        pass
    
    @abstractmethod
    async def exists(self, indicator_id: str) -> bool:
        """检查指标是否存在"""
        pass
    
    @abstractmethod
    async def count_by_type(self, indicator_type: IndicatorType) -> int:
        """统计指定类型的指标数量"""
        pass
    
    @abstractmethod
    async def find_indicators_created_after(self, created_after: datetime) -> List[Indicator]:
        """查找指定时间后创建的指标"""
        pass
    
    @abstractmethod
    async def find_error_indicators(self) -> List[Indicator]:
        """查找出错的指标"""
        pass
    
    @abstractmethod
    async def reset_indicator_status(self, indicator_id: str) -> bool:
        """重置指标状态"""
        pass
