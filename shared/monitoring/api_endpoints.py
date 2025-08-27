"""
监控系统API端点

为监控系统提供RESTful API接口，支持：
- 健康检查
- 指标查询
- 告警管理
- 监控状态查询
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json
from fastapi import APIRouter, HTTPException, Query, Path
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

from .unified_monitor import unified_monitor, get_monitoring_metrics, get_monitoring_status
from .prometheus_exporter import get_prometheus_metrics
from .health_check import get_health_status, get_service_health
from .alert_system import alert_manager

# 创建路由器
monitoring_router = APIRouter(prefix="/monitoring", tags=["monitoring"])


# Pydantic模型
class HealthResponse(BaseModel):
    status: str
    timestamp: str
    services: List[Dict[str, Any]]
    system: Dict[str, Any]


class MetricsResponse(BaseModel):
    timestamp: str
    system_health: str
    services_summary: Dict[str, int]
    active_alerts: int
    components: Dict[str, bool]


class AlertResponse(BaseModel):
    alert_id: str
    name: str
    level: str
    status: str
    metric_name: str
    current_value: float
    threshold_value: float
    timestamp: str


# 基础健康检查端点
@monitoring_router.get("/health")
async def health_check():
    """
    基础健康检查端点
    
    返回监控系统自身的健康状态
    """
    try:
        status = await get_monitoring_status()
        
        return {
            "status": "healthy" if status["system_health"] != "error" else "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "version": "2.0.0",
            "components": status["components"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"健康检查失败: {str(e)}")


# 详细健康检查端点
@monitoring_router.get("/health/detailed", response_model=HealthResponse)
async def detailed_health_check():
    """
    详细健康检查
    
    返回所有服务的详细健康状态
    """
    try:
        health_data = await get_health_status()
        return HealthResponse(**health_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取详细健康状态失败: {str(e)}")


# 单个服务健康检查
@monitoring_router.get("/health/{service_id}")
async def service_health_check(service_id: str = Path(..., description="服务ID")):
    """
    单个服务健康检查
    
    Args:
        service_id: 服务ID (如: vnpy_core, user_trading等)
    """
    try:
        health_data = await get_service_health(service_id)
        return health_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取服务健康状态失败: {str(e)}")


# Prometheus指标端点
@monitoring_router.get("/metrics", response_class=PlainTextResponse)
async def prometheus_metrics():
    """
    Prometheus指标端点
    
    返回Prometheus格式的监控指标
    """
    try:
        metrics_data = await get_prometheus_metrics()
        return PlainTextResponse(
            content=metrics_data,
            media_type="text/plain; version=0.0.4; charset=utf-8"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取Prometheus指标失败: {str(e)}")


# 监控指标摘要
@monitoring_router.get("/metrics/summary", response_model=MetricsResponse)
async def metrics_summary():
    """
    监控指标摘要
    
    返回关键监控指标的摘要信息
    """
    try:
        metrics_data = await get_monitoring_metrics()
        return MetricsResponse(**metrics_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取监控指标摘要失败: {str(e)}")


# 完整监控数据
@monitoring_router.get("/metrics/full")
async def full_metrics():
    """
    完整监控数据
    
    返回所有收集到的监控数据
    """
    try:
        if not unified_monitor.last_metrics:
            await unified_monitor.collect_all_metrics()
        
        return unified_monitor.last_metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取完整监控数据失败: {str(e)}")


# 监控状态
@monitoring_router.get("/status")
async def monitoring_status():
    """
    监控系统状态
    
    返回监控系统的整体状态信息
    """
    try:
        status = await get_monitoring_status()
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取监控状态失败: {str(e)}")


# 告警相关端点
@monitoring_router.get("/alerts")
async def list_alerts(
    status: Optional[str] = Query(None, description="告警状态过滤 (active, resolved, silenced)"),
    level: Optional[str] = Query(None, description="告警级别过滤 (critical, error, warning, info)"),
    limit: int = Query(100, ge=1, le=1000, description="返回数量限制")
):
    """
    获取告警列表
    
    Args:
        status: 告警状态过滤
        level: 告警级别过滤  
        limit: 返回数量限制
    """
    try:
        active_alerts = alert_manager.evaluator.get_active_alerts()
        
        # 应用过滤条件
        filtered_alerts = active_alerts
        
        if status:
            filtered_alerts = [a for a in filtered_alerts if a.status.value == status]
        
        if level:
            filtered_alerts = [a for a in filtered_alerts if a.level.value == level]
        
        # 限制数量
        filtered_alerts = filtered_alerts[:limit]
        
        # 转换为响应格式
        alert_responses = [
            AlertResponse(
                alert_id=alert.alert_id,
                name=alert.name,
                level=alert.level.value,
                status=alert.status.value,
                metric_name=alert.metric_name,
                current_value=alert.current_value,
                threshold_value=alert.threshold_value,
                timestamp=alert.timestamp.isoformat()
            )
            for alert in filtered_alerts
        ]
        
        return {
            "alerts": [alert.dict() for alert in alert_responses],
            "total": len(active_alerts),
            "filtered": len(filtered_alerts)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取告警列表失败: {str(e)}")


# 告警摘要
@monitoring_router.get("/alerts/summary")
async def alerts_summary():
    """
    告警摘要信息
    """
    try:
        summary = alert_manager.get_alert_summary()
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取告警摘要失败: {str(e)}")


# 确认告警
@monitoring_router.post("/alerts/{rule_id}/acknowledge")
async def acknowledge_alert(
    rule_id: str = Path(..., description="告警规则ID"),
    acknowledged_by: str = Query(..., description="确认人")
):
    """
    确认告警
    
    Args:
        rule_id: 告警规则ID
        acknowledged_by: 确认人
    """
    try:
        success = alert_manager.evaluator.acknowledge_alert(rule_id, acknowledged_by)
        
        if success:
            return {"message": f"告警 {rule_id} 已被 {acknowledged_by} 确认"}
        else:
            raise HTTPException(status_code=404, detail=f"未找到告警: {rule_id}")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"确认告警失败: {str(e)}")


# 静默告警
@monitoring_router.post("/alerts/{rule_id}/silence")
async def silence_alert(
    rule_id: str = Path(..., description="告警规则ID"),
    duration_minutes: int = Query(60, ge=1, le=1440, description="静默时长(分钟)")
):
    """
    静默告警
    
    Args:
        rule_id: 告警规则ID
        duration_minutes: 静默时长(分钟)
    """
    try:
        success = alert_manager.evaluator.silence_alert(rule_id, duration_minutes)
        
        if success:
            return {"message": f"告警 {rule_id} 已静默 {duration_minutes} 分钟"}
        else:
            raise HTTPException(status_code=404, detail=f"未找到告警: {rule_id}")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"静默告警失败: {str(e)}")


# DomesticGateway专用端点
@monitoring_router.get("/domestic-gateway/performance")
async def domestic_gateway_performance():
    """
    获取DomesticGateway性能指标
    """
    try:
        if not unified_monitor.domestic_gateway_monitor:
            raise HTTPException(status_code=404, detail="DomesticGatewayMonitor不可用")
        
        performance = unified_monitor.domestic_gateway_monitor.get_performance_summary()
        return {"performance": performance, "timestamp": datetime.now().isoformat()}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取DomesticGateway性能指标失败: {str(e)}")


@monitoring_router.get("/domestic-gateway/statistics")
async def domestic_gateway_statistics():
    """
    获取DomesticGateway统计信息
    """
    try:
        if not unified_monitor.domestic_gateway_monitor:
            raise HTTPException(status_code=404, detail="DomesticGatewayMonitor不可用")
        
        statistics = unified_monitor.domestic_gateway_monitor.get_statistics()
        return {"statistics": statistics, "timestamp": datetime.now().isoformat()}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取DomesticGateway统计信息失败: {str(e)}")


# 监控配置信息
@monitoring_router.get("/config")
async def monitoring_config():
    """
    获取监控系统配置信息
    """
    try:
        from config.backend.monitor_config import (
            MONITORED_SERVICES_DETAILED,
            ALERT_RULES_CONFIG,
            NOTIFICATION_CHANNELS_CONFIG
        )
        
        return {
            "services": {
                service_id: {
                    "name": config.get("name", service_id),
                    "port": config.get("port"),
                    "priority": config.get("priority"),
                    "type": config.get("type", "unknown")
                }
                for service_id, config in MONITORED_SERVICES_DETAILED.items()
            },
            "alert_rules": len(ALERT_RULES_CONFIG),
            "notification_channels": len(NOTIFICATION_CHANNELS_CONFIG),
            "components": {
                "prometheus": True,
                "grafana": True,
                "elasticsearch": True,
                "kibana": True,
                "domestic_gateway_monitor": unified_monitor.domestic_gateway_monitor is not None
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取监控配置失败: {str(e)}")


# 系统信息端点
@monitoring_router.get("/info")
async def system_info():
    """
    获取监控系统信息
    """
    return {
        "name": "RedFire监控系统",
        "version": "2.0.0",
        "description": "基于Prometheus+Grafana+ELK的统一监控平台",
        "features": [
            "系统监控 (CPU、内存、磁盘、网络)",
            "应用监控 (HTTP请求、响应时间、错误率)",
            "业务监控 (VnPy交易、网关状态、策略盈亏)",
            "健康检查 (服务状态、可用性监控)",
            "告警通知 (邮件、Webhook、短信、日志)",
            "日志分析 (ELK Stack结构化日志)",
            "专业交易监控 (DomesticGatewayMonitor)"
        ],
        "endpoints": {
            "健康检查": "/monitoring/health",
            "Prometheus指标": "/monitoring/metrics", 
            "监控摘要": "/monitoring/metrics/summary",
            "告警管理": "/monitoring/alerts",
            "系统状态": "/monitoring/status"
        },
        "external_services": {
            "grafana": "http://localhost:3000",
            "prometheus": "http://localhost:9090", 
            "kibana": "http://localhost:5601",
            "elasticsearch": "http://localhost:9200"
        },
        "timestamp": datetime.now().isoformat()
    }
