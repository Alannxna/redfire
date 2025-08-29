"""
资源管理器 - ResourceManager

负责管理系统资源，包括：
1. 内存管理 - 内存分配、监控、优化
2. CPU管理 - CPU使用率监控、负载均衡
3. 线程管理 - 线程池管理、任务调度
4. 缓存管理 - 缓存策略、内存清理
5. 性能优化 - 资源使用优化建议

作者: RedFire团队
创建时间: 2024年9月2日
"""

import time
import threading
import psutil
import gc
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
import weakref

from ...baseEngine import BaseEngine
from ...mainEngine import MainTradingEngine
from ...eventEngine import EventTradingEngine


class ResourceType(Enum):
    """资源类型枚举"""
    MEMORY = "memory"
    CPU = "cpu"
    THREAD = "thread"
    CACHE = "cache"
    NETWORK = "network"
    DISK = "disk"


class ResourceStatus(Enum):
    """资源状态枚举"""
    NORMAL = "normal"        # 正常
    WARNING = "warning"      # 警告
    CRITICAL = "critical"    # 严重
    EXHAUSTED = "exhausted"  # 耗尽


@dataclass
class ResourceThreshold:
    """资源阈值配置"""
    warning_threshold: float = 70.0    # 警告阈值（百分比）
    critical_threshold: float = 90.0   # 严重阈值（百分比）
    action_threshold: float = 95.0     # 行动阈值（百分比）


@dataclass
class ResourceMetrics:
    """资源指标"""
    current_usage: float = 0.0
    peak_usage: float = 0.0
    average_usage: float = 0.0
    status: ResourceStatus = ResourceStatus.NORMAL
    last_update: float = 0.0
    history: deque = field(default_factory=lambda: deque(maxlen=100))


class MemoryManager:
    """内存管理器"""
    
    def __init__(self, threshold: ResourceThreshold):
        self.threshold = threshold
        self.memory_metrics = ResourceMetrics()
        self.memory_watchers: List[Callable] = []
        
        # 获取系统内存信息
        self.total_memory = psutil.virtual_memory().total
        self.available_memory = psutil.virtual_memory().available
    
    def get_memory_usage(self) -> float:
        """获取内存使用率"""
        memory = psutil.virtual_memory()
        usage_percent = memory.percent
        self.available_memory = memory.available
        
        # 更新指标
        self._update_metrics(self.memory_metrics, usage_percent)
        
        return usage_percent
    
    def _update_metrics(self, metrics: ResourceMetrics, current_usage: float):
        """更新资源指标"""
        metrics.current_usage = current_usage
        metrics.last_update = time.time()
        
        if current_usage > metrics.peak_usage:
            metrics.peak_usage = current_usage
        
        # 更新历史记录
        metrics.history.append(current_usage)
        
        # 计算平均使用率
        if metrics.history:
            metrics.average_usage = sum(metrics.history) / len(metrics.history)
        
        # 更新状态
        if current_usage >= self.threshold.critical_threshold:
            metrics.status = ResourceStatus.CRITICAL
        elif current_usage >= self.threshold.warning_threshold:
            metrics.status = ResourceStatus.WARNING
        else:
            metrics.status = ResourceStatus.NORMAL
        
        # 触发告警
        self._trigger_memory_alert(metrics.status, current_usage)
    
    def _trigger_memory_alert(self, status: ResourceStatus, usage: float):
        """触发内存告警"""
        if status in [ResourceStatus.WARNING, ResourceStatus.CRITICAL]:
            for watcher in self.memory_watchers:
                try:
                    watcher(status, usage)
                except Exception as e:
                    print(f"内存告警回调异常: {e}")
    
    def add_memory_watcher(self, watcher: Callable):
        """添加内存监控回调"""
        self.memory_watchers.append(watcher)
    
    def optimize_memory(self):
        """优化内存使用"""
        # 强制垃圾回收
        collected = gc.collect()
        
        # 清理弱引用
        weakref.ref(lambda: None)()
        
        return collected
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """获取内存统计信息"""
        memory = psutil.virtual_memory()
        return {
            "total_memory": self.total_memory,
            "available_memory": self.available_memory,
            "used_memory": memory.used,
            "usage_percent": memory.percent,
            "metrics": {
                "current_usage": self.memory_metrics.current_usage,
                "peak_usage": self.memory_metrics.peak_usage,
                "average_usage": self.memory_metrics.average_usage,
                "status": self.memory_metrics.status.value,
                "last_update": self.memory_metrics.last_update
            }
        }


class ThreadManager:
    """线程管理器"""
    
    def __init__(self, threshold: ResourceThreshold):
        self.threshold = threshold
        self.thread_metrics = ResourceMetrics()
        self.active_threads: Dict[int, threading.Thread] = {}
        self.thread_pools: Dict[str, List[threading.Thread]] = defaultdict(list)
        
    def get_thread_count(self) -> int:
        """获取当前线程数"""
        thread_count = threading.active_count()
        self._update_metrics(self.thread_metrics, thread_count)
        return thread_count
    
    def _update_metrics(self, metrics: ResourceMetrics, current_usage: float):
        """更新资源指标"""
        metrics.current_usage = current_usage
        metrics.last_update = time.time()
        
        if current_usage > metrics.peak_usage:
            metrics.peak_usage = current_usage
        
        # 更新历史记录
        metrics.history.append(current_usage)
        
        # 计算平均使用率
        if metrics.history:
            metrics.average_usage = sum(metrics.history) / len(metrics.history)
        
        # 更新状态
        if current_usage >= self.threshold.critical_threshold:
            metrics.status = ResourceStatus.CRITICAL
        elif current_usage >= self.threshold.warning_threshold:
            metrics.status = ResourceStatus.WARNING
        else:
            metrics.status = ResourceStatus.NORMAL
    
    def register_thread(self, thread: threading.Thread, pool_name: str = "default"):
        """注册线程"""
        self.active_threads[thread.ident] = thread
        self.thread_pools[pool_name].append(thread)
    
    def unregister_thread(self, thread: threading.Thread):
        """注销线程"""
        thread_id = thread.ident
        if thread_id in self.active_threads:
            del self.active_threads[thread_id]
        
        # 从所有线程池中移除
        for pool in self.thread_pools.values():
            if thread in pool:
                pool.remove(thread)
    
    def get_thread_stats(self) -> Dict[str, Any]:
        """获取线程统计信息"""
        return {
            "active_threads": len(self.active_threads),
            "thread_pools": {name: len(threads) for name, threads in self.thread_pools.items()},
            "metrics": {
                "current_usage": self.thread_metrics.current_usage,
                "peak_usage": self.thread_metrics.peak_usage,
                "average_usage": self.thread_metrics.average_usage,
                "status": self.thread_metrics.status.value,
                "last_update": self.thread_metrics.last_update
            }
        }


class ResourceManager(BaseEngine):
    """
    资源管理器
    
    管理系统的各种资源，提供监控和优化功能
    """
    
    def __init__(self, main_engine: MainTradingEngine, event_engine: EventTradingEngine, engine_name: str = "ResourceManager"):
        super().__init__(main_engine, event_engine, engine_name)
        
        # 资源阈值配置
        self.memory_threshold = ResourceThreshold(warning_threshold=75.0, critical_threshold=90.0)
        self.cpu_threshold = ResourceThreshold(warning_threshold=80.0, critical_threshold=95.0)
        self.thread_threshold = ResourceThreshold(warning_threshold=100, critical_threshold=200)
        
        # 资源管理器
        self.memory_manager = MemoryManager(self.memory_threshold)
        self.thread_manager = ThreadManager(self.thread_threshold)
        
        # 监控配置
        self.monitoring_enabled = True
        self.monitoring_interval = 10.0
        
        # 性能优化
        self.auto_optimization = True
        self.optimization_threshold = 85.0
        
        # 初始化
        self._init_resource_manager()
    
    def _init_resource_manager(self):
        """初始化资源管理器"""
        self.logInfo("初始化资源管理器")
        
        # 添加内存监控回调
        self.memory_manager.add_memory_watcher(self._on_memory_alert)
        
        # 启动监控
        if self.monitoring_enabled:
            self._start_resource_monitoring()
    
    def _on_memory_alert(self, status: ResourceStatus, usage: float):
        """内存告警回调"""
        if status == ResourceStatus.CRITICAL:
            self.logWarning(f"内存使用率严重: {usage:.1f}%")
            if self.auto_optimization:
                self._optimize_resources()
        elif status == ResourceStatus.WARNING:
            self.logWarning(f"内存使用率警告: {usage:.1f}%")
    
    def _start_resource_monitoring(self):
        """启动资源监控"""
        def monitoring_loop():
            while self.monitoring_enabled:
                try:
                    self._collect_resource_metrics()
                    time.sleep(self.monitoring_interval)
                except Exception as e:
                    self.logError(f"资源监控异常: {e}")
        
        monitoring_thread = threading.Thread(target=monitoring_loop, daemon=True)
        monitoring_thread.start()
        self.logInfo("启动资源监控")
    
    def _collect_resource_metrics(self):
        """收集资源指标"""
        # 收集内存指标
        memory_usage = self.memory_manager.get_memory_usage()
        
        # 收集线程指标
        thread_count = self.thread_manager.get_thread_count()
        
        # 收集CPU指标
        cpu_usage = psutil.cpu_percent(interval=1)
        
        # 检查是否需要自动优化
        if self.auto_optimization:
            if memory_usage > self.optimization_threshold or cpu_usage > self.optimization_threshold:
                self._optimize_resources()
    
    def _optimize_resources(self):
        """优化资源使用"""
        self.logInfo("开始资源优化")
        
        # 内存优化
        collected = self.memory_manager.optimize_memory()
        self.logInfo(f"垃圾回收完成，回收对象数: {collected}")
        
        # 其他优化措施可以在这里添加
    
    def get_resource_stats(self) -> Dict[str, Any]:
        """获取资源统计信息"""
        return {
            "memory": self.memory_manager.get_memory_stats(),
            "thread": self.thread_manager.get_thread_stats(),
            "cpu": {
                "usage_percent": psutil.cpu_percent(interval=1),
                "count": psutil.cpu_count(),
                "freq": psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None
            },
            "system": {
                "boot_time": psutil.boot_time(),
                "uptime": time.time() - psutil.boot_time()
            }
        }
    
    def register_thread(self, thread: threading.Thread, pool_name: str = "default"):
        """注册线程"""
        self.thread_manager.register_thread(thread, pool_name)
    
    def unregister_thread(self, thread: threading.Thread):
        """注销线程"""
        self.thread_manager.unregister_thread(thread)
    
    def logInfo(self, message: str):
        """记录信息日志"""
        self.main_engine.logInfo(f"[{self.engine_name}] {message}")
    
    def logWarning(self, message: str):
        """记录警告日志"""
        self.main_engine.logWarning(f"[{self.engine_name}] {message}")
    
    def logError(self, message: str):
        """记录错误日志"""
        self.main_engine.logError(f"[{self.engine_name}] {message}")
    
    def close(self):
        """关闭资源管理器"""
        self.logInfo("关闭资源管理器")
        self.monitoring_enabled = False
        super().close()
