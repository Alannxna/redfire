#!/usr/bin/env python3
"""
API路由模块
"""

from .base import base_router
from .auth import auth_router
from .trading import order_router
from .strategy import strategy_router

__all__ = [
    "base_router",
    "auth_router", 
    "order_router",
    "strategy_router"
]
