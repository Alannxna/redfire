"""
持久化模型基类
提供ORM模型的基础功能
"""

from datetime import datetime
from typing import Any, Dict
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, DateTime, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID
import uuid

# 创建基类
Base = declarative_base()


class BaseModel(Base):
    """ORM模型基类
    
    提供所有数据模型的通用字段和方法
    """
    __abstract__ = True
    
    id = Column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    deleted_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }
    
    def soft_delete(self):
        """软删除"""
        self.deleted_at = datetime.utcnow()
        self.is_active = False
    
    def restore(self):
        """恢复删除"""
        self.deleted_at = None
        self.is_active = True
    
    @property
    def is_deleted(self) -> bool:
        """是否已删除"""
        return self.deleted_at is not None
    
    def __repr__(self) -> str:
        """字符串表示"""
        return f"<{self.__class__.__name__}(id={self.id})>"
