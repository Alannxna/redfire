#!/usr/bin/env python3
"""
认证模块API路由
"""

from .auth_routes import router as auth_router

__all__ = [
    "auth_router"
]
