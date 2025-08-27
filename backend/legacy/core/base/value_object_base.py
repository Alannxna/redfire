"""
值对象基类
==========

定义领域驱动设计中的值对象基类
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Tuple
from dataclasses import dataclass


class BaseValueObject(ABC):
    """
    值对象基类
    
    值对象是不变的对象，相等性基于其属性值而不是标识
    值对象应该是不可变的，修改操作应该返回新的值对象实例
    """
    
    def __eq__(self, other) -> bool:
        """值对象相等性比较基于所有属性值"""
        if not isinstance(other, self.__class__):
            return False
        return self._get_equality_components() == other._get_equality_components()
    
    def __hash__(self) -> int:
        """值对象哈希基于所有属性值"""
        return hash(self._get_equality_components())
    
    def __str__(self) -> str:
        """字符串表示"""
        components = self._get_equality_components()
        if isinstance(components, tuple) and len(components) == 1:
            return str(components[0])
        return str(components)
    
    def __repr__(self) -> str:
        """详细字符串表示"""
        components = self._get_equality_components()
        return f"{self.__class__.__name__}({components})"
    
    @abstractmethod
    def _get_equality_components(self) -> Tuple:
        """
        获取用于相等性比较的组件
        
        Returns:
            Tuple: 用于比较的属性值元组
        """
        pass
    
    @abstractmethod
    def validate(self) -> bool:
        """
        验证值对象的业务规则
        
        Returns:
            bool: 是否通过验证
        """
        pass
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典
        
        Returns:
            Dict[str, Any]: 值对象的字典表示
        """
        # 默认实现，子类可以重写
        return {"value": self._get_equality_components()}
    
    @classmethod
    @abstractmethod
    def from_primitive(cls, value: Any) -> 'BaseValueObject':
        """
        从原始值创建值对象
        
        Args:
            value: 原始值
            
        Returns:
            BaseValueObject: 值对象实例
        """
        pass
    
    def to_primitive(self) -> Any:
        """
        转换为原始值
        
        Returns:
            Any: 原始值
        """
        components = self._get_equality_components()
        if isinstance(components, tuple) and len(components) == 1:
            return components[0]
        return components


# 常用值对象实现示例

@dataclass(frozen=True)
class Money(BaseValueObject):
    """金额值对象"""
    
    amount: float
    currency: str = "CNY"
    
    def _get_equality_components(self) -> Tuple:
        return (self.amount, self.currency)
    
    def validate(self) -> bool:
        """验证金额有效性"""
        return (
            self.amount >= 0 and
            isinstance(self.currency, str) and
            len(self.currency) == 3
        )
    
    @classmethod
    def from_primitive(cls, value: Any) -> 'Money':
        """从原始值创建金额对象"""
        if isinstance(value, (int, float)):
            return cls(float(value))
        elif isinstance(value, dict):
            return cls(value.get("amount", 0), value.get("currency", "CNY"))
        elif isinstance(value, str):
            return cls(float(value))
        else:
            raise ValueError(f"无法从 {type(value)} 创建 Money 对象")
    
    def add(self, other: 'Money') -> 'Money':
        """加法运算"""
        if self.currency != other.currency:
            raise ValueError("不同货币无法直接相加")
        return Money(self.amount + other.amount, self.currency)
    
    def subtract(self, other: 'Money') -> 'Money':
        """减法运算"""
        if self.currency != other.currency:
            raise ValueError("不同货币无法直接相减")
        return Money(self.amount - other.amount, self.currency)
    
    def multiply(self, factor: float) -> 'Money':
        """乘法运算"""
        return Money(self.amount * factor, self.currency)
    
    def divide(self, divisor: float) -> 'Money':
        """除法运算"""
        if divisor == 0:
            raise ValueError("除数不能为零")
        return Money(self.amount / divisor, self.currency)
    
    def is_positive(self) -> bool:
        """是否为正数"""
        return self.amount > 0
    
    def is_negative(self) -> bool:
        """是否为负数"""
        return self.amount < 0
    
    def is_zero(self) -> bool:
        """是否为零"""
        return self.amount == 0


@dataclass(frozen=True)
class Price(BaseValueObject):
    """价格值对象"""
    
    value: float
    precision: int = 2
    
    def _get_equality_components(self) -> Tuple:
        return (round(self.value, self.precision), self.precision)
    
    def validate(self) -> bool:
        """验证价格有效性"""
        return (
            self.value >= 0 and
            self.precision >= 0 and
            isinstance(self.precision, int)
        )
    
    @classmethod
    def from_primitive(cls, value: Any) -> 'Price':
        """从原始值创建价格对象"""
        if isinstance(value, (int, float)):
            return cls(float(value))
        elif isinstance(value, dict):
            return cls(value.get("value", 0), value.get("precision", 2))
        elif isinstance(value, str):
            return cls(float(value))
        else:
            raise ValueError(f"无法从 {type(value)} 创建 Price 对象")
    
    def to_primitive(self) -> float:
        """转换为原始浮点数"""
        return round(self.value, self.precision)
    
    def to_string(self) -> str:
        """转换为格式化字符串"""
        return f"{self.value:.{self.precision}f}"


@dataclass(frozen=True)
class Volume(BaseValueObject):
    """数量值对象"""
    
    value: float
    unit: str = "手"
    
    def _get_equality_components(self) -> Tuple:
        return (self.value, self.unit)
    
    def validate(self) -> bool:
        """验证数量有效性"""
        return self.value >= 0
    
    @classmethod
    def from_primitive(cls, value: Any) -> 'Volume':
        """从原始值创建数量对象"""
        if isinstance(value, (int, float)):
            return cls(float(value))
        elif isinstance(value, dict):
            return cls(value.get("value", 0), value.get("unit", "手"))
        elif isinstance(value, str):
            return cls(float(value))
        else:
            raise ValueError(f"无法从 {type(value)} 创建 Volume 对象")
    
    def add(self, other: 'Volume') -> 'Volume':
        """加法运算"""
        if self.unit != other.unit:
            raise ValueError("不同单位无法直接相加")
        return Volume(self.value + other.value, self.unit)
    
    def subtract(self, other: 'Volume') -> 'Volume':
        """减法运算"""
        if self.unit != other.unit:
            raise ValueError("不同单位无法直接相减")
        return Volume(self.value - other.value, self.unit)


@dataclass(frozen=True)
class EmailAddress(BaseValueObject):
    """邮箱地址值对象"""
    
    value: str
    
    def _get_equality_components(self) -> Tuple:
        return (self.value.lower(),)
    
    def validate(self) -> bool:
        """验证邮箱地址有效性"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, self.value))
    
    @classmethod
    def from_primitive(cls, value: Any) -> 'EmailAddress':
        """从原始值创建邮箱地址对象"""
        if isinstance(value, str):
            email = cls(value.strip())
            if not email.validate():
                raise ValueError(f"无效的邮箱地址: {value}")
            return email
        else:
            raise ValueError(f"无法从 {type(value)} 创建 EmailAddress 对象")
    
    @property
    def domain(self) -> str:
        """获取域名部分"""
        return self.value.split('@')[1] if '@' in self.value else ""
    
    @property
    def local_part(self) -> str:
        """获取本地部分"""
        return self.value.split('@')[0] if '@' in self.value else self.value


@dataclass(frozen=True)
class DateRange(BaseValueObject):
    """日期范围值对象"""
    
    start_date: str  # ISO format date string
    end_date: str    # ISO format date string
    
    def _get_equality_components(self) -> Tuple:
        return (self.start_date, self.end_date)
    
    def validate(self) -> bool:
        """验证日期范围有效性"""
        try:
            from datetime import datetime
            start = datetime.fromisoformat(self.start_date)
            end = datetime.fromisoformat(self.end_date)
            return start <= end
        except ValueError:
            return False
    
    @classmethod
    def from_primitive(cls, value: Any) -> 'DateRange':
        """从原始值创建日期范围对象"""
        if isinstance(value, dict):
            range_obj = cls(value.get("start_date", ""), value.get("end_date", ""))
            if not range_obj.validate():
                raise ValueError(f"无效的日期范围: {value}")
            return range_obj
        else:
            raise ValueError(f"无法从 {type(value)} 创建 DateRange 对象")
    
    def contains_date(self, date_str: str) -> bool:
        """检查是否包含指定日期"""
        try:
            from datetime import datetime
            date = datetime.fromisoformat(date_str)
            start = datetime.fromisoformat(self.start_date)
            end = datetime.fromisoformat(self.end_date)
            return start <= date <= end
        except ValueError:
            return False
    
    def duration_days(self) -> int:
        """获取持续天数"""
        try:
            from datetime import datetime
            start = datetime.fromisoformat(self.start_date)
            end = datetime.fromisoformat(self.end_date)
            return (end - start).days
        except ValueError:
            return 0
