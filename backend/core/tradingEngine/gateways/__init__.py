"""
交易引擎网关模块

包含所有交易引擎相关的网关接口：
- 基础网关接口
- 模拟网关
"""

from .baseGateway import BaseGateway
from .simGateway import SimGateway

__all__ = [
    'BaseGateway',
    'SimGateway'
]
