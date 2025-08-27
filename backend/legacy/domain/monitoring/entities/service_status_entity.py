"""
服务状态实体
==========

定义服务状态的核心实体和值对象
"""

from datetime import datetime
from typing import Dict, Any, Optional, List
from enum import Enum
from pydantic import BaseModel, Field

from ...shared.events.domain_event import DomainEvent
from .health_check_entity import HealthStatus


class ServiceHealth(str, Enum):
    """服务健康状态枚举"""
    HEALTHY = "healthy"         # 健康
    DEGRADED = "degraded"       # 降级
    UNHEALTHY = "unhealthy"     # 不健康
    MAINTENANCE = "maintenance"  # 维护中
    UNKNOWN = "unknown"         # 未知


class ServiceType(str, Enum):
    """服务类型枚举"""
    WEB_API = "web_api"         # Web API服务
    DATABASE = "database"       # 数据库服务
    CACHE = "cache"            # 缓存服务
    MESSAGE_QUEUE = "message_queue"  # 消息队列
    EXTERNAL_API = "external_api"    # 外部API
    STRATEGY_ENGINE = "strategy_engine"  # 策略引擎
    DATA_FEED = "data_feed"     # 数据源
    MONITORING = "monitoring"   # 监控服务
    OTHER = "other"            # 其他


class ServiceStatus(BaseModel):
    """
    服务状态实体
    
    表示单个服务的完整状态信息，包含健康状态、
    性能指标、依赖关系等详细信息。
    """
    
    service_id: str = Field(..., description="服务唯一标识")
    service_name: str = Field(..., description="服务名称")
    service_type: ServiceType = Field(..., description="服务类型")
    health_status: ServiceHealth = Field(..., description="健康状态")
    
    # 状态信息
    version: Optional[str] = Field(None, description="服务版本")
    uptime_seconds: int = Field(default=0, description="运行时间（秒）")
    last_check_time: datetime = Field(default_factory=datetime.now, description="最后检查时间")
    
    # 性能指标
    response_time_ms: Optional[float] = Field(None, description="响应时间（毫秒）")
    cpu_usage_percent: Optional[float] = Field(None, description="CPU使用率")
    memory_usage_percent: Optional[float] = Field(None, description="内存使用率")
    active_connections: Optional[int] = Field(None, description="活跃连接数")
    
    # 状态消息
    status_message: Optional[str] = Field(None, description="状态消息")
    error_message: Optional[str] = Field(None, description="错误消息")
    
    # 依赖服务
    dependencies: List[str] = Field(default_factory=list, description="依赖的服务列表")
    dependents: List[str] = Field(default_factory=list, description="依赖此服务的服务列表")
    
    # 扩展信息
    metadata: Dict[str, Any] = Field(default_factory=dict, description="额外元数据")
    tags: List[str] = Field(default_factory=list, description="服务标签")
    
    # 统计信息
    total_requests: int = Field(default=0, description="总请求数")
    successful_requests: int = Field(default=0, description="成功请求数")
    failed_requests: int = Field(default=0, description="失败请求数")
    last_error_time: Optional[datetime] = Field(None, description="最后错误时间")
    
    class Config:
        """Pydantic配置"""
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    def is_healthy(self) -> bool:
        """检查服务是否健康"""
        return self.health_status == ServiceHealth.HEALTHY
    
    def is_degraded(self) -> bool:
        """检查服务是否降级"""
        return self.health_status == ServiceHealth.DEGRADED
    
    def is_unhealthy(self) -> bool:
        """检查服务是否不健康"""
        return self.health_status == ServiceHealth.UNHEALTHY
    
    def is_in_maintenance(self) -> bool:
        """检查服务是否在维护中"""
        return self.health_status == ServiceHealth.MAINTENANCE
    
    def get_success_rate(self) -> float:
        """获取成功率"""
        if self.total_requests == 0:
            return 100.0
        return (self.successful_requests / self.total_requests) * 100.0
    
    def get_error_rate(self) -> float:
        """获取错误率"""
        if self.total_requests == 0:
            return 0.0
        return (self.failed_requests / self.total_requests) * 100.0
    
    def get_uptime_formatted(self) -> str:
        """获取格式化的运行时间"""
        hours = self.uptime_seconds // 3600
        minutes = (self.uptime_seconds % 3600) // 60
        seconds = self.uptime_seconds % 60
        
        if hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "service_id": self.service_id,
            "service_name": self.service_name,
            "service_type": self.service_type.value,
            "health_status": self.health_status.value,
            "version": self.version,
            "uptime_seconds": self.uptime_seconds,
            "last_check_time": self.last_check_time.isoformat(),
            "response_time_ms": self.response_time_ms,
            "cpu_usage_percent": self.cpu_usage_percent,
            "memory_usage_percent": self.memory_usage_percent,
            "active_connections": self.active_connections,
            "status_message": self.status_message,
            "error_message": self.error_message,
            "dependencies": self.dependencies,
            "dependents": self.dependents,
            "metadata": self.metadata,
            "tags": self.tags,
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "last_error_time": self.last_error_time.isoformat() if self.last_error_time else None,
            "success_rate": self.get_success_rate(),
            "error_rate": self.get_error_rate(),
            "uptime_formatted": self.get_uptime_formatted()
        }


class ServiceStartedEvent(DomainEvent):
    """服务启动事件"""
    event_type: str = "service_started"
    service_id: str
    service_name: str
    service_type: ServiceType
    version: Optional[str] = None


class ServiceStoppedEvent(DomainEvent):
    """服务停止事件"""
    event_type: str = "service_stopped"
    service_id: str
    service_name: str
    service_type: ServiceType
    reason: Optional[str] = None


class ServiceHealthChangedEvent(DomainEvent):
    """服务健康状态变更事件"""
    event_type: str = "service_health_changed"
    service_id: str
    service_name: str
    old_health: ServiceHealth
    new_health: ServiceHealth
    reason: Optional[str] = None


class ServiceErrorEvent(DomainEvent):
    """服务错误事件"""
    event_type: str = "service_error"
    service_id: str
    service_name: str
    error_message: str
    error_type: str
    stack_trace: Optional[str] = None


class ServiceMetricsUpdatedEvent(DomainEvent):
    """服务指标更新事件"""
    event_type: str = "service_metrics_updated"
    service_id: str
    service_name: str
    metrics: Dict[str, Any]
