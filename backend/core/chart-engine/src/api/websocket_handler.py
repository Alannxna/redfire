"""
图表引擎WebSocket处理器 - 实时数据推送

提供WebSocket接口供前端订阅图表数据实时更新
"""

import json
import logging
import asyncio
from datetime import datetime
from typing import Dict, Set, Any, Optional
from fastapi import WebSocket, WebSocketDisconnect
from dataclasses import asdict

from ..core.chart_engine import ChartEngine
from ..models.chart_models import ChartUpdateEvent

logger = logging.getLogger(__name__)


class WebSocketConnectionManager:
    """WebSocket连接管理器"""
    
    def __init__(self):
        # 活跃连接 {connection_id: websocket}
        self.active_connections: Dict[str, WebSocket] = {}
        
        # 图表订阅关系 {chart_id: {connection_id}}
        self.chart_subscriptions: Dict[str, Set[str]] = {}
        
        # 连接订阅关系 {connection_id: {chart_id}}
        self.connection_subscriptions: Dict[str, Set[str]] = {}
        
        logger.info("WebSocket连接管理器初始化完成")
    
    async def connect(self, websocket: WebSocket, connection_id: str) -> None:
        """建立WebSocket连接"""
        try:
            await websocket.accept()
            self.active_connections[connection_id] = websocket
            self.connection_subscriptions[connection_id] = set()
            
            logger.info(f"WebSocket连接建立: {connection_id}")
            
            # 发送连接成功消息
            await self.send_message(connection_id, {
                "type": "connection",
                "status": "connected",
                "connection_id": connection_id,
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"WebSocket连接建立失败: {e}")
            raise
    
    async def disconnect(self, connection_id: str) -> None:
        """断开WebSocket连接"""
        try:
            # 清理订阅关系
            if connection_id in self.connection_subscriptions:
                chart_ids = self.connection_subscriptions[connection_id].copy()
                for chart_id in chart_ids:
                    await self.unsubscribe_chart(connection_id, chart_id)
                
                del self.connection_subscriptions[connection_id]
            
            # 删除连接
            if connection_id in self.active_connections:
                del self.active_connections[connection_id]
            
            logger.info(f"WebSocket连接断开: {connection_id}")
            
        except Exception as e:
            logger.error(f"WebSocket连接断开处理失败: {e}")
    
    async def subscribe_chart(self, connection_id: str, chart_id: str) -> None:
        """订阅图表"""
        try:
            if connection_id not in self.active_connections:
                raise ValueError(f"连接不存在: {connection_id}")
            
            # 添加订阅关系
            if chart_id not in self.chart_subscriptions:
                self.chart_subscriptions[chart_id] = set()
            
            self.chart_subscriptions[chart_id].add(connection_id)
            self.connection_subscriptions[connection_id].add(chart_id)
            
            logger.info(f"图表订阅成功: {connection_id} -> {chart_id}")
            
            # 发送订阅成功消息
            await self.send_message(connection_id, {
                "type": "subscription",
                "action": "subscribed",
                "chart_id": chart_id,
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"图表订阅失败: {e}")
            raise
    
    async def unsubscribe_chart(self, connection_id: str, chart_id: str) -> None:
        """取消订阅图表"""
        try:
            # 移除订阅关系
            if chart_id in self.chart_subscriptions:
                self.chart_subscriptions[chart_id].discard(connection_id)
                
                # 如果没有订阅者，删除图表订阅记录
                if not self.chart_subscriptions[chart_id]:
                    del self.chart_subscriptions[chart_id]
            
            if connection_id in self.connection_subscriptions:
                self.connection_subscriptions[connection_id].discard(chart_id)
            
            logger.info(f"图表取消订阅: {connection_id} -> {chart_id}")
            
            # 发送取消订阅消息
            if connection_id in self.active_connections:
                await self.send_message(connection_id, {
                    "type": "subscription",
                    "action": "unsubscribed",
                    "chart_id": chart_id,
                    "timestamp": datetime.now().isoformat()
                })
            
        except Exception as e:
            logger.error(f"取消订阅图表失败: {e}")
    
    async def broadcast_chart_update(self, chart_id: str, update_data: Dict[str, Any]) -> None:
        """广播图表更新到所有订阅者"""
        try:
            if chart_id not in self.chart_subscriptions:
                return
            
            subscribers = self.chart_subscriptions[chart_id].copy()
            
            # 准备广播消息
            message = {
                "type": "chart_update",
                "chart_id": chart_id,
                "data": update_data,
                "timestamp": datetime.now().isoformat()
            }
            
            # 广播给所有订阅者
            disconnect_connections = []
            for connection_id in subscribers:
                try:
                    await self.send_message(connection_id, message)
                except Exception as e:
                    logger.warning(f"向连接 {connection_id} 发送消息失败: {e}")
                    disconnect_connections.append(connection_id)
            
            # 清理断开的连接
            for connection_id in disconnect_connections:
                await self.disconnect(connection_id)
            
        except Exception as e:
            logger.error(f"广播图表更新失败: {e}")
    
    async def send_message(self, connection_id: str, message: Dict[str, Any]) -> None:
        """发送消息到指定连接"""
        try:
            if connection_id not in self.active_connections:
                return
            
            websocket = self.active_connections[connection_id]
            await websocket.send_text(json.dumps(message, ensure_ascii=False))
            
        except Exception as e:
            logger.error(f"发送WebSocket消息失败: {e}")
            # 连接可能已断开，移除连接
            await self.disconnect(connection_id)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取连接统计信息"""
        return {
            "active_connections": len(self.active_connections),
            "total_subscriptions": sum(len(subs) for subs in self.chart_subscriptions.values()),
            "charts_with_subscribers": len(self.chart_subscriptions)
        }


class ChartWebSocketHandler:
    """
    图表WebSocket处理器
    
    处理WebSocket连接和图表数据实时推送
    """
    
    def __init__(self, chart_engine: ChartEngine):
        self.chart_engine = chart_engine
        self.connection_manager = WebSocketConnectionManager()
        self._running = False
        
        logger.info("图表WebSocket处理器初始化完成")
    
    async def start(self) -> None:
        """启动WebSocket处理器"""
        self._running = True
        
        # 启动图表更新监听任务
        asyncio.create_task(self._chart_update_listener())
        
        logger.info("图表WebSocket处理器启动完成")
    
    async def stop(self) -> None:
        """停止WebSocket处理器"""
        self._running = False
        
        # 断开所有连接
        connection_ids = list(self.connection_manager.active_connections.keys())
        for connection_id in connection_ids:
            await self.connection_manager.disconnect(connection_id)
        
        logger.info("图表WebSocket处理器已停止")
    
    async def handle_websocket(self, websocket: WebSocket, connection_id: str) -> None:
        """处理WebSocket连接"""
        try:
            # 建立连接
            await self.connection_manager.connect(websocket, connection_id)
            
            # 处理消息循环
            while self._running:
                try:
                    # 接收消息
                    data = await websocket.receive_text()
                    message = json.loads(data)
                    
                    # 处理消息
                    await self._handle_message(connection_id, message)
                    
                except WebSocketDisconnect:
                    logger.info(f"WebSocket客户端断开: {connection_id}")
                    break
                except json.JSONDecodeError as e:
                    logger.warning(f"WebSocket消息JSON解析失败: {e}")
                    await self.connection_manager.send_message(connection_id, {
                        "type": "error",
                        "message": "消息格式错误",
                        "timestamp": datetime.now().isoformat()
                    })
                except Exception as e:
                    logger.error(f"WebSocket消息处理失败: {e}")
                    await self.connection_manager.send_message(connection_id, {
                        "type": "error",
                        "message": "消息处理失败",
                        "timestamp": datetime.now().isoformat()
                    })
        
        except Exception as e:
            logger.error(f"WebSocket连接处理失败: {e}")
        
        finally:
            # 清理连接
            await self.connection_manager.disconnect(connection_id)
    
    async def _handle_message(self, connection_id: str, message: Dict[str, Any]) -> None:
        """处理WebSocket消息"""
        try:
            action = message.get("action")
            
            if action == "subscribe":
                # 订阅图表
                chart_id = message.get("chart_id")
                if not chart_id:
                    raise ValueError("缺少chart_id参数")
                
                # 订阅图表引擎
                await self.chart_engine.subscribe_chart(chart_id, connection_id)
                
                # 订阅WebSocket
                await self.connection_manager.subscribe_chart(connection_id, chart_id)
                
                # 发送初始数据
                try:
                    render_data = await self.chart_engine.get_chart_render_data(chart_id)
                    await self.connection_manager.send_message(connection_id, {
                        "type": "initial_data",
                        "chart_id": chart_id,
                        "data": render_data,
                        "timestamp": datetime.now().isoformat()
                    })
                except Exception as e:
                    logger.warning(f"发送初始数据失败: {e}")
            
            elif action == "unsubscribe":
                # 取消订阅图表
                chart_id = message.get("chart_id")
                if not chart_id:
                    raise ValueError("缺少chart_id参数")
                
                # 取消订阅图表引擎
                await self.chart_engine.unsubscribe_chart(chart_id, connection_id)
                
                # 取消订阅WebSocket
                await self.connection_manager.unsubscribe_chart(connection_id, chart_id)
            
            elif action == "ping":
                # 心跳检查
                await self.connection_manager.send_message(connection_id, {
                    "type": "pong",
                    "timestamp": datetime.now().isoformat()
                })
            
            elif action == "get_chart_list":
                # 获取图表列表
                chart_list = []
                for chart_id in self.chart_engine.charts:
                    chart_info = self.chart_engine.get_chart_info(chart_id)
                    if chart_info:
                        chart_list.append(chart_info)
                
                await self.connection_manager.send_message(connection_id, {
                    "type": "chart_list",
                    "charts": chart_list,
                    "timestamp": datetime.now().isoformat()
                })
            
            else:
                raise ValueError(f"不支持的动作: {action}")
        
        except Exception as e:
            logger.error(f"处理WebSocket消息失败: {e}")
            await self.connection_manager.send_message(connection_id, {
                "type": "error",
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            })
    
    async def _chart_update_listener(self) -> None:
        """图表更新监听器"""
        while self._running:
            try:
                # 这里可以实现更复杂的图表更新监听逻辑
                # 目前简单等待，在实际应用中可以监听图表引擎的更新事件
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"图表更新监听失败: {e}")
                await asyncio.sleep(5)  # 错误时等待更长时间
    
    async def broadcast_chart_update(self, chart_update: ChartUpdateEvent) -> None:
        """广播图表更新事件"""
        try:
            update_data = chart_update.to_dict()
            await self.connection_manager.broadcast_chart_update(
                chart_update.chart_id, 
                update_data
            )
        except Exception as e:
            logger.error(f"广播图表更新事件失败: {e}")
    
    def get_handler_status(self) -> Dict[str, Any]:
        """获取处理器状态"""
        return {
            "is_running": self._running,
            "connection_stats": self.connection_manager.get_stats()
        }
