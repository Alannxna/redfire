"""
高级管理器子模块

包含以下管理器实现：
1. ConnectionManager - 连接管理器
2. ResourceManager - 资源管理器

作者: RedFire团队
创建时间: 2024年9月2日
"""

from .connectionManager import ConnectionManager, ConnectionPool, ConnectionConfig, ConnectionInstance
from .resourceManager import ResourceManager

__all__ = [
    "ConnectionManager",
    "ConnectionPool", 
    "ConnectionConfig",
    "ConnectionInstance",
    "ResourceManager"
]
