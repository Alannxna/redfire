"""
图表引擎核心 - 基于vnpy-core图表组件的Web图表引擎

移植vnpy强大的桌面图表能力到现代Web平台
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import json

from .data_manager import ChartDataManager
from .renderer import WebChartRenderer  
from .calculator import IndicatorCalculator
from ..models.chart_models import (
    ChartConfig, ChartType, Interval, BarData, 
    ChartUpdateEvent, SubscriptionInfo
)
from ..utils.performance import PerformanceMonitor

logger = logging.getLogger(__name__)


class ChartEngineStatus(str, Enum):
    """图表引擎状态"""
    STOPPED = "stopped"
    STARTING = "starting" 
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"


@dataclass
class ChartInstance:
    """图表实例"""
    chart_id: str
    symbol: str
    chart_type: ChartType
    interval: Interval
    config: ChartConfig
    created_at: datetime = field(default_factory=datetime.now)
    last_update: Optional[datetime] = None
    subscribers: List[str] = field(default_factory=list)
    is_active: bool = True
    bar_count: int = 0
    
    def add_subscriber(self, subscriber_id: str) -> None:
        """添加订阅者"""
        if subscriber_id not in self.subscribers:
            self.subscribers.append(subscriber_id)
    
    def remove_subscriber(self, subscriber_id: str) -> None:
        """移除订阅者"""
        if subscriber_id in self.subscribers:
            self.subscribers.remove(subscriber_id)


class ChartEngine:
    """
    RedFire图表引擎核心
    
    功能特性:
    1. 基于vnpy-core的专业图表算法
    2. 高性能Web渲染 (Canvas/WebGL)
    3. 实时数据流处理
    4. 技术指标计算
    5. 多图表并发管理
    
    架构设计:
    ChartEngine (核心引擎)
    ├── ChartDataManager (数据管理)
    ├── WebChartRenderer (Web渲染器)
    ├── IndicatorCalculator (指标计算器)
    └── PerformanceMonitor (性能监控)
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化图表引擎"""
        self.config = config or {}
        self.status = ChartEngineStatus.STOPPED
        
        # 核心组件
        self.data_manager = ChartDataManager()
        self.renderer = WebChartRenderer()
        self.calculator = IndicatorCalculator()
        self.performance_monitor = PerformanceMonitor()
        
        # 图表实例管理
        self.charts: Dict[str, ChartInstance] = {}
        self.subscriber_charts: Dict[str, List[str]] = {}  # subscriber_id -> chart_ids
        
        # 事件回调
        self.event_callbacks: Dict[str, List[Callable]] = {
            'chart_created': [],
            'chart_updated': [],
            'chart_deleted': [],
            'data_received': [],
            'error_occurred': []
        }
        
        # 性能配置
        self.max_charts = self.config.get('max_charts', 100)
        self.max_bars_per_chart = self.config.get('max_bars_per_chart', 10000)
        self.update_batch_size = self.config.get('update_batch_size', 50)
        self.render_fps = self.config.get('render_fps', 60)
        
        # 缓存配置
        self.cache_size = self.config.get('cache_size', 1000)
        self.cache_ttl = self.config.get('cache_ttl', 300)  # 5分钟
        
        logger.info("图表引擎初始化完成")
    
    async def start(self) -> None:
        """启动图表引擎"""
        try:
            self.status = ChartEngineStatus.STARTING
            logger.info("正在启动图表引擎...")
            
            # 启动核心组件
            await self.data_manager.start()
            await self.renderer.start()
            await self.calculator.start()
            
            # 启动性能监控
            self.performance_monitor.start()
            
            # 启动数据更新任务
            asyncio.create_task(self._run_update_loop())
            
            self.status = ChartEngineStatus.RUNNING
            logger.info("图表引擎启动成功")
            
        except Exception as e:
            self.status = ChartEngineStatus.ERROR
            logger.error(f"图表引擎启动失败: {e}")
            raise
    
    async def stop(self) -> None:
        """停止图表引擎"""
        try:
            self.status = ChartEngineStatus.STOPPING
            logger.info("正在停止图表引擎...")
            
            # 停止核心组件
            await self.data_manager.stop()
            await self.renderer.stop()
            await self.calculator.stop()
            
            # 停止性能监控
            self.performance_monitor.stop()
            
            # 清理资源
            self.charts.clear()
            self.subscriber_charts.clear()
            
            self.status = ChartEngineStatus.STOPPED
            logger.info("图表引擎已停止")
            
        except Exception as e:
            self.status = ChartEngineStatus.ERROR
            logger.error(f"图表引擎停止失败: {e}")
            raise
    
    async def create_chart(
        self,
        chart_id: str,
        symbol: str,
        chart_type: ChartType = ChartType.CANDLESTICK,
        interval: Interval = Interval.MINUTE_1,
        config: Optional[ChartConfig] = None
    ) -> ChartInstance:
        """创建新图表"""
        try:
            if chart_id in self.charts:
                raise ValueError(f"图表 {chart_id} 已存在")
            
            if len(self.charts) >= self.max_charts:
                raise ValueError(f"图表数量已达上限 {self.max_charts}")
            
            # 创建图表实例
            chart = ChartInstance(
                chart_id=chart_id,
                symbol=symbol,
                chart_type=chart_type,
                interval=interval,
                config=config or ChartConfig()
            )
            
            # 初始化数据
            await self.data_manager.create_chart_data(chart_id, symbol, interval)
            
            # 初始化渲染器
            await self.renderer.create_chart_renderer(chart_id, chart_type, config)
            
            # 注册图表
            self.charts[chart_id] = chart
            
            # 触发事件
            await self._trigger_event('chart_created', chart)
            
            logger.info(f"图表创建成功: {chart_id} ({symbol}, {interval})")
            return chart
            
        except Exception as e:
            logger.error(f"创建图表失败: {e}")
            raise
    
    async def delete_chart(self, chart_id: str) -> None:
        """删除图表"""
        try:
            if chart_id not in self.charts:
                raise ValueError(f"图表 {chart_id} 不存在")
            
            chart = self.charts[chart_id]
            
            # 清理数据
            await self.data_manager.delete_chart_data(chart_id)
            
            # 清理渲染器
            await self.renderer.delete_chart_renderer(chart_id)
            
            # 清理订阅关系
            for subscriber_id, chart_ids in self.subscriber_charts.items():
                if chart_id in chart_ids:
                    chart_ids.remove(chart_id)
            
            # 删除图表
            del self.charts[chart_id]
            
            # 触发事件
            await self._trigger_event('chart_deleted', chart)
            
            logger.info(f"图表删除成功: {chart_id}")
            
        except Exception as e:
            logger.error(f"删除图表失败: {e}")
            raise
    
    async def subscribe_chart(self, chart_id: str, subscriber_id: str) -> SubscriptionInfo:
        """订阅图表"""
        try:
            if chart_id not in self.charts:
                raise ValueError(f"图表 {chart_id} 不存在")
            
            chart = self.charts[chart_id]
            chart.add_subscriber(subscriber_id)
            
            # 更新订阅映射
            if subscriber_id not in self.subscriber_charts:
                self.subscriber_charts[subscriber_id] = []
            if chart_id not in self.subscriber_charts[subscriber_id]:
                self.subscriber_charts[subscriber_id].append(chart_id)
            
            # 获取初始数据
            initial_data = await self.data_manager.get_chart_data(
                chart_id, limit=self.max_bars_per_chart
            )
            
            subscription_info = SubscriptionInfo(
                chart_id=chart_id,
                subscriber_id=subscriber_id,
                initial_data=initial_data,
                config=chart.config
            )
            
            logger.info(f"订阅图表成功: {subscriber_id} -> {chart_id}")
            return subscription_info
            
        except Exception as e:
            logger.error(f"订阅图表失败: {e}")
            raise
    
    async def unsubscribe_chart(self, chart_id: str, subscriber_id: str) -> None:
        """取消订阅图表"""
        try:
            if chart_id in self.charts:
                self.charts[chart_id].remove_subscriber(subscriber_id)
            
            if subscriber_id in self.subscriber_charts:
                if chart_id in self.subscriber_charts[subscriber_id]:
                    self.subscriber_charts[subscriber_id].remove(chart_id)
                
                # 如果订阅者没有订阅任何图表，清理映射
                if not self.subscriber_charts[subscriber_id]:
                    del self.subscriber_charts[subscriber_id]
            
            logger.info(f"取消订阅图表成功: {subscriber_id} -> {chart_id}")
            
        except Exception as e:
            logger.error(f"取消订阅图表失败: {e}")
            raise
    
    async def update_chart_data(self, chart_id: str, bar_data: BarData) -> None:
        """更新图表数据"""
        try:
            if chart_id not in self.charts:
                return
            
            chart = self.charts[chart_id]
            
            # 更新数据
            await self.data_manager.add_bar_data(chart_id, bar_data)
            
            # 计算技术指标
            indicators = await self.calculator.calculate_indicators(
                chart_id, chart.config.indicators
            )
            
            # 准备更新事件
            update_event = ChartUpdateEvent(
                chart_id=chart_id,
                bar_data=bar_data,
                indicators=indicators,
                timestamp=datetime.now()
            )
            
            # 更新图表状态
            chart.last_update = datetime.now()
            chart.bar_count += 1
            
            # 触发事件
            await self._trigger_event('chart_updated', update_event)
            
        except Exception as e:
            logger.error(f"更新图表数据失败: {e}")
            await self._trigger_event('error_occurred', e)
    
    async def get_chart_render_data(self, chart_id: str) -> Dict[str, Any]:
        """获取图表渲染数据"""
        try:
            if chart_id not in self.charts:
                raise ValueError(f"图表 {chart_id} 不存在")
            
            chart = self.charts[chart_id]
            
            # 获取数据
            bars = await self.data_manager.get_chart_data(chart_id)
            indicators = await self.calculator.get_indicators(chart_id)
            
            # 渲染数据
            render_data = await self.renderer.prepare_render_data(
                chart_id, bars, indicators, chart.config
            )
            
            return render_data
            
        except Exception as e:
            logger.error(f"获取图表渲染数据失败: {e}")
            raise
    
    def register_event_callback(self, event_type: str, callback: Callable) -> None:
        """注册事件回调"""
        if event_type in self.event_callbacks:
            self.event_callbacks[event_type].append(callback)
        else:
            logger.warning(f"不支持的事件类型: {event_type}")
    
    async def _trigger_event(self, event_type: str, data: Any) -> None:
        """触发事件"""
        if event_type in self.event_callbacks:
            for callback in self.event_callbacks[event_type]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(data)
                    else:
                        callback(data)
                except Exception as e:
                    logger.error(f"事件回调执行失败: {e}")
    
    async def _run_update_loop(self) -> None:
        """运行更新循环"""
        while self.status == ChartEngineStatus.RUNNING:
            try:
                # 性能监控
                self.performance_monitor.record_metric('active_charts', len(self.charts))
                self.performance_monitor.record_metric('total_subscribers', len(self.subscriber_charts))
                
                # 清理过期缓存
                await self.data_manager.cleanup_cache()
                
                # 等待下一次循环
                await asyncio.sleep(1.0 / self.render_fps)
                
            except Exception as e:
                logger.error(f"更新循环错误: {e}")
                await asyncio.sleep(1.0)
    
    def get_engine_status(self) -> Dict[str, Any]:
        """获取引擎状态"""
        return {
            "status": self.status.value,
            "charts_count": len(self.charts),
            "subscribers_count": len(self.subscriber_charts),
            "performance": self.performance_monitor.get_metrics(),
            "config": self.config
        }
    
    def get_chart_info(self, chart_id: str) -> Optional[Dict[str, Any]]:
        """获取图表信息"""
        if chart_id not in self.charts:
            return None
        
        chart = self.charts[chart_id]
        return {
            "chart_id": chart.chart_id,
            "symbol": chart.symbol,
            "chart_type": chart.chart_type.value,
            "interval": chart.interval.value,
            "created_at": chart.created_at.isoformat(),
            "last_update": chart.last_update.isoformat() if chart.last_update else None,
            "subscribers_count": len(chart.subscribers),
            "is_active": chart.is_active,
            "bar_count": chart.bar_count
        }
