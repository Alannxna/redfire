"""
应用生命周期管理
===============

管理应用的启动和关闭流程，包括组件初始化和资源清理
"""

import logging
import asyncio
from typing import List, Callable, Any
from fastapi import FastAPI

from .config import AppConfig
from .initializer import ComponentInitializer

logger = logging.getLogger(__name__)


class ApplicationLifecycle:
    """应用生命周期管理"""
    
    def __init__(self, app: FastAPI, config: AppConfig):
        self.app = app
        self.config = config
        self.initializer = ComponentInitializer(config)
        self._startup_hooks: List[Callable] = []
        self._shutdown_hooks: List[Callable] = []
        self._components_started: List[str] = []
        
    def add_startup_hook(self, hook: Callable):
        """添加启动钩子"""
        self._startup_hooks.append(hook)
    
    def add_shutdown_hook(self, hook: Callable):
        """添加关闭钩子"""
        self._shutdown_hooks.append(hook)
    
    async def startup(self):
        """启动事件处理"""
        logger.info("🚀 开始启动RedFire应用...")
        logger.info(f"📊 运行环境: {self.config.environment}")
        logger.info(f"🔧 调试模式: {self.config.debug}")
        
        try:
            # 1. 执行启动前钩子
            await self._execute_startup_hooks()
            
            # 2. 初始化核心组件
            await self._initialize_core_components()
            
            # 3. 初始化业务组件
            await self._initialize_business_components()
            
            # 4. 启动监控服务
            await self._start_monitoring()
            
            # 5. 执行启动后处理
            await self._post_startup()
            
            logger.info("✅ RedFire应用启动完成!")
            
        except Exception as e:
            logger.error(f"❌ RedFire应用启动失败: {e}")
            # 如果启动失败，尝试清理已启动的组件
            await self._emergency_cleanup()
            raise
    
    async def shutdown(self):
        """关闭事件处理"""
        logger.info("🛑 开始关闭RedFire应用...")
        
        try:
            # 1. 执行关闭前钩子
            await self._execute_shutdown_hooks()
            
            # 2. 优雅关闭所有组件
            await self._graceful_shutdown()
            
            # 3. 清理资源
            await self._cleanup_resources()
            
            logger.info("✅ RedFire应用已优雅关闭")
            
        except Exception as e:
            logger.error(f"❌ RedFire应用关闭过程中出现错误: {e}")
            # 强制清理
            await self._force_cleanup()
    
    async def _execute_startup_hooks(self):
        """执行启动钩子"""
        for hook in self._startup_hooks:
            try:
                if asyncio.iscoroutinefunction(hook):
                    await hook()
                else:
                    hook()
                logger.debug(f"启动钩子执行完成: {hook.__name__}")
            except Exception as e:
                logger.error(f"启动钩子执行失败 {hook.__name__}: {e}")
                raise
    
    async def _execute_shutdown_hooks(self):
        """执行关闭钩子"""
        for hook in reversed(self._shutdown_hooks):  # 逆序执行
            try:
                if asyncio.iscoroutinefunction(hook):
                    await hook()
                else:
                    hook()
                logger.debug(f"关闭钩子执行完成: {hook.__name__}")
            except Exception as e:
                logger.error(f"关闭钩子执行失败 {hook.__name__}: {e}")
    
    async def _initialize_core_components(self):
        """初始化核心组件"""
        logger.info("初始化核心组件...")
        
        components = [
            ("database", self.initializer.initialize_database),
            ("redis", self.initializer.initialize_redis),
        ]
        
        for name, init_func in components:
            try:
                await init_func()
                self._components_started.append(name)
                logger.info(f"✅ {name} 初始化完成")
            except Exception as e:
                logger.error(f"❌ {name} 初始化失败: {e}")
                raise
    
    async def _initialize_business_components(self):
        """初始化业务组件"""
        logger.info("初始化业务组件...")
        
        # VnPy引擎初始化（可选）
        try:
            await self.initializer.initialize_vnpy_engine()
            self._components_started.append("vnpy_engine")
            logger.info("✅ VnPy引擎初始化完成")
        except Exception as e:
            logger.warning(f"⚠️ VnPy引擎初始化失败: {e}")
            # VnPy引擎初始化失败不影响整体启动
        
        # 策略引擎初始化（可选）
        try:
            await self.initializer.initialize_strategy_engine()
            self._components_started.append("strategy_engine")
            logger.info("✅ 策略引擎初始化完成")
        except Exception as e:
            logger.warning(f"⚠️ 策略引擎初始化失败: {e}")
    
    async def _start_monitoring(self):
        """启动监控服务"""
        try:
            await self.initializer.initialize_monitoring()
            self._components_started.append("monitoring")
            logger.info("✅ 监控服务启动完成")
        except Exception as e:
            logger.warning(f"⚠️ 监控服务启动失败: {e}")
    
    async def _post_startup(self):
        """启动后处理"""
        # 记录启动信息
        logger.info(f"🏠 服务地址: http://{self.config.host}:{self.config.port}")
        
        if self.config.is_development():
            logger.info(f"📚 API文档: http://{self.config.host}:{self.config.port}/docs")
            logger.info(f"🔍 ReDoc: http://{self.config.host}:{self.config.port}/redoc")
        
        # 验证关键组件状态
        await self._validate_components()
    
    async def _validate_components(self):
        """验证组件状态"""
        logger.info("验证组件状态...")
        
        # 数据库连接检查
        try:
            await self.initializer.validate_database_connection()
            logger.info("✅ 数据库连接正常")
        except Exception as e:
            logger.error(f"❌ 数据库连接异常: {e}")
        
        # Redis连接检查
        try:
            await self.initializer.validate_redis_connection()
            logger.info("✅ Redis连接正常")
        except Exception as e:
            logger.warning(f"⚠️ Redis连接异常: {e}")
    
    async def _graceful_shutdown(self):
        """优雅关闭所有组件"""
        logger.info("优雅关闭组件...")
        
        # 按启动相反顺序关闭组件
        for component in reversed(self._components_started):
            try:
                await self._shutdown_component(component)
                logger.info(f"✅ {component} 已关闭")
            except Exception as e:
                logger.error(f"❌ {component} 关闭失败: {e}")
    
    async def _shutdown_component(self, component: str):
        """关闭指定组件"""
        shutdown_methods = {
            "monitoring": self.initializer.shutdown_monitoring,
            "strategy_engine": self.initializer.shutdown_strategy_engine,
            "vnpy_engine": self.initializer.shutdown_vnpy_engine,
            "redis": self.initializer.shutdown_redis,
            "database": self.initializer.shutdown_database,
        }
        
        method = shutdown_methods.get(component)
        if method:
            await method()
    
    async def _cleanup_resources(self):
        """清理资源"""
        logger.info("清理系统资源...")
        
        # 清理临时文件
        try:
            import shutil
            import tempfile
            temp_dir = self.config.temp_dir
            if temp_dir and temp_dir != tempfile.gettempdir():
                # 只清理应用临时目录，不清理系统临时目录
                for item in Path(temp_dir).glob("*"):
                    if item.is_file():
                        item.unlink()
                    elif item.is_dir():
                        shutil.rmtree(item)
                logger.info("✅ 临时文件清理完成")
        except Exception as e:
            logger.warning(f"⚠️ 临时文件清理失败: {e}")
    
    async def _emergency_cleanup(self):
        """紧急清理（启动失败时）"""
        logger.warning("执行紧急清理...")
        
        for component in reversed(self._components_started):
            try:
                await self._shutdown_component(component)
                logger.info(f"紧急清理 {component} 完成")
            except Exception as e:
                logger.error(f"紧急清理 {component} 失败: {e}")
    
    async def _force_cleanup(self):
        """强制清理（关闭失败时）"""
        logger.warning("执行强制清理...")
        
        # 强制关闭所有连接
        try:
            await self.initializer.force_cleanup()
            logger.info("强制清理完成")
        except Exception as e:
            logger.error(f"强制清理失败: {e}")


from pathlib import Path
