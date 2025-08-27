#!/usr/bin/env python3
"""
API路由模块
"""

from .auth_routes import router as auth_router

__all__ = [
    "auth_router"
]
