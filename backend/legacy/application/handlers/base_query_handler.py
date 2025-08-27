"""
基础查询处理器
============

所有查询处理器的基类
"""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Any
from ..queries.base_query import QueryResult

# 定义查询类型变量
Q = TypeVar('Q')


class BaseQueryHandler(Generic[Q], ABC):
    """基础查询处理器抽象基类"""
    
    def __init__(self):
        """初始化查询处理器"""
        pass
    
    @abstractmethod
    async def handle(self, query: Q) -> QueryResult:
        """
        处理查询的抽象方法
        
        Args:
            query: 查询对象
            
        Returns:
            QueryResult: 查询结果
        """
        pass
    
    def validate_query(self, query: Q) -> bool:
        """
        验证查询对象
        
        Args:
            query: 查询对象
            
        Returns:
            bool: 验证是否通过
        """
        return query is not None
    
    def pre_process(self, query: Q) -> Q:
        """
        查询预处理
        
        Args:
            query: 查询对象
            
        Returns:
            Q: 处理后的查询对象
        """
        return query
    
    def post_process(self, result: QueryResult) -> QueryResult:
        """
        结果后处理
        
        Args:
            result: 查询结果
            
        Returns:
            QueryResult: 处理后的结果
        """
        return result
    
    async def execute(self, query: Q) -> QueryResult:
        """
        执行查询的完整流程
        
        Args:
            query: 查询对象
            
        Returns:
            QueryResult: 查询结果
        """
        try:
            # 验证查询
            if not self.validate_query(query):
                return QueryResult(
                    success=False,
                    error="查询对象无效"
                )
            
            # 预处理
            processed_query = self.pre_process(query)
            
            # 执行查询
            result = await self.handle(processed_query)
            
            # 后处理
            final_result = self.post_process(result)
            
            return final_result
            
        except Exception as e:
            return QueryResult(
                success=False,
                error=f"查询执行失败: {str(e)}"
            )
