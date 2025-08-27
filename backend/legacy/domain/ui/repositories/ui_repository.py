"""
UI仓储接口

定义UI相关数据的持久化接口
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime

from src.domain.ui.entities.ui_entity import (
    UIComponent, UIEvent, UILogEntry, UISession, UIAlert, UIState,
    UIComponentType, UIEventType, LogLevel, AlertLevel
)


class UIComponentRepository(ABC):
    """UI组件仓储接口"""
    
    @abstractmethod
    async def save(self, component: UIComponent) -> UIComponent:
        """保存UI组件"""
        pass
    
    @abstractmethod
    async def find_by_id(self, component_id: str) -> Optional[UIComponent]:
        """根据ID查找组件"""
        pass
    
    @abstractmethod
    async def find_by_user_id(self, user_id: str) -> List[UIComponent]:
        """根据用户ID查找组件"""
        pass
    
    @abstractmethod
    async def find_by_type(self, component_type: UIComponentType) -> List[UIComponent]:
        """根据组件类型查找"""
        pass
    
    @abstractmethod
    async def find_active_components(self, user_id: Optional[str] = None) -> List[UIComponent]:
        """查找活跃组件"""
        pass
    
    @abstractmethod
    async def update(self, component: UIComponent) -> UIComponent:
        """更新组件"""
        pass
    
    @abstractmethod
    async def delete(self, component_id: str) -> bool:
        """删除组件"""
        pass
    
    @abstractmethod
    async def cleanup_inactive_components(self, hours: int = 24) -> int:
        """清理非活跃组件"""
        pass


class UIEventRepository(ABC):
    """UI事件仓储接口"""
    
    @abstractmethod
    async def save(self, event: UIEvent) -> UIEvent:
        """保存UI事件"""
        pass
    
    @abstractmethod
    async def find_by_id(self, event_id: str) -> Optional[UIEvent]:
        """根据ID查找事件"""
        pass
    
    @abstractmethod
    async def find_by_component_id(self, component_id: str) -> List[UIEvent]:
        """根据组件ID查找事件"""
        pass
    
    @abstractmethod
    async def find_by_user_id(self, user_id: str) -> List[UIEvent]:
        """根据用户ID查找事件"""
        pass
    
    @abstractmethod
    async def find_by_type(self, event_type: UIEventType) -> List[UIEvent]:
        """根据事件类型查找"""
        pass
    
    @abstractmethod
    async def find_recent_events(
        self,
        hours: int = 24,
        user_id: Optional[str] = None,
        event_type: Optional[UIEventType] = None
    ) -> List[UIEvent]:
        """查找近期事件"""
        pass
    
    @abstractmethod
    async def cleanup_old_events(self, days: int = 30) -> int:
        """清理旧事件"""
        pass


class UILogRepository(ABC):
    """UI日志仓储接口"""
    
    @abstractmethod
    async def save(self, log_entry: UILogEntry) -> UILogEntry:
        """保存日志条目"""
        pass
    
    @abstractmethod
    async def find_by_id(self, log_id: str) -> Optional[UILogEntry]:
        """根据ID查找日志"""
        pass
    
    @abstractmethod
    async def find_by_level(self, level: LogLevel, limit: int = 100) -> List[UILogEntry]:
        """根据级别查找日志"""
        pass
    
    @abstractmethod
    async def find_by_user_id(self, user_id: str, limit: int = 100) -> List[UILogEntry]:
        """根据用户ID查找日志"""
        pass
    
    @abstractmethod
    async def find_by_component_id(self, component_id: str, limit: int = 100) -> List[UILogEntry]:
        """根据组件ID查找日志"""
        pass
    
    @abstractmethod
    async def find_recent_logs(
        self,
        hours: int = 24,
        level: Optional[LogLevel] = None,
        user_id: Optional[str] = None,
        limit: int = 100
    ) -> List[UILogEntry]:
        """查找近期日志"""
        pass
    
    @abstractmethod
    async def cleanup_old_logs(self, days: int = 7) -> int:
        """清理旧日志"""
        pass


class UISessionRepository(ABC):
    """UI会话仓储接口"""
    
    @abstractmethod
    async def save(self, session: UISession) -> UISession:
        """保存会话"""
        pass
    
    @abstractmethod
    async def find_by_id(self, session_id: str) -> Optional[UISession]:
        """根据ID查找会话"""
        pass
    
    @abstractmethod
    async def find_by_user_id(self, user_id: str) -> List[UISession]:
        """根据用户ID查找会话"""
        pass
    
    @abstractmethod
    async def find_active_sessions(self) -> List[UISession]:
        """查找活跃会话"""
        pass
    
    @abstractmethod
    async def update(self, session: UISession) -> UISession:
        """更新会话"""
        pass
    
    @abstractmethod
    async def cleanup_expired_sessions(self, timeout_minutes: int = 30) -> int:
        """清理过期会话"""
        pass


class UIAlertRepository(ABC):
    """UI警告仓储接口"""
    
    @abstractmethod
    async def save(self, alert: UIAlert) -> UIAlert:
        """保存警告"""
        pass
    
    @abstractmethod
    async def find_by_id(self, alert_id: str) -> Optional[UIAlert]:
        """根据ID查找警告"""
        pass
    
    @abstractmethod
    async def find_by_user_id(self, user_id: str, include_read: bool = False) -> List[UIAlert]:
        """根据用户ID查找警告"""
        pass
    
    @abstractmethod
    async def find_by_level(self, level: AlertLevel) -> List[UIAlert]:
        """根据级别查找警告"""
        pass
    
    @abstractmethod
    async def find_unread_alerts(self, user_id: Optional[str] = None) -> List[UIAlert]:
        """查找未读警告"""
        pass
    
    @abstractmethod
    async def mark_as_read(self, alert_id: str) -> bool:
        """标记为已读"""
        pass
    
    @abstractmethod
    async def cleanup_old_alerts(self, days: int = 30) -> int:
        """清理旧警告"""
        pass


class UIStateRepository(ABC):
    """UI状态仓储接口"""
    
    @abstractmethod
    async def save(self, user_id: str, state: UIState) -> UIState:
        """保存UI状态"""
        pass
    
    @abstractmethod
    async def find_by_user_id(self, user_id: str) -> Optional[UIState]:
        """根据用户ID查找状态"""
        pass
    
    @abstractmethod
    async def update(self, user_id: str, state: UIState) -> UIState:
        """更新UI状态"""
        pass
    
    @abstractmethod
    async def delete(self, user_id: str) -> bool:
        """删除UI状态"""
        pass
