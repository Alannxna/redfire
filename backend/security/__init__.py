"""
RedFire 企业级安全防护系统
========================

TODO-15: 安全防护机制优化
一站式安全防护解决方案

核心模块：
- security_config: 安全配置管理
- security_middleware: 安全防护中间件
- rate_limiter: 智能限流系统
- security_monitor: 安全监控和告警
- security_integration: 一键集成接口

主要特性：
🛡️ WAF Web应用防火墙
🔒 SQL注入、XSS、CSRF防护
🚦 多算法智能限流
📊 实时安全监控
🚨 智能威胁检测和告警
🔐 企业级认证授权
📈 安全指标统计
🌐 多渠道告警通知
"""

from .security_config import (
    SecurityConfigManager,
    SecurityLevel,
    ProtectionMode,
    NetworkSecurityConfig,
    WAFConfig,
    RateLimitConfig,
    AuthSecurityConfig,
    SecurityHeadersConfig,
    DataProtectionConfig,
    MonitoringConfig,
    ThreatDetectionConfig,
    security_config
)

from .security_middleware import (
    SecurityMiddleware,
    SecurityThreat,
    WAFEngine,
    CSRFProtection,
    SecurityHeadersManager,
    create_security_middleware,
    get_csrf_token
)

from .rate_limiter import (
    SmartRateLimiter,
    RateLimitResult,
    LimitAlgorithm,
    LimitScope,
    RateLimitRule,
    TokenBucket,
    SlidingWindowLimiter,
    AdaptiveLimiter,
    DDoSProtector
)

from .security_monitor import (
    SecurityMonitor,
    SecurityEvent,
    SecurityAlert,
    EventType,
    AlertChannel,
    AnomalyDetector,
    ThreatIntelligence,
    AlertManager
)

from .security_integration import (
    SecurityIntegration,
    setup_security,
    log_security_event
)

# 版本信息
__version__ = "1.0.0"
__author__ = "RedFire Security Team"
__description__ = "RedFire企业级安全防护系统"

# 导出的主要接口
__all__ = [
    # 配置类
    "SecurityConfigManager",
    "SecurityLevel", 
    "ProtectionMode",
    "security_config",
    
    # 中间件类
    "SecurityMiddleware",
    "WAFEngine",
    "CSRFProtection",
    "SecurityHeadersManager",
    "create_security_middleware",
    "get_csrf_token",
    
    # 限流类
    "SmartRateLimiter",
    "RateLimitResult",
    "LimitAlgorithm",
    "LimitScope",
    
    # 监控类
    "SecurityMonitor",
    "SecurityEvent",
    "SecurityAlert",
    "EventType",
    "AlertChannel",
    
    # 集成类
    "SecurityIntegration",
    "setup_security",
    "log_security_event",
]

# 便捷导入
from .security_integration import setup_security


def get_version():
    """获取版本信息"""
    return __version__


def get_security_info():
    """获取安全系统信息"""
    return {
        "name": "RedFire Security System",
        "version": __version__,
        "description": __description__,
        "features": [
            "Web应用防火墙 (WAF)",
            "智能限流保护",
            "实时安全监控",
            "威胁检测和告警",
            "安全配置管理",
            "CSRF防护",
            "安全响应头",
            "异常检测",
            "威胁情报集成",
            "多渠道告警"
        ],
        "supported_attacks": [
            "SQL注入",
            "XSS攻击",
            "CSRF攻击", 
            "DDoS攻击",
            "暴力破解",
            "路径遍历",
            "命令注入",
            "文件上传攻击",
            "会话劫持",
            "权限提升"
        ]
    }


# 安全系统启动检查
import logging
logger = logging.getLogger(__name__)

# 输出系统信息
logger.info(f"RedFire Security System v{__version__} 已加载")
logger.info("支持的安全防护: WAF, 限流, 监控, 告警, 威胁检测")

# 配置验证
try:
    warnings = security_config.validate_config()
    if warnings:
        for warning in warnings:
            logger.warning(f"安全配置警告: {warning}")
    else:
        logger.info("安全配置验证通过")
except Exception as e:
    logger.error(f"安全配置验证失败: {e}")
