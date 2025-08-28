"""
数据库包
========

统一的数据库管理模块
"""

from .connection import DatabaseManager, get_db

__all__ = ['DatabaseManager', 'get_db']