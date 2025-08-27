"""
微服务通信模块
=============

提供微服务间通信的基础设施
"""

from .websocket_bus import WebSocketMessageBus, WebSocketConnection
from .service_client import ServiceClient, ServiceResponse
from .event_bus import EventBus, DomainEvent

__all__ = [
    "WebSocketMessageBus",
    "WebSocketConnection", 
    "ServiceClient",
    "ServiceResponse",
    "EventBus",
    "DomainEvent"
]
