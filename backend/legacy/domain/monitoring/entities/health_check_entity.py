"""
健康检查实体
==========

定义系统健康检查的核心实体和值对象
"""

from datetime import datetime
from typing import Dict, Any, Optional, List
from enum import Enum
from pydantic import BaseModel, Field

from ...shared.events.domain_event import DomainEvent


class HealthStatus(str, Enum):
    """健康状态枚举"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class HealthCheckResult(BaseModel):
    """
    健康检查结果实体
    
    表示单次健康检查的完整结果，包含检查状态、
    响应时间、错误信息等详细信息。
    """
    
    check_id: str = Field(..., description="检查唯一标识")
    service_name: str = Field(..., description="服务名称")
    component_name: str = Field(..., description="组件名称")
    status: HealthStatus = Field(..., description="健康状态")
    timestamp: datetime = Field(default_factory=datetime.now, description="检查时间")
    response_time_ms: float = Field(..., description="响应时间（毫秒）")
    message: Optional[str] = Field(None, description="状态消息")
    error_details: Optional[str] = Field(None, description="错误详情")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="额外元数据")
    dependencies: List[str] = Field(default_factory=list, description="依赖的服务列表")
    
    class Config:
        """Pydantic配置"""
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    def is_healthy(self) -> bool:
        """检查是否健康"""
        return self.status == HealthStatus.HEALTHY
    
    def is_degraded(self) -> bool:
        """检查是否降级"""
        return self.status == HealthStatus.DEGRADED
    
    def is_unhealthy(self) -> bool:
        """检查是否不健康"""
        return self.status == HealthStatus.UNHEALTHY
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "check_id": self.check_id,
            "service_name": self.service_name,
            "component_name": self.component_name,
            "status": self.status.value,
            "timestamp": self.timestamp.isoformat(),
            "response_time_ms": self.response_time_ms,
            "message": self.message,
            "error_details": self.error_details,
            "metadata": self.metadata,
            "dependencies": self.dependencies
        }


class HealthCheckStartedEvent(DomainEvent):
    """健康检查开始事件"""
    event_type: str = "health_check_started"
    check_id: str
    service_name: str
    component_name: str


class HealthCheckCompletedEvent(DomainEvent):
    """健康检查完成事件"""
    event_type: str = "health_check_completed"
    check_id: str
    service_name: str
    component_name: str
    status: HealthStatus
    response_time_ms: float


class HealthStatusChangedEvent(DomainEvent):
    """健康状态变更事件"""
    event_type: str = "health_status_changed"
    service_name: str
    component_name: str
    old_status: HealthStatus
    new_status: HealthStatus
    message: Optional[str] = None
