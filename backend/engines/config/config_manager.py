"""
统一配置管理器
==============

提供配置的加载、管理、监听和热重载功能
"""

import os
import logging
from typing import Dict, Any, List, Callable, Optional, Type, Union
from pathlib import Path
import json
import yaml
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from .base_config import BaseConfig
from .app_config import AppConfig
from .environment_config import detect_environment, get_environment_config

logger = logging.getLogger(__name__)


class ConfigWatcher(FileSystemEventHandler):
    """配置文件监听器"""
    
    def __init__(self, callback: Callable[[str], None]):
        self.callback = callback
        
    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith(('.env', '.yaml', '.yml')):
            logger.info(f"配置文件变更: {event.src_path}")
            self.callback(event.src_path)


class ConfigLayer:
    """配置层"""
    
    def __init__(self, name: str, priority: int):
        self.name = name
        self.priority = priority
        self.data: Dict[str, Any] = {}
    
    def set_value(self, key: str, value: Any):
        """设置配置值"""
        self.data[key] = value
    
    def get_value(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        return self.data.get(key, default)
    
    def has_key(self, key: str) -> bool:
        """检查是否包含指定键"""
        return key in self.data
    
    def update(self, data: Dict[str, Any]):
        """更新配置数据"""
        self.data.update(data)


class ConfigHierarchy:
    """配置层次结构管理"""
    
    def __init__(self):
        self.layers: List[ConfigLayer] = [
            ConfigLayer("defaults", priority=1),      # 默认值
            ConfigLayer("file", priority=2),          # 配置文件
            ConfigLayer("environment", priority=3),   # 环境变量
            ConfigLayer("runtime", priority=4),       # 运行时配置
            ConfigLayer("override", priority=5)       # 强制覆盖
        ]
        self._load_environment_variables()
    
    def _load_environment_variables(self):
        """加载环境变量到环境层"""
        env_layer = self.get_layer("environment")
        for key, value in os.environ.items():
            env_layer.set_value(key.lower(), value)
    
    def get_layer(self, name: str) -> Optional[ConfigLayer]:
        """获取指定层"""
        for layer in self.layers:
            if layer.name == name:
                return layer
        return None
    
    def resolve_config(self, key: str, default: Any = None) -> Any:
        """解析配置值，按优先级顺序"""
        for layer in sorted(self.layers, key=lambda x: x.priority, reverse=True):
            if layer.has_key(key):
                return layer.get_value(key)
        return default
    
    def load_from_file(self, file_path: str):
        """从文件加载配置"""
        file_layer = self.get_layer("file")
        if not file_layer:
            return
        
        path = Path(file_path)
        if not path.exists():
            logger.warning(f"配置文件不存在: {file_path}")
            return
        
        try:
            if path.suffix.lower() in ['.yaml', '.yml']:
                with open(path, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f) or {}
            elif path.suffix.lower() == '.json':
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            elif path.suffix.lower() == '.env':
                data = self._parse_env_file(path)
            else:
                logger.warning(f"不支持的配置文件格式: {file_path}")
                return
            
            file_layer.update(data)
            logger.info(f"已加载配置文件: {file_path}")
            
        except Exception as e:
            logger.error(f"加载配置文件失败 {file_path}: {e}")
    
    def _parse_env_file(self, file_path: Path) -> Dict[str, Any]:
        """解析.env文件"""
        data = {}
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        if '=' in line:
                            key, value = line.split('=', 1)
                            key = key.strip().lower()
                            value = value.strip().strip('"\'')
                            data[key] = value
        except Exception as e:
            logger.error(f"解析.env文件失败 {file_path}: {e}")
        return data


class CoreConfigManager:
    """统一配置管理器"""
    
    def __init__(self):
        self._configs: Dict[str, BaseConfig] = {}
        self._hierarchy = ConfigHierarchy()
        self._watchers: List[Callable] = []
        self._observer: Optional[Observer] = None
        self._watch_enabled = False
        
    def register_config(self, name: str, config_class: Type[BaseConfig], **kwargs) -> BaseConfig:
        """注册配置类"""
        try:
            # 使用层次结构解析配置
            config_data = self._build_config_data(config_class)
            config = config_class(**config_data, **kwargs)
            
            self._configs[name] = config
            logger.info(f"已注册配置: {name}")
            return config
            
        except Exception as e:
            logger.error(f"配置注册失败 {name}: {e}")
            raise
    
    def _build_config_data(self, config_class: Type[BaseConfig]) -> Dict[str, Any]:
        """构建配置数据"""
        config_data = {}
        
        # 获取配置类的字段
        if hasattr(config_class, 'model_fields'):
            fields = config_class.model_fields
            for field_name, field_info in fields.items():
                # 尝试从层次结构解析值
                value = self._hierarchy.resolve_config(field_name.lower())
                if value is not None:
                    config_data[field_name] = value
        
        return config_data
    
    def get_config(self, name: str) -> Optional[BaseConfig]:
        """获取配置实例"""
        return self._configs.get(name)
    
    def get_app_config(self) -> AppConfig:
        """获取应用配置"""
        config = self.get_config('app')
        if not config:
            config = self.register_config('app', AppConfig)
        return config
    
    def reload_config(self, name: str):
        """重新加载配置"""
        if name not in self._configs:
            logger.warning(f"配置不存在: {name}")
            return
        
        config_class = type(self._configs[name])
        try:
            config_data = self._build_config_data(config_class)
            new_config = config_class(**config_data)
            old_config = self._configs[name]
            self._configs[name] = new_config
            
            # 通知配置变更
            self._notify_watchers(name, old_config, new_config)
            logger.info(f"配置重新加载完成: {name}")
            
        except Exception as e:
            logger.error(f"配置重新加载失败 {name}: {e}")
    
    def watch_config(self, callback: Callable[[str, BaseConfig, BaseConfig], None]):
        """监听配置变更"""
        self._watchers.append(callback)
    
    def _notify_watchers(self, name: str, old_config: BaseConfig, new_config: BaseConfig):
        """通知监听器"""
        for watcher in self._watchers:
            try:
                watcher(name, old_config, new_config)
            except Exception as e:
                logger.error(f"配置变更通知失败: {e}")
    
    def enable_file_watching(self, watch_paths: List[str] = None):
        """启用文件监听"""
        if self._watch_enabled:
            return
        
        if not watch_paths:
            watch_paths = ['.env', 'config.yaml', 'config.yml']
        
        def on_config_change(file_path: str):
            self._hierarchy.load_from_file(file_path)
            # 重新加载所有配置
            for name in self._configs.keys():
                self.reload_config(name)
        
        watcher = ConfigWatcher(on_config_change)
        self._observer = Observer()
        
        for path in watch_paths:
            if os.path.exists(path):
                if os.path.isfile(path):
                    watch_dir = os.path.dirname(os.path.abspath(path))
                else:
                    watch_dir = path
                self._observer.schedule(watcher, watch_dir, recursive=False)
        
        self._observer.start()
        self._watch_enabled = True
        logger.info("配置文件监听已启用")
    
    def disable_file_watching(self):
        """禁用文件监听"""
        if self._observer:
            self._observer.stop()
            self._observer.join()
            self._observer = None
        self._watch_enabled = False
        logger.info("配置文件监听已禁用")
    
    def load_from_file(self, file_path: str):
        """从文件加载配置"""
        self._hierarchy.load_from_file(file_path)
    
    def load_environment_config(self, env_name: str = None):
        """加载环境特定配置"""
        if not env_name:
            env_name = detect_environment()
        
        try:
            env_config = get_environment_config(env_name)
            self._configs['environment'] = env_config
            logger.info(f"已加载环境配置: {env_name}")
            return env_config
        except Exception as e:
            logger.error(f"加载环境配置失败 {env_name}: {e}")
            raise
    
    def validate_all_configs(self) -> bool:
        """验证所有配置"""
        all_valid = True
        for name, config in self._configs.items():
            try:
                if hasattr(config, 'validate_environment'):
                    config.validate_environment()
                logger.info(f"配置验证通过: {name}")
            except Exception as e:
                logger.error(f"配置验证失败 {name}: {e}")
                all_valid = False
        return all_valid
    
    def export_config(self, name: str, format: str = 'json') -> str:
        """导出配置"""
        config = self.get_config(name)
        if not config:
            raise ValueError(f"配置不存在: {name}")
        
        data = config.to_dict()
        
        if format.lower() == 'json':
            return json.dumps(data, indent=2, ensure_ascii=False)
        elif format.lower() in ['yaml', 'yml']:
            return yaml.dump(data, default_flow_style=False, allow_unicode=True)
        else:
            raise ValueError(f"不支持的导出格式: {format}")


# 全局配置管理器实例
_config_manager: Optional[CoreConfigManager] = None


def get_config_manager() -> CoreConfigManager:
    """获取全局配置管理器"""
    global _config_manager
    if _config_manager is None:
        _config_manager = CoreConfigManager()
        
        # 自动加载环境配置
        try:
            _config_manager.load_environment_config()
        except Exception as e:
            logger.warning(f"自动加载环境配置失败: {e}")
        
        # 自动注册应用配置
        try:
            _config_manager.register_config('app', AppConfig)
        except Exception as e:
            logger.warning(f"自动注册应用配置失败: {e}")
    
    return _config_manager


def get_app_config() -> AppConfig:
    """获取应用配置的便捷函数"""
    return get_config_manager().get_app_config()
