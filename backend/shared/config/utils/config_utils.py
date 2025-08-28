"""
统一配置工具模块
================

统一各配置管理器中重复的工具方法，实现代码重用和规范化
"""

import os
import json
import logging
from pathlib import Path
from typing import Any, Dict, Union, Optional, List
from enum import Enum

logger = logging.getLogger(__name__)


class ConfigError(Exception):
    """配置错误基类"""
    pass


class ConfigFormat(Enum):
    """配置文件格式枚举"""
    JSON = "json"
    YAML = "yaml"
    ENV = "env"
    TOML = "toml"


class ConfigTypeConverter:
    """配置类型转换器 - 统一环境变量值转换逻辑"""
    
    @staticmethod
    def convert_env_value(value: str) -> Union[str, int, float, bool, None]:
        """
        统一的环境变量值类型转换方法
        
        Args:
            value: 环境变量字符串值
            
        Returns:
            转换后的值 (bool, int, float, str, None)
        """
        if not value:
            return None
            
        # 去除首尾空格
        value = value.strip()
        
        # 处理引号包围的值
        if (value.startswith('"') and value.endswith('"')) or \
           (value.startswith("'") and value.endswith("'")):
            value = value[1:-1]
        
        # 空值处理
        if value.lower() in ('null', 'none', ''):
            return None
            
        # 布尔值处理
        if value.lower() in ('true', 'false', 'yes', 'no', 'on', 'off'):
            return value.lower() in ('true', 'yes', 'on')
        
        # 数字处理
        try:
            # 浮点数
            if '.' in value:
                return float(value)
            # 整数
            else:
                return int(value)
        except ValueError:
            pass
        
        # 列表处理 (逗号分隔)
        if ',' in value:
            return [item.strip() for item in value.split(',') if item.strip()]
        
        # 默认返回字符串
        return value
    
    @staticmethod
    def convert_dict_values(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        递归转换字典中的所有值
        
        Args:
            data: 待转换的字典
            
        Returns:
            转换后的字典
        """
        result = {}
        for key, value in data.items():
            if isinstance(value, dict):
                result[key] = ConfigTypeConverter.convert_dict_values(value)
            elif isinstance(value, str):
                result[key] = ConfigTypeConverter.convert_env_value(value)
            else:
                result[key] = value
        return result


class ConfigFileLoader:
    """统一配置文件加载器"""
    
    @staticmethod
    def detect_format(file_path: Path) -> ConfigFormat:
        """
        检测配置文件格式
        
        Args:
            file_path: 文件路径
            
        Returns:
            配置文件格式
        """
        suffix = file_path.suffix.lower()
        
        if suffix in ['.yaml', '.yml']:
            return ConfigFormat.YAML
        elif suffix == '.json':
            return ConfigFormat.JSON
        elif suffix == '.env':
            return ConfigFormat.ENV
        elif suffix == '.toml':
            return ConfigFormat.TOML
        else:
            raise ValueError(f"不支持的配置文件格式: {suffix}")
    
    @staticmethod
    def load_file(file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        统一的配置文件加载方法
        
        Args:
            file_path: 配置文件路径
            
        Returns:
            配置字典
            
        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 文件格式不支持
        """
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"配置文件不存在: {path}")
        
        format_type = ConfigFileLoader.detect_format(path)
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                if format_type == ConfigFormat.JSON:
                    return json.load(f)
                elif format_type == ConfigFormat.YAML:
                    return ConfigFileLoader._load_yaml(f)
                elif format_type == ConfigFormat.ENV:
                    return ConfigFileLoader._load_env_file(f)
                elif format_type == ConfigFormat.TOML:
                    return ConfigFileLoader._load_toml(f)
                    
        except Exception as e:
            logger.error(f"配置文件加载失败 {path}: {e}")
            raise
    
    @staticmethod
    def _load_yaml(file_handle) -> Dict[str, Any]:
        """加载YAML文件"""
        try:
            import yaml
            return yaml.safe_load(file_handle) or {}
        except ImportError:
            raise ImportError(
                "YAML支持未安装，请运行: pip install pyyaml"
            )
    
    @staticmethod
    def _load_toml(file_handle) -> Dict[str, Any]:
        """加载TOML文件"""
        try:
            import tomli
            return tomli.load(file_handle)
        except ImportError:
            raise ImportError(
                "TOML支持未安装，请运行: pip install tomli"
            )
    
    @staticmethod
    def _load_env_file(file_handle) -> Dict[str, Any]:
        """加载.env文件"""
        data = {}
        for line in file_handle:
            line = line.strip()
            if line and not line.startswith('#'):
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip().lower()
                    value = value.strip()
                    data[key] = ConfigTypeConverter.convert_env_value(value)
        return data


class ConfigEnvLoader:
    """统一环境变量加载器"""
    
    @staticmethod
    def load_env_config(prefix: str, nested_delimiter: str = "__") -> Dict[str, Any]:
        """
        统一的环境变量配置加载方法
        
        Args:
            prefix: 环境变量前缀
            nested_delimiter: 嵌套分隔符
            
        Returns:
            配置字典
        """
        config = {}
        
        for key, value in os.environ.items():
            if key.startswith(prefix):
                # 移除前缀
                config_key = key[len(prefix):]
                
                # 转换为小写并处理嵌套
                if nested_delimiter in config_key:
                    ConfigEnvLoader._set_nested_value(
                        config, 
                        config_key.lower(), 
                        ConfigTypeConverter.convert_env_value(value),
                        nested_delimiter
                    )
                else:
                    config[config_key.lower()] = ConfigTypeConverter.convert_env_value(value)
        
        return config
    
    @staticmethod
    def _set_nested_value(config: Dict[str, Any], key_path: str, 
                         value: Any, delimiter: str = "__"):
        """设置嵌套配置值"""
        keys = key_path.split(delimiter)
        current = config
        
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            elif not isinstance(current[key], dict):
                # 如果存在同名非字典值，创建新的字典
                current[key] = {}
            current = current[key]
        
        current[keys[-1]] = value


class ConfigMerger:
    """统一配置合并器"""
    
    @staticmethod
    def deep_merge(base: Dict[str, Any], override: Dict[str, Any], 
                   allow_override: bool = True) -> Dict[str, Any]:
        """
        深度合并配置字典
        
        Args:
            base: 基础配置字典
            override: 覆盖配置字典  
            allow_override: 是否允许覆盖非字典值
            
        Returns:
            合并后的配置字典
        """
        result = base.copy()
        
        for key, value in override.items():
            if key in result:
                if isinstance(result[key], dict) and isinstance(value, dict):
                    # 递归合并字典
                    result[key] = ConfigMerger.deep_merge(
                        result[key], value, allow_override
                    )
                elif allow_override:
                    # 允许覆盖时直接替换
                    result[key] = value
                else:
                    # 不允许覆盖时保留原值
                    logger.warning(f"配置项 {key} 已存在，跳过覆盖")
            else:
                result[key] = value
        
        return result
    
    @staticmethod
    def merge_multiple(configs: List[Dict[str, Any]], 
                      allow_override: bool = True) -> Dict[str, Any]:
        """
        合并多个配置字典
        
        Args:
            configs: 配置字典列表 (按优先级从低到高排序)
            allow_override: 是否允许覆盖
            
        Returns:
            合并后的配置字典
        """
        if not configs:
            return {}
        
        result = configs[0].copy()
        for config in configs[1:]:
            result = ConfigMerger.deep_merge(result, config, allow_override)
        
        return result


class ConfigValidator:
    """统一配置验证器"""
    
    @staticmethod
    def validate_required_keys(config: Dict[str, Any], 
                              required_keys: List[str],
                              nested_delimiter: str = ".") -> List[str]:
        """
        验证必需配置项
        
        Args:
            config: 配置字典
            required_keys: 必需的配置键列表 (支持嵌套路径)
            nested_delimiter: 嵌套分隔符
            
        Returns:
            缺失的配置键列表
        """
        missing_keys = []
        
        for key in required_keys:
            if not ConfigValidator._has_nested_key(config, key, nested_delimiter):
                missing_keys.append(key)
        
        return missing_keys
    
    @staticmethod
    def _has_nested_key(config: Dict[str, Any], key_path: str, 
                       delimiter: str = ".") -> bool:
        """检查是否存在嵌套键"""
        keys = key_path.split(delimiter)
        current = config
        
        for key in keys:
            if not isinstance(current, dict) or key not in current:
                return False
            current = current[key]
        
        return True
    
    @staticmethod
    def get_nested_value(config: Dict[str, Any], key_path: str,
                        default: Any = None, delimiter: str = ".") -> Any:
        """获取嵌套配置值"""
        keys = key_path.split(delimiter)
        current = config
        
        for key in keys:
            if not isinstance(current, dict) or key not in current:
                return default
            current = current[key]
        
        return current


class ConfigCache:
    """统一配置缓存管理器"""
    
    def __init__(self, max_size: int = 100, ttl_seconds: Optional[int] = None):
        """
        初始化配置缓存
        
        Args:
            max_size: 最大缓存项数
            ttl_seconds: 生存时间 (秒)，None表示永不过期
        """
        self._cache: Dict[str, Any] = {}
        self._timestamps: Dict[str, float] = {}
        self._max_size = max_size
        self._ttl_seconds = ttl_seconds
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取缓存值"""
        if not self._is_valid(key):
            return default
        return self._cache.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """设置缓存值"""
        import time
        
        # 清理过期缓存
        self._cleanup_expired()
        
        # 检查缓存大小限制
        if len(self._cache) >= self._max_size and key not in self._cache:
            self._evict_oldest()
        
        self._cache[key] = value
        self._timestamps[key] = time.time()
    
    def clear(self) -> None:
        """清空缓存"""
        self._cache.clear()
        self._timestamps.clear()
    
    def _is_valid(self, key: str) -> bool:
        """检查缓存项是否有效"""
        if key not in self._cache:
            return False
        
        if self._ttl_seconds is None:
            return True
        
        import time
        return (time.time() - self._timestamps[key]) < self._ttl_seconds
    
    def _cleanup_expired(self) -> None:
        """清理过期缓存"""
        if self._ttl_seconds is None:
            return
        
        import time
        current_time = time.time()
        
        expired_keys = [
            key for key, timestamp in self._timestamps.items()
            if (current_time - timestamp) >= self._ttl_seconds
        ]
        
        for key in expired_keys:
            self._cache.pop(key, None)
            self._timestamps.pop(key, None)
    
    def _evict_oldest(self) -> None:
        """移除最老的缓存项"""
        if not self._timestamps:
            return
        
        oldest_key = min(self._timestamps.keys(), 
                        key=lambda k: self._timestamps[k])
        self._cache.pop(oldest_key, None)
        self._timestamps.pop(oldest_key, None)


# 全局实例
default_cache = ConfigCache()


def get_nested_config(config: Dict[str, Any], key_path: str, 
                     default: Any = None) -> Any:
    """获取嵌套配置的便捷函数"""
    return ConfigValidator.get_nested_value(config, key_path, default)


def merge_configs(*configs: Dict[str, Any]) -> Dict[str, Any]:
    """合并配置的便捷函数"""
    return ConfigMerger.merge_multiple(list(configs))


def load_config_file(file_path: Union[str, Path]) -> Dict[str, Any]:
    """加载配置文件的便捷函数"""
    return ConfigFileLoader.load_file(file_path)


def load_env_config(prefix: str) -> Dict[str, Any]:
    """加载环境变量配置的便捷函数"""
    return ConfigEnvLoader.load_env_config(prefix)
