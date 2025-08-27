"""
监控领域服务
==========

监控领域的核心业务逻辑实现，负责协调各个监控组件
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from ....core.base import BaseDomainService, DomainServiceConfig
from ....core.common.enums.service_status import ServiceStatus
from ....core.common.exceptions import DomainException
from ..entities.health_check_entity import HealthCheckResult, HealthStatus
from ..entities.system_metrics_entity import SystemMetrics, MetricType
from ..entities.alert_rule_entity import AlertRule, AlertSeverity
from ..entities.service_status_entity import ServiceStatus as ServiceStatusEntity, ServiceHealth
from ..repositories.health_check_repository import IHealthCheckRepository
from ..repositories.system_metrics_repository import ISystemMetricsRepository
from ..repositories.alert_rule_repository import IAlertRuleRepository
from ..repositories.service_status_repository import IServiceStatusRepository


class MonitoringDomainServiceConfig(DomainServiceConfig):
    """监控领域服务配置"""
    
    def __init__(self):
        super().__init__(
            service_name="monitoring_domain_service",
            domain_name="monitoring",
            description="监控领域服务 - 负责系统监控、健康检查、告警管理等核心业务逻辑",
            version="1.0.0"
        )


class MonitoringDomainService(BaseDomainService):
    """
    监控领域服务
    
    负责监控相关的核心业务逻辑，包含：
    - 健康检查管理
    - 系统指标监控
    - 告警规则处理
    - 服务状态管理
    """
    
    def __init__(
        self, 
        config: MonitoringDomainServiceConfig,
        health_check_repository: IHealthCheckRepository,
        metrics_repository: ISystemMetricsRepository,
        alert_rule_repository: IAlertRuleRepository,
        service_status_repository: IServiceStatusRepository
    ):
        super().__init__(config)
        
        # 仓储依赖
        self._health_check_repo = health_check_repository
        self._metrics_repo = metrics_repository
        self._alert_rule_repo = alert_rule_repository
        self._service_status_repo = service_status_repository
        
        # 领域状态
        self._domain_state = {
            "monitoring_enabled": True,
            "health_checks": {},
            "active_alerts": {},
            "service_registry": {},
            "metrics_collectors": {},
        }
        
        # 监控配置
        self._health_check_interval = 30  # 健康检查间隔（秒）
        self._metrics_collection_interval = 10  # 指标收集间隔（秒）
        self._alert_evaluation_interval = 5  # 告警评估间隔（秒）
        self._data_retention_days = 30  # 数据保留天数
        
        # 后台任务
        self._background_tasks = []
        self._monitoring_enabled = True
        
        # 统计信息
        self._monitoring_statistics = {
            "total_health_checks": 0,
            "failed_health_checks": 0,
            "total_metrics_collected": 0,
            "active_alert_rules": 0,
            "triggered_alerts": 0,
            "monitored_services": 0,
        }
    
    async def _start_impl(self) -> bool:
        """启动监控领域服务"""
        try:
            # 初始化监控组件
            await self._initialize_monitoring_components()
            
            # 启动后台任务
            await self._start_background_tasks()
            
            self.logger.info(f"{self.service_id} 启动成功")
            return True
            
        except Exception as e:
            self.logger.error(f"{self.service_id} 启动失败: {e}")
            return False
    
    async def _stop_impl(self) -> bool:
        """停止监控领域服务"""
        try:
            # 停止后台任务
            await self._stop_background_tasks()
            
            # 清理监控资源
            await self._cleanup_monitoring_resources()
            
            self.logger.info(f"{self.service_id} 停止成功")
            return True
            
        except Exception as e:
            self.logger.error(f"{self.service_id} 停止失败: {e}")
            return False
    
    async def _initialize_monitoring_components(self):
        """初始化监控组件"""
        self.logger.info("初始化监控组件")
        
        # 加载活跃的告警规则
        active_rules = await self._alert_rule_repo.get_active_alert_rules()
        self._domain_state["active_alerts"] = {rule.rule_id: rule for rule in active_rules}
        
        # 初始化服务注册表
        services = await self._service_status_repo.get_all_service_statuses()
        self._domain_state["service_registry"] = {svc.service_id: svc for svc in services}
        
        self.logger.info(f"加载了 {len(active_rules)} 个告警规则，{len(services)} 个服务")
    
    async def _start_background_tasks(self):
        """启动后台任务"""
        self.logger.info("启动监控后台任务")
        
        # 健康检查任务
        health_check_task = asyncio.create_task(self._health_check_loop())
        self._background_tasks.append(health_check_task)
        
        # 指标收集任务
        metrics_task = asyncio.create_task(self._metrics_collection_loop())
        self._background_tasks.append(metrics_task)
        
        # 告警评估任务
        alert_task = asyncio.create_task(self._alert_evaluation_loop())
        self._background_tasks.append(alert_task)
        
        # 数据清理任务
        cleanup_task = asyncio.create_task(self._data_cleanup_loop())
        self._background_tasks.append(cleanup_task)
    
    async def _stop_background_tasks(self):
        """停止后台任务"""
        self.logger.info("停止监控后台任务")
        
        self._monitoring_enabled = False
        
        for task in self._background_tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        self._background_tasks.clear()
    
    async def _cleanup_monitoring_resources(self):
        """清理监控资源"""
        self.logger.info("清理监控资源")
        
        # 清理状态
        self._domain_state["monitoring_enabled"] = False
        self._domain_state["health_checks"].clear()
        self._domain_state["active_alerts"].clear()
        self._domain_state["service_registry"].clear()
        self._domain_state["metrics_collectors"].clear()
    
    async def _health_check_loop(self):
        """健康检查循环"""
        while self._monitoring_enabled:
            try:
                await self._perform_health_checks()
                await asyncio.sleep(self._health_check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"健康检查循环错误: {e}")
                await asyncio.sleep(5)
    
    async def _metrics_collection_loop(self):
        """指标收集循环"""
        while self._monitoring_enabled:
            try:
                await self._collect_system_metrics()
                await asyncio.sleep(self._metrics_collection_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"指标收集循环错误: {e}")
                await asyncio.sleep(5)
    
    async def _alert_evaluation_loop(self):
        """告警评估循环"""
        while self._monitoring_enabled:
            try:
                await self._evaluate_alert_rules()
                await asyncio.sleep(self._alert_evaluation_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"告警评估循环错误: {e}")
                await asyncio.sleep(5)
    
    async def _data_cleanup_loop(self):
        """数据清理循环"""
        while self._monitoring_enabled:
            try:
                await self._cleanup_old_data()
                # 每小时执行一次数据清理
                await asyncio.sleep(3600)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"数据清理循环错误: {e}")
                await asyncio.sleep(300)
    
    async def _perform_health_checks(self):
        """执行健康检查"""
        # 这里会被具体的健康检查实现替换
        pass
    
    async def _collect_system_metrics(self):
        """收集系统指标"""
        # 这里会被具体的指标收集实现替换
        pass
    
    async def _evaluate_alert_rules(self):
        """评估告警规则"""
        # 这里会被具体的告警评估实现替换
        pass
    
    async def _cleanup_old_data(self):
        """清理过期数据"""
        cutoff_time = datetime.now() - timedelta(days=self._data_retention_days)
        
        try:
            # 清理过期的健康检查记录
            deleted_health_checks = await self._health_check_repo.delete_old_health_check_results(cutoff_time)
            
            # 清理过期的指标数据
            deleted_metrics = await self._metrics_repo.delete_old_metrics(cutoff_time)
            
            self.logger.info(f"清理了 {deleted_health_checks} 条健康检查记录，{deleted_metrics} 条指标记录")
            
        except Exception as e:
            self.logger.error(f"数据清理失败: {e}")
    
    async def get_monitoring_status(self) -> Dict[str, Any]:
        """获取监控状态"""
        return {
            "monitoring_enabled": self._monitoring_enabled,
            "service_status": self.get_status(),
            "statistics": self._monitoring_statistics.copy(),
            "configuration": {
                "health_check_interval": self._health_check_interval,
                "metrics_collection_interval": self._metrics_collection_interval,
                "alert_evaluation_interval": self._alert_evaluation_interval,
                "data_retention_days": self._data_retention_days,
            },
            "active_services": len(self._domain_state["service_registry"]),
            "active_alert_rules": len(self._domain_state["active_alerts"]),
            "background_tasks": len(self._background_tasks),
        }
    
    async def _process_domain_event(self, event: Dict[str, Any]):
        """处理领域事件"""
        event_type = event.get("event_type")
        
        if event_type == "health_check_completed":
            await self._handle_health_check_completed(event)
        elif event_type == "metric_collected":
            await self._handle_metric_collected(event)
        elif event_type == "alert_triggered":
            await self._handle_alert_triggered(event)
        elif event_type == "service_health_changed":
            await self._handle_service_health_changed(event)
    
    async def _handle_health_check_completed(self, event: Dict[str, Any]):
        """处理健康检查完成事件"""
        self._monitoring_statistics["total_health_checks"] += 1
        
        if event.get("status") != HealthStatus.HEALTHY:
            self._monitoring_statistics["failed_health_checks"] += 1
    
    async def _handle_metric_collected(self, event: Dict[str, Any]):
        """处理指标收集事件"""
        self._monitoring_statistics["total_metrics_collected"] += 1
    
    async def _handle_alert_triggered(self, event: Dict[str, Any]):
        """处理告警触发事件"""
        self._monitoring_statistics["triggered_alerts"] += 1
    
    async def _handle_service_health_changed(self, event: Dict[str, Any]):
        """处理服务健康状态变更事件"""
        service_id = event.get("service_id")
        new_health = event.get("new_health")
        
        if service_id in self._domain_state["service_registry"]:
            service = self._domain_state["service_registry"][service_id]
            service.health_status = new_health
            
            self.logger.info(f"服务 {service_id} 健康状态变更为 {new_health}")
