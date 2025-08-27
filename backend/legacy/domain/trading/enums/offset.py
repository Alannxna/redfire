"""
开平仓类型枚举
"""

from enum import Enum
from typing import Dict


class Offset(Enum):
    """开平仓类型枚举"""
    
    OPEN = "OPEN"                    # 开仓
    CLOSE = "CLOSE"                  # 平仓
    CLOSETODAY = "CLOSETODAY"        # 平今
    CLOSEYESTERDAY = "CLOSEYESTERDAY"  # 平昨
    
    @property
    def chinese_name(self) -> str:
        """获取中文名称"""
        return self._chinese_mapping()[self]
    
    @classmethod
    def _chinese_mapping(cls) -> Dict["Offset", str]:
        """中文名称映射"""
        return {
            cls.OPEN: "开仓",
            cls.CLOSE: "平仓",
            cls.CLOSETODAY: "平今",
            cls.CLOSEYESTERDAY: "平昨",
        }
    
    @classmethod
    def from_string(cls, value: str) -> "Offset":
        """从字符串创建Offset对象"""
        value = value.upper()
        for offset in cls:
            if offset.value == value:
                return offset
        raise ValueError(f"Invalid offset: {value}")
    
    def __str__(self) -> str:
        return self.value
    
    def __repr__(self) -> str:
        return f"Offset.{self.name}"
    
    @property
    def is_open(self) -> bool:
        """是否为开仓"""
        return self == Offset.OPEN
    
    @property
    def is_close(self) -> bool:
        """是否为平仓（包括平今、平昨）"""
        return self in (Offset.CLOSE, Offset.CLOSETODAY, Offset.CLOSEYESTERDAY)
    
    @property
    def is_close_today(self) -> bool:
        """是否为平今"""
        return self == Offset.CLOSETODAY
    
    @property
    def is_close_yesterday(self) -> bool:
        """是否为平昨"""
        return self == Offset.CLOSEYESTERDAY
