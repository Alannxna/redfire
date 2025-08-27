"""
指标仓储实现
"""

from typing import List, Optional, Dict, Any
from datetime import datetime

from src.domain.chart.entities.indicator_entity import Indicator, IndicatorStatus
from src.domain.chart.value_objects.indicator_type import IndicatorType
from src.domain.chart.repositories.indicator_repository import IndicatorRepository


class InMemoryIndicatorRepository(IndicatorRepository):
    """
    内存指标仓储实现（用于演示）
    
    实际生产环境应该使用数据库实现
    """
    
    def __init__(self):
        self._indicators: Dict[str, Indicator] = {}
        # chart_id -> indicator_ids 映射
        self._chart_indicators: Dict[str, List[str]] = {}
    
    async def save(self, indicator: Indicator) -> Indicator:
        """保存指标"""
        self._indicators[indicator.indicator_id] = indicator
        return indicator
    
    def associate_with_chart(self, indicator_id: str, chart_id: str) -> None:
        """关联指标与图表"""
        if chart_id not in self._chart_indicators:
            self._chart_indicators[chart_id] = []
        
        if indicator_id not in self._chart_indicators[chart_id]:
            self._chart_indicators[chart_id].append(indicator_id)
    
    async def find_by_id(self, indicator_id: str) -> Optional[Indicator]:
        """根据ID查找指标"""
        return self._indicators.get(indicator_id)
    
    async def find_by_chart_id(self, chart_id: str) -> List[Indicator]:
        """根据图表ID查找指标"""
        indicator_ids = self._chart_indicators.get(chart_id, [])
        indicators = []
        
        for indicator_id in indicator_ids:
            indicator = self._indicators.get(indicator_id)
            if indicator:
                indicators.append(indicator)
        
        return indicators
    
    async def find_by_type(self, indicator_type: IndicatorType) -> List[Indicator]:
        """根据指标类型查找指标"""
        return [
            indicator for indicator in self._indicators.values()
            if indicator.indicator_type == indicator_type
        ]
    
    async def find_by_status(self, status: IndicatorStatus) -> List[Indicator]:
        """根据状态查找指标"""
        return [
            indicator for indicator in self._indicators.values()
            if indicator.status == status
        ]
    
    async def find_active_indicators(self) -> List[Indicator]:
        """查找所有激活的指标"""
        return await self.find_by_status(IndicatorStatus.ACTIVE)
    
    async def update(self, indicator: Indicator) -> Indicator:
        """更新指标"""
        if indicator.indicator_id in self._indicators:
            self._indicators[indicator.indicator_id] = indicator
        return indicator
    
    async def delete(self, indicator_id: str) -> bool:
        """删除指标"""
        if indicator_id in self._indicators:
            del self._indicators[indicator_id]
            
            # 清理图表关联
            for chart_id, indicator_ids in self._chart_indicators.items():
                if indicator_id in indicator_ids:
                    indicator_ids.remove(indicator_id)
            
            return True
        return False
    
    async def exists(self, indicator_id: str) -> bool:
        """检查指标是否存在"""
        return indicator_id in self._indicators
    
    async def count_by_type(self, indicator_type: IndicatorType) -> int:
        """统计指定类型的指标数量"""
        return len([
            indicator for indicator in self._indicators.values()
            if indicator.indicator_type == indicator_type
        ])
    
    async def find_indicators_created_after(self, created_after: datetime) -> List[Indicator]:
        """查找指定时间后创建的指标"""
        return [
            indicator for indicator in self._indicators.values()
            if indicator.created_at > created_after
        ]
    
    async def find_error_indicators(self) -> List[Indicator]:
        """查找出错的指标"""
        return await self.find_by_status(IndicatorStatus.ERROR)
    
    async def reset_indicator_status(self, indicator_id: str) -> bool:
        """重置指标状态"""
        indicator = self._indicators.get(indicator_id)
        if indicator:
            indicator.status = IndicatorStatus.INACTIVE
            indicator.updated_at = datetime.now()
            return True
        return False
