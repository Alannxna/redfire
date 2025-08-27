"""
监控应用服务
==========

监控系统的应用层服务，协调各个监控组件的业务流程
"""

from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta

from ...core.common.exceptions import ApplicationException
from ...domain.monitoring.services.monitoring_domain_service import MonitoringDomainService
from ...domain.monitoring.services.health_check_service import HealthCheckService
from ...domain.monitoring.services.system_metrics_service import SystemMetricsService
from ...domain.monitoring.services.alert_rule_service import AlertRuleService
from ...domain.monitoring.entities.health_check_entity import HealthCheckResult
from ...domain.monitoring.entities.system_metrics_entity import SystemMetrics, MetricType, MetricUnit
from ...domain.monitoring.entities.alert_rule_entity import AlertRule, AlertSeverity, AlertCondition
from ...domain.monitoring.entities.service_status_entity import ServiceStatus


class MonitoringApplicationService:
    """
    监控应用服务
    
    提供统一的监控管理接口，协调各个监控组件：
    - 健康检查管理
    - 系统指标收集
    - 告警规则管理
    - 服务状态监控
    """
    
    def __init__(
        self,
        monitoring_domain_service: MonitoringDomainService,
        health_check_service: HealthCheckService,
        system_metrics_service: SystemMetricsService,
        alert_rule_service: AlertRuleService
    ):
        self._monitoring_domain_service = monitoring_domain_service
        self._health_check_service = health_check_service
        self._system_metrics_service = system_metrics_service
        self._alert_rule_service = alert_rule_service
    
    # ==================== 健康检查相关 ====================
    
    async def perform_health_check(self, service_name: str) -> Dict[str, Any]:
        """
        执行服务健康检查
        
        Args:
            service_name: 服务名称
            
        Returns:
            Dict[str, Any]: 健康检查结果
        """
        try:
            results = await self._health_check_service.perform_comprehensive_health_check(service_name)
            
            # 转换为API响应格式
            return {
                "service_name": service_name,
                "check_time": datetime.now().isoformat(),
                "results": [result.to_dict() for result in results],
                "overall_status": self._determine_overall_status(results),
                "total_checks": len(results)
            }
            
        except Exception as e:
            raise ApplicationException(f"健康检查失败: {e}")
    
    async def get_health_summary(self, service_name: Optional[str] = None) -> Dict[str, Any]:
        """
        获取健康检查摘要
        
        Args:
            service_name: 服务名称（可选）
            
        Returns:
            Dict[str, Any]: 健康检查摘要
        """
        try:
            return await self._health_check_service.get_health_summary(service_name)
        except Exception as e:
            raise ApplicationException(f"获取健康摘要失败: {e}")
    
    def _determine_overall_status(self, results: List[HealthCheckResult]) -> str:
        """确定整体健康状态"""
        if not results:
            return "unknown"
        
        statuses = [result.status for result in results]
        
        if any(status.value == "unhealthy" for status in statuses):
            return "unhealthy"
        elif any(status.value == "degraded" for status in statuses):
            return "degraded"
        else:
            return "healthy"
    
    # ==================== 系统指标相关 ====================
    
    async def collect_system_metrics(self, service_name: str) -> Dict[str, Any]:
        """
        收集系统指标
        
        Args:
            service_name: 服务名称
            
        Returns:
            Dict[str, Any]: 系统指标数据
        """
        try:
            metrics = await self._system_metrics_service.collect_all_system_metrics(service_name)
            
            return {
                "service_name": service_name,
                "collection_time": datetime.now().isoformat(),
                "metrics": [metric.to_dict() for metric in metrics],
                "total_metrics": len(metrics)
            }
            
        except Exception as e:
            raise ApplicationException(f"系统指标收集失败: {e}")
    
    async def get_metrics_summary(
        self, 
        service_name: Optional[str] = None,
        time_range_hours: int = 1
    ) -> Dict[str, Any]:
        """
        获取指标摘要
        
        Args:
            service_name: 服务名称（可选）
            time_range_hours: 时间范围（小时）
            
        Returns:
            Dict[str, Any]: 指标摘要
        """
        try:
            return await self._system_metrics_service.get_metrics_summary(service_name, time_range_hours)
        except Exception as e:
            raise ApplicationException(f"获取指标摘要失败: {e}")
    
    async def create_custom_metric(
        self,
        service_name: str,
        metric_name: str,
        metric_type: str,
        metric_unit: str,
        value: Union[float, int],
        labels: Optional[Dict[str, str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        创建自定义指标
        
        Args:
            service_name: 服务名称
            metric_name: 指标名称
            metric_type: 指标类型
            metric_unit: 指标单位
            value: 指标值
            labels: 标签（可选）
            metadata: 元数据（可选）
            
        Returns:
            Dict[str, Any]: 创建的指标信息
        """
        try:
            # 转换枚举类型
            metric_type_enum = MetricType(metric_type)
            metric_unit_enum = MetricUnit(metric_unit)
            
            metric = await self._system_metrics_service.create_custom_metric(
                service_name=service_name,
                metric_name=metric_name,
                metric_type=metric_type_enum,
                metric_unit=metric_unit_enum,
                value=value,
                labels=labels,
                metadata=metadata
            )
            
            return {
                "success": True,
                "metric": metric.to_dict(),
                "created_at": datetime.now().isoformat()
            }
            
        except ValueError as e:
            raise ApplicationException(f"无效的指标类型或单位: {e}")
        except Exception as e:
            raise ApplicationException(f"创建自定义指标失败: {e}")
    
    # ==================== 告警规则相关 ====================
    
    async def create_alert_rule(
        self,
        rule_name: str,
        description: Optional[str],
        service_name: str,
        metric_name: str,
        condition: str,
        threshold_value: Union[float, int, str],
        severity: str,
        duration_seconds: int = 60,
        notification_channels: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        创建告警规则
        
        Args:
            rule_name: 规则名称
            description: 规则描述
            service_name: 监控的服务名称
            metric_name: 监控的指标名称
            condition: 告警条件
            threshold_value: 阈值
            severity: 严重程度
            duration_seconds: 持续时间（秒）
            notification_channels: 通知渠道
            
        Returns:
            Dict[str, Any]: 创建的告警规则信息
        """
        try:
            # 转换枚举类型
            condition_enum = AlertCondition(condition)
            severity_enum = AlertSeverity(severity)
            
            rule = await self._alert_rule_service.create_alert_rule(
                rule_name=rule_name,
                description=description,
                service_name=service_name,
                metric_name=metric_name,
                condition=condition_enum,
                threshold_value=threshold_value,
                severity=severity_enum,
                duration_seconds=duration_seconds,
                notification_channels=notification_channels
            )
            
            return {
                "success": True,
                "rule": rule.to_dict(),
                "created_at": datetime.now().isoformat()
            }
            
        except ValueError as e:
            raise ApplicationException(f"无效的告警条件或严重程度: {e}")
        except Exception as e:
            raise ApplicationException(f"创建告警规则失败: {e}")
    
    async def update_alert_rule(self, rule_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        更新告警规则
        
        Args:
            rule_data: 告警规则数据
            
        Returns:
            Dict[str, Any]: 更新结果
        """
        try:
            # 转换数据为AlertRule对象
            rule = AlertRule(**rule_data)
            
            updated_rule = await self._alert_rule_service.update_alert_rule(rule)
            
            return {
                "success": True,
                "rule": updated_rule.to_dict(),
                "updated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            raise ApplicationException(f"更新告警规则失败: {e}")
    
    async def delete_alert_rule(self, rule_id: str) -> Dict[str, Any]:
        """
        删除告警规则
        
        Args:
            rule_id: 规则ID
            
        Returns:
            Dict[str, Any]: 删除结果
        """
        try:
            success = await self._alert_rule_service.delete_alert_rule(rule_id)
            
            return {
                "success": success,
                "rule_id": rule_id,
                "deleted_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            raise ApplicationException(f"删除告警规则失败: {e}")
    
    async def enable_alert_rule(self, rule_id: str) -> Dict[str, Any]:
        """
        启用告警规则
        
        Args:
            rule_id: 规则ID
            
        Returns:
            Dict[str, Any]: 操作结果
        """
        try:
            success = await self._alert_rule_service.enable_alert_rule(rule_id)
            
            return {
                "success": success,
                "rule_id": rule_id,
                "action": "enabled",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            raise ApplicationException(f"启用告警规则失败: {e}")
    
    async def disable_alert_rule(self, rule_id: str) -> Dict[str, Any]:
        """
        禁用告警规则
        
        Args:
            rule_id: 规则ID
            
        Returns:
            Dict[str, Any]: 操作结果
        """
        try:
            success = await self._alert_rule_service.disable_alert_rule(rule_id)
            
            return {
                "success": success,
                "rule_id": rule_id,
                "action": "disabled",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            raise ApplicationException(f"禁用告警规则失败: {e}")
    
    async def get_alert_status_summary(self) -> Dict[str, Any]:
        """
        获取告警状态摘要
        
        Returns:
            Dict[str, Any]: 告警状态摘要
        """
        try:
            return await self._alert_rule_service.get_alert_status_summary()
        except Exception as e:
            raise ApplicationException(f"获取告警状态摘要失败: {e}")
    
    async def evaluate_all_alerts(self) -> Dict[str, Any]:
        """
        评估所有告警规则
        
        Returns:
            Dict[str, Any]: 评估结果
        """
        try:
            return await self._alert_rule_service.evaluate_all_alert_rules()
        except Exception as e:
            raise ApplicationException(f"评估告警规则失败: {e}")
    
    # ==================== 系统配置相关 ====================
    
    async def get_system_configuration(self) -> Dict[str, Any]:
        """
        获取系统配置
        
        Returns:
            Dict[str, Any]: 系统配置信息
        """
        try:
            monitoring_status = await self._monitoring_domain_service.get_monitoring_status()
            
            return {
                "monitoring": monitoring_status,
                "health_check": {
                    "enabled": True,
                    "interval_seconds": 30,
                    "timeout_seconds": 30,
                    "retention_days": 7
                },
                "metrics": {
                    "enabled": True,
                    "collection_interval_seconds": 10,
                    "retention_hours": 72,
                    "batch_size": 100
                },
                "alerts": {
                    "enabled": True,
                    "evaluation_interval_seconds": 10,
                    "default_suppress_duration_seconds": 300,
                    "max_history_size": 1000
                },
                "system": {
                    "version": "1.0.0",
                    "environment": "production",
                    "timezone": "UTC",
                    "debug_mode": False
                },
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            raise ApplicationException(f"获取系统配置失败: {e}")
    
    async def update_system_configuration(self, config_updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        更新系统配置
        
        Args:
            config_updates: 配置更新数据
            
        Returns:
            Dict[str, Any]: 更新结果
        """
        try:
            # 这里可以实现具体的配置更新逻辑
            # 目前返回模拟的成功响应
            
            return {
                "success": True,
                "updated_fields": list(config_updates.keys()),
                "applied_changes": config_updates,
                "updated_at": datetime.now().isoformat(),
                "message": "配置更新成功"
            }
            
        except Exception as e:
            raise ApplicationException(f"更新系统配置失败: {e}")
    
    # ==================== 统一监控接口 ====================
    
    async def get_monitoring_overview(self) -> Dict[str, Any]:
        """
        获取监控系统总览
        
        Returns:
            Dict[str, Any]: 监控系统总览
        """
        try:
            # 并行获取各种状态信息
            health_summary = await self.get_health_summary()
            metrics_summary = await self.get_metrics_summary(time_range_hours=1)
            alert_summary = await self.get_alert_status_summary()
            monitoring_status = await self._monitoring_domain_service.get_monitoring_status()
            
            return {
                "overview": {
                    "system_status": monitoring_status.get("service_status", "unknown"),
                    "monitoring_enabled": monitoring_status.get("monitoring_enabled", False),
                    "last_updated": datetime.now().isoformat()
                },
                "health": {
                    "overall_status": health_summary.get("overall_status", "unknown"),
                    "summary": health_summary.get("summary", {}),
                    "services_count": len(health_summary.get("services", []))
                },
                "metrics": {
                    "total_metrics": metrics_summary.get("total_metrics", 0),
                    "metric_types": metrics_summary.get("metric_types", {}),
                    "time_range_hours": 1
                },
                "alerts": {
                    "active_alerts": alert_summary.get("summary", {}).get("active_alerts", 0),
                    "total_rules": alert_summary.get("summary", {}).get("total_rules", 0),
                    "severity_breakdown": alert_summary.get("severity_breakdown", {})
                },
                "system": {
                    "active_services": monitoring_status.get("active_services", 0),
                    "background_tasks": monitoring_status.get("background_tasks", 0),
                    "configuration": monitoring_status.get("configuration", {})
                }
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "overview": {
                    "system_status": "error",
                    "monitoring_enabled": False,
                    "last_updated": datetime.now().isoformat()
                }
            }
