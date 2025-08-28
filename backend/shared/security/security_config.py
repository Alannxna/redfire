"""
RedFire 企业级安全配置系统
========================

TODO-15: 安全防护机制优化
提供全面的安全配置和策略管理

功能特性：
- 🛡️ 全面安全策略配置
- 🔒 多层级安全防护设置
- 🌐 网络安全和访问控制
- 📊 安全监控和告警配置
- 🔐 加密和数据保护配置
"""

import os
import secrets
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set
from enum import Enum
import ipaddress
from datetime import timedelta


class SecurityLevel(str, Enum):
    """安全级别枚举"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ProtectionMode(str, Enum):
    """防护模式"""
    MONITOR = "monitor"      # 仅监控，不阻断
    BLOCK = "block"         # 阻断威胁
    HYBRID = "hybrid"       # 混合模式


@dataclass
class NetworkSecurityConfig:
    """网络安全配置"""
    # IP白名单
    ip_whitelist: Set[str] = field(default_factory=set)
    # IP黑名单
    ip_blacklist: Set[str] = field(default_factory=set)
    # 地理位置限制
    allowed_countries: Set[str] = field(default_factory=lambda: {"CN", "US", "HK"})
    blocked_countries: Set[str] = field(default_factory=set)
    # 网络段限制
    allowed_networks: List[str] = field(default_factory=list)
    blocked_networks: List[str] = field(default_factory=list)
    # 代理检测
    block_proxies: bool = True
    block_tor: bool = True
    block_vpn: bool = False
    # DNS安全
    dns_filtering: bool = True
    malicious_domain_blocking: bool = True

    def is_ip_allowed(self, ip: str) -> bool:
        """检查IP是否被允许"""
        if ip in self.ip_blacklist:
            return False
        
        if self.ip_whitelist and ip not in self.ip_whitelist:
            return False
            
        # 检查网络段
        try:
            ip_obj = ipaddress.ip_address(ip)
            for network in self.blocked_networks:
                if ip_obj in ipaddress.ip_network(network):
                    return False
                    
            if self.allowed_networks:
                allowed = False
                for network in self.allowed_networks:
                    if ip_obj in ipaddress.ip_network(network):
                        allowed = True
                        break
                return allowed
        except ValueError:
            return False
            
        return True


@dataclass
class WAFConfig:
    """Web应用防火墙配置"""
    # 基础防护
    enabled: bool = True
    protection_mode: ProtectionMode = ProtectionMode.BLOCK
    
    # SQL注入防护
    sql_injection_protection: bool = True
    sql_injection_sensitivity: SecurityLevel = SecurityLevel.HIGH
    
    # XSS防护
    xss_protection: bool = True
    xss_sensitivity: SecurityLevel = SecurityLevel.HIGH
    
    # CSRF防护
    csrf_protection: bool = True
    csrf_token_expiry: int = 3600  # 秒
    
    # 文件上传防护
    file_upload_protection: bool = True
    max_file_size: int = 50 * 1024 * 1024  # 50MB
    allowed_file_types: Set[str] = field(default_factory=lambda: {
        ".jpg", ".jpeg", ".png", ".gif", ".pdf", ".doc", ".docx", ".xls", ".xlsx"
    })
    scan_for_malware: bool = True
    
    # 目录遍历防护
    path_traversal_protection: bool = True
    
    # 命令注入防护
    command_injection_protection: bool = True
    
    # HTTP参数污染防护
    hpp_protection: bool = True
    
    # 自定义规则
    custom_rules: List[Dict] = field(default_factory=list)


@dataclass
class RateLimitConfig:
    """速率限制配置"""
    # 全局限流
    global_enabled: bool = True
    global_requests_per_minute: int = 1000
    global_requests_per_hour: int = 10000
    
    # 用户级限流
    user_enabled: bool = True
    user_requests_per_minute: int = 100
    user_requests_per_hour: int = 1000
    
    # IP级限流
    ip_enabled: bool = True
    ip_requests_per_minute: int = 200
    ip_requests_per_hour: int = 2000
    
    # API端点级限流
    endpoint_limits: Dict[str, Dict[str, int]] = field(default_factory=lambda: {
        "/api/auth/login": {"per_minute": 5, "per_hour": 20},
        "/api/auth/register": {"per_minute": 2, "per_hour": 5},
        "/api/trading/orders": {"per_minute": 50, "per_hour": 500},
        "/api/data/quotes": {"per_minute": 200, "per_hour": 2000},
    })
    
    # 突发流量配置
    burst_protection: bool = True
    burst_threshold: float = 1.5  # 允许突发流量倍数
    burst_window: int = 60  # 突发检测窗口（秒）
    
    # 分布式限流
    distributed_mode: bool = True
    redis_key_prefix: str = "redfire:ratelimit"


@dataclass
class AuthSecurityConfig:
    """认证安全配置"""
    # 密码策略
    min_password_length: int = 12
    require_uppercase: bool = True
    require_lowercase: bool = True
    require_numbers: bool = True
    require_special_chars: bool = True
    password_history_count: int = 5
    password_expiry_days: int = 90
    
    # 账户锁定
    max_failed_attempts: int = 5
    lockout_duration: timedelta = field(default_factory=lambda: timedelta(minutes=30))
    progressive_lockout: bool = True  # 渐进式锁定
    
    # 会话安全
    session_timeout: timedelta = field(default_factory=lambda: timedelta(hours=8))
    max_concurrent_sessions: int = 3
    session_fixation_protection: bool = True
    secure_cookies: bool = True
    httponly_cookies: bool = True
    samesite_cookies: str = "strict"
    
    # JWT安全
    jwt_secret_rotation: bool = True
    jwt_secret_rotation_interval: timedelta = field(default_factory=lambda: timedelta(days=30))
    jwt_blacklist_enabled: bool = True
    
    # MFA配置
    mfa_enabled: bool = False
    mfa_required_for_admin: bool = True
    totp_issuer: str = "RedFire"
    
    # 设备信任
    device_fingerprinting: bool = True
    trusted_device_duration: timedelta = field(default_factory=lambda: timedelta(days=30))


@dataclass
class SecurityHeadersConfig:
    """安全响应头配置"""
    # 基础安全头
    x_content_type_options: str = "nosniff"
    x_frame_options: str = "DENY"
    x_xss_protection: str = "1; mode=block"
    
    # HSTS配置
    strict_transport_security: bool = True
    hsts_max_age: int = 31536000  # 1年
    hsts_include_subdomains: bool = True
    hsts_preload: bool = True
    
    # CSP配置
    content_security_policy: bool = True
    csp_default_src: str = "'self'"
    csp_script_src: str = "'self' 'unsafe-inline'"
    csp_style_src: str = "'self' 'unsafe-inline'"
    csp_img_src: str = "'self' data: https:"
    csp_font_src: str = "'self'"
    csp_connect_src: str = "'self'"
    csp_frame_ancestors: str = "'none'"
    
    # 权限策略
    permissions_policy: bool = True
    permissions_camera: str = "()"
    permissions_microphone: str = "()"
    permissions_geolocation: str = "()"
    permissions_payment: str = "()"
    
    # 其他安全头
    referrer_policy: str = "strict-origin-when-cross-origin"
    cross_origin_embedder_policy: str = "require-corp"
    cross_origin_opener_policy: str = "same-origin"
    cross_origin_resource_policy: str = "same-origin"


@dataclass
class DataProtectionConfig:
    """数据保护配置"""
    # 加密配置
    encryption_at_rest: bool = True
    encryption_in_transit: bool = True
    encryption_algorithm: str = "AES-256-GCM"
    
    # 密钥管理
    key_rotation_enabled: bool = True
    key_rotation_interval: timedelta = field(default_factory=lambda: timedelta(days=90))
    key_derivation_iterations: int = 100000
    
    # 数据分类
    data_classification_enabled: bool = True
    sensitive_data_encryption: bool = True
    pii_data_masking: bool = True
    
    # 数据备份安全
    backup_encryption: bool = True
    backup_integrity_check: bool = True
    backup_retention_days: int = 90
    
    # 数据传输
    tls_min_version: str = "1.2"
    certificate_pinning: bool = True
    
    # 数据删除
    secure_deletion: bool = True
    data_retention_policy: bool = True


@dataclass
class MonitoringConfig:
    """安全监控配置"""
    # 日志配置
    security_logging: bool = True
    log_level: str = "INFO"
    log_retention_days: int = 365
    log_encryption: bool = True
    
    # 实时监控
    real_time_monitoring: bool = True
    anomaly_detection: bool = True
    threat_intelligence: bool = True
    
    # 告警配置
    alert_enabled: bool = True
    alert_channels: List[str] = field(default_factory=lambda: ["email", "webhook", "sms"])
    alert_severity_threshold: SecurityLevel = SecurityLevel.MEDIUM
    
    # 审计配置
    audit_enabled: bool = True
    audit_all_requests: bool = False  # 仅审计敏感操作
    audit_failed_requests: bool = True
    
    # 性能监控
    performance_monitoring: bool = True
    latency_threshold_ms: int = 1000
    error_rate_threshold: float = 0.05  # 5%


@dataclass
class ThreatDetectionConfig:
    """威胁检测配置"""
    # 基础检测
    enabled: bool = True
    detection_mode: ProtectionMode = ProtectionMode.HYBRID
    
    # 暴力破解检测
    brute_force_detection: bool = True
    brute_force_threshold: int = 10
    brute_force_window: int = 300  # 5分钟
    
    # 异常行为检测
    anomaly_detection: bool = True
    user_behavior_analysis: bool = True
    session_anomaly_detection: bool = True
    
    # 恶意IP检测
    malicious_ip_detection: bool = True
    threat_intelligence_feeds: List[str] = field(default_factory=lambda: [
        "spamhaus", "malwaredomainlist", "abuse.ch"
    ])
    
    # Bot检测
    bot_detection: bool = True
    captcha_enabled: bool = True
    
    # 高级威胁检测
    advanced_persistent_threat: bool = True
    zero_day_protection: bool = True
    
    # 机器学习检测
    ml_detection: bool = False  # 可选的机器学习检测
    ml_model_update_interval: timedelta = field(default_factory=lambda: timedelta(hours=24))


class SecurityConfigManager:
    """安全配置管理器"""
    
    def __init__(self, environment: str = "production"):
        self.environment = environment
        self._load_config()
    
    def _load_config(self):
        """加载安全配置"""
        if self.environment == "production":
            self._load_production_config()
        elif self.environment == "staging":
            self._load_staging_config()
        else:
            self._load_development_config()
    
    def _load_production_config(self):
        """生产环境安全配置"""
        self.network = NetworkSecurityConfig(
            ip_whitelist=set(),  # 生产环境可配置白名单
            block_proxies=True,
            block_tor=True,
            dns_filtering=True
        )
        
        self.waf = WAFConfig(
            protection_mode=ProtectionMode.BLOCK,
            sql_injection_sensitivity=SecurityLevel.HIGH,
            xss_sensitivity=SecurityLevel.HIGH
        )
        
        self.rate_limit = RateLimitConfig(
            global_requests_per_minute=1000,
            user_requests_per_minute=100,
            distributed_mode=True
        )
        
        self.auth = AuthSecurityConfig(
            min_password_length=12,
            max_failed_attempts=5,
            mfa_required_for_admin=True,
            session_timeout=timedelta(hours=8)
        )
        
        self.headers = SecurityHeadersConfig(
            strict_transport_security=True,
            content_security_policy=True
        )
        
        self.data_protection = DataProtectionConfig(
            encryption_at_rest=True,
            key_rotation_enabled=True,
            tls_min_version="1.3"
        )
        
        self.monitoring = MonitoringConfig(
            real_time_monitoring=True,
            alert_severity_threshold=SecurityLevel.MEDIUM,
            audit_enabled=True
        )
        
        self.threat_detection = ThreatDetectionConfig(
            detection_mode=ProtectionMode.BLOCK,
            anomaly_detection=True,
            malicious_ip_detection=True
        )
    
    def _load_staging_config(self):
        """预发布环境配置"""
        self._load_production_config()
        # 预发布环境可以稍微宽松一些
        self.waf.protection_mode = ProtectionMode.HYBRID
        self.threat_detection.detection_mode = ProtectionMode.MONITOR
        self.rate_limit.global_requests_per_minute = 2000
    
    def _load_development_config(self):
        """开发环境配置"""
        self.network = NetworkSecurityConfig(
            block_proxies=False,
            block_tor=False,
            dns_filtering=False
        )
        
        self.waf = WAFConfig(
            protection_mode=ProtectionMode.MONITOR,
            sql_injection_sensitivity=SecurityLevel.MEDIUM
        )
        
        self.rate_limit = RateLimitConfig(
            global_requests_per_minute=10000,
            user_requests_per_minute=1000,
            distributed_mode=False
        )
        
        self.auth = AuthSecurityConfig(
            min_password_length=8,
            max_failed_attempts=10,
            mfa_required_for_admin=False
        )
        
        self.headers = SecurityHeadersConfig(
            strict_transport_security=False,
            content_security_policy=False
        )
        
        self.data_protection = DataProtectionConfig(
            encryption_at_rest=False,
            key_rotation_enabled=False,
            tls_min_version="1.2"
        )
        
        self.monitoring = MonitoringConfig(
            real_time_monitoring=False,
            alert_enabled=False,
            audit_enabled=False
        )
        
        self.threat_detection = ThreatDetectionConfig(
            detection_mode=ProtectionMode.MONITOR,
            anomaly_detection=False,
            malicious_ip_detection=False
        )
    
    def get_jwt_secret_key(self) -> str:
        """获取JWT密钥"""
        key = os.getenv("JWT_SECRET_KEY")
        if not key:
            if self.environment == "production":
                raise ValueError("生产环境必须设置JWT_SECRET_KEY环境变量")
            key = secrets.token_urlsafe(32)
        return key
    
    def get_encryption_key(self) -> bytes:
        """获取加密密钥"""
        key = os.getenv("ENCRYPTION_KEY")
        if not key:
            if self.environment == "production":
                raise ValueError("生产环境必须设置ENCRYPTION_KEY环境变量")
            key = secrets.token_bytes(32)
        else:
            key = key.encode()
        return key
    
    def validate_config(self) -> List[str]:
        """验证安全配置"""
        warnings = []
        
        if self.environment == "production":
            if not self.headers.strict_transport_security:
                warnings.append("生产环境建议启用HSTS")
            
            if not self.data_protection.encryption_at_rest:
                warnings.append("生产环境建议启用静态数据加密")
            
            if self.auth.min_password_length < 12:
                warnings.append("生产环境建议密码长度至少12位")
            
            if not self.monitoring.audit_enabled:
                warnings.append("生产环境建议启用审计日志")
        
        return warnings
    
    def export_config(self) -> Dict:
        """导出配置为字典"""
        return {
            "environment": self.environment,
            "network": self.network.__dict__,
            "waf": self.waf.__dict__,
            "rate_limit": self.rate_limit.__dict__,
            "auth": self.auth.__dict__,
            "headers": self.headers.__dict__,
            "data_protection": self.data_protection.__dict__,
            "monitoring": self.monitoring.__dict__,
            "threat_detection": self.threat_detection.__dict__
        }


# 全局安全配置实例
security_config = SecurityConfigManager(
    environment=os.getenv("ENVIRONMENT", "development")
)

# 验证配置并输出警告
config_warnings = security_config.validate_config()
if config_warnings:
    import logging
    logger = logging.getLogger(__name__)
    for warning in config_warnings:
        logger.warning(f"安全配置警告: {warning}")
