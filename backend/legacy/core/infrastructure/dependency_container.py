"""
依赖注入容器

实现IoC（控制反转）和DI（依赖注入）模式
支持单例、瞬态和作用域服务生命周期管理
"""

import asyncio
import logging
from typing import Type, TypeVar, Callable, Dict, Any, Optional, Union, get_type_hints
from enum import Enum
from abc import ABC, abstractmethod
import inspect
from functools import wraps

from ..common.exceptions import InfrastructureException


class ServiceScope(Enum):
    """服务生命周期作用域"""
    SINGLETON = "singleton"      # 单例 - 全局唯一实例
    TRANSIENT = "transient"      # 瞬态 - 每次请求创建新实例
    SCOPED = "scoped"           # 作用域 - 在特定作用域内单例


T = TypeVar('T')


class ServiceDescriptor:
    """服务描述符
    
    描述服务的注册信息，包括服务类型、实现类型、生命周期等
    """
    
    def __init__(self, service_type: Type, implementation: Union[Type, Callable], 
                 scope: ServiceScope = ServiceScope.TRANSIENT, 
                 factory: Optional[Callable] = None):
        self.service_type = service_type
        self.implementation = implementation
        self.scope = scope
        self.factory = factory
        self.instance = None  # 用于单例模式
        
    def __repr__(self):
        return f"ServiceDescriptor({self.service_type.__name__} -> {self.implementation.__name__}, {self.scope.value})"


class DependencyContainer:
    """依赖注入容器
    
    负责服务的注册、解析和生命周期管理
    支持构造函数注入、属性注入和方法注入
    """
    
    def __init__(self):
        self._services: Dict[Type, ServiceDescriptor] = {}
        self._singletons: Dict[Type, Any] = {}
        self._scoped_instances: Dict[str, Dict[Type, Any]] = {}
        self._current_scope: Optional[str] = None
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def register_singleton(self, service_type: Type[T], 
                          implementation: Union[Type[T], T, Callable[[], T]]) -> 'DependencyContainer':
        """注册单例服务
        
        Args:
            service_type: 服务接口类型
            implementation: 服务实现类、实例或工厂函数
            
        Returns:
            容器自身，支持链式调用
        """
        return self._register_service(service_type, implementation, ServiceScope.SINGLETON)
    
    def register_transient(self, service_type: Type[T], 
                          implementation: Union[Type[T], Callable[[], T]]) -> 'DependencyContainer':
        """注册瞬态服务
        
        Args:
            service_type: 服务接口类型
            implementation: 服务实现类或工厂函数
            
        Returns:
            容器自身，支持链式调用
        """
        return self._register_service(service_type, implementation, ServiceScope.TRANSIENT)
    
    def register_scoped(self, service_type: Type[T], 
                       implementation: Union[Type[T], Callable[[], T]]) -> 'DependencyContainer':
        """注册作用域服务
        
        Args:
            service_type: 服务接口类型
            implementation: 服务实现类或工厂函数
            
        Returns:
            容器自身，支持链式调用
        """
        return self._register_service(service_type, implementation, ServiceScope.SCOPED)
    
    def _register_service(self, service_type: Type, implementation: Union[Type, Any, Callable], 
                         scope: ServiceScope) -> 'DependencyContainer':
        """内部注册服务方法"""
        if service_type in self._services:
            self.logger.warning(f"服务已存在，将被覆盖: {service_type.__name__}")
        
        # 如果implementation是实例，直接注册为单例
        if not inspect.isclass(implementation) and not callable(implementation):
            self._singletons[service_type] = implementation
            descriptor = ServiceDescriptor(service_type, type(implementation), ServiceScope.SINGLETON)
        else:
            descriptor = ServiceDescriptor(service_type, implementation, scope)
        
        self._services[service_type] = descriptor
        self.logger.info(f"注册服务: {descriptor}")
        
        return self
    
    def register_factory(self, service_type: Type[T], 
                        factory: Callable[['DependencyContainer'], T],
                        scope: ServiceScope = ServiceScope.TRANSIENT) -> 'DependencyContainer':
        """注册工厂函数
        
        Args:
            service_type: 服务类型
            factory: 工厂函数，接收容器作为参数
            scope: 服务生命周期
            
        Returns:
            容器自身
        """
        descriptor = ServiceDescriptor(service_type, factory, scope, factory)
        self._services[service_type] = descriptor
        self.logger.info(f"注册工厂: {service_type.__name__} -> factory function")
        
        return self
    
    def resolve(self, service_type: Type[T]) -> T:
        """解析服务实例
        
        Args:
            service_type: 服务类型
            
        Returns:
            服务实例
            
        Raises:
            InfrastructureException: 服务未注册或创建失败
        """
        if service_type not in self._services:
            raise InfrastructureException(f"服务未注册: {service_type.__name__}")
        
        descriptor = self._services[service_type]
        
        # 单例模式
        if descriptor.scope == ServiceScope.SINGLETON:
            if service_type in self._singletons:
                return self._singletons[service_type]
            
            instance = self._create_instance(descriptor)
            self._singletons[service_type] = instance
            return instance
        
        # 作用域模式
        elif descriptor.scope == ServiceScope.SCOPED:
            if not self._current_scope:
                raise InfrastructureException("当前无活动作用域")
            
            scope_instances = self._scoped_instances.get(self._current_scope, {})
            if service_type in scope_instances:
                return scope_instances[service_type]
            
            instance = self._create_instance(descriptor)
            scope_instances[service_type] = instance
            self._scoped_instances[self._current_scope] = scope_instances
            return instance
        
        # 瞬态模式
        else:
            return self._create_instance(descriptor)
    
    def _create_instance(self, descriptor: ServiceDescriptor) -> Any:
        """创建服务实例"""
        try:
            # 使用工厂函数
            if descriptor.factory:
                return descriptor.factory(self)
            
            # 使用实现类
            implementation = descriptor.implementation
            if inspect.isclass(implementation):
                return self._create_class_instance(implementation)
            elif callable(implementation):
                return implementation()
            else:
                return implementation
                
        except Exception as e:
            raise InfrastructureException(
                f"创建服务实例失败: {descriptor.service_type.__name__} - {str(e)}"
            ) from e
    
    def _create_class_instance(self, cls: Type) -> Any:
        """通过构造函数注入创建类实例"""
        # 获取构造函数参数
        init_signature = inspect.signature(cls.__init__)
        parameters = {}
        
        for param_name, param in init_signature.parameters.items():
            if param_name == 'self':
                continue
                
            # 获取参数类型
            param_type = param.annotation
            if param_type == inspect.Parameter.empty:
                # 尝试从类型提示获取
                type_hints = get_type_hints(cls.__init__)
                param_type = type_hints.get(param_name)
            
            if param_type and param_type != inspect.Parameter.empty:
                try:
                    # 递归解析依赖
                    parameters[param_name] = self.resolve(param_type)
                except InfrastructureException:
                    # 如果依赖解析失败，检查是否有默认值
                    if param.default != inspect.Parameter.empty:
                        parameters[param_name] = param.default
                    elif param.default is None:
                        parameters[param_name] = None
                    else:
                        raise
        
        return cls(**parameters)
    
    def create_scope(self, scope_id: Optional[str] = None) -> 'ServiceScope':
        """创建服务作用域
        
        Args:
            scope_id: 作用域ID，如果不提供则自动生成
            
        Returns:
            作用域管理器
        """
        if scope_id is None:
            scope_id = f"scope_{id(object())}"
        
        return ServiceScopeManager(self, scope_id)
    
    def _enter_scope(self, scope_id: str) -> None:
        """进入作用域"""
        self._current_scope = scope_id
        if scope_id not in self._scoped_instances:
            self._scoped_instances[scope_id] = {}
        self.logger.debug(f"进入作用域: {scope_id}")
    
    def _exit_scope(self, scope_id: str) -> None:
        """退出作用域"""
        if scope_id in self._scoped_instances:
            # 清理作用域内的服务实例
            scope_instances = self._scoped_instances.pop(scope_id)
            for instance in scope_instances.values():
                if hasattr(instance, 'dispose'):
                    try:
                        instance.dispose()
                    except Exception as e:
                        self.logger.warning(f"清理服务实例失败: {e}")
        
        self._current_scope = None
        self.logger.debug(f"退出作用域: {scope_id}")
    
    def is_registered(self, service_type: Type) -> bool:
        """检查服务是否已注册"""
        return service_type in self._services
    
    def get_registered_services(self) -> Dict[str, str]:
        """获取已注册的服务列表"""
        return {
            service_type.__name__: f"{descriptor.implementation.__name__} ({descriptor.scope.value})"
            for service_type, descriptor in self._services.items()
        }
    
    def dispose(self) -> None:
        """释放容器资源"""
        # 清理单例实例
        for instance in self._singletons.values():
            if hasattr(instance, 'dispose'):
                try:
                    instance.dispose()
                except Exception as e:
                    self.logger.warning(f"清理单例实例失败: {e}")
        
        # 清理所有作用域
        for scope_id in list(self._scoped_instances.keys()):
            self._exit_scope(scope_id)
        
        self._services.clear()
        self._singletons.clear()
        self._scoped_instances.clear()
        
        self.logger.info("依赖注入容器已释放")


class ServiceScopeManager:
    """服务作用域管理器
    
    用于with语句，自动管理作用域的进入和退出
    """
    
    def __init__(self, container: DependencyContainer, scope_id: str):
        self.container = container
        self.scope_id = scope_id
    
    def __enter__(self):
        self.container._enter_scope(self.scope_id)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.container._exit_scope(self.scope_id)


def inject(service_type: Type[T]) -> Callable[[Callable], Callable]:
    """依赖注入装饰器
    
    自动为函数或方法注入指定类型的服务
    
    Args:
        service_type: 要注入的服务类型
        
    Returns:
        装饰器函数
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 从全局容器解析服务
            if hasattr(wrapper, '_container'):
                service = wrapper._container.resolve(service_type)
                return func(service, *args, **kwargs)
            else:
                raise InfrastructureException("未设置依赖注入容器")
        
        return wrapper
    return decorator


# 全局依赖注入容器实例
_global_container = DependencyContainer()


def get_container() -> DependencyContainer:
    """获取全局依赖注入容器"""
    return _global_container


def set_container(container: DependencyContainer) -> None:
    """设置全局依赖注入容器"""
    global _global_container
    _global_container = container
