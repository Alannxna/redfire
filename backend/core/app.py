"""
RedFire应用统一入口点
==================

整合所有功能模块，提供单一主入口点
"""

import logging
import asyncio
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from .config import get_app_config, get_config_manager, AppConfig
from .lifecycle import ApplicationLifecycle
from .middleware import setup_middleware

logger = logging.getLogger(__name__)


class RedFireApplication:
    """RedFire应用主类"""
    
    def __init__(self, config: Optional[AppConfig] = None):
        self.config = config or get_app_config()
        self.app: Optional[FastAPI] = None
        self._components: Dict[str, Any] = {}
        self._lifecycle: Optional[ApplicationLifecycle] = None
        
        # 确保创建必需的目录
        self.config.create_directories()
        
        logger.info(f"RedFire应用初始化完成 - 环境: {self.config.environment}")
    
    def create_app(self) -> FastAPI:
        """创建FastAPI应用实例"""
        
        @asynccontextmanager
        async def lifespan(app: FastAPI):
            # 启动事件
            await self._startup()
            yield
            # 关闭事件
            await self._shutdown()
        
        # 创建FastAPI应用
        self.app = FastAPI(
            title=self.config.app_name,
            description="RedFire 量化交易平台后端API服务",
            version=self.config.app_version,
            debug=self.config.debug,
            docs_url="/docs" if self.config.is_development() else None,
            redoc_url="/redoc" if self.config.is_development() else None,
            lifespan=lifespan
        )
        
        # 设置组件
        self._setup_components()
        
        # 注册中间件
        self._register_middleware()
        
        # 注册路由
        self._register_routes()
        
        # 设置异常处理
        self._setup_exception_handlers()
        
        logger.info("FastAPI应用创建完成")
        return self.app
    
    def _setup_components(self):
        """设置应用组件"""
        # 创建生命周期管理器
        self._lifecycle = ApplicationLifecycle(self.app, self.config)
        
        logger.info("应用组件设置完成")
    
    def _register_middleware(self):
        """注册中间件"""
        if not self.app:
            return
        
        # CORS中间件
        cors_settings = self.config.get_cors_settings()
        self.app.add_middleware(CORSMiddleware, **cors_settings)
        
        # 设置其他中间件
        setup_middleware(self.app, self.config)
        
        logger.info("中间件注册完成")
    
    def _register_routes(self):
        """注册路由"""
        if not self.app:
            return
        
        # 健康检查
        @self.app.get("/health")
        async def health_check():
            return {
                "status": "healthy",
                "service": self.config.app_name,
                "version": self.config.app_version,
                "environment": self.config.environment
            }
        
        @self.app.get("/")
        async def root():
            return {
                "message": f"欢迎使用 {self.config.app_name}",
                "version": self.config.app_version,
                "environment": self.config.environment,
                "docs": "/docs" if self.config.is_development() else "文档在生产环境中不可用",
                "health": "/health"
            }
        
        # 导入并注册业务路由
        self._register_business_routes()
        
        logger.info("路由注册完成")
    
    def _register_business_routes(self):
        """注册业务路由"""
        if not self.app:
            return
        
        try:
            # 认证路由
            try:
                from api.auth_routes import router as auth_router
                self.app.include_router(auth_router)  # auth_router 已经有 /api/auth 前缀
                logger.info("认证路由注册完成")
            except ImportError as e:
                logger.warning(f"认证路由导入失败: {e}")
            
            # 图表引擎路由
            try:
                from .chart_engine.src.core.chart_engine import ChartEngine
                from .chart_engine.src.api.chart_api import ChartEngineAPI
                
                # 初始化图表引擎
                chart_engine = ChartEngine()
                self._components['chart_engine'] = chart_engine
                
                # 创建图表API
                chart_api = ChartEngineAPI(chart_engine)
                
                # 注册图表API路由
                self.app.include_router(
                    chart_api.get_router(),
                    tags=["图表引擎"]
                )
                
                # 注册WebSocket路由
                from .chart_engine.src.api.websocket_handler import ChartWebSocketHandler
                chart_ws_handler = ChartWebSocketHandler(chart_engine)
                self._components['chart_ws_handler'] = chart_ws_handler
                
                @self.app.websocket("/api/chart/ws")
                async def chart_websocket_endpoint(websocket, connection_id: str = None):
                    import uuid
                    if not connection_id:
                        connection_id = str(uuid.uuid4())
                    await chart_ws_handler.handle_websocket(websocket, connection_id)
                
                logger.info("图表引擎路由注册完成")
                
            except ImportError as e:
                logger.warning(f"图表引擎路由导入失败: {e}")
            
            # 策略引擎路由
            try:
                from strategy.integration.strategy_integration import setup_strategy_system
                
                # 设置策略系统
                strategy_system = setup_strategy_system(self.app)
                self._components['strategy_system'] = strategy_system
                
                logger.info("策略引擎路由注册完成")
                
            except ImportError as e:
                logger.warning(f"策略引擎路由导入失败: {e}")
            
            # 安全系统路由
            try:
                from security.security_integration import SecurityIntegration
                
                # 初始化安全系统
                security_integration = SecurityIntegration()
                security_integration.setup_security(self.app)
                self._components['security_integration'] = security_integration
                
                logger.info("安全系统路由注册完成")
                
            except ImportError as e:
                logger.warning(f"安全系统路由导入失败: {e}")
            
            # VnPy Web API路由（如果存在）
            try:
                from legacy.interfaces.rest.controllers.user_controller import UserController
                from legacy.interfaces.rest.controllers.trading_controller import TradingController
                from legacy.interfaces.rest.controllers.dashboard_controller import DashboardController
                
                # 用户管理路由
                user_controller = UserController()
                self.app.include_router(
                    user_controller.router,
                    prefix="/api/v1/users",
                    tags=["用户管理"]
                )
                
                # 交易管理路由
                trading_controller = TradingController()
                self.app.include_router(
                    trading_controller.router,
                    prefix="/api/v1/trading",
                    tags=["交易管理"]
                )
                
                # 仪表盘路由
                dashboard_controller = DashboardController()
                self.app.include_router(
                    dashboard_controller.router,
                    prefix="/api/v1/dashboard",
                    tags=["系统监控"]
                )
                
                logger.info("VnPy Web API路由注册完成")
                
            except ImportError as e:
                logger.warning(f"VnPy Web API路由导入失败: {e}")
            
            # 静态文件服务（开发环境）
            if self.config.is_development():
                try:
                    static_dir = self.config.upload_dir
                    self.app.mount("/static", StaticFiles(directory=static_dir), name="static")
                    logger.info(f"静态文件服务已挂载: {static_dir}")
                except Exception as e:
                    logger.warning(f"静态文件服务挂载失败: {e}")
                    
        except Exception as e:
            logger.error(f"业务路由注册失败: {e}")
    
    def _setup_exception_handlers(self):
        """设置异常处理器"""
        if not self.app:
            return
        
        @self.app.exception_handler(404)
        async def not_found_handler(request: Request, exc):
            return JSONResponse(
                status_code=404,
                content={
                    "success": False,
                    "message": "请求的资源不存在",
                    "path": str(request.url.path),
                    "method": request.method
                }
            )
        
        @self.app.exception_handler(500)
        async def internal_error_handler(request: Request, exc):
            logger.error(f"内部服务器错误: {exc}")
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "message": "内部服务器错误",
                    "detail": "请稍后重试或联系管理员" if self.config.is_production() else str(exc)
                }
            )
        
        logger.info("异常处理器设置完成")
    
    async def _startup(self):
        """应用启动事件"""
        try:
            if self._lifecycle:
                await self._lifecycle.startup()
            
            # 启动图表引擎
            if 'chart_engine' in self._components:
                await self._components['chart_engine'].start()
                logger.info("图表引擎启动完成")
            
            # 启动图表WebSocket处理器
            if 'chart_ws_handler' in self._components:
                await self._components['chart_ws_handler'].start()
                logger.info("图表WebSocket处理器启动完成")
            
            # 启动策略系统
            if 'strategy_system' in self._components:
                await self._components['strategy_system'].start()
                logger.info("策略系统启动完成")
            
            logger.info("应用启动完成")
        except Exception as e:
            logger.error(f"应用启动失败: {e}")
            raise
    
    async def _shutdown(self):
        """应用关闭事件"""
        try:
            # 关闭图表WebSocket处理器
            if 'chart_ws_handler' in self._components:
                await self._components['chart_ws_handler'].stop()
                logger.info("图表WebSocket处理器关闭完成")
            
            # 关闭图表引擎
            if 'chart_engine' in self._components:
                await self._components['chart_engine'].stop()
                logger.info("图表引擎关闭完成")
            
            # 关闭策略系统
            if 'strategy_system' in self._components:
                await self._components['strategy_system'].stop()
                logger.info("策略系统关闭完成")
            
            if self._lifecycle:
                await self._lifecycle.shutdown()
            logger.info("应用关闭完成")
        except Exception as e:
            logger.error(f"应用关闭失败: {e}")
    
    def get_app(self) -> FastAPI:
        """获取FastAPI应用实例"""
        if not self.app:
            self.app = self.create_app()
        return self.app
    
    def get_component(self, name: str) -> Any:
        """获取组件"""
        return self._components.get(name)


def create_app(config: Optional[AppConfig] = None) -> FastAPI:
    """创建应用的工厂函数"""
    redfire_app = RedFireApplication(config)
    return redfire_app.create_app()


# 全局应用实例
_app_instance: Optional[RedFireApplication] = None


def get_app_instance() -> RedFireApplication:
    """获取全局应用实例"""
    global _app_instance
    if _app_instance is None:
        _app_instance = RedFireApplication()
    return _app_instance
