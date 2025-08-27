"""
基础查询和查询处理器

实现查询模式的基础抽象类
"""

# 标准库导入
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import TypeVar, Generic, Any, Dict, Optional, List

# 核心层导入
from ...core.common.exceptions import ApplicationException


@dataclass
class BaseQuery(ABC):
    """查询基类
    
    所有查询都应继承此类
    查询是不可变对象，包含执行查询所需的所有参数
    """
    query_id: str = None
    user_id: Optional[str] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.query_id is None:
            self.query_id = str(uuid.uuid4())
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'query_id': self.query_id,
            'user_id': self.user_id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'query_type': self.__class__.__name__
        }


@dataclass
class PaginationQuery(BaseQuery):
    """分页查询基类"""
    page: int = 1
    page_size: int = 20
    sort_field: Optional[str] = None
    sort_order: str = "asc"  # asc 或 desc
    
    def __post_init__(self):
        super().__post_init__()
        if self.page < 1:
            self.page = 1
        if self.page_size < 1 or self.page_size > 1000:
            self.page_size = 20
        if self.sort_order not in ["asc", "desc"]:
            self.sort_order = "asc"
    
    @property
    def offset(self) -> int:
        """计算偏移量"""
        return (self.page - 1) * self.page_size


TQuery = TypeVar('TQuery', bound=BaseQuery)
TResult = TypeVar('TResult')


class BaseQueryHandler(Generic[TQuery, TResult], ABC):
    """查询处理器基类
    
    负责处理特定类型的查询
    实现查询验证、执行和结果返回
    """
    
    @abstractmethod
    async def handle(self, query: TQuery) -> TResult:
        """处理查询
        
        Args:
            query: 要处理的查询
            
        Returns:
            查询结果
            
        Raises:
            ApplicationException: 查询处理失败
        """
        pass
    
    async def validate(self, query: TQuery) -> None:
        """验证查询
        
        Args:
            query: 要验证的查询
            
        Raises:
            ApplicationException: 验证失败
        """
        if not query.query_id:
            raise ApplicationException("查询ID不能为空")
    
    def get_query_type(self) -> type:
        """获取处理的查询类型"""
        return self.__orig_bases__[0].__args__[0]


class QueryResult:
    """查询结果包装器"""
    
    def __init__(self, data: Any = None, total_count: Optional[int] = None,
                 page: Optional[int] = None, page_size: Optional[int] = None,
                 message: str = "查询成功", meta: Optional[Dict[str, Any]] = None):
        self.data = data
        self.total_count = total_count
        self.page = page
        self.page_size = page_size
        self.message = message
        self.meta = meta or {}
        self.timestamp = datetime.utcnow()
    
    @property
    def total_pages(self) -> Optional[int]:
        """计算总页数"""
        if self.total_count is not None and self.page_size:
            return (self.total_count + self.page_size - 1) // self.page_size
        return None
    
    @property
    def has_next(self) -> bool:
        """是否有下一页"""
        if self.page and self.total_pages:
            return self.page < self.total_pages
        return False
    
    @property
    def has_previous(self) -> bool:
        """是否有上一页"""
        if self.page:
            return self.page > 1
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = {
            'data': self.data,
            'message': self.message,
            'timestamp': self.timestamp.isoformat(),
            'meta': self.meta
        }
        
        # 如果是分页查询，添加分页信息
        if self.total_count is not None:
            result['pagination'] = {
                'total_count': self.total_count,
                'total_pages': self.total_pages,
                'current_page': self.page,
                'page_size': self.page_size,
                'has_next': self.has_next,
                'has_previous': self.has_previous
            }
        
        return result
    
    @classmethod
    def empty_result(cls, message: str = "未找到数据") -> 'QueryResult':
        """创建空结果"""
        return cls(data=[], message=message)
    
    @classmethod
    def single_result(cls, data: Any, message: str = "查询成功") -> 'QueryResult':
        """创建单个结果"""
        return cls(data=data, message=message)
    
    @classmethod
    def paginated_result(cls, data: List[Any], total_count: int, 
                        page: int, page_size: int, 
                        message: str = "查询成功") -> 'QueryResult':
        """创建分页结果"""
        return cls(
            data=data,
            total_count=total_count,
            page=page,
            page_size=page_size,
            message=message
        )


# 为了向后兼容，添加别名
PaginatedQuery = PaginationQuery
