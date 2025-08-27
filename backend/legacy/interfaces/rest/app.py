"""
VnPy Web API 应用程序
====================

FastAPI应用程序的主入口点
"""

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import logging
import os
from typing import Dict, Any

from .controllers.user_controller import UserController
from .controllers.dashboard_controller import DashboardController
from .controllers.trading_controller import TradingController
from .middleware.auth_middleware import AuthMiddleware
from .middleware.error_middleware import ErrorHandlingMiddleware
from .models.common import APIResponse, HealthCheckResponse
from ...core.config.unified_config import UnifiedConfig


class VnPyWebAPI:
    """VnPy Web API 应用程序"""
    
    def __init__(self):
        self.app = FastAPI(
            title="VnPy Web API",
            description="VnPy Web后端API服务",
            version="1.0.0",
            docs_url="/docs",
            redoc_url="/redoc"
        )
        
        self._logger = logging.getLogger(self.__class__.__name__)
        self._config = UnifiedConfig()
        
        # 初始化组件
        self._setup_middleware()
        self._setup_static_files()
        self._setup_routes()
        self._setup_event_handlers()
    
    def _setup_middleware(self):
        """设置中间件"""
        # CORS中间件
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # 生产环境应该限制具体域名
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # 错误处理中间件
        error_middleware = ErrorHandlingMiddleware()
        self.app.middleware("http")(error_middleware.handle_errors)
        
        # 认证中间件
        auth_middleware = AuthMiddleware()
        self.app.middleware("http")(auth_middleware.authenticate)
    
    def _setup_static_files(self):
        """设置静态文件服务"""
        # 获取静态文件目录路径
        current_dir = os.path.dirname(__file__)
        static_dir = os.path.join(current_dir, "static")
        
        # 确保静态文件目录存在
        if os.path.exists(static_dir):
            self.app.mount("/dashboard/static", StaticFiles(directory=static_dir), name="dashboard_static")
            self._logger.info(f"静态文件服务已挂载: {static_dir}")
        else:
            self._logger.warning(f"静态文件目录不存在: {static_dir}")
    
    def _setup_routes(self):
        """设置路由"""
        # 健康检查
        @self.app.get("/health", response_model=HealthCheckResponse)
        async def health_check():
            return HealthCheckResponse(
                status="healthy",
                message="VnPy Web API is running",
                version="1.0.0"
            )
        
        @self.app.get("/", response_model=APIResponse)
        async def root():
            return APIResponse(
                success=True,
                message="欢迎使用 VnPy Web API",
                data={
                    "service": "VnPy Web API",
                    "version": "1.0.0",
                    "docs": "/docs",
                    "health": "/health",
                    "dashboard": "/dashboard"
                }
            )
        
        # 用户相关路由
        user_controller = UserController()
        self.app.include_router(
            user_controller.router,
            prefix="/api/v1/users",
            tags=["用户管理"]
        )
        
        # 仪表盘相关路由
        dashboard_controller = DashboardController()
        self.app.include_router(
            dashboard_controller.router,
            prefix="/dashboard",
            tags=["系统监控"]
        )
        
        # 交易相关路由
        trading_controller = TradingController()
        self.app.include_router(
            trading_controller.router,
            tags=["交易管理"]
        )
        
        # 策略引擎相关路由
        from .controllers.strategy_engine_controller import router as strategy_engine_router
        self.app.include_router(strategy_engine_router)
        
        # 数据管理相关路由
        from ...api.data.market_data_api import market_data_router
        from ...api.data.historical_data_api import historical_data_router
        from ...api.data.backtest_api import backtest_router
        
        self.app.include_router(market_data_router)
        self.app.include_router(historical_data_router)
        self.app.include_router(backtest_router)
        
        # 监控系统相关路由
        # 注意：这里暂时注释掉，因为需要依赖注入支持
        # from .controllers.monitoring_controller import create_monitoring_router
        # monitoring_service = container.get(MonitoringApplicationService)
        # monitoring_router = create_monitoring_router(monitoring_service)
        # self.app.include_router(monitoring_router)
    
    def _setup_event_handlers(self):
        """设置事件处理器"""
        @self.app.on_event("startup")
        async def startup_event():
            self._logger.info("🚀 VnPy Web API 启动中...")
            self._logger.info(f"📊 配置环境: {self._config.environment}")
            self._logger.info("✅ VnPy Web API 启动完成")
        
        @self.app.on_event("shutdown")
        async def shutdown_event():
            self._logger.info("🛑 VnPy Web API 关闭中...")
            self._logger.info("✅ VnPy Web API 关闭完成")
    
    def get_app(self) -> FastAPI:
        """获取FastAPI应用实例"""
        return self.app


# 创建应用实例
vnpy_api = VnPyWebAPI()
app = vnpy_api.get_app()


def create_app() -> FastAPI:
    """创建FastAPI应用实例的工厂函数"""
    api = VnPyWebAPI()
    return api.get_app()


if __name__ == "__main__":
    import uvicorn
    
    # 开发模式运行
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )