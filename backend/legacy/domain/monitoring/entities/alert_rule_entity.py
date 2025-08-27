"""
告警规则实体
==========

定义告警规则的核心实体和值对象
"""

from datetime import datetime
from typing import Dict, Any, Optional, List, Union
from enum import Enum
from pydantic import BaseModel, Field, validator

from ...shared.events.domain_event import DomainEvent


class AlertSeverity(str, Enum):
    """告警严重程度枚举"""
    CRITICAL = "critical"    # 严重
    HIGH = "high"           # 高
    MEDIUM = "medium"       # 中
    LOW = "low"            # 低
    INFO = "info"          # 信息


class AlertCondition(str, Enum):
    """告警条件枚举"""
    GREATER_THAN = "gt"         # 大于
    GREATER_EQUAL = "gte"       # 大于等于
    LESS_THAN = "lt"           # 小于
    LESS_EQUAL = "lte"         # 小于等于
    EQUAL = "eq"               # 等于
    NOT_EQUAL = "ne"           # 不等于
    CONTAINS = "contains"       # 包含
    NOT_CONTAINS = "not_contains"  # 不包含


class AlertStatus(str, Enum):
    """告警状态枚举"""
    ACTIVE = "active"       # 激活
    INACTIVE = "inactive"   # 未激活
    DISABLED = "disabled"   # 已禁用
    RESOLVED = "resolved"   # 已解决


class AlertRule(BaseModel):
    """
    告警规则实体
    
    定义系统监控的告警规则，包含触发条件、
    严重程度、通知方式等配置信息。
    """
    
    rule_id: str = Field(..., description="规则唯一标识")
    rule_name: str = Field(..., description="规则名称")
    description: Optional[str] = Field(None, description="规则描述")
    service_name: str = Field(..., description="监控的服务名称")
    metric_name: str = Field(..., description="监控的指标名称")
    
    # 告警条件
    condition: AlertCondition = Field(..., description="告警条件")
    threshold_value: Union[float, int, str] = Field(..., description="阈值")
    duration_seconds: int = Field(default=60, description="持续时间（秒）")
    
    # 告警配置
    severity: AlertSeverity = Field(..., description="严重程度")
    status: AlertStatus = Field(default=AlertStatus.ACTIVE, description="规则状态")
    
    # 时间配置
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")
    last_triggered_at: Optional[datetime] = Field(None, description="最后触发时间")
    
    # 通知配置
    notification_channels: List[str] = Field(default_factory=list, description="通知渠道")
    notification_template: Optional[str] = Field(None, description="通知模板")
    
    # 扩展配置
    labels: Dict[str, str] = Field(default_factory=dict, description="标签")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="额外元数据")
    
    # 抑制配置
    suppress_duration_seconds: int = Field(default=300, description="抑制持续时间（秒）")
    max_alerts_per_hour: int = Field(default=10, description="每小时最大告警数")
    
    class Config:
        """Pydantic配置"""
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    @validator('duration_seconds')
    def validate_duration(cls, v):
        """验证持续时间"""
        if v <= 0:
            raise ValueError("持续时间必须大于0")
        return v
    
    @validator('suppress_duration_seconds')
    def validate_suppress_duration(cls, v):
        """验证抑制持续时间"""
        if v < 0:
            raise ValueError("抑制持续时间不能为负数")
        return v
    
    @validator('max_alerts_per_hour')
    def validate_max_alerts(cls, v):
        """验证最大告警数"""
        if v <= 0:
            raise ValueError("最大告警数必须大于0")
        return v
    
    def is_active(self) -> bool:
        """检查规则是否激活"""
        return self.status == AlertStatus.ACTIVE
    
    def is_disabled(self) -> bool:
        """检查规则是否已禁用"""
        return self.status == AlertStatus.DISABLED
    
    def evaluate_condition(self, current_value: Union[float, int, str]) -> bool:
        """
        评估告警条件
        
        Args:
            current_value: 当前指标值
            
        Returns:
            bool: 是否满足告警条件
        """
        try:
            if self.condition == AlertCondition.GREATER_THAN:
                return float(current_value) > float(self.threshold_value)
            elif self.condition == AlertCondition.GREATER_EQUAL:
                return float(current_value) >= float(self.threshold_value)
            elif self.condition == AlertCondition.LESS_THAN:
                return float(current_value) < float(self.threshold_value)
            elif self.condition == AlertCondition.LESS_EQUAL:
                return float(current_value) <= float(self.threshold_value)
            elif self.condition == AlertCondition.EQUAL:
                return str(current_value) == str(self.threshold_value)
            elif self.condition == AlertCondition.NOT_EQUAL:
                return str(current_value) != str(self.threshold_value)
            elif self.condition == AlertCondition.CONTAINS:
                return str(self.threshold_value) in str(current_value)
            elif self.condition == AlertCondition.NOT_CONTAINS:
                return str(self.threshold_value) not in str(current_value)
            else:
                return False
        except (ValueError, TypeError):
            return False
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "rule_id": self.rule_id,
            "rule_name": self.rule_name,
            "description": self.description,
            "service_name": self.service_name,
            "metric_name": self.metric_name,
            "condition": self.condition.value,
            "threshold_value": self.threshold_value,
            "duration_seconds": self.duration_seconds,
            "severity": self.severity.value,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "last_triggered_at": self.last_triggered_at.isoformat() if self.last_triggered_at else None,
            "notification_channels": self.notification_channels,
            "notification_template": self.notification_template,
            "labels": self.labels,
            "metadata": self.metadata,
            "suppress_duration_seconds": self.suppress_duration_seconds,
            "max_alerts_per_hour": self.max_alerts_per_hour
        }


class AlertTriggeredEvent(DomainEvent):
    """告警触发事件"""
    event_type: str = "alert_triggered"
    rule_id: str
    rule_name: str
    service_name: str
    metric_name: str
    current_value: Union[float, int, str]
    threshold_value: Union[float, int, str]
    severity: AlertSeverity


class AlertResolvedEvent(DomainEvent):
    """告警解决事件"""
    event_type: str = "alert_resolved"
    rule_id: str
    rule_name: str
    service_name: str
    metric_name: str
    resolved_reason: str


class AlertRuleCreatedEvent(DomainEvent):
    """告警规则创建事件"""
    event_type: str = "alert_rule_created"
    rule_id: str
    rule_name: str
    service_name: str
    severity: AlertSeverity


class AlertRuleUpdatedEvent(DomainEvent):
    """告警规则更新事件"""
    event_type: str = "alert_rule_updated"
    rule_id: str
    rule_name: str
    service_name: str
    changes: Dict[str, Any]


class AlertRuleDeletedEvent(DomainEvent):
    """告警规则删除事件"""
    event_type: str = "alert_rule_deleted"
    rule_id: str
    rule_name: str
    service_name: str
