"""
查询总线实现
============

提供查询的分发和处理功能
"""

# 标准库导入
import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, Type, Any, Optional, List

# 核心层导入
from ...core.base.exceptions import DomainException


class Query(ABC):
    """查询基类"""
    
    def __init__(self):
        self.query_id: str = ""
        self.timestamp: str = ""
        self.user_id: Optional[str] = None
        self.correlation_id: Optional[str] = None


class QueryHandler(ABC):
    """查询处理器基类"""
    
    @abstractmethod
    async def handle(self, query: Query) -> Any:
        """处理查询"""
        pass


class QueryResult:
    """查询执行结果"""
    
    def __init__(self, success: bool = True, data: Any = None, 
                 error: Optional[str] = None, total_count: Optional[int] = None):
        self.success = success
        self.data = data
        self.error = error
        self.total_count = total_count


class PaginatedQuery(Query):
    """分页查询基类"""
    
    def __init__(self, page: int = 1, page_size: int = 20):
        super().__init__()
        self.page = max(1, page)
        self.page_size = min(max(1, page_size), 100)  # 限制最大页面大小
    
    @property
    def offset(self) -> int:
        """计算偏移量"""
        return (self.page - 1) * self.page_size


class IQueryBus(ABC):
    """查询总线接口"""
    
    @abstractmethod
    async def dispatch(self, query: Query) -> QueryResult:
        """分发查询"""
        pass
    
    @abstractmethod
    def register_handler(self, query_type: Type[Query], handler: QueryHandler) -> None:
        """注册查询处理器"""
        pass


class QueryBus(IQueryBus):
    """查询总线"""
    
    def __init__(self):
        self._handlers: Dict[Type[Query], QueryHandler] = {}
        self._logger = logging.getLogger(__name__)
    
    def register_handler(self, query_type: Type[Query], handler: QueryHandler):
        """注册查询处理器"""
        self._handlers[query_type] = handler
        self._logger.debug(f"注册查询处理器: {query_type.__name__} -> {handler.__class__.__name__}")
    
    async def dispatch(self, query: Query) -> QueryResult:
        """分发查询"""
        query_type = type(query)
        
        if query_type not in self._handlers:
            error_msg = f"未找到查询处理器: {query_type.__name__}"
            self._logger.error(error_msg)
            return QueryResult(success=False, error=error_msg)
        
        handler = self._handlers[query_type]
        
        try:
            self._logger.info(f"执行查询: {query_type.__name__}")
            result = await handler.handle(query)
            
            # 处理分页查询结果
            if isinstance(query, PaginatedQuery) and isinstance(result, dict):
                return QueryResult(
                    success=True, 
                    data=result.get('items', result),
                    total_count=result.get('total_count')
                )
            
            return QueryResult(success=True, data=result)
            
        except DomainException as e:
            self._logger.warning(f"查询执行失败 - 领域异常: {e}")
            return QueryResult(success=False, error=str(e))
            
        except Exception as e:
            self._logger.error(f"查询执行失败 - 系统异常: {e}")
            return QueryResult(success=False, error=f"系统错误: {str(e)}")
    
    def get_registered_handlers(self) -> Dict[str, str]:
        """获取已注册的处理器列表"""
        return {
            query_type.__name__: handler.__class__.__name__ 
            for query_type, handler in self._handlers.items()
        }


# 全局查询总线实例
query_bus = QueryBus()