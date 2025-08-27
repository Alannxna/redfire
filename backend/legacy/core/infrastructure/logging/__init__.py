"""
日志基础设施模块

提供统一的日志管理和配置
"""

from .log_manager import LogManager, LogConfig, get_logger
from .formatters import StructuredFormatter, JSONFormatter

def configure_logging(config: dict = None):
    """配置日志系统"""
    if config is None:
        config = {
            "level": "INFO",
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        }
    
    import logging
    logging.basicConfig(
        level=getattr(logging, config.get("level", "INFO")),
        format=config.get("format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )

__all__ = [
    "LogManager",
    "LogConfig",
    "get_logger",
    "StructuredFormatter",
    "JSONFormatter",
    "configure_logging"
]
