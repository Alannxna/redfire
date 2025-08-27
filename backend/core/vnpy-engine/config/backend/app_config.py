"""
应用配置管理模块
统一管理所有配置项，支持环境变量和配置文件
"""

import os
from typing import List, Optional, Union, Any
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from enum import Enum
import json


class LogLevel(str, Enum):
    """日志级别"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogFormat(str, Enum):
    """日志格式"""
    JSON = "json"
    TEXT = "text"


class AppConfig(BaseSettings):
    """应用配置"""
    
    # ===== 应用基础配置 =====
    app_name: str = Field(default="VnPy Web Backend", description="应用名称")
    app_version: str = Field(default="1.0.0", description="应用版本")
    debug: bool = Field(default=False, description="调试模式")
    secret_key: str = Field(default="dev-secret-key-change-in-production", description="密钥")
    
    # ===== 服务器配置 =====
    host: str = Field(default="0.0.0.0", description="服务器主机")
    port: int = Field(default=8000, description="服务器端口")
    workers: int = Field(default=1, description="工作进程数")
    
    # ===== 数据库配置 =====
    db_type: str = Field(default="sqlite", description="数据库类型")
    db_host: Optional[str] = Field(default=None, description="数据库主机")
    db_port: Optional[int] = Field(default=None, description="数据库端口")
    db_user: Optional[str] = Field(default=None, description="数据库用户名")
    db_password: Optional[str] = Field(default=None, description="数据库密码")
    db_name: Optional[str] = Field(default=None, description="数据库名称")
    db_sqlite_path: Optional[str] = Field(default=None, description="SQLite文件路径")
    
    # 数据库连接池配置
    db_pool_size: int = Field(default=10, description="连接池大小")
    db_max_overflow: int = Field(default=20, description="最大溢出连接数")
    db_pool_timeout: int = Field(default=30, description="连接池超时时间")
    db_pool_recycle: int = Field(default=3600, description="连接回收时间")
    db_echo: bool = Field(default=False, description="是否打印SQL")
    
    # ===== JWT认证配置 =====
    jwt_secret_key: str = Field(default="jwt-secret-key-change-in-production", description="JWT密钥")
    jwt_algorithm: str = Field(default="HS256", description="JWT算法")
    jwt_access_token_expire_minutes: int = Field(default=30, description="访问令牌过期时间(分钟)")
    jwt_refresh_token_expire_days: int = Field(default=30, description="刷新令牌过期时间(天)")
    
    # ===== Redis配置 =====
    redis_url: str = Field(default="redis://localhost:6379/0", description="Redis连接URL")
    redis_password: Optional[str] = Field(default=None, description="Redis密码")
    redis_db: int = Field(default=0, description="Redis数据库")
    
    # ===== 数据库配置 =====
    database_url: Optional[str] = Field(default=None, description="数据库连接URL")
    
    # ===== 文件存储配置 =====
    data_dir: str = Field(default="./data", description="数据目录")
    log_dir: str = Field(default="./logs", description="日志目录")
    temp_dir: str = Field(default="./temp", description="临时文件目录")
    upload_dir: str = Field(default="./uploads", description="上传文件目录")
    
    # ===== 日志配置 =====
    log_level: LogLevel = Field(default=LogLevel.INFO, description="日志级别")
    log_format: LogFormat = Field(default=LogFormat.JSON, description="日志格式")
    log_rotation: str = Field(default="1 day", description="日志轮转")
    log_retention: str = Field(default="30 days", description="日志保留时间")
    log_file_path: str = Field(default="./logs/vnpy_web.log", description="主日志文件路径")
    
    # ===== VnPy配置 =====
    vnpy_data_dir: str = Field(default="./vnpy_data", description="VnPy数据目录")
    vnpy_log_dir: str = Field(default="./vnpy_logs", description="VnPy日志目录")
    vnpy_config_dir: str = Field(default="./vnpy_config", description="VnPy配置目录")
    
    @property
    def vnpy_data_path(self) -> str:
        """VnPy数据路径（兼容性属性）"""
        return self.vnpy_data_dir
    
    # ===== 安全配置 =====
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"],
        description="CORS允许的源"
    )
    allowed_hosts: List[str] = Field(
        default=["localhost", "127.0.0.1"],
        description="允许的主机"
    )
    
    # ===== 性能配置 =====
    max_connections: int = Field(default=100, description="最大连接数")
    request_timeout: int = Field(default=30, description="请求超时时间")
    keep_alive_timeout: int = Field(default=5, description="保持连接超时时间")
    
    # ===== 开发配置 =====
    reload: bool = Field(default=False, description="自动重载")
    access_log: bool = Field(default=True, description="访问日志")
    
    @field_validator('port')
    @classmethod
    def validate_port(cls, v):
        """验证端口号"""
        if v < 1 or v > 65535:
            raise ValueError('端口号必须在1-65535之间')
        return v
    
    @field_validator('workers')
    @classmethod
    def validate_workers(cls, v):
        """验证工作进程数"""
        if v < 1:
            raise ValueError('工作进程数必须大于0')
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
    
    @field_validator('allowed_hosts', mode='before')
    @classmethod
    def parse_allowed_hosts(cls, v):
        """解析允许的主机"""
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return [host.strip() for host in v.split(',') if host.strip()]
        return v
    
    def get_data_path(self) -> Path:
        """获取数据目录路径"""
        path = Path(self.data_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    def get_log_path(self) -> Path:
        """获取日志目录路径"""
        path = Path(self.log_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    def get_temp_path(self) -> Path:
        """获取临时目录路径"""
        path = Path(self.temp_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    def get_upload_path(self) -> Path:
        """获取上传目录路径"""
        path = Path(self.upload_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    def get_vnpy_data_path(self) -> Path:
        """获取VnPy数据目录路径"""
        path = Path(self.vnpy_data_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    def get_vnpy_log_path(self) -> Path:
        """获取VnPy日志目录路径"""
        path = Path(self.vnpy_log_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    def get_vnpy_config_path(self) -> Path:
        """获取VnPy配置目录路径"""
        path = Path(self.vnpy_config_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    def create_directories(self):
        """创建所有必需的目录"""
        self.get_data_path()
        self.get_log_path()
        self.get_temp_path()
        self.get_upload_path()
        self.get_vnpy_data_path()
        self.get_vnpy_log_path()
        self.get_vnpy_config_path()
    
    def is_development(self) -> bool:
        """是否为开发环境"""
        return self.debug
    
    def is_production(self) -> bool:
        """是否为生产环境"""
        return not self.debug
    
    def build_database_url(self) -> str:
        """构建数据库连接URL"""
        if self.database_url:
            return self.database_url
        
        # 根据数据库类型构建URL
        if self.db_type.lower() == "mysql":
            if not all([self.db_host, self.db_user, self.db_password, self.db_name]):
                raise ValueError("MySQL配置不完整，需要host、user、password、name")
            port = self.db_port or 3306
            return f"mysql+pymysql://{self.db_user}:{self.db_password}@{self.db_host}:{port}/{self.db_name}?charset=utf8mb4"
        elif self.db_type.lower() == "postgresql":
            if not all([self.db_host, self.db_user, self.db_password, self.db_name]):
                raise ValueError("PostgreSQL配置不完整，需要host、user、password、name")
            port = self.db_port or 5432
            return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{port}/{self.db_name}"
        else:  # SQLite
            db_path = self.db_sqlite_path or "./vnpy_web.db"
            return f"sqlite:///{db_path}"
    
    def get_service_config(self, service_key: str) -> dict:
        """获取指定微服务配置"""
        # 定义各个服务的默认配置
        service_configs = {
            "user_trading": {
                "name": "用户交易服务",
                "port": 8001,
                "host": self.host,
                "url": f"http://{self.host}:8001",
                "api_url": f"http://{self.host}:8001",
                "description": "用户认证、账户管理、订单交易、风险控制"
            },
            "vnpy_core": {
                "name": "VnPy核心交易引擎服务",
                "port": 8006,
                "host": self.host,
                "url": f"http://{self.host}:8006",
                "api_url": f"http://{self.host}:8006",
                "description": "VnPy核心交易引擎"
            },
            "strategy_data": {
                "name": "策略数据服务",
                "port": 8002,
                "host": self.host,
                "url": f"http://{self.host}:8002",
                "api_url": f"http://{self.host}:8002",
                "description": "策略管理和历史数据服务"
            },
            "gateway": {
                "name": "网关适配服务",
                "port": 8004,
                "host": self.host,
                "url": f"http://{self.host}:8004",
                "api_url": f"http://{self.host}:8004",
                "description": "交易网关适配服务"
            },
            "monitor": {
                "name": "监控通知服务",
                "port": 8005,
                "host": self.host,
                "url": f"http://{self.host}:8005",
                "api_url": f"http://{self.host}:8005",
                "description": "系统监控和通知服务"
            }
        }
        
        return service_configs.get(service_key, {})
    
    @property
    def service_host(self) -> str:
        """服务主机地址"""
        return self.host
    
    model_config = {
        # 环境变量配置
        "env_file": "config.env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "allow"
    }


# 全局配置实例
_app_config: Optional[AppConfig] = None


def get_app_config() -> AppConfig:
    """获取应用配置"""
    global _app_config
    if _app_config is None:
        _app_config = AppConfig()
        # 创建必需的目录
        _app_config.create_directories()
    return _app_config


def set_app_config(config: AppConfig):
    """设置应用配置"""
    global _app_config
    _app_config = config


def reload_config():
    """重新加载配置"""
    global _app_config
    _app_config = None
    return get_app_config()


# 配置文件路径管理
def get_config_file_path() -> Path:
    """获取配置文件路径"""
    return Path("config.env")


def create_default_config_file():
    """创建默认配置文件"""
    config_path = get_config_file_path()
    example_path = Path("config.env.example")
    
    if not config_path.exists() and example_path.exists():
        import shutil
        shutil.copy2(example_path, config_path)
        print(f"已创建默认配置文件: {config_path}")
    elif not config_path.exists():
        # 如果示例文件也不存在，创建一个基础配置
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write("""# VnPy Web后端配置文件
# 基础配置
DEBUG=false
SECRET_KEY=change-this-in-production
HOST=0.0.0.0
PORT=8000

# 数据库配置
DB_TYPE=sqlite
DB_SQLITE_PATH=./data/vnpy_web.db

# 目录配置
DATA_DIR=./data
LOG_DIR=./logs
TEMP_DIR=./temp
UPLOAD_DIR=./uploads
""")
        print(f"已创建基础配置文件: {config_path}")


# 导出常用配置获取函数
def get_database_config_dict() -> dict:
    """获取数据库配置字典"""
    config = get_app_config()
    return {
        'db_type': config.db_type,
        'host': config.db_host,
        'port': config.db_port,
        'username': config.db_user,
        'password': config.db_password,
        'database': config.db_name,
        'sqlite_path': config.db_sqlite_path,
        'pool_size': config.db_pool_size,
        'max_overflow': config.db_max_overflow,
        'pool_timeout': config.db_pool_timeout,
        'pool_recycle': config.db_pool_recycle,
        'echo': config.db_echo,
    }
