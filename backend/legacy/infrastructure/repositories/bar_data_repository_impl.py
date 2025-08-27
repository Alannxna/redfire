"""
K线数据仓储实现
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from src.domain.chart.entities.bar_data_entity import BarData
from src.domain.chart.value_objects.interval import Interval
from src.domain.chart.repositories.bar_data_repository import BarDataRepository


class InMemoryBarDataRepository(BarDataRepository):
    """
    内存K线数据仓储实现（用于演示）
    
    实际生产环境应该使用时序数据库实现
    """
    
    def __init__(self):
        # 数据结构: {symbol: {interval: [BarData]}}
        self._bars: Dict[str, Dict[str, List[BarData]]] = {}
    
    async def save_bar(self, bar: BarData) -> BarData:
        """保存单根K线"""
        if bar.symbol not in self._bars:
            self._bars[bar.symbol] = {}
        
        interval_key = bar.interval if hasattr(bar, 'interval') else "1m"
        if interval_key not in self._bars[bar.symbol]:
            self._bars[bar.symbol][interval_key] = []
        
        # 检查是否已存在相同时间的K线
        bars_list = self._bars[bar.symbol][interval_key]
        for i, existing_bar in enumerate(bars_list):
            if existing_bar.datetime == bar.datetime:
                # 更新现有K线
                bars_list[i] = bar
                return bar
        
        # 添加新K线并保持时间顺序
        bars_list.append(bar)
        bars_list.sort(key=lambda x: x.datetime)
        
        return bar
    
    async def save_bars(self, bars: List[BarData]) -> List[BarData]:
        """批量保存K线"""
        for bar in bars:
            await self.save_bar(bar)
        return bars
    
    async def find_bars(
        self,
        symbol: str,
        interval: Interval,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> List[BarData]:
        """查找K线数据"""
        if symbol not in self._bars:
            return []
        
        interval_key = interval.value
        if interval_key not in self._bars[symbol]:
            return []
        
        bars = self._bars[symbol][interval_key].copy()
        
        # 时间过滤
        if start_time:
            bars = [bar for bar in bars if bar.datetime >= start_time]
        
        if end_time:
            bars = [bar for bar in bars if bar.datetime <= end_time]
        
        # 排序
        bars.sort(key=lambda x: x.datetime)
        
        # 限制数量
        if limit:
            bars = bars[-limit:]
        
        return bars
    
    async def find_latest_bar(self, symbol: str, interval: Interval) -> Optional[BarData]:
        """查找最新的K线"""
        bars = await self.find_bars(symbol, interval, limit=1)
        return bars[0] if bars else None
    
    async def find_bars_count(
        self,
        symbol: str,
        interval: Interval,
        count: int
    ) -> List[BarData]:
        """查找指定数量的最新K线"""
        return await self.find_bars(symbol, interval, limit=count)
    
    async def update_bar(self, bar: BarData) -> BarData:
        """更新K线数据"""
        return await self.save_bar(bar)
    
    async def delete_bars(
        self,
        symbol: str,
        interval: Interval,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> int:
        """删除K线数据，返回删除数量"""
        if symbol not in self._bars:
            return 0
        
        interval_key = interval.value
        if interval_key not in self._bars[symbol]:
            return 0
        
        bars = self._bars[symbol][interval_key]
        original_count = len(bars)
        
        # 过滤要保留的K线
        filtered_bars = []
        for bar in bars:
            should_delete = True
            
            if start_time and bar.datetime < start_time:
                should_delete = False
            
            if end_time and bar.datetime > end_time:
                should_delete = False
            
            if not should_delete:
                filtered_bars.append(bar)
        
        self._bars[symbol][interval_key] = filtered_bars
        return original_count - len(filtered_bars)
    
    async def exists_bar(
        self,
        symbol: str,
        interval: Interval,
        datetime: datetime
    ) -> bool:
        """检查K线是否存在"""
        if symbol not in self._bars:
            return False
        
        interval_key = interval.value
        if interval_key not in self._bars[symbol]:
            return False
        
        for bar in self._bars[symbol][interval_key]:
            if bar.datetime == datetime:
                return True
        
        return False
    
    async def get_time_range(
        self,
        symbol: str,
        interval: Interval
    ) -> Optional[Dict[str, datetime]]:
        """获取K线数据的时间范围"""
        bars = await self.find_bars(symbol, interval)
        
        if not bars:
            return None
        
        return {
            "start": min(bar.datetime for bar in bars),
            "end": max(bar.datetime for bar in bars)
        }
    
    async def count_bars(
        self,
        symbol: str,
        interval: Interval,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> int:
        """统计K线数量"""
        bars = await self.find_bars(symbol, interval, start_time, end_time)
        return len(bars)
    
    async def get_symbols(self) -> List[str]:
        """获取所有交易品种"""
        return list(self._bars.keys())
    
    async def get_intervals_by_symbol(self, symbol: str) -> List[Interval]:
        """获取指定交易品种的所有时间周期"""
        if symbol not in self._bars:
            return []
        
        interval_keys = list(self._bars[symbol].keys())
        intervals = []
        
        for interval_key in interval_keys:
            try:
                intervals.append(Interval(interval_key))
            except ValueError:
                continue
        
        return intervals
    
    async def cleanup_old_data(
        self,
        symbol: str,
        interval: Interval,
        keep_days: int
    ) -> int:
        """清理旧数据，返回清理数量"""
        cutoff_time = datetime.now() - timedelta(days=keep_days)
        return await self.delete_bars(symbol, interval, end_time=cutoff_time)
