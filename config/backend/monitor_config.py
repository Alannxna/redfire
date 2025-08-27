"""
监控服务详细配置
================

包含监控指标、告警规则、通知配置等详细设置
"""

from typing import Dict, List, Any
from dataclasses import dataclass, field
from enum import Enum


class MonitorLevel(Enum):
    """监控级别"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class MetricType(Enum):
    """监控指标类型"""
    SYSTEM = "system"        # 系统指标
    APPLICATION = "application"  # 应用指标
    BUSINESS = "business"    # 业务指标
    NETWORK = "network"      # 网络指标
    DATABASE = "database"    # 数据库指标


@dataclass
class MetricConfig:
    """监控指标配置"""
    name: str
    description: str
    metric_type: MetricType
    unit: str
    collection_interval: int  # 秒
    retention_hours: int = 24
    thresholds: Dict[str, float] = field(default_factory=dict)
    is_enabled: bool = True


@dataclass
class AlertRuleConfig:
    """告警规则配置"""
    rule_id: str
    name: str
    description: str
    metric_name: str
    condition: str  # 例如: "value > 80"
    level: MonitorLevel
    notification_channels: List[str]
    cooldown_seconds: int = 300  # 冷却期
    repeat_interval_hours: int = 1  # 重复通知间隔
    is_enabled: bool = True


@dataclass
class NotificationChannelConfig:
    """通知渠道配置"""
    channel_id: str
    name: str
    channel_type: str  # email, sms, webhook, slack, wechat
    config: Dict[str, Any]
    is_enabled: bool = True


# ====================== 系统监控指标配置 ======================

SYSTEM_METRICS_CONFIG = {
    "cpu_usage": MetricConfig(
        name="cpu_usage",
        description="CPU使用率",
        metric_type=MetricType.SYSTEM,
        unit="percent",
        collection_interval=30,
        retention_hours=24,
        thresholds={
            "warning": 70.0,
            "error": 85.0,
            "critical": 95.0
        }
    ),
    
    "memory_usage": MetricConfig(
        name="memory_usage",
        description="内存使用率",
        metric_type=MetricType.SYSTEM,
        unit="percent",
        collection_interval=30,
        retention_hours=24,
        thresholds={
            "warning": 75.0,
            "error": 90.0,
            "critical": 98.0
        }
    ),
    
    "disk_usage": MetricConfig(
        name="disk_usage",
        description="磁盘使用率",
        metric_type=MetricType.SYSTEM,
        unit="percent",
        collection_interval=60,
        retention_hours=24,
        thresholds={
            "warning": 80.0,
            "error": 90.0,
            "critical": 95.0
        }
    ),
    
    "network_io": MetricConfig(
        name="network_io",
        description="网络IO流量",
        metric_type=MetricType.NETWORK,
        unit="bytes/sec",
        collection_interval=30,
        retention_hours=12,
        thresholds={
            "warning": 100 * 1024 * 1024,  # 100MB/s
            "error": 500 * 1024 * 1024,    # 500MB/s
            "critical": 1000 * 1024 * 1024  # 1GB/s
        }
    ),
    
    "process_count": MetricConfig(
        name="process_count",
        description="系统进程数量",
        metric_type=MetricType.SYSTEM,
        unit="count",
        collection_interval=60,
        retention_hours=6,
        thresholds={
            "warning": 300,
            "error": 500,
            "critical": 800
        }
    ),
    
    "load_average": MetricConfig(
        name="load_average",
        description="系统负载平均值",
        metric_type=MetricType.SYSTEM,
        unit="ratio",
        collection_interval=30,
        retention_hours=12,
        thresholds={
            "warning": 2.0,
            "error": 4.0,
            "critical": 8.0
        }
    ),
    
    "tcp_connections": MetricConfig(
        name="tcp_connections",
        description="TCP连接数",
        metric_type=MetricType.NETWORK,
        unit="count",
        collection_interval=30,
        retention_hours=6,
        thresholds={
            "warning": 1000,
            "error": 2000,
            "critical": 5000
        }
    )
}


# ====================== 应用监控指标配置 ======================

APPLICATION_METRICS_CONFIG = {
    "request_rate": MetricConfig(
        name="request_rate",
        description="API请求速率",
        metric_type=MetricType.APPLICATION,
        unit="requests/min",
        collection_interval=30,
        retention_hours=12,
        thresholds={
            "warning": 1000,
            "error": 5000,
            "critical": 10000
        }
    ),
    
    "response_time": MetricConfig(
        name="response_time",
        description="平均响应时间",
        metric_type=MetricType.APPLICATION,
        unit="milliseconds",
        collection_interval=30,
        retention_hours=12,
        thresholds={
            "warning": 500,
            "error": 1000,
            "critical": 2000
        }
    ),
    
    "error_rate": MetricConfig(
        name="error_rate",
        description="错误率",
        metric_type=MetricType.APPLICATION,
        unit="percent",
        collection_interval=30,
        retention_hours=24,
        thresholds={
            "warning": 1.0,
            "error": 5.0,
            "critical": 10.0
        }
    ),
    
    "active_users": MetricConfig(
        name="active_users",
        description="活跃用户数",
        metric_type=MetricType.BUSINESS,
        unit="count",
        collection_interval=60,
        retention_hours=24,
        thresholds={
            "warning": 100,
            "error": 500,
            "critical": 1000
        }
    ),
    
    "thread_pool_usage": MetricConfig(
        name="thread_pool_usage",
        description="线程池使用率",
        metric_type=MetricType.APPLICATION,
        unit="percent",
        collection_interval=30,
        retention_hours=6,
        thresholds={
            "warning": 70.0,
            "error": 85.0,
            "critical": 95.0
        }
    )
}


# ====================== 告警规则配置 ======================

ALERT_RULES_CONFIG = [
    AlertRuleConfig(
        rule_id="cpu_high",
        name="CPU使用率过高",
        description="系统CPU使用率超过阈值时触发告警",
        metric_name="cpu_usage",
        condition="value > 85",
        level=MonitorLevel.ERROR,
        notification_channels=["email", "webhook"],
        cooldown_seconds=300,
        repeat_interval_hours=1
    ),
    
    AlertRuleConfig(
        rule_id="memory_critical",
        name="内存严重不足",
        description="系统内存使用率达到危险水平",
        metric_name="memory_usage",
        condition="value > 95",
        level=MonitorLevel.CRITICAL,
        notification_channels=["email", "sms", "webhook"],
        cooldown_seconds=60,
        repeat_interval_hours=0.5
    ),
    
    AlertRuleConfig(
        rule_id="disk_full",
        name="磁盘空间不足",
        description="系统磁盘使用率过高",
        metric_name="disk_usage",
        condition="value > 90",
        level=MonitorLevel.ERROR,
        notification_channels=["email", "webhook"],
        cooldown_seconds=600,
        repeat_interval_hours=2
    ),
    
    AlertRuleConfig(
        rule_id="service_down",
        name="服务不可用",
        description="关键服务停止响应",
        metric_name="service_health",
        condition="healthy == false",
        level=MonitorLevel.CRITICAL,
        notification_channels=["email", "sms", "webhook"],
        cooldown_seconds=120,
        repeat_interval_hours=0.5
    ),
    
    AlertRuleConfig(
        rule_id="high_error_rate",
        name="高错误率告警",
        description="应用错误率异常升高",
        metric_name="error_rate",
        condition="value > 5",
        level=MonitorLevel.WARNING,
        notification_channels=["email", "webhook"],
        cooldown_seconds=300,
        repeat_interval_hours=1
    ),
    
    AlertRuleConfig(
        rule_id="slow_response",
        name="响应时间过慢",
        description="API平均响应时间超过阈值",
        metric_name="response_time",
        condition="value > 1000",
        level=MonitorLevel.WARNING,
        notification_channels=["email"],
        cooldown_seconds=300,
        repeat_interval_hours=1
    ),
    
    AlertRuleConfig(
        rule_id="high_load",
        name="系统负载过高",
        description="系统负载平均值超过正常范围",
        metric_name="load_average",
        condition="value > 4.0",
        level=MonitorLevel.ERROR,
        notification_channels=["email", "webhook"],
        cooldown_seconds=300,
        repeat_interval_hours=1
    ),
    
    AlertRuleConfig(
        rule_id="connection_limit",
        name="连接数告警",
        description="TCP连接数接近系统限制",
        metric_name="tcp_connections",
        condition="value > 2000",
        level=MonitorLevel.WARNING,
        notification_channels=["email"],
        cooldown_seconds=600,
        repeat_interval_hours=2
    )
]


# ====================== 通知渠道配置 ======================

NOTIFICATION_CHANNELS_CONFIG = {
    "email": NotificationChannelConfig(
        channel_id="email",
        name="邮件通知",
        channel_type="email",
        config={
            "smtp_server": "smtp.163.com",
            "smtp_port": 587,
            "use_tls": True,
            "username": "vnpy_monitor@163.com",
            "password": "your_email_password",
            "from_email": "vnpy_monitor@163.com",
            "to_emails": ["admin@company.com", "ops@company.com"],
            "template": {
                "subject": "VnPy监控告警: {alert_title}",
                "body": """
尊敬的管理员：

VnPy交易系统监控告警详情如下：

告警标题: {alert_title}
告警级别: {alert_level}
触发时间: {alert_time}
服务名称: {service_name}
指标名称: {metric_name}
当前值: {current_value}
阈值: {threshold}
告警描述: {description}

请及时处理相关问题。

--
VnPy Web监控系统
                """
            }
        }
    ),
    
    "webhook": NotificationChannelConfig(
        channel_id="webhook",
        name="Webhook通知",
        channel_type="webhook",
        config={
            "urls": [
                "https://hooks.slack.com/services/YOUR/WEBHOOK/URL",
                "https://your-company.com/api/alerts"
            ],
            "method": "POST",
            "headers": {
                "Content-Type": "application/json",
                "Authorization": "Bearer your_token"
            },
            "timeout_seconds": 10,
            "retry_count": 3,
            "payload_template": {
                "alert_id": "{alert_id}",
                "title": "{alert_title}",
                "level": "{alert_level}",
                "time": "{alert_time}",
                "service": "{service_name}",
                "metric": "{metric_name}",
                "value": "{current_value}",
                "threshold": "{threshold}",
                "description": "{description}",
                "source": "vnpy_web_monitor"
            }
        }
    ),
    
    "sms": NotificationChannelConfig(
        channel_id="sms",
        name="短信通知",
        channel_type="sms",
        config={
            "provider": "aliyun",  # 阿里云短信服务
            "access_key": "your_access_key",
            "access_secret": "your_access_secret",
            "region": "cn-hangzhou",
            "sign_name": "VnPy监控",
            "template_code": "SMS_123456789",
            "phone_numbers": ["+86 138 0013 8000", "+86 138 0013 8001"],
            "template": "VnPy告警:{alert_title},级别:{alert_level},时间:{alert_time},请及时处理"
        }
    ),
    
    "log": NotificationChannelConfig(
        channel_id="log",
        name="日志记录",
        channel_type="log",
        config={
            "log_level": "WARNING",
            "log_file": "logs/monitor_alerts.log",
            "max_file_size": "100MB",
            "backup_count": 5,
            "format": "[{timestamp}] {level} {service_name}.{metric_name}: {message}"
        },
        is_enabled=True
    )
}


# ====================== 服务监控配置 ======================

MONITORED_SERVICES_DETAILED = {
    "vnpy_core": {
        "name": "🔥 VnPy核心服务",
        "port": 8006,
        "type": "core",
        "priority": "critical",
        "health_check": {
            "endpoint": "/health",
            "timeout": 5,
            "interval": 30,
            "retry_count": 3
        },
        "metrics": ["request_rate", "response_time", "error_rate", "active_users"],
        "description": "VnPy交易引擎核心服务，负责策略管理和交易执行"
    },
    
    "user_trading": {
        "name": "👤 用户交易服务",
        "port": 8001,
        "type": "auxiliary",
        "priority": "high",
        "health_check": {
            "endpoint": "/health",
            "timeout": 5,
            "interval": 60,
            "retry_count": 2
        },
        "metrics": ["request_rate", "response_time", "error_rate"],
        "description": "用户认证、账户管理、订单交易处理"
    },
    
    "strategy_data": {
        "name": "📊 策略数据服务",
        "port": 8002,
        "type": "auxiliary", 
        "priority": "high",
        "health_check": {
            "endpoint": "/health",
            "timeout": 5,
            "interval": 60,
            "retry_count": 2
        },
        "metrics": ["request_rate", "response_time"],
        "description": "策略管理和历史数据服务"
    },
    
    "gateway": {
        "name": "🌐 网关适配服务",
        "port": 8004,
        "type": "auxiliary",
        "priority": "medium",
        "health_check": {
            "endpoint": "/health", 
            "timeout": 5,
            "interval": 60,
            "retry_count": 2
        },
        "metrics": ["request_rate", "response_time", "error_rate"],
        "description": "交易网关适配和连接管理"
    },
    
    "monitor": {
        "name": "📱 监控通知服务",
        "port": 8005,
        "type": "auxiliary",
        "priority": "medium",
        "health_check": {
            "endpoint": "/health",
            "timeout": 5,
            "interval": 120,
            "retry_count": 1
        },
        "metrics": ["request_rate", "response_time"],
        "description": "系统监控、告警通知、性能分析"
    },
    
    "frontend": {
        "name": "🌐 前端开发服务器",
        "port": 3000,
        "type": "frontend",
        "priority": "medium",
        "health_check": {
            "endpoint": "/",
            "timeout": 10,
            "interval": 120,
            "retry_count": 1
        },
        "metrics": ["response_time"],
        "description": "Vue 3前端界面服务"
    }
}


# ====================== 监控仪表板配置 ======================

DASHBOARD_CONFIG = {
    "title": "VnPy Web 监控仪表板",
    "refresh_interval": 30,  # 秒
    "theme": "dark",
    "charts": {
        "system_overview": {
            "title": "系统概览",
            "type": "gauge",
            "metrics": ["cpu_usage", "memory_usage", "disk_usage"],
            "position": {"row": 1, "col": 1, "width": 12, "height": 4}
        },
        "performance_trend": {
            "title": "性能趋势",
            "type": "line",
            "metrics": ["cpu_usage", "memory_usage"],
            "time_range": "1h",
            "position": {"row": 2, "col": 1, "width": 8, "height": 6}
        },
        "service_status": {
            "title": "服务状态",
            "type": "status_grid",
            "services": list(MONITORED_SERVICES_DETAILED.keys()),
            "position": {"row": 2, "col": 9, "width": 4, "height": 6}
        },
        "network_io": {
            "title": "网络IO",
            "type": "area",
            "metrics": ["network_io"],
            "time_range": "30m",
            "position": {"row": 3, "col": 1, "width": 6, "height": 4}
        },
        "alerts_summary": {
            "title": "告警汇总",
            "type": "table",
            "data_source": "recent_alerts",
            "position": {"row": 3, "col": 7, "width": 6, "height": 4}
        }
    }
}


# ====================== 数据保留策略 ======================

DATA_RETENTION_CONFIG = {
    "metrics": {
        "real_time": {
            "interval": "1m",
            "retention": "2h"
        },
        "short_term": {
            "interval": "5m", 
            "retention": "24h"
        },
        "medium_term": {
            "interval": "1h",
            "retention": "7d"
        },
        "long_term": {
            "interval": "1d",
            "retention": "30d"
        }
    },
    "alerts": {
        "active": "never_delete",
        "resolved": "7d",
        "archived": "30d"
    },
    "logs": {
        "error": "30d",
        "warning": "7d", 
        "info": "3d",
        "debug": "1d"
    }
}


def get_metric_config(metric_name: str) -> MetricConfig:
    """获取指标配置"""
    return SYSTEM_METRICS_CONFIG.get(metric_name) or APPLICATION_METRICS_CONFIG.get(metric_name)


def get_alert_rules() -> List[AlertRuleConfig]:
    """获取所有告警规则"""
    return ALERT_RULES_CONFIG


def get_notification_channel_config(channel_id: str) -> NotificationChannelConfig:
    """获取通知渠道配置"""
    return NOTIFICATION_CHANNELS_CONFIG.get(channel_id)


def get_service_config(service_name: str) -> Dict[str, Any]:
    """获取服务监控配置"""
    return MONITORED_SERVICES_DETAILED.get(service_name, {})


def get_all_metrics() -> Dict[str, MetricConfig]:
    """获取所有监控指标配置"""
    return {**SYSTEM_METRICS_CONFIG, **APPLICATION_METRICS_CONFIG}
