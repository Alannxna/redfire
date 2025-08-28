"""
环境特定配置
============

不同环境（开发、测试、生产）的特定配置
"""

from typing import List, Optional
from pydantic import Field

from .base_config import BaseConfig


class EnvironmentConfig(BaseConfig):
    """环境特定配置基类"""
    
    # 环境标识
    environment: str = Field(..., description="环境名称")
    
    # 数据库配置
    database_url: str = Field(..., description="数据库连接URL")
    redis_url: str = Field(..., description="Redis连接URL")
    
    # 日志配置
    log_level: str = Field(default="INFO", description="日志级别")
    log_file_enabled: bool = Field(default=True, description="是否启用文件日志")
    
    # 安全配置
    secret_key: str = Field(..., description="应用密钥")
    jwt_secret_key: str = Field(..., description="JWT密钥")
    
    # 性能配置
    workers: int = Field(default=1, description="工作进程数")
    max_connections: int = Field(default=100, description="最大连接数")


class DevelopmentConfig(EnvironmentConfig):
    """开发环境配置"""
    
    environment: str = Field(default="development")
    debug: bool = Field(default=True)
    
    # 数据库配置（开发环境默认值）
    database_url: str = Field(default="sqlite:///./data/redfire_dev.db")
    redis_url: str = Field(default="redis://localhost:6379/0")
    
    # 安全配置（开发环境宽松设置）
    secret_key: str = Field(default="dev-secret-key-not-for-production")
    jwt_secret_key: str = Field(default="dev-jwt-secret-key-not-for-production")
    
    # 日志配置
    log_level: str = Field(default="DEBUG")
    
    # CORS配置（开发环境允许所有来源）
    cors_origins: List[str] = Field(default=["*"])
    
    # 开发特定设置
    hot_reload: bool = Field(default=True)
    api_docs_enabled: bool = Field(default=True)
    access_log: bool = Field(default=True)
    
    # VnPy配置
    vnpy_data_dir: str = Field(default="./data/vnpy_dev")
    vnpy_log_dir: str = Field(default="./logs/vnpy_dev")


class TestingConfig(EnvironmentConfig):
    """测试环境配置"""
    
    environment: str = Field(default="testing")
    debug: bool = Field(default=True)
    
    # 数据库配置（测试环境）
    database_url: str = Field(default="sqlite:///./data/redfire_test.db")
    redis_url: str = Field(default="redis://localhost:6379/1")
    
    # 安全配置
    secret_key: str = Field(default="test-secret-key")
    jwt_secret_key: str = Field(default="test-jwt-secret-key")
    
    # 日志配置
    log_level: str = Field(default="DEBUG")
    log_file_enabled: bool = Field(default=False)  # 测试时不写文件
    
    # 测试特定设置
    testing: bool = Field(default=True)
    api_docs_enabled: bool = Field(default=True)


class StagingConfig(EnvironmentConfig):
    """预发布环境配置"""
    
    environment: str = Field(default="staging")
    debug: bool = Field(default=False)
    
    # 数据库配置（从环境变量获取）
    database_url: str = Field(..., env="DATABASE_URL")
    redis_url: str = Field(..., env="REDIS_URL")
    
    # 安全配置（从环境变量获取）
    secret_key: str = Field(..., env="SECRET_KEY", min_length=32)
    jwt_secret_key: str = Field(..., env="JWT_SECRET_KEY", min_length=32)
    
    # 日志配置
    log_level: str = Field(default="INFO")
    
    # 性能配置
    workers: int = Field(default=2, env="WORKERS")
    max_connections: int = Field(default=100, env="MAX_CONNECTIONS")
    
    # CORS配置（受限）
    cors_origins: List[str] = Field(..., env="ALLOWED_ORIGINS")


class ProductionConfig(EnvironmentConfig):
    """生产环境配置"""
    
    environment: str = Field(default="production")
    debug: bool = Field(default=False)
    
    # 数据库配置（必须从环境变量获取）
    database_url: str = Field(..., env="DATABASE_URL")
    redis_url: str = Field(..., env="REDIS_URL")
    
    # 安全配置（必须从环境变量获取）
    secret_key: str = Field(..., env="SECRET_KEY", min_length=32)
    jwt_secret_key: str = Field(..., env="JWT_SECRET_KEY", min_length=32)
    
    # 允许的主机（必须设置）
    allowed_hosts: List[str] = Field(..., env="ALLOWED_HOSTS")
    cors_origins: List[str] = Field(..., env="ALLOWED_ORIGINS")
    
    # 日志配置
    log_level: str = Field(default="WARNING", env="LOG_LEVEL")
    
    # 性能配置
    workers: int = Field(default=4, env="WORKERS")
    max_connections: int = Field(default=200, env="MAX_CONNECTIONS")
    
    # SSL配置
    ssl_enabled: bool = Field(default=True, env="SSL_ENABLED")
    ssl_cert_path: Optional[str] = Field(default=None, env="SSL_CERT_PATH")
    ssl_key_path: Optional[str] = Field(default=None, env="SSL_KEY_PATH")
    
    # 监控配置
    monitoring_enabled: bool = Field(default=True)
    metrics_enabled: bool = Field(default=True)
    
    def _validate_config(self):
        """生产环境额外验证"""
        super()._validate_config()
        
        if self.ssl_enabled and (not self.ssl_cert_path or not self.ssl_key_path):
            raise ValueError("生产环境启用SSL时必须提供证书路径")


def get_environment_config(env_name: str) -> EnvironmentConfig:
    """根据环境名称获取对应的配置类"""
    config_mapping = {
        "development": DevelopmentConfig,
        "testing": TestingConfig,
        "staging": StagingConfig, 
        "production": ProductionConfig
    }
    
    config_class = config_mapping.get(env_name.lower())
    if not config_class:
        raise ValueError(f"不支持的环境: {env_name}")
    
    return config_class()


def detect_environment() -> str:
    """自动检测当前运行环境"""
    import os
    
    # 优先级：环境变量 > 文件标识 > 默认值
    env = os.getenv('ENVIRONMENT', os.getenv('ENV', 'development'))
    
    # 检查常见的环境标识文件
    env_files = {
        '.env.production': 'production',
        '.env.staging': 'staging',
        '.env.testing': 'testing',
        '.env.development': 'development'
    }
    
    for file_name, env_name in env_files.items():
        if os.path.exists(file_name):
            return env_name
    
    return env.lower()
