#!/usr/bin/env python3
"""
交易模块API路由
"""

from .order_routes import router as order_router

__all__ = [
    "order_router"
]
