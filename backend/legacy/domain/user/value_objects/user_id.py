"""
用户ID值对象

用户唯一标识符
"""

import uuid
from typing import Any

from ....core.base.value_object_base import BaseValueObject
from ....core.common.exceptions.domain_exceptions import DomainException


class UserId(BaseValueObject):
    """用户ID值对象
    
    确保用户ID的格式正确性和唯一性
    """
    
    def __init__(self, value: str = None):
        if value is None:
            value = str(uuid.uuid4())
        
        if not value:
            raise DomainException("用户ID不能为空")
        
        # 验证UUID格式
        try:
            uuid.UUID(value)
        except ValueError:
            raise DomainException(f"无效的用户ID格式: {value}")
        
        self._value = value
    
    @property
    def value(self) -> str:
        """获取用户ID值"""
        return self._value
    
    def _get_equality_components(self) -> tuple:
        """获取用于相等性比较的组件"""
        return (self._value,)
    
    def validate(self) -> bool:
        """验证用户ID有效性"""
        if not self._value:
            return False
        try:
            uuid.UUID(self._value)
            return True
        except ValueError:
            return False
    
    @classmethod
    def from_primitive(cls, value: Any) -> 'UserId':
        """从原始值创建用户ID"""
        if isinstance(value, str):
            return cls(value)
        else:
            raise ValueError(f"无法从 {type(value)} 创建 UserId 对象")
    
    @classmethod
    def generate(cls) -> 'UserId':
        """生成新的用户ID
        
        Returns:
            新的用户ID值对象
        """
        return cls(str(uuid.uuid4()))
    
    @classmethod
    def from_string(cls, value: str) -> 'UserId':
        """从字符串创建用户ID
        
        Args:
            value: 用户ID字符串
            
        Returns:
            用户ID值对象
        """
        return cls(value)
    
    def __str__(self) -> str:
        """字符串表示"""
        return self.value
