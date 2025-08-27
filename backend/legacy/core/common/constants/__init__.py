"""
统一常量定义模块
================

提供全项目统一的常量定义
"""

from .system_constants import *
from .business_constants import *
from .config_constants import *

__all__ = [
    # 系统常量
    'DEFAULT_PAGE_SIZE',
    'MAX_PAGE_SIZE',
    'DEFAULT_TIMEOUT',
    'MAX_RETRY_ATTEMPTS',
    'SERVICE_HEALTH_CHECK_INTERVAL',
    
    # 业务常量
    'MIN_ORDER_AMOUNT',
    'MAX_ORDER_AMOUNT',
    'DEFAULT_LEVERAGE',
    'MAX_LEVERAGE',
    'RISK_WARNING_THRESHOLD',
    'STOP_LOSS_THRESHOLD',
    
    # 配置常量
    'CONFIG_FILE_PATHS',
    'LOG_LEVELS',
    'DATABASE_POOL_SIZES',
    'CACHE_TTL_VALUES'
]
