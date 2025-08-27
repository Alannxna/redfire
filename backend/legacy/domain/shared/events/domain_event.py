"""
领域事件基类

定义领域事件的基本结构和行为
"""

from datetime import datetime
from typing import Any, Dict, Optional
from dataclasses import dataclass, field
from abc import ABC


@dataclass
class DomainEvent(ABC):
    """领域事件基类
    
    所有领域事件都应该继承此类
    """
    
    # 事件发生时间
    occurred_at: datetime = field(default_factory=datetime.now)
    
    # 事件类型（子类应该重写）
    event_type: str = "domain_event"
    
    # 事件版本
    version: str = "1.0"
    
    # 聚合根ID（可选）
    aggregate_id: Optional[str] = None
    
    # 事件元数据
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """初始化后处理"""
        # 确保occurred_at是datetime对象
        if not isinstance(self.occurred_at, datetime):
            self.occurred_at = datetime.now()
    
    @property
    def event_id(self) -> str:
        """事件唯一标识"""
        import uuid
        return str(uuid.uuid4())
    
    def add_metadata(self, key: str, value: Any) -> None:
        """添加元数据
        
        Args:
            key: 元数据键
            value: 元数据值
        """
        self.metadata[key] = value
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """获取元数据
        
        Args:
            key: 元数据键
            default: 默认值
            
        Returns:
            元数据值
        """
        return self.metadata.get(key, default)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式
        
        Returns:
            事件字典表示
        """
        from dataclasses import asdict
        return asdict(self)
    
    def __str__(self) -> str:
        """字符串表示"""
        return f"{self.event_type}(occurred_at={self.occurred_at})"
