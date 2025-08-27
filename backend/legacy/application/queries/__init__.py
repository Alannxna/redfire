"""
查询层 - Query Pattern Implementation

实现查询模式，处理所有的读操作
遵循CQRS模式的查询端设计
"""

from .base_query import BaseQuery, BaseQueryHandler
from .query_bus import QueryBus

__all__ = [
    "BaseQuery",
    "BaseQueryHandler",
    "QueryBus"
]
