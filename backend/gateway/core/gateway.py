"""
API网关核心实现
==============

提供统一的API入口点和路由管理
"""

import logging
import time
from typing import Dict, Optional, Any, List
from dataclasses import dataclass
from fastapi import FastAPI, Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import httpx
import asyncio

from ..config.gateway_config import GatewayConfig
from ..middleware.auth_middleware import GatewayAuthMiddleware
from ..middleware.rate_limit_middleware import RateLimitMiddleware
from ..middleware.load_balancer_middleware import LoadBalancerMiddleware
from ..routing.service_router import ServiceRouter
from ..discovery.service_registry import ServiceRegistry
from ..monitoring.metrics_collector import MetricsCollector

logger = logging.getLogger(__name__)


@dataclass
class ServiceInfo:
    """服务信息"""
    name: str
    host: str
    port: int
    health_check_url: str
    weight: int = 1
    status: str = "healthy"


class APIGateway:
    """API网关核心类"""
    
    def __init__(self, config: GatewayConfig):
        self.config = config
        self.app = FastAPI(
            title="RedFire API Gateway",
            description="统一API网关服务",
            version="1.0.0"
        )
        
        # 核心组件
        self.service_registry = ServiceRegistry(config.registry)
        self.service_router = ServiceRouter(self.service_registry)
        self.auth_middleware = GatewayAuthMiddleware(config.auth)
        self.rate_limiter = RateLimitMiddleware(config.rate_limit)
        self.load_balancer = LoadBalancerMiddleware(config.load_balancer)
        self.metrics_collector = MetricsCollector(config.monitoring)
        
        # HTTP客户端池
        self.http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0),
            limits=httpx.Limits(max_keepalive_connections=100, max_connections=200)
        )
        
        self._setup_middleware()
        self._setup_routes()
        
    def _setup_middleware(self):
        """设置中间件"""
        # CORS支持
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=self.config.cors.allowed_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"]
        )
        
        # 注册自定义中间件
        @self.app.middleware("http")
        async def gateway_middleware(request: Request, call_next):
            start_time = time.time()
            
            try:
                # 1. 指标收集开始
                self.metrics_collector.record_request_start(request)
                
                # 2. 限流检查
                await self.rate_limiter.check_rate_limit(request)
                
                # 3. 认证检查
                user_context = await self.auth_middleware.authenticate_request(request)
                request.state.user_context = user_context
                
                # 4. 路由到后端服务
                if request.url.path.startswith("/api/"):
                    response = await self._route_to_service(request)
                else:
                    response = await call_next(request)
                
                # 5. 响应处理
                process_time = time.time() - start_time
                self.metrics_collector.record_request_complete(
                    request, response, process_time
                )
                
                return response
                
            except HTTPException as e:
                self.metrics_collector.record_request_error(request, e)
                return JSONResponse(
                    status_code=e.status_code,
                    content={
                        "error": e.detail,
                        "status_code": e.status_code
                    }
                )
            except Exception as e:
                logger.error(f"网关处理错误: {e}")
                self.metrics_collector.record_request_error(request, e)
                return JSONResponse(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    content={
                        "error": "网关内部错误",
                        "status_code": 500
                    }
                )
    
    def _setup_routes(self):
        """设置路由"""
        
        @self.app.get("/health")
        async def health_check():
            """健康检查"""
            return {
                "status": "healthy",
                "services": await self.service_registry.get_healthy_services(),
                "timestamp": time.time()
            }
        
        @self.app.get("/metrics")
        async def get_metrics():
            """获取监控指标"""
            return await self.metrics_collector.get_metrics()
        
        @self.app.post("/admin/services/register")
        async def register_service(service_info: dict):
            """注册服务"""
            await self.service_registry.register_service(
                ServiceInfo(**service_info)
            )
            return {"message": "服务注册成功"}
        
        @self.app.delete("/admin/services/{service_name}")
        async def unregister_service(service_name: str):
            """注销服务"""
            await self.service_registry.unregister_service(service_name)
            return {"message": "服务注销成功"}
    
    async def _route_to_service(self, request: Request) -> Response:
        """路由请求到后端服务"""
        try:
            # 1. 确定目标服务
            service_name = self.service_router.get_service_name(request.url.path)
            if not service_name:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="未找到对应的服务"
                )
            
            # 2. 负载均衡选择实例
            service_instance = await self.load_balancer.select_instance(
                service_name, request
            )
            if not service_instance:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"服务 {service_name} 不可用"
                )
            
            # 3. 构建目标URL
            target_url = f"http://{service_instance.host}:{service_instance.port}"
            full_url = f"{target_url}{request.url.path}"
            if request.url.query:
                full_url += f"?{request.url.query}"
            
            # 4. 转发请求
            headers = dict(request.headers)
            headers.update({
                "X-Forwarded-For": request.client.host,
                "X-Forwarded-Proto": request.url.scheme,
                "X-Gateway-Request-ID": str(id(request)),
            })
            
            # 添加用户上下文到请求头
            if hasattr(request.state, 'user_context') and request.state.user_context:
                user_context = request.state.user_context
                headers.update({
                    "X-User-ID": user_context.user_id,
                    "X-User-Roles": ",".join(user_context.roles),
                })
            
            # 读取请求体
            body = await request.body() if request.method in ["POST", "PUT", "PATCH"] else None
            
            # 发送请求
            response = await self.http_client.request(
                method=request.method,
                url=full_url,
                headers=headers,
                content=body,
                timeout=30.0
            )
            
            # 5. 返回响应
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.headers.get("content-type")
            )
            
        except httpx.RequestError as e:
            logger.error(f"请求转发失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="后端服务请求失败"
            )
        except httpx.TimeoutException:
            logger.error("请求超时")
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="后端服务响应超时"
            )
    
    async def start(self):
        """启动网关"""
        logger.info("启动API网关...")
        
        # 初始化组件
        await self.service_registry.initialize()
        await self.metrics_collector.initialize()
        
        # 启动健康检查
        asyncio.create_task(self._health_check_loop())
        
        logger.info("API网关启动完成")
    
    async def stop(self):
        """停止网关"""
        logger.info("停止API网关...")
        
        await self.http_client.aclose()
        await self.service_registry.close()
        await self.metrics_collector.close()
        
        logger.info("API网关已停止")
    
    async def _health_check_loop(self):
        """健康检查循环"""
        while True:
            try:
                await self.service_registry.perform_health_checks()
                await asyncio.sleep(self.config.health_check_interval)
            except Exception as e:
                logger.error(f"健康检查错误: {e}")
                await asyncio.sleep(5)
