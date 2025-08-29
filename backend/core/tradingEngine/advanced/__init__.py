"""
高级交易引擎模块

本模块包含vnpy-engine的高级功能迁移，包括：
1. 高级主引擎 - 多连接管理、负载均衡
2. 连接管理器 - 连接池、故障转移
3. 资源管理器 - 资源分配、监控
4. 引擎工具 - 通用工具函数

作者: RedFire团队
创建时间: 2024年9月2日
"""

from .engines.advancedMainEngine import AdvancedMainEngine
from .engines.multiConnectionEngine import MultiConnectionEngine
from .engines.loadBalancingEngine import LoadBalancingEngine
from .managers.connectionManager import ConnectionManager
from .managers.resourceManager import ResourceManager
from .utils.engineUtils import EngineUtils

__all__ = [
    "AdvancedMainEngine",
    "MultiConnectionEngine", 
    "LoadBalancingEngine",
    "ConnectionManager",
    "ResourceManager",
    "EngineUtils"
]

__version__ = "1.0.0"
__author__ = "RedFire Team"
