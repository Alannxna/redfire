"""
Legacy配置整合器

将After服务的legacy配置系统整合到Backend的统一配置管理中
"""

import os
import json
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, asdict
from datetime import datetime

from .base_config import BaseConfig, ConfigMetadata
from .config_manager import LegacyConfigManager
from ..infrastructure.exceptions import ConfigurationError
from pydantic import Field, validator

logger = logging.getLogger(__name__)


@dataclass
class LegacyPaths:
    """Legacy路径配置"""
    vnpy_core: str
    vnpy_framework: str
    vnpy_config: str
    vnpy_data: str
    vnpy_logs: str
    project_root: str
    after_root: str
    backend_root: str


@dataclass
class DatabaseSettings:
    """数据库设置（从After迁移）"""
    name: str = "mysql"
    host: str = "127.0.0.1"
    port: int = 3306
    user: str = "root"
    password: str = "root"
    database: str = "vnpy"
    timezone: str = "Asia/Shanghai"
    charset: str = "utf8mb4"
    
    def to_sqlalchemy_url(self) -> str:
        """转换为SQLAlchemy连接URL"""
        return (
            f"{self.name}://{self.user}:{self.password}@"
            f"{self.host}:{self.port}/{self.database}"
            f"?charset={self.charset}&timezone={self.timezone}"
        )


@dataclass
class AppSettings:
    """应用设置（从After迁移）"""
    debug: bool = True
    log_level: str = "INFO"
    host: str = "0.0.0.0"
    port: int = 8000
    secret_key: str = "vnpy-secret-key"
    timezone: str = "Asia/Shanghai"
    language: str = "zh_CN"


@dataclass
class RedisSettings:
    """Redis设置（从After迁移）"""
    host: str = "127.0.0.1"
    port: int = 6379
    password: str = ""
    database: int = 0
    max_connections: int = 10
    socket_timeout: int = 5


class LegacyConfig(BaseConfig):
    """Legacy配置类"""
    
    # 配置名称
    name: str = Field(default="legacy_config", description="Legacy配置名称")
    
    # 路径配置
    paths: Optional[Dict[str, str]] = Field(default=None, description="路径配置")
    
    # 数据库配置
    database: Dict[str, Any] = Field(default_factory=dict, description="数据库配置")
    
    # 应用配置
    app: Dict[str, Any] = Field(default_factory=dict, description="应用配置")
    
    # Redis配置
    redis: Dict[str, Any] = Field(default_factory=dict, description="Redis配置")
    
    # VnPy设置
    vt_settings: Dict[str, Any] = Field(default_factory=dict, description="VnPy设置")
    
    # 环境变量配置
    env_settings: Dict[str, Any] = Field(default_factory=dict, description="环境变量配置")
    
    # 服务配置
    services: Dict[str, Any] = Field(default_factory=dict, description="服务配置")
    
    def _create_metadata(self) -> ConfigMetadata:
        """创建配置元数据"""
        return ConfigMetadata(
            name=self.name,
            version="1.0.0",
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            source="legacy_integration"
        )
    
    def validate_config(self) -> bool:
        """验证配置的有效性"""
        try:
            # 验证路径配置
            if self.paths:
                for key, path in self.paths.items():
                    if not path or not isinstance(path, str):
                        logger.warning(f"无效的路径配置: {key} = {path}")
            
            # 验证数据库配置
            if self.database:
                required_db_fields = ["host", "port", "user", "database"]
                for field in required_db_fields:
                    if field not in self.database:
                        logger.warning(f"缺少数据库配置字段: {field}")
            
            return True
            
        except Exception as e:
            logger.error(f"配置验证失败: {e}")
            return False


class LegacyConfigIntegrator:
    """Legacy配置整合器"""
    
    def __init__(self, config_manager: Optional[LegacyConfigManager] = None):
        self.config_manager = config_manager or LegacyConfigManager()
        self.legacy_config: Optional[LegacyConfig] = None
        self.paths: Optional[LegacyPaths] = None
        self._integration_complete = False
        
        logger.info("Legacy配置整合器初始化完成")
    
    def integrate_legacy_configuration(self) -> LegacyConfig:
        """整合Legacy配置"""
        try:
            logger.info("开始整合Legacy配置...")
            
            # 1. 设置路径
            self._setup_paths()
            
            # 2. 创建Legacy配置对象
            self.legacy_config = LegacyConfig()
            
            # 3. 加载路径配置
            self.legacy_config.paths = asdict(self.paths)
            
            # 4. 加载VnPy设置
            vt_settings = self._load_vt_setting()
            self.legacy_config.vt_settings = vt_settings
            
            # 5. 加载环境配置
            env_config = self._load_env_config()
            self.legacy_config.env_settings = env_config
            
            # 6. 解析数据库配置
            db_config = self._parse_database_config(vt_settings, env_config)
            self.legacy_config.database = asdict(db_config)
            
            # 7. 解析应用配置
            app_config = self._parse_app_config(env_config)
            self.legacy_config.app = asdict(app_config)
            
            # 8. 解析Redis配置
            redis_config = self._parse_redis_config(vt_settings, env_config)
            self.legacy_config.redis = asdict(redis_config)
            
            # 9. 加载服务配置
            service_config = self._load_service_config()
            self.legacy_config.services = service_config
            
            # 10. 验证配置
            if not self.legacy_config.validate_config():
                logger.warning("Legacy配置验证失败，但继续使用")
            
            # 11. 整合到配置管理器
            self._integrate_to_config_manager()
            
            self._integration_complete = True
            logger.info("Legacy配置整合完成")
            
            return self.legacy_config
            
        except Exception as e:
            logger.error(f"Legacy配置整合失败: {e}")
            raise ConfigurationError(f"Legacy配置整合失败: {e}")
    
    def _setup_paths(self):
        """设置路径配置"""
        try:
            # 获取当前文件路径
            current_file = Path(__file__).resolve()
            backend_root = current_file.parents[3]  # backend目录
            project_root = backend_root.parent      # vnpy项目根目录
            
            # 检查是否在vnpy项目结构中
            if not (project_root / "vnpy").exists() and not (project_root / "vnpy-core").exists():
                # 如果不在标准结构中，尝试向上查找
                search_path = project_root
                for _ in range(3):  # 最多向上查找3层
                    search_path = search_path.parent
                    if (search_path / "vnpy").exists() or (search_path / "vnpy-core").exists():
                        project_root = search_path
                        break
            
            # 构建路径配置
            paths_dict = {
                "vnpy_core": os.getenv("VNPY_CORE_PATH", str(project_root / "vnpy-core")),
                "vnpy_framework": os.getenv("VNPY_FRAMEWORK_PATH", str(project_root / "vnpy")),
                "vnpy_config": os.getenv("VNPY_CONFIG_PATH", str(project_root / "config")),
                "vnpy_data": os.getenv("VNPY_DATA_PATH", str(project_root / "vnpy_data")),
                "vnpy_logs": os.getenv("VNPY_LOG_PATH", str(project_root / "vnpy_logs")),
                "project_root": str(project_root),
                "after_root": os.getenv("AFTER_ROOT_PATH", str(project_root / "After")),
                "backend_root": str(backend_root)
            }
            
            self.paths = LegacyPaths(**paths_dict)
            
            # 创建必要的目录
            self._ensure_directories()
            
            logger.info("路径配置设置完成")
            logger.info(f"项目根目录: {self.paths.project_root}")
            logger.info(f"Backend根目录: {self.paths.backend_root}")
            
        except Exception as e:
            logger.error(f"路径设置失败: {e}")
            raise ConfigurationError(f"路径设置失败: {e}")
    
    def _ensure_directories(self):
        """确保必要的目录存在"""
        if not self.paths:
            return
        
        directories_to_create = [
            self.paths.vnpy_data,
            self.paths.vnpy_logs,
            self.paths.vnpy_config
        ]
        
        for dir_path in directories_to_create:
            try:
                Path(dir_path).mkdir(parents=True, exist_ok=True)
                logger.debug(f"目录已确保存在: {dir_path}")
            except Exception as e:
                logger.warning(f"创建目录失败: {dir_path} - {e}")
    
    def _load_vt_setting(self) -> Dict[str, Any]:
        """加载VnPy设置文件"""
        vt_settings = {}
        
        if not self.paths:
            return vt_settings
        
        # 可能的vt_setting.json位置
        possible_locations = [
            Path(self.paths.vnpy_config) / "vt_setting.json",
            Path(self.paths.project_root) / "vt_setting.json",
            Path(self.paths.project_root) / "config" / "vt_setting.json",
            Path(self.paths.after_root) / "vt_setting.json" if Path(self.paths.after_root).exists() else None
        ]
        
        for location in possible_locations:
            if location and location.exists():
                try:
                    with open(location, 'r', encoding='utf-8') as f:
                        vt_settings.update(json.load(f))
                    logger.info(f"已加载VnPy设置: {location}")
                    break
                except Exception as e:
                    logger.warning(f"加载VnPy设置失败: {location} - {e}")
        
        # 如果没有找到设置文件，使用默认设置
        if not vt_settings:
            vt_settings = self._get_default_vt_settings()
            logger.info("使用默认VnPy设置")
        
        return vt_settings
    
    def _get_default_vt_settings(self) -> Dict[str, Any]:
        """获取默认VnPy设置"""
        return {
            "font.family": "微软雅黑",
            "font.size": 12,
            "log.active": True,
            "log.level": "INFO",
            "log.console": True,
            "log.file": True,
            "database.timezone": "Asia/Shanghai",
            "database.name": "mysql",
            "database.host": "127.0.0.1",
            "database.port": 3306,
            "database.user": "root",
            "database.password": "root",
            "database.database": "vnpy"
        }
    
    def _load_env_config(self) -> Dict[str, Any]:
        """加载环境变量配置"""
        env_config = {}
        
        if not self.paths:
            return env_config
        
        # 可能的.env文件位置
        possible_env_files = [
            Path(self.paths.project_root) / ".env",
            Path(self.paths.project_root) / "config" / "config.env",
            Path(self.paths.project_root) / "config" / "backend" / "config.env",
            Path(self.paths.backend_root) / ".env",
            Path(self.paths.after_root) / ".env" if Path(self.paths.after_root).exists() else None
        ]
        
        for env_file in possible_env_files:
            if env_file and env_file.exists():
                try:
                    file_config = self._parse_env_file(env_file)
                    env_config.update(file_config)
                    logger.info(f"已加载环境配置: {env_file}")
                except Exception as e:
                    logger.warning(f"加载环境配置失败: {env_file} - {e}")
        
        # 加载系统环境变量
        system_env = self._load_system_env_vars()
        env_config.update(system_env)
        
        return env_config
    
    def _parse_env_file(self, env_file: Path) -> Dict[str, Any]:
        """解析环境配置文件"""
        config = {}
        
        try:
            with open(env_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    
                    # 跳过空行和注释行
                    if not line or line.startswith('#'):
                        continue
                    
                    # 解析键值对
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip().strip('"').strip("'")
                        
                        # 转换为合适的类型
                        config[key] = self._parse_env_value(value)
                    else:
                        logger.warning(f"环境文件格式错误 {env_file}:{line_num}: {line}")
                        
        except Exception as e:
            logger.error(f"解析环境文件失败: {env_file} - {e}")
            
        return config
    
    def _load_system_env_vars(self) -> Dict[str, Any]:
        """加载系统环境变量"""
        config = {}
        
        # 加载以VNPY_开头的环境变量
        vnpy_prefix = "VNPY_"
        for key, value in os.environ.items():
            if key.startswith(vnpy_prefix):
                config_key = key[len(vnpy_prefix):].lower()
                config[config_key] = self._parse_env_value(value)
        
        # 加载其他重要的环境变量
        important_env_vars = [
            "DATABASE_URL", "REDIS_URL", "SECRET_KEY", "DEBUG",
            "LOG_LEVEL", "HOST", "PORT", "ENVIRONMENT"
        ]
        
        for var in important_env_vars:
            if var in os.environ:
                config[var.lower()] = self._parse_env_value(os.environ[var])
        
        return config
    
    def _parse_env_value(self, value: str) -> Union[str, int, float, bool]:
        """解析环境变量值"""
        if not value:
            return ""
        
        # 布尔值
        if value.lower() in ('true', 'false'):
            return value.lower() == 'true'
        
        # 数字
        try:
            if '.' in value:
                return float(value)
            else:
                return int(value)
        except ValueError:
            pass
        
        return value
    
    def _parse_database_config(self, vt_settings: Dict[str, Any], env_config: Dict[str, Any]) -> DatabaseSettings:
        """解析数据库配置"""
        # 优先级：环境变量 > VnPy设置 > 默认值
        
        # 从环境变量获取
        db_config = {
            "name": env_config.get("database_driver", "mysql"),
            "host": env_config.get("database_host", "127.0.0.1"),
            "port": int(env_config.get("database_port", 3306)),
            "user": env_config.get("database_user", "root"),
            "password": env_config.get("database_password", "root"),
            "database": env_config.get("database_name", "vnpy"),
            "timezone": env_config.get("database_timezone", "Asia/Shanghai"),
            "charset": env_config.get("database_charset", "utf8mb4")
        }
        
        # 从VnPy设置覆盖
        if "database.name" in vt_settings:
            db_config["name"] = vt_settings["database.name"]
        if "database.host" in vt_settings:
            db_config["host"] = vt_settings["database.host"]
        if "database.port" in vt_settings:
            db_config["port"] = int(vt_settings["database.port"])
        if "database.user" in vt_settings:
            db_config["user"] = vt_settings["database.user"]
        if "database.password" in vt_settings:
            db_config["password"] = vt_settings["database.password"]
        if "database.database" in vt_settings:
            db_config["database"] = vt_settings["database.database"]
        if "database.timezone" in vt_settings:
            db_config["timezone"] = vt_settings["database.timezone"]
        
        return DatabaseSettings(**db_config)
    
    def _parse_app_config(self, env_config: Dict[str, Any]) -> AppSettings:
        """解析应用配置"""
        app_config = {
            "debug": env_config.get("debug", True),
            "log_level": env_config.get("log_level", "INFO"),
            "host": env_config.get("host", "0.0.0.0"),
            "port": int(env_config.get("port", 8000)),
            "secret_key": env_config.get("secret_key", "vnpy-secret-key"),
            "timezone": env_config.get("timezone", "Asia/Shanghai"),
            "language": env_config.get("language", "zh_CN")
        }
        
        return AppSettings(**app_config)
    
    def _parse_redis_config(self, vt_settings: Dict[str, Any], env_config: Dict[str, Any]) -> RedisSettings:
        """解析Redis配置"""
        redis_config = {
            "host": env_config.get("redis_host", "127.0.0.1"),
            "port": int(env_config.get("redis_port", 6379)),
            "password": env_config.get("redis_password", ""),
            "database": int(env_config.get("redis_database", 0)),
            "max_connections": int(env_config.get("redis_max_connections", 10)),
            "socket_timeout": int(env_config.get("redis_socket_timeout", 5))
        }
        
        return RedisSettings(**redis_config)
    
    def _load_service_config(self) -> Dict[str, Any]:
        """加载服务配置"""
        service_config = {}
        
        if not self.paths:
            return service_config
        
        # 尝试加载服务配置文件
        config_files = [
            Path(self.paths.vnpy_config) / "service_config.json",
            Path(self.paths.vnpy_config) / "service_config.yaml",
            Path(self.paths.project_root) / "config" / "service_config.yaml"
        ]
        
        for config_file in config_files:
            if config_file.exists():
                try:
                    if config_file.suffix == '.json':
                        with open(config_file, 'r', encoding='utf-8') as f:
                            service_config.update(json.load(f))
                    elif config_file.suffix in ['.yaml', '.yml']:
                        with open(config_file, 'r', encoding='utf-8') as f:
                            service_config.update(yaml.safe_load(f))
                    
                    logger.info(f"已加载服务配置: {config_file}")
                    break
                    
                except Exception as e:
                    logger.warning(f"加载服务配置失败: {config_file} - {e}")
        
        # 默认服务配置
        if not service_config:
            service_config = self._get_default_service_config()
        
        return service_config
    
    def _get_default_service_config(self) -> Dict[str, Any]:
        """获取默认服务配置"""
        return {
            "chart_service": {
                "enabled": True,
                "port": 8001,
                "max_connections": 100
            },
            "research_service": {
                "enabled": True,
                "port": 8002,
                "cache_size": 1000
            },
            "strategy_engine": {
                "enabled": True,
                "max_strategies": 50,
                "risk_check": True
            },
            "web_ui": {
                "enabled": True,
                "websocket_port": 8003,
                "static_files": True
            }
        }
    
    def _integrate_to_config_manager(self):
        """将Legacy配置整合到配置管理器"""
        if not self.legacy_config:
            return
        
        try:
            # 获取当前配置
            current_config = self.config_manager.get_config()
            
            # 添加Legacy配置到现有配置
            legacy_dict = self.legacy_config.to_dict()
            
            # 更新配置管理器中的相关配置
            self._update_database_config(current_config, legacy_dict.get("database", {}))
            self._update_app_config(current_config, legacy_dict.get("app", {}))
            self._update_redis_config(current_config, legacy_dict.get("redis", {}))
            self._update_paths_config(current_config, legacy_dict.get("paths", {}))
            
            # 保存更新后的配置
            self.config_manager.set_config(current_config)
            
            logger.info("Legacy配置已整合到配置管理器")
            
        except Exception as e:
            logger.error(f"整合配置到配置管理器失败: {e}")
    
    def _update_database_config(self, current_config, db_config: Dict[str, Any]):
        """更新数据库配置"""
        if hasattr(current_config, 'database') and db_config:
            for key, value in db_config.items():
                setattr(current_config.database, key, value)
    
    def _update_app_config(self, current_config, app_config: Dict[str, Any]):
        """更新应用配置"""
        if hasattr(current_config, 'environment') and app_config:
            for key, value in app_config.items():
                if hasattr(current_config.environment, key):
                    setattr(current_config.environment, key, value)
    
    def _update_redis_config(self, current_config, redis_config: Dict[str, Any]):
        """更新Redis配置"""
        if hasattr(current_config, 'redis') and redis_config:
            for key, value in redis_config.items():
                setattr(current_config.redis, key, value)
    
    def _update_paths_config(self, current_config, paths_config: Dict[str, Any]):
        """更新路径配置"""
        # 将路径信息添加到环境变量中
        if paths_config:
            for key, value in paths_config.items():
                env_var_name = f"VNPY_{key.upper()}"
                os.environ[env_var_name] = str(value)
    
    def get_integrated_config(self) -> Optional[LegacyConfig]:
        """获取整合后的配置"""
        return self.legacy_config
    
    def is_integration_complete(self) -> bool:
        """检查整合是否完成"""
        return self._integration_complete
    
    def export_legacy_config(self, output_path: Union[str, Path], format: str = "json") -> bool:
        """导出Legacy配置"""
        if not self.legacy_config:
            logger.error("没有可导出的Legacy配置")
            return False
        
        try:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            config_data = self.legacy_config.to_dict()
            
            if format.lower() == "json":
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(config_data, f, indent=2, ensure_ascii=False)
            elif format.lower() in ["yaml", "yml"]:
                with open(output_file, 'w', encoding='utf-8') as f:
                    yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True)
            else:
                logger.error(f"不支持的导出格式: {format}")
                return False
            
            logger.info(f"Legacy配置已导出到: {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"导出Legacy配置失败: {e}")
            return False


# 全局Legacy配置整合器实例
_legacy_integrator: Optional[LegacyConfigIntegrator] = None


def get_legacy_integrator() -> LegacyConfigIntegrator:
    """获取Legacy配置整合器实例"""
    global _legacy_integrator
    if _legacy_integrator is None:
        _legacy_integrator = LegacyConfigIntegrator()
    return _legacy_integrator


def integrate_legacy_config() -> LegacyConfig:
    """整合Legacy配置的便捷函数"""
    integrator = get_legacy_integrator()
    return integrator.integrate_legacy_configuration()


def get_legacy_config() -> Optional[LegacyConfig]:
    """获取已整合的Legacy配置"""
    integrator = get_legacy_integrator()
    return integrator.get_integrated_config()
