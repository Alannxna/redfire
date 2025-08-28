"""
RedFire 配置文件路径标准化规范

本文件定义了统一的配置文件路径约定，解决当前配置文件分散问题
"""

from pathlib import Path
from typing import Optional, List, Dict
from enum import Enum
import os


class ConfigType(Enum):
    """配置类型枚举"""
    APPLICATION = "application"      # 应用程序配置
    DATABASE = "database"           # 数据库配置
    CACHE = "cache"                 # 缓存配置
    SECURITY = "security"           # 安全配置
    LOGGING = "logging"             # 日志配置
    MONITORING = "monitoring"       # 监控配置
    VNPY = "vnpy"                  # VnPy配置
    GATEWAY = "gateway"            # 网关配置
    STRATEGY = "strategy"          # 策略配置


class Environment(Enum):
    """环境枚举"""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


class ConfigPathStandards:
    """
    配置文件路径标准化
    
    统一路径约定:
    ├── backend/
    │   ├── config/                     # 根配置目录
    │   │   ├── shared/                 # 共享配置
    │   │   │   ├── development/        # 开发环境
    │   │   │   │   ├── application.yaml
    │   │   │   │   ├── database.yaml
    │   │   │   │   ├── cache.yaml
    │   │   │   │   └── ...
    │   │   │   ├── testing/            # 测试环境
    │   │   │   ├── staging/            # 预发环境
    │   │   │   └── production/         # 生产环境
    │   │   ├── services/               # 微服务配置
    │   │   │   ├── user-service/
    │   │   │   │   ├── development/
    │   │   │   │   │   ├── application.yaml
    │   │   │   │   │   └── database.yaml
    │   │   │   │   └── ...
    │   │   │   ├── trading-service/
    │   │   │   ├── strategy-service/
    │   │   │   └── config-service/
    │   │   ├── legacy/                 # 遗留配置（待迁移）
    │   │   └── examples/               # 配置示例
    │   └── ...
    """
    
    # 根配置目录
    ROOT_CONFIG_DIR = Path("backend/config")
    
    # 子目录
    SHARED_CONFIG_DIR = ROOT_CONFIG_DIR / "shared"
    SERVICES_CONFIG_DIR = ROOT_CONFIG_DIR / "services" 
    LEGACY_CONFIG_DIR = ROOT_CONFIG_DIR / "legacy"
    EXAMPLES_CONFIG_DIR = ROOT_CONFIG_DIR / "examples"
    
    # 配置文件扩展名
    CONFIG_EXTENSIONS = [".yaml", ".yml", ".json", ".env"]
    
    # 环境变量前缀
    ENV_PREFIX = "REDFIRE"
    
    @classmethod
    def get_shared_config_path(
        cls,
        config_type: ConfigType,
        environment: Environment = Environment.DEVELOPMENT,
        file_format: str = "yaml"
    ) -> Path:
        """获取共享配置文件路径"""
        return cls.SHARED_CONFIG_DIR / environment.value / f"{config_type.value}.{file_format}"
    
    @classmethod
    def get_service_config_path(
        cls,
        service_name: str,
        config_type: ConfigType,
        environment: Environment = Environment.DEVELOPMENT,
        file_format: str = "yaml"
    ) -> Path:
        """获取服务特定配置文件路径"""
        return (cls.SERVICES_CONFIG_DIR / 
                service_name / 
                environment.value / 
                f"{config_type.value}.{file_format}")
    
    @classmethod
    def get_legacy_config_path(
        cls,
        config_name: str,
        service_name: Optional[str] = None
    ) -> Path:
        """获取遗留配置文件路径"""
        if service_name:
            return cls.LEGACY_CONFIG_DIR / service_name / config_name
        return cls.LEGACY_CONFIG_DIR / config_name
    
    @classmethod
    def get_config_search_paths(
        cls,
        service_name: str,
        config_type: ConfigType,
        environment: Environment = Environment.DEVELOPMENT
    ) -> List[Path]:
        """
        获取配置文件搜索路径（按优先级排序）
        
        优先级：
        1. 服务特定配置
        2. 共享配置
        3. 遗留配置
        4. 环境变量
        """
        paths = []
        
        # 1. 服务特定配置
        service_config = cls.get_service_config_path(service_name, config_type, environment)
        paths.append(service_config)
        
        # 2. 共享配置
        shared_config = cls.get_shared_config_path(config_type, environment)
        paths.append(shared_config)
        
        # 3. 遗留配置路径（用于向后兼容）
        legacy_patterns = [
            cls.LEGACY_CONFIG_DIR / service_name / f"{config_type.value}.yaml",
            cls.LEGACY_CONFIG_DIR / f"{service_name}_{config_type.value}.yaml",
            cls.LEGACY_CONFIG_DIR / f"{config_type.value}.yaml"
        ]
        paths.extend(legacy_patterns)
        
        return paths
    
    @classmethod
    def ensure_directories(cls) -> None:
        """确保配置目录存在"""
        directories = [
            cls.ROOT_CONFIG_DIR,
            cls.SHARED_CONFIG_DIR,
            cls.SERVICES_CONFIG_DIR,
            cls.LEGACY_CONFIG_DIR,
            cls.EXAMPLES_CONFIG_DIR
        ]
        
        # 为每个环境创建目录
        for env in Environment:
            directories.append(cls.SHARED_CONFIG_DIR / env.value)
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def get_environment_from_env_var(cls) -> Environment:
        """从环境变量获取当前环境"""
        env_value = os.getenv(f"{cls.ENV_PREFIX}_ENVIRONMENT", "development").lower()
        try:
            return Environment(env_value)
        except ValueError:
            return Environment.DEVELOPMENT
    
    @classmethod
    def validate_config_file(cls, config_path: Path) -> bool:
        """验证配置文件是否符合标准"""
        if not config_path.exists():
            return False
        
        # 检查文件扩展名
        if config_path.suffix not in cls.CONFIG_EXTENSIONS:
            return False
        
        # 检查路径是否在标准目录下
        try:
            config_path.relative_to(cls.ROOT_CONFIG_DIR)
            return True
        except ValueError:
            return False
    
    @classmethod
    def migrate_legacy_config(
        cls,
        old_path: Path,
        service_name: str,
        config_type: ConfigType,
        environment: Environment = Environment.DEVELOPMENT
    ) -> Path:
        """迁移遗留配置文件到标准路径"""
        if not old_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {old_path}")
        
        # 获取新路径
        new_path = cls.get_service_config_path(service_name, config_type, environment)
        
        # 确保目录存在
        new_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 复制文件
        import shutil
        shutil.copy2(old_path, new_path)
        
        return new_path
    
    @classmethod
    def get_config_inventory(cls) -> Dict[str, List[Path]]:
        """获取当前配置文件清单"""
        inventory = {
            "shared": [],
            "services": [],
            "legacy": [],
            "examples": []
        }
        
        # 扫描各目录
        if cls.SHARED_CONFIG_DIR.exists():
            inventory["shared"] = list(cls.SHARED_CONFIG_DIR.rglob("*"))
        
        if cls.SERVICES_CONFIG_DIR.exists():
            inventory["services"] = list(cls.SERVICES_CONFIG_DIR.rglob("*"))
        
        if cls.LEGACY_CONFIG_DIR.exists():
            inventory["legacy"] = list(cls.LEGACY_CONFIG_DIR.rglob("*"))
        
        if cls.EXAMPLES_CONFIG_DIR.exists():
            inventory["examples"] = list(cls.EXAMPLES_CONFIG_DIR.rglob("*"))
        
        return inventory


# 标准化配置服务名称映射
SERVICE_NAME_MAPPING = {
    "user_service": "user-service",
    "trading_service": "trading-service", 
    "strategy_service": "strategy-service",
    "config_service": "config-service",
    "vnpy_service": "vnpy-service",
    "gateway_service": "gateway-service",
    "monitor_service": "monitor-service"
}


def get_standard_service_name(service_name: str) -> str:
    """获取标准化的服务名称"""
    return SERVICE_NAME_MAPPING.get(service_name, service_name)


def get_current_environment() -> Environment:
    """获取当前环境"""
    return ConfigPathStandards.get_environment_from_env_var()


# 快捷函数
def get_app_config_path(service_name: str, environment: Optional[Environment] = None) -> Path:
    """获取应用配置路径"""
    env = environment or get_current_environment()
    return ConfigPathStandards.get_service_config_path(
        get_standard_service_name(service_name),
        ConfigType.APPLICATION,
        env
    )


def get_db_config_path(service_name: str, environment: Optional[Environment] = None) -> Path:
    """获取数据库配置路径"""
    env = environment or get_current_environment()
    return ConfigPathStandards.get_service_config_path(
        get_standard_service_name(service_name),
        ConfigType.DATABASE,
        env
    )


if __name__ == "__main__":
    # 示例用法
    ConfigPathStandards.ensure_directories()
    
    # 获取用户服务的应用配置路径
    user_app_config = get_app_config_path("user_service")
    print(f"用户服务应用配置路径: {user_app_config}")
    
    # 获取共享数据库配置路径
    shared_db_config = ConfigPathStandards.get_shared_config_path(ConfigType.DATABASE)
    print(f"共享数据库配置路径: {shared_db_config}")
    
    # 获取配置清单
    inventory = ConfigPathStandards.get_config_inventory()
    print(f"配置文件清单: {inventory}")
