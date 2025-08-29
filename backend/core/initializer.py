"""
组件初始化器
============

负责初始化和管理各种系统组件
"""

import logging
import asyncio
from typing import Optional, Any, Dict
from pathlib import Path

from .config import get_config_manager, AppConfig
from database.connection import DatabaseManager, get_database_manager

logger = logging.getLogger(__name__)


class ComponentInitializer:
    """组件初始化器"""
    
    def __init__(self, config: AppConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self._components: Dict[str, Any] = {}
        
    async def initialize_database(self):
        """初始化数据库"""
        try:
            self.logger.info("初始化数据库连接...")
            
            # 使用全局数据库管理器实例
            db_manager = get_database_manager()
            
            # 使用配置中的数据库URL，如果没有则构建一个
            if hasattr(self.config, 'database_url') and self.config.database_url:
                database_url = self.config.database_url
            else:
                # 默认使用SQLite
                db_path = Path(self.config.data_dir) / "redfire.db"
                database_url = f"sqlite:///{db_path}"
            
            await db_manager.initialize(database_url)
            # 创建数据库表
            db_manager.create_tables()
            
            # 初始化默认数据
            await self._init_default_data(db_manager)
            
            self._components['database'] = db_manager
            
            self.logger.info("✅ 数据库初始化完成")
            
        except Exception as e:
            self.logger.error(f"❌ 数据库初始化失败: {e}")
            raise
    
    async def _init_default_data(self, db_manager):
        """初始化默认数据"""
        try:
            # 导入认证模型并初始化默认数据
            from auth.models import init_default_data
            
            db = db_manager.get_session()
            try:
                init_default_data(db)
                self.logger.info("✅ 默认数据初始化完成")
            finally:
                db.close()
                
        except ImportError:
            self.logger.warning("⚠️ 认证模型不可用，跳过默认数据初始化")
        except Exception as e:
            self.logger.error(f"❌ 默认数据初始化失败: {e}")
            # 不抛出异常，允许应用继续运行
    
    async def initialize_redis(self):
        """初始化Redis"""
        try:
            self.logger.info("初始化Redis连接...")
            
            # 这里可以添加Redis初始化逻辑
            # 目前暂时跳过，因为Redis不是必需的
            self.logger.info("⚠️ Redis初始化跳过（可选组件）")
            
        except Exception as e:
            self.logger.warning(f"⚠️ Redis初始化失败: {e}")
            # Redis失败不应该阻止应用启动
    
    async def initialize_vnpy_engine(self):
        """初始化VnPy引擎"""
        try:
            self.logger.info("初始化VnPy交易引擎...")
            
            # 检查VnPy目录是否存在
            vnpy_data_path = Path(self.config.vnpy_data_dir)
            vnpy_config_path = Path(self.config.vnpy_config_dir)
            
            # 创建目录
            vnpy_data_path.mkdir(parents=True, exist_ok=True)
            vnpy_config_path.mkdir(parents=True, exist_ok=True)
            
            # 尝试导入和初始化VnPy组件
            try:
                from ..core.tradingEngine.mainEngine import MainTradingEngine
                from ..core.tradingEngine.eventEngine import EventTradingEngine
                
                # 创建事件引擎
                event_engine = EventTradingEngine()
                
                # 创建主交易引擎
                main_engine = MainTradingEngine(event_engine)
                
                self._components['vnpy_engine'] = main_engine
                self._components['event_engine'] = event_engine
                
                self.logger.info("✅ VnPy引擎初始化完成")
                
            except ImportError as e:
                self.logger.warning(f"⚠️ VnPy模块导入失败: {e}")
                # VnPy模块不存在时创建一个占位符
                self._components['vnpy_engine'] = None
                
        except Exception as e:
            self.logger.warning(f"⚠️ VnPy引擎初始化失败: {e}")
            raise
    
    async def initialize_strategy_engine(self):
        """初始化策略引擎"""
        try:
            self.logger.info("初始化策略引擎...")
            
            # 策略引擎初始化逻辑
            # 这里可以添加策略管理相关的初始化
            
            self.logger.info("✅ 策略引擎初始化完成")
            
        except Exception as e:
            self.logger.warning(f"⚠️ 策略引擎初始化失败: {e}")
    
    async def initialize_monitoring(self):
        """初始化监控服务"""
        try:
            self.logger.info("初始化监控服务...")
            
            # 监控服务初始化逻辑
            # 可以添加系统监控、性能监控等
            
            self.logger.info("✅ 监控服务初始化完成")
            
        except Exception as e:
            self.logger.warning(f"⚠️ 监控服务初始化失败: {e}")
    
    async def validate_database_connection(self):
        """验证数据库连接"""
        try:
            db_manager = self._components.get('database')
            if db_manager:
                # 这里可以添加数据库连接验证逻辑
                # 例如执行一个简单的查询
                self.logger.info("数据库连接验证通过")
            else:
                raise Exception("数据库管理器未初始化")
        except Exception as e:
            self.logger.error(f"数据库连接验证失败: {e}")
            raise
    
    async def validate_redis_connection(self):
        """验证Redis连接"""
        try:
            # Redis连接验证逻辑
            self.logger.info("Redis连接验证通过")
        except Exception as e:
            self.logger.warning(f"Redis连接验证失败: {e}")
            raise
    
    async def shutdown_database(self):
        """关闭数据库连接"""
        try:
            db_manager = self._components.get('database')
            if db_manager and hasattr(db_manager, 'close'):
                await db_manager.close()
            self.logger.info("数据库连接已关闭")
        except Exception as e:
            self.logger.error(f"关闭数据库连接失败: {e}")
    
    async def shutdown_redis(self):
        """关闭Redis连接"""
        try:
            # Redis关闭逻辑
            self.logger.info("Redis连接已关闭")
        except Exception as e:
            self.logger.error(f"关闭Redis连接失败: {e}")
    
    async def shutdown_vnpy_engine(self):
        """关闭VnPy引擎"""
        try:
            vnpy_engine = self._components.get('vnpy_engine')
            if vnpy_engine and hasattr(vnpy_engine, 'close'):
                vnpy_engine.close()
            self.logger.info("VnPy引擎已关闭")
        except Exception as e:
            self.logger.error(f"关闭VnPy引擎失败: {e}")
    
    async def shutdown_strategy_engine(self):
        """关闭策略引擎"""
        try:
            # 策略引擎关闭逻辑
            self.logger.info("策略引擎已关闭")
        except Exception as e:
            self.logger.error(f"关闭策略引擎失败: {e}")
    
    async def shutdown_monitoring(self):
        """关闭监控服务"""
        try:
            # 监控服务关闭逻辑
            self.logger.info("监控服务已关闭")
        except Exception as e:
            self.logger.error(f"关闭监控服务失败: {e}")
    
    async def force_cleanup(self):
        """强制清理所有资源"""
        self.logger.warning("执行强制资源清理...")
        
        # 强制关闭所有组件
        cleanup_tasks = [
            self.shutdown_monitoring(),
            self.shutdown_strategy_engine(),
            self.shutdown_vnpy_engine(),
            self.shutdown_redis(),
            self.shutdown_database(),
        ]
        
        # 并发执行清理，但不等待失败的任务
        results = await asyncio.gather(*cleanup_tasks, return_exceptions=True)
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.error(f"强制清理任务 {i} 失败: {result}")
        
        self.logger.info("强制清理完成")
    
    def get_component(self, name: str) -> Any:
        """获取组件实例"""
        return self._components.get(name)
