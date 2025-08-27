"""
统一枚举定义模块
================

提供全项目统一的枚举定义，避免重复定义
"""

from .service_status import ServiceStatus
from .user_roles import UserRole, TradingPermission
from .order_status import OrderStatus, OrderType, Direction
from .trading_enums import ExchangeType, StrategyStatus, GatewayStatus

__all__ = [
    # 服务状态
    'ServiceStatus',
    
    # 用户角色和权限
    'UserRole',
    'TradingPermission',
    
    # 订单相关
    'OrderStatus',
    'OrderType', 
    'Direction',
    
    # 交易相关
    'ExchangeType',
    'StrategyStatus',
    'GatewayStatus'
]
