"""
Legacy配置系统整合模块

将原有配置文件整合到Backend系统中，
提供向后兼容和统一的配置管理
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass, asdict
from datetime import datetime
from pydantic import BaseModel, Field

from .vnpy_integration_config import VnPyIntegrationConfig, get_vnpy_integration_config
# from .unified_config import UnifiedConfig  # 避免循环导入

logger = logging.getLogger(__name__)


@dataclass
class LegacyDatabaseSettings:
    """Legacy数据库设置"""
    name: str = "mysql"
    host: str = "127.0.0.1"
    port: int = 3306
    user: str = "root"
    password: str = "root"
    database: str = "vnpy"
    timezone: str = "Asia/Shanghai"
    charset: str = "utf8mb4"


@dataclass
class LegacyAppSettings:
    """Legacy应用设置"""
    debug: bool = False
    testing: bool = False
    log_level: str = "INFO"
    secret_key: str = "change-me-in-production"
    api_prefix: str = "/api/v1"
    docs_url: str = "/docs"
    redoc_url: str = "/redoc"


@dataclass
class LegacyServiceSettings:
    """Legacy服务设置"""
    redis_host: str = "127.0.0.1"
    redis_port: int = 6379
    redis_password: str = ""
    redis_db: int = 0
    redis_url: str = ""
    
    jwt_secret_key: str = "jwt-secret-key"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7
    
    cors_origins: list = None
    allowed_hosts: list = None
    
    enable_cache: bool = True

    def __post_init__(self):
        if self.cors_origins is None:
            self.cors_origins = ["*"]
        if self.allowed_hosts is None:
            self.allowed_hosts = ["*"]


class LegacyConfigIntegrator:
    """Legacy配置整合器"""
    
    def __init__(self):
        # self.unified_config = UnifiedConfig()  # 避免循环导入
        self.vnpy_integration = get_vnpy_integration_config()
        
    def load_vt_setting(self) -> Dict[str, Any]:
        """加载vt_setting.json配置"""
        try:
            # 获取项目根路径
            project_root = Path.cwd()
            
            # 尝试多个可能的路径
            possible_paths = [
                project_root / "config" / "vt_setting.json",
                project_root / "../config" / "vt_setting.json",
                project_root / "vt_setting.json",
                Path.home() / ".vnpy" / "vt_setting.json"
            ]
            
            for vt_setting_path in possible_paths:
                if vt_setting_path.exists():
                    with open(vt_setting_path, 'r', encoding='utf-8') as f:
                        vt_setting = json.load(f)
                        logger.info(f"已加载vt_setting.json: {vt_setting_path}")
                        return vt_setting
            
            logger.warning("未找到vt_setting.json文件")
                
        except Exception as e:
            logger.error(f"加载vt_setting.json失败: {e}")
            
        # 返回默认配置
        return {
            "database.name": "mysql",
            "database.database": "vnpy",
            "database.host": "127.0.0.1",
            "database.port": 3306,
            "database.user": "root",
            "database.password": "root",
            "database.timezone": "Asia/Shanghai"
        }
    
    def load_env_config(self) -> Dict[str, Any]:
        """加载环境配置文件"""
        env_config = {}
        
        # 尝试加载.env文件
        env_files = [
            ".env",
            "config/.env",
            "../config/.env",
            "config/config.env",
            "../config/config.env"
        ]
        
        for env_file in env_files:
            env_path = Path(env_file)
            if env_path.exists():
                try:
                    # 简单的.env文件解析
                    with open(env_path, 'r', encoding='utf-8') as f:
                        for line in f:
                            line = line.strip()
                            if line and not line.startswith('#'):
                                if '=' in line:
                                    key, value = line.split('=', 1)
                                    key = key.strip()
                                    value = value.strip().strip('"').strip("'")
                                    env_config[key] = value
                    
                    logger.info(f"已加载环境配置: {env_path}")
                    break
                except Exception as e:
                    logger.error(f"加载环境配置失败 {env_path}: {e}")
        
        # 从系统环境变量获取配置
        env_vars = [
            'DATABASE_HOST', 'DATABASE_PORT', 'DATABASE_USER', 'DATABASE_PASSWORD',
            'DATABASE_NAME', 'DATABASE_URL',
            'REDIS_HOST', 'REDIS_PORT', 'REDIS_PASSWORD', 'REDIS_DB', 'REDIS_URL',
            'SECRET_KEY', 'JWT_SECRET_KEY', 'DEBUG', 'LOG_LEVEL',
            'VNPY_CORE_PATH', 'VNPY_PATH'
        ]
        
        for var in env_vars:
            value = os.getenv(var)
            if value is not None:
                env_config[var.lower()] = value
        
        return env_config
    
    def create_database_config(self, vt_setting: Dict[str, Any], env_config: Dict[str, Any]) -> LegacyDatabaseSettings:
        """创建数据库配置"""
        db_config = LegacyDatabaseSettings()
        
        # 从vt_setting读取数据库配置
        if "database.name" in vt_setting:
            db_config.name = vt_setting["database.name"]
        if "database.host" in vt_setting:
            db_config.host = vt_setting["database.host"]
        if "database.port" in vt_setting:
            db_config.port = int(vt_setting["database.port"])
        if "database.user" in vt_setting:
            db_config.user = vt_setting["database.user"]
        if "database.password" in vt_setting:
            db_config.password = vt_setting["database.password"]
        if "database.database" in vt_setting:
            db_config.database = vt_setting["database.database"]
        if "database.timezone" in vt_setting:
            db_config.timezone = vt_setting["database.timezone"]
        
        # 环境变量覆盖vt_setting
        if "database_host" in env_config:
            db_config.host = env_config["database_host"]
        if "database_port" in env_config:
            db_config.port = int(env_config["database_port"])
        if "database_user" in env_config:
            db_config.user = env_config["database_user"]
        if "database_password" in env_config:
            db_config.password = env_config["database_password"]
        if "database_name" in env_config:
            db_config.database = env_config["database_name"]
            
        return db_config
    
    def create_app_config(self, env_config: Dict[str, Any]) -> LegacyAppSettings:
        """创建应用配置"""
        app_config = LegacyAppSettings()
        
        if "debug" in env_config:
            app_config.debug = env_config["debug"].lower() in ('true', '1', 'yes')
        if "testing" in env_config:
            app_config.testing = env_config["testing"].lower() in ('true', '1', 'yes')
        if "log_level" in env_config:
            app_config.log_level = env_config["log_level"].upper()
        if "secret_key" in env_config:
            app_config.secret_key = env_config["secret_key"]
        if "api_prefix" in env_config:
            app_config.api_prefix = env_config["api_prefix"]
        if "docs_url" in env_config:
            app_config.docs_url = env_config["docs_url"]
        if "redoc_url" in env_config:
            app_config.redoc_url = env_config["redoc_url"]
            
        return app_config
    
    def create_service_config(self, env_config: Dict[str, Any]) -> LegacyServiceSettings:
        """创建服务配置"""
        service_config = LegacyServiceSettings()
        
        if "redis_host" in env_config:
            service_config.redis_host = env_config["redis_host"]
        if "redis_port" in env_config:
            service_config.redis_port = int(env_config["redis_port"])
        if "redis_password" in env_config:
            service_config.redis_password = env_config["redis_password"]
        if "redis_db" in env_config:
            service_config.redis_db = int(env_config["redis_db"])
        if "redis_url" in env_config:
            service_config.redis_url = env_config["redis_url"]
            
        if "jwt_secret_key" in env_config:
            service_config.jwt_secret_key = env_config["jwt_secret_key"]
        if "jwt_algorithm" in env_config:
            service_config.jwt_algorithm = env_config["jwt_algorithm"]
        if "jwt_access_token_expire_minutes" in env_config:
            service_config.jwt_access_token_expire_minutes = int(env_config["jwt_access_token_expire_minutes"])
        if "jwt_refresh_token_expire_days" in env_config:
            service_config.jwt_refresh_token_expire_days = int(env_config["jwt_refresh_token_expire_days"])
            
        if "cors_origins" in env_config:
            service_config.cors_origins = env_config["cors_origins"].split(',')
        if "allowed_hosts" in env_config:
            service_config.allowed_hosts = env_config["allowed_hosts"].split(',')
            
        # 构建Redis URL（如果没有直接配置）
        if not service_config.redis_url:
            if service_config.redis_password:
                service_config.redis_url = f"redis://:{service_config.redis_password}@{service_config.redis_host}:{service_config.redis_port}/{service_config.redis_db}"
            else:
                service_config.redis_url = f"redis://{service_config.redis_host}:{service_config.redis_port}/{service_config.redis_db}"
        
        return service_config
    
    def integrate_all_configs(self) -> Dict[str, Any]:
        """整合所有配置"""
        logger.info("开始整合Legacy配置...")
        
        # 1. 加载各种配置源
        vt_setting = self.load_vt_setting()
        env_config = self.load_env_config()
        
        # 2. 创建结构化配置
        database_config = self.create_database_config(vt_setting, env_config)
        app_config = self.create_app_config(env_config)
        service_config = self.create_service_config(env_config)
        
        # 3. 获取VnPy路径配置
        vnpy_paths = {}
        try:
            vnpy_paths = self.vnpy_integration.get_paths_dict()
        except Exception as e:
            logger.warning(f"获取VnPy路径配置失败: {e}")
        
        # 4. 构建最终配置字典
        integrated_config = {
            'legacy_integration': {
                'loaded': True,
                'sources': {
                    'vt_setting': bool(vt_setting),
                    'env_config': bool(env_config)
                },
                'timestamp': str(datetime.now())
            },
            'database': asdict(database_config),
            'app': asdict(app_config),
            'services': asdict(service_config),
            'vnpy_paths': vnpy_paths
        }
        
        logger.info("Legacy配置整合完成")
        return integrated_config
    
    def get_database_url(self, db_config: Optional[LegacyDatabaseSettings] = None) -> str:
        """获取数据库URL"""
        if db_config is None:
            config = self.integrate_all_configs()
            db_config = LegacyDatabaseSettings(**config['database'])
        
        if db_config.name.lower() == "mysql":
            return f"mysql+pymysql://{db_config.user}:{db_config.password}@{db_config.host}:{db_config.port}/{db_config.database}?charset={db_config.charset}"
        elif db_config.name.lower() == "postgresql":
            return f"postgresql+asyncpg://{db_config.user}:{db_config.password}@{db_config.host}:{db_config.port}/{db_config.database}"
        elif db_config.name.lower() == "sqlite":
            return f"sqlite:///{db_config.database}.db"
        else:
            return f"mysql+pymysql://{db_config.user}:{db_config.password}@{db_config.host}:{db_config.port}/{db_config.database}"
    
    def get_redis_url(self, service_config: Optional[LegacyServiceSettings] = None) -> str:
        """获取Redis URL"""
        if service_config is None:
            config = self.integrate_all_configs()
            service_config = LegacyServiceSettings(**config['services'])
        
        return service_config.redis_url


# 全局Legacy配置整合器实例
_legacy_integrator: Optional[LegacyConfigIntegrator] = None


def get_legacy_integrator() -> LegacyConfigIntegrator:
    """获取全局Legacy配置整合器实例"""
    global _legacy_integrator
    if _legacy_integrator is None:
        _legacy_integrator = LegacyConfigIntegrator()
    return _legacy_integrator


def integrate_legacy_config() -> Dict[str, Any]:
    """整合Legacy配置的便捷函数"""
    return get_legacy_integrator().integrate_all_configs()


def get_database_url() -> str:
    """获取数据库URL的便捷函数"""
    return get_legacy_integrator().get_database_url()


def get_redis_url() -> str:
    """获取Redis URL的便捷函数"""
    return get_legacy_integrator().get_redis_url()
