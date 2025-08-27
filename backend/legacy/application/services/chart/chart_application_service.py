"""
图表应用服务
"""

import asyncio
import logging
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import asdict

from src.application.services.base_application_service import BaseApplicationService
from src.domain.chart.entities.chart_entity import Chart
from src.domain.chart.entities.bar_data_entity import BarData
from src.domain.chart.entities.tick_data_entity import TickData
from src.domain.chart.entities.indicator_entity import Indicator, IndicatorStatus
from src.domain.chart.value_objects.chart_config import ChartConfig
from src.domain.chart.value_objects.chart_type import ChartType
from src.domain.chart.value_objects.interval import Interval
from src.domain.chart.value_objects.indicator_type import IndicatorType
from src.domain.chart.services.chart_domain_service import ChartDomainService
from src.domain.chart.services.indicator_calculation_service import IndicatorCalculationService
from src.domain.chart.services.indicator_manager_service import IndicatorManagerService
from src.domain.chart.services.chart_type_manager_service import ChartTypeManagerService
from src.domain.chart.repositories.chart_repository import ChartRepository
from src.domain.chart.repositories.bar_data_repository import BarDataRepository
from src.domain.chart.repositories.indicator_repository import IndicatorRepository

logger = logging.getLogger(__name__)


class ChartApplicationService(BaseApplicationService):
    """
    图表应用服务
    
    提供完整的图表功能，包括：
    1. 实时K线图表显示
    2. 技术指标计算和显示
    3. 多时间周期支持
    4. WebSocket实时数据推送
    5. 自定义图表配置
    
    对标vnpy-core的ChartWidget功能
    """
    
    def __init__(
        self,
        chart_repository: ChartRepository,
        bar_data_repository: BarDataRepository,
        indicator_repository: IndicatorRepository,
        chart_domain_service: ChartDomainService,
        indicator_calculation_service: IndicatorCalculationService
    ):
        # 创建模拟的command_bus和query_bus以避免循环依赖
        from unittest.mock import Mock
        mock_command_bus = Mock()
        mock_query_bus = Mock()
        super().__init__(mock_command_bus, mock_query_bus)
        
        self.chart_repository = chart_repository
        self.bar_data_repository = bar_data_repository
        self.indicator_repository = indicator_repository
        self.chart_domain_service = chart_domain_service
        self.indicator_calculation_service = indicator_calculation_service
        
        # 集成After服务的管理器
        self.indicator_manager = IndicatorManagerService()
        self.chart_type_manager = ChartTypeManagerService()
        
        # WebSocket连接管理
        self.websocket_connections: Dict[str, List[Any]] = {}
        
        # 数据缓存 - 扩展支持更多数据类型
        self.chart_data_cache: Dict[str, List[BarData]] = {}
        self.tick_data_cache: Dict[str, List[TickData]] = {}
        self.indicator_cache: Dict[str, Dict[str, Any]] = {}
        
        # 配置 - 与After服务兼容
        self.max_bars_per_chart = 1000
        self.cache_expiry_minutes = 5
        self.supported_intervals = ["1s", "5s", "15s", "30s", "1m", "5m", "15m", "30m", "1h", "4h", "1d", "1w"]
        
        # 实时数据推送配置
        self.realtime_push_enabled = True
        self.push_batch_size = 10
        
        logger.info("图表应用服务初始化完成")
    
    def get_service_info(self) -> Dict[str, Any]:
        """获取服务信息"""
        return {
            "service_name": "ChartApplicationService",
            "version": "1.0.0",
            "description": "图表应用服务 - 提供完整的图表功能",
            "supported_features": [
                "实时K线图表显示",
                "技术指标计算和显示",
                "多时间周期支持",
                "WebSocket实时数据推送",
                "自定义图表配置"
            ],
            "max_bars_per_chart": self.max_bars_per_chart,
            "cache_expiry_minutes": self.cache_expiry_minutes,
            "supported_intervals": self.supported_intervals
        }
    
    async def create_chart(
        self,
        symbol: str,
        chart_type: ChartType = ChartType.CANDLESTICK,
        interval: Interval = Interval.MINUTE_1,
        config: Optional[ChartConfig] = None
    ) -> Dict[str, Any]:
        """创建新图表"""
        try:
            # 验证输入
            if not self.chart_domain_service.validate_chart_creation(symbol, chart_type, interval):
                return {"success": False, "error": "图表创建参数无效"}
            
            # 检查是否已存在相同配置的图表
            existing_chart = await self.chart_repository.find_by_symbol_and_interval(symbol, interval)
            if existing_chart and existing_chart.is_active:
                return {
                    "success": True,
                    "chart_id": existing_chart.chart_id,
                    "message": "图表已存在",
                    "chart": existing_chart.__dict__
                }
            
            # 创建新图表
            chart = Chart(
                symbol=symbol,
                chart_type=chart_type,
                interval=interval,
                config=config or ChartConfig()
            )
            
            saved_chart = await self.chart_repository.save(chart)
            
            # 加载初始数据
            await self._load_initial_chart_data(saved_chart)
            
            logger.info(f"创建图表成功: {symbol}-{interval}")
            
            return {
                "success": True,
                "chart_id": saved_chart.chart_id,
                "chart": saved_chart.__dict__
            }
            
        except Exception as e:
            logger.error(f"创建图表失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_chart_data(
        self,
        chart_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """获取图表数据"""
        try:
            chart = await self.chart_repository.find_by_id(chart_id)
            if not chart:
                return {"success": False, "error": "图表不存在"}
            
            # 从缓存或数据库获取K线数据
            bars = await self._get_chart_bars(chart, start_time, end_time, limit)
            
            # 获取指标数据
            indicators_data = await self._get_chart_indicators(chart_id)
            
            # 计算统计信息
            stats = self.chart_domain_service.calculate_chart_statistics(bars)
            
            return {
                "success": True,
                "chart": asdict(chart),
                "bars": [asdict(bar) for bar in bars],
                "indicators": indicators_data,
                "statistics": stats
            }
            
        except Exception as e:
            logger.error(f"获取图表数据失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def update_chart_config(self, chart_id: str, config: ChartConfig) -> Dict[str, Any]:
        """更新图表配置"""
        try:
            chart = await self.chart_repository.find_by_id(chart_id)
            if not chart:
                return {"success": False, "error": "图表不存在"}
            
            chart.update_config(config)
            updated_chart = await self.chart_repository.update(chart)
            
            # 通知WebSocket订阅者
            await self._notify_chart_update(chart_id, {"type": "config_update", "config": asdict(config)})
            
            return {
                "success": True,
                "chart": asdict(updated_chart)
            }
            
        except Exception as e:
            logger.error(f"更新图表配置失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def add_indicator(
        self,
        chart_id: str,
        indicator_type: IndicatorType,
        parameters: Optional[Dict[str, Any]] = None,
        name: Optional[str] = None
    ) -> Dict[str, Any]:
        """添加技术指标"""
        try:
            chart = await self.chart_repository.find_by_id(chart_id)
            if not chart:
                return {"success": False, "error": "图表不存在"}
            
            # 创建指标
            indicator = Indicator(
                name=name or f"{indicator_type.value}_{chart_id[:8]}",
                indicator_type=indicator_type,
                parameters=parameters or indicator_type.get_default_parameters()
            )
            
            saved_indicator = await self.indicator_repository.save(indicator)
            
            # 激活指标并开始计算
            saved_indicator.activate()
            await self._calculate_indicator_values(saved_indicator, chart)
            
            return {
                "success": True,
                "indicator": asdict(saved_indicator)
            }
            
        except Exception as e:
            logger.error(f"添加技术指标失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def subscribe_chart(self, chart_id: str, websocket) -> Dict[str, Any]:
        """订阅图表WebSocket更新"""
        try:
            chart = await self.chart_repository.find_by_id(chart_id)
            if not chart:
                return {"success": False, "error": "图表不存在"}
            
            # 添加WebSocket连接
            if chart_id not in self.websocket_connections:
                self.websocket_connections[chart_id] = []
            
            self.websocket_connections[chart_id].append(websocket)
            
            # 更新图表订阅者
            chart.add_subscriber(str(id(websocket)))
            await self.chart_repository.update(chart)
            
            logger.info(f"WebSocket订阅图表: {chart_id}")
            
            return {"success": True, "message": "订阅成功"}
            
        except Exception as e:
            logger.error(f"订阅图表失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def unsubscribe_chart(self, chart_id: str, websocket) -> Dict[str, Any]:
        """取消订阅图表"""
        try:
            if chart_id in self.websocket_connections:
                connections = self.websocket_connections[chart_id]
                if websocket in connections:
                    connections.remove(websocket)
                    
                    # 更新图表订阅者
                    chart = await self.chart_repository.find_by_id(chart_id)
                    if chart:
                        chart.remove_subscriber(str(id(websocket)))
                        await self.chart_repository.update(chart)
                    
                    logger.info(f"WebSocket取消订阅图表: {chart_id}")
            
            return {"success": True, "message": "取消订阅成功"}
            
        except Exception as e:
            logger.error(f"取消订阅图表失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def push_real_time_data(self, symbol: str, bar_data: BarData) -> None:
        """推送实时数据"""
        try:
            # 找到相关图表
            charts = await self.chart_repository.find_by_symbol(symbol)
            
            for chart in charts:
                if not chart.is_active:
                    continue
                
                # 更新缓存
                await self._update_chart_cache(chart.chart_id, bar_data)
                
                # 通知WebSocket订阅者
                await self._notify_chart_update(
                    chart.chart_id,
                    {
                        "type": "new_bar",
                        "bar": asdict(bar_data)
                    }
                )
                
                # 重新计算指标
                await self._recalculate_chart_indicators(chart)
            
        except Exception as e:
            logger.error(f"推送实时数据失败: {e}")
    
    async def _load_initial_chart_data(self, chart: Chart) -> None:
        """加载图表初始数据"""
        try:
            # 计算需要的K线数量
            required_bars = self.chart_domain_service.calculate_required_bars(chart.interval)
            
            # 从数据库加载数据
            bars = await self.bar_data_repository.find_bars_count(
                chart.symbol,
                chart.interval,
                min(required_bars, self.max_bars_per_chart)
            )
            
            # 更新缓存
            self.chart_data_cache[chart.chart_id] = bars
            
            # 更新图表统计
            chart.update_bar_count(len(bars))
            await self.chart_repository.update(chart)
            
        except Exception as e:
            logger.error(f"加载图表初始数据失败: {e}")
    
    async def _get_chart_bars(
        self,
        chart: Chart,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> List[BarData]:
        """获取图表K线数据"""
        # 首先尝试从缓存获取
        cached_bars = self.chart_data_cache.get(chart.chart_id, [])
        
        if cached_bars and not start_time and not end_time:
            # 返回缓存数据
            if limit:
                return cached_bars[-limit:]
            return cached_bars
        
        # 从数据库查询
        bars = await self.bar_data_repository.find_bars(
            chart.symbol,
            chart.interval,
            start_time,
            end_time,
            limit
        )
        
        return bars
    
    async def _get_chart_indicators(self, chart_id: str) -> Dict[str, Any]:
        """获取图表指标数据"""
        indicators = await self.indicator_repository.find_by_chart_id(chart_id)
        
        result = {}
        for indicator in indicators:
            if indicator.indicator_id in self.indicator_cache:
                result[indicator.indicator_id] = {
                    "indicator": asdict(indicator),
                    "data": self.indicator_cache[indicator.indicator_id]
                }
        
        return result
    
    async def _calculate_indicator_values(self, indicator: Indicator, chart: Chart) -> None:
        """计算指标值"""
        try:
            indicator.start_calculation()
            await self.indicator_repository.update(indicator)
            
            # 获取K线数据
            bars = self.chart_data_cache.get(chart.chart_id, [])
            if not bars:
                bars = await self.bar_data_repository.find_bars_count(
                    chart.symbol,
                    chart.interval,
                    self.max_bars_per_chart
                )
            
            # 计算指标
            calculation_result = self.indicator_calculation_service.calculate_indicator(indicator, bars)
            
            if calculation_result.get("error"):
                indicator.error_occurred(calculation_result["error"])
            else:
                indicator.complete_calculation()
                # 缓存结果
                self.indicator_cache[indicator.indicator_id] = calculation_result["values"]
            
            await self.indicator_repository.update(indicator)
            
        except Exception as e:
            logger.error(f"计算指标失败: {e}")
            indicator.error_occurred(str(e))
            await self.indicator_repository.update(indicator)
    
    async def _recalculate_chart_indicators(self, chart: Chart) -> None:
        """重新计算图表所有指标"""
        indicators = await self.indicator_repository.find_by_chart_id(chart.chart_id)
        
        for indicator in indicators:
            if indicator.status == IndicatorStatus.ACTIVE:
                await self._calculate_indicator_values(indicator, chart)
    
    async def _update_chart_cache(self, chart_id: str, new_bar: BarData) -> None:
        """更新图表缓存 - 增强版本"""
        if chart_id not in self.chart_data_cache:
            self.chart_data_cache[chart_id] = []
        
        bars = self.chart_data_cache[chart_id]
        
        # 检查是否为更新最后一根K线还是新增K线
        if bars and bars[-1].datetime == new_bar.datetime:
            # 更新最后一根K线
            bars[-1] = new_bar
        else:
            # 新增K线
            bars.append(new_bar)
            
            # 限制缓存大小
            if len(bars) > self.max_bars_per_chart:
                bars.pop(0)
        
        # 记录缓存更新时间
        cache_update_time = datetime.now()
        if not hasattr(self, 'cache_update_times'):
            self.cache_update_times = {}
        self.cache_update_times[chart_id] = cache_update_time
    
    async def _notify_chart_update(self, chart_id: str, data: Dict[str, Any]) -> None:
        """通知WebSocket订阅者图表更新"""
        if chart_id not in self.websocket_connections:
            return
        
        connections = self.websocket_connections[chart_id].copy()
        
        for websocket in connections:
            try:
                await websocket.send_json(data)
            except Exception as e:
                # 连接断开，移除
                self.websocket_connections[chart_id].remove(websocket)
                logger.warning(f"WebSocket连接断开，移除订阅: {e}")
    
    async def get_websocket_stats(self) -> Dict[str, Any]:
        """
        获取WebSocket连接统计 - 来自After服务的功能
        
        Returns:
            Dict[str, Any]: WebSocket统计信息
        """
        total_connections = sum(len(connections) for connections in self.websocket_connections.values())
        
        return {
            "total_connections": total_connections,
            "charts_with_connections": len(self.websocket_connections),
            "connections_by_chart": {
                chart_id: len(connections) 
                for chart_id, connections in self.websocket_connections.items()
            },
            "cache_stats": {
                "chart_data_cache_size": len(self.chart_data_cache),
                "tick_data_cache_size": len(self.tick_data_cache),
                "indicator_cache_size": len(self.indicator_cache)
            }
        }
    
    async def cleanup_inactive_charts(self) -> int:
        """清理非活跃图表"""
        try:
            # 清理没有订阅者且长时间未更新的图表
            cutoff_time = datetime.now() - timedelta(hours=24)
            old_charts = await self.chart_repository.find_charts_created_after(cutoff_time)
            
            cleanup_count = 0
            for chart in old_charts:
                if chart.subscriber_count == 0 and not chart.is_active:
                    await self.chart_repository.delete(chart.chart_id)
                    
                    # 清理缓存
                    if chart.chart_id in self.chart_data_cache:
                        del self.chart_data_cache[chart.chart_id]
                    
                    cleanup_count += 1
            
            logger.info(f"清理非活跃图表: {cleanup_count} 个")
            return cleanup_count
            
        except Exception as e:
            logger.error(f"清理非活跃图表失败: {e}")
            return 0
    
    # =============================================================================
    # After服务集成的新功能
    # =============================================================================
    
    async def update_tick_data(self, tick: TickData) -> None:
        """
        更新Tick数据 - 来自After服务的功能
        
        Args:
            tick: Tick数据
        """
        try:
            symbol = tick.symbol
            
            # 存储Tick数据到缓存
            if symbol not in self.tick_data_cache:
                self.tick_data_cache[symbol] = []
            
            self.tick_data_cache[symbol].append(tick)
            
            # 保持缓存大小限制
            if len(self.tick_data_cache[symbol]) > self.max_bars_per_chart:
                self.tick_data_cache[symbol].pop(0)
            
            # 推送实时Tick数据到WebSocket客户端
            await self._broadcast_tick_update(symbol, tick)
            
            logger.debug(f"更新Tick数据: {symbol} - {tick.last_price}")
            
        except Exception as e:
            logger.error(f"更新Tick数据失败: {e}")
    
    async def get_enhanced_chart_data(
        self,
        chart_id: str,
        include_indicators: bool = True,
        include_statistics: bool = True,
        data_format: str = "standard"
    ) -> Dict[str, Any]:
        """
        获取增强的图表数据 - 集成After服务功能
        
        Args:
            chart_id: 图表ID
            include_indicators: 是否包含指标数据
            include_statistics: 是否包含统计信息
            data_format: 数据格式 (standard/charting_library)
            
        Returns:
            Dict[str, Any]: 增强的图表数据
        """
        try:
            chart = await self.chart_repository.find_by_id(chart_id)
            if not chart:
                return {"success": False, "error": "图表不存在"}
            
            # 获取K线数据
            bars = await self._get_chart_bars(chart)
            
            # 根据图表类型转换数据格式
            chart_data = self.chart_type_manager.convert_chart_data(bars, chart.chart_type)
            
            result = {
                "success": True,
                "chart": asdict(chart),
                "data": chart_data,
                "data_format": data_format,
                "timestamp": datetime.now().isoformat()
            }
            
            # 包含指标数据
            if include_indicators:
                indicators_data = await self._get_enhanced_indicators_data(chart_id)
                result["indicators"] = indicators_data
            
            # 包含统计信息
            if include_statistics:
                stats = self._calculate_enhanced_statistics(bars)
                result["statistics"] = stats
            
            # 获取图表配置建议
            recommended_config = self.chart_type_manager.get_recommended_config(
                chart.chart_type, chart.symbol, chart.interval
            )
            result["recommended_config"] = asdict(recommended_config)
            
            return result
            
        except Exception as e:
            logger.error(f"获取增强图表数据失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def add_enhanced_indicator(
        self,
        chart_id: str,
        indicator_type: IndicatorType,
        parameters: Optional[Dict[str, Any]] = None,
        name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        添加增强技术指标 - 使用After服务的指标管理器
        
        Args:
            chart_id: 图表ID
            indicator_type: 指标类型
            parameters: 指标参数
            name: 指标名称
            
        Returns:
            Dict[str, Any]: 添加结果
        """
        try:
            chart = await self.chart_repository.find_by_id(chart_id)
            if not chart:
                return {"success": False, "error": "图表不存在"}
            
            # 创建指标实例
            indicator = Indicator(
                name=name or f"{indicator_type.value}_{chart_id[:8]}",
                indicator_type=indicator_type,
                parameters=parameters or indicator_type.get_default_parameters()
            )
            
            # 使用After服务的指标管理器
            success = self.indicator_manager.add_indicator(chart.symbol, indicator)
            
            if success:
                # 保存到仓储
                saved_indicator = await self.indicator_repository.save(indicator)
                saved_indicator.activate()
                
                # 计算指标值
                bars = self.chart_data_cache.get(chart_id, [])
                if bars:
                    calculation_result = self.indicator_manager.calculate_single(
                        chart.symbol, indicator.name, bars
                    )
                    
                    if calculation_result.success:
                        self.indicator_cache[indicator.indicator_id] = calculation_result.values
                
                # 通知WebSocket订阅者
                await self._notify_chart_update(
                    chart_id, 
                    {
                        "type": "indicator_added",
                        "indicator": asdict(saved_indicator)
                    }
                )
                
                return {
                    "success": True,
                    "indicator": asdict(saved_indicator)
                }
            else:
                return {"success": False, "error": "指标添加失败"}
                
        except Exception as e:
            logger.error(f"添加增强技术指标失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def remove_enhanced_indicator(
        self, 
        chart_id: str, 
        indicator_name: str
    ) -> Dict[str, Any]:
        """
        移除增强技术指标
        
        Args:
            chart_id: 图表ID
            indicator_name: 指标名称
            
        Returns:
            Dict[str, Any]: 移除结果
        """
        try:
            chart = await self.chart_repository.find_by_id(chart_id)
            if not chart:
                return {"success": False, "error": "图表不存在"}
            
            # 从指标管理器移除
            success = self.indicator_manager.remove_indicator(chart.symbol, indicator_name)
            
            if success:
                # 从仓储删除
                indicators = await self.indicator_repository.find_by_chart_id(chart_id)
                for indicator in indicators:
                    if indicator.name == indicator_name:
                        await self.indicator_repository.delete(indicator.indicator_id)
                        break
                
                # 清理缓存
                cache_keys_to_remove = [
                    key for key in self.indicator_cache.keys() 
                    if indicator_name in key
                ]
                for key in cache_keys_to_remove:
                    del self.indicator_cache[key]
                
                # 通知WebSocket订阅者
                await self._notify_chart_update(
                    chart_id,
                    {
                        "type": "indicator_removed",
                        "indicator_name": indicator_name
                    }
                )
                
                return {"success": True, "message": f"指标 {indicator_name} 移除成功"}
            else:
                return {"success": False, "error": "指标移除失败"}
                
        except Exception as e:
            logger.error(f"移除增强技术指标失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def refresh_enhanced_chart_data(self, chart_id: str) -> Dict[str, Any]:
        """
        刷新增强图表数据 - 重新计算所有指标
        
        Args:
            chart_id: 图表ID
            
        Returns:
            Dict[str, Any]: 刷新结果
        """
        try:
            chart = await self.chart_repository.find_by_id(chart_id)
            if not chart:
                return {"success": False, "error": "图表不存在"}
            
            # 获取最新数据
            bars = await self._get_chart_bars(chart)
            
            # 重新计算所有指标
            indicators_data = self.indicator_manager.calculate_all(chart.symbol, bars)
            
            # 更新缓存
            for indicator_name, values in indicators_data.items():
                if "error" not in values:
                    cache_key = f"{chart.symbol}_{indicator_name}"
                    self.indicator_cache[cache_key] = values
            
            # 推送更新的数据
            await self._notify_chart_update(
                chart_id,
                {
                    "type": "chart_refreshed",
                    "indicators": indicators_data,
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            return {
                "success": True,
                "message": "图表数据刷新成功",
                "indicators_count": len(indicators_data)
            }
            
        except Exception as e:
            logger.error(f"刷新增强图表数据失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def _broadcast_tick_update(self, symbol: str, tick: TickData) -> None:
        """
        广播Tick更新 - 来自After服务的功能
        
        Args:
            symbol: 交易品种
            tick: Tick数据
        """
        # 找到相关图表的WebSocket连接
        charts = await self.chart_repository.find_by_symbol(symbol)
        
        for chart in charts:
            if chart.chart_id in self.websocket_connections:
                message = {
                    "type": "tick_update",
                    "symbol": symbol,
                    "tick": tick.dict(),
                    "timestamp": datetime.now().isoformat()
                }
                
                await self._notify_chart_update(chart.chart_id, message)
    
    async def _get_enhanced_indicators_data(self, chart_id: str) -> Dict[str, Any]:
        """
        获取增强的指标数据
        
        Args:
            chart_id: 图表ID
            
        Returns:
            Dict[str, Any]: 增强的指标数据
        """
        chart = await self.chart_repository.find_by_id(chart_id)
        if not chart:
            return {}
        
        # 从指标管理器获取数据
        indicators = self.indicator_manager.get_indicators(chart.symbol)
        
        result = {}
        for indicator in indicators:
            cache_key = f"{chart.symbol}_{indicator.name}"
            if cache_key in self.indicator_cache:
                result[indicator.name] = {
                    "indicator": asdict(indicator),
                    "data": self.indicator_cache[cache_key],
                    "last_updated": datetime.now().isoformat()
                }
        
        return result
    
    def _calculate_enhanced_statistics(self, bars: List[BarData]) -> Dict[str, Any]:
        """
        计算增强的统计信息
        
        Args:
            bars: K线数据
            
        Returns:
            Dict[str, Any]: 统计信息
        """
        if not bars:
            return {}
        
        # 基本统计
        prices = [float(bar.close_price) for bar in bars]
        volumes = [float(bar.volume) for bar in bars]
        
        return {
            "total_bars": len(bars),
            "price_stats": {
                "min": min(prices),
                "max": max(prices),
                "avg": sum(prices) / len(prices),
                "first": prices[0],
                "last": prices[-1],
                "change": prices[-1] - prices[0],
                "change_pct": ((prices[-1] - prices[0]) / prices[0] * 100) if prices[0] != 0 else 0
            },
            "volume_stats": {
                "total": sum(volumes),
                "avg": sum(volumes) / len(volumes),
                "max": max(volumes),
                "min": min(volumes)
            },
            "time_range": {
                "start": bars[0].datetime.isoformat(),
                "end": bars[-1].datetime.isoformat(),
                "duration_hours": (bars[-1].datetime - bars[0].datetime).total_seconds() / 3600
            }
        }
    
    # =============================================================================
    # 测试支持方法 - 添加缺失的方法以支持测试
    # =============================================================================
    
    async def get_chart(self, chart_id: str) -> Chart:
        """获取图表"""
        chart = await self.chart_repository.find_by_id(chart_id)
        if not chart:
            raise ValueError("Chart not found")
        return chart
    
    async def update_chart(self, chart_id: str, title: Optional[str] = None, description: Optional[str] = None) -> Chart:
        """更新图表"""
        chart = await self.chart_repository.find_by_id(chart_id)
        if not chart:
            raise ValueError("Chart not found")
        
        if title:
            chart.update_info(title=title, description=description)
        
        return await self.chart_repository.update(chart)
    
    async def delete_chart(self, chart_id: str) -> bool:
        """删除图表"""
        return await self.chart_repository.delete(chart_id)
    
    async def get_charts_by_symbol(self, symbol: str) -> List[Chart]:
        """根据交易品种获取图表"""
        return await self.chart_repository.find_by_symbol(symbol)
    
    async def get_chart_bars(self, chart_id: str, limit: Optional[int] = None) -> List[BarData]:
        """获取图表K线数据"""
        chart = await self.chart_repository.find_by_id(chart_id)
        if not chart:
            raise ValueError("Chart not found")
        
        return await self._get_chart_bars(chart, limit=limit)
    
    async def get_chart_indicators(self, chart_id: str) -> List[Indicator]:
        """获取图表指标"""
        return await self.indicator_repository.find_by_chart_id(chart_id)
    
    async def remove_indicator(self, indicator_id: str) -> bool:
        """删除指标"""
        return await self.indicator_repository.delete(indicator_id)
    
    async def update_indicator(self, indicator_id: str, name: Optional[str] = None, parameters: Optional[Dict[str, Any]] = None) -> Indicator:
        """更新指标"""
        indicator = await self.indicator_repository.find_by_id(indicator_id)
        if not indicator:
            raise ValueError("Indicator not found")
        
        if name:
            indicator.name = name
        if parameters:
            indicator.update_parameters(parameters)
        
        return await self.indicator_repository.update(indicator)
