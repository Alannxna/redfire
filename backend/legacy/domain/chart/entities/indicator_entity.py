"""
技术指标实体
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass, field
from uuid import uuid4
from enum import Enum

from ..value_objects.indicator_type import IndicatorType


class IndicatorStatus(str, Enum):
    """指标状态"""
    INACTIVE = "inactive"
    ACTIVE = "active" 
    CALCULATING = "calculating"
    ERROR = "error"


@dataclass
class Indicator:
    """
    技术指标实体
    
    管理单个技术指标的配置和计算状态
    """
    indicator_id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    indicator_type: IndicatorType = IndicatorType.MA
    parameters: Dict[str, Any] = field(default_factory=dict)
    status: IndicatorStatus = IndicatorStatus.INACTIVE
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    # 计算相关
    _last_calculation: Optional[datetime] = None
    _calculation_count: int = 0
    _error_count: int = 0
    _last_error: Optional[str] = None
    
    def activate(self) -> None:
        """激活指标"""
        self.status = IndicatorStatus.ACTIVE
        self.updated_at = datetime.now()
    
    def deactivate(self) -> None:
        """停用指标"""
        self.status = IndicatorStatus.INACTIVE
        self.updated_at = datetime.now()
    
    def start_calculation(self) -> None:
        """开始计算"""
        self.status = IndicatorStatus.CALCULATING
        self.updated_at = datetime.now()
    
    def complete_calculation(self) -> None:
        """完成计算"""
        self.status = IndicatorStatus.ACTIVE
        self._last_calculation = datetime.now()
        self._calculation_count += 1
        self.updated_at = datetime.now()
    
    def error_occurred(self, error_message: str) -> None:
        """发生错误"""
        self.status = IndicatorStatus.ERROR
        self._error_count += 1
        self._last_error = error_message
        self.updated_at = datetime.now()
    
    def update_parameters(self, parameters: Dict[str, Any]) -> None:
        """更新参数"""
        self.parameters.update(parameters)
        self.updated_at = datetime.now()
    
    @property
    def last_calculation(self) -> Optional[datetime]:
        """最后计算时间"""
        return self._last_calculation
    
    @property
    def calculation_count(self) -> int:
        """计算次数"""
        return self._calculation_count
    
    @property
    def error_count(self) -> int:
        """错误次数"""
        return self._error_count
    
    @property
    def last_error(self) -> Optional[str]:
        """最后错误信息"""
        return self._last_error
    
    @property
    def is_healthy(self) -> bool:
        """是否健康"""
        return self.status != IndicatorStatus.ERROR and self._error_count < 5
    
    @classmethod
    def create(cls, indicator_type: IndicatorType, name: str, parameters: Optional[Dict[str, Any]] = None) -> 'Indicator':
        """创建指标实例"""
        return cls(
            name=name,
            indicator_type=indicator_type,
            parameters=parameters or {}
        )