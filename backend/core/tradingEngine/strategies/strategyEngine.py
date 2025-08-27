"""
独立策略引擎

提供独立的策略运行环境，确保策略间隔离并支持多策略并发执行。
"""

import logging
import asyncio
import uuid
from typing import Dict, List, Optional, Any, Callable, Type
from dataclasses import dataclass
from enum import Enum
from abc import ABC, abstractmethod
import time
import threading
from pathlib import Path
import importlib.util
import sys


class StrategyState(Enum):
    """策略状态"""
    UNKNOWN = "unknown"
    LOADING = "loading"
    LOADED = "loaded"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


class StrategyIsolationLevel(Enum):
    """策略隔离级别"""
    NONE = "none"          # 无隔离
    THREAD = "thread"      # 线程隔离
    PROCESS = "process"    # 进程隔离


@dataclass
class StrategyConfig:
    """策略配置"""
    strategy_id: str
    strategy_name: str
    strategy_class: str
    strategy_module: str
    isolation_level: StrategyIsolationLevel = StrategyIsolationLevel.THREAD
    max_memory_mb: int = 512
    max_cpu_percent: float = 50.0
    timeout_seconds: int = 300
    auto_restart: bool = True
    restart_count: int = 0
    max_restart_count: int = 3
    config_data: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.config_data is None:
            self.config_data = {}


class BaseStrategy(ABC):
    """
    基础策略类
    
    所有策略都应该继承此类并实现抽象方法
    """
    
    def __init__(self, strategy_id: str, config: StrategyConfig):
        self.strategy_id = strategy_id
        self.config = config
        self.logger = logging.getLogger(f"strategy.{strategy_id}")
        
        # 策略状态
        self.state = StrategyState.UNKNOWN
        self.start_time: Optional[float] = None
        self.stop_time: Optional[float] = None
        
        # 事件回调
        self.on_tick_callback: Optional[Callable] = None
        self.on_bar_callback: Optional[Callable] = None
        self.on_order_callback: Optional[Callable] = None
        self.on_trade_callback: Optional[Callable] = None
        
        # 性能统计
        self.performance_stats: Dict[str, Any] = {}
        
        # 初始化策略
        self._initialize()
    
    def _initialize(self):
        """初始化策略"""
        self.state = StrategyState.LOADED
        self.logger.info(f"策略 {self.strategy_id} 初始化完成")
    
    @abstractmethod
    async def on_start(self):
        """策略启动时调用"""
        pass
    
    @abstractmethod
    async def on_stop(self):
        """策略停止时调用"""
        pass
    
    @abstractmethod
    async def on_tick(self, tick_data: Any):
        """行情tick数据处理"""
        pass
    
    @abstractmethod
    async def on_bar(self, bar_data: Any):
        """K线数据处理"""
        pass
    
    @abstractmethod
    async def on_order(self, order_data: Any):
        """订单状态更新处理"""
        pass
    
    @abstractmethod
    async def on_trade(self, trade_data: Any):
        """成交数据处理"""
        pass
    
    def get_state(self) -> StrategyState:
        """获取策略状态"""
        return self.state
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计"""
        return self.performance_stats.copy()
    
    def log_info(self, message: str):
        """记录信息日志"""
        self.logger.info(message)
    
    def log_warning(self, message: str):
        """记录警告日志"""
        self.logger.warning(message)
    
    def log_error(self, message: str):
        """记录错误日志"""
        self.logger.error(message)


class StrategyContainer:
    """
    策略容器
    
    提供策略运行的独立环境，包括资源限制和监控
    """
    
    def __init__(self, strategy_config: StrategyConfig):
        self.config = strategy_config
        self.strategy_instance: Optional[BaseStrategy] = None
        self.logger = logging.getLogger(f"container.{strategy_config.strategy_id}")
        
        # 容器状态
        self.container_id = str(uuid.uuid4())
        self.state = StrategyState.UNKNOWN
        self.start_time: Optional[float] = None
        self.stop_time: Optional[float] = None
        
        # 线程/进程相关
        self.execution_thread: Optional[threading.Thread] = None
        self.event_loop: Optional[asyncio.AbstractEventLoop] = None
        self.stop_event = threading.Event()
        
        # 资源监控
        self.resource_monitor: Optional[threading.Thread] = None
        self.memory_usage_mb = 0
        self.cpu_usage_percent = 0.0
        
        # 事件队列
        self.event_queue = asyncio.Queue()
        
        # 统计信息
        self.stats = {
            'processed_events': 0,
            'errors': 0,
            'restarts': 0,
            'uptime_seconds': 0
        }
    
    async def load_strategy(self) -> bool:
        """加载策略"""
        try:
            self.state = StrategyState.LOADING
            self.logger.info(f"加载策略: {self.config.strategy_name}")
            
            # 动态导入策略模块
            strategy_class = await self._import_strategy_class()
            if not strategy_class:
                return False
            
            # 创建策略实例
            self.strategy_instance = strategy_class(
                self.config.strategy_id,
                self.config
            )
            
            self.state = StrategyState.LOADED
            self.logger.info(f"策略加载成功: {self.config.strategy_name}")
            return True
            
        except Exception as e:
            self.state = StrategyState.ERROR
            self.logger.error(f"策略加载失败: {e}")
            return False
    
    async def _import_strategy_class(self) -> Optional[Type[BaseStrategy]]:
        """动态导入策略类"""
        try:
            # 从模块路径导入
            if self.config.strategy_module.endswith('.py'):
                # 文件路径
                module_path = Path(self.config.strategy_module)
                if not module_path.exists():
                    self.logger.error(f"策略模块文件不存在: {module_path}")
                    return None
                
                spec = importlib.util.spec_from_file_location(
                    f"strategy_{self.config.strategy_id}",
                    module_path
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
            else:
                # 模块名
                module = importlib.import_module(self.config.strategy_module)
            
            # 获取策略类
            strategy_class = getattr(module, self.config.strategy_class)
            
            if not issubclass(strategy_class, BaseStrategy):
                self.logger.error(f"策略类必须继承BaseStrategy: {self.config.strategy_class}")
                return None
            
            return strategy_class
            
        except Exception as e:
            self.logger.error(f"导入策略类失败: {e}")
            return None
    
    async def start(self) -> bool:
        """启动策略容器"""
        try:
            if self.state not in [StrategyState.LOADED, StrategyState.STOPPED]:
                self.logger.warning(f"策略状态不允许启动: {self.state}")
                return False
            
            self.state = StrategyState.STARTING
            self.start_time = time.time()
            self.stop_event.clear()
            
            # 根据隔离级别启动策略
            if self.config.isolation_level == StrategyIsolationLevel.THREAD:
                await self._start_thread_isolated()
            elif self.config.isolation_level == StrategyIsolationLevel.PROCESS:
                await self._start_process_isolated()
            else:
                await self._start_no_isolation()
            
            # 启动资源监控
            await self._start_resource_monitor()
            
            self.state = StrategyState.RUNNING
            self.logger.info(f"策略容器启动成功: {self.config.strategy_name}")
            return True
            
        except Exception as e:
            self.state = StrategyState.ERROR
            self.logger.error(f"策略容器启动失败: {e}")
            return False
    
    async def _start_thread_isolated(self):
        """线程隔离启动"""
        def thread_target():
            # 创建新的事件循环
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            self.event_loop = loop
            
            try:
                # 运行策略
                loop.run_until_complete(self._run_strategy())
            finally:
                loop.close()
        
        self.execution_thread = threading.Thread(target=thread_target, daemon=True)
        self.execution_thread.start()
    
    async def _start_process_isolated(self):
        """进程隔离启动（暂未实现）"""
        # TODO: 实现进程隔离
        self.logger.warning("进程隔离暂未实现，使用线程隔离")
        await self._start_thread_isolated()
    
    async def _start_no_isolation(self):
        """无隔离启动"""
        # 在当前事件循环中运行
        asyncio.create_task(self._run_strategy())
    
    async def _run_strategy(self):
        """运行策略主循环"""
        try:
            if not self.strategy_instance:
                raise RuntimeError("策略实例未创建")
            
            # 启动策略
            await self.strategy_instance.on_start()
            self.strategy_instance.state = StrategyState.RUNNING
            
            # 主事件循环
            while not self.stop_event.is_set():
                try:
                    # 处理事件队列
                    try:
                        event = await asyncio.wait_for(
                            self.event_queue.get(),
                            timeout=1.0
                        )
                        await self._process_event(event)
                        self.stats['processed_events'] += 1
                    except asyncio.TimeoutError:
                        continue
                    
                except Exception as e:
                    self.logger.error(f"处理事件异常: {e}")
                    self.stats['errors'] += 1
                    continue
            
            # 停止策略
            await self.strategy_instance.on_stop()
            self.strategy_instance.state = StrategyState.STOPPED
            
        except Exception as e:
            self.logger.error(f"策略运行异常: {e}")
            self.strategy_instance.state = StrategyState.ERROR
            self.state = StrategyState.ERROR
    
    async def _process_event(self, event: Dict[str, Any]):
        """处理事件"""
        if not self.strategy_instance:
            return
        
        event_type = event.get('type')
        event_data = event.get('data')
        
        if event_type == 'tick':
            await self.strategy_instance.on_tick(event_data)
        elif event_type == 'bar':
            await self.strategy_instance.on_bar(event_data)
        elif event_type == 'order':
            await self.strategy_instance.on_order(event_data)
        elif event_type == 'trade':
            await self.strategy_instance.on_trade(event_data)
        else:
            self.logger.warning(f"未知事件类型: {event_type}")
    
    async def _start_resource_monitor(self):
        """启动资源监控"""
        def monitor_target():
            while not self.stop_event.is_set():
                try:
                    # TODO: 实现实际的资源监控
                    # 监控内存使用量
                    # 监控CPU使用率
                    # 检查是否超过限制
                    time.sleep(5)
                except Exception as e:
                    self.logger.error(f"资源监控异常: {e}")
        
        self.resource_monitor = threading.Thread(target=monitor_target, daemon=True)
        self.resource_monitor.start()
    
    async def stop(self) -> bool:
        """停止策略容器"""
        try:
            if self.state not in [StrategyState.RUNNING, StrategyState.STARTING]:
                self.logger.warning(f"策略状态不允许停止: {self.state}")
                return False
            
            self.state = StrategyState.STOPPING
            self.logger.info(f"停止策略容器: {self.config.strategy_name}")
            
            # 设置停止事件
            self.stop_event.set()
            
            # 等待执行线程结束
            if self.execution_thread and self.execution_thread.is_alive():
                self.execution_thread.join(timeout=10.0)
                if self.execution_thread.is_alive():
                    self.logger.warning("策略执行线程未能在超时时间内停止")
            
            # 等待资源监控线程结束
            if self.resource_monitor and self.resource_monitor.is_alive():
                self.resource_monitor.join(timeout=5.0)
            
            self.state = StrategyState.STOPPED
            self.stop_time = time.time()
            
            # 更新统计信息
            if self.start_time:
                self.stats['uptime_seconds'] = self.stop_time - self.start_time
            
            self.logger.info(f"策略容器已停止: {self.config.strategy_name}")
            return True
            
        except Exception as e:
            self.state = StrategyState.ERROR
            self.logger.error(f"停止策略容器失败: {e}")
            return False
    
    async def send_event(self, event_type: str, event_data: Any):
        """发送事件到策略"""
        try:
            await self.event_queue.put({
                'type': event_type,
                'data': event_data,
                'timestamp': time.time()
            })
        except Exception as e:
            self.logger.error(f"发送事件失败: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """获取容器状态"""
        return {
            'container_id': self.container_id,
            'strategy_id': self.config.strategy_id,
            'strategy_name': self.config.strategy_name,
            'state': self.state.value,
            'isolation_level': self.config.isolation_level.value,
            'start_time': self.start_time,
            'stop_time': self.stop_time,
            'uptime_seconds': time.time() - self.start_time if self.start_time else 0,
            'memory_usage_mb': self.memory_usage_mb,
            'cpu_usage_percent': self.cpu_usage_percent,
            'stats': self.stats.copy(),
            'strategy_state': self.strategy_instance.state.value if self.strategy_instance else None
        }


class IndependentStrategyEngine:
    """
    独立策略引擎
    
    管理多个策略容器，提供策略的独立运行环境
    """
    
    def __init__(self, main_engine=None):
        self.main_engine = main_engine
        self.logger = logging.getLogger(__name__)
        
        # 策略容器管理
        self.strategy_containers: Dict[str, StrategyContainer] = {}
        self.strategy_configs: Dict[str, StrategyConfig] = {}
        
        # 引擎状态
        self.is_active = False
        self.start_time: Optional[float] = None
        
        # 事件分发
        self.event_subscribers: Dict[str, List[str]] = {}  # event_type -> strategy_ids
        
        # 统计信息
        self.stats = {
            'total_strategies': 0,
            'running_strategies': 0,
            'stopped_strategies': 0,
            'error_strategies': 0,
            'total_events_processed': 0
        }
    
    async def start(self) -> bool:
        """启动策略引擎"""
        try:
            if self.is_active:
                self.logger.warning("策略引擎已经运行")
                return True
            
            self.logger.info("启动独立策略引擎...")
            
            self.is_active = True
            self.start_time = time.time()
            
            self.logger.info("独立策略引擎启动成功")
            return True
            
        except Exception as e:
            self.logger.error(f"策略引擎启动失败: {e}")
            return False
    
    async def stop(self) -> bool:
        """停止策略引擎"""
        try:
            if not self.is_active:
                self.logger.warning("策略引擎未运行")
                return True
            
            self.logger.info("停止独立策略引擎...")
            
            # 停止所有策略容器
            for strategy_id, container in self.strategy_containers.items():
                await container.stop()
                self.logger.info(f"策略容器已停止: {strategy_id}")
            
            self.is_active = False
            self.logger.info("独立策略引擎已停止")
            return True
            
        except Exception as e:
            self.logger.error(f"策略引擎停止失败: {e}")
            return False
    
    async def add_strategy(self, config: StrategyConfig) -> bool:
        """添加策略"""
        try:
            if config.strategy_id in self.strategy_containers:
                self.logger.warning(f"策略已存在: {config.strategy_id}")
                return False
            
            # 创建策略容器
            container = StrategyContainer(config)
            
            # 加载策略
            if not await container.load_strategy():
                return False
            
            # 注册容器
            self.strategy_containers[config.strategy_id] = container
            self.strategy_configs[config.strategy_id] = config
            
            # 更新统计
            self.stats['total_strategies'] = len(self.strategy_containers)
            
            self.logger.info(f"策略添加成功: {config.strategy_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"添加策略失败: {e}")
            return False
    
    async def remove_strategy(self, strategy_id: str) -> bool:
        """移除策略"""
        try:
            if strategy_id not in self.strategy_containers:
                self.logger.warning(f"策略不存在: {strategy_id}")
                return False
            
            container = self.strategy_containers[strategy_id]
            
            # 停止策略容器
            await container.stop()
            
            # 移除容器
            del self.strategy_containers[strategy_id]
            del self.strategy_configs[strategy_id]
            
            # 清理事件订阅
            for event_type, subscribers in self.event_subscribers.items():
                if strategy_id in subscribers:
                    subscribers.remove(strategy_id)
            
            # 更新统计
            self.stats['total_strategies'] = len(self.strategy_containers)
            
            self.logger.info(f"策略移除成功: {strategy_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"移除策略失败: {e}")
            return False
    
    async def start_strategy(self, strategy_id: str) -> bool:
        """启动策略"""
        try:
            if strategy_id not in self.strategy_containers:
                self.logger.error(f"策略不存在: {strategy_id}")
                return False
            
            container = self.strategy_containers[strategy_id]
            result = await container.start()
            
            # 更新统计
            self._update_strategy_stats()
            
            return result
            
        except Exception as e:
            self.logger.error(f"启动策略失败: {e}")
            return False
    
    async def stop_strategy(self, strategy_id: str) -> bool:
        """停止策略"""
        try:
            if strategy_id not in self.strategy_containers:
                self.logger.error(f"策略不存在: {strategy_id}")
                return False
            
            container = self.strategy_containers[strategy_id]
            result = await container.stop()
            
            # 更新统计
            self._update_strategy_stats()
            
            return result
            
        except Exception as e:
            self.logger.error(f"停止策略失败: {e}")
            return False
    
    async def broadcast_event(self, event_type: str, event_data: Any):
        """广播事件到所有订阅的策略"""
        try:
            subscribers = self.event_subscribers.get(event_type, [])
            
            for strategy_id in subscribers:
                if strategy_id in self.strategy_containers:
                    container = self.strategy_containers[strategy_id]
                    if container.state == StrategyState.RUNNING:
                        await container.send_event(event_type, event_data)
            
            self.stats['total_events_processed'] += len(subscribers)
            
        except Exception as e:
            self.logger.error(f"广播事件失败: {e}")
    
    def subscribe_event(self, strategy_id: str, event_type: str):
        """订阅事件"""
        if event_type not in self.event_subscribers:
            self.event_subscribers[event_type] = []
        
        if strategy_id not in self.event_subscribers[event_type]:
            self.event_subscribers[event_type].append(strategy_id)
            self.logger.info(f"策略 {strategy_id} 订阅事件 {event_type}")
    
    def unsubscribe_event(self, strategy_id: str, event_type: str):
        """取消订阅事件"""
        if event_type in self.event_subscribers:
            if strategy_id in self.event_subscribers[event_type]:
                self.event_subscribers[event_type].remove(strategy_id)
                self.logger.info(f"策略 {strategy_id} 取消订阅事件 {event_type}")
    
    def _update_strategy_stats(self):
        """更新策略统计"""
        running = 0
        stopped = 0
        error = 0
        
        for container in self.strategy_containers.values():
            if container.state == StrategyState.RUNNING:
                running += 1
            elif container.state == StrategyState.STOPPED:
                stopped += 1
            elif container.state == StrategyState.ERROR:
                error += 1
        
        self.stats.update({
            'running_strategies': running,
            'stopped_strategies': stopped,
            'error_strategies': error
        })
    
    def get_strategy_status(self, strategy_id: str) -> Optional[Dict[str, Any]]:
        """获取策略状态"""
        if strategy_id not in self.strategy_containers:
            return None
        
        return self.strategy_containers[strategy_id].get_status()
    
    def get_all_strategies_status(self) -> Dict[str, Dict[str, Any]]:
        """获取所有策略状态"""
        return {
            strategy_id: container.get_status()
            for strategy_id, container in self.strategy_containers.items()
        }
    
    def get_engine_status(self) -> Dict[str, Any]:
        """获取引擎状态"""
        return {
            'is_active': self.is_active,
            'start_time': self.start_time,
            'uptime_seconds': time.time() - self.start_time if self.start_time else 0,
            'stats': self.stats.copy(),
            'strategies': list(self.strategy_containers.keys()),
            'event_subscribers': {
                event_type: len(subscribers)
                for event_type, subscribers in self.event_subscribers.items()
            }
        }
