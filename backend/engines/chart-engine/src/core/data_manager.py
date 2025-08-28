"""
图表数据管理器 - 基于vnpy-core BarManager的Web优化版本

负责K线数据的存储、缓存、检索和管理
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict, deque
import numpy as np

from ..models.chart_models import BarData, Interval
from ..utils.cache import LRUCache
from ..utils.performance import PerformanceMonitor

logger = logging.getLogger(__name__)


class ChartDataBuffer:
    """
    图表数据缓冲区 - 基于vnpy-core BarManager设计
    
    高性能内存缓存，支持快速检索和更新
    """
    
    def __init__(self, max_size: int = 10000):
        self.max_size = max_size
        self.bars: deque[BarData] = deque(maxlen=max_size)
        self.datetime_index: Dict[datetime, int] = {}  # 时间索引
        self.symbol: Optional[str] = None
        self.interval: Optional[Interval] = None
        
    def add_bar(self, bar: BarData) -> None:
        """添加K线数据"""
        # 检查是否需要更新现有数据
        if bar.datetime in self.datetime_index:
            # 更新现有K线
            index = self.datetime_index[bar.datetime]
            if index < len(self.bars):
                self.bars[index] = bar
        else:
            # 添加新K线
            if len(self.bars) >= self.max_size:
                # 移除最老的数据
                old_bar = self.bars[0]
                if old_bar.datetime in self.datetime_index:
                    del self.datetime_index[old_bar.datetime]
            
            self.bars.append(bar)
            self.datetime_index[bar.datetime] = len(self.bars) - 1
        
        # 更新基础信息
        if not self.symbol:
            self.symbol = bar.symbol
    
    def get_bars(self, count: Optional[int] = None) -> List[BarData]:
        """获取K线数据"""
        if count is None:
            return list(self.bars)
        return list(self.bars)[-count:] if count > 0 else []
    
    def get_bars_by_time_range(
        self, 
        start_time: datetime, 
        end_time: datetime
    ) -> List[BarData]:
        """按时间范围获取K线数据"""
        result = []
        for bar in self.bars:
            if start_time <= bar.datetime <= end_time:
                result.append(bar)
        return result
    
    def get_latest_bar(self) -> Optional[BarData]:
        """获取最新K线"""
        return self.bars[-1] if self.bars else None
    
    def get_bar_by_datetime(self, dt: datetime) -> Optional[BarData]:
        """根据时间获取K线"""
        if dt in self.datetime_index:
            index = self.datetime_index[dt]
            if index < len(self.bars):
                return self.bars[index]
        return None
    
    def clear(self) -> None:
        """清空数据"""
        self.bars.clear()
        self.datetime_index.clear()
    
    def size(self) -> int:
        """获取数据数量"""
        return len(self.bars)
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        if not self.bars:
            return {"count": 0}
        
        prices = [bar.close_price for bar in self.bars]
        volumes = [bar.volume for bar in self.bars]
        
        return {
            "count": len(self.bars),
            "symbol": self.symbol,
            "interval": self.interval.value if self.interval else None,
            "time_range": {
                "start": self.bars[0].datetime.isoformat(),
                "end": self.bars[-1].datetime.isoformat()
            },
            "price_range": {
                "min": min(prices),
                "max": max(prices),
                "latest": prices[-1]
            },
            "volume_range": {
                "min": min(volumes),
                "max": max(volumes),
                "total": sum(volumes)
            }
        }


class ChartDataManager:
    """
    图表数据管理器
    
    功能特性:
    1. 多图表数据并发管理
    2. 高性能内存缓存
    3. 数据持久化支持
    4. 实时数据更新
    5. 历史数据加载
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # 数据缓冲区管理
        self.buffers: Dict[str, ChartDataBuffer] = {}  # chart_id -> buffer
        
        # 缓存管理
        self.cache_size = self.config.get('cache_size', 1000)
        self.cache = LRUCache(self.cache_size)
        
        # 性能监控
        self.performance_monitor = PerformanceMonitor()
        
        # 配置
        self.max_buffer_size = self.config.get('max_buffer_size', 10000)
        self.cache_ttl = self.config.get('cache_ttl', 300)  # 5分钟
        
        # 数据源配置 (可扩展支持数据库、文件等)
        self.data_sources = self.config.get('data_sources', {})
        
        # 运行状态
        self.is_running = False
        
        logger.info("图表数据管理器初始化完成")
    
    async def start(self) -> None:
        """启动数据管理器"""
        try:
            self.is_running = True
            
            # 启动缓存清理任务
            asyncio.create_task(self._cache_cleanup_loop())
            
            logger.info("图表数据管理器启动成功")
            
        except Exception as e:
            logger.error(f"图表数据管理器启动失败: {e}")
            raise
    
    async def stop(self) -> None:
        """停止数据管理器"""
        try:
            self.is_running = False
            
            # 清理资源
            self.buffers.clear()
            self.cache.clear()
            
            logger.info("图表数据管理器已停止")
            
        except Exception as e:
            logger.error(f"图表数据管理器停止失败: {e}")
            raise
    
    async def create_chart_data(
        self, 
        chart_id: str, 
        symbol: str, 
        interval: Interval
    ) -> None:
        """创建图表数据缓冲区"""
        try:
            if chart_id in self.buffers:
                logger.warning(f"图表数据 {chart_id} 已存在")
                return
            
            # 创建数据缓冲区
            buffer = ChartDataBuffer(max_size=self.max_buffer_size)
            buffer.symbol = symbol
            buffer.interval = interval
            
            self.buffers[chart_id] = buffer
            
            # 加载历史数据
            await self._load_historical_data(chart_id, symbol, interval)
            
            logger.info(f"图表数据创建成功: {chart_id} ({symbol}, {interval.value})")
            
        except Exception as e:
            logger.error(f"创建图表数据失败: {e}")
            raise
    
    async def delete_chart_data(self, chart_id: str) -> None:
        """删除图表数据"""
        try:
            if chart_id in self.buffers:
                self.buffers[chart_id].clear()
                del self.buffers[chart_id]
            
            # 清理相关缓存
            cache_keys = [key for key in self.cache.keys() if chart_id in key]
            for key in cache_keys:
                self.cache.delete(key)
            
            logger.info(f"图表数据删除成功: {chart_id}")
            
        except Exception as e:
            logger.error(f"删除图表数据失败: {e}")
            raise
    
    async def add_bar_data(self, chart_id: str, bar: BarData) -> None:
        """添加K线数据"""
        try:
            if chart_id not in self.buffers:
                raise ValueError(f"图表数据 {chart_id} 不存在")
            
            buffer = self.buffers[chart_id]
            buffer.add_bar(bar)
            
            # 记录性能指标
            self.performance_monitor.record_metric(f'bars_count_{chart_id}', buffer.size())
            
            # 清理相关缓存
            cache_pattern = f"{chart_id}_bars_"
            self._invalidate_cache_by_pattern(cache_pattern)
            
        except Exception as e:
            logger.error(f"添加K线数据失败: {e}")
            raise
    
    async def get_chart_data(
        self, 
        chart_id: str, 
        limit: Optional[int] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[BarData]:
        """获取图表数据"""
        try:
            if chart_id not in self.buffers:
                return []
            
            # 尝试从缓存获取
            cache_key = f"{chart_id}_bars_{limit}_{start_time}_{end_time}"
            cached_data = self.cache.get(cache_key)
            if cached_data:
                return cached_data
            
            buffer = self.buffers[chart_id]
            
            # 根据条件获取数据
            if start_time and end_time:
                bars = buffer.get_bars_by_time_range(start_time, end_time)
            elif limit:
                bars = buffer.get_bars(limit)
            else:
                bars = buffer.get_bars()
            
            # 缓存结果
            self.cache.set(cache_key, bars, ttl=self.cache_ttl)
            
            return bars
            
        except Exception as e:
            logger.error(f"获取图表数据失败: {e}")
            return []
    
    async def get_latest_bar(self, chart_id: str) -> Optional[BarData]:
        """获取最新K线"""
        try:
            if chart_id not in self.buffers:
                return None
            
            return self.buffers[chart_id].get_latest_bar()
            
        except Exception as e:
            logger.error(f"获取最新K线失败: {e}")
            return None
    
    async def get_bar_by_datetime(self, chart_id: str, dt: datetime) -> Optional[BarData]:
        """根据时间获取K线"""
        try:
            if chart_id not in self.buffers:
                return None
            
            return self.buffers[chart_id].get_bar_by_datetime(dt)
            
        except Exception as e:
            logger.error(f"根据时间获取K线失败: {e}")
            return None
    
    async def get_price_range(
        self, 
        chart_id: str, 
        count: Optional[int] = None
    ) -> Tuple[float, float]:
        """获取价格范围 (最低价, 最高价)"""
        try:
            bars = await self.get_chart_data(chart_id, limit=count)
            if not bars:
                return 0.0, 0.0
            
            lows = [bar.low_price for bar in bars]
            highs = [bar.high_price for bar in bars]
            
            return min(lows), max(highs)
            
        except Exception as e:
            logger.error(f"获取价格范围失败: {e}")
            return 0.0, 0.0
    
    async def get_volume_range(
        self, 
        chart_id: str, 
        count: Optional[int] = None
    ) -> Tuple[float, float]:
        """获取成交量范围 (最小量, 最大量)"""
        try:
            bars = await self.get_chart_data(chart_id, limit=count)
            if not bars:
                return 0.0, 0.0
            
            volumes = [bar.volume for bar in bars]
            return min(volumes), max(volumes)
            
        except Exception as e:
            logger.error(f"获取成交量范围失败: {e}")
            return 0.0, 0.0
    
    async def get_chart_statistics(self, chart_id: str) -> Dict[str, Any]:
        """获取图表统计信息"""
        try:
            if chart_id not in self.buffers:
                return {"error": "图表不存在"}
            
            return self.buffers[chart_id].get_statistics()
            
        except Exception as e:
            logger.error(f"获取图表统计信息失败: {e}")
            return {"error": str(e)}
    
    async def cleanup_cache(self) -> None:
        """清理过期缓存"""
        try:
            cleaned_count = self.cache.cleanup()
            if cleaned_count > 0:
                logger.debug(f"清理了 {cleaned_count} 个过期缓存项")
            
        except Exception as e:
            logger.error(f"清理缓存失败: {e}")
    
    def _invalidate_cache_by_pattern(self, pattern: str) -> None:
        """根据模式清理缓存"""
        keys_to_delete = [key for key in self.cache.keys() if pattern in key]
        for key in keys_to_delete:
            self.cache.delete(key)
    
    async def _load_historical_data(
        self, 
        chart_id: str, 
        symbol: str, 
        interval: Interval
    ) -> None:
        """加载历史数据 (预留接口，可连接数据库、文件等)"""
        try:
            # 这里可以实现从数据库、文件或其他数据源加载历史数据
            # 暂时使用模拟数据
            
            if 'mock_data' in self.data_sources and self.data_sources['mock_data']:
                await self._load_mock_data(chart_id, symbol, interval)
            
        except Exception as e:
            logger.error(f"加载历史数据失败: {e}")
    
    async def _load_mock_data(
        self, 
        chart_id: str, 
        symbol: str, 
        interval: Interval
    ) -> None:
        """加载模拟数据 (用于测试)"""
        try:
            # 生成模拟K线数据
            now = datetime.now()
            base_price = 100.0
            
            for i in range(100):  # 生成100根K线
                dt = now - timedelta(minutes=i)
                
                # 简单的随机价格生成
                price = base_price + np.random.uniform(-5, 5)
                high = price + np.random.uniform(0, 2)
                low = price - np.random.uniform(0, 2)
                volume = np.random.uniform(1000, 10000)
                
                bar = BarData(
                    symbol=symbol,
                    datetime=dt,
                    open_price=price,
                    high_price=high,
                    low_price=low,
                    close_price=price + np.random.uniform(-1, 1),
                    volume=volume
                )
                
                await self.add_bar_data(chart_id, bar)
            
            logger.info(f"加载模拟数据完成: {chart_id} (100根K线)")
            
        except Exception as e:
            logger.error(f"加载模拟数据失败: {e}")
    
    async def _cache_cleanup_loop(self) -> None:
        """缓存清理循环"""
        while self.is_running:
            try:
                await self.cleanup_cache()
                await asyncio.sleep(60)  # 每分钟清理一次
                
            except Exception as e:
                logger.error(f"缓存清理循环错误: {e}")
                await asyncio.sleep(60)
    
    def get_manager_status(self) -> Dict[str, Any]:
        """获取管理器状态"""
        return {
            "is_running": self.is_running,
            "buffers_count": len(self.buffers),
            "cache_size": self.cache.size(),
            "cache_hit_rate": self.cache.get_hit_rate(),
            "performance": self.performance_monitor.get_metrics(),
            "config": self.config
        }
