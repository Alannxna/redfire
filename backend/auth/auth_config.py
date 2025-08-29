"""
认证配置模块
============

认证授权系统的配置管理
"""

import os
from typing import List, Optional
from dataclasses import dataclass, field
from enum import Enum


class Environment(str, Enum):
    """环境枚举"""
    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"


@dataclass
class AuthConfig:
    """认证配置类"""
    
    # 环境配置
    environment: Environment = field(default_factory=lambda: Environment(os.getenv("ENVIRONMENT", "development")))
    
    # JWT配置
    jwt_secret_key: str = field(default_factory=lambda: os.getenv("JWT_SECRET_KEY", "jwt-secret-key-change-in-production"))
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = field(default_factory=lambda: int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")))
    refresh_token_expire_days: int = field(default_factory=lambda: int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7")))
    
    # 安全配置
    max_login_attempts: int = field(default_factory=lambda: int(os.getenv("MAX_LOGIN_ATTEMPTS", "5")))
    lockout_duration_minutes: int = field(default_factory=lambda: int(os.getenv("LOCKOUT_DURATION_MINUTES", "15")))
    password_min_length: int = 8
    require_strong_password: bool = field(default_factory=lambda: os.getenv("REQUIRE_STRONG_PASSWORD", "true").lower() == "true")
    
    # 会话配置
    max_concurrent_sessions: int = field(default_factory=lambda: int(os.getenv("MAX_CONCURRENT_SESSIONS", "3")))
    session_timeout_minutes: int = field(default_factory=lambda: int(os.getenv("SESSION_TIMEOUT_MINUTES", "60")))
    
    # Redis配置
    redis_url: str = field(default_factory=lambda: os.getenv("REDIS_URL", "redis://localhost:6379/0"))
    cache_enabled: bool = field(default_factory=lambda: os.getenv("CACHE_ENABLED", "true").lower() == "true")
    cache_ttl_seconds: int = 300
    
    # IP限制配置
    enable_ip_whitelist: bool = field(default_factory=lambda: os.getenv("ENABLE_IP_WHITELIST", "false").lower() == "true")
    ip_whitelist: List[str] = field(default_factory=lambda: os.getenv("IP_WHITELIST", "").split(",") if os.getenv("IP_WHITELIST") else [])
    
    # 安全响应头配置
    enable_security_headers: bool = field(default_factory=lambda: os.getenv("ENABLE_SECURITY_HEADERS", "true").lower() == "true")
    cors_enabled: bool = field(default_factory=lambda: os.getenv("CORS_ENABLED", "true").lower() == "true")
    cors_origins: List[str] = field(default_factory=lambda: os.getenv("CORS_ORIGINS", "*").split(","))
    
    # 日志配置
    log_level: str = field(default_factory=lambda: os.getenv("AUTH_LOG_LEVEL", "INFO"))
    enable_audit_log: bool = field(default_factory=lambda: os.getenv("ENABLE_AUDIT_LOG", "true").lower() == "true")
    
    def __post_init__(self):
        """初始化后处理"""
        # 生产环境安全检查
        if self.environment == Environment.PRODUCTION:
            self._validate_production_config()
        
        # 清理空白的IP白名单条目
        self.ip_whitelist = [ip.strip() for ip in self.ip_whitelist if ip.strip()]
        self.cors_origins = [origin.strip() for origin in self.cors_origins if origin.strip()]
    
    def _validate_production_config(self):
        """验证生产环境配置"""
        warnings = []
        
        if self.jwt_secret_key == "jwt-secret-key-change-in-production":
            warnings.append("生产环境使用默认JWT密钥，存在安全风险")
        
        if len(self.jwt_secret_key) < 32:
            warnings.append("JWT密钥长度不足，建议至少32位")
        
        if not self.require_strong_password:
            warnings.append("生产环境建议启用强密码要求")
        
        if not self.enable_security_headers:
            warnings.append("生产环境建议启用安全响应头")
        
        if "*" in self.cors_origins:
            warnings.append("生产环境不建议使用通配符CORS配置")
        
        if warnings:
            import logging
            logger = logging.getLogger(__name__)
            for warning in warnings:
                logger.warning(f"配置安全警告: {warning}")
    
    @classmethod
    def from_env(cls) -> "AuthConfig":
        """从环境变量创建配置"""
        return cls()
    
    @classmethod
    def for_development(cls) -> "AuthConfig":
        """开发环境配置"""
        return cls(
            environment=Environment.DEVELOPMENT,
            jwt_secret_key="development-secret-key",
            access_token_expire_minutes=60,  # 开发环境延长到1小时
            require_strong_password=False,
            enable_ip_whitelist=False,
            cors_origins=["http://localhost:3000", "http://localhost:8080"]
        )
    
    @classmethod
    def for_testing(cls) -> "AuthConfig":
        """测试环境配置"""
        return cls(
            environment=Environment.TESTING,
            jwt_secret_key="testing-secret-key",
            access_token_expire_minutes=5,  # 测试环境短时间
            max_login_attempts=3,
            cache_enabled=False,  # 测试环境禁用缓存
            enable_security_headers=False
        )
    
    @classmethod
    def for_production(cls) -> "AuthConfig":
        """生产环境配置"""
        return cls(
            environment=Environment.PRODUCTION,
            access_token_expire_minutes=15,  # 生产环境较短
            require_strong_password=True,
            enable_security_headers=True,
            enable_ip_whitelist=True,
            cors_origins=[]  # 生产环境需要明确配置
        )


# 全局配置实例
_auth_config: Optional[AuthConfig] = None


def get_auth_config() -> AuthConfig:
    """获取全局认证配置"""
    global _auth_config
    if _auth_config is None:
        _auth_config = AuthConfig.from_env()
    return _auth_config


def set_auth_config(config: AuthConfig):
    """设置全局认证配置"""
    global _auth_config
    _auth_config = config


def reset_auth_config():
    """重置全局认证配置"""
    global _auth_config
    _auth_config = None
