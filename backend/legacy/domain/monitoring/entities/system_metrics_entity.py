"""
系统指标实体
==========

定义系统性能指标的核心实体和值对象
"""

from datetime import datetime
from typing import Dict, Any, Optional, List, Union
from enum import Enum
from pydantic import BaseModel, Field, validator

from ...shared.events.domain_event import DomainEvent


class MetricType(str, Enum):
    """指标类型枚举"""
    COUNTER = "counter"          # 计数器
    GAUGE = "gauge"              # 计量器
    HISTOGRAM = "histogram"      # 直方图
    SUMMARY = "summary"          # 摘要
    RATE = "rate"               # 速率


class MetricUnit(str, Enum):
    """指标单位枚举"""
    # 时间单位
    MILLISECONDS = "ms"
    SECONDS = "s"
    MINUTES = "min"
    HOURS = "h"
    
    # 存储单位
    BYTES = "bytes"
    KILOBYTES = "KB"
    MEGABYTES = "MB"
    GIGABYTES = "GB"
    
    # 比率单位
    PERCENTAGE = "%"
    RATIO = "ratio"
    
    # 计数单位
    COUNT = "count"
    REQUESTS = "requests"
    ERRORS = "errors"
    
    # 网络单位
    BYTES_PER_SECOND = "bytes/s"
    REQUESTS_PER_SECOND = "requests/s"
    
    # 无单位
    NONE = "none"


class SystemMetrics(BaseModel):
    """
    系统指标实体
    
    表示系统的性能指标数据，包含CPU、内存、磁盘、
    网络等各种系统资源的使用情况。
    """
    
    metric_id: str = Field(..., description="指标唯一标识")
    service_name: str = Field(..., description="服务名称")
    metric_name: str = Field(..., description="指标名称")
    metric_type: MetricType = Field(..., description="指标类型")
    metric_unit: MetricUnit = Field(..., description="指标单位")
    value: Union[float, int] = Field(..., description="指标值")
    timestamp: datetime = Field(default_factory=datetime.now, description="采集时间")
    labels: Dict[str, str] = Field(default_factory=dict, description="标签")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="额外元数据")
    
    # 扩展字段
    min_value: Optional[float] = Field(None, description="最小值")
    max_value: Optional[float] = Field(None, description="最大值")
    avg_value: Optional[float] = Field(None, description="平均值")
    percentiles: Optional[Dict[str, float]] = Field(None, description="百分位数")
    
    class Config:
        """Pydantic配置"""
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    @validator('value')
    def validate_value(cls, v):
        """验证指标值"""
        if v is None:
            raise ValueError("指标值不能为空")
        if isinstance(v, (int, float)) and v < 0:
            raise ValueError("指标值不能为负数")
        return v
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "metric_id": self.metric_id,
            "service_name": self.service_name,
            "metric_name": self.metric_name,
            "metric_type": self.metric_type.value,
            "metric_unit": self.metric_unit.value,
            "value": self.value,
            "timestamp": self.timestamp.isoformat(),
            "labels": self.labels,
            "metadata": self.metadata,
            "min_value": self.min_value,
            "max_value": self.max_value,
            "avg_value": self.avg_value,
            "percentiles": self.percentiles
        }
    
    def get_formatted_value(self) -> str:
        """获取格式化的指标值"""
        if self.metric_unit == MetricUnit.PERCENTAGE:
            return f"{self.value:.2f}%"
        elif self.metric_unit in [MetricUnit.BYTES, MetricUnit.KILOBYTES, MetricUnit.MEGABYTES, MetricUnit.GIGABYTES]:
            return f"{self.value:.2f} {self.metric_unit.value}"
        elif self.metric_unit in [MetricUnit.MILLISECONDS, MetricUnit.SECONDS]:
            return f"{self.value:.2f} {self.metric_unit.value}"
        else:
            return f"{self.value} {self.metric_unit.value}"


class CPUMetrics(SystemMetrics):
    """CPU指标"""
    
    def __init__(self, **data):
        data.setdefault('metric_name', 'cpu_usage')
        data.setdefault('metric_type', MetricType.GAUGE)
        data.setdefault('metric_unit', MetricUnit.PERCENTAGE)
        super().__init__(**data)


class MemoryMetrics(SystemMetrics):
    """内存指标"""
    
    def __init__(self, **data):
        data.setdefault('metric_name', 'memory_usage')
        data.setdefault('metric_type', MetricType.GAUGE)
        data.setdefault('metric_unit', MetricUnit.PERCENTAGE)
        super().__init__(**data)


class DiskMetrics(SystemMetrics):
    """磁盘指标"""
    
    def __init__(self, **data):
        data.setdefault('metric_name', 'disk_usage')
        data.setdefault('metric_type', MetricType.GAUGE)
        data.setdefault('metric_unit', MetricUnit.PERCENTAGE)
        super().__init__(**data)


class NetworkMetrics(SystemMetrics):
    """网络指标"""
    
    def __init__(self, **data):
        data.setdefault('metric_name', 'network_bytes')
        data.setdefault('metric_type', MetricType.COUNTER)
        data.setdefault('metric_unit', MetricUnit.BYTES_PER_SECOND)
        super().__init__(**data)


class MetricCollectedEvent(DomainEvent):
    """指标采集事件"""
    event_type: str = "metric_collected"
    metric_id: str
    service_name: str
    metric_name: str
    value: Union[float, int]


class MetricThresholdExceededEvent(DomainEvent):
    """指标阈值超限事件"""
    event_type: str = "metric_threshold_exceeded"
    metric_id: str
    service_name: str
    metric_name: str
    current_value: Union[float, int]
    threshold_value: Union[float, int]
    threshold_type: str  # "min" or "max"
