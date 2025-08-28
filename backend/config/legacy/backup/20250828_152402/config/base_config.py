"""
基础配置类定义
==============

提供所有配置类的基础功能，包括验证、序列化、环境变量支持等。
"""

import os
import json
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Type, TypeVar, Union, List
from pathlib import Path

# 导入依赖处理
try:
    from pydantic import BaseModel, Field, ConfigDict
    from pydantic_settings import BaseSettings
    PYDANTIC_AVAILABLE = True
except ImportError:
    # 简单的替代实现
    class Field:
        def __init__(self, *args, **kwargs):
            pass
    
    class ConfigDict(dict):
        pass
    
    class BaseModel:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)
        
        def model_dump(self):
            return {k: v for k, v in self.__dict__.items() if not k.startswith('_')}
    
    class BaseSettings(BaseModel):
        pass
    
    PYDANTIC_AVAILABLE = False

try:
    from loguru import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

T = TypeVar('T', bound='BaseConfig')


class ConfigMetadata(BaseModel):
    """配置元数据"""
    name: str
    version: str
    description: str
    created_at: str
    updated_at: str
    source: str  # env, file, default


class BaseConfig(BaseSettings, ABC):
    """
    基础配置类
    
    所有配置类都应该继承此类，提供统一的接口和功能。
    """
    
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="allow",
        validate_assignment=True,
        arbitrary_types_allowed=True
    )
    
    # 元数据信息
    _metadata: Optional[ConfigMetadata] = None
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._metadata = self._create_metadata()
    
    @abstractmethod
    def _create_metadata(self) -> ConfigMetadata:
        """创建配置元数据"""
        pass
    
    @abstractmethod
    def validate_config(self) -> bool:
        """验证配置的有效性"""
        pass
    
    def get_metadata(self) -> ConfigMetadata:
        """获取配置元数据"""
        return self._metadata
    
    def to_dict(self, exclude_private: bool = True) -> Dict[str, Any]:
        """转换为字典格式"""
        data = self.model_dump()
        
        if exclude_private:
            # 移除以下划线开头的私有字段
            data = {k: v for k, v in data.items() if not k.startswith('_')}
        
        return data
    
    def to_json(self, pretty: bool = False) -> str:
        """转换为JSON格式"""
        data = self.to_dict()
        if pretty:
            return json.dumps(data, indent=2, ensure_ascii=False)
        return json.dumps(data, ensure_ascii=False)
    
    def save_to_file(self, file_path: Union[str, Path], format: str = "json") -> bool:
        """保存配置到文件"""
        try:
            file_path = Path(file_path)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            if format.lower() == "json":
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.to_json(pretty=True))
            elif format.lower() == "env":
                self._save_to_env_file(file_path)
            else:
                raise ValueError(f"不支持的格式: {format}")
            
            logger.info(f"配置已保存到: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"保存配置失败: {e}")
            return False
    
    def _save_to_env_file(self, file_path: Path):
        """保存为环境变量文件"""
        lines = []
        lines.append(f"# {self._metadata.name} 配置文件")
        lines.append(f"# 版本: {self._metadata.version}")
        lines.append(f"# 描述: {self._metadata.description}")
        lines.append("")
        
        # 转换配置为环境变量格式
        for key, value in self.to_dict().items():
            env_key = key.upper()
            env_value = self._format_env_value(value)
            lines.append(f"{env_key}={env_value}")
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
    
    def _format_env_value(self, value: Any) -> str:
        """格式化环境变量值"""
        if isinstance(value, bool):
            return str(value).lower()
        elif isinstance(value, (list, dict)):
            return json.dumps(value, ensure_ascii=False)
        elif value is None:
            return ""
        else:
            return str(value)
    
    @classmethod
    def load_from_file(cls: Type[T], file_path: Union[str, Path]) -> T:
        """从文件加载配置"""
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {file_path}")
        
        try:
            if file_path.suffix.lower() == ".json":
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return cls(**data)
            
            elif file_path.suffix.lower() == ".env":
                # 临时设置环境变量文件
                original_env_file = cls.model_config.get("env_file")
                cls.model_config["env_file"] = str(file_path)
                try:
                    instance = cls()
                    return instance
                finally:
                    cls.model_config["env_file"] = original_env_file
            
            else:
                raise ValueError(f"不支持的文件格式: {file_path.suffix}")
                
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            raise
    
    @classmethod
    def load_from_env(cls: Type[T], prefix: str = "") -> T:
        """从环境变量加载配置"""
        return cls(_env_prefix=prefix)
    
    def update_from_dict(self, data: Dict[str, Any]) -> bool:
        """从字典更新配置"""
        try:
            for key, value in data.items():
                if hasattr(self, key):
                    setattr(self, key, value)
            return True
        except Exception as e:
            logger.error(f"更新配置失败: {e}")
            return False
    
    def update_from_env(self, prefix: str = "") -> bool:
        """从环境变量更新配置"""
        try:
            # 重新创建实例以加载最新的环境变量
            new_instance = self.__class__.load_from_env(prefix)
            self.update_from_dict(new_instance.to_dict())
            return True
        except Exception as e:
            logger.error(f"从环境变量更新配置失败: {e}")
            return False
    
    def get_env_vars(self) -> Dict[str, str]:
        """获取所有相关的环境变量"""
        env_vars = {}
        for key in self.to_dict().keys():
            env_key = key.upper()
            env_value = os.getenv(env_key)
            if env_value is not None:
                env_vars[env_key] = env_value
        return env_vars
    
    def compare_with(self, other: 'BaseConfig') -> Dict[str, Any]:
        """与另一个配置实例比较差异"""
        if not isinstance(other, self.__class__):
            raise ValueError("只能与相同类型的配置实例比较")
        
        self_dict = self.to_dict()
        other_dict = other.to_dict()
        
        differences = {}
        all_keys = set(self_dict.keys()) | set(other_dict.keys())
        
        for key in all_keys:
            self_value = self_dict.get(key)
            other_value = other_dict.get(key)
            
            if self_value != other_value:
                differences[key] = {
                    "self": self_value,
                    "other": other_value
                }
        
        return differences
    
    def create_backup(self, backup_dir: Union[str, Path] = "backups") -> Path:
        """创建配置备份"""
        backup_dir = Path(backup_dir)
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = backup_dir / f"{self._metadata.name}_{timestamp}.json"
        
        self.save_to_file(backup_file, format="json")
        return backup_file
    
    def restore_from_backup(self, backup_file: Union[str, Path]) -> bool:
        """从备份恢复配置"""
        try:
            backup_instance = self.load_from_file(backup_file)
            self.update_from_dict(backup_instance.to_dict())
            logger.info(f"从备份恢复配置: {backup_file}")
            return True
        except Exception as e:
            logger.error(f"从备份恢复配置失败: {e}")
            return False
    
    def get_config_summary(self) -> Dict[str, Any]:
        """获取配置摘要信息"""
        return {
            "metadata": self._metadata.model_dump() if self._metadata else None,
            "total_fields": len(self.to_dict()),
            "env_vars_count": len(self.get_env_vars()),
            "validation_status": self.validate_config(),
            "last_updated": self._metadata.updated_at if self._metadata else None
        }
    
    def __str__(self) -> str:
        """字符串表示"""
        return f"{self.__class__.__name__}({self._metadata.name if self._metadata else 'Unknown'})"
    
    def __repr__(self) -> str:
        """详细字符串表示"""
        return f"{self.__class__.__name__}(name='{self._metadata.name if self._metadata else 'Unknown'}', fields={len(self.to_dict())})"


class ConfigGroup(BaseModel):
    """配置组，用于管理一组相关的配置"""
    
    name: str
    description: str
    configs: Dict[str, BaseConfig] = Field(default_factory=dict)
    
    def add_config(self, key: str, config: BaseConfig):
        """添加配置"""
        self.configs[key] = config
    
    def get_config(self, key: str) -> Optional[BaseConfig]:
        """获取配置"""
        return self.configs.get(key)
    
    def remove_config(self, key: str) -> bool:
        """移除配置"""
        if key in self.configs:
            del self.configs[key]
            return True
        return False
    
    def validate_all(self) -> Dict[str, bool]:
        """验证所有配置"""
        results = {}
        for key, config in self.configs.items():
            results[key] = config.validate_config()
        return results
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "description": self.description,
            "configs": {key: config.to_dict() for key, config in self.configs.items()}
        }


class ConfigRegistry:
    """配置注册表，管理所有配置类型"""
    
    def __init__(self):
        self._config_types: Dict[str, Type[BaseConfig]] = {}
        self._config_instances: Dict[str, BaseConfig] = {}
    
    def register_config_type(self, name: str, config_class: Type[BaseConfig]):
        """注册配置类型"""
        self._config_types[name] = config_class
        logger.debug(f"注册配置类型: {name} -> {config_class}")
    
    def create_config(self, name: str, **kwargs) -> Optional[BaseConfig]:
        """创建配置实例"""
        if name not in self._config_types:
            logger.error(f"未知的配置类型: {name}")
            return None
        
        try:
            config_class = self._config_types[name]
            instance = config_class(**kwargs)
            self._config_instances[name] = instance
            return instance
        except Exception as e:
            logger.error(f"创建配置实例失败: {e}")
            return None
    
    def get_config(self, name: str) -> Optional[BaseConfig]:
        """获取配置实例"""
        return self._config_instances.get(name)
    
    def list_config_types(self) -> List[str]:
        """列出所有注册的配置类型"""
        return list(self._config_types.keys())
    
    def list_config_instances(self) -> List[str]:
        """列出所有配置实例"""
        return list(self._config_instances.keys())


# 全局配置注册表
config_registry = ConfigRegistry()
