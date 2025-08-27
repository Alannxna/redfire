"""
日志管理器

提供统一的日志配置和管理功能
"""

import logging
import logging.handlers
import sys
import json
from typing import Dict, Any, Optional, Union
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

from .formatters import StructuredFormatter, JSONFormatter


class LogLevel(Enum):
    """日志级别"""
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


@dataclass
class LogConfig:
    """日志配置"""
    level: Union[str, int] = "INFO"
    format_type: str = "structured"  # structured, json, simple
    enable_console: bool = True
    enable_file: bool = True
    file_path: Optional[str] = None
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5
    enable_json_logs: bool = False
    log_service_name: bool = True
    extra_fields: Dict[str, Any] = None


class LogManager:
    """日志管理器
    
    提供统一的日志配置和管理功能
    """
    
    def __init__(self):
        self._loggers: Dict[str, logging.Logger] = {}
        self._config: Optional[LogConfig] = None
        self._initialized = False
    
    def configure(self, config: LogConfig):
        """配置日志系统"""
        self._config = config
        
        # 设置根日志级别
        root_logger = logging.getLogger()
        root_logger.setLevel(self._get_log_level(config.level))
        
        # 清除现有处理器
        root_logger.handlers.clear()
        
        # 配置控制台处理器
        if config.enable_console:
            self._add_console_handler(root_logger, config)
        
        # 配置文件处理器
        if config.enable_file:
            self._add_file_handler(root_logger, config)
        
        self._initialized = True
    
    def _get_log_level(self, level: Union[str, int]) -> int:
        """获取日志级别"""
        if isinstance(level, str):
            return getattr(logging, level.upper(), logging.INFO)
        return level
    
    def _add_console_handler(self, logger: logging.Logger, config: LogConfig):
        """添加控制台处理器"""
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(self._get_log_level(config.level))
        
        # 设置格式化器
        formatter = self._create_formatter(config, is_console=True)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(console_handler)
    
    def _add_file_handler(self, logger: logging.Logger, config: LogConfig):
        """添加文件处理器"""
        if not config.file_path:
            # 默认日志文件路径
            log_dir = Path("logs")
            log_dir.mkdir(exist_ok=True)
            config.file_path = str(log_dir / "vnpy_web.log")
        
        # 使用RotatingFileHandler实现日志轮转
        file_handler = logging.handlers.RotatingFileHandler(
            config.file_path,
            maxBytes=config.max_file_size,
            backupCount=config.backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(self._get_log_level(config.level))
        
        # 设置格式化器
        formatter = self._create_formatter(config, is_console=False)
        file_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
    
    def _create_formatter(self, config: LogConfig, is_console: bool = True) -> logging.Formatter:
        """创建格式化器"""
        if config.format_type == "json" or (config.enable_json_logs and not is_console):
            return JSONFormatter(
                include_service_name=config.log_service_name,
                extra_fields=config.extra_fields or {}
            )
        elif config.format_type == "structured":
            return StructuredFormatter(
                include_service_name=config.log_service_name,
                use_colors=is_console
            )
        else:
            # 简单格式
            format_str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            return logging.Formatter(format_str)
    
    def get_logger(self, name: str) -> logging.Logger:
        """获取日志记录器"""
        if name in self._loggers:
            return self._loggers[name]
        
        logger = logging.getLogger(name)
        
        # 如果还没有初始化，使用默认配置
        if not self._initialized:
            default_config = LogConfig()
            self.configure(default_config)
        
        self._loggers[name] = logger
        return logger
    
    def set_logger_level(self, name: str, level: Union[str, int]):
        """设置特定日志记录器的级别"""
        logger = self.get_logger(name)
        logger.setLevel(self._get_log_level(level))
    
    def add_custom_handler(self, handler: logging.Handler, logger_name: Optional[str] = None):
        """添加自定义处理器"""
        if logger_name:
            logger = self.get_logger(logger_name)
        else:
            logger = logging.getLogger()
        
        logger.addHandler(handler)
    
    def get_config(self) -> Optional[LogConfig]:
        """获取当前配置"""
        return self._config
    
    def is_initialized(self) -> bool:
        """检查是否已初始化"""
        return self._initialized
    
    @classmethod
    def create_from_dict(cls, config_dict: Dict[str, Any]) -> 'LogManager':
        """从字典创建日志管理器"""
        config = LogConfig(**config_dict)
        manager = cls()
        manager.configure(config)
        return manager


# 全局日志管理器实例
_global_log_manager: Optional[LogManager] = None


def get_log_manager() -> LogManager:
    """获取全局日志管理器"""
    global _global_log_manager
    if _global_log_manager is None:
        _global_log_manager = LogManager()
    return _global_log_manager


def configure_logging(config: Union[LogConfig, Dict[str, Any]]):
    """配置全局日志系统"""
    manager = get_log_manager()
    
    if isinstance(config, dict):
        config = LogConfig(**config)
    
    manager.configure(config)


def get_logger(name: str) -> logging.Logger:
    """获取日志记录器的便捷函数"""
    return get_log_manager().get_logger(name)


def set_logger_level(name: str, level: Union[str, int]):
    """设置日志级别的便捷函数"""
    get_log_manager().set_logger_level(name, level)
