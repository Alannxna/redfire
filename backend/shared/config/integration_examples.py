"""
配置加载器集成示例
================

展示如何在现有服务中集成新的配置加载器
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from pathlib import Path

from .config_loader import (
    get_config_loader, 
    load_config,
    load_app_config,
    load_database_config,
    create_legacy_adapter,
    ConfigSource
)

logger = logging.getLogger(__name__)


# =============================================================================
# 1. 现代化异步服务集成示例
# =============================================================================

class ModernService:
    """现代化异步服务示例"""
    
    def __init__(self):
        self.config: Dict[str, Any] = {}
        self.db_config: Dict[str, Any] = {}
        
    async def initialize(self):
        """异步初始化服务"""
        try:
            # 使用统一配置加载器
            loader = get_config_loader()
            
            async with loader:
                # 加载应用配置
                app_result = await loader.load_config(
                    'app',
                    sources=[ConfigSource.SERVICE, ConfigSource.FILE, ConfigSource.ENV],
                    fallback_config={
                        'debug': True,
                        'host': '0.0.0.0',
                        'port': 8000
                    }
                )
                self.config = app_result.data
                
                # 加载数据库配置
                db_result = await loader.load_config(
                    'database',
                    sources=[ConfigSource.SERVICE, ConfigSource.FILE],
                    fallback_config={
                        'engine': 'sqlite',
                        'database': 'fallback.db'
                    }
                )
                self.db_config = db_result.data
                
                logger.info("现代化服务配置加载完成")
                logger.info(f"应用配置源: {app_result.source}")
                logger.info(f"数据库配置源: {db_result.source}")
                
        except Exception as e:
            logger.error(f"服务初始化失败: {e}")
            raise
    
    def get_service_info(self) -> Dict[str, Any]:
        """获取服务信息"""
        return {
            'name': self.config.get('name', 'unknown'),
            'version': self.config.get('version', '1.0.0'),
            'database_engine': self.db_config.get('engine', 'unknown'),
            'config_loaded': len(self.config) > 0
        }


# =============================================================================
# 2. Legacy服务集成示例
# =============================================================================

class LegacyService:
    """Legacy服务集成示例"""
    
    def __init__(self):
        # 使用Legacy适配器，保持同步API
        self.config_adapter = create_legacy_adapter()
        self.config: Dict[str, Any] = {}
        
    def initialize(self):
        """同步初始化 (Legacy方式)"""
        try:
            # 使用同步API加载配置
            self.config = self.config_adapter.load_config('app')
            
            logger.info("Legacy服务配置加载完成")
            logger.info(f"配置项数量: {len(self.config)}")
            
        except Exception as e:
            logger.error(f"Legacy服务初始化失败: {e}")
            raise
    
    def get_config_value(self, key: str, default: Any = None) -> Any:
        """获取配置值 (Legacy方式)"""
        return self.config.get(key, default)


# =============================================================================
# 3. FastAPI服务集成示例
# =============================================================================

async def create_fastapi_app():
    """创建FastAPI应用的示例"""
    from fastapi import FastAPI
    
    app = FastAPI()
    
    # 在启动时加载配置
    @app.on_event("startup")
    async def startup_event():
        """启动事件处理"""
        try:
            # 加载应用配置
            config = await load_app_config(
                sources=[ConfigSource.SERVICE, ConfigSource.FILE],
                fallback_config={
                    'title': 'RedFire API',
                    'version': '1.0.0',
                    'debug': False
                }
            )
            
            # 更新FastAPI配置
            app.title = config.get('title', 'API')
            app.version = config.get('version', '1.0.0')
            app.debug = config.get('debug', False)
            
            # 加载数据库配置
            db_config = await load_database_config(
                fallback_config={
                    'engine': 'sqlite',
                    'database': 'app.db'
                }
            )
            
            # 存储配置供后续使用
            app.state.config = config
            app.state.db_config = db_config
            
            logger.info("FastAPI应用配置加载完成")
            
        except Exception as e:
            logger.error(f"FastAPI启动配置失败: {e}")
            raise
    
    @app.get("/config")
    async def get_config():
        """获取当前配置"""
        return {
            'app_config': app.state.config,
            'db_config': app.state.db_config
        }
    
    return app


# =============================================================================
# 4. 数据库服务集成示例
# =============================================================================

class DatabaseManager:
    """数据库管理器集成示例"""
    
    def __init__(self):
        self.connection = None
        self.config: Dict[str, Any] = {}
        
    async def initialize(self):
        """初始化数据库连接"""
        try:
            # 加载数据库配置
            self.config = await load_database_config(
                sources=[ConfigSource.SERVICE, ConfigSource.FILE],
                fallback_config={
                    'engine': 'sqlite',
                    'host': 'localhost',
                    'port': 3306,
                    'database': 'redfire',
                    'username': 'user',
                    'password': 'password'
                }
            )
            
            # 根据配置创建连接
            engine = self.config.get('engine', 'sqlite')
            
            if engine == 'mysql':
                await self._create_mysql_connection()
            elif engine == 'postgresql':
                await self._create_postgres_connection()
            else:
                await self._create_sqlite_connection()
                
            logger.info(f"数据库连接已建立: {engine}")
            
        except Exception as e:
            logger.error(f"数据库初始化失败: {e}")
            raise
    
    async def _create_mysql_connection(self):
        """创建MySQL连接"""
        # 示例实现
        connection_string = (
            f"mysql://{self.config['username']}:{self.config['password']}"
            f"@{self.config['host']}:{self.config['port']}/{self.config['database']}"
        )
        logger.info(f"MySQL连接字符串: {connection_string}")
        # 实际连接逻辑...
    
    async def _create_postgres_connection(self):
        """创建PostgreSQL连接"""
        # 示例实现
        connection_string = (
            f"postgresql://{self.config['username']}:{self.config['password']}"
            f"@{self.config['host']}:{self.config['port']}/{self.config['database']}"
        )
        logger.info(f"PostgreSQL连接字符串: {connection_string}")
        # 实际连接逻辑...
    
    async def _create_sqlite_connection(self):
        """创建SQLite连接"""
        # 示例实现
        db_path = self.config.get('database', 'app.db')
        logger.info(f"SQLite数据库: {db_path}")
        # 实际连接逻辑...


# =============================================================================
# 5. VnPy集成示例
# =============================================================================

class VnPyIntegrationService:
    """VnPy集成服务示例"""
    
    def __init__(self):
        self.vnpy_config: Dict[str, Any] = {}
        self.gateway_configs: Dict[str, Any] = {}
        
    async def initialize(self):
        """初始化VnPy集成"""
        try:
            loader = get_config_loader()
            
            async with loader:
                # 加载VnPy配置
                vnpy_result = await loader.load_config(
                    'vnpy',
                    sources=[ConfigSource.SERVICE, ConfigSource.FILE],
                    fallback_config={
                        'data_path': './vnpy_data',
                        'log_path': './vnpy_logs',
                        'gateway_settings': {
                            'ctp': {'enabled': False}
                        }
                    }
                )
                self.vnpy_config = vnpy_result.data
                
                # 加载网关配置
                gateway_result = await loader.load_config(
                    'gateway',
                    sources=[ConfigSource.SERVICE, ConfigSource.FILE],
                    fallback_config={
                        'ctp': {'enabled': False},
                        'binance': {'enabled': False}
                    }
                )
                self.gateway_configs = gateway_result.data
                
                logger.info("VnPy集成配置加载完成")
                
        except Exception as e:
            logger.error(f"VnPy集成初始化失败: {e}")
            raise
    
    def get_enabled_gateways(self) -> list:
        """获取启用的网关列表"""
        enabled = []
        for gateway, config in self.gateway_configs.items():
            if config.get('enabled', False):
                enabled.append(gateway)
        return enabled


# =============================================================================
# 6. 配置热重载示例
# =============================================================================

class ConfigurableService:
    """支持配置热重载的服务示例"""
    
    def __init__(self):
        self.config: Dict[str, Any] = {}
        self.reload_callbacks: list = []
        
    async def initialize(self):
        """初始化服务"""
        await self._load_config()
        
        # 设置配置重载监听
        # 这里可以集成文件监听或配置服务的变更通知
        
    async def _load_config(self):
        """加载配置"""
        try:
            self.config = await load_app_config(
                sources=[ConfigSource.SERVICE, ConfigSource.FILE],
                fallback_config={'debug': True}
            )
            
            # 触发重载回调
            for callback in self.reload_callbacks:
                await callback(self.config)
                
            logger.info("配置重载完成")
            
        except Exception as e:
            logger.error(f"配置重载失败: {e}")
    
    async def reload_config(self):
        """手动重载配置"""
        # 清除缓存
        loader = get_config_loader()
        loader.clear_cache('app')
        
        # 重新加载
        await self._load_config()
    
    def add_reload_callback(self, callback):
        """添加重载回调"""
        self.reload_callbacks.append(callback)


# =============================================================================
# 7. 运行示例
# =============================================================================

async def run_integration_examples():
    """运行集成示例"""
    
    print("🚀 开始运行配置加载器集成示例...")
    
    # 1. 现代化服务示例
    print("\n1. 现代化异步服务示例:")
    modern_service = ModernService()
    await modern_service.initialize()
    print(f"   服务信息: {modern_service.get_service_info()}")
    
    # 2. Legacy服务示例
    print("\n2. Legacy服务示例:")
    legacy_service = LegacyService()
    legacy_service.initialize()
    print(f"   配置值示例: debug={legacy_service.get_config_value('debug', False)}")
    
    # 3. 数据库管理器示例
    print("\n3. 数据库管理器示例:")
    db_manager = DatabaseManager()
    await db_manager.initialize()
    print(f"   数据库引擎: {db_manager.config.get('engine', 'unknown')}")
    
    # 4. VnPy集成示例
    print("\n4. VnPy集成示例:")
    vnpy_service = VnPyIntegrationService()
    await vnpy_service.initialize()
    print(f"   启用的网关: {vnpy_service.get_enabled_gateways()}")
    
    # 5. 配置热重载示例
    print("\n5. 配置热重载示例:")
    configurable_service = ConfigurableService()
    await configurable_service.initialize()
    
    # 添加重载回调
    async def on_config_reload(config):
        print(f"   配置已重载: debug={config.get('debug', False)}")
    
    configurable_service.add_reload_callback(on_config_reload)
    await configurable_service.reload_config()
    
    # 6. 健康检查示例
    print("\n6. 配置加载器健康检查:")
    loader = get_config_loader()
    async with loader:
        health = await loader.health_check()
        print(f"   健康状态: {health}")
    
    print("\n✅ 所有集成示例运行完成!")


if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 运行示例
    asyncio.run(run_integration_examples())
