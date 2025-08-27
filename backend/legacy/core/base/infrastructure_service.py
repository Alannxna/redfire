"""
基础设施服务基类
================

基础设施层服务的基类，提供技术实现相关的功能
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
import asyncio

from .service_base import BaseService, ServiceConfig


@dataclass
class InfrastructureServiceConfig(ServiceConfig):
    """基础设施服务配置"""
    connection_pool_size: int = 10
    connection_timeout: int = 30
    retry_policy: str = "exponential_backoff"  # linear, exponential_backoff, fixed
    circuit_breaker_enabled: bool = True
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout: int = 60
    monitoring_enabled: bool = True
    metrics_collection_interval: int = 60
    resource_limits: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConnectionInfo:
    """连接信息"""
    connection_id: str
    host: str
    port: int
    protocol: str
    status: str
    created_at: str
    last_used: str
    error_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MetricData:
    """指标数据"""
    metric_name: str
    metric_value: Union[int, float, str]
    metric_type: str  # counter, gauge, histogram, summary
    timestamp: str
    tags: Dict[str, str] = field(default_factory=dict)


class BaseInfrastructureService(BaseService, ABC):
    """
    基础设施服务基类
    
    提供基础设施层功能：
    - 连接池管理
    - 资源管理
    - 监控指标收集
    - 断路器模式
    - 重试机制
    - 性能优化
    """
    
    def __init__(self, config: InfrastructureServiceConfig):
        super().__init__(config)
        self.infra_config = config
        
        # 连接池管理
        self.connection_pool: Dict[str, ConnectionInfo] = {}
        self.active_connections: int = 0
        self.max_connections = config.connection_pool_size
        
        # 断路器状态
        self.circuit_breaker_state = "closed"  # closed, open, half_open
        self.circuit_breaker_failures = 0
        self.circuit_breaker_last_failure_time = None
        
        # 监控指标
        self.metrics_data: List[MetricData] = []
        self.performance_stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "average_response_time": 0.0,
            "total_response_time": 0.0
        }
        
        # 资源使用情况
        self.resource_usage = {
            "cpu_usage": 0.0,
            "memory_usage": 0.0,
            "disk_usage": 0.0,
            "network_usage": 0.0
        }
        
        self.logger.info(f"基础设施服务初始化完成")
    
    async def acquire_connection(self, connection_key: str = "default") -> Optional[ConnectionInfo]:
        """
        获取连接
        
        Args:
            connection_key: 连接键
            
        Returns:
            Optional[ConnectionInfo]: 连接信息
        """
        if self.circuit_breaker_state == "open":
            if not await self._check_circuit_breaker():
                raise Exception("Circuit breaker is open")
        
        if self.active_connections >= self.max_connections:
            self.logger.warning("连接池已满，等待可用连接")
            return None
        
        try:
            connection = await self._create_connection(connection_key)
            if connection:
                self.connection_pool[connection.connection_id] = connection
                self.active_connections += 1
                await self._record_metric("connections_acquired", 1, "counter")
                
            return connection
            
        except Exception as e:
            await self._handle_connection_error(str(e))
            raise
    
    async def release_connection(self, connection_id: str):
        """
        释放连接
        
        Args:
            connection_id: 连接ID
        """
        if connection_id in self.connection_pool:
            connection = self.connection_pool[connection_id]
            await self._close_connection(connection)
            del self.connection_pool[connection_id]
            self.active_connections -= 1
            await self._record_metric("connections_released", 1, "counter")
    
    async def execute_with_retry(self, operation: callable, *args, **kwargs) -> Any:
        """
        使用重试机制执行操作
        
        Args:
            operation: 要执行的操作
            *args: 操作参数
            **kwargs: 操作关键字参数
            
        Returns:
            Any: 操作结果
        """
        retry_count = 0
        max_retries = self.config.retry_count
        
        while retry_count < max_retries:
            try:
                start_time = asyncio.get_event_loop().time()
                
                if asyncio.iscoroutinefunction(operation):
                    result = await operation(*args, **kwargs)
                else:
                    result = operation(*args, **kwargs)
                
                # 记录成功指标
                end_time = asyncio.get_event_loop().time()
                response_time = end_time - start_time
                await self._record_performance_metrics(True, response_time)
                
                # 重置断路器
                await self._reset_circuit_breaker()
                
                return result
                
            except Exception as e:
                retry_count += 1
                
                # 记录失败指标
                await self._record_performance_metrics(False, 0)
                
                # 处理断路器
                await self._handle_circuit_breaker_failure()
                
                if retry_count >= max_retries:
                    self.logger.error(f"操作重试失败，已达最大重试次数: {max_retries}")
                    raise
                
                # 计算重试延迟
                delay = await self._calculate_retry_delay(retry_count)
                self.logger.warning(f"操作失败，{delay}秒后重试 (第{retry_count}次): {e}")
                await asyncio.sleep(delay)
        
        raise Exception(f"操作在{max_retries}次重试后仍然失败")
    
    async def collect_metrics(self) -> List[MetricData]:
        """
        收集监控指标
        
        Returns:
            List[MetricData]: 指标数据列表
        """
        current_metrics = []
        
        # 连接池指标
        await self._record_metric("active_connections", self.active_connections, "gauge")
        await self._record_metric("connection_pool_size", self.max_connections, "gauge")
        await self._record_metric("connection_pool_usage", 
                                 self.active_connections / self.max_connections * 100, "gauge")
        
        # 性能指标
        await self._record_metric("total_requests", self.performance_stats["total_requests"], "counter")
        await self._record_metric("successful_requests", self.performance_stats["successful_requests"], "counter")
        await self._record_metric("failed_requests", self.performance_stats["failed_requests"], "counter")
        await self._record_metric("average_response_time", self.performance_stats["average_response_time"], "gauge")
        
        # 断路器指标
        await self._record_metric("circuit_breaker_state", 1 if self.circuit_breaker_state == "open" else 0, "gauge")
        await self._record_metric("circuit_breaker_failures", self.circuit_breaker_failures, "counter")
        
        # 资源使用指标
        await self._update_resource_usage()
        for resource, usage in self.resource_usage.items():
            await self._record_metric(f"resource_{resource}", usage, "gauge")
        
        # 获取子类特定指标
        custom_metrics = await self._collect_custom_metrics()
        current_metrics.extend(custom_metrics)
        
        return self.metrics_data[-100:]  # 返回最近100个指标
    
    async def _create_connection(self, connection_key: str) -> ConnectionInfo:
        """
        创建连接（子类实现）
        
        Args:
            connection_key: 连接键
            
        Returns:
            ConnectionInfo: 连接信息
        """
        return await self._create_connection_impl(connection_key)
    
    async def _close_connection(self, connection: ConnectionInfo):
        """
        关闭连接（子类实现）
        
        Args:
            connection: 连接信息
        """
        await self._close_connection_impl(connection)
    
    async def _handle_connection_error(self, error: str):
        """
        处理连接错误
        
        Args:
            error: 错误信息
        """
        self.logger.error(f"连接错误: {error}")
        await self._record_metric("connection_errors", 1, "counter")
    
    async def _check_circuit_breaker(self) -> bool:
        """
        检查断路器状态
        
        Returns:
            bool: 是否可以继续执行
        """
        if self.circuit_breaker_state == "open":
            if self.circuit_breaker_last_failure_time:
                from datetime import datetime, timedelta
                current_time = datetime.now()
                failure_time = datetime.fromisoformat(self.circuit_breaker_last_failure_time)
                
                if current_time - failure_time > timedelta(seconds=self.infra_config.circuit_breaker_timeout):
                    self.circuit_breaker_state = "half_open"
                    self.logger.info("断路器状态变更为半开")
                    return True
                else:
                    return False
            return False
        
        return True
    
    async def _handle_circuit_breaker_failure(self):
        """处理断路器失败"""
        if not self.infra_config.circuit_breaker_enabled:
            return
        
        self.circuit_breaker_failures += 1
        
        if self.circuit_breaker_failures >= self.infra_config.circuit_breaker_threshold:
            self.circuit_breaker_state = "open"
            self.circuit_breaker_last_failure_time = self._get_current_timestamp()
            self.logger.warning(f"断路器开启，失败次数: {self.circuit_breaker_failures}")
    
    async def _reset_circuit_breaker(self):
        """重置断路器"""
        if self.circuit_breaker_state in ["half_open", "open"]:
            self.circuit_breaker_state = "closed"
            self.circuit_breaker_failures = 0
            self.circuit_breaker_last_failure_time = None
            self.logger.info("断路器重置为关闭状态")
    
    async def _calculate_retry_delay(self, retry_count: int) -> float:
        """
        计算重试延迟
        
        Args:
            retry_count: 重试次数
            
        Returns:
            float: 延迟时间(秒)
        """
        base_delay = self.config.retry_delay
        
        if self.infra_config.retry_policy == "linear":
            return base_delay * retry_count
        elif self.infra_config.retry_policy == "exponential_backoff":
            return base_delay * (2 ** (retry_count - 1))
        else:  # fixed
            return base_delay
    
    async def _record_metric(self, name: str, value: Union[int, float, str], metric_type: str, tags: Dict[str, str] = None):
        """
        记录指标
        
        Args:
            name: 指标名称
            value: 指标值
            metric_type: 指标类型
            tags: 标签
        """
        if not self.infra_config.monitoring_enabled:
            return
        
        metric = MetricData(
            metric_name=name,
            metric_value=value,
            metric_type=metric_type,
            timestamp=self._get_current_timestamp(),
            tags=tags or {}
        )
        
        self.metrics_data.append(metric)
        
        # 保持指标数据不超过1000条
        if len(self.metrics_data) > 1000:
            self.metrics_data = self.metrics_data[-1000:]
    
    async def _record_performance_metrics(self, success: bool, response_time: float):
        """
        记录性能指标
        
        Args:
            success: 是否成功
            response_time: 响应时间
        """
        self.performance_stats["total_requests"] += 1
        
        if success:
            self.performance_stats["successful_requests"] += 1
        else:
            self.performance_stats["failed_requests"] += 1
        
        if response_time > 0:
            self.performance_stats["total_response_time"] += response_time
            self.performance_stats["average_response_time"] = (
                self.performance_stats["total_response_time"] / 
                self.performance_stats["total_requests"]
            )
    
    async def _update_resource_usage(self):
        """更新资源使用情况"""
        try:
            import psutil
            
            # CPU使用率
            self.resource_usage["cpu_usage"] = psutil.cpu_percent()
            
            # 内存使用率
            memory = psutil.virtual_memory()
            self.resource_usage["memory_usage"] = memory.percent
            
            # 磁盘使用率
            disk = psutil.disk_usage('/')
            self.resource_usage["disk_usage"] = (disk.used / disk.total) * 100
            
            # 网络使用情况（简化）
            network = psutil.net_io_counters()
            self.resource_usage["network_usage"] = network.bytes_sent + network.bytes_recv
            
        except ImportError:
            # psutil不可用时的默认值
            pass
    
    def _get_current_timestamp(self) -> str:
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    async def get_infrastructure_metrics(self) -> Dict[str, Any]:
        """
        获取基础设施监控指标
        
        Returns:
            Dict[str, Any]: 基础设施指标
        """
        return {
            "connection_pool": {
                "active_connections": self.active_connections,
                "max_connections": self.max_connections,
                "usage_percentage": (self.active_connections / self.max_connections) * 100
            },
            "circuit_breaker": {
                "state": self.circuit_breaker_state,
                "failures": self.circuit_breaker_failures,
                "enabled": self.infra_config.circuit_breaker_enabled
            },
            "performance": self.performance_stats,
            "resource_usage": self.resource_usage
        }
    
    async def _health_check_impl(self) -> Dict[str, Any]:
        """基础设施服务健康检查实现"""
        infra_metrics = await self.get_infrastructure_metrics()
        
        # 健康检查逻辑
        healthy = True
        health_issues = []
        
        # 检查连接池使用率
        if infra_metrics["connection_pool"]["usage_percentage"] > 90:
            healthy = False
            health_issues.append("连接池使用率过高")
        
        # 检查断路器状态
        if infra_metrics["circuit_breaker"]["state"] == "open":
            healthy = False
            health_issues.append("断路器开启")
        
        # 检查错误率
        total_requests = infra_metrics["performance"]["total_requests"]
        failed_requests = infra_metrics["performance"]["failed_requests"]
        if total_requests > 0 and (failed_requests / total_requests) > 0.1:
            healthy = False
            health_issues.append("错误率过高")
        
        return {
            "infrastructure_healthy": healthy,
            "health_issues": health_issues,
            "infrastructure_metrics": infra_metrics,
            "circuit_breaker_enabled": self.infra_config.circuit_breaker_enabled,
            "monitoring_enabled": self.infra_config.monitoring_enabled
        }
    
    # 子类需要实现的抽象方法
    @abstractmethod
    async def _create_connection_impl(self, connection_key: str) -> ConnectionInfo:
        """
        创建连接的具体实现
        
        Args:
            connection_key: 连接键
            
        Returns:
            ConnectionInfo: 连接信息
        """
        pass
    
    @abstractmethod
    async def _close_connection_impl(self, connection: ConnectionInfo):
        """
        关闭连接的具体实现
        
        Args:
            connection: 连接信息
        """
        pass
    
    async def _collect_custom_metrics(self) -> List[MetricData]:
        """
        收集自定义指标（可选重写）
        
        Returns:
            List[MetricData]: 自定义指标列表
        """
        return []
