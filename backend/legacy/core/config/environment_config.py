"""
环境配置管理
============

管理不同环境（开发、测试、生产）的配置差异。
"""

import os
from enum import Enum
from typing import Dict, Any, Optional, List
from datetime import datetime

# 导入依赖处理
try:
    from pydantic import Field, field_validator
    PYDANTIC_AVAILABLE = True
except ImportError:
    # 简单的替代实现
    class Field:
        def __init__(self, *args, **kwargs):
            pass
    
    def validator(*args, **kwargs):
        def decorator(func):
            return func
        return decorator
    
    PYDANTIC_AVAILABLE = False

from .base_config import BaseConfig, ConfigMetadata


class Environment(str, Enum):
    """环境类型"""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


class EnvironmentConfig(BaseConfig):
    """环境配置类"""
    
    # 配置名称
    name: str = Field(default="environment_config", description="配置名称")
    
    # 环境信息
    environment: Environment = Field(default=Environment.DEVELOPMENT, description="运行环境")
    debug: bool = Field(default=True, description="调试模式")
    
    # 应用信息
    app_name: str = Field(default="VnPy Web", description="应用名称")
    app_version: str = Field(default="1.0.0", description="应用版本")
    
    # 安全配置
    secret_key: str = Field(default="dev-secret-key", description="密钥")
    allowed_hosts: List[str] = Field(default=["localhost", "127.0.0.1"], description="允许的主机")
    cors_origins: List[str] = Field(default=["http://localhost:3000"], description="CORS允许的源")
    
    # 日志配置
    log_level: str = Field(default="INFO", description="日志级别")
    log_format: str = Field(default="json", description="日志格式")
    
    # 性能配置
    max_connections: int = Field(default=100, description="最大连接数")
    request_timeout: int = Field(default=30, description="请求超时时间")
    
    @field_validator('environment', mode='before')
    def validate_environment(cls, v):
        """验证环境类型"""
        if isinstance(v, str):
            try:
                return Environment(v.lower())
            except ValueError:
                raise ValueError(f"无效的环境类型: {v}")
        return v
    
    @field_validator('secret_key')
    def validate_secret_key(cls, v, info):
        """验证密钥安全性"""
        env = info.data.get('environment', Environment.DEVELOPMENT)
        
        if env == Environment.PRODUCTION:
            if v == "dev-secret-key" or len(v) < 32:
                raise ValueError("生产环境必须使用强密钥（至少32位）")
        
        return v
    
    @field_validator('debug')
    def validate_debug_mode(cls, v, info):
        """验证调试模式设置"""
        env = info.data.get('environment', Environment.DEVELOPMENT)
        
        if env == Environment.PRODUCTION and v:
            raise ValueError("生产环境不应启用调试模式")
        
        return v
    
    def _create_metadata(self) -> ConfigMetadata:
        """创建配置元数据"""
        return ConfigMetadata(
            name="environment_config",
            version="1.0.0",
            description="环境配置管理",
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            source="env"
        )
    
    def validate_config(self) -> bool:
        """验证配置有效性"""
        try:
            # 基础验证
            if not self.app_name:
                return False
            
            if not self.secret_key:
                return False
            
            # 环境特定验证
            if self.environment == Environment.PRODUCTION:
                if self.debug:
                    return False
                if self.secret_key == "dev-secret-key":
                    return False
                if self.log_level == "DEBUG":
                    return False
            
            return True
            
        except Exception:
            return False
    
    def is_development(self) -> bool:
        """是否为开发环境"""
        return self.environment == Environment.DEVELOPMENT
    
    def is_testing(self) -> bool:
        """是否为测试环境"""
        return self.environment == Environment.TESTING
    
    def is_staging(self) -> bool:
        """是否为预发环境"""
        return self.environment == Environment.STAGING
    
    def is_production(self) -> bool:
        """是否为生产环境"""
        return self.environment == Environment.PRODUCTION
    
    def get_environment_specific_config(self) -> Dict[str, Any]:
        """获取环境特定配置"""
        base_config = {
            "debug": self.debug,
            "log_level": self.log_level,
            "max_connections": self.max_connections,
            "request_timeout": self.request_timeout
        }
        
        if self.environment == Environment.DEVELOPMENT:
            base_config.update({
                "debug": True,
                "log_level": "DEBUG",
                "auto_reload": True,
                "show_docs": True,
                "cors_allow_all": True
            })
        
        elif self.environment == Environment.TESTING:
            base_config.update({
                "debug": False,
                "log_level": "INFO",
                "auto_reload": False,
                "show_docs": True,
                "test_mode": True
            })
        
        elif self.environment == Environment.STAGING:
            base_config.update({
                "debug": False,
                "log_level": "INFO",
                "auto_reload": False,
                "show_docs": True,
                "monitoring_enabled": True
            })
        
        elif self.environment == Environment.PRODUCTION:
            base_config.update({
                "debug": False,
                "log_level": "WARNING",
                "auto_reload": False,
                "show_docs": False,
                "monitoring_enabled": True,
                "security_enhanced": True
            })
        
        return base_config
    
    def apply_environment_defaults(self):
        """应用环境默认配置"""
        env_config = self.get_environment_specific_config()
        
        for key, value in env_config.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    @classmethod
    def from_environment(cls, env_name: Optional[str] = None) -> 'EnvironmentConfig':
        """根据环境名称创建配置"""
        if env_name is None:
            env_name = os.getenv('ENVIRONMENT', 'development')
        
        # 创建基础配置
        config = cls(environment=env_name)
        
        # 应用环境默认值
        config.apply_environment_defaults()
        
        return config
    
    def get_security_config(self) -> Dict[str, Any]:
        """获取安全配置"""
        return {
            "secret_key": self.secret_key,
            "allowed_hosts": self.allowed_hosts,
            "cors_origins": self.cors_origins,
            "https_only": self.is_production(),
            "secure_cookies": self.is_production(),
            "csrf_protection": not self.is_development()
        }
    
    def get_logging_config(self) -> Dict[str, Any]:
        """获取日志配置"""
        return {
            "level": self.log_level,
            "format": self.log_format,
            "show_sql": self.is_development(),
            "file_logging": not self.is_development(),
            "error_tracking": self.is_production()
        }
    
    def get_performance_config(self) -> Dict[str, Any]:
        """获取性能配置"""
        return {
            "max_connections": self.max_connections,
            "request_timeout": self.request_timeout,
            "enable_caching": not self.is_development(),
            "enable_compression": self.is_production(),
            "worker_count": 1 if self.is_development() else 4
        }


# 环境配置预设
ENVIRONMENT_PRESETS = {
    Environment.DEVELOPMENT: {
        "debug": True,
        "log_level": "DEBUG",
        "secret_key": "dev-secret-key-change-in-production",
        "allowed_hosts": ["localhost", "127.0.0.1", "0.0.0.0"],
        "cors_origins": ["http://localhost:3000", "http://127.0.0.1:3000"],
        "max_connections": 50,
        "request_timeout": 60
    },
    
    Environment.TESTING: {
        "debug": False,
        "log_level": "INFO",
        "secret_key": "test-secret-key-for-testing",
        "allowed_hosts": ["localhost", "127.0.0.1", "testserver"],
        "cors_origins": ["http://localhost:3000"],
        "max_connections": 30,
        "request_timeout": 30
    },
    
    Environment.STAGING: {
        "debug": False,
        "log_level": "INFO",
        "secret_key": "staging-secret-key-please-change",
        "allowed_hosts": ["staging.vnpy.com", "localhost"],
        "cors_origins": ["https://staging.vnpy.com"],
        "max_connections": 100,
        "request_timeout": 30
    },
    
    Environment.PRODUCTION: {
        "debug": False,
        "log_level": "WARNING",
        "secret_key": "production-secret-key-must-be-secure",
        "allowed_hosts": ["vnpy.com", "www.vnpy.com"],
        "cors_origins": ["https://vnpy.com", "https://www.vnpy.com"],
        "max_connections": 200,
        "request_timeout": 20
    }
}


def create_environment_config(environment: Environment) -> EnvironmentConfig:
    """创建环境配置"""
    preset = ENVIRONMENT_PRESETS.get(environment, {})
    return EnvironmentConfig(environment=environment, **preset)


def get_current_environment() -> Environment:
    """获取当前环境"""
    env_name = os.getenv('ENVIRONMENT', 'development').lower()
    try:
        return Environment(env_name)
    except ValueError:
        return Environment.DEVELOPMENT


def is_development() -> bool:
    """是否为开发环境"""
    return get_current_environment() == Environment.DEVELOPMENT


def is_production() -> bool:
    """是否为生产环境"""
    return get_current_environment() == Environment.PRODUCTION


# 全局环境配置实例
_environment_config: Optional[EnvironmentConfig] = None


def get_environment_config() -> EnvironmentConfig:
    """获取环境配置实例"""
    global _environment_config
    if _environment_config is None:
        _environment_config = EnvironmentConfig.from_environment()
    return _environment_config


def set_environment_config(config: EnvironmentConfig):
    """设置环境配置实例"""
    global _environment_config
    _environment_config = config


def reload_environment_config():
    """重新加载环境配置"""
    global _environment_config
    _environment_config = None
    return get_environment_config()
