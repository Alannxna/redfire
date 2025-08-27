"""
UI领域实体

定义UI系统的核心实体和值对象
"""

from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import uuid


class UIComponentType(str, Enum):
    """UI组件类型"""
    MAIN_WINDOW = "main_window"
    TRADING_PANEL = "trading_panel"
    PORTFOLIO_PANEL = "portfolio_panel"
    ORDER_PANEL = "order_panel"
    POSITION_PANEL = "position_panel"
    MARKET_DATA_PANEL = "market_data_panel"
    LOG_PANEL = "log_panel"
    CHART_PANEL = "chart_panel"
    STRATEGY_PANEL = "strategy_panel"
    RISK_PANEL = "risk_panel"


class UIEventType(str, Enum):
    """UI事件类型"""
    COMPONENT_CREATED = "component_created"
    COMPONENT_UPDATED = "component_updated"
    COMPONENT_CLOSED = "component_closed"
    DATA_UPDATED = "data_updated"
    USER_ACTION = "user_action"
    ALERT = "alert"
    CONNECTION_ESTABLISHED = "connection_established"
    CONNECTION_LOST = "connection_lost"


class LogLevel(str, Enum):
    """日志级别"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class AlertLevel(str, Enum):
    """警告级别"""
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class UIPosition:
    """UI位置"""
    x: int = 0
    y: int = 0
    
    def to_dict(self) -> Dict[str, int]:
        return {"x": self.x, "y": self.y}


@dataclass
class UISize:
    """UI尺寸"""
    width: int = 800
    height: int = 600
    
    def to_dict(self) -> Dict[str, int]:
        return {"width": self.width, "height": self.height}


@dataclass
class UIComponent:
    """UI组件实体"""
    component_id: str
    component_type: UIComponentType
    title: str
    config: Dict[str, Any]
    user_id: Optional[str] = None
    is_visible: bool = True
    is_active: bool = True
    position: UIPosition = field(default_factory=UIPosition)
    size: UISize = field(default_factory=UISize)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    @classmethod
    def create(
        cls,
        component_type: UIComponentType,
        title: str,
        config: Dict[str, Any],
        user_id: Optional[str] = None
    ) -> 'UIComponent':
        """创建UI组件"""
        component_id = f"{component_type}_{uuid.uuid4().hex[:8]}"
        
        return cls(
            component_id=component_id,
            component_type=component_type,
            title=title,
            config=config,
            user_id=user_id
        )
    
    def update(self, updates: Dict[str, Any]) -> bool:
        """更新组件"""
        updated = False
        
        for key, value in updates.items():
            if hasattr(self, key) and key not in ['component_id', 'created_at']:
                setattr(self, key, value)
                updated = True
        
        if updated:
            self.updated_at = datetime.now()
        
        return updated
    
    def close(self):
        """关闭组件"""
        self.is_active = False
        self.updated_at = datetime.now()
    
    def hide(self):
        """隐藏组件"""
        self.is_visible = False
        self.updated_at = datetime.now()
    
    def show(self):
        """显示组件"""
        self.is_visible = True
        self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "component_id": self.component_id,
            "component_type": self.component_type.value,
            "title": self.title,
            "config": self.config,
            "user_id": self.user_id,
            "is_visible": self.is_visible,
            "is_active": self.is_active,
            "position": self.position.to_dict(),
            "size": self.size.to_dict(),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


@dataclass
class UIEvent:
    """UI事件实体"""
    event_id: str
    event_type: UIEventType
    component_id: Optional[str]
    user_id: Optional[str]
    data: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    session_id: Optional[str] = None
    
    @classmethod
    def create(
        cls,
        event_type: UIEventType,
        data: Dict[str, Any],
        component_id: Optional[str] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> 'UIEvent':
        """创建UI事件"""
        event_id = f"event_{uuid.uuid4().hex[:8]}"
        
        return cls(
            event_id=event_id,
            event_type=event_type,
            component_id=component_id,
            user_id=user_id,
            data=data,
            session_id=session_id
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "component_id": self.component_id,
            "user_id": self.user_id,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
            "session_id": self.session_id
        }


@dataclass
class UILogEntry:
    """UI日志条目"""
    log_id: str
    level: LogLevel
    message: str
    source: str
    user_id: Optional[str] = None
    component_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    extra_data: Optional[Dict[str, Any]] = None
    
    @classmethod
    def create(
        cls,
        level: LogLevel,
        message: str,
        source: str = "system",
        user_id: Optional[str] = None,
        component_id: Optional[str] = None,
        extra_data: Optional[Dict[str, Any]] = None
    ) -> 'UILogEntry':
        """创建日志条目"""
        log_id = f"log_{uuid.uuid4().hex[:8]}"
        
        return cls(
            log_id=log_id,
            level=level,
            message=message,
            source=source,
            user_id=user_id,
            component_id=component_id,
            extra_data=extra_data or {}
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "log_id": self.log_id,
            "level": self.level.value,
            "message": self.message,
            "source": self.source,
            "user_id": self.user_id,
            "component_id": self.component_id,
            "timestamp": self.timestamp.isoformat(),
            "extra_data": self.extra_data
        }


@dataclass
class UISession:
    """UI会话实体"""
    session_id: str
    user_id: Optional[str]
    connection_type: str  # websocket, http
    client_info: Dict[str, Any]
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    components: List[str] = field(default_factory=list)
    
    @classmethod
    def create(
        cls,
        connection_type: str,
        client_info: Dict[str, Any],
        user_id: Optional[str] = None
    ) -> 'UISession':
        """创建UI会话"""
        session_id = f"session_{uuid.uuid4().hex[:8]}"
        
        return cls(
            session_id=session_id,
            user_id=user_id,
            connection_type=connection_type,
            client_info=client_info
        )
    
    def update_activity(self):
        """更新活动时间"""
        self.last_activity = datetime.now()
    
    def add_component(self, component_id: str):
        """添加组件"""
        if component_id not in self.components:
            self.components.append(component_id)
        self.update_activity()
    
    def remove_component(self, component_id: str):
        """移除组件"""
        if component_id in self.components:
            self.components.remove(component_id)
        self.update_activity()
    
    def close(self):
        """关闭会话"""
        self.is_active = False
        self.last_activity = datetime.now()
    
    def is_expired(self, timeout_minutes: int = 30) -> bool:
        """检查会话是否过期"""
        if not self.is_active:
            return True
        
        timeout = datetime.now() - self.last_activity
        return timeout.total_seconds() > timeout_minutes * 60
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "connection_type": self.connection_type,
            "client_info": self.client_info,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "components": self.components
        }


@dataclass
class UIAlert:
    """UI警告实体"""
    alert_id: str
    level: AlertLevel
    title: str
    message: str
    user_id: Optional[str] = None
    component_id: Optional[str] = None
    is_read: bool = False
    is_persistent: bool = False
    auto_dismiss_seconds: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.now)
    
    @classmethod
    def create(
        cls,
        level: AlertLevel,
        title: str,
        message: str,
        user_id: Optional[str] = None,
        component_id: Optional[str] = None,
        is_persistent: bool = False,
        auto_dismiss_seconds: Optional[int] = None
    ) -> 'UIAlert':
        """创建UI警告"""
        alert_id = f"alert_{uuid.uuid4().hex[:8]}"
        
        return cls(
            alert_id=alert_id,
            level=level,
            title=title,
            message=message,
            user_id=user_id,
            component_id=component_id,
            is_persistent=is_persistent,
            auto_dismiss_seconds=auto_dismiss_seconds
        )
    
    def mark_read(self):
        """标记为已读"""
        self.is_read = True
    
    def should_auto_dismiss(self) -> bool:
        """检查是否应该自动关闭"""
        if self.auto_dismiss_seconds is None:
            return False
        
        elapsed = (datetime.now() - self.created_at).total_seconds()
        return elapsed >= self.auto_dismiss_seconds
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "alert_id": self.alert_id,
            "level": self.level.value,
            "title": self.title,
            "message": self.message,
            "user_id": self.user_id,
            "component_id": self.component_id,
            "is_read": self.is_read,
            "is_persistent": self.is_persistent,
            "auto_dismiss_seconds": self.auto_dismiss_seconds,
            "created_at": self.created_at.isoformat()
        }


@dataclass
class UIState:
    """UI状态聚合根"""
    current_user: Optional[str] = None
    active_symbol: str = ""
    theme: str = "light"
    language: str = "zh-CN"
    layout_config: Dict[str, Any] = field(default_factory=dict)
    preferences: Dict[str, Any] = field(default_factory=dict)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def update(self, updates: Dict[str, Any]) -> bool:
        """更新UI状态"""
        updated = False
        
        for key, value in updates.items():
            if hasattr(self, key) and key != 'updated_at':
                setattr(self, key, value)
                updated = True
        
        if updated:
            self.updated_at = datetime.now()
        
        return updated
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "current_user": self.current_user,
            "active_symbol": self.active_symbol,
            "theme": self.theme,
            "language": self.language,
            "layout_config": self.layout_config,
            "preferences": self.preferences,
            "updated_at": self.updated_at.isoformat()
        }
