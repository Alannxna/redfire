"""
统一配置管理器
==============

整合所有配置模块，提供统一的配置接口。
"""

import os
import sys
import json
from typing import Dict, Any, Optional, Type, List
from pathlib import Path
from datetime import datetime

try:
    from pydantic import BaseModel, Field
except ImportError:
    # 简单的替代实现
    class Field:
        def __init__(self, *args, **kwargs):
            pass
    class BaseModel:
        pass

try:
    from loguru import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

from .base_config import BaseConfig, ConfigMetadata
from .environment_config import EnvironmentConfig, get_environment_config
# 延迟导入以避免循环依赖
# from .legacy_config_integrator import LegacyConfigIntegrator, integrate_legacy_config, get_legacy_config
from .environment_manager import EnvironmentManager, get_environment_manager
from .vnpy_integration_config import VnPyIntegrationConfig, get_vnpy_integration_config

# 导入现有配置模块
try:
    from config.backend.app_config import AppConfig
    from config.backend.database_config import DatabaseConfig
    from config.backend.path_config import PathConfig
    from config.backend.service_config import ServiceRegistry
    HAS_LEGACY_CONFIGS = True
except ImportError:
    logger.warning("无法导入现有配置模块，将使用默认配置")
    HAS_LEGACY_CONFIGS = False


class DatabaseSettings(BaseModel):
    """数据库配置设置"""
    db_type: str = "mysql"
    host: str = "localhost"
    port: int = 3306
    username: str = "root"
    password: str = "root"
    database: str = "vnpy"
    charset: str = "utf8mb4"
    echo: bool = False
    
    def build_connection_url(self) -> str:
        """构建数据库连接URL"""
        if self.db_type.lower() == "mysql":
            return f"mysql+pymysql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}?charset={self.charset}"
        elif self.db_type.lower() == "sqlite":
            return f"sqlite:///{self.database}"
        else:
            raise ValueError(f"不支持的数据库类型: {self.db_type}")


class PathSettings(BaseModel):
    """路径配置设置"""
    project_root: str
    data_dir: str
    logs_dir: str
    temp_dir: str
    uploads_dir: str
    vnpy_data_dir: str
    vnpy_config_dir: str
    
    def get_log_file_path(self) -> str:
        """获取日志文件路径"""
        return str(Path(self.logs_dir) / "vnpy_web.log")
    
    def get_vnpy_data_path(self) -> str:
        """获取VnPy数据路径"""
        return self.vnpy_data_dir
    
    def get_upload_path(self) -> str:
        """获取上传路径"""
        return self.uploads_dir


class ServiceSettings(BaseModel):
    """服务配置设置"""
    vnpy_core_port: int = 8006
    user_trading_port: int = 8001
    strategy_data_port: int = 8002
    gateway_port: int = 8004
    monitor_port: int = 8005
    service_host: str = "0.0.0.0"
    api_host: str = "127.0.0.1"
    
    def get_service_port(self, service_name: str) -> Optional[int]:
        """获取服务端口"""
        port_map = {
            "vnpy_core": self.vnpy_core_port,
            "user_trading": self.user_trading_port,
            "strategy_data": self.strategy_data_port,
            "gateway": self.gateway_port,
            "monitor": self.monitor_port
        }
        return port_map.get(service_name)
    
    def get_service_url(self, service_name: str) -> Optional[str]:
        """获取服务URL"""
        port = self.get_service_port(service_name)
        if port:
            return f"http://{self.api_host}:{port}"
        return None


class UnifiedConfig(BaseConfig):
    """统一配置类"""
    
    # 配置文件路径
    config_file: Optional[str] = Field(default=None, description="配置文件路径")
    working_dir: str = Field(default_factory=lambda: str(Path.cwd()), description="工作目录")
    
    # 环境配置
    environment: EnvironmentConfig = Field(default_factory=get_environment_config)
    
    # 核心配置组件
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    paths: PathSettings = Field(default_factory=lambda: PathSettings(
        project_root=str(Path.cwd()),
        data_dir="./data",
        logs_dir="./logs",
        temp_dir="./temp",
        uploads_dir="./uploads",
        vnpy_data_dir="./vnpy_data",
        vnpy_config_dir="./vnpy_config"
    ))
    services: ServiceSettings = Field(default_factory=ServiceSettings)
    
    # 应用配置
    app_name: str = Field(default="VnPy Web", description="应用名称")
    app_version: str = Field(default="1.0.0", description="应用版本")
    host: str = Field(default="0.0.0.0", description="服务器主机")
    port: int = Field(default=8000, description="服务器端口")
    
    # JWT配置
    jwt_secret_key: str = Field(default="jwt-secret-key", description="JWT密钥")
    jwt_algorithm: str = Field(default="HS256", description="JWT算法")
    jwt_access_token_expire_minutes: int = Field(default=30, description="访问令牌过期时间")
    
    # Redis配置
    redis_url: str = Field(default="redis://localhost:6379/0", description="Redis连接URL")
    redis_host: str = Field(default="localhost", description="Redis主机")
    redis_port: int = Field(default=6379, description="Redis端口")
    redis_db: int = Field(default=0, description="Redis数据库")
    
    def __init__(self, **kwargs):
        # 初始化环境管理器
        self.env_manager = get_environment_manager()
        # 延迟导入避免循环依赖
        from .legacy_integration import LegacyConfigIntegrator
        self.legacy_integrator = LegacyConfigIntegrator()
        
        # 如果有现有配置，尝试从中加载
        if HAS_LEGACY_CONFIGS:
            self._load_from_legacy_configs(kwargs)
        
        super().__init__(**kwargs)
        
        # 整合Legacy配置
        self._integrate_legacy_config()
        
        # 整合环境变量
        self._integrate_environment_variables()
        
        self._ensure_paths_exist()
    
    def _load_from_legacy_configs(self, kwargs: Dict[str, Any]):
        """从现有配置模块加载配置"""
        try:
            # 加载应用配置
            app_config = AppConfig()
            kwargs.setdefault('app_name', app_config.app_name)
            kwargs.setdefault('app_version', app_config.app_version)
            kwargs.setdefault('host', app_config.host)
            kwargs.setdefault('port', app_config.port)
            kwargs.setdefault('jwt_secret_key', app_config.jwt_secret_key)
            kwargs.setdefault('redis_url', app_config.redis_url)
            
            # 加载数据库配置
            db_config = DatabaseConfig.from_env()
            kwargs.setdefault('database', DatabaseSettings(
                db_type=db_config.db_type.value,
                host=db_config.host or "localhost",
                port=db_config.port or 3306,
                username=db_config.username or "root",
                password=db_config.password or "root",
                database=db_config.database or "vnpy",
                charset=db_config.charset,
                echo=db_config.echo
            ))
            
            # 加载路径配置
            path_config = PathConfig()
            kwargs.setdefault('paths', PathSettings(
                project_root=str(path_config.project_root),
                data_dir=str(path_config.data_dir),
                logs_dir=str(path_config.logs_dir),
                temp_dir=str(path_config.temp_dir),
                uploads_dir=str(path_config.uploads_dir),
                vnpy_data_dir=str(path_config.vnpy_data_dir),
                vnpy_config_dir=str(path_config.vnpy_config_dir)
            ))
            
            # 加载服务配置
            service_registry = ServiceRegistry()
            port_config = service_registry.port_config
            kwargs.setdefault('services', ServiceSettings(
                vnpy_core_port=port_config.vnpy_core_port,
                user_trading_port=port_config.user_trading_port,
                strategy_data_port=port_config.strategy_data_port,
                gateway_port=port_config.gateway_port,
                monitor_port=port_config.monitor_port,
                service_host=port_config.service_host,
                api_host=port_config.api_host
            ))
            
        except Exception as e:
            logger.warning(f"从现有配置加载失败，使用默认配置: {e}")
    
    def _ensure_paths_exist(self):
        """确保必要的路径存在"""
        paths_to_create = [
            self.paths.data_dir,
            self.paths.logs_dir,
            self.paths.temp_dir,
            self.paths.uploads_dir,
            self.paths.vnpy_data_dir,
            self.paths.vnpy_config_dir
        ]
        
        for path_str in paths_to_create:
            path = Path(path_str)
            path.mkdir(parents=True, exist_ok=True)
    
    def _create_metadata(self) -> ConfigMetadata:
        """创建配置元数据"""
        return ConfigMetadata(
            name="unified_config",
            version="1.0.0",
            description="VnPy Web 统一配置管理",
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            source="unified"
        )
    
    def validate_config(self) -> bool:
        """验证配置有效性"""
        try:
            # 验证环境配置
            if not self.environment.validate_config():
                return False
            
            # 验证端口
            if not (1 <= self.port <= 65535):
                return False
            
            # 验证数据库配置
            try:
                self.database.build_connection_url()
            except Exception:
                return False
            
            # 验证路径
            if not self.paths.project_root:
                return False
            
            return True
            
        except Exception:
            return False
    
    def get_database_url(self) -> str:
        """获取数据库连接URL"""
        return self.database.build_connection_url()
    
    def get_service_config(self, service_name: str) -> Dict[str, Any]:
        """获取服务配置"""
        port = self.services.get_service_port(service_name)
        url = self.services.get_service_url(service_name)
        
        return {
            "name": service_name,
            "port": port,
            "url": url,
            "host": self.services.service_host,
            "api_host": self.services.api_host
        }
    
    def get_logging_config(self) -> Dict[str, Any]:
        """获取日志配置"""
        return {
            "level": self.environment.log_level,
            "format": self.environment.log_format,
            "file_path": self.paths.get_log_file_path(),
            "directory": self.paths.logs_dir
        }
    
    def get_security_config(self) -> Dict[str, Any]:
        """获取安全配置"""
        return {
            "secret_key": self.environment.secret_key,
            "jwt_secret_key": self.jwt_secret_key,
            "jwt_algorithm": self.jwt_algorithm,
            "jwt_expire_minutes": self.jwt_access_token_expire_minutes,
            "allowed_hosts": self.environment.allowed_hosts,
            "cors_origins": self.environment.cors_origins
        }
    
    def is_development(self) -> bool:
        """是否为开发环境"""
        return self.environment.is_development()
    
    def is_production(self) -> bool:
        """是否为生产环境"""
        return self.environment.is_production()
    
    def create_directories(self):
        """创建所有必需的目录"""
        self._ensure_paths_exist()
    
    def sync_with_legacy_configs(self):
        """与现有配置同步"""
        if not HAS_LEGACY_CONFIGS:
            return
        
        try:
            # 更新应用配置
            from config.backend.app_config import set_app_config
            app_config = AppConfig(
                app_name=self.app_name,
                app_version=self.app_version,
                host=self.host,
                port=self.port,
                jwt_secret_key=self.jwt_secret_key,
                redis_url=self.redis_url,
                debug=self.environment.debug
            )
            set_app_config(app_config)
            
            logger.info("已同步统一配置到现有配置系统")
            
        except Exception as e:
            logger.warning(f"同步配置失败: {e}")
    
    def export_to_env_file(self, file_path: str = ".env") -> bool:
        """导出配置到环境变量文件"""
        try:
            env_lines = [
                "# VnPy Web 统一配置文件",
                f"# 生成时间: {datetime.now().isoformat()}",
                "",
                "# === 应用配置 ===",
                f"APP_NAME={self.app_name}",
                f"APP_VERSION={self.app_version}",
                f"HOST={self.host}",
                f"PORT={self.port}",
                f"ENVIRONMENT={self.environment.environment.value}",
                f"DEBUG={str(self.environment.debug).lower()}",
                "",
                "# === 数据库配置 ===",
                f"DB_TYPE={self.database.db_type}",
                f"DB_HOST={self.database.host}",
                f"DB_PORT={self.database.port}",
                f"DB_USER={self.database.username}",
                f"DB_PASSWORD={self.database.password}",
                f"DB_NAME={self.database.database}",
                "",
                "# === Redis配置 ===",
                f"REDIS_URL={self.redis_url}",
                f"REDIS_HOST={self.redis_host}",
                f"REDIS_PORT={self.redis_port}",
                f"REDIS_DB={self.redis_db}",
                "",
                "# === JWT配置 ===",
                f"JWT_SECRET_KEY={self.jwt_secret_key}",
                f"JWT_ALGORITHM={self.jwt_algorithm}",
                f"JWT_ACCESS_TOKEN_EXPIRE_MINUTES={self.jwt_access_token_expire_minutes}",
                "",
                "# === 服务端口配置 ===",
                f"VNPY_CORE_PORT={self.services.vnpy_core_port}",
                f"USER_TRADING_PORT={self.services.user_trading_port}",
                f"STRATEGY_DATA_PORT={self.services.strategy_data_port}",
                f"GATEWAY_PORT={self.services.gateway_port}",
                f"MONITOR_PORT={self.services.monitor_port}",
                f"SERVICE_HOST={self.services.service_host}",
                f"API_HOST={self.services.api_host}",
                "",
                "# === 路径配置 ===",
                f"DATA_DIR={self.paths.data_dir}",
                f"LOGS_DIR={self.paths.logs_dir}",
                f"TEMP_DIR={self.paths.temp_dir}",
                f"UPLOADS_DIR={self.paths.uploads_dir}",
                f"VNPY_DATA_DIR={self.paths.vnpy_data_dir}",
                f"VNPY_CONFIG_DIR={self.paths.vnpy_config_dir}",
            ]
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(env_lines))
            
            logger.info(f"配置已导出到: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"导出配置失败: {e}")
            return False
    
    def _integrate_legacy_config(self):
        """整合Legacy配置"""
        try:
            # 使用legacy配置整合器
            legacy_config = self.legacy_integrator.integrate_all_configs()
            
            if legacy_config:
                # 更新数据库配置
                if 'database' in legacy_config:
                    db_config = legacy_config['database']
                    self.database.host = db_config.get('host', self.database.host)
                    self.database.port = db_config.get('port', self.database.port)
                    self.database.username = db_config.get('user', self.database.username)
                    self.database.password = db_config.get('password', self.database.password)
                    self.database.database = db_config.get('database', self.database.database)
                    self.database.db_type = db_config.get('name', self.database.db_type)
                
                # 更新应用配置
                if 'app' in legacy_config:
                    app_config = legacy_config['app']
                    self.environment.debug = app_config.get('debug', self.environment.debug)
                    self.environment.log_level = app_config.get('log_level', self.environment.log_level)
                    if 'secret_key' in app_config:
                        self.jwt_secret_key = app_config['secret_key']
                
                # 更新服务配置
                if 'services' in legacy_config:
                    services_config = legacy_config['services']
                    self.redis_host = services_config.get('redis_host', self.redis_host)
                    self.redis_port = services_config.get('redis_port', self.redis_port)
                    self.redis_db = services_config.get('redis_db', self.redis_db)
                    if 'redis_url' in services_config:
                        self.redis_url = services_config['redis_url']
                
                # 更新路径配置
                if 'vnpy_paths' in legacy_config:
                    paths_config = legacy_config['vnpy_paths']
                    if 'vnpy_data' in paths_config:
                        self.paths.vnpy_data_dir = paths_config['vnpy_data']
                    if 'vnpy_config' in paths_config:
                        self.paths.vnpy_config_dir = paths_config['vnpy_config']
                    if 'vnpy_logs' in paths_config:
                        self.paths.logs_dir = paths_config['vnpy_logs']
                
                logger.info("Legacy配置整合完成")
            
        except Exception as e:
            logger.warning(f"Legacy配置整合失败: {e}")
    
    def _integrate_environment_variables(self):
        """整合环境变量"""
        try:
            # 从环境变量更新配置
            self.app_name = self.env_manager.get_variable('APP_NAME', self.app_name)
            self.app_version = self.env_manager.get_variable('APP_VERSION', self.app_version)
            self.host = self.env_manager.get_variable('HOST', self.host)
            
            # 端口配置
            port_str = self.env_manager.get_variable('PORT')
            if port_str:
                try:
                    self.port = int(port_str)
                except ValueError:
                    logger.warning(f"无效的端口配置: {port_str}")
            
            # 数据库配置
            db_host = self.env_manager.get_variable('DATABASE_HOST')
            if db_host:
                self.database.host = db_host
            
            db_port = self.env_manager.get_variable('DATABASE_PORT')
            if db_port:
                try:
                    self.database.port = int(db_port)
                except ValueError:
                    logger.warning(f"无效的数据库端口: {db_port}")
            
            db_user = self.env_manager.get_variable('DATABASE_USER')
            if db_user:
                self.database.username = db_user
            
            db_password = self.env_manager.get_variable('DATABASE_PASSWORD')
            if db_password:
                self.database.password = db_password
            
            db_name = self.env_manager.get_variable('DATABASE_NAME')
            if db_name:
                self.database.database = db_name
            
            # Redis配置
            redis_host = self.env_manager.get_variable('REDIS_HOST')
            if redis_host:
                self.redis_host = redis_host
            
            redis_port = self.env_manager.get_variable('REDIS_PORT')
            if redis_port:
                try:
                    self.redis_port = int(redis_port)
                except ValueError:
                    logger.warning(f"无效的Redis端口: {redis_port}")
            
            redis_db = self.env_manager.get_variable('REDIS_DB')
            if redis_db:
                try:
                    self.redis_db = int(redis_db)
                except ValueError:
                    logger.warning(f"无效的Redis数据库: {redis_db}")
            
            # 更新Redis URL
            redis_url = self.env_manager.get_variable('REDIS_URL')
            if redis_url:
                self.redis_url = redis_url
            else:
                self.redis_url = f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"
            
            # JWT配置
            jwt_secret = self.env_manager.get_variable('JWT_SECRET_KEY')
            if jwt_secret:
                self.jwt_secret_key = jwt_secret
            
            # 环境配置
            environment = self.env_manager.get_variable('ENVIRONMENT')
            if environment:
                self.environment.environment = environment
            
            debug = self.env_manager.get_variable('DEBUG')
            if debug:
                self.environment.debug = debug.lower() in ('true', '1', 'yes', 'on')
            
            log_level = self.env_manager.get_variable('LOG_LEVEL')
            if log_level:
                self.environment.log_level = log_level
            
            logger.info("环境变量整合完成")
            
        except Exception as e:
            logger.warning(f"环境变量整合失败: {e}")
    
    def get_configuration_summary(self) -> Dict[str, Any]:
        """获取配置摘要"""
        return {
            "application": {
                "name": self.app_name,
                "version": self.app_version,
                "environment": self.environment.environment.value,
                "debug": self.environment.debug,
                "host": self.host,
                "port": self.port
            },
            "database": {
                "type": self.database.db_type,
                "host": self.database.host,
                "port": self.database.port,
                "database": self.database.database,
                "connection_url": "***" if self.database.password else self.get_database_url()
            },
            "redis": {
                "host": self.redis_host,
                "port": self.redis_port,
                "database": self.redis_db,
                "url": "***" if ":" in self.redis_url.split("@")[0] else self.redis_url
            },
            "paths": {
                "project_root": self.paths.project_root,
                "data_dir": self.paths.data_dir,
                "logs_dir": self.paths.logs_dir,
                "vnpy_data_dir": self.paths.vnpy_data_dir
            },
            "services": {
                "vnpy_core_port": self.services.vnpy_core_port,
                "user_trading_port": self.services.user_trading_port,
                "strategy_data_port": self.services.strategy_data_port
            },
            "legacy_integration": {
                "integrator_active": hasattr(self, 'legacy_integrator'),
                "env_manager_active": hasattr(self, 'env_manager')
            }
        }
    
    def reload_configuration(self) -> bool:
        """重新加载配置"""
        try:
            # 重新整合Legacy配置
            self._integrate_legacy_config()
            
            # 重新整合环境变量
            self._integrate_environment_variables()
            
            # 重新验证配置
            if not self.validate_config():
                logger.warning("配置重新加载后验证失败")
                return False
            
            logger.info("配置重新加载成功")
            return True
            
        except Exception as e:
            logger.error(f"配置重新加载失败: {e}")
            return False
    
    def export_legacy_compatible_config(self, output_dir: str = "./config_export") -> bool:
        """导出兼容Legacy系统的配置"""
        try:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            # 导出VnPy设置
            vt_settings = {
                "font.family": "微软雅黑",
                "font.size": 12,
                "log.active": True,
                "log.level": self.environment.log_level,
                "log.console": True,
                "log.file": True,
                "database.timezone": "Asia/Shanghai",
                "database.name": self.database.db_type,
                "database.host": self.database.host,
                "database.port": self.database.port,
                "database.user": self.database.username,
                "database.password": self.database.password,
                "database.database": self.database.database
            }
            
            import json
            with open(output_path / "vt_setting.json", 'w', encoding='utf-8') as f:
                json.dump(vt_settings, f, indent=2, ensure_ascii=False)
            
            # 导出环境配置
            self.export_to_env_file(str(output_path / "config.env"))
            
            # 如果有Legacy整合器，导出Legacy配置
            if hasattr(self, 'legacy_integrator'):
                try:
                    legacy_config = self.legacy_integrator.integrate_all_configs()
                    with open(output_path / "legacy_config.json", 'w', encoding='utf-8') as f:
                        json.dump(legacy_config, f, indent=2, ensure_ascii=False)
                except Exception as e:
                    logger.warning(f"导出Legacy配置失败: {e}")
            
            # 如果有环境管理器，导出环境配置档案
            if hasattr(self, 'env_manager'):
                for profile_name in self.env_manager.list_profiles():
                    profile_config = self.env_manager.export_environment(profile_name, "yaml")
                    with open(output_path / f"env_profile_{profile_name}.yaml", 'w', encoding='utf-8') as f:
                        f.write(profile_config)
            
            logger.info(f"配置已导出到: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"导出配置失败: {e}")
            return False
    
    def get_environment_profile_info(self) -> Dict[str, Any]:
        """获取环境配置档案信息"""
        if not hasattr(self, 'env_manager'):
            return {"error": "环境管理器未初始化"}
        
        return self.env_manager.get_statistics()
    
    def switch_environment_profile(self, profile_name: str) -> bool:
        """切换环境配置档案"""
        if not hasattr(self, 'env_manager'):
            logger.error("环境管理器未初始化")
            return False
        
        success = self.env_manager.set_active_profile(profile_name)
        if success:
            # 重新加载配置
            self.reload_configuration()
        
        return success
    
    def validate_full_configuration(self) -> Dict[str, Any]:
        """完整配置验证"""
        validation_result = {
            "overall_valid": True,
            "errors": [],
            "warnings": [],
            "components": {}
        }
        
        # 验证基础配置
        try:
            base_valid = self.validate_config()
            validation_result["components"]["base_config"] = {
                "valid": base_valid,
                "errors": [] if base_valid else ["基础配置验证失败"]
            }
            if not base_valid:
                validation_result["overall_valid"] = False
        except Exception as e:
            validation_result["components"]["base_config"] = {
                "valid": False,
                "errors": [str(e)]
            }
            validation_result["overall_valid"] = False
        
        # 验证环境管理器
        if hasattr(self, 'env_manager'):
            try:
                env_validation = self.env_manager.validate_environment()
                validation_result["components"]["environment"] = env_validation
                if not env_validation.get("valid", False):
                    validation_result["overall_valid"] = False
                    validation_result["errors"].extend(env_validation.get("errors", []))
                    validation_result["warnings"].extend(env_validation.get("warnings", []))
            except Exception as e:
                validation_result["components"]["environment"] = {
                    "valid": False,
                    "errors": [str(e)]
                }
                validation_result["overall_valid"] = False
        
        # 验证Legacy配置
        if hasattr(self, 'legacy_integrator'):
            try:
                legacy_config = self.legacy_integrator.integrate_all_configs()
                if legacy_config:
                    legacy_valid = True  # 简单验证，检查是否有必要的字段
                    if 'database' not in legacy_config:
                        legacy_valid = False
                    validation_result["components"]["legacy"] = {
                        "valid": legacy_valid,
                        "errors": [] if legacy_valid else ["Legacy配置缺少必要字段"]
                    }
                    if not legacy_valid:
                        validation_result["overall_valid"] = False
            except Exception as e:
                validation_result["components"]["legacy"] = {
                    "valid": False,
                    "errors": [str(e)]
                }
                validation_result["overall_valid"] = False
        
        return validation_result
    
    @classmethod
    def from_env_file(cls, file_path: str = ".env") -> 'UnifiedConfig':
        """从环境变量文件加载配置"""
        # 临时设置环境变量文件
        original_env_file = cls.model_config.get("env_file")
        cls.model_config["env_file"] = file_path
        
        try:
            return cls()
        finally:
            cls.model_config["env_file"] = original_env_file
