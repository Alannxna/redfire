"""
配置管理器

提供统一的配置管理服务，支持多环境配置、动态配置更新等
"""

import os
import json
import yaml
from typing import Dict, Any, Optional, Union
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum

from ..common.exceptions import InfrastructureException


class EnvironmentType(Enum):
    """环境类型枚举"""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


@dataclass
class ConfigSource:
    """配置源描述"""
    source_type: str  # file, env, remote
    location: str
    priority: int = 0
    enabled: bool = True


class ConfigManager:
    """配置管理器
    
    统一管理应用配置，支持多种配置源和环境
    """
    
    def __init__(self, base_path: Optional[Path] = None):
        self.base_path = base_path or Path.cwd()
        self.config_data: Dict[str, Any] = {}
        self.config_sources: list[ConfigSource] = []
        self.environment = self._detect_environment()
        self._load_default_sources()
    
    def _detect_environment(self) -> EnvironmentType:
        """检测当前环境"""
        env_name = os.getenv('ENVIRONMENT', 'development').lower()
        try:
            return EnvironmentType(env_name)
        except ValueError:
            return EnvironmentType.DEVELOPMENT
    
    def _load_default_sources(self):
        """加载默认配置源"""
        # 基础配置文件
        config_dir = self.base_path / "config"
        
        # 添加默认配置源（按优先级排序）
        self.add_config_source("file", str(config_dir / "default.yaml"), priority=1)
        self.add_config_source("file", str(config_dir / f"{self.environment.value}.yaml"), priority=2)
        self.add_config_source("env", "", priority=3)
        
        # 本地覆盖配置（最高优先级）
        local_config = config_dir / "local.yaml"
        if local_config.exists():
            self.add_config_source("file", str(local_config), priority=4)
    
    def add_config_source(self, source_type: str, location: str, priority: int = 0):
        """添加配置源"""
        source = ConfigSource(
            source_type=source_type,
            location=location,
            priority=priority
        )
        self.config_sources.append(source)
        # 按优先级排序
        self.config_sources.sort(key=lambda x: x.priority)
    
    def load_config(self) -> Dict[str, Any]:
        """加载所有配置"""
        merged_config = {}
        
        # 按优先级顺序加载配置
        for source in self.config_sources:
            if not source.enabled:
                continue
                
            try:
                config_data = self._load_from_source(source)
                merged_config = self._deep_merge(merged_config, config_data)
            except Exception as e:
                if source.source_type == "file" and source.location and not Path(source.location).exists():
                    continue  # 文件不存在，跳过
                raise InfrastructureException(
                    f"加载配置源失败: {source.source_type}:{source.location} - {e}"
                )
        
        self.config_data = merged_config
        return self.config_data
    
    def _load_from_source(self, source: ConfigSource) -> Dict[str, Any]:
        """从配置源加载数据"""
        if source.source_type == "file":
            return self._load_from_file(source.location)
        elif source.source_type == "env":
            return self._load_from_environment()
        elif source.source_type == "remote":
            return self._load_from_remote(source.location)
        else:
            raise InfrastructureException(f"不支持的配置源类型: {source.source_type}")
    
    def _load_from_file(self, file_path: str) -> Dict[str, Any]:
        """从文件加载配置"""
        path = Path(file_path)
        if not path.exists():
            return {}
        
        with open(path, 'r', encoding='utf-8') as f:
            if path.suffix.lower() in ['.yaml', '.yml']:
                return yaml.safe_load(f) or {}
            elif path.suffix.lower() == '.json':
                return json.load(f)
            else:
                raise InfrastructureException(f"不支持的配置文件格式: {path.suffix}")
    
    def _load_from_environment(self) -> Dict[str, Any]:
        """从环境变量加载配置"""
        config = {}
        
        # 加载以特定前缀开头的环境变量
        prefix = "VNPY_"
        for key, value in os.environ.items():
            if key.startswith(prefix):
                # 转换环境变量名为配置路径
                config_key = key[len(prefix):].lower().replace('_', '.')
                self._set_nested_value(config, config_key, self._parse_env_value(value))
        
        return config
    
    def _load_from_remote(self, url: str) -> Dict[str, Any]:
        """从远程源加载配置"""
        # TODO: 实现远程配置加载
        raise NotImplementedError("远程配置加载功能尚未实现")
    
    def _parse_env_value(self, value: str) -> Union[str, int, float, bool]:
        """解析环境变量值"""
        # 尝试解析为不同类型
        if value.lower() in ('true', 'false'):
            return value.lower() == 'true'
        
        try:
            if '.' in value:
                return float(value)
            else:
                return int(value)
        except ValueError:
            return value
    
    def _set_nested_value(self, config: Dict[str, Any], key_path: str, value: Any):
        """设置嵌套配置值"""
        keys = key_path.split('.')
        current = config
        
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        current[keys[-1]] = value
    
    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """深度合并配置字典"""
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """获取配置值"""
        if not self.config_data:
            self.load_config()
        
        keys = key_path.split('.')
        current = self.config_data
        
        try:
            for key in keys:
                current = current[key]
            return current
        except (KeyError, TypeError):
            return default
    
    def set(self, key_path: str, value: Any):
        """设置配置值（运行时）"""
        if not self.config_data:
            self.load_config()
        
        self._set_nested_value(self.config_data, key_path, value)
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """获取配置段"""
        return self.get(section, {})
    
    def has(self, key_path: str) -> bool:
        """检查配置项是否存在"""
        return self.get(key_path) is not None
    
    def get_environment(self) -> EnvironmentType:
        """获取当前环境"""
        return self.environment
    
    def is_development(self) -> bool:
        """是否为开发环境"""
        return self.environment == EnvironmentType.DEVELOPMENT
    
    def is_production(self) -> bool:
        """是否为生产环境"""
        return self.environment == EnvironmentType.PRODUCTION
    
    def reload(self):
        """重新加载配置"""
        self.config_data.clear()
        self.load_config()
    
    def to_dict(self) -> Dict[str, Any]:
        """导出配置为字典"""
        if not self.config_data:
            self.load_config()
        return self.config_data.copy()
    
    def save_to_file(self, file_path: str, section: Optional[str] = None):
        """保存配置到文件"""
        data = self.get_section(section) if section else self.to_dict()
        
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'w', encoding='utf-8') as f:
            if path.suffix.lower() in ['.yaml', '.yml']:
                yaml.safe_dump(data, f, default_flow_style=False, allow_unicode=True)
            elif path.suffix.lower() == '.json':
                json.dump(data, f, indent=2, ensure_ascii=False)
            else:
                raise InfrastructureException(f"不支持的文件格式: {path.suffix}")


# 全局配置管理器实例
_global_config_manager: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """获取全局配置管理器"""
    global _global_config_manager
    if _global_config_manager is None:
        _global_config_manager = ConfigManager()
        _global_config_manager.load_config()
    return _global_config_manager


def set_config_manager(config_manager: ConfigManager):
    """设置全局配置管理器"""
    global _global_config_manager
    _global_config_manager = config_manager


# 便捷函数
def get_config(key_path: str, default: Any = None) -> Any:
    """获取配置值的便捷函数"""
    return get_config_manager().get(key_path, default)


def get_config_section(section: str) -> Dict[str, Any]:
    """获取配置段的便捷函数"""
    return get_config_manager().get_section(section)
