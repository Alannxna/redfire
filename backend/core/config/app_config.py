"""
应用核心配置
============

RedFire应用的核心配置类
"""

import os
from typing import List, Optional
from pathlib import Path
from pydantic import Field, field_validator
import json

from .base_config import BaseConfig


class AppConfig(BaseConfig):
    """应用核心配置"""
    
    # ===== 应用基础信息 =====
    app_name: str = Field(default="RedFire", description="应用名称")
    app_version: str = Field(default="2.0.0", description="应用版本")
    debug: bool = Field(default=False, description="调试模式")
    environment: str = Field(default="development", description="运行环境")
    
    # ===== 服务器配置 =====
    host: str = Field(default="0.0.0.0", description="服务器主机")
    port: int = Field(default=8000, ge=1, le=65535, description="服务器端口")
    workers: int = Field(default=1, ge=1, description="工作进程数")
    
    # ===== 安全配置 =====
    secret_key: str = Field(default="dev-secret-key-change-in-production", description="应用密钥")
    jwt_secret_key: str = Field(default="jwt-secret-key-change-in-production", description="JWT密钥")
    jwt_algorithm: str = Field(default="HS256", description="JWT算法")
    jwt_access_token_expire_minutes: int = Field(default=30, description="访问令牌过期时间(分钟)")
    jwt_refresh_token_expire_days: int = Field(default=30, description="刷新令牌过期时间(天)")
    
    # ===== CORS配置 =====
    cors_origins: List[str] = Field(
        default=[
            "http://localhost:3000",
            "http://127.0.0.1:3000", 
            "http://localhost:5173",
            "http://127.0.0.1:5173"
        ],
        description="CORS允许的源"
    )
    cors_allow_credentials: bool = Field(default=True, description="CORS允许凭证")
    cors_allow_methods: List[str] = Field(
        default=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        description="CORS允许的方法"
    )
    cors_allow_headers: List[str] = Field(
        default=["*"],
        description="CORS允许的头部"
    )
    
    # ===== 数据库配置 =====
    database_url: Optional[str] = Field(default=None, description="数据库连接URL")
    db_echo: bool = Field(default=False, description="是否打印SQL")
    db_pool_size: int = Field(default=10, description="连接池大小")
    db_max_overflow: int = Field(default=20, description="最大溢出连接数")
    
    # ===== Redis配置 =====
    redis_url: str = Field(default="redis://localhost:6379/0", description="Redis连接URL")
    redis_password: Optional[str] = Field(default=None, description="Redis密码")
    
    # ===== 目录配置 =====
    data_dir: str = Field(default="./data", description="数据目录")
    log_dir: str = Field(default="./logs", description="日志目录")
    temp_dir: str = Field(default="./temp", description="临时文件目录")
    upload_dir: str = Field(default="./uploads", description="上传文件目录")
    
    # ===== VnPy配置 =====
    vnpy_data_dir: str = Field(default="./vnpy_data", description="VnPy数据目录")
    vnpy_log_dir: str = Field(default="./vnpy_logs", description="VnPy日志目录")
    vnpy_config_dir: str = Field(default="./vnpy_config", description="VnPy配置目录")
    
    # ===== 日志配置 =====
    log_level: str = Field(default="INFO", description="日志级别")
    log_format: str = Field(default="json", description="日志格式")
    
    # ===== 性能配置 =====
    max_connections: int = Field(default=100, description="最大连接数")
    request_timeout: int = Field(default=30, description="请求超时时间")
    
    @field_validator('environment')
    @classmethod
    def validate_environment(cls, v):
        """验证环境"""
        allowed = ['development', 'testing', 'staging', 'production']
        if v not in allowed:
            raise ValueError(f'环境必须是 {allowed} 之一')
        return v
    
    @field_validator('port')
    @classmethod
    def validate_port(cls, v):
        """验证端口号"""
        if v < 1 or v > 65535:
            raise ValueError('端口号必须在1-65535之间')
        return v
    
    @field_validator('cors_origins', mode='before')
    @classmethod
    def parse_cors_origins(cls, v):
        """解析CORS源"""
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return [origin.strip() for origin in v.split(',') if origin.strip()]
        return v
    
    def _validate_config(self):
        """配置验证"""
        super()._validate_config()
        
        # 生产环境安全检查
        if self.environment == 'production':
            if self.secret_key == "dev-secret-key-change-in-production":
                raise ValueError("生产环境必须设置安全的secret_key")
            if self.jwt_secret_key == "jwt-secret-key-change-in-production":
                raise ValueError("生产环境必须设置安全的jwt_secret_key")
            if self.debug:
                raise ValueError("生产环境不能启用调试模式")
    
    def create_directories(self):
        """创建所有必需的目录"""
        directories = [
            self.data_dir,
            self.log_dir, 
            self.temp_dir,
            self.upload_dir,
            self.vnpy_data_dir,
            self.vnpy_log_dir,
            self.vnpy_config_dir
        ]
        
        for dir_path in directories:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    def get_cors_settings(self) -> dict:
        """获取CORS设置"""
        return {
            "allow_origins": self.cors_origins,
            "allow_credentials": self.cors_allow_credentials,
            "allow_methods": self.cors_allow_methods,
            "allow_headers": self.cors_allow_headers
        }
    
    def is_development(self) -> bool:
        """是否为开发环境"""
        return self.environment == "development"
    
    def is_production(self) -> bool:
        """是否为生产环境"""
        return self.environment == "production"
    
    def get_service_config(self, service_name: str) -> dict:
        """获取微服务配置"""
        service_configs = {
            "user_trading": {
                "name": "用户交易服务",
                "port": 8001,
                "host": self.host,
                "description": "用户认证、账户管理、订单交易、风险控制"
            },
            "vnpy_core": {
                "name": "VnPy核心交易引擎服务", 
                "port": 8006,
                "host": self.host,
                "description": "VnPy核心交易引擎"
            },
            "strategy_data": {
                "name": "策略数据服务",
                "port": 8002, 
                "host": self.host,
                "description": "策略管理和历史数据服务"
            },
            "gateway": {
                "name": "网关适配服务",
                "port": 8004,
                "host": self.host,
                "description": "交易网关适配服务"
            },
            "monitor": {
                "name": "监控通知服务",
                "port": 8005,
                "host": self.host,
                "description": "系统监控和通知服务"
            }
        }
        
        return service_configs.get(service_name, {})
