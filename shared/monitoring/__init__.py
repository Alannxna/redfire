"""
RedFire统一监控系统

基于现有85%完善基础构建的企业级监控解决方案：

核心组件：
- PrometheusExporter: 指标收集和导出
- HealthChecker: 服务健康检查
- AlertManager: 告警评估和通知
- UnifiedMonitor: 统一监控服务
- API端点: RESTful监控接口

技术栈：
- Prometheus + Grafana: 指标监控和可视化
- ELK Stack: 日志收集和分析
- Docker: 容器化部署
- FastAPI: 监控API服务

特色功能：
- 集成DomesticGatewayMonitor专业交易监控
- 基于monitor_config.py的647行企业级配置
- 支持系统、应用、业务三层监控
- 多通道告警通知 (邮件、Webhook、短信、日志)
- 一键Docker部署方案

使用示例：
```python
from shared.monitoring import unified_monitor, monitoring_router

# 启动统一监控
await unified_monitor.start_monitoring()

# 集成到FastAPI应用
app.include_router(monitoring_router)
```
"""

from .prometheus_exporter import prometheus_exporter, get_prometheus_metrics
from .health_check import health_checker, get_health_status, get_service_health
from .alert_system import alert_manager, Alert, AlertStatus, NotificationResult
from .unified_monitor import unified_monitor, get_monitoring_metrics, get_monitoring_status
from .api_endpoints import monitoring_router

__version__ = "2.0.0"
__author__ = "RedFire架构团队"

__all__ = [
    # 核心组件
    "prometheus_exporter",
    "health_checker", 
    "alert_manager",
    "unified_monitor",
    
    # API函数
    "get_prometheus_metrics",
    "get_health_status",
    "get_service_health", 
    "get_monitoring_metrics",
    "get_monitoring_status",
    
    # FastAPI路由
    "monitoring_router",
    
    # 数据类
    "Alert",
    "AlertStatus", 
    "NotificationResult",
    
    # 版本信息
    "__version__",
    "__author__"
]

# 模块初始化日志
import logging
logger = logging.getLogger(__name__)
logger.info(f"RedFire监控系统 v{__version__} 已加载")
logger.info("支持组件: Prometheus, Grafana, ELK, DomesticGateway, Docker")
logger.info("配置基础: monitor_config.py (647行企业级配置)")
