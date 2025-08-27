"""
用户名值对象

用户名的业务规则验证
"""

import re
from typing import Any

from ....core.base.value_object_base import BaseValueObject
from ....core.common.exceptions.domain_exceptions import DomainException


class Username(BaseValueObject):
    """用户名值对象
    
    确保用户名符合业务规则和格式要求
    """
    
    MIN_LENGTH = 3
    MAX_LENGTH = 30
    PATTERN = re.compile(r'^[a-zA-Z0-9_-]+$')
    
    def __init__(self, value: str):
        if not value:
            raise DomainException("用户名不能为空")
        
        value = value.strip()
        
        # 长度验证
        if len(value) < self.MIN_LENGTH:
            raise DomainException(f"用户名长度不能少于{self.MIN_LENGTH}个字符")
        
        if len(value) > self.MAX_LENGTH:
            raise DomainException(f"用户名长度不能超过{self.MAX_LENGTH}个字符")
        
        # 格式验证
        if not self.PATTERN.match(value):
            raise DomainException("用户名只能包含字母、数字、下划线和连字符")
        
        # 保留字检查
        if self._is_reserved_word(value):
            raise DomainException(f"用户名 '{value}' 是保留字，不能使用")
        
        self._value = value
    
    @property
    def value(self) -> str:
        """获取用户名值"""
        return self._value
    
    def _get_equality_components(self) -> tuple:
        """获取用于相等性比较的组件"""
        return (self._value,)
    
    def validate(self) -> bool:
        """验证用户名有效性"""
        return self.is_valid(self._value)
    
    @classmethod
    def from_primitive(cls, value: Any) -> 'Username':
        """从原始值创建用户名"""
        if isinstance(value, str):
            return cls(value)
        else:
            raise ValueError(f"无法从 {type(value)} 创建 Username 对象")
    
    def _is_reserved_word(self, value: str) -> bool:
        """检查是否为保留字
        
        Args:
            value: 用户名
            
        Returns:
            是否为保留字
        """
        reserved_words = {
            'admin', 'administrator', 'root', 'system', 'api', 'www',
            'mail', 'email', 'ftp', 'http', 'https', 'smtp', 'pop',
            'imap', 'dns', 'localhost', 'test', 'demo', 'support',
            'help', 'info', 'news', 'blog', 'forum', 'shop', 'store',
            'vnpy', 'trading', 'strategy', 'user', 'users', 'account',
            'accounts', 'login', 'logout', 'register', 'signup', 'signin'
        }
        
        return value.lower() in reserved_words
    
    @classmethod
    def is_valid(cls, value: str) -> bool:
        """验证用户名是否有效
        
        Args:
            value: 用户名
            
        Returns:
            是否有效
        """
        try:
            cls(value)
            return True
        except DomainException:
            return False
    
    def __str__(self) -> str:
        """字符串表示"""
        return self.value
