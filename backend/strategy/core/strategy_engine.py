"""
量化策略执行引擎

提供高性能的策略执行环境，支持多策略并发运行、
实时数据处理、订单管理和风险控制。
"""

import logging
import asyncio
import uuid
from typing import Dict, List, Optional, Any, Callable, Set, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import pandas as pd
import threading
from concurrent.futures import ThreadPoolExecutor

from .strategy_base import (
    BaseStrategy, StrategyConfig, StrategyState, StrategyType,
    MarketData, OrderInfo, TradeInfo, PositionInfo, OrderSide, OrderType
)


class EngineState(Enum):
    """引擎状态"""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"


class DataSource(Enum):
    """数据源类型"""
    LIVE = "live"           # 实时数据
    BACKTEST = "backtest"   # 回测数据
    PAPER = "paper"         # 模拟数据


@dataclass
class EngineConfig:
    """引擎配置"""
    engine_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    # 数据配置
    data_source: DataSource = DataSource.PAPER
    data_feed_interval: float = 1.0  # 数据推送间隔(秒)
    
    # 性能配置
    max_strategies: int = 100
    max_workers: int = 10
    order_queue_size: int = 1000
    data_queue_size: int = 10000
    
    # 风险配置
    enable_risk_control: bool = True
    max_daily_loss: float = 0.05
    max_position_per_strategy: float = 0.1
    
    # 监控配置
    performance_update_interval: int = 60
    health_check_interval: int = 30
    enable_logging: bool = True
    log_level: str = "INFO"


@dataclass 
class EngineStats:
    """引擎统计信息"""
    start_time: Optional[datetime] = None
    uptime: timedelta = field(default_factory=timedelta)
    
    # 策略统计
    total_strategies: int = 0
    running_strategies: int = 0
    stopped_strategies: int = 0
    error_strategies: int = 0
    
    # 交易统计
    total_orders: int = 0
    filled_orders: int = 0
    cancelled_orders: int = 0
    total_trades: int = 0
    
    # 数据统计
    data_packets_processed: int = 0
    data_processing_latency: float = 0.0  # 毫秒
    
    # 系统统计
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    error_count: int = 0


class StrategyEngine:
    """
    策略执行引擎
    
    负责管理策略生命周期、数据分发、订单执行等核心功能。
    """
    
    def __init__(self, config: Optional[EngineConfig] = None):
        """
        初始化策略引擎
        
        Args:
            config: 引擎配置
        """
        self.config = config or EngineConfig()
        self.engine_id = self.config.engine_id
        
        # 状态管理
        self._state = EngineState.STOPPED
        self._stats = EngineStats()
        
        # 日志记录
        self.logger = logging.getLogger(f"strategy_engine.{self.engine_id}")
        self.logger.setLevel(getattr(logging, self.config.log_level.upper()))
        
        # 策略管理
        self._strategies: Dict[str, BaseStrategy] = {}
        self._strategy_tasks: Dict[str, asyncio.Task] = {}
        self._strategy_locks: Dict[str, asyncio.Lock] = {}
        
        # 数据管理
        self._data_queue: asyncio.Queue = asyncio.Queue(maxsize=self.config.data_queue_size)
        self._data_subscribers: Dict[str, Set[str]] = {}  # symbol -> strategy_ids
        self._data_cache: Dict[str, MarketData] = {}
        
        # 订单管理
        self._order_queue: asyncio.Queue = asyncio.Queue(maxsize=self.config.order_queue_size)
        self._pending_orders: Dict[str, OrderInfo] = {}
        self._order_callbacks: Dict[str, Callable] = {}
        
        # 线程池
        self._thread_pool = ThreadPoolExecutor(max_workers=self.config.max_workers)
        
        # 事件循环
        self._main_loop: Optional[asyncio.Task] = None
        self._data_processor: Optional[asyncio.Task] = None
        self._order_processor: Optional[asyncio.Task] = None
        self._monitor_task: Optional[asyncio.Task] = None
        
        # 回调函数
        self._event_callbacks: Dict[str, List[Callable]] = {
            "strategy_started": [],
            "strategy_stopped": [],
            "strategy_error": [],
            "order_filled": [],
            "data_received": []
        }
        
        self.logger.info(f"策略引擎初始化完成: {self.engine_id}")
    
    @property
    def state(self) -> EngineState:
        """获取引擎状态"""
        return self._state
    
    @property
    def stats(self) -> EngineStats:
        """获取引擎统计"""
        return self._stats
    
    @property
    def is_running(self) -> bool:
        """引擎是否运行中"""
        return self._state == EngineState.RUNNING
    
    # ==================== 引擎生命周期 ====================
    
    async def start(self) -> bool:
        """启动引擎"""
        try:
            if self._state == EngineState.RUNNING:
                self.logger.warning("引擎已经在运行")
                return True
            
            self._state = EngineState.STARTING
            self.logger.info("启动策略引擎...")
            
            # 重置统计
            self._stats = EngineStats(start_time=datetime.now())
            
            # 启动核心任务
            self._data_processor = asyncio.create_task(self._process_data())
            self._order_processor = asyncio.create_task(self._process_orders())
            self._monitor_task = asyncio.create_task(self._monitor_engine())
            
            self._state = EngineState.RUNNING
            self.logger.info("策略引擎启动成功")
            return True
            
        except Exception as e:
            self._state = EngineState.ERROR
            self.logger.error(f"引擎启动失败: {e}")
            return False
    
    async def stop(self) -> bool:
        """停止引擎"""
        try:
            if self._state == EngineState.STOPPED:
                self.logger.warning("引擎已经停止")
                return True
            
            self._state = EngineState.STOPPING
            self.logger.info("停止策略引擎...")
            
            # 停止所有策略
            await self.stop_all_strategies()
            
            # 停止核心任务
            if self._data_processor:
                self._data_processor.cancel()
            if self._order_processor:
                self._order_processor.cancel()
            if self._monitor_task:
                self._monitor_task.cancel()
            
            # 关闭线程池
            self._thread_pool.shutdown(wait=True)
            
            self._state = EngineState.STOPPED
            self.logger.info("策略引擎停止成功")
            return True
            
        except Exception as e:
            self._state = EngineState.ERROR
            self.logger.error(f"引擎停止失败: {e}")
            return False
    
    # ==================== 策略管理 ====================
    
    async def add_strategy(self, strategy: BaseStrategy) -> bool:
        """添加策略"""
        try:
            strategy_id = strategy.strategy_id
            
            if strategy_id in self._strategies:
                self.logger.error(f"策略已存在: {strategy_id}")
                return False
            
            if len(self._strategies) >= self.config.max_strategies:
                self.logger.error(f"策略数量超限: {len(self._strategies)}")
                return False
            
            # 添加策略
            self._strategies[strategy_id] = strategy
            self._strategy_locks[strategy_id] = asyncio.Lock()
            
            # 订阅数据
            for symbol in strategy.config.symbols:
                if symbol not in self._data_subscribers:
                    self._data_subscribers[symbol] = set()
                self._data_subscribers[symbol].add(strategy_id)
            
            self._stats.total_strategies += 1
            self.logger.info(f"策略添加成功: {strategy_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"添加策略失败: {e}")
            return False
    
    async def remove_strategy(self, strategy_id: str) -> bool:
        """移除策略"""
        try:
            if strategy_id not in self._strategies:
                self.logger.error(f"策略不存在: {strategy_id}")
                return False
            
            # 停止策略
            await self.stop_strategy(strategy_id)
            
            # 移除订阅
            strategy = self._strategies[strategy_id]
            for symbol in strategy.config.symbols:
                if symbol in self._data_subscribers:
                    self._data_subscribers[symbol].discard(strategy_id)
                    if not self._data_subscribers[symbol]:
                        del self._data_subscribers[symbol]
            
            # 移除策略
            del self._strategies[strategy_id]
            if strategy_id in self._strategy_locks:
                del self._strategy_locks[strategy_id]
            
            self._stats.total_strategies -= 1
            self.logger.info(f"策略移除成功: {strategy_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"移除策略失败: {e}")
            return False
    
    async def start_strategy(self, strategy_id: str) -> bool:
        """启动策略"""
        try:
            if strategy_id not in self._strategies:
                self.logger.error(f"策略不存在: {strategy_id}")
                return False
            
            strategy = self._strategies[strategy_id]
            
            if strategy.is_running:
                self.logger.warning(f"策略已在运行: {strategy_id}")
                return True
            
            # 启动策略
            success = await strategy.start()
            
            if success:
                # 创建策略任务
                self._strategy_tasks[strategy_id] = asyncio.create_task(
                    self._run_strategy(strategy_id)
                )
                
                self._stats.running_strategies += 1
                self._trigger_event("strategy_started", strategy)
                self.logger.info(f"策略启动成功: {strategy_id}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"启动策略失败: {e}")
            return False
    
    async def stop_strategy(self, strategy_id: str) -> bool:
        """停止策略"""
        try:
            if strategy_id not in self._strategies:
                self.logger.error(f"策略不存在: {strategy_id}")
                return False
            
            strategy = self._strategies[strategy_id]
            
            if not strategy.is_running:
                self.logger.warning(f"策略未运行: {strategy_id}")
                return True
            
            # 停止策略任务
            if strategy_id in self._strategy_tasks:
                self._strategy_tasks[strategy_id].cancel()
                del self._strategy_tasks[strategy_id]
            
            # 停止策略
            success = await strategy.stop()
            
            if success:
                self._stats.running_strategies -= 1
                self._stats.stopped_strategies += 1
                self._trigger_event("strategy_stopped", strategy)
                self.logger.info(f"策略停止成功: {strategy_id}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"停止策略失败: {e}")
            return False
    
    async def start_all_strategies(self) -> int:
        """启动所有策略"""
        started_count = 0
        for strategy_id in list(self._strategies.keys()):
            if await self.start_strategy(strategy_id):
                started_count += 1
        return started_count
    
    async def stop_all_strategies(self) -> int:
        """停止所有策略"""
        stopped_count = 0
        for strategy_id in list(self._strategies.keys()):
            if await self.stop_strategy(strategy_id):
                stopped_count += 1
        return stopped_count
    
    async def _run_strategy(self, strategy_id: str):
        """运行策略任务"""
        try:
            strategy = self._strategies.get(strategy_id)
            if not strategy:
                return
            
            while strategy.is_running and self.is_running:
                await asyncio.sleep(0.1)  # 策略主循环
                
        except asyncio.CancelledError:
            pass
        except Exception as e:
            self.logger.error(f"策略运行异常 {strategy_id}: {e}")
            self._stats.error_strategies += 1
            self._trigger_event("strategy_error", strategy, e)
    
    # ==================== 数据管理 ====================
    
    async def feed_data(self, data: MarketData):
        """推送市场数据"""
        try:
            if not self.is_running:
                return
            
            # 数据缓存
            self._data_cache[data.symbol] = data
            
            # 推送到队列
            if not self._data_queue.full():
                await self._data_queue.put(data)
                self._stats.data_packets_processed += 1
            else:
                self.logger.warning("数据队列已满，丢弃数据")
                
        except Exception as e:
            self.logger.error(f"推送数据失败: {e}")
    
    async def _process_data(self):
        """处理数据队列"""
        try:
            while self.is_running:
                try:
                    # 获取数据
                    data = await asyncio.wait_for(self._data_queue.get(), timeout=1.0)
                    
                    start_time = datetime.now()
                    
                    # 分发数据到订阅策略
                    if data.symbol in self._data_subscribers:
                        tasks = []
                        for strategy_id in self._data_subscribers[data.symbol]:
                            if strategy_id in self._strategies:
                                strategy = self._strategies[strategy_id]
                                if strategy.is_running:
                                    task = asyncio.create_task(
                                        self._send_data_to_strategy(strategy, data)
                                    )
                                    tasks.append(task)
                        
                        # 等待所有策略处理完成
                        if tasks:
                            await asyncio.gather(*tasks, return_exceptions=True)
                    
                    # 更新延迟统计
                    latency = (datetime.now() - start_time).total_seconds() * 1000
                    self._stats.data_processing_latency = latency
                    
                    self._trigger_event("data_received", data)
                    
                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    self.logger.error(f"处理数据异常: {e}")
                    
        except asyncio.CancelledError:
            pass
    
    async def _send_data_to_strategy(self, strategy: BaseStrategy, data: MarketData):
        """发送数据到策略"""
        try:
            # 使用锁防止并发问题
            async with self._strategy_locks[strategy.strategy_id]:
                await strategy._on_market_data(data)
                
        except Exception as e:
            self.logger.error(f"策略数据处理异常 {strategy.strategy_id}: {e}")
    
    # ==================== 订单管理 ====================
    
    async def place_order(self, order: OrderInfo, callback: Optional[Callable] = None) -> bool:
        """下单"""
        try:
            if not self.is_running:
                return False
            
            # 风险检查
            if self.config.enable_risk_control:
                if not await self._check_order_risk(order):
                    return False
            
            # 添加到队列
            if not self._order_queue.full():
                await self._order_queue.put(order)
                self._pending_orders[order.order_id] = order
                if callback:
                    self._order_callbacks[order.order_id] = callback
                
                self._stats.total_orders += 1
                return True
            else:
                self.logger.warning("订单队列已满")
                return False
                
        except Exception as e:
            self.logger.error(f"下单失败: {e}")
            return False
    
    async def _process_orders(self):
        """处理订单队列"""
        try:
            while self.is_running:
                try:
                    # 获取订单
                    order = await asyncio.wait_for(self._order_queue.get(), timeout=1.0)
                    
                    # 执行订单
                    success = await self._execute_order(order)
                    
                    if success:
                        self._stats.filled_orders += 1
                    else:
                        self._stats.cancelled_orders += 1
                    
                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    self.logger.error(f"处理订单异常: {e}")
                    
        except asyncio.CancelledError:
            pass
    
    async def _execute_order(self, order: OrderInfo) -> bool:
        """执行订单"""
        try:
            # 这里应该连接真实的交易接口
            # 现在模拟执行
            await asyncio.sleep(0.1)  # 模拟网络延迟
            
            # 模拟成交
            order.status = "filled"
            order.filled_quantity = order.quantity
            
            # 获取成交价格
            if order.order_type == OrderType.MARKET:
                # 市价单使用当前价格
                if order.symbol in self._data_cache:
                    order.average_price = self._data_cache[order.symbol].close
                else:
                    order.average_price = order.price or 0
            else:
                # 限价单使用限价
                order.average_price = order.price
            
            # 创建成交记录
            trade = TradeInfo(
                trade_id=str(uuid.uuid4()),
                order_id=order.order_id,
                symbol=order.symbol,
                side=order.side,
                quantity=order.quantity,
                price=order.average_price,
                strategy_id=order.strategy_id
            )
            
            # 通知策略
            if order.strategy_id in self._strategies:
                strategy = self._strategies[order.strategy_id]
                await strategy._on_trade_filled(trade)
            
            # 回调通知
            if order.order_id in self._order_callbacks:
                callback = self._order_callbacks[order.order_id]
                await callback(order, trade)
                del self._order_callbacks[order.order_id]
            
            # 清理
            if order.order_id in self._pending_orders:
                del self._pending_orders[order.order_id]
            
            self._stats.total_trades += 1
            self._trigger_event("order_filled", order, trade)
            
            return True
            
        except Exception as e:
            self.logger.error(f"执行订单失败: {e}")
            return False
    
    async def _check_order_risk(self, order: OrderInfo) -> bool:
        """订单风险检查"""
        try:
            # 检查策略持仓限制
            if order.strategy_id in self._strategies:
                strategy = self._strategies[order.strategy_id]
                
                # 检查最大持仓
                current_position = strategy.get_position(order.symbol)
                if current_position:
                    position_value = abs(float(current_position.quantity * current_position.average_price))
                    max_position = float(strategy.config.initial_capital * strategy.config.max_position_size)
                    
                    if position_value > max_position:
                        self.logger.warning(f"策略持仓超限: {order.strategy_id}")
                        return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"风险检查失败: {e}")
            return False
    
    # ==================== 监控 ====================
    
    async def _monitor_engine(self):
        """引擎监控"""
        try:
            while self.is_running:
                await self._update_stats()
                await self._health_check()
                await asyncio.sleep(self.config.health_check_interval)
                
        except asyncio.CancelledError:
            pass
        except Exception as e:
            self.logger.error(f"监控异常: {e}")
    
    async def _update_stats(self):
        """更新统计信息"""
        try:
            if self._stats.start_time:
                self._stats.uptime = datetime.now() - self._stats.start_time
            
            # 统计策略状态
            running_count = sum(1 for s in self._strategies.values() if s.is_running)
            self._stats.running_strategies = running_count
            self._stats.stopped_strategies = self._stats.total_strategies - running_count
            
        except Exception as e:
            self.logger.error(f"更新统计失败: {e}")
    
    async def _health_check(self):
        """健康检查"""
        try:
            # 检查队列大小
            data_queue_size = self._data_queue.qsize()
            order_queue_size = self._order_queue.qsize()
            
            if data_queue_size > self.config.data_queue_size * 0.8:
                self.logger.warning(f"数据队列接近满载: {data_queue_size}")
            
            if order_queue_size > self.config.order_queue_size * 0.8:
                self.logger.warning(f"订单队列接近满载: {order_queue_size}")
            
            # 检查策略状态
            for strategy_id, strategy in self._strategies.items():
                if strategy.state == StrategyState.ERROR:
                    self.logger.warning(f"策略异常: {strategy_id}")
                    
        except Exception as e:
            self.logger.error(f"健康检查失败: {e}")
    
    # ==================== 事件系统 ====================
    
    def add_event_listener(self, event_type: str, callback: Callable):
        """添加事件监听器"""
        if event_type not in self._event_callbacks:
            self._event_callbacks[event_type] = []
        self._event_callbacks[event_type].append(callback)
    
    def _trigger_event(self, event_type: str, *args, **kwargs):
        """触发事件"""
        if event_type in self._event_callbacks:
            for callback in self._event_callbacks[event_type]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        asyncio.create_task(callback(*args, **kwargs))
                    else:
                        self._thread_pool.submit(callback, *args, **kwargs)
                except Exception as e:
                    self.logger.error(f"事件回调异常 {event_type}: {e}")
    
    # ==================== 查询接口 ====================
    
    def get_strategy(self, strategy_id: str) -> Optional[BaseStrategy]:
        """获取策略"""
        return self._strategies.get(strategy_id)
    
    def get_all_strategies(self) -> Dict[str, BaseStrategy]:
        """获取所有策略"""
        return self._strategies.copy()
    
    def get_strategy_states(self) -> Dict[str, StrategyState]:
        """获取策略状态"""
        return {sid: strategy.state for sid, strategy in self._strategies.items()}
    
    def get_pending_orders(self) -> Dict[str, OrderInfo]:
        """获取待处理订单"""
        return self._pending_orders.copy()
    
    def get_market_data(self, symbol: str) -> Optional[MarketData]:
        """获取市场数据"""
        return self._data_cache.get(symbol)


class StrategyManager:
    """
    策略管理器
    
    提供策略的高级管理功能，包括策略组合、资金分配、
    风险控制等。
    """
    
    def __init__(self, engine: StrategyEngine):
        """
        初始化策略管理器
        
        Args:
            engine: 策略引擎
        """
        self.engine = engine
        self.logger = logging.getLogger(f"strategy_manager.{engine.engine_id}")
        
        # 策略组合
        self._strategy_groups: Dict[str, List[str]] = {}
        self._group_configs: Dict[str, Dict[str, Any]] = {}
        
        # 资金分配
        self._capital_allocations: Dict[str, float] = {}
        self._group_allocations: Dict[str, float] = {}
        
        # 绩效监控
        self._group_performance: Dict[str, Dict[str, Any]] = {}
        
        self.logger.info("策略管理器初始化完成")
    
    # ==================== 策略组合管理 ====================
    
    def create_strategy_group(self, group_name: str, strategy_ids: List[str],
                            capital_allocation: float = 1.0,
                            config: Optional[Dict[str, Any]] = None) -> bool:
        """创建策略组合"""
        try:
            if group_name in self._strategy_groups:
                self.logger.error(f"策略组合已存在: {group_name}")
                return False
            
            # 验证策略存在
            for strategy_id in strategy_ids:
                if strategy_id not in self.engine._strategies:
                    self.logger.error(f"策略不存在: {strategy_id}")
                    return False
            
            # 创建组合
            self._strategy_groups[group_name] = strategy_ids.copy()
            self._group_allocations[group_name] = capital_allocation
            self._group_configs[group_name] = config or {}
            
            self.logger.info(f"策略组合创建成功: {group_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"创建策略组合失败: {e}")
            return False
    
    def add_strategy_to_group(self, group_name: str, strategy_id: str) -> bool:
        """添加策略到组合"""
        try:
            if group_name not in self._strategy_groups:
                self.logger.error(f"策略组合不存在: {group_name}")
                return False
            
            if strategy_id not in self.engine._strategies:
                self.logger.error(f"策略不存在: {strategy_id}")
                return False
            
            if strategy_id not in self._strategy_groups[group_name]:
                self._strategy_groups[group_name].append(strategy_id)
                self.logger.info(f"策略添加到组合: {strategy_id} -> {group_name}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"添加策略到组合失败: {e}")
            return False
    
    def remove_strategy_from_group(self, group_name: str, strategy_id: str) -> bool:
        """从组合移除策略"""
        try:
            if group_name not in self._strategy_groups:
                self.logger.error(f"策略组合不存在: {group_name}")
                return False
            
            if strategy_id in self._strategy_groups[group_name]:
                self._strategy_groups[group_name].remove(strategy_id)
                self.logger.info(f"策略从组合移除: {strategy_id} <- {group_name}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"从组合移除策略失败: {e}")
            return False
    
    async def start_strategy_group(self, group_name: str) -> bool:
        """启动策略组合"""
        try:
            if group_name not in self._strategy_groups:
                self.logger.error(f"策略组合不存在: {group_name}")
                return False
            
            # 分配资金
            await self._allocate_capital_to_group(group_name)
            
            # 启动组合中的所有策略
            started_count = 0
            for strategy_id in self._strategy_groups[group_name]:
                if await self.engine.start_strategy(strategy_id):
                    started_count += 1
            
            self.logger.info(f"策略组合启动: {group_name}, 成功启动 {started_count} 个策略")
            return started_count > 0
            
        except Exception as e:
            self.logger.error(f"启动策略组合失败: {e}")
            return False
    
    async def stop_strategy_group(self, group_name: str) -> bool:
        """停止策略组合"""
        try:
            if group_name not in self._strategy_groups:
                self.logger.error(f"策略组合不存在: {group_name}")
                return False
            
            # 停止组合中的所有策略
            stopped_count = 0
            for strategy_id in self._strategy_groups[group_name]:
                if await self.engine.stop_strategy(strategy_id):
                    stopped_count += 1
            
            self.logger.info(f"策略组合停止: {group_name}, 成功停止 {stopped_count} 个策略")
            return stopped_count > 0
            
        except Exception as e:
            self.logger.error(f"停止策略组合失败: {e}")
            return False
    
    # ==================== 资金分配 ====================
    
    async def _allocate_capital_to_group(self, group_name: str):
        """分配资金到组合"""
        try:
            if group_name not in self._strategy_groups:
                return
            
            group_allocation = self._group_allocations.get(group_name, 1.0)
            strategy_ids = self._strategy_groups[group_name]
            
            if not strategy_ids:
                return
            
            # 平均分配资金到策略
            capital_per_strategy = group_allocation / len(strategy_ids)
            
            for strategy_id in strategy_ids:
                self._capital_allocations[strategy_id] = capital_per_strategy
                
                # 更新策略配置
                if strategy_id in self.engine._strategies:
                    strategy = self.engine._strategies[strategy_id]
                    # 这里可以更新策略的资金配置
                    # strategy.config.initial_capital *= capital_per_strategy
            
            self.logger.info(f"资金分配完成: {group_name}, 每策略分配: {capital_per_strategy:.2%}")
            
        except Exception as e:
            self.logger.error(f"资金分配失败: {e}")
    
    # ==================== 绩效监控 ====================
    
    async def update_group_performance(self, group_name: str) -> Dict[str, Any]:
        """更新组合绩效"""
        try:
            if group_name not in self._strategy_groups:
                return {}
            
            strategy_ids = self._strategy_groups[group_name]
            
            # 聚合策略绩效
            total_pnl = 0.0
            total_trades = 0
            group_stats = []
            
            for strategy_id in strategy_ids:
                if strategy_id in self.engine._strategies:
                    strategy = self.engine._strategies[strategy_id]
                    stats = strategy.performance_stats
                    
                    total_pnl += stats.get('total_pnl', 0)
                    total_trades += stats.get('trade_count', 0)
                    group_stats.append(stats)
            
            # 计算组合指标
            group_performance = {
                'timestamp': datetime.now(),
                'total_pnl': total_pnl,
                'total_trades': total_trades,
                'strategy_count': len(strategy_ids),
                'running_strategies': len([s for s in strategy_ids 
                                         if s in self.engine._strategies and 
                                         self.engine._strategies[s].is_running]),
                'individual_stats': group_stats
            }
            
            self._group_performance[group_name] = group_performance
            return group_performance
            
        except Exception as e:
            self.logger.error(f"更新组合绩效失败: {e}")
            return {}
    
    def get_group_performance(self, group_name: str) -> Dict[str, Any]:
        """获取组合绩效"""
        return self._group_performance.get(group_name, {})
    
    def get_all_groups(self) -> Dict[str, List[str]]:
        """获取所有策略组合"""
        return self._strategy_groups.copy()
    
    def get_group_config(self, group_name: str) -> Dict[str, Any]:
        """获取组合配置"""
        return self._group_configs.get(group_name, {})
