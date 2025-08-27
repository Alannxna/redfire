"""
WebSocket认证中间件
提供WebSocket连接的JWT认证和权限验证
"""

from fastapi import WebSocket, WebSocketDisconnect, HTTPException
from typing import Optional, Dict, Any, List
import json
import logging
from datetime import datetime
import time

from ....application.services.user.user_query_service import UserQueryService
from ....domain.user.entities.user import User
from .auth_middleware import JWTAuthService
from .websocket_permissions import (
    WebSocketPermissionManager,
    WebSocketResourcePermissions,
    get_permission_manager,
    get_resource_permissions
)
from ....core.exceptions.auth_exceptions import AuthenticationError, AuthorizationError

logger = logging.getLogger(__name__)


class WebSocketAuthError(Exception):
    """WebSocket认证错误"""
    def __init__(self, message: str, code: str = "AUTH_ERROR"):
        self.message = message
        self.code = code
        super().__init__(message)


class WebSocketSession:
    """WebSocket会话信息"""
    
    def __init__(
        self,
        websocket: WebSocket,
        session_id: str,
        connected_at: float = None
    ):
        self.websocket = websocket
        self.session_id = session_id
        self.connected_at = connected_at or time.time()
        self.authenticated_at: Optional[float] = None
        self.user: Optional[User] = None
        self.permissions: List[str] = []
        self.is_authenticated = False
        
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "session_id": self.session_id,
            "connected_at": self.connected_at,
            "authenticated_at": self.authenticated_at,
            "user_id": self.user.id if self.user else None,
            "username": self.user.username if self.user else None,
            "permissions": self.permissions,
            "is_authenticated": self.is_authenticated
        }


class WebSocketAuthMiddleware:
    """WebSocket认证中间件"""
    
    def __init__(
        self,
        jwt_service: JWTAuthService,
        user_query_service: UserQueryService
    ):
        self.jwt_service = jwt_service
        self.user_query_service = user_query_service
        self.sessions: Dict[str, WebSocketSession] = {}
        self.permission_manager = get_permission_manager()
        self.resource_permissions = get_resource_permissions()
        
    async def authenticate_websocket(
        self,
        websocket: WebSocket,
        session_id: str,
        token: str
    ) -> WebSocketSession:
        """
        认证WebSocket连接
        
        Args:
            websocket: WebSocket连接
            session_id: 会话ID
            token: JWT令牌
            
        Returns:
            WebSocketSession: 认证后的会话信息
            
        Raises:
            WebSocketAuthError: 认证失败
        """
        try:
            # 验证JWT令牌
            payload = await self.jwt_service.verify_token(token)
            user_id = payload.get("user_id")
            
            if not user_id:
                raise WebSocketAuthError("Invalid token: missing user_id")
            
            # 获取用户信息
            user = await self.user_query_service.get_user_by_id(user_id)
            if not user:
                raise WebSocketAuthError("User not found")
            
            # 检查用户状态
            if not user.is_active:
                raise WebSocketAuthError("User account is deactivated")
            
            # 创建会话
            session = WebSocketSession(websocket, session_id)
            session.user = user
            session.is_authenticated = True
            session.authenticated_at = time.time()
            session.permissions = self._get_user_permissions(user)
            
            # 保存会话
            self.sessions[session_id] = session
            
            logger.info(f"WebSocket authentication successful: {session_id}, user: {user.username}")
            return session
            
        except AuthenticationError as e:
            raise WebSocketAuthError(f"Authentication failed: {str(e)}")
        except Exception as e:
            logger.error(f"WebSocket authentication error: {e}")
            raise WebSocketAuthError(f"Authentication error: {str(e)}")
    
    def _get_user_permissions(self, user: User) -> List[str]:
        """获取用户权限列表"""
        return list(self.permission_manager.get_user_permissions(user.role))
    
    def get_session(self, session_id: str) -> Optional[WebSocketSession]:
        """获取会话信息"""
        return self.sessions.get(session_id)
    
    def remove_session(self, session_id: str):
        """移除会话"""
        if session_id in self.sessions:
            session = self.sessions[session_id]
            logger.info(f"WebSocket session removed: {session_id}, user: {session.user.username if session.user else 'anonymous'}")
            del self.sessions[session_id]
    
    def check_permission(self, session_id: str, permission: str) -> bool:
        """
        检查会话权限
        
        Args:
            session_id: 会话ID
            permission: 权限名称
            
        Returns:
            bool: 是否有权限
        """
        session = self.get_session(session_id)
        if not session or not session.is_authenticated or not session.user:
            return False
        
        return self.permission_manager.check_permission(session.user.role, permission)
    
    def check_resource_access(
        self, 
        session_id: str, 
        resource_type: str, 
        resource_id: str = None
    ) -> bool:
        """
        检查资源访问权限
        
        Args:
            session_id: 会话ID
            resource_type: 资源类型 ('chart', 'trade', 'user_data')
            resource_id: 资源ID
            
        Returns:
            bool: 是否有权限
        """
        session = self.get_session(session_id)
        if not session or not session.is_authenticated or not session.user:
            return False
        
        user_role = session.user.role
        user_id = session.user.id
        
        if resource_type == "chart":
            return self.resource_permissions.can_access_chart(user_role, resource_id, user_id)
        elif resource_type == "trade":
            return self.resource_permissions.can_execute_trade(user_role, user_id)
        elif resource_type == "user_data":
            return self.resource_permissions.can_view_user_data(user_role, resource_id, user_id)
        
        return False
    
    async def send_auth_message(
        self,
        websocket: WebSocket,
        message_type: str,
        data: Dict[str, Any] = None
    ):
        """发送认证相关消息"""
        message = {
            "type": message_type,
            "timestamp": datetime.now().isoformat()
        }
        
        if data:
            message.update(data)
        
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"Failed to send auth message: {e}")
    
    async def handle_auth_message(
        self,
        websocket: WebSocket,
        session_id: str,
        message: Dict[str, Any]
    ) -> WebSocketSession:
        """
        处理认证消息
        
        Args:
            websocket: WebSocket连接
            session_id: 会话ID
            message: 认证消息
            
        Returns:
            WebSocketSession: 认证后的会话
        """
        try:
            token = message.get("token")
            if not token:
                raise WebSocketAuthError("Missing token")
            
            # 执行认证
            session = await self.authenticate_websocket(websocket, session_id, token)
            
            # 发送成功消息
            await self.send_auth_message(websocket, "auth_success", {
                "session_id": session_id,
                "user": {
                    "id": session.user.id,
                    "username": session.user.username,
                    "role": session.user.role
                },
                "permissions": session.permissions
            })
            
            return session
            
        except WebSocketAuthError as e:
            # 发送错误消息
            await self.send_auth_message(websocket, "auth_error", {
                "error": e.message,
                "code": e.code
            })
            raise
    
    def get_authenticated_sessions(self) -> List[WebSocketSession]:
        """获取所有已认证的会话"""
        return [
            session for session in self.sessions.values()
            if session.is_authenticated
        ]
    
    def get_user_sessions(self, user_id: str) -> List[WebSocketSession]:
        """获取指定用户的所有会话"""
        return [
            session for session in self.sessions.values()
            if session.user and session.user.id == user_id
        ]
    
    async def broadcast_to_authenticated(
        self,
        message: Dict[str, Any],
        permission: str = None
    ):
        """
        向所有已认证的会话广播消息
        
        Args:
            message: 要广播的消息
            permission: 可选的权限要求
        """
        disconnected_sessions = []
        
        for session in self.get_authenticated_sessions():
            # 检查权限
            if permission and not self.check_permission(session.session_id, permission):
                continue
            
            try:
                await session.websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Failed to broadcast to session {session.session_id}: {e}")
                disconnected_sessions.append(session.session_id)
        
        # 清理断开的会话
        for session_id in disconnected_sessions:
            self.remove_session(session_id)


# 全局实例（将在依赖注入容器中初始化）
websocket_auth_middleware: Optional[WebSocketAuthMiddleware] = None


def get_websocket_auth_middleware() -> WebSocketAuthMiddleware:
    """获取WebSocket认证中间件实例"""
    if not websocket_auth_middleware:
        raise RuntimeError("WebSocket auth middleware not initialized")
    return websocket_auth_middleware


def init_websocket_auth_middleware(
    jwt_service: JWTAuthService,
    user_query_service: UserQueryService
) -> WebSocketAuthMiddleware:
    """初始化WebSocket认证中间件"""
    global websocket_auth_middleware
    websocket_auth_middleware = WebSocketAuthMiddleware(jwt_service, user_query_service)
    return websocket_auth_middleware
