"""
网关配置管理
===========

API网关的所有配置参数
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from pydantic import BaseModel


@dataclass
class AuthConfig:
    """认证配置"""
    jwt_secret: str = "your-secret-key"
    jwt_algorithm: str = "HS256"
    jwt_expiration: int = 3600  # 1小时
    public_paths: List[str] = field(default_factory=lambda: [
        "/health", "/docs", "/redoc", "/openapi.json",
        "/api/v1/auth/login", "/api/v1/auth/register"
    ])
    

@dataclass
class RateLimitConfig:
    """限流配置"""
    enabled: bool = True
    default_limit: int = 100  # 每分钟请求数
    burst_limit: int = 200   # 突发请求数
    window_size: int = 60    # 时间窗口(秒)
    storage_type: str = "redis"  # redis | memory
    redis_url: Optional[str] = None


@dataclass
class LoadBalancerConfig:
    """负载均衡配置"""
    algorithm: str = "round_robin"  # round_robin | weighted | least_connections
    health_check_enabled: bool = True
    health_check_timeout: int = 5
    circuit_breaker_enabled: bool = True
    circuit_breaker_threshold: int = 5  # 连续失败次数


@dataclass
class RegistryConfig:
    """服务注册配置"""
    type: str = "redis"  # redis | consul | etcd
    redis_url: str = "redis://localhost:6379/0"
    service_ttl: int = 30  # 服务TTL(秒)
    refresh_interval: int = 10  # 刷新间隔(秒)


@dataclass  
class MonitoringConfig:
    """监控配置"""
    enabled: bool = True
    metrics_path: str = "/metrics"
    detailed_logging: bool = True
    slow_request_threshold: float = 1.0  # 慢请求阈值(秒)


@dataclass
class CORSConfig:
    """CORS配置"""
    allowed_origins: List[str] = field(default_factory=lambda: ["*"])
    allowed_methods: List[str] = field(default_factory=lambda: ["*"])
    allowed_headers: List[str] = field(default_factory=lambda: ["*"])
    allow_credentials: bool = True


@dataclass
class GatewayConfig:
    """网关主配置"""
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    
    # 子配置
    auth: AuthConfig = field(default_factory=AuthConfig)
    rate_limit: RateLimitConfig = field(default_factory=RateLimitConfig)
    load_balancer: LoadBalancerConfig = field(default_factory=LoadBalancerConfig)
    registry: RegistryConfig = field(default_factory=RegistryConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)
    cors: CORSConfig = field(default_factory=CORSConfig)
    
    # 服务配置
    services: Dict[str, Dict[str, Any]] = field(default_factory=lambda: {
        "user_service": {
            "prefix": "/api/v1/users",
            "instances": [{"host": "localhost", "port": 8001}]
        },
        "strategy_service": {
            "prefix": "/api/v1/strategies", 
            "instances": [{"host": "localhost", "port": 8002}]
        },
        "data_service": {
            "prefix": "/api/v1/data",
            "instances": [{"host": "localhost", "port": 8003}]
        },
        "gateway_service": {
            "prefix": "/api/v1/gateway",
            "instances": [{"host": "localhost", "port": 8004}]
        },
        "vnpy_service": {
            "prefix": "/api/v1/vnpy",
            "instances": [{"host": "localhost", "port": 8006}]
        }
    })
    
    # 超时配置
    request_timeout: int = 30
    health_check_interval: int = 30
    
    @classmethod
    def from_env(cls) -> "GatewayConfig":
        """从环境变量创建配置"""
        import os
        
        return cls(
            host=os.getenv("GATEWAY_HOST", "0.0.0.0"),
            port=int(os.getenv("GATEWAY_PORT", "8000")),
            debug=os.getenv("GATEWAY_DEBUG", "false").lower() == "true",
            auth=AuthConfig(
                jwt_secret=os.getenv("JWT_SECRET", "your-secret-key"),
                jwt_algorithm=os.getenv("JWT_ALGORITHM", "HS256"),
                jwt_expiration=int(os.getenv("JWT_EXPIRATION", "3600"))
            ),
            rate_limit=RateLimitConfig(
                enabled=os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true",
                default_limit=int(os.getenv("RATE_LIMIT_DEFAULT", "100")),
                redis_url=os.getenv("REDIS_URL", "redis://localhost:6379/0")
            ),
            registry=RegistryConfig(
                redis_url=os.getenv("REDIS_URL", "redis://localhost:6379/0")
            )
        )


class ServiceRouteConfig(BaseModel):
    """服务路由配置"""
    service_name: str
    path_prefix: str
    strip_prefix: bool = True
    rewrite_rules: Dict[str, str] = {}
    timeout: int = 30
    retries: int = 3
    circuit_breaker: bool = True
