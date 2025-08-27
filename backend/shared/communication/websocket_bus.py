"""
WebSocket消息总线
================

实现WebSocket连接管理和消息路由
"""

import json
import time
import uuid
import logging
import asyncio
from typing import Dict, Set, Optional, Any, Callable, List
from dataclasses import dataclass, field
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect
import redis.asyncio as redis

logger = logging.getLogger(__name__)


@dataclass
class UserContext:
    """用户上下文"""
    user_id: str
    username: str
    roles: List[str] = field(default_factory=list)
    permissions: List[str] = field(default_factory=list)


@dataclass
class WebSocketConnection:
    """WebSocket连接信息"""
    id: str
    websocket: WebSocket
    user_context: Optional[UserContext] = None
    connected_at: datetime = field(default_factory=datetime.utcnow)
    last_heartbeat: datetime = field(default_factory=datetime.utcnow)
    subscriptions: Set[str] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def is_authenticated(self) -> bool:
        """是否已认证"""
        return self.user_context is not None


@dataclass
class Message:
    """消息结构"""
    id: str
    type: str
    topic: str
    payload: Dict[str, Any]
    sender_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "type": self.type,
            "topic": self.topic,
            "payload": self.payload,
            "sender_id": self.sender_id,
            "timestamp": self.timestamp.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Message":
        """从字典创建"""
        return cls(
            id=data["id"],
            type=data["type"],
            topic=data["topic"],
            payload=data["payload"],
            sender_id=data.get("sender_id"),
            timestamp=datetime.fromisoformat(data["timestamp"])
        )


class WebSocketMessageBus:
    """WebSocket消息总线"""
    
    def __init__(self, redis_url: Optional[str] = None):
        self.connections: Dict[str, WebSocketConnection] = {}
        self.subscriptions: Dict[str, Set[str]] = {}  # topic -> connection_ids
        self.message_handlers: Dict[str, Callable] = {}
        
        # Redis客户端用于跨实例消息传递
        self.redis: Optional[redis.Redis] = None
        self.redis_url = redis_url
        
        # 统计信息
        self.total_connections = 0
        self.total_messages = 0
        self.start_time = datetime.utcnow()
        
        # 后台任务
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._redis_listener_task: Optional[asyncio.Task] = None
    
    async def initialize(self):
        """初始化消息总线"""
        logger.info("初始化WebSocket消息总线...")
        
        # 连接Redis
        if self.redis_url:
            try:
                self.redis = redis.from_url(self.redis_url, decode_responses=True)
                await self.redis.ping()
                logger.info("WebSocket消息总线Redis连接成功")
                
                # 启动Redis监听器
                self._redis_listener_task = asyncio.create_task(self._redis_message_listener())
            except Exception as e:
                logger.warning(f"WebSocket消息总线Redis连接失败: {e}")
        
        # 启动心跳检查
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        
        logger.info("WebSocket消息总线初始化完成")
    
    async def connect(self, websocket: WebSocket, connection_id: str, 
                     user_context: Optional[UserContext] = None) -> str:
        """建立WebSocket连接"""
        await websocket.accept()
        
        connection = WebSocketConnection(
            id=connection_id,
            websocket=websocket,
            user_context=user_context
        )
        
        self.connections[connection_id] = connection
        self.total_connections += 1
        
        logger.info(f"WebSocket连接建立: {connection_id}")
        
        # 发送欢迎消息
        await self._send_to_connection(connection_id, {
            "type": "connection_established",
            "connection_id": connection_id,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        try:
            # 处理消息循环
            async for message in websocket.iter_text():
                await self._handle_message(connection_id, message)
        except WebSocketDisconnect:
            await self.disconnect(connection_id)
        except Exception as e:
            logger.error(f"WebSocket连接错误 {connection_id}: {e}")
            await self.disconnect(connection_id)
        
        return connection_id
    
    async def disconnect(self, connection_id: str):
        """断开WebSocket连接"""
        if connection_id not in self.connections:
            return
        
        connection = self.connections[connection_id]
        
        # 取消所有订阅
        for topic in list(connection.subscriptions):
            await self.unsubscribe(connection_id, topic)
        
        # 移除连接
        del self.connections[connection_id]
        
        logger.info(f"WebSocket连接断开: {connection_id}")
    
    async def subscribe(self, connection_id: str, topic: str) -> bool:
        """订阅主题"""
        if connection_id not in self.connections:
            logger.warning(f"连接不存在: {connection_id}")
            return False
        
        connection = self.connections[connection_id]
        
        # 检查权限
        if not self._check_subscription_permission(connection, topic):
            logger.warning(f"订阅权限不足: {connection_id} -> {topic}")
            await self._send_error(connection_id, f"订阅主题 {topic} 权限不足")
            return False
        
        # 添加订阅
        if topic not in self.subscriptions:
            self.subscriptions[topic] = set()
        
        self.subscriptions[topic].add(connection_id)
        connection.subscriptions.add(topic)
        
        logger.info(f"订阅主题: {connection_id} -> {topic}")
        
        # 发送确认消息
        await self._send_to_connection(connection_id, {
            "type": "subscription_confirmed",
            "topic": topic,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return True
    
    async def unsubscribe(self, connection_id: str, topic: str) -> bool:
        """取消订阅"""
        if connection_id not in self.connections:
            return False
        
        connection = self.connections[connection_id]
        
        # 移除订阅
        if topic in self.subscriptions:
            self.subscriptions[topic].discard(connection_id)
            if not self.subscriptions[topic]:
                del self.subscriptions[topic]
        
        connection.subscriptions.discard(topic)
        
        logger.info(f"取消订阅: {connection_id} -> {topic}")
        
        # 发送确认消息
        await self._send_to_connection(connection_id, {
            "type": "unsubscription_confirmed",
            "topic": topic,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return True
    
    async def publish(self, topic: str, payload: Dict[str, Any], 
                     sender_id: Optional[str] = None,
                     exclude_connections: Optional[Set[str]] = None) -> int:
        """发布消息到主题"""
        message = Message(
            id=str(uuid.uuid4()),
            type="topic_message",
            topic=topic,
            payload=payload,
            sender_id=sender_id
        )
        
        self.total_messages += 1
        
        # 本地分发
        local_count = await self._distribute_locally(message, exclude_connections)
        
        # Redis分发到其他实例
        if self.redis:
            await self._distribute_via_redis(message)
        
        logger.debug(f"发布消息到主题 {topic}: 本地分发 {local_count} 个连接")
        
        return local_count
    
    async def send_to_user(self, user_id: str, message: Dict[str, Any]) -> bool:
        """发送消息给特定用户"""
        target_connections = [
            conn_id for conn_id, conn in self.connections.items()
            if conn.user_context and conn.user_context.user_id == user_id
        ]
        
        if not target_connections:
            logger.debug(f"用户 {user_id} 不在线")
            return False
        
        for conn_id in target_connections:
            await self._send_to_connection(conn_id, message)
        
        logger.debug(f"发送消息给用户 {user_id}: {len(target_connections)} 个连接")
        return True
    
    async def broadcast(self, message: Dict[str, Any], 
                       exclude_connections: Optional[Set[str]] = None) -> int:
        """广播消息给所有连接"""
        count = 0
        exclude_connections = exclude_connections or set()
        
        for conn_id in self.connections:
            if conn_id not in exclude_connections:
                await self._send_to_connection(conn_id, message)
                count += 1
        
        logger.debug(f"广播消息: {count} 个连接")
        return count
    
    def register_message_handler(self, message_type: str, handler: Callable):
        """注册消息处理器"""
        self.message_handlers[message_type] = handler
        logger.info(f"注册消息处理器: {message_type}")
    
    async def _handle_message(self, connection_id: str, message_text: str):
        """处理WebSocket消息"""
        try:
            data = json.loads(message_text)
            message_type = data.get("type")
            
            if not message_type:
                await self._send_error(connection_id, "消息类型不能为空")
                return
            
            logger.debug(f"处理消息: {connection_id} -> {message_type}")
            
            # 更新心跳时间
            if connection_id in self.connections:
                self.connections[connection_id].last_heartbeat = datetime.utcnow()
            
            # 内置消息处理
            if message_type == "subscribe":
                topic = data.get("topic")
                if topic:
                    await self.subscribe(connection_id, topic)
                else:
                    await self._send_error(connection_id, "缺少主题参数")
            
            elif message_type == "unsubscribe":
                topic = data.get("topic")
                if topic:
                    await self.unsubscribe(connection_id, topic)
                else:
                    await self._send_error(connection_id, "缺少主题参数")
            
            elif message_type == "publish":
                topic = data.get("topic")
                payload = data.get("payload", {})
                if topic:
                    await self.publish(topic, payload, connection_id)
                else:
                    await self._send_error(connection_id, "缺少主题参数")
            
            elif message_type == "heartbeat":
                await self._send_to_connection(connection_id, {
                    "type": "heartbeat_ack",
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            # 自定义消息处理器
            elif message_type in self.message_handlers:
                handler = self.message_handlers[message_type]
                await handler(connection_id, data)
            
            else:
                logger.warning(f"未知消息类型: {message_type}")
                await self._send_error(connection_id, f"未知消息类型: {message_type}")
                
        except json.JSONDecodeError:
            await self._send_error(connection_id, "消息格式错误")
        except Exception as e:
            logger.error(f"消息处理失败 {connection_id}: {e}")
            await self._send_error(connection_id, "消息处理失败")
    
    async def _send_to_connection(self, connection_id: str, message: Dict[str, Any]):
        """发送消息到指定连接"""
        if connection_id not in self.connections:
            return
        
        connection = self.connections[connection_id]
        
        try:
            await connection.websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"发送消息失败 {connection_id}: {e}")
            await self.disconnect(connection_id)
    
    async def _send_error(self, connection_id: str, error_message: str):
        """发送错误消息"""
        await self._send_to_connection(connection_id, {
            "type": "error",
            "message": error_message,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    async def _distribute_locally(self, message: Message, 
                                exclude_connections: Optional[Set[str]] = None) -> int:
        """本地分发消息"""
        if message.topic not in self.subscriptions:
            return 0
        
        exclude_connections = exclude_connections or set()
        count = 0
        
        for connection_id in self.subscriptions[message.topic]:
            if connection_id not in exclude_connections:
                await self._send_to_connection(connection_id, message.to_dict())
                count += 1
        
        return count
    
    async def _distribute_via_redis(self, message: Message):
        """通过Redis分发消息到其他实例"""
        if not self.redis:
            return
        
        try:
            channel = f"websocket:{message.topic}"
            await self.redis.publish(channel, json.dumps(message.to_dict()))
        except Exception as e:
            logger.error(f"Redis消息发布失败: {e}")
    
    async def _redis_message_listener(self):
        """Redis消息监听器"""
        if not self.redis:
            return
        
        pubsub = self.redis.pubsub()
        await pubsub.psubscribe("websocket:*")
        
        try:
            async for message in pubsub.listen():
                if message["type"] == "pmessage":
                    try:
                        channel = message["channel"]
                        topic = channel.split(":", 1)[1]
                        data = json.loads(message["data"])
                        
                        # 重构消息对象
                        msg = Message.from_dict(data)
                        
                        # 本地分发（排除发送者）
                        exclude = {msg.sender_id} if msg.sender_id else set()
                        await self._distribute_locally(msg, exclude)
                        
                    except Exception as e:
                        logger.error(f"Redis消息处理失败: {e}")
        except Exception as e:
            logger.error(f"Redis监听器错误: {e}")
        finally:
            await pubsub.close()
    
    def _check_subscription_permission(self, connection: WebSocketConnection, topic: str) -> bool:
        """检查订阅权限"""
        # 公开主题
        public_topics = ["system", "announcements", "general"]
        if topic in public_topics:
            return True
        
        # 需要认证的主题
        if not connection.is_authenticated:
            return False
        
        user_context = connection.user_context
        
        # 用户私有主题
        if topic.startswith(f"user:{user_context.user_id}"):
            return True
        
        # 角色相关主题
        if topic.startswith("role:"):
            required_role = topic.split(":", 1)[1]
            return required_role in user_context.roles
        
        # 权限相关主题
        if topic.startswith("permission:"):
            required_permission = topic.split(":", 1)[1]
            return required_permission in user_context.permissions
        
        # 默认拒绝
        return False
    
    async def _heartbeat_loop(self):
        """心跳检查循环"""
        while True:
            try:
                now = datetime.utcnow()
                timeout_connections = []
                
                for conn_id, connection in self.connections.items():
                    # 检查心跳超时
                    if (now - connection.last_heartbeat).total_seconds() > 60:
                        timeout_connections.append(conn_id)
                
                # 断开超时连接
                for conn_id in timeout_connections:
                    logger.info(f"心跳超时，断开连接: {conn_id}")
                    await self.disconnect(conn_id)
                
                await asyncio.sleep(30)  # 30秒检查一次
                
            except Exception as e:
                logger.error(f"心跳检查错误: {e}")
                await asyncio.sleep(5)
    
    async def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        now = datetime.utcnow()
        uptime = (now - self.start_time).total_seconds()
        
        return {
            "uptime_seconds": uptime,
            "total_connections_ever": self.total_connections,
            "current_connections": len(self.connections),
            "total_messages": self.total_messages,
            "active_topics": len(self.subscriptions),
            "connections": [
                {
                    "id": conn.id,
                    "user_id": conn.user_context.user_id if conn.user_context else None,
                    "connected_at": conn.connected_at.isoformat(),
                    "subscriptions": list(conn.subscriptions)
                }
                for conn in self.connections.values()
            ]
        }
    
    async def close(self):
        """关闭消息总线"""
        logger.info("关闭WebSocket消息总线...")
        
        # 停止后台任务
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
        if self._redis_listener_task:
            self._redis_listener_task.cancel()
        
        # 断开所有连接
        for connection_id in list(self.connections.keys()):
            await self.disconnect(connection_id)
        
        # 关闭Redis连接
        if self.redis:
            await self.redis.close()
        
        logger.info("WebSocket消息总线已关闭")
