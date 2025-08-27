"""
依赖注入助手
============

提供增强的依赖注入配置和管理功能，支持CQRS架构的自动化配置
"""

# 标准库导入
import asyncio
import inspect
import logging
from typing import Dict, Type, List, Any, Optional, Callable, TypeVar, get_type_hints
from abc import ABC, abstractmethod
from dataclasses import dataclass

# 核心层导入
from ...core.infrastructure.dependency_container import DependencyContainer, ServiceScope

# 应用层内部导入
from ..commands.command_bus import CommandHandler
from ..queries.query_bus import QueryHandler


logger = logging.getLogger(__name__)
T = TypeVar('T')


@dataclass
class ServiceRegistration:
    """服务注册信息"""
    service_type: Type
    implementation: Type
    scope: ServiceScope
    factory: Optional[Callable] = None
    dependencies: List[Type] = None
    configuration: Dict[str, Any] = None


class DependencyProfile:
    """依赖配置文件"""
    
    def __init__(self, name: str):
        self.name = name
        self.registrations: List[ServiceRegistration] = []
        self.configurations: Dict[str, Any] = {}
        self.initialization_order: List[Type] = []
    
    def add_singleton(self, service_type: Type[T], implementation: Type[T] = None, 
                     factory: Callable = None, **config) -> 'DependencyProfile':
        """添加单例服务"""
        self.registrations.append(ServiceRegistration(
            service_type=service_type,
            implementation=implementation or service_type,
            scope=ServiceScope.SINGLETON,
            factory=factory,
            configuration=config
        ))
        return self
    
    def add_transient(self, service_type: Type[T], implementation: Type[T] = None,
                     factory: Callable = None, **config) -> 'DependencyProfile':
        """添加瞬态服务"""
        self.registrations.append(ServiceRegistration(
            service_type=service_type,
            implementation=implementation or service_type,
            scope=ServiceScope.TRANSIENT,
            factory=factory,
            configuration=config
        ))
        return self
    
    def add_scoped(self, service_type: Type[T], implementation: Type[T] = None,
                  factory: Callable = None, **config) -> 'DependencyProfile':
        """添加作用域服务"""
        self.registrations.append(ServiceRegistration(
            service_type=service_type,
            implementation=implementation or service_type,
            scope=ServiceScope.SCOPED,
            factory=factory,
            configuration=config
        ))
        return self
    
    def configure(self, key: str, value: Any) -> 'DependencyProfile':
        """添加配置"""
        self.configurations[key] = value
        return self
    
    def set_initialization_order(self, types: List[Type]) -> 'DependencyProfile':
        """设置初始化顺序"""
        self.initialization_order = types
        return self


class DependencyInjectionHelper:
    """依赖注入助手"""
    
    def __init__(self, container: DependencyContainer):
        self.container = container
        self.profiles: Dict[str, DependencyProfile] = {}
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def create_profile(self, name: str) -> DependencyProfile:
        """创建依赖配置文件"""
        profile = DependencyProfile(name)
        self.profiles[name] = profile
        return profile
    
    async def apply_profile(self, profile_name: str) -> None:
        """应用依赖配置文件"""
        if profile_name not in self.profiles:
            raise ValueError(f"未找到配置文件: {profile_name}")
        
        profile = self.profiles[profile_name]
        self.logger.info(f"应用依赖配置文件: {profile_name}")
        
        # 应用配置
        for key, value in profile.configurations.items():
            self.logger.debug(f"配置: {key} = {value}")
        
        # 注册服务
        for registration in profile.registrations:
            await self._register_service(registration)
        
        self.logger.info(f"依赖配置文件 {profile_name} 应用完成")
    
    async def _register_service(self, registration: ServiceRegistration) -> None:
        """注册服务"""
        try:
            if registration.factory:
                # 使用工厂方法注册
                if registration.scope == ServiceScope.SINGLETON:
                    self.container.register_singleton_factory(
                        registration.service_type, 
                        registration.factory
                    )
                elif registration.scope == ServiceScope.TRANSIENT:
                    self.container.register_transient_factory(
                        registration.service_type,
                        registration.factory
                    )
                elif registration.scope == ServiceScope.SCOPED:
                    self.container.register_scoped_factory(
                        registration.service_type,
                        registration.factory
                    )
            else:
                # 使用类型注册
                if registration.scope == ServiceScope.SINGLETON:
                    self.container.register_singleton(
                        registration.service_type,
                        registration.implementation
                    )
                elif registration.scope == ServiceScope.TRANSIENT:
                    self.container.register_transient(
                        registration.service_type,
                        registration.implementation
                    )
                elif registration.scope == ServiceScope.SCOPED:
                    self.container.register_scoped(
                        registration.service_type,
                        registration.implementation
                    )
            
            self.logger.debug(
                f"注册服务: {registration.service_type.__name__} -> "
                f"{registration.implementation.__name__} ({registration.scope.value})"
            )
            
        except Exception as e:
            self.logger.error(f"注册服务失败: {registration.service_type.__name__} - {e}")
            raise
    
    def auto_register_handlers(self, module_path: str, 
                              handler_base_types: List[Type] = None) -> DependencyProfile:
        """自动注册处理器"""
        handler_base_types = handler_base_types or [CommandHandler, QueryHandler]
        
        profile = self.create_profile(f"auto_handlers_{module_path}")
        
        try:
            import importlib
            module = importlib.import_module(module_path)
            
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if (obj.__module__ == module_path and
                    any(issubclass(obj, base_type) for base_type in handler_base_types) and
                    obj not in handler_base_types):
                    
                    profile.add_transient(obj)
                    self.logger.debug(f"自动注册处理器: {obj.__name__}")
            
        except Exception as e:
            self.logger.error(f"自动注册处理器失败: {module_path} - {e}")
        
        return profile
    
    def validate_dependencies(self) -> Dict[str, List[str]]:
        """验证依赖关系"""
        issues = {}
        
        try:
            # 获取所有已注册的服务
            registered_services = self.container.get_registered_services()
            
            for service_type in registered_services:
                service_issues = []
                
                # 检查构造函数依赖
                try:
                    constructor = service_type.__init__
                    type_hints = get_type_hints(constructor)
                    
                    for param_name, param_type in type_hints.items():
                        if param_name != 'return' and param_name != 'self':
                            if not self.container.is_registered(param_type):
                                service_issues.append(f"未注册的依赖: {param_type.__name__}")
                
                except Exception as e:
                    service_issues.append(f"依赖分析失败: {e}")
                
                if service_issues:
                    issues[service_type.__name__] = service_issues
        
        except Exception as e:
            self.logger.error(f"依赖验证失败: {e}")
            issues["validation_error"] = [str(e)]
        
        return issues
    
    def get_dependency_graph(self) -> Dict[str, List[str]]:
        """获取依赖关系图"""
        graph = {}
        
        try:
            registered_services = self.container.get_registered_services()
            
            for service_type in registered_services:
                dependencies = []
                
                try:
                    constructor = service_type.__init__
                    type_hints = get_type_hints(constructor)
                    
                    for param_name, param_type in type_hints.items():
                        if param_name != 'return' and param_name != 'self':
                            if inspect.isclass(param_type):
                                dependencies.append(param_type.__name__)
                
                except Exception:
                    pass
                
                graph[service_type.__name__] = dependencies
        
        except Exception as e:
            self.logger.error(f"生成依赖图失败: {e}")
        
        return graph
    
    def create_application_profile(self) -> DependencyProfile:
        """创建标准应用层配置文件"""
        from ..commands.command_bus import ICommandBus, CommandBus
        from ..queries.query_bus import IQueryBus, QueryBus
        
        profile = self.create_profile("application_layer")
        
        # 注册CQRS基础设施
        profile.add_singleton(ICommandBus, CommandBus)
        profile.add_singleton(CommandBus)
        profile.add_singleton(IQueryBus, QueryBus)
        profile.add_singleton(QueryBus)
        
        return profile
    
    def create_infrastructure_profile(self) -> DependencyProfile:
        """创建基础设施层配置文件"""
        profile = self.create_profile("infrastructure_layer")
        
        # 在这里添加基础设施服务注册
        # 例如：数据库连接、缓存、日志等
        
        return profile


class DIConfiguration:
    """依赖注入配置类"""
    
    @staticmethod
    def configure_application_layer(helper: DependencyInjectionHelper) -> None:
        """配置应用层依赖注入"""
        logger.info("配置应用层依赖注入...")
        
        # 创建并应用应用层配置文件
        profile = helper.create_application_profile()
        
        # 可以在这里添加额外的应用层服务配置
        
        # 应用配置
        asyncio.create_task(helper.apply_profile("application_layer"))
        
        logger.info("应用层依赖注入配置完成")
    
    @staticmethod
    def configure_infrastructure_layer(helper: DependencyInjectionHelper) -> None:
        """配置基础设施层依赖注入"""
        logger.info("配置基础设施层依赖注入...")
        
        # 创建并应用基础设施层配置文件
        profile = helper.create_infrastructure_profile()
        
        # 应用配置
        asyncio.create_task(helper.apply_profile("infrastructure_layer"))
        
        logger.info("基础设施层依赖注入配置完成")


# 全局依赖注入助手实例
_global_di_helper: Optional[DependencyInjectionHelper] = None


def get_di_helper() -> Optional[DependencyInjectionHelper]:
    """获取全局依赖注入助手"""
    return _global_di_helper


def set_di_helper(helper: DependencyInjectionHelper) -> None:
    """设置全局依赖注入助手"""
    global _global_di_helper
    _global_di_helper = helper


def create_di_helper(container: DependencyContainer) -> DependencyInjectionHelper:
    """创建依赖注入助手"""
    helper = DependencyInjectionHelper(container)
    set_di_helper(helper)
    return helper
