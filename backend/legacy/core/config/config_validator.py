"""
配置验证器模块
提供配置验证、热重载和配置管理功能
"""

import os
import json
import yaml
import logging
from typing import Dict, Any, List, Optional, Callable
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import threading
import time


class ConfigValidator:
    """配置验证器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.validation_rules = {}
        self.custom_validators = {}
        
    def add_validation_rule(self, config_key: str, rule: Dict[str, Any]):
        """添加验证规则
        
        Args:
            config_key: 配置键名
            rule: 验证规则字典
        """
        self.validation_rules[config_key] = rule
        
    def add_custom_validator(self, config_key: str, validator: Callable):
        """添加自定义验证器
        
        Args:
            config_key: 配置键名
            validator: 验证函数
        """
        self.custom_validators[config_key] = validator
        
    def validate_config(self, config: Dict[str, Any]) -> Dict[str, List[str]]:
        """验证配置
        
        Args:
            config: 待验证的配置字典
            
        Returns:
            验证结果，包含错误和警告信息
        """
        errors = []
        warnings = []
        
        for key, value in config.items():
            # 检查是否有验证规则
            if key in self.validation_rules:
                rule = self.validation_rules[key]
                result = self._validate_value(key, value, rule)
                errors.extend(result.get('errors', []))
                warnings.extend(result.get('warnings', []))
                
            # 检查是否有自定义验证器
            if key in self.custom_validators:
                try:
                    validator = self.custom_validators[key]
                    if not validator(value):
                        errors.append(f"自定义验证失败: {key}")
                except Exception as e:
                    errors.append(f"自定义验证器异常 {key}: {str(e)}")
                    
        return {
            'errors': errors,
            'warnings': warnings,
            'is_valid': len(errors) == 0
        }
        
    def _validate_value(self, key: str, value: Any, rule: Dict[str, Any]) -> Dict[str, List[str]]:
        """验证单个配置值
        
        Args:
            key: 配置键名
            value: 配置值
            rule: 验证规则
            
        Returns:
            验证结果
        """
        errors = []
        warnings = []
        
        # 类型验证
        if 'type' in rule:
            expected_type = rule['type']
            if not isinstance(value, expected_type):
                errors.append(f"{key}: 期望类型 {expected_type.__name__}, 实际类型 {type(value).__name__}")
                
        # 范围验证
        if 'min' in rule and isinstance(value, (int, float)):
            if value < rule['min']:
                errors.append(f"{key}: 值 {value} 小于最小值 {rule['min']}")
                
        if 'max' in rule and isinstance(value, (int, float)):
            if value > rule['max']:
                errors.append(f"{key}: 值 {value} 大于最大值 {rule['max']}")
                
        # 长度验证
        if 'min_length' in rule and hasattr(value, '__len__'):
            if len(value) < rule['min_length']:
                errors.append(f"{key}: 长度 {len(value)} 小于最小长度 {rule['min_length']}")
                
        if 'max_length' in rule and hasattr(value, '__len__'):
            if len(value) > rule['max_length']:
                errors.append(f"{key}: 长度 {len(value)} 大于最大长度 {rule['max_length']}")
                
        # 枚举值验证
        if 'enum' in rule:
            if value not in rule['enum']:
                errors.append(f"{key}: 值 {value} 不在允许的枚举值中 {rule['enum']}")
                
        # 正则表达式验证
        if 'pattern' in rule and isinstance(value, str):
            import re
            if not re.match(rule['pattern'], value):
                errors.append(f"{key}: 值 {value} 不符合正则表达式 {rule['pattern']}")
                
        # 必需字段验证
        if rule.get('required', False) and value is None:
            errors.append(f"{key}: 必需字段不能为空")
            
        return {'errors': errors, 'warnings': warnings}


class ConfigHotReloader:
    """配置热重载器"""
    
    def __init__(self, config_file: str, callback: Callable[[Dict[str, Any]], None]):
        """初始化热重载器
        
        Args:
            config_file: 配置文件路径
            callback: 配置更新回调函数
        """
        self.config_file = Path(config_file)
        self.callback = callback
        self.observer = Observer()
        self.is_watching = False
        self.logger = logging.getLogger(__name__)
        
    def start_watching(self):
        """开始监控配置文件变化"""
        if self.is_watching:
            return
            
        event_handler = ConfigFileHandler(self.config_file, self.callback)
        self.observer.schedule(event_handler, str(self.config_file.parent), recursive=False)
        self.observer.start()
        self.is_watching = True
        self.logger.info(f"开始监控配置文件: {self.config_file}")
        
    def stop_watching(self):
        """停止监控配置文件变化"""
        if not self.is_watching:
            return
            
        self.observer.stop()
        self.observer.join()
        self.is_watching = False
        self.logger.info("停止监控配置文件")
        
    def __enter__(self):
        self.start_watching()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop_watching()


class ConfigFileHandler(FileSystemEventHandler):
    """配置文件变化处理器"""
    
    def __init__(self, config_file: Path, callback: Callable[[Dict[str, Any]], None]):
        self.config_file = config_file
        self.callback = callback
        self.last_modified = 0
        self.logger = logging.getLogger(__name__)
        
    def on_modified(self, event):
        if event.is_directory:
            return
            
        if event.src_path == str(self.config_file):
            current_time = time.time()
            # 防止重复触发
            if current_time - self.last_modified > 1:
                self.last_modified = current_time
                self.logger.info(f"配置文件发生变化: {self.config_file}")
                try:
                    # 延迟执行，确保文件写入完成
                    threading.Timer(0.5, self._reload_config).start()
                except Exception as e:
                    self.logger.error(f"处理配置文件变化失败: {e}")
                    
    def _reload_config(self):
        """重新加载配置"""
        try:
            # 这里应该调用配置加载器重新加载配置
            # 然后调用回调函数
            self.logger.info("重新加载配置完成")
            # self.callback(new_config)
        except Exception as e:
            self.logger.error(f"重新加载配置失败: {e}")


class LegacyValidationConfigManager:
    """遗留配置验证管理器"""
    
    def __init__(self):
        self.config = {}
        self.validator = ConfigValidator()
        self.hot_reloader = None
        self.logger = logging.getLogger(__name__)
        
        # 设置默认验证规则
        self._setup_default_rules()
        
    def _setup_default_rules(self):
        """设置默认验证规则"""
        # 数据库配置验证规则
        self.validator.add_validation_rule('database', {
            'type': dict,
            'required': True
        })
        
        self.validator.add_validation_rule('database.host', {
            'type': str,
            'required': True,
            'min_length': 1
        })
        
        self.validator.add_validation_rule('database.port', {
            'type': int,
            'min': 1,
            'max': 65535
        })
        
        # 交易引擎配置验证规则
        self.validator.add_validation_rule('trading_engine', {
            'type': dict,
            'required': True
        })
        
        self.validator.add_validation_rule('trading_engine.max_workers', {
            'type': int,
            'min': 1,
            'max': 100
        })
        
        # 日志配置验证规则
        self.validator.add_validation_rule('logging', {
            'type': dict
        })
        
        self.validator.add_validation_rule('logging.level', {
            'type': str,
            'enum': ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        })
        
    def load_config(self, config_file: str) -> bool:
        """加载配置文件
        
        Args:
            config_file: 配置文件路径
            
        Returns:
            是否加载成功
        """
        try:
            config_path = Path(config_file)
            if not config_path.exists():
                self.logger.error(f"配置文件不存在: {config_file}")
                return False
                
            # 根据文件扩展名选择加载方式
            if config_path.suffix.lower() == '.json':
                with open(config_file, 'r', encoding='utf-8') as f:
                    new_config = json.load(f)
            elif config_path.suffix.lower() in ['.yml', '.yaml']:
                with open(config_file, 'r', encoding='utf-8') as f:
                    new_config = yaml.safe_load(f)
            else:
                self.logger.error(f"不支持的配置文件格式: {config_path.suffix}")
                return False
                
            # 验证配置
            validation_result = self.validator.validate_config(new_config)
            if not validation_result['is_valid']:
                self.logger.error("配置验证失败:")
                for error in validation_result['errors']:
                    self.logger.error(f"  - {error}")
                return False
                
            if validation_result['warnings']:
                self.logger.warning("配置验证警告:")
                for warning in validation_result['warnings']:
                    self.logger.warning(f"  - {warning}")
                    
            # 更新配置
            self.config = new_config
            self.logger.info(f"配置文件加载成功: {config_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"加载配置文件失败: {e}")
            return False
            
    def get_config(self, key: str = None, default: Any = None) -> Any:
        """获取配置值
        
        Args:
            key: 配置键名，支持点号分隔的嵌套键
            default: 默认值
            
        Returns:
            配置值
        """
        if key is None:
            return self.config
            
        # 支持嵌套键访问，如 'database.host'
        keys = key.split('.')
        value = self.config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
            
    def set_config(self, key: str, value: Any):
        """设置配置值
        
        Args:
            key: 配置键名，支持点号分隔的嵌套键
            value: 配置值
        """
        keys = key.split('.')
        config = self.config
        
        # 创建嵌套结构
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
            
        config[keys[-1]] = value
        
    def enable_hot_reload(self, config_file: str):
        """启用配置热重载
        
        Args:
            config_file: 配置文件路径
        """
        if self.hot_reloader:
            self.hot_reloader.stop_watching()
            
        self.hot_reloader = ConfigHotReloader(config_file, self._on_config_changed)
        self.hot_reloader.start_watching()
        
    def disable_hot_reload(self):
        """禁用配置热重载"""
        if self.hot_reloader:
            self.hot_reloader.stop_watching()
            self.hot_reloader = None
            
    def _on_config_changed(self, new_config: Dict[str, Any]):
        """配置变化回调函数"""
        self.logger.info("检测到配置变化，重新加载配置")
        # 这里可以实现配置热重载逻辑
        # 比如重新初始化某些组件等
        
    def save_config(self, config_file: str) -> bool:
        """保存配置到文件
        
        Args:
            config_file: 配置文件路径
            
        Returns:
            是否保存成功
        """
        try:
            config_path = Path(config_file)
            
            # 根据文件扩展名选择保存方式
            if config_path.suffix.lower() == '.json':
                with open(config_file, 'w', encoding='utf-8') as f:
                    json.dump(self.config, f, indent=2, ensure_ascii=False)
            elif config_path.suffix.lower() in ['.yml', '.yaml']:
                with open(config_file, 'w', encoding='utf-8') as f:
                    yaml.dump(self.config, f, default_flow_style=False, allow_unicode=True)
            else:
                self.logger.error(f"不支持的配置文件格式: {config_path.suffix}")
                return False
                
            self.logger.info(f"配置文件保存成功: {config_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"保存配置文件失败: {e}")
            return False
            
    def validate_current_config(self) -> Dict[str, List[str]]:
        """验证当前配置
        
        Returns:
            验证结果
        """
        return self.validator.validate_config(self.config)
        
    def get_config_summary(self) -> Dict[str, Any]:
        """获取配置摘要
        
        Returns:
            配置摘要信息
        """
        validation_result = self.validator.validate_config(self.config)
        
        return {
            'config_keys': list(self.config.keys()),
            'total_keys': len(self.config),
            'validation_result': validation_result,
            'hot_reload_enabled': self.hot_reloader is not None
        }
