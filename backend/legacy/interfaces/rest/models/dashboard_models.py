"""
仪表盘数据模型
==============

定义仪表盘相关的请求/响应模型
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime


class ServiceConfigModel(BaseModel):
    """服务配置模型"""
    service_id: str = Field(..., description="服务ID")
    name: str = Field(..., description="服务名称")
    port: int = Field(..., description="服务端口")
    description: str = Field(..., description="服务描述")
    type: str = Field(..., description="服务类型")
    health_check: Optional[str] = Field(None, description="健康检查URL")

    class Config:
        json_schema_extra = {
            "example": {
                "service_id": "vnpy_backend",
                "name": "VnPy后端API",
                "port": 8000,
                "description": "FastAPI后端服务 - DDD架构",
                "type": "api",
                "health_check": "http://localhost:8000/health"
            }
        }


class ServiceStatusResponse(BaseModel):
    """服务状态响应模型"""
    service_id: str = Field(..., description="服务ID")
    name: str = Field(..., description="服务名称")
    port: int = Field(..., description="服务端口")
    description: str = Field(..., description="服务描述")
    type: str = Field(..., description="服务类型")
    port_active: bool = Field(..., description="端口是否活跃")
    health_ok: bool = Field(..., description="健康检查是否通过")
    status: str = Field(..., description="服务状态: online/partial/offline")
    last_check: str = Field(..., description="最后检查时间")
    health_details: Optional[Dict[str, Any]] = Field(None, description="健康检查详情")
    internal_status: Optional[Dict[str, Any]] = Field(None, description="内部服务状态")

    class Config:
        json_schema_extra = {
            "example": {
                "service_id": "vnpy_backend",
                "name": "VnPy后端API",
                "port": 8000,
                "description": "FastAPI后端服务 - DDD架构",
                "type": "api",
                "port_active": True,
                "health_ok": True,
                "status": "online",
                "last_check": "2024-01-01T12:00:00",
                "health_details": {
                    "status": "healthy",
                    "version": "1.0.0"
                },
                "internal_status": {
                    "overall_healthy": True,
                    "services": {}
                }
            }
        }


class ServiceHealthResponse(BaseModel):
    """服务健康状态响应模型"""
    service_id: str = Field(..., description="服务ID")
    name: str = Field(..., description="服务名称")
    healthy: bool = Field(..., description="是否健康")
    port_active: bool = Field(..., description="端口是否活跃")
    details: Dict[str, Any] = Field(..., description="健康检查详情")
    response_time: Optional[float] = Field(None, description="响应时间(秒)")
    last_check: str = Field(..., description="最后检查时间")

    class Config:
        json_schema_extra = {
            "example": {
                "service_id": "vnpy_backend",
                "name": "VnPy后端API",
                "healthy": True,
                "port_active": True,
                "details": {
                    "status": "healthy",
                    "version": "1.0.0",
                    "services": {}
                },
                "response_time": 0.123,
                "last_check": "2024-01-01T12:00:00"
            }
        }


class SystemInfoResponse(BaseModel):
    """系统信息响应模型"""
    cpu_percent: float = Field(..., description="CPU使用率(%)")
    memory: Dict[str, Any] = Field(..., description="内存信息")
    disk: Dict[str, Any] = Field(..., description="磁盘信息")
    uptime: float = Field(..., description="系统运行时间(秒)")
    last_check: str = Field(..., description="最后检查时间")

    class Config:
        json_schema_extra = {
            "example": {
                "cpu_percent": 25.5,
                "memory": {
                    "total": 17179869184,
                    "available": 8589934592,
                    "percent": 50.0,
                    "used": 8589934592
                },
                "disk": {
                    "total": 1000000000000,
                    "free": 500000000000,
                    "used": 500000000000,
                    "percent": 50.0
                },
                "uptime": 86400.0,
                "last_check": "2024-01-01T12:00:00"
            }
        }


class DashboardOverviewResponse(BaseModel):
    """仪表盘概览响应模型"""
    total_services: int = Field(..., description="总服务数")
    online_services: int = Field(..., description="在线服务数")
    offline_services: int = Field(..., description="离线服务数")
    partial_services: int = Field(..., description="部分在线服务数")
    system_health: str = Field(..., description="系统健康状态")
    uptime: float = Field(..., description="系统运行时间(秒)")
    cpu_usage: float = Field(..., description="CPU使用率(%)")
    memory_usage: float = Field(..., description="内存使用率(%)")
    disk_usage: float = Field(..., description="磁盘使用率(%)")
    last_update: str = Field(..., description="最后更新时间")

    class Config:
        json_schema_extra = {
            "example": {
                "total_services": 7,
                "online_services": 5,
                "offline_services": 1,
                "partial_services": 1,
                "system_health": "healthy",
                "uptime": 86400.0,
                "cpu_usage": 25.5,
                "memory_usage": 50.0,
                "disk_usage": 45.0,
                "last_update": "2024-01-01T12:00:00"
            }
        }


class AlertModel(BaseModel):
    """告警模型"""
    alert_id: str = Field(..., description="告警ID")
    service_id: str = Field(..., description="服务ID")
    alert_type: str = Field(..., description="告警类型")
    severity: str = Field(..., description="严重程度: low/medium/high/critical")
    title: str = Field(..., description="告警标题")
    message: str = Field(..., description="告警消息")
    created_at: str = Field(..., description="创建时间")
    status: str = Field(..., description="告警状态: active/resolved/acknowledged")

    class Config:
        json_schema_extra = {
            "example": {
                "alert_id": "alert_001",
                "service_id": "vnpy_backend",
                "alert_type": "high_cpu_usage",
                "severity": "medium",
                "title": "CPU使用率过高",
                "message": "CPU使用率超过80%，当前值: 85%",
                "created_at": "2024-01-01T12:00:00",
                "status": "active"
            }
        }


class MetricModel(BaseModel):
    """指标模型"""
    metric_name: str = Field(..., description="指标名称")
    value: float = Field(..., description="指标值")
    unit: str = Field(..., description="单位")
    timestamp: str = Field(..., description="时间戳")
    tags: Optional[Dict[str, str]] = Field(None, description="标签")

    class Config:
        json_schema_extra = {
            "example": {
                "metric_name": "cpu_usage",
                "value": 75.5,
                "unit": "percent",
                "timestamp": "2024-01-01T12:00:00",
                "tags": {
                    "host": "localhost",
                    "service": "vnpy_backend"
                }
            }
        }


class DashboardStatsResponse(BaseModel):
    """仪表盘统计响应模型"""
    services: List[ServiceStatusResponse] = Field(..., description="服务状态列表")
    system_info: SystemInfoResponse = Field(..., description="系统信息")
    overview: DashboardOverviewResponse = Field(..., description="概览信息")
    alerts: List[AlertModel] = Field(default=[], description="活跃告警列表")
    recent_metrics: List[MetricModel] = Field(default=[], description="最近的指标数据")

    class Config:
        json_schema_extra = {
            "example": {
                "services": [],
                "system_info": {},
                "overview": {},
                "alerts": [],
                "recent_metrics": []
            }
        }
