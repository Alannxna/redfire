"""
手机号值对象

手机号码的验证和规范化
"""

import re
from typing import Any

from ....core.base.value_object_base import BaseValueObject
from ....core.common.exceptions.domain_exceptions import DomainException


class Phone(BaseValueObject):
    """手机号值对象
    
    确保手机号码格式正确并进行规范化处理
    """
    
    # 中国大陆手机号格式
    CHINA_MOBILE_PATTERN = re.compile(r'^1[3-9]\d{9}$')
    
    # 国际手机号格式（简化版）
    INTERNATIONAL_PATTERN = re.compile(r'^\+\d{1,3}\d{6,14}$')
    
    def __init__(self, value: str):
        if not value:
            raise DomainException("手机号码不能为空")
        
        # 规范化：去除空格、连字符等
        normalized_value = re.sub(r'[\s\-\(\)]', '', value.strip())
        
        # 如果以+86开头，转换为国内格式
        if normalized_value.startswith('+86'):
            normalized_value = normalized_value[3:]
        elif normalized_value.startswith('86') and len(normalized_value) == 13:
            normalized_value = normalized_value[2:]
        
        # 格式验证
        if not self._is_valid_format(normalized_value):
            raise DomainException(f"无效的手机号码格式: {value}")
        
        super().__init__(normalized_value)
    
    def _is_valid_format(self, value: str) -> bool:
        """验证手机号格式
        
        Args:
            value: 规范化后的手机号
            
        Returns:
            是否有效
        """
        # 中国大陆手机号
        if self.CHINA_MOBILE_PATTERN.match(value):
            return True
        
        # 国际手机号
        if value.startswith('+') and self.INTERNATIONAL_PATTERN.match(value):
            return True
        
        return False
    
    @property
    def is_china_mobile(self) -> bool:
        """是否为中国大陆手机号
        
        Returns:
            是否为中国大陆手机号
        """
        return self.CHINA_MOBILE_PATTERN.match(self.value) is not None
    
    @property
    def international_format(self) -> str:
        """获取国际格式（+86前缀）
        
        Returns:
            国际格式手机号
        """
        if self.is_china_mobile:
            return f"+86{self.value}"
        elif self.value.startswith('+'):
            return self.value
        else:
            # 对于其他格式，假设为国际号码
            return f"+{self.value}"
    
    @property
    def masked(self) -> str:
        """获取掩码格式（中间4位用*替代）
        
        Returns:
            掩码格式手机号
        """
        if self.is_china_mobile and len(self.value) == 11:
            return f"{self.value[:3]}****{self.value[7:]}"
        elif len(self.value) >= 7:
            # 对于其他格式，保留前3位和后3位
            return f"{self.value[:3]}****{self.value[-3:]}"
        else:
            return "****"
    
    @classmethod
    def is_valid(cls, value: str) -> bool:
        """验证手机号是否有效
        
        Args:
            value: 手机号
            
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
