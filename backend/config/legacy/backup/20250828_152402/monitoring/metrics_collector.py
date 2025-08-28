"""
指标收集器
=========

收集和汇总API网关的监控指标
"""

import time
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from collections import defaultdict, deque
import asyncio
from fastapi import Request, Response
import redis.asyncio as redis
import json

from ..config.gateway_config import MonitoringConfig

logger = logging.getLogger(__name__)


@dataclass
class RequestMetrics:
    """请求指标"""
    timestamp: float
    method: str
    path: str
    status_code: int
    response_time: float
    service_name: Optional[str] = None
    user_id: Optional[str] = None
    error_type: Optional[str] = None


@dataclass
class ServiceMetrics:
    """服务指标"""
    name: str
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_response_time: float = 0.0
    min_response_time: float = float('inf')
    max_response_time: float = 0.0
    response_times: deque = field(default_factory=lambda: deque(maxlen=1000))
    
    @property
    def success_rate(self) -> float:
        """成功率"""
        if self.total_requests == 0:
            return 0.0
        return self.successful_requests / self.total_requests * 100
    
    @property
    def average_response_time(self) -> float:
        """平均响应时间"""
        if self.total_requests == 0:
            return 0.0
        return self.total_response_time / self.total_requests
    
    @property
    def p95_response_time(self) -> float:
        """95%分位响应时间"""
        if not self.response_times:
            return 0.0
        sorted_times = sorted(self.response_times)
        index = int(len(sorted_times) * 0.95)
        return sorted_times[min(index, len(sorted_times) - 1)]


class MetricsCollector:
    """指标收集器"""
    
    def __init__(self, config: MonitoringConfig):
        self.config = config
        self.redis: Optional[redis.Redis] = None
        
        # 内存指标
        self.service_metrics: Dict[str, ServiceMetrics] = defaultdict(lambda: ServiceMetrics(""))
        self.recent_requests: deque = deque(maxlen=10000)  # 最近1万个请求
        self.error_counts: Dict[str, int] = defaultdict(int)
        
        # 时间窗口统计
        self.minute_stats = defaultdict(lambda: {"requests": 0, "errors": 0})
        self.hour_stats = defaultdict(lambda: {"requests": 0, "errors": 0})
        
        # 启动时间
        self.start_time = time.time()
        
        # 后台任务
        self._stats_task: Optional[asyncio.Task] = None
    
    async def initialize(self):
        """初始化指标收集器"""
        if self.config.enabled:
            logger.info("初始化指标收集器...")
            
            # 连接Redis（可选）
            if hasattr(self.config, 'redis_url') and self.config.redis_url:
                try:
                    self.redis = redis.from_url(self.config.redis_url, decode_responses=True)
                    await self.redis.ping()
                    logger.info("指标收集器Redis连接成功")
                except Exception as e:
                    logger.warning(f"指标收集器Redis连接失败: {e}")
            
            # 启动统计任务
            self._stats_task = asyncio.create_task(self._stats_aggregation_loop())
            
            logger.info("指标收集器初始化完成")
    
    def record_request_start(self, request: Request):
        """记录请求开始"""
        if not self.config.enabled:
            return
        
        request.state.start_time = time.time()
        request.state.metrics_id = id(request)
    
    def record_request_complete(self, request: Request, response: Response, process_time: float):
        """记录请求完成"""
        if not self.config.enabled:
            return
        
        # 创建请求指标
        metrics = RequestMetrics(
            timestamp=time.time(),
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            response_time=process_time,
            service_name=getattr(request.state, 'service_name', None),
            user_id=getattr(request.state, 'user_id', None)
        )
        
        # 记录到内存
        self._record_request_metrics(metrics)
        
        # 记录慢请求
        if process_time > self.config.slow_request_threshold:
            logger.warning(
                f"慢请求: {request.method} {request.url.path} "
                f"耗时 {process_time:.3f}s"
            )
        
        # 异步持久化到Redis
        if self.redis:
            asyncio.create_task(self._persist_metrics(metrics))
    
    def record_request_error(self, request: Request, error: Exception):
        """记录请求错误"""
        if not self.config.enabled:
            return
        
        error_type = type(error).__name__
        self.error_counts[error_type] += 1
        
        # 记录错误指标
        process_time = time.time() - getattr(request.state, 'start_time', time.time())
        
        metrics = RequestMetrics(
            timestamp=time.time(),
            method=request.method,
            path=request.url.path,
            status_code=getattr(error, 'status_code', 500),
            response_time=process_time,
            service_name=getattr(request.state, 'service_name', None),
            user_id=getattr(request.state, 'user_id', None),
            error_type=error_type
        )
        
        self._record_request_metrics(metrics)
        
        if self.redis:
            asyncio.create_task(self._persist_metrics(metrics))
    
    def _record_request_metrics(self, metrics: RequestMetrics):
        """记录请求指标到内存"""
        # 添加到最近请求
        self.recent_requests.append(metrics)
        
        # 更新服务指标
        if metrics.service_name:
            service_metrics = self.service_metrics[metrics.service_name]
            service_metrics.name = metrics.service_name
            service_metrics.total_requests += 1
            service_metrics.total_response_time += metrics.response_time
            service_metrics.response_times.append(metrics.response_time)
            
            if metrics.status_code < 400:
                service_metrics.successful_requests += 1
            else:
                service_metrics.failed_requests += 1
            
            # 更新响应时间范围
            service_metrics.min_response_time = min(
                service_metrics.min_response_time, 
                metrics.response_time
            )
            service_metrics.max_response_time = max(
                service_metrics.max_response_time,
                metrics.response_time
            )
        
        # 更新时间窗口统计
        now = time.time()
        minute_key = int(now // 60)
        hour_key = int(now // 3600)
        
        self.minute_stats[minute_key]["requests"] += 1
        self.hour_stats[hour_key]["requests"] += 1
        
        if metrics.status_code >= 400:
            self.minute_stats[minute_key]["errors"] += 1
            self.hour_stats[hour_key]["errors"] += 1
    
    async def _persist_metrics(self, metrics: RequestMetrics):
        """持久化指标到Redis"""
        try:
            if not self.redis:
                return
            
            # 存储到Redis Stream
            stream_name = "redfire:metrics:requests"
            data = {
                "timestamp": metrics.timestamp,
                "method": metrics.method,
                "path": metrics.path,
                "status_code": metrics.status_code,
                "response_time": metrics.response_time,
                "service_name": metrics.service_name or "",
                "user_id": metrics.user_id or "",
                "error_type": metrics.error_type or ""
            }
            
            await self.redis.xadd(stream_name, data, maxlen=100000)  # 保留最近10万条记录
            
        except Exception as e:
            logger.error(f"持久化指标失败: {e}")
    
    async def get_metrics(self) -> Dict[str, Any]:
        """获取当前指标"""
        now = time.time()
        uptime = now - self.start_time
        
        # 基础指标
        total_requests = sum(len(self.minute_stats.get(minute, {}).get("requests", 0)) for minute in self.minute_stats)
        total_errors = sum(self.error_counts.values())
        
        # 服务指标
        services_stats = {}
        for service_name, metrics in self.service_metrics.items():
            services_stats[service_name] = {
                "total_requests": metrics.total_requests,
                "success_rate": metrics.success_rate,
                "average_response_time": metrics.average_response_time,
                "p95_response_time": metrics.p95_response_time,
                "min_response_time": metrics.min_response_time if metrics.min_response_time != float('inf') else 0,
                "max_response_time": metrics.max_response_time
            }
        
        # 最近请求统计
        recent_minute = int(now // 60)
        recent_hour = int(now // 3600)
        
        return {
            "gateway": {
                "uptime_seconds": uptime,
                "total_requests": len(self.recent_requests),
                "total_errors": total_errors,
                "requests_per_minute": self.minute_stats.get(recent_minute, {}).get("requests", 0),
                "requests_per_hour": sum(
                    self.minute_stats.get(recent_minute - i, {}).get("requests", 0)
                    for i in range(60)
                ),
                "error_rate": (total_errors / len(self.recent_requests) * 100) if self.recent_requests else 0
            },
            "services": services_stats,
            "errors": dict(self.error_counts),
            "timestamp": now
        }
    
    async def get_detailed_metrics(self, service_name: Optional[str] = None, 
                                 time_range: int = 3600) -> Dict[str, Any]:
        """获取详细指标"""
        now = time.time()
        start_time = now - time_range
        
        # 过滤指定时间范围的请求
        filtered_requests = [
            req for req in self.recent_requests 
            if req.timestamp >= start_time and (not service_name or req.service_name == service_name)
        ]
        
        if not filtered_requests:
            return {"message": "没有找到符合条件的请求"}
        
        # 计算详细统计
        status_codes = defaultdict(int)
        response_times = []
        paths = defaultdict(int)
        methods = defaultdict(int)
        errors = defaultdict(int)
        
        for req in filtered_requests:
            status_codes[req.status_code] += 1
            response_times.append(req.response_time)
            paths[req.path] += 1
            methods[req.method] += 1
            
            if req.error_type:
                errors[req.error_type] += 1
        
        # 响应时间分析
        response_times.sort()
        total_requests = len(filtered_requests)
        
        return {
            "time_range_seconds": time_range,
            "total_requests": total_requests,
            "response_time_stats": {
                "min": min(response_times) if response_times else 0,
                "max": max(response_times) if response_times else 0,
                "avg": sum(response_times) / len(response_times) if response_times else 0,
                "p50": response_times[int(len(response_times) * 0.5)] if response_times else 0,
                "p95": response_times[int(len(response_times) * 0.95)] if response_times else 0,
                "p99": response_times[int(len(response_times) * 0.99)] if response_times else 0
            },
            "status_codes": dict(status_codes),
            "top_paths": dict(sorted(paths.items(), key=lambda x: x[1], reverse=True)[:10]),
            "methods": dict(methods),
            "errors": dict(errors) if errors else {}
        }
    
    async def _stats_aggregation_loop(self):
        """统计聚合循环"""
        while True:
            try:
                await self._aggregate_stats()
                await asyncio.sleep(60)  # 每分钟聚合一次
                
            except Exception as e:
                logger.error(f"统计聚合错误: {e}")
                await asyncio.sleep(10)
    
    async def _aggregate_stats(self):
        """聚合统计数据"""
        now = time.time()
        current_minute = int(now // 60)
        current_hour = int(now // 3600)
        
        # 清理过期的分钟统计（保留24小时）
        cutoff_minute = current_minute - (24 * 60)
        expired_minutes = [k for k in self.minute_stats.keys() if k < cutoff_minute]
        for minute in expired_minutes:
            del self.minute_stats[minute]
        
        # 清理过期的小时统计（保留30天）
        cutoff_hour = current_hour - (30 * 24)
        expired_hours = [k for k in self.hour_stats.keys() if k < cutoff_hour]
        for hour in expired_hours:
            del self.hour_stats[hour]
        
        # 如果启用Redis，聚合数据到Redis
        if self.redis:
            await self._aggregate_to_redis()
    
    async def _aggregate_to_redis(self):
        """聚合数据到Redis"""
        try:
            # 将当前指标快照存储到Redis
            metrics = await self.get_metrics()
            await self.redis.set(
                "redfire:metrics:current",
                json.dumps(metrics),
                ex=300  # 5分钟过期
            )
            
        except Exception as e:
            logger.error(f"Redis聚合失败: {e}")
    
    async def reset_metrics(self):
        """重置指标"""
        self.service_metrics.clear()
        self.recent_requests.clear()
        self.error_counts.clear()
        self.minute_stats.clear()
        self.hour_stats.clear()
        self.start_time = time.time()
        
        logger.info("指标已重置")
    
    async def close(self):
        """关闭指标收集器"""
        if self._stats_task:
            self._stats_task.cancel()
        
        if self.redis:
            await self.redis.close()
        
        logger.info("指标收集器已关闭")
