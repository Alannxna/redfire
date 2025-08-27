"""
监控领域仓储接口
==============

包含监控系统的仓储接口：
- IHealthCheckRepository: 健康检查仓储接口
- ISystemMetricsRepository: 系统指标仓储接口
- IAlertRuleRepository: 告警规则仓储接口
- IServiceStatusRepository: 服务状态仓储接口
"""

from .health_check_repository import IHealthCheckRepository
from .system_metrics_repository import ISystemMetricsRepository
from .alert_rule_repository import IAlertRuleRepository
from .service_status_repository import IServiceStatusRepository

__all__ = [
    "IHealthCheckRepository",
    "ISystemMetricsRepository", 
    "IAlertRuleRepository",
    "IServiceStatusRepository"
]
