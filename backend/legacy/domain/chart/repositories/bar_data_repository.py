"""
K线数据仓储接口
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..entities.bar_data_entity import BarData
from ..value_objects.interval import Interval


class BarDataRepository(ABC):
    """
    K线数据仓储接口
    
    定义K线数据的持久化和查询操作
    """
    
    @abstractmethod
    async def save_bar(self, bar: BarData) -> BarData:
        """保存单根K线"""
        pass
    
    @abstractmethod
    async def save_bars(self, bars: List[BarData]) -> List[BarData]:
        """批量保存K线"""
        pass
    
    @abstractmethod
    async def find_bars(
        self,
        symbol: str,
        interval: Interval,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> List[BarData]:
        """查找K线数据"""
        pass
    
    @abstractmethod
    async def find_latest_bar(self, symbol: str, interval: Interval) -> Optional[BarData]:
        """查找最新的K线"""
        pass
    
    @abstractmethod
    async def find_bars_count(
        self,
        symbol: str,
        interval: Interval,
        count: int
    ) -> List[BarData]:
        """查找指定数量的最新K线"""
        pass
    
    @abstractmethod
    async def update_bar(self, bar: BarData) -> BarData:
        """更新K线数据"""
        pass
    
    @abstractmethod
    async def delete_bars(
        self,
        symbol: str,
        interval: Interval,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> int:
        """删除K线数据，返回删除数量"""
        pass
    
    @abstractmethod
    async def exists_bar(
        self,
        symbol: str,
        interval: Interval,
        datetime: datetime
    ) -> bool:
        """检查K线是否存在"""
        pass
    
    @abstractmethod
    async def get_time_range(
        self,
        symbol: str,
        interval: Interval
    ) -> Optional[Dict[str, datetime]]:
        """获取K线数据的时间范围"""
        pass
    
    @abstractmethod
    async def count_bars(
        self,
        symbol: str,
        interval: Interval,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> int:
        """统计K线数量"""
        pass
    
    @abstractmethod
    async def get_symbols(self) -> List[str]:
        """获取所有交易品种"""
        pass
    
    @abstractmethod
    async def get_intervals_by_symbol(self, symbol: str) -> List[Interval]:
        """获取指定交易品种的所有时间周期"""
        pass
    
    @abstractmethod
    async def cleanup_old_data(
        self,
        symbol: str,
        interval: Interval,
        keep_days: int
    ) -> int:
        """清理旧数据，返回清理数量"""
        pass
