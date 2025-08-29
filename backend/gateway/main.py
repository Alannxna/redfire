"""
API网关主入口
============

启动统一的API网关服务
"""

import asyncio
import logging
import uvicorn
from contextlib import asynccontextmanager

from .core.gateway import APIGateway
from .config.gateway_config import GatewayConfig
from ..shared.communication import ServiceClient, register_service

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app):
    """应用生命周期管理"""
    # 启动时初始化
    logger.info("启动API网关...")
    
    # 从环境变量加载配置
    config = GatewayConfig.from_env()
    
    # 创建网关实例
    gateway = APIGateway(config)
    app.state.gateway = gateway
    
    # 启动网关
    await gateway.start()
    
    # 注册服务到服务发现
    await _register_services(config)
    
    logger.info("API网关启动完成")
    
    yield
    
    # 关闭时清理
    logger.info("关闭API网关...")
    await gateway.stop()
    logger.info("API网关已关闭")


async def _register_services(config: GatewayConfig):
    """注册微服务到服务发现"""
    for service_name, service_config in config.services.items():
        instances = service_config.get("instances", [])
        
        for instance in instances:
            await config.registry.register_service({
                "name": service_name,
                "host": instance["host"],
                "port": instance["port"],
                "health_check_url": instance.get("health_check_url", "/health"),
                "metadata": {
                    "prefix": service_config.get("prefix", ""),
                    "version": instance.get("version", "1.0.0")
                }
            })
        
        # 注册到服务客户端池
        base_url = f"http://{instances[0]['host']}:{instances[0]['port']}"
        register_service(service_name, base_url)


def create_app():
    """创建FastAPI应用"""
    config = GatewayConfig.from_env()
    gateway = APIGateway(config)
    
    # 设置生命周期
    gateway.app.router.lifespan_context = lifespan
    
    return gateway.app


def main():
    """主函数"""
    config = GatewayConfig.from_env()
    
    logger.info(f"启动API网关在 {config.host}:{config.port}")
    
    uvicorn.run(
        "gateway.main:create_app",
        factory=True,
        host=config.host,
        port=config.port,
        reload=config.debug,
        log_level="info" if not config.debug else "debug"
    )


if __name__ == "__main__":
    main()
