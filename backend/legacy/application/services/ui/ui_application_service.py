"""
UI应用服务

提供完整的Web UI系统功能
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
import json

from src.application.services.base_application_service import BaseApplicationService
from src.domain.ui.entities.ui_entity import (
    UIComponent, UIEvent, UILogEntry, UISession, UIAlert, UIState,
    UIComponentType, UIEventType, LogLevel, AlertLevel
)
from src.domain.ui.repositories.ui_repository import (
    UIComponentRepository, UIEventRepository, UILogRepository,
    UISessionRepository, UIAlertRepository, UIStateRepository
)
from src.domain.ui.services.ui_domain_service import (
    UIComponentValidationService, UILayoutService, UIEventProcessingService,
    UIPermissionService, UISessionManagementService
)

logger = logging.getLogger(__name__)


class WebSocketConnectionManager:
    """WebSocket连接管理器"""
    
    def __init__(self):
        self.connections: Dict[str, Any] = {}  # session_id -> websocket
        self.session_connections: Dict[str, List[str]] = {}  # user_id -> [session_ids]
    
    def add_connection(self, session_id: str, websocket: Any, user_id: Optional[str] = None):
        """添加连接"""
        self.connections[session_id] = websocket
        
        if user_id:
            if user_id not in self.session_connections:
                self.session_connections[user_id] = []
            if session_id not in self.session_connections[user_id]:
                self.session_connections[user_id].append(session_id)
    
    def remove_connection(self, session_id: str, user_id: Optional[str] = None):
        """移除连接"""
        if session_id in self.connections:
            del self.connections[session_id]
        
        if user_id and user_id in self.session_connections:
            if session_id in self.session_connections[user_id]:
                self.session_connections[user_id].remove(session_id)
            
            if not self.session_connections[user_id]:
                del self.session_connections[user_id]
    
    def get_connection(self, session_id: str) -> Optional[Any]:
        """获取连接"""
        return self.connections.get(session_id)
    
    def get_user_connections(self, user_id: str) -> List[Any]:
        """获取用户的所有连接"""
        connections = []
        session_ids = self.session_connections.get(user_id, [])
        
        for session_id in session_ids:
            connection = self.connections.get(session_id)
            if connection:
                connections.append(connection)
        
        return connections
    
    def get_all_connections(self) -> List[Any]:
        """获取所有连接"""
        return list(self.connections.values())


class UIApplicationService(BaseApplicationService):
    """
    UI应用服务
    
    提供完整的Web UI系统功能，包括：
    1. UI组件生命周期管理
    2. 实时WebSocket通信
    3. 用户会话管理
    4. UI状态管理
    5. 事件处理和广播
    6. 权限控制
    7. 布局管理
    
    对标After服务的web_trader_ui功能
    """
    
    def __init__(
        self,
        component_repository: UIComponentRepository,
        event_repository: UIEventRepository,
        log_repository: UILogRepository,
        session_repository: UISessionRepository,
        alert_repository: UIAlertRepository,
        state_repository: UIStateRepository,
        validation_service: UIComponentValidationService,
        layout_service: UILayoutService,
        event_service: UIEventProcessingService,
        permission_service: UIPermissionService,
        session_service: UISessionManagementService
    ):
        super().__init__()
        self.component_repository = component_repository
        self.event_repository = event_repository
        self.log_repository = log_repository
        self.session_repository = session_repository
        self.alert_repository = alert_repository
        self.state_repository = state_repository
        
        # 领域服务
        self.validation_service = validation_service
        self.layout_service = layout_service
        self.event_service = event_service
        self.permission_service = permission_service
        self.session_service = session_service
        
        # WebSocket连接管理
        self.connection_manager = WebSocketConnectionManager()
        
        # 后台任务
        self.cleanup_task = None
        self.alert_check_task = None
        
        logger.info("UI应用服务初始化完成")
    
    async def initialize(self):
        """初始化服务"""
        # 设置事件处理器
        self._setup_event_handlers()
        
        # 启动后台任务
        self.cleanup_task = asyncio.create_task(self._cleanup_loop())
        self.alert_check_task = asyncio.create_task(self._alert_check_loop())
        
        logger.info("UI应用服务启动完成")
    
    async def shutdown(self):
        """关闭服务"""
        # 停止后台任务
        if self.cleanup_task:
            self.cleanup_task.cancel()
        if self.alert_check_task:
            self.alert_check_task.cancel()
        
        # 关闭所有WebSocket连接
        await self._close_all_connections()
        
        logger.info("UI应用服务关闭完成")
    
    # ===== 组件管理 =====
    
    async def create_component(
        self,
        component_type: UIComponentType,
        title: str,
        config: Dict[str, Any],
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """创建UI组件"""
        try:
            # 验证组件配置
            is_valid, errors = self.validation_service.validate_component_config(component_type, config)
            if not is_valid:
                return {"success": False, "errors": errors}
            
            # 权限检查
            if user_id:
                user_permissions = await self._get_user_permissions(user_id)
                if not self.permission_service.can_access_component(user_permissions, component_type):
                    return {"success": False, "error": "权限不足"}
            
            # 创建组件
            component = UIComponent.create(component_type, title, config, user_id)
            saved_component = await self.component_repository.save(component)
            
            # 创建事件
            event = UIEvent.create(
                UIEventType.COMPONENT_CREATED,
                {"component": saved_component.to_dict()},
                component_id=saved_component.component_id,
                user_id=user_id
            )
            await self.event_repository.save(event)
            await self.event_service.process_event(event)
            
            # 记录日志
            await self._add_log(
                LogLevel.INFO,
                f"创建组件: {component_type.value} - {title}",
                "component",
                user_id,
                saved_component.component_id
            )
            
            # 广播更新
            await self._broadcast_update("component_created", saved_component.to_dict(), user_id)
            
            return {
                "success": True,
                "component": saved_component.to_dict()
            }
            
        except Exception as e:
            logger.error(f"创建组件失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def update_component(
        self,
        component_id: str,
        updates: Dict[str, Any],
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """更新UI组件"""
        try:
            # 获取组件
            component = await self.component_repository.find_by_id(component_id)
            if not component:
                return {"success": False, "error": "组件不存在"}
            
            # 权限检查
            if user_id and component.user_id != user_id:
                user_permissions = await self._get_user_permissions(user_id)
                if not self.permission_service.can_access_component(user_permissions, component.component_type):
                    return {"success": False, "error": "权限不足"}
            
            # 更新组件
            success = component.update(updates)
            if not success:
                return {"success": False, "error": "更新失败"}
            
            updated_component = await self.component_repository.update(component)
            
            # 创建事件
            event = UIEvent.create(
                UIEventType.COMPONENT_UPDATED,
                {"component_id": component_id, "updates": updates},
                component_id=component_id,
                user_id=user_id
            )
            await self.event_repository.save(event)
            await self.event_service.process_event(event)
            
            # 记录日志
            await self._add_log(
                LogLevel.INFO,
                f"更新组件: {component_id}",
                "component",
                user_id,
                component_id
            )
            
            # 广播更新
            await self._broadcast_update("component_updated", {
                "component_id": component_id,
                "updates": updates
            }, user_id)
            
            return {
                "success": True,
                "component": updated_component.to_dict()
            }
            
        except Exception as e:
            logger.error(f"更新组件失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def close_component(self, component_id: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """关闭UI组件"""
        try:
            component = await self.component_repository.find_by_id(component_id)
            if not component:
                return {"success": False, "error": "组件不存在"}
            
            # 权限检查
            if user_id and component.user_id != user_id:
                return {"success": False, "error": "权限不足"}
            
            # 关闭组件
            component.close()
            await self.component_repository.update(component)
            
            # 创建事件
            event = UIEvent.create(
                UIEventType.COMPONENT_CLOSED,
                {"component_id": component_id},
                component_id=component_id,
                user_id=user_id
            )
            await self.event_repository.save(event)
            await self.event_service.process_event(event)
            
            # 记录日志
            await self._add_log(
                LogLevel.INFO,
                f"关闭组件: {component_id}",
                "component",
                user_id,
                component_id
            )
            
            # 广播更新
            await self._broadcast_update("component_closed", {"component_id": component_id}, user_id)
            
            return {"success": True}
            
        except Exception as e:
            logger.error(f"关闭组件失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_user_components(self, user_id: str) -> Dict[str, Any]:
        """获取用户的组件"""
        try:
            components = await self.component_repository.find_by_user_id(user_id)
            
            # 过滤权限
            user_permissions = await self._get_user_permissions(user_id)
            accessible_components = self.permission_service.filter_accessible_components(
                user_permissions, components
            )
            
            return {
                "success": True,
                "components": [comp.to_dict() for comp in accessible_components]
            }
            
        except Exception as e:
            logger.error(f"获取用户组件失败: {e}")
            return {"success": False, "error": str(e)}
    
    # ===== 会话管理 =====
    
    async def create_session(
        self,
        connection_type: str,
        client_info: Dict[str, Any],
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """创建UI会话"""
        try:
            # 检查是否可以创建新会话
            if user_id:
                existing_sessions = await self.session_repository.find_by_user_id(user_id)
                if not self.session_service.can_create_new_session(user_id, existing_sessions):
                    return {"success": False, "error": "会话数量超过限制"}
            
            # 创建会话
            session = UISession.create(connection_type, client_info, user_id)
            saved_session = await self.session_repository.save(session)
            
            # 记录日志
            await self._add_log(
                LogLevel.INFO,
                f"创建会话: {session.session_id}",
                "session",
                user_id
            )
            
            return {
                "success": True,
                "session": saved_session.to_dict()
            }
            
        except Exception as e:
            logger.error(f"创建会话失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def close_session(self, session_id: str) -> Dict[str, Any]:
        """关闭会话"""
        try:
            session = await self.session_repository.find_by_id(session_id)
            if not session:
                return {"success": False, "error": "会话不存在"}
            
            session.close()
            await self.session_repository.update(session)
            
            # 移除WebSocket连接
            self.connection_manager.remove_connection(session_id, session.user_id)
            
            # 记录日志
            await self._add_log(
                LogLevel.INFO,
                f"关闭会话: {session_id}",
                "session",
                session.user_id
            )
            
            return {"success": True}
            
        except Exception as e:
            logger.error(f"关闭会话失败: {e}")
            return {"success": False, "error": str(e)}
    
    # ===== WebSocket管理 =====
    
    async def handle_websocket_connection(self, websocket: Any, session_id: str) -> bool:
        """处理WebSocket连接"""
        try:
            # 获取会话
            session = await self.session_repository.find_by_id(session_id)
            if not session or not self.session_service.validate_session(session):
                return False
            
            # 添加连接
            self.connection_manager.add_connection(session_id, websocket, session.user_id)
            
            # 更新会话活动时间
            session.update_activity()
            await self.session_repository.update(session)
            
            # 发送初始化数据
            await self._send_initialization_data(websocket, session)
            
            # 记录日志
            await self._add_log(
                LogLevel.INFO,
                f"WebSocket连接建立: {session_id}",
                "websocket",
                session.user_id
            )
            
            return True
            
        except Exception as e:
            logger.error(f"处理WebSocket连接失败: {e}")
            return False
    
    async def handle_websocket_disconnect(self, session_id: str):
        """处理WebSocket断开"""
        try:
            # 获取会话
            session = await self.session_repository.find_by_id(session_id)
            if session:
                # 移除连接
                self.connection_manager.remove_connection(session_id, session.user_id)
                
                # 记录日志
                await self._add_log(
                    LogLevel.INFO,
                    f"WebSocket连接断开: {session_id}",
                    "websocket",
                    session.user_id
                )
            
        except Exception as e:
            logger.error(f"处理WebSocket断开失败: {e}")
    
    async def handle_websocket_message(
        self,
        session_id: str,
        message: Dict[str, Any]
    ) -> Dict[str, Any]:
        """处理WebSocket消息"""
        try:
            # 获取会话
            session = await self.session_repository.find_by_id(session_id)
            if not session or not self.session_service.validate_session(session):
                return {"error": "会话无效"}
            
            # 更新活动时间
            session.update_activity()
            await self.session_repository.update(session)
            
            message_type = message.get("type")
            
            if message_type == "ping":
                return {"type": "pong"}
            elif message_type == "user_action":
                return await self._handle_user_action(session, message.get("data", {}))
            elif message_type == "subscribe":
                return await self._handle_subscription(session, message.get("data", {}))
            else:
                return {"error": "未知消息类型"}
            
        except Exception as e:
            logger.error(f"处理WebSocket消息失败: {e}")
            return {"error": "消息处理失败"}
    
    # ===== 状态管理 =====
    
    async def get_ui_state(self, user_id: str) -> Dict[str, Any]:
        """获取UI状态"""
        try:
            state = await self.state_repository.find_by_user_id(user_id)
            
            if not state:
                # 创建默认状态
                state = UIState(current_user=user_id)
                await self.state_repository.save(user_id, state)
            
            return {
                "success": True,
                "state": state.to_dict()
            }
            
        except Exception as e:
            logger.error(f"获取UI状态失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def update_ui_state(self, user_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """更新UI状态"""
        try:
            state = await self.state_repository.find_by_user_id(user_id)
            
            if not state:
                state = UIState(current_user=user_id)
            
            state.update(updates)
            updated_state = await self.state_repository.update(user_id, state)
            
            # 广播状态更新
            await self._broadcast_to_user("state_updated", updated_state.to_dict(), user_id)
            
            return {
                "success": True,
                "state": updated_state.to_dict()
            }
            
        except Exception as e:
            logger.error(f"更新UI状态失败: {e}")
            return {"success": False, "error": str(e)}
    
    # ===== 警告管理 =====
    
    async def create_alert(
        self,
        level: AlertLevel,
        title: str,
        message: str,
        user_id: Optional[str] = None,
        component_id: Optional[str] = None,
        is_persistent: bool = False,
        auto_dismiss_seconds: Optional[int] = None
    ) -> Dict[str, Any]:
        """创建警告"""
        try:
            alert = UIAlert.create(
                level, title, message, user_id, component_id, is_persistent, auto_dismiss_seconds
            )
            saved_alert = await self.alert_repository.save(alert)
            
            # 广播警告
            if user_id:
                await self._broadcast_to_user("alert", saved_alert.to_dict(), user_id)
            else:
                await self._broadcast_to_all("alert", saved_alert.to_dict())
            
            return {
                "success": True,
                "alert": saved_alert.to_dict()
            }
            
        except Exception as e:
            logger.error(f"创建警告失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_user_alerts(self, user_id: str, include_read: bool = False) -> Dict[str, Any]:
        """获取用户警告"""
        try:
            alerts = await self.alert_repository.find_by_user_id(user_id, include_read)
            
            return {
                "success": True,
                "alerts": [alert.to_dict() for alert in alerts]
            }
            
        except Exception as e:
            logger.error(f"获取用户警告失败: {e}")
            return {"success": False, "error": str(e)}
    
    # ===== 布局管理 =====
    
    async def get_layout(self, layout_name: str) -> Dict[str, Any]:
        """获取布局"""
        try:
            layout = self.layout_service.get_default_layout(layout_name)
            
            if not layout:
                return {"success": False, "error": "布局不存在"}
            
            return {
                "success": True,
                "layout": layout
            }
            
        except Exception as e:
            logger.error(f"获取布局失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def validate_layout(self, layout_config: Dict[str, Any]) -> Dict[str, Any]:
        """验证布局"""
        try:
            is_valid, errors = self.layout_service.validate_layout(layout_config)
            
            return {
                "success": True,
                "is_valid": is_valid,
                "errors": errors
            }
            
        except Exception as e:
            logger.error(f"验证布局失败: {e}")
            return {"success": False, "error": str(e)}
    
    # ===== 私有方法 =====
    
    def _setup_event_handlers(self):
        """设置事件处理器"""
        
        async def on_component_created(event: UIEvent):
            """组件创建事件处理"""
            await self._add_log(
                LogLevel.INFO,
                f"组件创建事件: {event.component_id}",
                "event",
                event.user_id,
                event.component_id
            )
        
        async def on_component_updated(event: UIEvent):
            """组件更新事件处理"""
            await self._add_log(
                LogLevel.INFO,
                f"组件更新事件: {event.component_id}",
                "event",
                event.user_id,
                event.component_id
            )
        
        async def on_component_closed(event: UIEvent):
            """组件关闭事件处理"""
            await self._add_log(
                LogLevel.INFO,
                f"组件关闭事件: {event.component_id}",
                "event",
                event.user_id,
                event.component_id
            )
        
        # 注册事件处理器
        self.event_service.register_handler(UIEventType.COMPONENT_CREATED, on_component_created)
        self.event_service.register_handler(UIEventType.COMPONENT_UPDATED, on_component_updated)
        self.event_service.register_handler(UIEventType.COMPONENT_CLOSED, on_component_closed)
    
    async def _add_log(
        self,
        level: LogLevel,
        message: str,
        source: str = "system",
        user_id: Optional[str] = None,
        component_id: Optional[str] = None,
        extra_data: Optional[Dict[str, Any]] = None
    ):
        """添加日志"""
        log_entry = UILogEntry.create(level, message, source, user_id, component_id, extra_data)
        await self.log_repository.save(log_entry)
    
    async def _broadcast_update(self, update_type: str, data: Dict[str, Any], user_id: Optional[str] = None):
        """广播更新"""
        message = {
            "type": update_type,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        
        if user_id:
            await self._broadcast_to_user(update_type, data, user_id)
        else:
            await self._broadcast_to_all(update_type, data)
    
    async def _broadcast_to_user(self, message_type: str, data: Dict[str, Any], user_id: str):
        """向特定用户广播"""
        message = {
            "type": message_type,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        
        connections = self.connection_manager.get_user_connections(user_id)
        await self._send_to_connections(connections, message)
    
    async def _broadcast_to_all(self, message_type: str, data: Dict[str, Any]):
        """向所有用户广播"""
        message = {
            "type": message_type,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        
        connections = self.connection_manager.get_all_connections()
        await self._send_to_connections(connections, message)
    
    async def _send_to_connections(self, connections: List[Any], message: Dict[str, Any]):
        """向连接列表发送消息"""
        message_text = json.dumps(message)
        
        for connection in connections:
            try:
                await connection.send_text(message_text)
            except Exception as e:
                logger.error(f"发送WebSocket消息失败: {e}")
    
    async def _send_initialization_data(self, websocket: Any, session: UISession):
        """发送初始化数据"""
        try:
            # 获取用户组件
            components = []
            if session.user_id:
                result = await self.get_user_components(session.user_id)
                if result.get("success"):
                    components = result.get("components", [])
            
            # 获取UI状态
            state = {}
            if session.user_id:
                result = await self.get_ui_state(session.user_id)
                if result.get("success"):
                    state = result.get("state", {})
            
            init_data = {
                "type": "init",
                "data": {
                    "session": session.to_dict(),
                    "components": components,
                    "ui_state": state
                }
            }
            
            await websocket.send_text(json.dumps(init_data))
            
        except Exception as e:
            logger.error(f"发送初始化数据失败: {e}")
    
    async def _handle_user_action(self, session: UISession, action_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理用户操作"""
        try:
            action = action_data.get("action")
            
            # 权限检查
            if session.user_id:
                user_permissions = await self._get_user_permissions(session.user_id)
                if not self.permission_service.can_perform_action(user_permissions, action):
                    return {"error": "权限不足"}
            
            # 创建用户操作事件
            event = UIEvent.create(
                UIEventType.USER_ACTION,
                action_data,
                user_id=session.user_id,
                session_id=session.session_id
            )
            await self.event_repository.save(event)
            await self.event_service.process_event(event)
            
            # 记录日志
            await self._add_log(
                LogLevel.INFO,
                f"用户操作: {action}",
                "user_action",
                session.user_id,
                extra_data=action_data
            )
            
            return {"success": True}
            
        except Exception as e:
            logger.error(f"处理用户操作失败: {e}")
            return {"error": str(e)}
    
    async def _handle_subscription(self, session: UISession, subscription_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理订阅请求"""
        try:
            # 这里可以实现数据订阅逻辑
            # 例如订阅行情数据、订单更新等
            
            return {"success": True}
            
        except Exception as e:
            logger.error(f"处理订阅失败: {e}")
            return {"error": str(e)}
    
    async def _get_user_permissions(self, user_id: str) -> List[str]:
        """获取用户权限"""
        # 这里应该从用户服务获取权限
        # 目前返回默认权限
        return ["trading", "portfolio_view", "market_data", "chart_view", "log_view"]
    
    async def _close_all_connections(self):
        """关闭所有连接"""
        connections = self.connection_manager.get_all_connections()
        
        for connection in connections:
            try:
                await connection.close()
            except Exception as e:
                logger.error(f"关闭连接失败: {e}")
        
        self.connection_manager.connections.clear()
        self.connection_manager.session_connections.clear()
    
    async def _cleanup_loop(self):
        """清理循环"""
        while True:
            try:
                # 清理过期会话
                await self.session_repository.cleanup_expired_sessions()
                
                # 清理非活跃组件
                await self.component_repository.cleanup_inactive_components()
                
                # 清理旧日志
                await self.log_repository.cleanup_old_logs()
                
                # 清理旧事件
                await self.event_repository.cleanup_old_events()
                
                # 清理旧警告
                await self.alert_repository.cleanup_old_alerts()
                
                await asyncio.sleep(3600)  # 每小时清理一次
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"清理任务失败: {e}")
                await asyncio.sleep(300)  # 出错时5分钟后重试
    
    async def _alert_check_loop(self):
        """警告检查循环"""
        while True:
            try:
                # 检查需要自动关闭的警告
                # 这里可以实现更复杂的警告逻辑
                
                await asyncio.sleep(60)  # 每分钟检查一次
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"警告检查任务失败: {e}")
                await asyncio.sleep(60)
