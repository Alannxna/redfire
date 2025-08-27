"""
实体基类
========

定义领域驱动设计中的实体基类
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, TypeVar
from datetime import datetime
from uuid import UUID, uuid4


class BaseEntity(ABC):
    """
    实体基类
    
    实体是具有唯一标识的领域对象
    实体的相等性基于其标识而不是属性值
    """
    
    def __init__(self, entity_id: Optional[str] = None):
        """
        初始化实体
        
        Args:
            entity_id: 实体唯一标识，如果为None则自动生成
        """
        self._id = entity_id or str(uuid4())
        self._created_at = datetime.now()
        self._updated_at = datetime.now()
        self._version = 1
        self._domain_events: List[Dict[str, Any]] = []
    
    @property
    def id(self) -> str:
        """获取实体ID"""
        return self._id
    
    @property
    def created_at(self) -> datetime:
        """获取创建时间"""
        return self._created_at
    
    @property
    def updated_at(self) -> datetime:
        """获取更新时间"""
        return self._updated_at
    
    @property
    def version(self) -> int:
        """获取版本号（用于乐观锁）"""
        return self._version
    
    @property
    def domain_events(self) -> List[Dict[str, Any]]:
        """获取领域事件列表"""
        return self._domain_events.copy()
    
    def mark_as_modified(self):
        """标记实体已修改"""
        self._updated_at = datetime.now()
        self._version += 1
    
    def add_domain_event(self, event_type: str, event_data: Dict[str, Any] = None):
        """
        添加领域事件
        
        Args:
            event_type: 事件类型
            event_data: 事件数据
        """
        if event_data is None:
            event_data = {}
        event = {
            "event_type": event_type,
            "event_data": event_data,
            "entity_id": self._id,
            "entity_type": self.__class__.__name__,
            "timestamp": datetime.now().isoformat(),
            "version": self._version
        }
        self._domain_events.append(event)
    
    def clear_domain_events(self):
        """清空领域事件"""
        self._domain_events.clear()
    
    def __eq__(self, other) -> bool:
        """实体相等性比较基于ID"""
        if not isinstance(other, BaseEntity):
            return False
        return self._id == other._id
    
    def __hash__(self) -> int:
        """实体哈希基于ID"""
        return hash(self._id)
    
    def __str__(self) -> str:
        """字符串表示"""
        return f"{self.__class__.__name__}(id={self._id})"
    
    def __repr__(self) -> str:
        """详细字符串表示"""
        return (f"{self.__class__.__name__}("
                f"id={self._id}, "
                f"version={self._version}, "
                f"created_at={self._created_at}, "
                f"updated_at={self._updated_at})")
    
    @abstractmethod
    def validate(self) -> bool:
        """
        验证实体的业务规则
        
        Returns:
            bool: 是否通过验证
        """
        pass
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典
        
        Returns:
            Dict[str, Any]: 实体的字典表示
        """
        return {
            "id": self._id,
            "created_at": self._created_at.isoformat(),
            "updated_at": self._updated_at.isoformat(),
            "version": self._version
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BaseEntity':
        """
        从字典创建实体
        
        Args:
            data: 实体数据字典
            
        Returns:
            BaseEntity: 实体实例
        """
        entity = cls(data.get("id"))
        if "created_at" in data:
            entity._created_at = datetime.fromisoformat(data["created_at"])
        if "updated_at" in data:
            entity._updated_at = datetime.fromisoformat(data["updated_at"])
        if "version" in data:
            entity._version = data["version"]
        return entity


class BaseAggregateRoot(BaseEntity):
    """
    聚合根基类
    
    聚合根是聚合的唯一入口点，负责维护聚合的一致性
    """
    
    def __init__(self, entity_id: Optional[str] = None):
        super().__init__(entity_id)
        self._child_entities: Dict[str, List[BaseEntity]] = {}
    
    def add_child_entity(self, entity_type: str, entity: BaseEntity):
        """
        添加子实体
        
        Args:
            entity_type: 实体类型
            entity: 子实体
        """
        if entity_type not in self._child_entities:
            self._child_entities[entity_type] = []
        self._child_entities[entity_type].append(entity)
        self.mark_as_modified()
    
    def remove_child_entity(self, entity_type: str, entity_id: str) -> bool:
        """
        移除子实体
        
        Args:
            entity_type: 实体类型
            entity_id: 实体ID
            
        Returns:
            bool: 是否成功移除
        """
        if entity_type not in self._child_entities:
            return False
        
        for i, entity in enumerate(self._child_entities[entity_type]):
            if entity.id == entity_id:
                del self._child_entities[entity_type][i]
                self.mark_as_modified()
                return True
        return False
    
    def get_child_entities(self, entity_type: str) -> List[BaseEntity]:
        """
        获取子实体列表
        
        Args:
            entity_type: 实体类型
            
        Returns:
            List[BaseEntity]: 子实体列表
        """
        return self._child_entities.get(entity_type, []).copy()
    
    def get_all_child_entities(self) -> Dict[str, List[BaseEntity]]:
        """
        获取所有子实体
        
        Returns:
            Dict[str, List[BaseEntity]]: 所有子实体字典
        """
        return {k: v.copy() for k, v in self._child_entities.items()}
    
    @abstractmethod
    def check_invariants(self) -> bool:
        """
        检查聚合不变式
        
        Returns:
            bool: 不变式是否满足
        """
        pass
    
    def to_dict(self) -> Dict[str, Any]:
        """扩展字典表示，包含子实体"""
        base_dict = super().to_dict()
        base_dict["child_entities"] = {
            entity_type: [entity.to_dict() for entity in entities]
            for entity_type, entities in self._child_entities.items()
        }
        return base_dict


class EntitySnapshot:
    """
    实体快照
    
    用于实现事件溯源和审计
    """
    
    def __init__(self, entity: BaseEntity, snapshot_type: str = "manual"):
        """
        创建实体快照
        
        Args:
            entity: 要快照的实体
            snapshot_type: 快照类型
        """
        self.entity_id = entity.id
        self.entity_type = entity.__class__.__name__
        self.snapshot_data = entity.to_dict()
        self.snapshot_time = datetime.now()
        self.snapshot_type = snapshot_type
        self.version = entity.version
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "entity_id": self.entity_id,
            "entity_type": self.entity_type,
            "snapshot_data": self.snapshot_data,
            "snapshot_time": self.snapshot_time.isoformat(),
            "snapshot_type": self.snapshot_type,
            "version": self.version
        }
