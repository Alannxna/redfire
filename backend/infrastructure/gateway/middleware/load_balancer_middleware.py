"""
负载均衡中间件
=============

实现服务实例的负载均衡选择
"""

import time
import random
import logging
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from fastapi import Request, HTTPException, status
import asyncio
import httpx
from enum import Enum

from ..config.gateway_config import LoadBalancerConfig

logger = logging.getLogger(__name__)


class ServiceStatus(Enum):
    """服务状态"""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    CIRCUIT_OPEN = "circuit_open"


@dataclass
class ServiceInstance:
    """服务实例"""
    id: str
    name: str
    host: str
    port: int
    weight: int = 1
    status: ServiceStatus = ServiceStatus.HEALTHY
    
    # 健康检查
    health_check_url: Optional[str] = None
    last_health_check: float = 0
    consecutive_failures: int = 0
    
    # 连接统计
    active_connections: int = 0
    total_requests: int = 0
    failed_requests: int = 0
    response_times: List[float] = field(default_factory=list)
    
    @property
    def url(self) -> str:
        """服务URL"""
        return f"http://{self.host}:{self.port}"
    
    @property
    def average_response_time(self) -> float:
        """平均响应时间"""
        if not self.response_times:
            return 0.0
        return sum(self.response_times[-100:]) / len(self.response_times[-100:])  # 最近100次
    
    @property
    def success_rate(self) -> float:
        """成功率"""
        if self.total_requests == 0:
            return 1.0
        return (self.total_requests - self.failed_requests) / self.total_requests
    
    def record_request(self, success: bool, response_time: float):
        """记录请求结果"""
        self.total_requests += 1
        if not success:
            self.failed_requests += 1
            self.consecutive_failures += 1
        else:
            self.consecutive_failures = 0
        
        self.response_times.append(response_time)
        if len(self.response_times) > 1000:  # 保留最近1000次记录
            self.response_times = self.response_times[-1000:]


class CircuitBreaker:
    """熔断器"""
    
    def __init__(self, failure_threshold: int = 5, recovery_time: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_time = recovery_time
        self.state = "closed"  # closed, open, half_open
        self.failure_count = 0
        self.last_failure_time = 0
        self.next_attempt_time = 0
    
    def record_success(self):
        """记录成功"""
        self.failure_count = 0
        self.state = "closed"
    
    def record_failure(self):
        """记录失败"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "open"
            self.next_attempt_time = time.time() + self.recovery_time
    
    def can_execute(self) -> bool:
        """是否可以执行请求"""
        now = time.time()
        
        if self.state == "closed":
            return True
        elif self.state == "open":
            if now >= self.next_attempt_time:
                self.state = "half_open"
                return True
            return False
        else:  # half_open
            return True


class LoadBalancerAlgorithm:
    """负载均衡算法基类"""
    
    def select_instance(self, instances: List[ServiceInstance], request: Request) -> Optional[ServiceInstance]:
        """选择服务实例"""
        raise NotImplementedError


class RoundRobinAlgorithm(LoadBalancerAlgorithm):
    """轮询算法"""
    
    def __init__(self):
        self.current_index = 0
    
    def select_instance(self, instances: List[ServiceInstance], request: Request) -> Optional[ServiceInstance]:
        if not instances:
            return None
        
        healthy_instances = [inst for inst in instances if inst.status == ServiceStatus.HEALTHY]
        if not healthy_instances:
            return None
        
        instance = healthy_instances[self.current_index % len(healthy_instances)]
        self.current_index += 1
        return instance


class WeightedRoundRobinAlgorithm(LoadBalancerAlgorithm):
    """加权轮询算法"""
    
    def __init__(self):
        self.weighted_list: List[ServiceInstance] = []
        self.current_index = 0
    
    def select_instance(self, instances: List[ServiceInstance], request: Request) -> Optional[ServiceInstance]:
        if not instances:
            return None
        
        healthy_instances = [inst for inst in instances if inst.status == ServiceStatus.HEALTHY]
        if not healthy_instances:
            return None
        
        # 重建加权列表
        if not self.weighted_list or set(self.weighted_list) != set(healthy_instances):
            self.weighted_list = []
            for instance in healthy_instances:
                self.weighted_list.extend([instance] * instance.weight)
        
        if not self.weighted_list:
            return None
        
        instance = self.weighted_list[self.current_index % len(self.weighted_list)]
        self.current_index += 1
        return instance


class LeastConnectionsAlgorithm(LoadBalancerAlgorithm):
    """最少连接算法"""
    
    def select_instance(self, instances: List[ServiceInstance], request: Request) -> Optional[ServiceInstance]:
        if not instances:
            return None
        
        healthy_instances = [inst for inst in instances if inst.status == ServiceStatus.HEALTHY]
        if not healthy_instances:
            return None
        
        # 选择连接数最少的实例
        return min(healthy_instances, key=lambda x: x.active_connections)


class RandomAlgorithm(LoadBalancerAlgorithm):
    """随机算法"""
    
    def select_instance(self, instances: List[ServiceInstance], request: Request) -> Optional[ServiceInstance]:
        if not instances:
            return None
        
        healthy_instances = [inst for inst in instances if inst.status == ServiceStatus.HEALTHY]
        if not healthy_instances:
            return None
        
        return random.choice(healthy_instances)


class LoadBalancerMiddleware:
    """负载均衡中间件"""
    
    def __init__(self, config: LoadBalancerConfig):
        self.config = config
        self.services: Dict[str, List[ServiceInstance]] = {}
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        
        # 选择负载均衡算法
        self.algorithm = self._create_algorithm(config.algorithm)
        
        # HTTP客户端用于健康检查
        self.http_client = httpx.AsyncClient(timeout=httpx.Timeout(config.health_check_timeout))
        
        # 启动健康检查任务
        if config.health_check_enabled:
            asyncio.create_task(self._health_check_loop())
    
    def _create_algorithm(self, algorithm_name: str) -> LoadBalancerAlgorithm:
        """创建负载均衡算法"""
        algorithms = {
            "round_robin": RoundRobinAlgorithm,
            "weighted": WeightedRoundRobinAlgorithm,
            "least_connections": LeastConnectionsAlgorithm,
            "random": RandomAlgorithm
        }
        
        algorithm_class = algorithms.get(algorithm_name, RoundRobinAlgorithm)
        return algorithm_class()
    
    def register_service(self, service_name: str, instances: List[Dict[str, Any]]):
        """注册服务实例"""
        service_instances = []
        
        for i, instance_config in enumerate(instances):
            instance = ServiceInstance(
                id=f"{service_name}_{i}",
                name=service_name,
                host=instance_config["host"],
                port=instance_config["port"],
                weight=instance_config.get("weight", 1),
                health_check_url=instance_config.get("health_check_url", "/health")
            )
            service_instances.append(instance)
            
            # 初始化熔断器
            if self.config.circuit_breaker_enabled:
                self.circuit_breakers[instance.id] = CircuitBreaker(
                    self.config.circuit_breaker_threshold
                )
        
        self.services[service_name] = service_instances
        logger.info(f"注册服务 {service_name}，实例数: {len(service_instances)}")
    
    async def select_instance(self, service_name: str, request: Request) -> Optional[ServiceInstance]:
        """选择服务实例"""
        instances = self.services.get(service_name, [])
        if not instances:
            logger.warning(f"服务 {service_name} 没有可用实例")
            return None
        
        # 过滤熔断状态的实例
        available_instances = []
        for instance in instances:
            if self.config.circuit_breaker_enabled:
                circuit_breaker = self.circuit_breakers.get(instance.id)
                if circuit_breaker and not circuit_breaker.can_execute():
                    instance.status = ServiceStatus.CIRCUIT_OPEN
                    continue
            
            if instance.status in [ServiceStatus.HEALTHY, ServiceStatus.CIRCUIT_OPEN]:
                available_instances.append(instance)
        
        if not available_instances:
            logger.warning(f"服务 {service_name} 没有健康实例")
            return None
        
        # 使用负载均衡算法选择实例
        selected = self.algorithm.select_instance(available_instances, request)
        
        if selected:
            selected.active_connections += 1
            logger.debug(f"选择实例: {selected.id}")
        
        return selected
    
    def record_request_result(self, instance: ServiceInstance, success: bool, response_time: float):
        """记录请求结果"""
        instance.active_connections = max(0, instance.active_connections - 1)
        instance.record_request(success, response_time)
        
        # 更新熔断器状态
        if self.config.circuit_breaker_enabled:
            circuit_breaker = self.circuit_breakers.get(instance.id)
            if circuit_breaker:
                if success:
                    circuit_breaker.record_success()
                    if instance.status == ServiceStatus.CIRCUIT_OPEN:
                        instance.status = ServiceStatus.HEALTHY
                        logger.info(f"实例 {instance.id} 恢复健康")
                else:
                    circuit_breaker.record_failure()
                    if circuit_breaker.state == "open":
                        instance.status = ServiceStatus.CIRCUIT_OPEN
                        logger.warning(f"实例 {instance.id} 熔断开启")
    
    async def _health_check_loop(self):
        """健康检查循环"""
        while True:
            try:
                await self._perform_health_checks()
                await asyncio.sleep(30)  # 30秒检查一次
            except Exception as e:
                logger.error(f"健康检查循环错误: {e}")
                await asyncio.sleep(5)
    
    async def _perform_health_checks(self):
        """执行健康检查"""
        for service_name, instances in self.services.items():
            for instance in instances:
                await self._check_instance_health(instance)
    
    async def _check_instance_health(self, instance: ServiceInstance):
        """检查实例健康状态"""
        if not instance.health_check_url:
            return
        
        health_url = f"{instance.url}{instance.health_check_url}"
        
        try:
            start_time = time.time()
            response = await self.http_client.get(health_url)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                if instance.status == ServiceStatus.UNHEALTHY:
                    logger.info(f"实例 {instance.id} 恢复健康")
                instance.status = ServiceStatus.HEALTHY
                instance.consecutive_failures = 0
            else:
                self._mark_instance_unhealthy(instance)
                
        except Exception as e:
            logger.debug(f"实例 {instance.id} 健康检查失败: {e}")
            self._mark_instance_unhealthy(instance)
        
        instance.last_health_check = time.time()
    
    def _mark_instance_unhealthy(self, instance: ServiceInstance):
        """标记实例为不健康"""
        instance.consecutive_failures += 1
        
        if instance.consecutive_failures >= 3:  # 连续3次失败才标记为不健康
            if instance.status == ServiceStatus.HEALTHY:
                logger.warning(f"实例 {instance.id} 标记为不健康")
            instance.status = ServiceStatus.UNHEALTHY
    
    async def get_service_stats(self, service_name: str) -> Dict[str, Any]:
        """获取服务统计信息"""
        instances = self.services.get(service_name, [])
        
        stats = {
            "service_name": service_name,
            "total_instances": len(instances),
            "healthy_instances": len([i for i in instances if i.status == ServiceStatus.HEALTHY]),
            "instances": []
        }
        
        for instance in instances:
            instance_stats = {
                "id": instance.id,
                "host": instance.host,
                "port": instance.port,
                "status": instance.status.value,
                "weight": instance.weight,
                "active_connections": instance.active_connections,
                "total_requests": instance.total_requests,
                "failed_requests": instance.failed_requests,
                "success_rate": instance.success_rate,
                "average_response_time": instance.average_response_time,
                "consecutive_failures": instance.consecutive_failures
            }
            stats["instances"].append(instance_stats)
        
        return stats
    
    async def close(self):
        """关闭中间件"""
        await self.http_client.aclose()
