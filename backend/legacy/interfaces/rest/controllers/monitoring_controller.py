"""
监控API控制器
==========

提供监控系统的REST API接口
"""

from typing import Dict, Any, List, Optional, Union
from fastapi import APIRouter, HTTPException, Depends, Query, Path, Body
from pydantic import BaseModel, Field
from datetime import datetime

from ....core.common.exceptions import ApplicationException
from ....application.monitoring.monitoring_application_service import MonitoringApplicationService
from ..middleware.auth_middleware import get_current_user
from ..models.response_models import ApiResponse


# ==================== 请求模型 ====================

class HealthCheckRequest(BaseModel):
    """健康检查请求"""
    service_name: str = Field(..., description="服务名称")


class CustomMetricRequest(BaseModel):
    """自定义指标请求"""
    service_name: str = Field(..., description="服务名称")
    metric_name: str = Field(..., description="指标名称")
    metric_type: str = Field(..., description="指标类型", regex="^(counter|gauge|histogram|summary|rate)$")
    metric_unit: str = Field(..., description="指标单位")
    value: Union[float, int] = Field(..., description="指标值")
    labels: Optional[Dict[str, str]] = Field(None, description="标签")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")


class AlertRuleRequest(BaseModel):
    """告警规则请求"""
    rule_name: str = Field(..., description="规则名称")
    description: Optional[str] = Field(None, description="规则描述")
    service_name: str = Field(..., description="监控的服务名称")
    metric_name: str = Field(..., description="监控的指标名称")
    condition: str = Field(..., description="告警条件", regex="^(gt|gte|lt|lte|eq|ne|contains|not_contains)$")
    threshold_value: Union[float, int, str] = Field(..., description="阈值")
    severity: str = Field(..., description="严重程度", regex="^(critical|high|medium|low|info)$")
    duration_seconds: int = Field(60, description="持续时间（秒）", ge=0)
    notification_channels: Optional[List[str]] = Field(None, description="通知渠道")


class AlertRuleUpdateRequest(BaseModel):
    """告警规则更新请求"""
    rule_id: str = Field(..., description="规则ID")
    rule_name: Optional[str] = Field(None, description="规则名称")
    description: Optional[str] = Field(None, description="规则描述")
    condition: Optional[str] = Field(None, description="告警条件")
    threshold_value: Optional[Union[float, int, str]] = Field(None, description="阈值")
    severity: Optional[str] = Field(None, description="严重程度")
    duration_seconds: Optional[int] = Field(None, description="持续时间（秒）", ge=0)
    notification_channels: Optional[List[str]] = Field(None, description="通知渠道")


class SystemConfigUpdateRequest(BaseModel):
    """系统配置更新请求"""
    monitoring: Optional[Dict[str, Any]] = Field(None, description="监控配置")
    health_check: Optional[Dict[str, Any]] = Field(None, description="健康检查配置")
    metrics: Optional[Dict[str, Any]] = Field(None, description="指标配置")
    alerts: Optional[Dict[str, Any]] = Field(None, description="告警配置")
    system: Optional[Dict[str, Any]] = Field(None, description="系统配置")


# ==================== 控制器类 ====================

class MonitoringController:
    """
    监控控制器
    
    提供监控系统的完整REST API接口，包括：
    - 健康检查管理
    - 系统指标监控
    - 告警规则管理
    - 系统配置管理
    """
    
    def __init__(self, monitoring_service: MonitoringApplicationService):
        self.monitoring_service = monitoring_service
        self.router = APIRouter(prefix="/api/monitoring", tags=["监控系统"])
        self._setup_routes()
    
    def _setup_routes(self):
        """设置路由"""
        
        # ==================== 健康检查接口 ====================
        
        @self.router.post("/health-check", response_model=ApiResponse)
        async def perform_health_check(
            request: HealthCheckRequest,
            current_user=Depends(get_current_user)
        ):
            """执行健康检查"""
            try:
                result = await self.monitoring_service.perform_health_check(request.service_name)
                return ApiResponse(success=True, data=result, message="健康检查完成")
            except ApplicationException as e:
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"健康检查失败: {e}")
        
        @self.router.get("/health-summary", response_model=ApiResponse)
        async def get_health_summary(
            service_name: Optional[str] = Query(None, description="服务名称"),
            current_user=Depends(get_current_user)
        ):
            """获取健康检查摘要"""
            try:
                result = await self.monitoring_service.get_health_summary(service_name)
                return ApiResponse(success=True, data=result, message="获取健康摘要成功")
            except ApplicationException as e:
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"获取健康摘要失败: {e}")
        
        # ==================== 系统指标接口 ====================
        
        @self.router.post("/metrics/collect", response_model=ApiResponse)
        async def collect_system_metrics(
            service_name: str = Body(..., embed=True),
            current_user=Depends(get_current_user)
        ):
            """收集系统指标"""
            try:
                result = await self.monitoring_service.collect_system_metrics(service_name)
                return ApiResponse(success=True, data=result, message="系统指标收集完成")
            except ApplicationException as e:
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"系统指标收集失败: {e}")
        
        @self.router.get("/metrics/summary", response_model=ApiResponse)
        async def get_metrics_summary(
            service_name: Optional[str] = Query(None, description="服务名称"),
            time_range_hours: int = Query(1, description="时间范围（小时）", ge=1, le=168),
            current_user=Depends(get_current_user)
        ):
            """获取指标摘要"""
            try:
                result = await self.monitoring_service.get_metrics_summary(service_name, time_range_hours)
                return ApiResponse(success=True, data=result, message="获取指标摘要成功")
            except ApplicationException as e:
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"获取指标摘要失败: {e}")
        
        @self.router.post("/metrics/custom", response_model=ApiResponse)
        async def create_custom_metric(
            request: CustomMetricRequest,
            current_user=Depends(get_current_user)
        ):
            """创建自定义指标"""
            try:
                result = await self.monitoring_service.create_custom_metric(
                    service_name=request.service_name,
                    metric_name=request.metric_name,
                    metric_type=request.metric_type,
                    metric_unit=request.metric_unit,
                    value=request.value,
                    labels=request.labels,
                    metadata=request.metadata
                )
                return ApiResponse(success=True, data=result, message="自定义指标创建成功")
            except ApplicationException as e:
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"自定义指标创建失败: {e}")
        
        # ==================== 告警规则接口 ====================
        
        @self.router.post("/alerts/rules", response_model=ApiResponse)
        async def create_alert_rule(
            request: AlertRuleRequest,
            current_user=Depends(get_current_user)
        ):
            """创建告警规则"""
            try:
                result = await self.monitoring_service.create_alert_rule(
                    rule_name=request.rule_name,
                    description=request.description,
                    service_name=request.service_name,
                    metric_name=request.metric_name,
                    condition=request.condition,
                    threshold_value=request.threshold_value,
                    severity=request.severity,
                    duration_seconds=request.duration_seconds,
                    notification_channels=request.notification_channels
                )
                return ApiResponse(success=True, data=result, message="告警规则创建成功")
            except ApplicationException as e:
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"告警规则创建失败: {e}")
        
        @self.router.put("/alerts/rules", response_model=ApiResponse)
        async def update_alert_rule(
            request: AlertRuleUpdateRequest,
            current_user=Depends(get_current_user)
        ):
            """更新告警规则"""
            try:
                # 过滤非空字段
                update_data = {k: v for k, v in request.dict().items() if v is not None}
                
                result = await self.monitoring_service.update_alert_rule(update_data)
                return ApiResponse(success=True, data=result, message="告警规则更新成功")
            except ApplicationException as e:
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"告警规则更新失败: {e}")
        
        @self.router.delete("/alerts/rules/{rule_id}", response_model=ApiResponse)
        async def delete_alert_rule(
            rule_id: str = Path(..., description="规则ID"),
            current_user=Depends(get_current_user)
        ):
            """删除告警规则"""
            try:
                result = await self.monitoring_service.delete_alert_rule(rule_id)
                return ApiResponse(success=True, data=result, message="告警规则删除成功")
            except ApplicationException as e:
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"告警规则删除失败: {e}")
        
        @self.router.post("/alerts/rules/{rule_id}/enable", response_model=ApiResponse)
        async def enable_alert_rule(
            rule_id: str = Path(..., description="规则ID"),
            current_user=Depends(get_current_user)
        ):
            """启用告警规则"""
            try:
                result = await self.monitoring_service.enable_alert_rule(rule_id)
                return ApiResponse(success=True, data=result, message="告警规则启用成功")
            except ApplicationException as e:
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"告警规则启用失败: {e}")
        
        @self.router.post("/alerts/rules/{rule_id}/disable", response_model=ApiResponse)
        async def disable_alert_rule(
            rule_id: str = Path(..., description="规则ID"),
            current_user=Depends(get_current_user)
        ):
            """禁用告警规则"""
            try:
                result = await self.monitoring_service.disable_alert_rule(rule_id)
                return ApiResponse(success=True, data=result, message="告警规则禁用成功")
            except ApplicationException as e:
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"告警规则禁用失败: {e}")
        
        @self.router.get("/alerts/status", response_model=ApiResponse)
        async def get_alert_status_summary(
            current_user=Depends(get_current_user)
        ):
            """获取告警状态摘要"""
            try:
                result = await self.monitoring_service.get_alert_status_summary()
                return ApiResponse(success=True, data=result, message="获取告警状态摘要成功")
            except ApplicationException as e:
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"获取告警状态摘要失败: {e}")
        
        @self.router.post("/alerts/evaluate", response_model=ApiResponse)
        async def evaluate_all_alerts(
            current_user=Depends(get_current_user)
        ):
            """评估所有告警规则"""
            try:
                result = await self.monitoring_service.evaluate_all_alerts()
                return ApiResponse(success=True, data=result, message="告警规则评估完成")
            except ApplicationException as e:
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"告警规则评估失败: {e}")
        
        # ==================== 系统配置接口 ====================
        
        @self.router.get("/config", response_model=ApiResponse)
        async def get_system_configuration(
            current_user=Depends(get_current_user)
        ):
            """获取系统配置"""
            try:
                result = await self.monitoring_service.get_system_configuration()
                return ApiResponse(success=True, data=result, message="获取系统配置成功")
            except ApplicationException as e:
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"获取系统配置失败: {e}")
        
        @self.router.put("/config", response_model=ApiResponse)
        async def update_system_configuration(
            request: SystemConfigUpdateRequest,
            current_user=Depends(get_current_user)
        ):
            """更新系统配置"""
            try:
                # 过滤非空字段
                config_updates = {k: v for k, v in request.dict().items() if v is not None}
                
                result = await self.monitoring_service.update_system_configuration(config_updates)
                return ApiResponse(success=True, data=result, message="系统配置更新成功")
            except ApplicationException as e:
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"系统配置更新失败: {e}")
        
        # ==================== 监控总览接口 ====================
        
        @self.router.get("/overview", response_model=ApiResponse)
        async def get_monitoring_overview(
            current_user=Depends(get_current_user)
        ):
            """获取监控系统总览"""
            try:
                result = await self.monitoring_service.get_monitoring_overview()
                return ApiResponse(success=True, data=result, message="获取监控总览成功")
            except ApplicationException as e:
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"获取监控总览失败: {e}")


# ==================== 路由函数 ====================

def create_monitoring_router(monitoring_service: MonitoringApplicationService) -> APIRouter:
    """
    创建监控路由
    
    Args:
        monitoring_service: 监控应用服务
        
    Returns:
        APIRouter: 监控路由器
    """
    controller = MonitoringController(monitoring_service)
    return controller.router
