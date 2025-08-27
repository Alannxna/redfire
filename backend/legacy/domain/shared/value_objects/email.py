"""
邮箱值对象

邮箱地址的验证和规范化
"""

import re
from typing import Any

from ....core.base.value_object_base import BaseValueObject
from ....core.common.exceptions.domain_exceptions import DomainException


class Email(BaseValueObject):
    """邮箱值对象
    
    确保邮箱地址格式正确并进行规范化处理
    """
    
    # 邮箱格式正则表达式
    EMAIL_PATTERN = re.compile(
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    )
    
    def __init__(self, value: str):
        if not value:
            raise DomainException("邮箱地址不能为空")
        
        # 规范化：去除空格并转为小写
        normalized_value = value.strip().lower()
        
        # 格式验证
        if not self.EMAIL_PATTERN.match(normalized_value):
            raise DomainException(f"无效的邮箱地址格式: {value}")
        
        # 长度限制
        if len(normalized_value) > 254:  # RFC 5321 限制
            raise DomainException("邮箱地址长度不能超过254个字符")
        
        # 检查本地部分长度
        local_part = normalized_value.split('@')[0]
        if len(local_part) > 64:  # RFC 5321 限制
            raise DomainException("邮箱地址本地部分长度不能超过64个字符")
        
        self._value = normalized_value
    
    @property
    def value(self) -> str:
        """获取邮箱地址值"""
        return self._value
    
    def _get_equality_components(self) -> tuple:
        """获取用于相等性比较的组件"""
        return (self._value,)
    
    def validate(self) -> bool:
        """验证邮箱地址有效性"""
        return self.is_valid(self._value)
    
    @classmethod
    def from_primitive(cls, value: Any) -> 'Email':
        """从原始值创建邮箱地址"""
        if isinstance(value, str):
            return cls(value)
        else:
            raise ValueError(f"无法从 {type(value)} 创建 Email 对象")
    
    @property
    def local_part(self) -> str:
        """获取邮箱的本地部分（@符号前面的部分）
        
        Returns:
            本地部分
        """
        return self.value.split('@')[0]
    
    @property
    def domain(self) -> str:
        """获取邮箱的域名部分（@符号后面的部分）
        
        Returns:
            域名部分
        """
        return self.value.split('@')[1]
    
    @classmethod
    def is_valid(cls, value: str) -> bool:
        """验证邮箱地址是否有效
        
        Args:
            value: 邮箱地址
            
        Returns:
            是否有效
        """
        try:
            cls(value)
            return True
        except DomainException:
            return False
    
    def is_same_domain(self, other: 'Email') -> bool:
        """检查是否与另一个邮箱地址同域
        
        Args:
            other: 另一个邮箱地址
            
        Returns:
            是否同域
        """
        return self.domain == other.domain
    
    def __str__(self) -> str:
        """字符串表示"""
        return self.value
