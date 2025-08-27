"""
CQRS配置管理器
==============

统一管理CQRS架构的命令查询处理器配置、自动注册机制和依赖注入
"""

# 标准库导入
import inspect
import logging
from typing import Dict, Type, List, Any, Optional, Tuple, get_type_hints
from abc import ABC, abstractmethod
from pathlib import Path
import importlib
import pkgutil

# 核心层导入
from ...core.infrastructure.dependency_container import DependencyContainer, ServiceScope

# 应用层内部导入
from ..commands.command_bus import Command, CommandHandler, ICommandBus, CommandBus
from ..queries.query_bus import Query, QueryHandler, IQueryBus, QueryBus


logger = logging.getLogger(__name__)


class CQRSModuleInfo:
    """CQRS模块信息"""
    
    def __init__(self, name: str, path: str):
        self.name = name
        self.path = path
        self.commands: List[Type[Command]] = []
        self.queries: List[Type[Query]] = []
        self.command_handlers: List[Type[CommandHandler]] = []
        self.query_handlers: List[Type[QueryHandler]] = []
        self.command_handler_mapping: Dict[Type[Command], Type[CommandHandler]] = {}
        self.query_handler_mapping: Dict[Type[Query], Type[QueryHandler]] = {}


class CQRSHandlerRegistry:
    """CQRS处理器注册表"""
    
    def __init__(self):
        self.command_handlers: Dict[Type[Command], Type[CommandHandler]] = {}
        self.query_handlers: Dict[Type[Query], Type[QueryHandler]] = {}
        self.registered_modules: Dict[str, CQRSModuleInfo] = {}
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def register_command_handler(self, command_type: Type[Command], handler_type: Type[CommandHandler]) -> None:
        """注册命令处理器"""
        self.command_handlers[command_type] = handler_type
        self.logger.debug(f"注册命令处理器: {command_type.__name__} -> {handler_type.__name__}")
    
    def register_query_handler(self, query_type: Type[Query], handler_type: Type[QueryHandler]) -> None:
        """注册查询处理器"""
        self.query_handlers[query_type] = handler_type
        self.logger.debug(f"注册查询处理器: {query_type.__name__} -> {handler_type.__name__}")
    
    def register_module(self, module_info: CQRSModuleInfo) -> None:
        """注册模块信息"""
        self.registered_modules[module_info.name] = module_info
        
        # 注册模块中的处理器映射
        for command_type, handler_type in module_info.command_handler_mapping.items():
            self.register_command_handler(command_type, handler_type)
        
        for query_type, handler_type in module_info.query_handler_mapping.items():
            self.register_query_handler(query_type, handler_type)
    
    def get_command_handler(self, command_type: Type[Command]) -> Optional[Type[CommandHandler]]:
        """获取命令处理器类型"""
        return self.command_handlers.get(command_type)
    
    def get_query_handler(self, query_type: Type[Query]) -> Optional[Type[QueryHandler]]:
        """获取查询处理器类型"""
        return self.query_handlers.get(query_type)
    
    def get_all_command_handlers(self) -> Dict[Type[Command], Type[CommandHandler]]:
        """获取所有命令处理器"""
        return self.command_handlers.copy()
    
    def get_all_query_handlers(self) -> Dict[Type[Query], Type[QueryHandler]]:
        """获取所有查询处理器"""
        return self.query_handlers.copy()


class CQRSAutoDiscovery:
    """CQRS自动发现机制"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def discover_cqrs_modules(self, base_package: str) -> List[CQRSModuleInfo]:
        """自动发现CQRS模块"""
        modules = []
        try:
            # 导入基础包
            base_module = importlib.import_module(base_package)
            base_path = Path(base_module.__file__).parent
            
            # 遍历子包发现CQRS组件
            for finder, name, ispkg in pkgutil.walk_packages(
                [str(base_path)], 
                prefix=f"{base_package}."
            ):
                if self._is_cqrs_module(name):
                    module_info = self._analyze_module(name)
                    if module_info:
                        modules.append(module_info)
            
            self.logger.info(f"发现 {len(modules)} 个CQRS模块")
            return modules
            
        except Exception as e:
            self.logger.error(f"CQRS模块自动发现失败: {e}")
            return []
    
    def _is_cqrs_module(self, module_name: str) -> bool:
        """判断是否为CQRS模块"""
        cqrs_keywords = ['commands', 'queries', 'handlers']
        return any(keyword in module_name for keyword in cqrs_keywords)
    
    def _analyze_module(self, module_name: str) -> Optional[CQRSModuleInfo]:
        """分析模块中的CQRS组件"""
        try:
            module = importlib.import_module(module_name)
            module_info = CQRSModuleInfo(module_name, module.__file__ or "")
            
            # 扫描模块中的类
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if obj.__module__ != module_name:
                    continue
                
                # 检查是否为命令、查询或处理器
                if self._is_command(obj):
                    module_info.commands.append(obj)
                elif self._is_query(obj):
                    module_info.queries.append(obj)
                elif self._is_command_handler(obj):
                    module_info.command_handlers.append(obj)
                elif self._is_query_handler(obj):
                    module_info.query_handlers.append(obj)
            
            # 建立处理器映射关系
            self._build_handler_mappings(module_info)
            
            if (module_info.commands or module_info.queries or 
                module_info.command_handlers or module_info.query_handlers):
                return module_info
            
        except Exception as e:
            self.logger.warning(f"分析模块 {module_name} 失败: {e}")
        
        return None
    
    def _is_command(self, cls: Type) -> bool:
        """检查是否为命令类"""
        return (inspect.isclass(cls) and 
                issubclass(cls, Command) and 
                cls is not Command)
    
    def _is_query(self, cls: Type) -> bool:
        """检查是否为查询类"""
        return (inspect.isclass(cls) and 
                issubclass(cls, Query) and 
                cls is not Query)
    
    def _is_command_handler(self, cls: Type) -> bool:
        """检查是否为命令处理器"""
        return (inspect.isclass(cls) and 
                issubclass(cls, CommandHandler) and 
                cls is not CommandHandler)
    
    def _is_query_handler(self, cls: Type) -> bool:
        """检查是否为查询处理器"""
        return (inspect.isclass(cls) and 
                issubclass(cls, QueryHandler) and 
                cls is not QueryHandler)
    
    def _build_handler_mappings(self, module_info: CQRSModuleInfo) -> None:
        """构建处理器映射关系"""
        # 构建命令处理器映射
        for handler_type in module_info.command_handlers:
            command_type = self._extract_handled_type(handler_type, Command)
            if command_type:
                module_info.command_handler_mapping[command_type] = handler_type
        
        # 构建查询处理器映射
        for handler_type in module_info.query_handlers:
            query_type = self._extract_handled_type(handler_type, Query)
            if query_type:
                module_info.query_handler_mapping[query_type] = handler_type
    
    def _extract_handled_type(self, handler_type: Type, base_type: Type) -> Optional[Type]:
        """从处理器中提取处理的命令/查询类型"""
        try:
            # 检查handle方法的类型注解
            handle_method = getattr(handler_type, 'handle', None)
            if handle_method:
                type_hints = get_type_hints(handle_method)
                for param_name, param_type in type_hints.items():
                    if (param_name != 'return' and 
                        inspect.isclass(param_type) and 
                        issubclass(param_type, base_type) and
                        param_type is not base_type):
                        return param_type
            
            # 尝试从类名推断
            handler_name = handler_type.__name__
            if handler_name.endswith('Handler'):
                potential_type_name = handler_name[:-7]  # 去掉Handler后缀
                
                # 在当前模块中查找对应的命令/查询类型
                module = importlib.import_module(handler_type.__module__)
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if (name == potential_type_name and 
                        issubclass(obj, base_type) and 
                        obj is not base_type):
                        return obj
            
        except Exception as e:
            self.logger.debug(f"提取处理器类型失败 {handler_type.__name__}: {e}")
        
        return None


class CQRSConfigurationManager:
    """CQRS配置管理器"""
    
    def __init__(self, container: DependencyContainer):
        self.container = container
        self.registry = CQRSHandlerRegistry()
        self.discovery = CQRSAutoDiscovery()
        self.logger = logging.getLogger(self.__class__.__name__)
        self._initialized = False
    
    async def initialize(self, auto_discover: bool = True, base_packages: Optional[List[str]] = None) -> None:
        """初始化CQRS配置"""
        if self._initialized:
            return
        
        self.logger.info("开始初始化CQRS配置...")
        
        try:
            # 1. 注册CQRS基础设施
            await self._register_cqrs_infrastructure()
            
            # 2. 自动发现和注册处理器
            if auto_discover:
                await self._auto_register_handlers(base_packages or ["backend.src.application"])
            
            # 3. 配置处理器映射
            await self._configure_handler_mappings()
            
            self._initialized = True
            self.logger.info("CQRS配置初始化完成")
            
        except Exception as e:
            self.logger.error(f"CQRS配置初始化失败: {e}")
            raise
    
    async def _register_cqrs_infrastructure(self) -> None:
        """注册CQRS基础设施"""
        self.logger.info("注册CQRS基础设施...")
        
        # 注册命令总线
        self.container.register_singleton(ICommandBus, CommandBus)
        self.container.register_singleton(CommandBus, CommandBus)
        
        # 注册查询总线
        self.container.register_singleton(IQueryBus, QueryBus)
        self.container.register_singleton(QueryBus, QueryBus)
        
        self.logger.info("CQRS基础设施注册完成")
    
    async def _auto_register_handlers(self, base_packages: List[str]) -> None:
        """自动注册处理器"""
        self.logger.info("开始自动注册CQRS处理器...")
        
        for package in base_packages:
            modules = self.discovery.discover_cqrs_modules(package)
            
            for module_info in modules:
                self.logger.info(f"处理模块: {module_info.name}")
                
                # 注册模块信息
                self.registry.register_module(module_info)
                
                # 注册处理器到DI容器
                await self._register_module_handlers(module_info)
        
        self.logger.info("CQRS处理器自动注册完成")
    
    async def _register_module_handlers(self, module_info: CQRSModuleInfo) -> None:
        """注册模块处理器到DI容器"""
        # 注册命令处理器
        for handler_type in module_info.command_handlers:
            self.container.register_transient(handler_type, handler_type)
            self.logger.debug(f"注册命令处理器: {handler_type.__name__}")
        
        # 注册查询处理器
        for handler_type in module_info.query_handlers:
            self.container.register_transient(handler_type, handler_type)
            self.logger.debug(f"注册查询处理器: {handler_type.__name__}")
    
    async def _configure_handler_mappings(self) -> None:
        """配置处理器映射"""
        self.logger.info("配置CQRS处理器映射...")
        
        # 获取总线实例
        command_bus = self.container.resolve(CommandBus)
        query_bus = self.container.resolve(QueryBus)
        
        # 配置命令处理器映射
        for command_type, handler_type in self.registry.get_all_command_handlers().items():
            handler_instance = self.container.resolve(handler_type)
            command_bus.register_handler(command_type, handler_instance)
        
        # 配置查询处理器映射
        for query_type, handler_type in self.registry.get_all_query_handlers().items():
            handler_instance = self.container.resolve(handler_type)
            query_bus.register_handler(query_type, handler_instance)
        
        self.logger.info("CQRS处理器映射配置完成")
    
    def register_command_handler(self, command_type: Type[Command], handler_type: Type[CommandHandler]) -> None:
        """手动注册命令处理器"""
        self.registry.register_command_handler(command_type, handler_type)
        self.container.register_transient(handler_type, handler_type)
    
    def register_query_handler(self, query_type: Type[Query], handler_type: Type[QueryHandler]) -> None:
        """手动注册查询处理器"""
        self.registry.register_query_handler(query_type, handler_type)
        self.container.register_transient(handler_type, handler_type)
    
    def get_command_bus(self) -> CommandBus:
        """获取命令总线"""
        return self.container.resolve(CommandBus)
    
    def get_query_bus(self) -> QueryBus:
        """获取查询总线"""
        return self.container.resolve(QueryBus)
    
    def get_registry_info(self) -> Dict[str, Any]:
        """获取注册表信息"""
        return {
            "command_handlers": {
                cmd.__name__: handler.__name__ 
                for cmd, handler in self.registry.get_all_command_handlers().items()
            },
            "query_handlers": {
                query.__name__: handler.__name__ 
                for query, handler in self.registry.get_all_query_handlers().items()
            },
            "registered_modules": list(self.registry.registered_modules.keys())
        }


# 全局CQRS配置管理器实例
_global_cqrs_manager: Optional[CQRSConfigurationManager] = None


def get_cqrs_manager() -> Optional[CQRSConfigurationManager]:
    """获取全局CQRS配置管理器"""
    return _global_cqrs_manager


def set_cqrs_manager(manager: CQRSConfigurationManager) -> None:
    """设置全局CQRS配置管理器"""
    global _global_cqrs_manager
    _global_cqrs_manager = manager


async def initialize_cqrs(container: DependencyContainer, auto_discover: bool = True) -> CQRSConfigurationManager:
    """初始化CQRS系统"""
    manager = CQRSConfigurationManager(container)
    await manager.initialize(auto_discover=auto_discover)
    set_cqrs_manager(manager)
    return manager
