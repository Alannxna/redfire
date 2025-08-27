"""
查询总线和基础设施
"""

from .base_query import BaseQuery, BaseQueryHandler, QueryResult, PaginationQuery
from .query_bus import QueryBus, IQueryBus, QueryHandler

# 为了保持兼容性，创建一些别名
PaginatedResult = QueryResult

__all__ = [
    'BaseQuery',
    'BaseQueryHandler', 
    'QueryResult',
    'PaginationQuery',
    'QueryBus',
    'IQueryBus',
    'QueryHandler',
    'PaginatedResult'
]
