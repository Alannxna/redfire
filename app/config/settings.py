"""
应用配置管理模块

This module provides centralized configuration management for the RedFire application.
It uses Pydantic for type-safe configuration with environment variable support.

Features:
- Environment-based configuration
- Type validation with Pydantic
- Database, Redis, and VnPy settings
- Security and logging configuration
"""

import os
from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from pydantic import BaseSettings, Field, validator


class DatabaseSettings(BaseSettings):
    """数据库配置"""
    
    host: str = Field(default="localhost", env="DB_HOST")
    port: int = Field(default=5432, env="DB_PORT")
    username: str = Field(default="postgres", env="DB_USERNAME")
    password: str = Field(default="password", env="DB_PASSWORD")
    database: str = Field(default="redfire", env="DB_DATABASE")
    
    # Connection pool settings
    pool_size: int = Field(default=10, env="DB_POOL_SIZE")
    max_overflow: int = Field(default=20, env="DB_MAX_OVERFLOW")
    pool_timeout: int = Field(default=30, env="DB_POOL_TIMEOUT")
    pool_recycle: int = Field(default=3600, env="DB_POOL_RECYCLE")
    
    # Additional settings
    echo: bool = Field(default=False, env="DB_ECHO")
    echo_pool: bool = Field(default=False, env="DB_ECHO_POOL")
    
    class Config:
        env_prefix = "DB_"
        case_sensitive = False
    
    @property
    def url(self) -> str:
        """Generate database URL."""
        return f"postgresql+asyncpg://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"
    
    @property
    def sync_url(self) -> str:
        """Generate synchronous database URL."""
        return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"


class RedisSettings(BaseSettings):
    """Redis配置"""
    
    host: str = Field(default="localhost", env="REDIS_HOST")
    port: int = Field(default=6379, env="REDIS_PORT")
    password: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    db: int = Field(default=0, env="REDIS_DB")
    
    # Connection settings
    socket_timeout: int = Field(default=5, env="REDIS_SOCKET_TIMEOUT")
    socket_connect_timeout: int = Field(default=5, env="REDIS_SOCKET_CONNECT_TIMEOUT")
    retry_on_timeout: bool = Field(default=True, env="REDIS_RETRY_ON_TIMEOUT")
    max_connections: int = Field(default=50, env="REDIS_MAX_CONNECTIONS")
    
    class Config:
        env_prefix = "REDIS_"
        case_sensitive = False
    
    @property
    def url(self) -> str:
        """Generate Redis URL."""
        auth = f":{self.password}@" if self.password else ""
        return f"redis://{auth}{self.host}:{self.port}/{self.db}"


class VnPySettings(BaseSettings):
    """VnPy配置"""
    
    gateways: List[str] = Field(default=["CTP"], env="VNPY_GATEWAYS")
    log_level: str = Field(default="INFO", env="VNPY_LOG_LEVEL")
    data_path: str = Field(default="./vnpy_data", env="VNPY_DATA_PATH")
    log_path: str = Field(default="./vnpy_logs", env="VNPY_LOG_PATH")
    
    # CTP Gateway settings
    ctp_userid: Optional[str] = Field(default=None, env="CTP_USERID")
    ctp_password: Optional[str] = Field(default=None, env="CTP_PASSWORD")
    ctp_brokerid: Optional[str] = Field(default=None, env="CTP_BROKERID")
    ctp_td_server: Optional[str] = Field(default=None, env="CTP_TD_SERVER")
    ctp_md_server: Optional[str] = Field(default=None, env="CTP_MD_SERVER")
    ctp_appid: Optional[str] = Field(default=None, env="CTP_APPID")
    ctp_auth_code: Optional[str] = Field(default=None, env="CTP_AUTH_CODE")
    ctp_product_info: str = Field(default="", env="CTP_PRODUCT_INFO")
    
    class Config:
        env_prefix = "VNPY_"
        case_sensitive = False
        use_enum_values = True
    
    @validator('gateways', pre=True)
    def parse_gateways(cls, v):
        """Parse comma-separated gateway string."""
        if isinstance(v, str):
            return [g.strip() for g in v.split(',') if g.strip()]
        return v


class SecuritySettings(BaseSettings):
    """安全配置"""
    
    secret_key: str = Field(..., env="SECRET_KEY")
    algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(default=7, env="REFRESH_TOKEN_EXPIRE_DAYS")
    
    # CORS settings
    allowed_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"],
        env="ALLOWED_ORIGINS"
    )
    allowed_methods: List[str] = Field(default=["*"], env="ALLOWED_METHODS")
    allowed_headers: List[str] = Field(default=["*"], env="ALLOWED_HEADERS")
    
    class Config:
        env_prefix = "SECURITY_"
        case_sensitive = False
    
    @validator('allowed_origins', pre=True)
    def parse_origins(cls, v):
        """Parse comma-separated origins string."""
        if isinstance(v, str):
            return [o.strip() for o in v.split(',') if o.strip()]
        return v


class LoggingSettings(BaseSettings):
    """日志配置"""
    
    level: str = Field(default="INFO", env="LOG_LEVEL")
    format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        env="LOG_FORMAT"
    )
    file_path: Optional[str] = Field(default=None, env="LOG_FILE_PATH")
    max_file_size: int = Field(default=10485760, env="LOG_MAX_FILE_SIZE")  # 10MB
    backup_count: int = Field(default=5, env="LOG_BACKUP_COUNT")
    
    class Config:
        env_prefix = "LOG_"
        case_sensitive = False


class Settings(BaseSettings):
    """主应用配置"""
    
    # Basic app settings
    app_name: str = Field(default="RedFire Trading Platform", env="APP_NAME")
    version: str = Field(default="2.0.0", env="APP_VERSION")
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=False, env="DEBUG")
    
    # Server settings
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    workers: int = Field(default=1, env="WORKERS")
    
    # Sub-configurations
    database: DatabaseSettings = DatabaseSettings()
    redis: RedisSettings = RedisSettings()
    vnpy: VnPySettings = VnPySettings()
    security: SecuritySettings = SecuritySettings()
    logging: LoggingSettings = LoggingSettings()
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    @validator('environment')
    def validate_environment(cls, v):
        """Validate environment value."""
        valid_envs = ["development", "staging", "production"]
        if v.lower() not in valid_envs:
            raise ValueError(f"Environment must be one of: {valid_envs}")
        return v.lower()
    
    @validator('debug', pre=True)
    def parse_debug(cls, v):
        """Parse debug boolean from string."""
        if isinstance(v, str):
            return v.lower() in ("true", "1", "yes", "on")
        return v
    
    # Derived properties
    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.environment == "development"
    
    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.environment == "production"
    
    @property
    def log_level(self) -> str:
        """Get effective log level."""
        return "DEBUG" if self.debug else self.logging.level


# Global settings instance
_settings: Optional[Settings] = None


@lru_cache()
def get_settings() -> Settings:
    """
    Get application settings instance.
    
    This function uses LRU cache to ensure settings are loaded only once
    and reused across the application.
    
    Returns:
        Settings: Application settings instance
    """
    global _settings
    
    if _settings is None:
        # Try to load from different possible .env locations
        env_file_paths = [
            Path(".env"),
            Path("../.env"),
            Path("../../.env"),
            Path("/app/.env")
        ]
        
        env_file = None
        for path in env_file_paths:
            if path.exists():
                env_file = str(path)
                break
        
        if env_file:
            _settings = Settings(_env_file=env_file)
        else:
            _settings = Settings()
    
    return _settings


def reload_settings() -> Settings:
    """
    Reload settings from environment.
    
    This function clears the cache and reloads settings.
    Useful for testing or when environment variables change.
    
    Returns:
        Settings: Reloaded settings instance
    """
    global _settings
    _settings = None
    get_settings.cache_clear()
    return get_settings()


# Export key components
__all__ = [
    "Settings",
    "DatabaseSettings", 
    "RedisSettings",
    "VnPySettings",
    "SecuritySettings",
    "LoggingSettings",
    "get_settings",
    "reload_settings"
]
