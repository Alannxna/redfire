"""
API网关集成测试
==============

测试API网关的各种功能和组件
"""

import pytest
import asyncio
import json
from unittest.mock import AsyncMock, Mock
from fastapi.testclient import TestClient
import httpx

from ..core.gateway import APIGateway
from ..config.gateway_config import GatewayConfig
from ..middleware.auth_middleware import GatewayAuthMiddleware, UserContext
from ..middleware.rate_limit_middleware import RateLimitMiddleware
from ..middleware.load_balancer_middleware import LoadBalancerMiddleware
from ..discovery.service_registry import ServiceRegistry, ServiceInfo
from ...shared.communication import EventBus, DomainEvent, WebSocketMessageBus


class TestGatewayCore:
    """网关核心功能测试"""
    
    @pytest.fixture
    def gateway_config(self):
        """测试配置"""
        return GatewayConfig(
            host="localhost",
            port=8000,
            debug=True
        )
    
    @pytest.fixture
    async def gateway(self, gateway_config):
        """网关实例"""
        gateway = APIGateway(gateway_config)
        await gateway.start()
        yield gateway
        await gateway.stop()
    
    def test_gateway_creation(self, gateway_config):
        """测试网关创建"""
        gateway = APIGateway(gateway_config)
        
        assert gateway.config == gateway_config
        assert gateway.app is not None
        assert gateway.service_registry is not None
        assert gateway.auth_middleware is not None
        assert gateway.rate_limiter is not None
    
    async def test_gateway_startup_shutdown(self, gateway_config):
        """测试网关启动和关闭"""
        gateway = APIGateway(gateway_config)
        
        # 启动
        await gateway.start()
        assert gateway.service_registry is not None
        
        # 关闭
        await gateway.stop()
        # 验证清理完成


class TestAuthentication:
    """认证中间件测试"""
    
    @pytest.fixture
    def auth_config(self):
        """认证配置"""
        from ..config.gateway_config import AuthConfig
        return AuthConfig(
            jwt_secret="test-secret",
            jwt_algorithm="HS256"
        )
    
    @pytest.fixture
    def auth_middleware(self, auth_config):
        """认证中间件"""
        return GatewayAuthMiddleware(auth_config)
    
    async def test_public_path_access(self, auth_middleware):
        """测试公开路径访问"""
        from fastapi import Request
        
        # 模拟请求
        request = Mock(spec=Request)
        request.url.path = "/health"
        
        # 公开路径应该返回None（无需认证）
        result = await auth_middleware.authenticate_request(request)
        assert result is None
    
    async def test_missing_token(self, auth_middleware):
        """测试缺少令牌"""
        from fastapi import Request, HTTPException
        
        request = Mock(spec=Request)
        request.url.path = "/api/v1/users"
        request.headers = {}
        
        with pytest.raises(HTTPException) as exc_info:
            await auth_middleware.authenticate_request(request)
        
        assert exc_info.value.status_code == 401
    
    async def test_valid_token(self, auth_middleware):
        """测试有效令牌"""
        from fastapi import Request
        import jwt
        
        # 创建有效令牌
        payload = {"sub": "test_user", "username": "test"}
        token = jwt.encode(payload, "test-secret", algorithm="HS256")
        
        request = Mock(spec=Request)
        request.url.path = "/api/v1/users"
        request.headers = {"Authorization": f"Bearer {token}"}
        request.method = "GET"
        
        # 模拟用户上下文构建
        auth_middleware._mock_get_user_roles = lambda user_id: ["user"]
        auth_middleware._mock_get_user_permissions = lambda user_id: ["user:read"]
        
        result = await auth_middleware.authenticate_request(request)
        assert result is not None
        assert result.user_id == "test_user"
        assert result.username == "test"


class TestRateLimit:
    """限流测试"""
    
    @pytest.fixture
    def rate_limit_config(self):
        """限流配置"""
        from ..config.gateway_config import RateLimitConfig
        return RateLimitConfig(
            enabled=True,
            default_limit=5,
            window_size=60,
            storage_type="memory"
        )
    
    @pytest.fixture
    def rate_limiter(self, rate_limit_config):
        """限流器"""
        return RateLimitMiddleware(rate_limit_config)
    
    async def test_rate_limit_allow(self, rate_limiter):
        """测试允许的请求"""
        from fastapi import Request
        
        request = Mock(spec=Request)
        request.url.path = "/api/v1/test"
        request.method = "GET"
        request.client.host = "127.0.0.1"
        request.headers = {}
        request.state = Mock()
        
        # 前几个请求应该被允许
        for i in range(3):
            await rate_limiter.check_rate_limit(request)
    
    async def test_rate_limit_exceed(self, rate_limiter):
        """测试超过限制的请求"""
        from fastapi import Request, HTTPException
        
        request = Mock(spec=Request)
        request.url.path = "/api/v1/test"
        request.method = "GET"
        request.client.host = "127.0.0.1"
        request.headers = {}
        request.state = Mock()
        
        # 超过限制
        for i in range(6):  # 超过限制(5)
            if i < 5:
                await rate_limiter.check_rate_limit(request)
            else:
                with pytest.raises(HTTPException) as exc_info:
                    await rate_limiter.check_rate_limit(request)
                assert exc_info.value.status_code == 429


class TestLoadBalancer:
    """负载均衡测试"""
    
    @pytest.fixture
    def lb_config(self):
        """负载均衡配置"""
        from ..config.gateway_config import LoadBalancerConfig
        return LoadBalancerConfig(
            algorithm="round_robin",
            health_check_enabled=False  # 测试时禁用健康检查
        )
    
    @pytest.fixture
    def load_balancer(self, lb_config):
        """负载均衡器"""
        return LoadBalancerMiddleware(lb_config)
    
    async def test_service_registration(self, load_balancer):
        """测试服务注册"""
        instances = [
            {"host": "localhost", "port": 8001},
            {"host": "localhost", "port": 8002}
        ]
        
        load_balancer.register_service("test_service", instances)
        
        assert "test_service" in load_balancer.services
        assert len(load_balancer.services["test_service"]) == 2
    
    async def test_round_robin_selection(self, load_balancer):
        """测试轮询选择"""
        from fastapi import Request
        
        instances = [
            {"host": "localhost", "port": 8001},
            {"host": "localhost", "port": 8002}
        ]
        
        load_balancer.register_service("test_service", instances)
        
        request = Mock(spec=Request)
        
        # 测试轮询
        selected1 = await load_balancer.select_instance("test_service", request)
        selected2 = await load_balancer.select_instance("test_service", request)
        selected3 = await load_balancer.select_instance("test_service", request)
        
        assert selected1 is not None
        assert selected2 is not None
        assert selected3 is not None
        
        # 轮询应该选择不同的实例
        assert selected1.port != selected2.port
        assert selected1.port == selected3.port  # 第三次应该回到第一个


class TestServiceRegistry:
    """服务注册测试"""
    
    @pytest.fixture
    def registry_config(self):
        """注册中心配置"""
        from ..config.gateway_config import RegistryConfig
        return RegistryConfig(
            redis_url="redis://localhost:6379/1"  # 使用不同的数据库
        )
    
    @pytest.fixture
    async def service_registry(self, registry_config):
        """服务注册中心"""
        registry = ServiceRegistry(registry_config)
        try:
            await registry.initialize()
            yield registry
        except Exception:
            # Redis连接失败时跳过测试
            pytest.skip("Redis not available")
        finally:
            await registry.close()
    
    async def test_service_registration(self, service_registry):
        """测试服务注册"""
        service = ServiceInfo(
            name="test_service",
            host="localhost",
            port=8001,
            version="1.0.0"
        )
        
        result = await service_registry.register_service(service)
        assert result is True
    
    async def test_service_discovery(self, service_registry):
        """测试服务发现"""
        # 先注册服务
        service = ServiceInfo(
            name="test_service",
            host="localhost",
            port=8001
        )
        
        await service_registry.register_service(service)
        
        # 发现服务
        services = await service_registry.discover_services("test_service")
        assert len(services) >= 1
        assert services[0].name == "test_service"


class TestEventBus:
    """事件总线测试"""
    
    @pytest.fixture
    async def event_bus(self):
        """事件总线"""
        bus = EventBus("redis://localhost:6379/2", "test_service")
        try:
            await bus.initialize()
            yield bus
        except Exception:
            pytest.skip("Redis not available")
        finally:
            await bus.close()
    
    async def test_event_publishing(self, event_bus):
        """测试事件发布"""
        event = DomainEvent.create(
            event_type="test.event",
            aggregate_id="test_123",
            aggregate_type="Test",
            payload={"message": "Hello World"}
        )
        
        result = await event_bus.publish_event(event)
        assert result is True
    
    async def test_event_handler_registration(self, event_bus):
        """测试事件处理器注册"""
        handler_called = False
        
        async def test_handler(event: DomainEvent):
            nonlocal handler_called
            handler_called = True
        
        event_bus.register_handler("test.event", test_handler)
        
        assert "test.event" in event_bus.handlers
        assert len(event_bus.handlers["test.event"]) == 1


class TestWebSocketBus:
    """WebSocket消息总线测试"""
    
    @pytest.fixture
    async def ws_bus(self):
        """WebSocket消息总线"""
        bus = WebSocketMessageBus("redis://localhost:6379/3")
        try:
            await bus.initialize()
            yield bus
        except Exception:
            pytest.skip("Redis not available")
        finally:
            await bus.close()
    
    async def test_message_publishing(self, ws_bus):
        """测试消息发布"""
        count = await ws_bus.publish("test_topic", {"message": "Hello"})
        # 没有订阅者时应该返回0
        assert count == 0
    
    async def test_subscription_management(self, ws_bus):
        """测试订阅管理"""
        # 模拟连接
        from fastapi import WebSocket
        mock_websocket = Mock(spec=WebSocket)
        mock_websocket.accept = AsyncMock()
        
        # 这里只测试订阅逻辑，不测试实际WebSocket连接
        assert len(ws_bus.subscriptions) == 0


class TestIntegrationScenarios:
    """集成场景测试"""
    
    async def test_complete_request_flow(self):
        """测试完整的请求流程"""
        # 这个测试需要启动完整的网关和模拟服务
        # 由于复杂性，这里只做基本的流程验证
        
        config = GatewayConfig(debug=True)
        gateway = APIGateway(config)
        
        try:
            await gateway.start()
            
            # 验证网关各组件都已初始化
            assert gateway.service_registry is not None
            assert gateway.auth_middleware is not None
            assert gateway.rate_limiter is not None
            assert gateway.load_balancer is not None
            
        finally:
            await gateway.stop()
    
    async def test_service_communication_flow(self):
        """测试服务间通信流程"""
        from ...shared.communication import ServiceClient
        
        # 创建客户端（不实际连接）
        client = ServiceClient(
            service_name="test_service",
            base_url="http://localhost:8001"
        )
        
        # 验证客户端创建成功
        assert client.service_name == "test_service"
        assert client.base_url == "http://localhost:8001"
        
        await client.close()


@pytest.mark.asyncio
async def test_performance_basic():
    """基本性能测试"""
    config = GatewayConfig(debug=False)
    gateway = APIGateway(config)
    
    import time
    
    start_time = time.time()
    await gateway.start()
    startup_time = time.time() - start_time
    
    # 启动时间应该在合理范围内
    assert startup_time < 5.0  # 5秒内启动
    
    await gateway.stop()


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])
