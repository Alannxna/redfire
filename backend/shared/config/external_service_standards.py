"""
外部微服务配置标准规范
=====================

符合新外部微服务架构的配置管理标准
"""

import os
from typing import Dict, Any, Optional
from pathlib import Path
from enum import Enum


class ServiceType(Enum):
    """微服务类型枚举"""
    # 核心业务微服务
    USER_SERVICE = "user"
    TRADING_SERVICE = "trading"
    STRATEGY_SERVICE = "strategy"
    MARKET_SERVICE = "market"
    RISK_SERVICE = "risk"
    NOTIFY_SERVICE = "notify"
    
    # 基础设施微服务
    CONFIG_SERVICE = "config"
    AUTH_SERVICE = "auth"
    LOG_SERVICE = "log"
    MONITOR_SERVICE = "monitor"
    
    # 外部集成服务
    VNPY_SERVICE = "vnpy"
    DATA_SERVICE = "data"
    PAYMENT_SERVICE = "payment"


class ExternalServiceConfigStandard:
    """外部微服务配置标准"""
    
    # 统一的配置路径约定
    CONFIG_BASE_PATH = "config"
    CONFIG_PATH_TEMPLATE = "{base}/{service}/{environment}/{name}.yaml"
    
    # 统一的环境变量前缀
    ENV_PREFIX = "REDFIRE"
    ENV_TEMPLATE = "{prefix}_{service}_{key}"
    
    # 配置服务地址
    DEFAULT_CONFIG_SERVICE_URL = "http://localhost:8001"
    DEFAULT_CONFIG_SERVICE_TOKEN = "redfire_config_token"
    
    # 配置优先级 (数字越大优先级越高)
    PRIORITY_SERVICE = 5    # 外部配置服务
    PRIORITY_DICT = 4       # 字典配置
    PRIORITY_REMOTE = 3     # 远程URL
    PRIORITY_ENV = 2        # 环境变量
    PRIORITY_FILE = 1       # 配置文件
    
    @classmethod
    def get_config_path(cls, 
                       service: str, 
                       name: str = "config", 
                       environment: str = None) -> str:
        """获取标准配置文件路径"""
        if environment is None:
            environment = os.getenv('REDFIRE_ENVIRONMENT', 'development')
            
        return cls.CONFIG_PATH_TEMPLATE.format(
            base=cls.CONFIG_BASE_PATH,
            service=service,
            environment=environment,
            name=name
        )
    
    @classmethod
    def get_env_var_name(cls, service: str, key: str) -> str:
        """获取标准环境变量名"""
        return cls.ENV_TEMPLATE.format(
            prefix=cls.ENV_PREFIX,
            service=service.upper(),
            key=key.upper()
        )
    
    @classmethod
    def get_service_config_url(cls, service: str, config_name: str = "config") -> str:
        """获取配置服务API URL"""
        base_url = os.getenv('REDFIRE_CONFIG_SERVICE_URL', cls.DEFAULT_CONFIG_SERVICE_URL)
        return f"{base_url}/config/{service}/{config_name}"


class ExternalServiceDirectoryStandard:
    """外部微服务目录结构标准"""
    
    @staticmethod
    def get_service_structure() -> Dict[str, Any]:
        """获取标准微服务目录结构"""
        return {
            "microservices": {
                "user_service": {
                    "path": "services/user",
                    "config_path": "config/user",
                    "api_prefix": "/api/v1/user",
                    "port": 8010
                },
                "trading_service": {
                    "path": "services/trading",
                    "config_path": "config/trading",
                    "api_prefix": "/api/v1/trading",
                    "port": 8020
                },
                "strategy_service": {
                    "path": "services/strategy",
                    "config_path": "config/strategy", 
                    "api_prefix": "/api/v1/strategy",
                    "port": 8030
                },
                "market_service": {
                    "path": "services/market",
                    "config_path": "config/market",
                    "api_prefix": "/api/v1/market",
                    "port": 8040
                },
                "config_service": {
                    "path": "services/config",
                    "config_path": "config/config",
                    "api_prefix": "/api/v1/config",
                    "port": 8001
                },
                "auth_service": {
                    "path": "services/auth",
                    "config_path": "config/auth",
                    "api_prefix": "/api/v1/auth",
                    "port": 8002
                },
                "vnpy_service": {
                    "path": "services/vnpy",
                    "config_path": "config/vnpy",
                    "api_prefix": "/api/v1/vnpy",
                    "port": 8050
                }
            }
        }
    
    @staticmethod
    def get_config_directory_structure() -> Dict[str, Any]:
        """获取配置目录结构标准"""
        return {
            "config": {
                "user": {
                    "development": ["config.yaml", "database.yaml"],
                    "testing": ["config.yaml", "database.yaml"],
                    "production": ["config.yaml", "database.yaml"]
                },
                "trading": {
                    "development": ["config.yaml", "vnpy.yaml", "risk.yaml"],
                    "testing": ["config.yaml", "vnpy.yaml", "risk.yaml"], 
                    "production": ["config.yaml", "vnpy.yaml", "risk.yaml"]
                },
                "strategy": {
                    "development": ["config.yaml", "vnpy.yaml"],
                    "testing": ["config.yaml", "vnpy.yaml"],
                    "production": ["config.yaml", "vnpy.yaml"]
                },
                "shared": {
                    "development": ["database.yaml", "redis.yaml", "logging.yaml"],
                    "testing": ["database.yaml", "redis.yaml", "logging.yaml"],
                    "production": ["database.yaml", "redis.yaml", "logging.yaml"]
                }
            }
        }


class ConfigMigrationHelper:
    """配置迁移助手"""
    
    @staticmethod
    def migrate_legacy_path_to_standard(legacy_path: str, service: str) -> str:
        """将Legacy路径迁移到标准路径"""
        mapping = {
            "backend/legacy/core/config/config_manager.py": f"config/{service}/development/config.yaml",
            "backend/core/config/config_manager.py": f"config/{service}/production/config.yaml",
            "backend/config_service/config/app.yaml": f"config/{service}/development/config.yaml",
            "config/backend/app_config.py": f"config/{service}/development/config.yaml",
        }
        return mapping.get(legacy_path, f"config/{service}/development/config.yaml")
    
    @staticmethod
    def migrate_legacy_env_to_standard(legacy_env: str, service: str) -> str:
        """将Legacy环境变量迁移到标准格式"""
        # 移除常见前缀并标准化
        cleaned = legacy_env.replace("APP_", "").replace("CONFIG_", "").replace("VNPY_", "")
        return ExternalServiceConfigStandard.get_env_var_name(service, cleaned)


def validate_service_config_compliance(service: str, config_data: Dict[str, Any]) -> Dict[str, Any]:
    """验证服务配置是否符合外部微服务标准"""
    
    validation_result = {
        "compliant": True,
        "issues": [],
        "recommendations": []
    }
    
    # 检查必需的配置项
    required_fields = {
        "app": ["name", "version", "environment"],
        "database": ["host", "port", "name"],
        "logging": ["level", "format"]
    }
    
    for category, fields in required_fields.items():
        if category in config_data:
            category_config = config_data[category]
            for field in fields:
                if field not in category_config:
                    validation_result["compliant"] = False
                    validation_result["issues"].append(
                        f"缺少必需配置项: {category}.{field}"
                    )
    
    # 检查环境变量命名规范
    if "environment_variables" in config_data:
        for env_var in config_data["environment_variables"]:
            if not env_var.startswith(f"{ExternalServiceConfigStandard.ENV_PREFIX}_{service.upper()}_"):
                validation_result["recommendations"].append(
                    f"环境变量 {env_var} 建议使用标准前缀: {ExternalServiceConfigStandard.ENV_PREFIX}_{service.upper()}_"
                )
    
    # 检查配置服务集成
    if "config_service" not in config_data:
        validation_result["recommendations"].append(
            "建议添加配置服务集成设置"
        )
    
    return validation_result


def generate_service_config_template(service: str, environment: str = "development") -> Dict[str, Any]:
    """生成符合标准的服务配置模板"""
    
    template = {
        "app": {
            "name": f"{service}_service",
            "version": "1.0.0",
            "environment": environment,
            "service_type": service,
            "port": ExternalServiceDirectoryStandard.get_service_structure()["microservices"].get(
                f"{service}_service", {}
            ).get("port", 8000)
        },
        "config_service": {
            "url": ExternalServiceConfigStandard.DEFAULT_CONFIG_SERVICE_URL,
            "token": ExternalServiceConfigStandard.DEFAULT_CONFIG_SERVICE_TOKEN,
            "enabled": True,
            "cache_ttl": 300
        },
        "database": {
            "host": "${REDFIRE_" + service.upper() + "_DB_HOST:localhost}",
            "port": "${REDFIRE_" + service.upper() + "_DB_PORT:5432}",
            "name": "${REDFIRE_" + service.upper() + "_DB_NAME:" + service + "_db}",
            "user": "${REDFIRE_" + service.upper() + "_DB_USER:" + service + "_user}",
            "password": "${REDFIRE_" + service.upper() + "_DB_PASSWORD}",
            "pool_size": 20,
            "max_overflow": 10
        },
        "redis": {
            "host": "${REDFIRE_" + service.upper() + "_REDIS_HOST:localhost}",
            "port": "${REDFIRE_" + service.upper() + "_REDIS_PORT:6379}",
            "db": "${REDFIRE_" + service.upper() + "_REDIS_DB:0}",
            "password": "${REDFIRE_" + service.upper() + "_REDIS_PASSWORD}",
            "pool_size": 10
        },
        "logging": {
            "level": "${REDFIRE_" + service.upper() + "_LOG_LEVEL:INFO}",
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "file": f"logs/{service}_service.log",
            "max_size": "100MB",
            "backup_count": 5
        },
        "monitoring": {
            "metrics_enabled": True,
            "health_check_path": "/health",
            "prometheus_port": "${REDFIRE_" + service.upper() + "_METRICS_PORT:9090}"
        }
    }
    
    # 为特定服务添加专用配置
    if service == "trading":
        template["vnpy"] = {
            "config_path": "config/vnpy/development/config.yaml",
            "data_path": "data/vnpy",
            "log_path": "logs/vnpy"
        }
        template["risk"] = {
            "max_position": 1000000,
            "max_daily_loss": 50000,
            "risk_check_interval": 5
        }
    
    elif service == "strategy":
        template["strategy"] = {
            "strategy_path": "strategies",
            "backtest_data_path": "data/backtest",
            "live_trading": False
        }
    
    elif service == "market":
        template["market_data"] = {
            "sources": ["ctp", "ib", "okex"],
            "cache_size": 10000,
            "update_interval": 1
        }
    
    return template


# 导出标准配置
EXTERNAL_SERVICE_CONFIG = ExternalServiceConfigStandard()
EXTERNAL_SERVICE_DIRECTORY = ExternalServiceDirectoryStandard()
