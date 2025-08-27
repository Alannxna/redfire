"""
仓储基类
========

定义领域驱动设计中的仓储模式基类
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, TypeVar, Generic
from uuid import UUID

# 定义泛型类型
T = TypeVar('T')
ID = TypeVar('ID')


class BaseRepository(ABC, Generic[T, ID]):
    """
    仓储基类
    
    提供领域对象的持久化抽象接口
    所有仓储实现都应该继承此基类
    """
    
    @abstractmethod
    async def get_by_id(self, entity_id: ID) -> Optional[T]:
        """
        根据ID获取实体
        
        Args:
            entity_id: 实体ID
            
        Returns:
            Optional[T]: 实体对象或None
        """
        pass
    
    @abstractmethod
    async def save(self, entity: T) -> T:
        """
        保存实体
        
        Args:
            entity: 要保存的实体
            
        Returns:
            T: 保存后的实体
        """
        pass
    
    @abstractmethod
    async def delete(self, entity_id: ID) -> bool:
        """
        删除实体
        
        Args:
            entity_id: 要删除的实体ID
            
        Returns:
            bool: 是否删除成功
        """
        pass
    
    @abstractmethod
    async def find_all(self, limit: int = 100, offset: int = 0) -> List[T]:
        """
        查找所有实体
        
        Args:
            limit: 查询限制数量
            offset: 查询偏移量
            
        Returns:
            List[T]: 实体列表
        """
        pass
    
    @abstractmethod
    async def find_by_criteria(self, criteria: Dict[str, Any]) -> List[T]:
        """
        根据条件查找实体
        
        Args:
            criteria: 查询条件
            
        Returns:
            List[T]: 匹配的实体列表
        """
        pass
    
    @abstractmethod
    async def count(self, criteria: Optional[Dict[str, Any]] = None) -> int:
        """
        统计实体数量
        
        Args:
            criteria: 查询条件，None表示统计全部
            
        Returns:
            int: 实体数量
        """
        pass
    
    @abstractmethod
    async def exists(self, entity_id: ID) -> bool:
        """
        检查实体是否存在
        
        Args:
            entity_id: 实体ID
            
        Returns:
            bool: 是否存在
        """
        pass
    
    async def update(self, entity: T) -> T:
        """
        更新实体（默认实现为保存）
        
        Args:
            entity: 要更新的实体
            
        Returns:
            T: 更新后的实体
        """
        return await self.save(entity)
    
    async def save_batch(self, entities: List[T]) -> List[T]:
        """
        批量保存实体
        
        Args:
            entities: 要保存的实体列表
            
        Returns:
            List[T]: 保存后的实体列表
        """
        result = []
        for entity in entities:
            saved_entity = await self.save(entity)
            result.append(saved_entity)
        return result
    
    async def delete_batch(self, entity_ids: List[ID]) -> int:
        """
        批量删除实体
        
        Args:
            entity_ids: 要删除的实体ID列表
            
        Returns:
            int: 实际删除的数量
        """
        deleted_count = 0
        for entity_id in entity_ids:
            if await self.delete(entity_id):
                deleted_count += 1
        return deleted_count


class BaseReadOnlyRepository(ABC, Generic[T, ID]):
    """
    只读仓储基类
    
    提供只读操作的仓储接口
    """
    
    @abstractmethod
    async def get_by_id(self, entity_id: ID) -> Optional[T]:
        """根据ID获取实体"""
        pass
    
    @abstractmethod
    async def find_all(self, limit: int = 100, offset: int = 0) -> List[T]:
        """查找所有实体"""
        pass
    
    @abstractmethod
    async def find_by_criteria(self, criteria: Dict[str, Any]) -> List[T]:
        """根据条件查找实体"""
        pass
    
    @abstractmethod
    async def count(self, criteria: Optional[Dict[str, Any]] = None) -> int:
        """统计实体数量"""
        pass
    
    @abstractmethod
    async def exists(self, entity_id: ID) -> bool:
        """检查实体是否存在"""
        pass


class BaseWriteOnlyRepository(ABC, Generic[T, ID]):
    """
    只写仓储基类
    
    提供只写操作的仓储接口
    """
    
    @abstractmethod
    async def save(self, entity: T) -> T:
        """保存实体"""
        pass
    
    @abstractmethod
    async def delete(self, entity_id: ID) -> bool:
        """删除实体"""
        pass
    
    async def update(self, entity: T) -> T:
        """更新实体"""
        return await self.save(entity)
    
    async def save_batch(self, entities: List[T]) -> List[T]:
        """批量保存实体"""
        result = []
        for entity in entities:
            saved_entity = await self.save(entity)
            result.append(saved_entity)
        return result


class BaseUnitOfWork(ABC):
    """
    工作单元基类
    
    管理事务边界和聚合根的持久化
    """
    
    def __init__(self):
        self._repositories: Dict[str, BaseRepository] = {}
        self._new_entities: List[Any] = []
        self._dirty_entities: List[Any] = []
        self._removed_entities: List[Any] = []
    
    @abstractmethod
    async def begin(self):
        """开始事务"""
        pass
    
    @abstractmethod
    async def commit(self):
        """提交事务"""
        pass
    
    @abstractmethod
    async def rollback(self):
        """回滚事务"""
        pass
    
    def register_new(self, entity: Any):
        """注册新实体"""
        self._new_entities.append(entity)
    
    def register_dirty(self, entity: Any):
        """注册修改的实体"""
        if entity not in self._dirty_entities:
            self._dirty_entities.append(entity)
    
    def register_removed(self, entity: Any):
        """注册要删除的实体"""
        self._removed_entities.append(entity)
    
    def register_repository(self, name: str, repository: BaseRepository):
        """注册仓储"""
        self._repositories[name] = repository
    
    def get_repository(self, name: str) -> BaseRepository:
        """获取仓储"""
        return self._repositories.get(name)
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.begin()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if exc_type is None:
            await self.commit()
        else:
            await self.rollback()
