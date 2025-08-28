"""
性能监控工具
"""

import time
import threading
from typing import Dict, Any, List
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class MetricData:
    """指标数据"""
    name: str
    value: float
    timestamp: datetime = field(default_factory=datetime.now)
    tags: Dict[str, str] = field(default_factory=dict)


class PerformanceMonitor:
    """
    性能监控器
    
    功能:
    1. 指标收集和统计
    2. 时间序列数据
    3. 聚合统计
    4. 性能报告
    """
    
    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self._metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_history))
        self._counters: Dict[str, int] = defaultdict(int)
        self._timers: Dict[str, List[float]] = defaultdict(list)
        self._lock = threading.RLock()
        self._start_time = time.time()
    
    def record_metric(self, name: str, value: float, tags: Dict[str, str] = None) -> None:
        """记录指标"""
        with self._lock:
            metric = MetricData(
                name=name,
                value=value,
                tags=tags or {}
            )
            self._metrics[name].append(metric)
    
    def increment_counter(self, name: str, value: int = 1) -> None:
        """增加计数器"""
        with self._lock:
            self._counters[name] += value
    
    def record_timer(self, name: str, duration: float) -> None:
        """记录时间"""
        with self._lock:
            self._timers[name].append(duration)
            # 保持最近的1000个记录
            if len(self._timers[name]) > self.max_history:
                self._timers[name] = self._timers[name][-self.max_history:]
    
    def timer(self, name: str):
        """时间上下文管理器"""
        return TimerContext(self, name)
    
    def get_metric_stats(self, name: str) -> Dict[str, Any]:
        """获取指标统计"""
        with self._lock:
            if name not in self._metrics:
                return {}
            
            values = [m.value for m in self._metrics[name]]
            if not values:
                return {}
            
            return {
                "count": len(values),
                "min": min(values),
                "max": max(values),
                "avg": sum(values) / len(values),
                "latest": values[-1] if values else 0
            }
    
    def get_timer_stats(self, name: str) -> Dict[str, Any]:
        """获取时间统计"""
        with self._lock:
            if name not in self._timers or not self._timers[name]:
                return {}
            
            times = self._timers[name]
            return {
                "count": len(times),
                "min": min(times),
                "max": max(times),
                "avg": sum(times) / len(times),
                "p50": self._percentile(times, 0.5),
                "p90": self._percentile(times, 0.9),
                "p99": self._percentile(times, 0.99)
            }
    
    def get_metrics(self) -> Dict[str, Any]:
        """获取所有指标"""
        with self._lock:
            result = {
                "uptime": time.time() - self._start_time,
                "counters": dict(self._counters),
                "metrics": {},
                "timers": {}
            }
            
            # 指标统计
            for name in self._metrics:
                result["metrics"][name] = self.get_metric_stats(name)
            
            # 时间统计
            for name in self._timers:
                result["timers"][name] = self.get_timer_stats(name)
            
            return result
    
    def reset(self) -> None:
        """重置所有指标"""
        with self._lock:
            self._metrics.clear()
            self._counters.clear()
            self._timers.clear()
            self._start_time = time.time()
    
    def start(self) -> None:
        """启动监控"""
        self._start_time = time.time()
    
    def stop(self) -> None:
        """停止监控"""
        pass
    
    def _percentile(self, values: List[float], p: float) -> float:
        """计算百分位数"""
        if not values:
            return 0.0
        
        sorted_values = sorted(values)
        index = int(len(sorted_values) * p)
        
        if index >= len(sorted_values):
            return sorted_values[-1]
        
        return sorted_values[index]


class TimerContext:
    """时间上下文管理器"""
    
    def __init__(self, monitor: PerformanceMonitor, name: str):
        self.monitor = monitor
        self.name = name
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = time.time() - self.start_time
            self.monitor.record_timer(self.name, duration)
