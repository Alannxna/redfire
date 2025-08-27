"""
服务间HTTP客户端
===============

提供微服务间HTTP通信的统一客户端
"""

import time
import logging
import asyncio
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass
from enum import Enum
import httpx
import json

logger = logging.getLogger(__name__)


class RetryStrategy(Enum):
    """重试策略"""
    NONE = "none"
    FIXED = "fixed"
    EXPONENTIAL = "exponential"
    LINEAR = "linear"


@dataclass
class ServiceResponse:
    """服务响应"""
    status_code: int
    data: Any
    headers: Dict[str, str]
    response_time: float
    service_name: str
    success: bool
    
    @property
    def is_success(self) -> bool:
        """是否成功"""
        return self.success and 200 <= self.status_code < 300


@dataclass
class CircuitBreakerConfig:
    """熔断器配置"""
    enabled: bool = True
    failure_threshold: int = 5
    recovery_timeout: int = 60
    half_open_max_calls: int = 3


@dataclass
class RetryConfig:
    """重试配置"""
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 30.0
    backoff_multiplier: float = 2.0


class CircuitBreaker:
    """熔断器"""
    
    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.failure_count = 0
        self.last_failure_time = 0
        self.state = "closed"  # closed, open, half_open
        self.half_open_calls = 0
        
    def can_call(self) -> bool:
        """是否可以调用"""
        if not self.config.enabled:
            return True
            
        now = time.time()
        
        if self.state == "closed":
            return True
        elif self.state == "open":
            if now - self.last_failure_time >= self.config.recovery_timeout:
                self.state = "half_open"
                self.half_open_calls = 0
                return True
            return False
        else:  # half_open
            return self.half_open_calls < self.config.half_open_max_calls
    
    def record_success(self):
        """记录成功"""
        if self.state == "half_open":
            self.state = "closed"
        self.failure_count = 0
    
    def record_failure(self):
        """记录失败"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.state == "half_open":
            self.state = "open"
        elif self.failure_count >= self.config.failure_threshold:
            self.state = "open"
    
    def on_call(self):
        """调用开始"""
        if self.state == "half_open":
            self.half_open_calls += 1


class ServiceClient:
    """服务客户端"""
    
    def __init__(self, 
                 service_name: str,
                 base_url: str,
                 timeout: float = 30.0,
                 retry_config: Optional[RetryConfig] = None,
                 circuit_breaker_config: Optional[CircuitBreakerConfig] = None):
        
        self.service_name = service_name
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        
        # 配置
        self.retry_config = retry_config or RetryConfig()
        self.circuit_breaker = CircuitBreaker(
            circuit_breaker_config or CircuitBreakerConfig()
        )
        
        # HTTP客户端
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=50)
        )
        
        # 统计信息
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.total_response_time = 0.0
        
    async def get(self, path: str, params: Optional[Dict] = None, 
                  headers: Optional[Dict] = None, **kwargs) -> ServiceResponse:
        """GET请求"""
        return await self.request("GET", path, params=params, headers=headers, **kwargs)
    
    async def post(self, path: str, json_data: Optional[Dict] = None,
                   data: Optional[Any] = None, headers: Optional[Dict] = None, **kwargs) -> ServiceResponse:
        """POST请求"""
        return await self.request("POST", path, json=json_data, data=data, headers=headers, **kwargs)
    
    async def put(self, path: str, json_data: Optional[Dict] = None,
                  data: Optional[Any] = None, headers: Optional[Dict] = None, **kwargs) -> ServiceResponse:
        """PUT请求"""
        return await self.request("PUT", path, json=json_data, data=data, headers=headers, **kwargs)
    
    async def delete(self, path: str, headers: Optional[Dict] = None, **kwargs) -> ServiceResponse:
        """DELETE请求"""
        return await self.request("DELETE", path, headers=headers, **kwargs)
    
    async def request(self, method: str, path: str, **kwargs) -> ServiceResponse:
        """通用请求方法"""
        if not self.circuit_breaker.can_call():
            return ServiceResponse(
                status_code=503,
                data={"error": "Circuit breaker is open"},
                headers={},
                response_time=0.0,
                service_name=self.service_name,
                success=False
            )
        
        # 开始调用
        self.circuit_breaker.on_call()
        
        # 执行重试逻辑
        last_exception = None
        
        for attempt in range(self.retry_config.max_retries + 1):
            try:
                response = await self._make_request(method, path, **kwargs)
                
                # 记录成功
                self.circuit_breaker.record_success()
                self._record_success(response.response_time)
                
                return response
                
            except Exception as e:
                last_exception = e
                logger.warning(f"请求失败 {self.service_name} {method} {path} (尝试 {attempt + 1}): {e}")
                
                # 最后一次重试失败
                if attempt == self.retry_config.max_retries:
                    break
                
                # 计算重试延迟
                delay = self._calculate_retry_delay(attempt)
                await asyncio.sleep(delay)
        
        # 所有重试都失败
        self.circuit_breaker.record_failure()
        self._record_failure()
        
        return ServiceResponse(
            status_code=500,
            data={"error": f"Request failed after {self.retry_config.max_retries + 1} attempts", 
                  "last_error": str(last_exception)},
            headers={},
            response_time=0.0,
            service_name=self.service_name,
            success=False
        )
    
    async def _make_request(self, method: str, path: str, **kwargs) -> ServiceResponse:
        """执行HTTP请求"""
        url = f"{self.base_url}{path}"
        start_time = time.time()
        
        try:
            response = await self.client.request(method, url, **kwargs)
            response_time = time.time() - start_time
            
            # 解析响应数据
            try:
                if response.headers.get("content-type", "").startswith("application/json"):
                    data = response.json()
                else:
                    data = response.text
            except Exception:
                data = response.text
            
            return ServiceResponse(
                status_code=response.status_code,
                data=data,
                headers=dict(response.headers),
                response_time=response_time,
                service_name=self.service_name,
                success=200 <= response.status_code < 300
            )
            
        except httpx.TimeoutException:
            response_time = time.time() - start_time
            raise Exception(f"Request timeout after {response_time:.2f}s")
        except httpx.RequestError as e:
            raise Exception(f"Request error: {e}")
    
    def _calculate_retry_delay(self, attempt: int) -> float:
        """计算重试延迟"""
        if self.retry_config.strategy == RetryStrategy.NONE:
            return 0.0
        elif self.retry_config.strategy == RetryStrategy.FIXED:
            return self.retry_config.base_delay
        elif self.retry_config.strategy == RetryStrategy.LINEAR:
            delay = self.retry_config.base_delay * (attempt + 1)
        else:  # EXPONENTIAL
            delay = self.retry_config.base_delay * (self.retry_config.backoff_multiplier ** attempt)
        
        return min(delay, self.retry_config.max_delay)
    
    def _record_success(self, response_time: float):
        """记录成功请求"""
        self.total_requests += 1
        self.successful_requests += 1
        self.total_response_time += response_time
    
    def _record_failure(self):
        """记录失败请求"""
        self.total_requests += 1
        self.failed_requests += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "service_name": self.service_name,
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "success_rate": (self.successful_requests / self.total_requests * 100) if self.total_requests > 0 else 0,
            "average_response_time": (self.total_response_time / self.successful_requests) if self.successful_requests > 0 else 0,
            "circuit_breaker_state": self.circuit_breaker.state,
            "circuit_breaker_failure_count": self.circuit_breaker.failure_count
        }
    
    async def health_check(self, path: str = "/health") -> bool:
        """健康检查"""
        try:
            response = await self.get(path)
            return response.is_success
        except Exception:
            return False
    
    async def close(self):
        """关闭客户端"""
        await self.client.aclose()


class ServiceClientPool:
    """服务客户端池"""
    
    def __init__(self):
        self.clients: Dict[str, ServiceClient] = {}
        self.service_configs: Dict[str, Dict[str, Any]] = {}
    
    def register_service(self, service_name: str, base_url: str, **config):
        """注册服务"""
        self.service_configs[service_name] = {
            "base_url": base_url,
            **config
        }
        
        # 创建客户端
        self.clients[service_name] = ServiceClient(
            service_name=service_name,
            base_url=base_url,
            **config
        )
        
        logger.info(f"注册服务客户端: {service_name} -> {base_url}")
    
    def get_client(self, service_name: str) -> Optional[ServiceClient]:
        """获取服务客户端"""
        return self.clients.get(service_name)
    
    async def call_service(self, service_name: str, method: str, path: str, **kwargs) -> ServiceResponse:
        """调用服务"""
        client = self.get_client(service_name)
        if not client:
            return ServiceResponse(
                status_code=404,
                data={"error": f"Service {service_name} not found"},
                headers={},
                response_time=0.0,
                service_name=service_name,
                success=False
            )
        
        return await client.request(method, path, **kwargs)
    
    async def health_check_all(self) -> Dict[str, bool]:
        """检查所有服务健康状态"""
        results = {}
        
        for service_name, client in self.clients.items():
            try:
                results[service_name] = await client.health_check()
            except Exception:
                results[service_name] = False
        
        return results
    
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """获取所有服务统计"""
        return {
            service_name: client.get_stats()
            for service_name, client in self.clients.items()
        }
    
    async def close_all(self):
        """关闭所有客户端"""
        for client in self.clients.values():
            await client.close()
        self.clients.clear()


# 全局服务客户端池
service_pool = ServiceClientPool()


# 便捷函数
async def call_service(service_name: str, method: str, path: str, **kwargs) -> ServiceResponse:
    """调用服务的便捷函数"""
    return await service_pool.call_service(service_name, method, path, **kwargs)


def register_service(service_name: str, base_url: str, **config):
    """注册服务的便捷函数"""
    service_pool.register_service(service_name, base_url, **config)
