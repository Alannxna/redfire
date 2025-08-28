# 🔧 RedFire外部配置管理服务
# 简单直接的配置管理微服务，完全舍弃DDD架构复杂性

"""
RedFire配置管理服务

这是一个基于外部微服务架构的配置管理系统，提供以下功能：

核心特性:
- 多源配置加载 (文件、环境变量、字典)
- 实时配置热重载
- REST API配置管理
- 配置验证和缓存
- 事件驱动的配置变更通知

架构特点:
- 完全舍弃复杂的DDD架构
- 采用简单直接的三层架构: API → Service → Repository
- 基于Pydantic的类型安全配置模型
- FastAPI高性能API服务
- 异步I/O支持

使用示例:
    # 基本使用
    from backend.config_service import initialize_config, get_config
    
    # 初始化配置
    config = await initialize_config("config.yaml")
    
    # 获取配置
    db_config = get_config().database
    redis_config = get_config().redis
    
    # 获取特定配置
    host = get_nested_config("database.host")

目录结构:
    backend/config_service/
    ├── __init__.py              # 包初始化
    ├── main.py                  # 服务启动入口
    ├── models/                  # Pydantic配置模型
    │   ├── __init__.py
    │   └── config_models.py     # 配置数据模型
    ├── core/                    # 核心服务层
    │   ├── __init__.py
    │   └── config_manager.py    # 配置管理器
    └── api/                     # API接口层
        ├── __init__.py
        └── config_api.py        # REST API接口
"""

__version__ = "1.0.0"
__author__ = "RedFire Team"
__description__ = "RedFire外部配置管理服务"

# =============================================================================
# 导入核心组件
# =============================================================================

# 配置模型
from .models.config_models import (
    # 主配置类
    AppConfig,
    
    # 子配置类
    DatabaseConfig,
    RedisConfig,
    VnPyConfig,
    SecurityConfig,
    MonitoringConfig,
    APIGatewayConfig,
    
    # 枚举类型
    Environment,
    LogLevel,
    CacheBackend,
    DatabaseEngine,
    
    # 工厂函数
    create_config_from_dict,
    create_config_from_file,
    create_config_from_env,
    validate_config,
    export_config_template
)

# 配置管理器
from .core.config_manager import (
    # 配置管理器类
    ExternalConfigManager,
    
    # 全局实例和便捷函数
    config_manager,
    initialize_config,
    get_config,
    get_database_config,
    get_redis_config,
    get_vnpy_config,
    get_security_config,
    get_monitoring_config,
    get_api_gateway_config,
    reload_config
)

# API应用
from .api.config_api import (
    create_app,
    create_config_app
)

# =============================================================================
# 包级别便捷函数
# =============================================================================

def get_version() -> str:
    """获取包版本"""
    return __version__

def get_package_info() -> dict:
    """获取包信息"""
    return {
        "name": "config_service",
        "version": __version__,
        "author": __author__,
        "description": __description__,
        "features": [
            "多源配置加载",
            "实时热重载",
            "REST API管理",
            "配置验证",
            "事件通知",
            "缓存支持"
        ],
        "architecture": "简单三层架构",
        "framework": "FastAPI + Pydantic"
    }

# =============================================================================
# 快速启动函数
# =============================================================================

async def quick_start(
    config_file: str = None,
    host: str = "0.0.0.0",
    port: int = 8001,
    reload: bool = False
) -> None:
    """
    快速启动配置服务
    
    Args:
        config_file: 配置文件路径
        host: 监听主机
        port: 监听端口
        reload: 是否启用热重载
    """
    import asyncio
    import logging
    
    try:
        import uvicorn  # type: ignore
    except ImportError:
        raise ImportError(
            "uvicorn is required for running the config service. "
            "Install it with: pip install uvicorn"
        )
    
    # 设置日志
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    try:
        # 初始化配置
        logger.info("🔧 初始化配置管理服务...")
        await initialize_config(config_file, enable_file_watching=True)
        
        # 创建应用
        app = create_app()
        
        # 获取最终配置
        config = get_config()
        final_host = config.host if hasattr(config, 'host') else host
        final_port = config.port if hasattr(config, 'port') else port
        
        logger.info(f"🚀 启动配置服务: http://{final_host}:{final_port}")
        logger.info(f"📚 API文档: http://{final_host}:{final_port}/docs")
        
        # 运行服务
        uvicorn_config = uvicorn.Config(
            app=app,
            host=final_host,
            port=final_port,
            reload=reload,
            log_level="info"
        )
        
        server = uvicorn.Server(uvicorn_config)
        await server.serve()
        
    except Exception as e:
        logger.error(f"❌ 配置服务启动失败: {e}")
        raise
    
    finally:
        await config_manager.shutdown()

# =============================================================================
# 导出列表
# =============================================================================

__all__ = [
    # 版本信息
    "__version__",
    "__author__",
    "__description__",
    
    # 配置模型
    "AppConfig",
    "DatabaseConfig", 
    "RedisConfig",
    "VnPyConfig",
    "SecurityConfig",
    "MonitoringConfig",
    "APIGatewayConfig",
    
    # 枚举
    "Environment",
    "LogLevel",
    "CacheBackend", 
    "DatabaseEngine",
    
    # 配置管理器
    "ExternalConfigManager",
    "config_manager",
    
    # 核心函数
    "initialize_config",
    "get_config",
    "get_database_config",
    "get_redis_config", 
    "get_vnpy_config",
    "get_security_config",
    "get_monitoring_config",
    "get_api_gateway_config",
    "reload_config",
    
    # 工厂函数
    "create_config_from_dict",
    "create_config_from_file",
    "create_config_from_env",
    "validate_config",
    "export_config_template",
    
    # API应用
    "create_app",
    "create_config_app",
    
    # 工具函数
    "get_version",
    "get_package_info",
    "quick_start"
]

# =============================================================================
# 包初始化日志
# =============================================================================

import logging
logger = logging.getLogger(__name__)
logger.debug(f"✅ RedFire配置管理服务包已加载 v{__version__}")
