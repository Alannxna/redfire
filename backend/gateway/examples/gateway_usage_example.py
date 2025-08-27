"""
API网关使用示例
==============

演示如何使用API网关的各种功能
"""

import asyncio
import logging
from datetime import datetime

from ..shared.communication import (
    ServiceClient, 
    EventBus, 
    DomainEvent,
    WebSocketMessageBus,
    UserContext
)
from ..gateway.config.gateway_config import GatewayConfig
from ..gateway.core.gateway import APIGateway

logger = logging.getLogger(__name__)


async def example_service_communication():
    """服务间通信示例"""
    print("=== 服务间通信示例 ===")
    
    # 创建服务客户端
    user_service = ServiceClient(
        service_name="user_service",
        base_url="http://localhost:8001"
    )
    
    # 调用用户服务
    try:
        # 获取用户列表
        response = await user_service.get("/api/v1/users")
        print(f"用户列表响应: {response.status_code}")
        print(f"数据: {response.data}")
        
        # 创建用户
        user_data = {
            "username": "test_user",
            "email": "test@example.com",
            "password": "password123"
        }
        
        response = await user_service.post("/api/v1/users", json_data=user_data)
        print(f"创建用户响应: {response.status_code}")
        
        # 获取服务统计
        stats = user_service.get_stats()
        print(f"服务统计: {stats}")
        
    except Exception as e:
        print(f"服务调用错误: {e}")
    
    finally:
        await user_service.close()


async def example_event_driven_architecture():
    """事件驱动架构示例"""
    print("=== 事件驱动架构示例 ===")
    
    # 创建事件总线
    event_bus = EventBus(
        redis_url="redis://localhost:6379/0",
        service_name="example_service"
    )
    
    try:
        await event_bus.initialize()
        
        # 注册事件处理器
        async def handle_user_registered(event: DomainEvent):
            print(f"处理用户注册事件: {event.event_id}")
            print(f"用户ID: {event.aggregate_id}")
            print(f"用户数据: {event.payload}")
            
            # 模拟处理逻辑
            await asyncio.sleep(0.1)
            print("用户注册处理完成")
        
        async def handle_order_created(event: DomainEvent):
            print(f"处理订单创建事件: {event.event_id}")
            print(f"订单ID: {event.aggregate_id}")
            print(f"订单数据: {event.payload}")
        
        # 注册处理器
        event_bus.register_handler("user.registered", handle_user_registered)
        event_bus.register_handler("order.created", handle_order_created)
        
        # 发布事件
        user_event_id = await event_bus.publish_domain_event(
            event_type="user.registered",
            aggregate_id="user_123",
            aggregate_type="User",
            payload={
                "username": "new_user",
                "email": "new_user@example.com",
                "registration_time": datetime.utcnow().isoformat()
            },
            user_id="user_123"
        )
        
        print(f"发布用户注册事件: {user_event_id}")
        
        order_event_id = await event_bus.publish_domain_event(
            event_type="order.created",
            aggregate_id="order_456",
            aggregate_type="Order",
            payload={
                "user_id": "user_123",
                "symbol": "AAPL",
                "quantity": 100,
                "price": 150.0,
                "order_type": "limit"
            },
            user_id="user_123",
            correlation_id=user_event_id  # 关联到用户注册事件
        )
        
        print(f"发布订单创建事件: {order_event_id}")
        
        # 等待事件处理
        await asyncio.sleep(2)
        
        # 获取事件统计
        stats = await event_bus.get_event_stats()
        print(f"事件统计: {stats}")
        
    finally:
        await event_bus.close()


async def example_websocket_communication():
    """WebSocket通信示例"""
    print("=== WebSocket通信示例 ===")
    
    # 创建WebSocket消息总线
    ws_bus = WebSocketMessageBus("redis://localhost:6379/0")
    
    try:
        await ws_bus.initialize()
        
        # 模拟WebSocket连接（实际应该通过FastAPI WebSocket）
        print("WebSocket消息总线初始化完成")
        
        # 注册自定义消息处理器
        async def handle_trading_signal(connection_id: str, message: dict):
            print(f"处理交易信号: {connection_id}")
            print(f"信号数据: {message}")
            
            # 广播信号给所有订阅者
            await ws_bus.publish("trading_signals", {
                "signal_type": message.get("signal_type"),
                "symbol": message.get("symbol"),
                "action": message.get("action"),
                "timestamp": datetime.utcnow().isoformat()
            })
        
        ws_bus.register_message_handler("trading_signal", handle_trading_signal)
        
        # 发布消息到主题
        await ws_bus.publish("system_notifications", {
            "type": "info",
            "message": "系统启动完成",
            "timestamp": datetime.utcnow().isoformat()
        })
        
        print("发布系统通知")
        
        # 获取统计信息
        stats = await ws_bus.get_stats()
        print(f"WebSocket统计: {stats}")
        
    finally:
        await ws_bus.close()


async def example_gateway_integration():
    """网关集成示例"""
    print("=== 网关集成示例 ===")
    
    # 创建网关配置
    config = GatewayConfig(
        host="localhost",
        port=8000,
        debug=True
    )
    
    # 创建网关实例
    gateway = APIGateway(config)
    
    try:
        # 启动网关（在实际应用中，这会在后台运行）
        await gateway.start()
        print("API网关启动完成")
        
        # 获取健康检查信息
        # 注意：这里只是演示，实际的健康检查会通过HTTP请求
        print("网关健康状态: 运行中")
        
        # 获取监控指标
        if gateway.metrics_collector:
            metrics = await gateway.metrics_collector.get_metrics()
            print(f"网关指标: {metrics}")
        
    finally:
        await gateway.stop()


async def main():
    """主示例函数"""
    print("RedFire API网关和微服务通信示例")
    print("=" * 50)
    
    # 配置日志
    logging.basicConfig(level=logging.INFO)
    
    try:
        # 运行各种示例
        await example_service_communication()
        print()
        
        await example_event_driven_architecture()
        print()
        
        await example_websocket_communication()
        print()
        
        await example_gateway_integration()
        print()
        
        print("所有示例运行完成！")
        
    except Exception as e:
        print(f"示例运行错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
