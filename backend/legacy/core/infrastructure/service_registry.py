"""
服务注册中心

统一管理所有基础设施服务的生命周期
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Type
from dataclasses import dataclass, field
from enum import Enum

from ..base.infrastructure_service import BaseInfrastructureService
from ..common.exceptions import InfrastructureException
from .dependency_container import DependencyContainer
from .config_manager import InfraConfigManager
from .cache_manager import CacheManager  
from .monitoring import MonitorService, MonitorServiceConfig
from .logging import LogManager


class ServicePriority(Enum):
    """服务启动优先级"""
    CRITICAL = 1    # 关键服务，如配置管理、日志
    HIGH = 2        # 高优先级，如依赖注入、缓存
    NORMAL = 3      # 普通优先级，如监控
    LOW = 4         # 低优先级


@dataclass
class ServiceDescriptor:
    """服务描述符"""
    service_type: Type[BaseInfrastructureService]
    instance: Optional[BaseInfrastructureService] = None
    priority: ServicePriority = ServicePriority.NORMAL
    auto_start: bool = True
    dependencies: List[str] = field(default_factory=list)
    config: Optional[Any] = None


class ServiceRegistry:
    """服务注册中心
    
    管理所有基础设施服务的注册、启动、停止和依赖关系
    """
    
    def __init__(self):
        self.services: Dict[str, ServiceDescriptor] = {}
        self.running_services: Dict[str, BaseInfrastructureService] = {}
        self.logger = logging.getLogger(self.__class__.__name__)
        self._startup_order: List[str] = []
        
        # 注册核心基础设施服务
        self._register_core_services()
    
    def _register_core_services(self):
        """注册核心基础设施服务"""
        # 注册日志管理器（最高优先级）
        self.register_service(
            "log_manager",
            LogManager,
            priority=ServicePriority.CRITICAL,
            auto_start=True
        )
        
        # 注册配置管理器
        self.register_service(
            "config_manager", 
            InfraConfigManager,
            priority=ServicePriority.CRITICAL,
            auto_start=True
        )
        
        # 注册依赖注入容器
        self.register_service(
            "dependency_container",
            DependencyContainer,
            priority=ServicePriority.HIGH,
            auto_start=True
        )
        
        # 注册缓存管理器
        self.register_service(
            "cache_manager",
            CacheManager,
            priority=ServicePriority.HIGH,
            auto_start=True
        )
        
        # 注册监控服务
        self.register_service(
            "monitor_service",
            MonitorService,
            priority=ServicePriority.NORMAL,
            auto_start=True,
            config=MonitorServiceConfig(
                service_name="monitor_service",
                description="系统监控服务"
            )
        )
    
    def register_service(self, service_name: str, service_type: Type[BaseInfrastructureService],
                        priority: ServicePriority = ServicePriority.NORMAL,
                        auto_start: bool = True, dependencies: List[str] = None,
                        config: Any = None):
        """注册服务
        
        Args:
            service_name: 服务名称
            service_type: 服务类型
            priority: 启动优先级
            auto_start: 是否自动启动
            dependencies: 依赖的服务列表
            config: 服务配置
        """
        descriptor = ServiceDescriptor(
            service_type=service_type,
            priority=priority,
            auto_start=auto_start,
            dependencies=dependencies or [],
            config=config
        )
        
        self.services[service_name] = descriptor
        self.logger.info(f"注册服务: {service_name} ({service_type.__name__})")
    
    def get_service(self, service_name: str) -> Optional[BaseInfrastructureService]:
        """获取服务实例"""
        return self.running_services.get(service_name)
    
    def is_service_running(self, service_name: str) -> bool:
        """检查服务是否运行中"""
        service = self.running_services.get(service_name)
        return service is not None and service.is_running
    
    async def start_all_services(self) -> bool:
        """启动所有自动启动的服务"""
        try:
            self.logger.info("开始启动所有基础设施服务")
            
            # 计算启动顺序
            self._calculate_startup_order()
            
            # 按顺序启动服务
            for service_name in self._startup_order:
                descriptor = self.services[service_name]
                if descriptor.auto_start:
                    success = await self.start_service(service_name)
                    if not success:
                        self.logger.error(f"启动服务失败: {service_name}")
                        return False
            
            self.logger.info("所有基础设施服务启动完成")
            return True
            
        except Exception as e:
            self.logger.error(f"启动服务失败: {e}")
            return False
    
    async def stop_all_services(self):
        """停止所有运行中的服务"""
        try:
            self.logger.info("开始停止所有基础设施服务")
            
            # 按启动顺序的逆序停止服务
            for service_name in reversed(self._startup_order):
                if service_name in self.running_services:
                    await self.stop_service(service_name)
            
            self.logger.info("所有基础设施服务已停止")
            
        except Exception as e:
            self.logger.error(f"停止服务失败: {e}")
    
    async def start_service(self, service_name: str) -> bool:
        """启动单个服务"""
        if service_name not in self.services:
            self.logger.error(f"服务未注册: {service_name}")
            return False
        
        if service_name in self.running_services:
            self.logger.warning(f"服务已在运行: {service_name}")
            return True
        
        descriptor = self.services[service_name]
        
        try:
            # 检查依赖服务
            for dep_service in descriptor.dependencies:
                if not self.is_service_running(dep_service):
                    self.logger.error(f"依赖服务未运行: {dep_service}")
                    return False
            
            # 创建服务实例
            if descriptor.config:
                service_instance = descriptor.service_type(descriptor.config)
            else:
                # 为没有配置的服务创建默认配置
                service_instance = descriptor.service_type()
            
            # 启动服务
            success = await service_instance.start()
            if success:
                descriptor.instance = service_instance
                self.running_services[service_name] = service_instance
                self.logger.info(f"服务启动成功: {service_name}")
                return True
            else:
                self.logger.error(f"服务启动失败: {service_name}")
                return False
                
        except Exception as e:
            self.logger.error(f"启动服务异常 {service_name}: {e}")
            return False
    
    async def stop_service(self, service_name: str) -> bool:
        """停止单个服务"""
        if service_name not in self.running_services:
            self.logger.warning(f"服务未运行: {service_name}")
            return True
        
        try:
            service_instance = self.running_services[service_name]
            success = await service_instance.stop()
            
            if success:
                del self.running_services[service_name]
                descriptor = self.services[service_name]
                descriptor.instance = None
                self.logger.info(f"服务停止成功: {service_name}")
                return True
            else:
                self.logger.error(f"服务停止失败: {service_name}")
                return False
                
        except Exception as e:
            self.logger.error(f"停止服务异常 {service_name}: {e}")
            return False
    
    async def restart_service(self, service_name: str) -> bool:
        """重启服务"""
        self.logger.info(f"重启服务: {service_name}")
        
        # 先停止
        await self.stop_service(service_name)
        
        # 等待一下
        await asyncio.sleep(1)
        
        # 再启动
        return await self.start_service(service_name)
    
    def _calculate_startup_order(self):
        """计算服务启动顺序"""
        # 按优先级和依赖关系排序
        services_to_sort = [(name, desc) for name, desc in self.services.items() if desc.auto_start]
        
        # 拓扑排序处理依赖关系
        visited = set()
        temp_visited = set()
        order = []
        
        def visit(service_name: str, descriptor: ServiceDescriptor):
            if service_name in temp_visited:
                raise InfrastructureException(f"检测到循环依赖: {service_name}")
            
            if service_name in visited:
                return
            
            temp_visited.add(service_name)
            
            # 先访问依赖服务
            for dep_name in descriptor.dependencies:
                if dep_name in self.services:
                    dep_desc = self.services[dep_name]
                    visit(dep_name, dep_desc)
            
            temp_visited.remove(service_name)
            visited.add(service_name)
            order.append(service_name)
        
        # 按优先级分组
        priority_groups = {}
        for name, desc in services_to_sort:
            priority = desc.priority.value
            if priority not in priority_groups:
                priority_groups[priority] = []
            priority_groups[priority].append((name, desc))
        
        # 按优先级顺序处理
        final_order = []
        for priority in sorted(priority_groups.keys()):
            group_order = []
            group_visited = set()
            
            for service_name, descriptor in priority_groups[priority]:
                if service_name not in group_visited:
                    group_temp_visited = set()
                    
                    def group_visit(name: str, desc: ServiceDescriptor):
                        if name in group_temp_visited:
                            raise InfrastructureException(f"检测到循环依赖: {name}")
                        
                        if name in group_visited:
                            return
                        
                        group_temp_visited.add(name)
                        
                        # 处理同优先级内的依赖
                        for dep_name in desc.dependencies:
                            if dep_name in [n for n, d in priority_groups[priority]]:
                                dep_desc = self.services[dep_name]
                                group_visit(dep_name, dep_desc)
                        
                        group_temp_visited.remove(name)
                        group_visited.add(name)
                        group_order.append(name)
                    
                    group_visit(service_name, descriptor)
            
            final_order.extend(group_order)
        
        self._startup_order = final_order
        self.logger.info(f"服务启动顺序: {' -> '.join(self._startup_order)}")
    
    def get_service_status(self) -> Dict[str, Any]:
        """获取所有服务状态"""
        status = {
            "registered_services": len(self.services),
            "running_services": len(self.running_services),
            "startup_order": self._startup_order,
            "services": {}
        }
        
        for service_name, descriptor in self.services.items():
            service_status = {
                "type": descriptor.service_type.__name__,
                "priority": descriptor.priority.value,
                "auto_start": descriptor.auto_start,
                "dependencies": descriptor.dependencies,
                "running": service_name in self.running_services
            }
            
            if descriptor.instance:
                try:
                    service_status.update(descriptor.instance.get_status_info())
                except Exception as e:
                    service_status["status_error"] = str(e)
            
            status["services"][service_name] = service_status
        
        return status
    
    async def health_check_all(self) -> Dict[str, Any]:
        """对所有服务进行健康检查"""
        health_status = {
            "overall_healthy": True,
            "services": {}
        }
        
        for service_name, service_instance in self.running_services.items():
            try:
                service_health = await service_instance.health_check()
                health_status["services"][service_name] = service_health
                
                if not service_health.get("healthy", False):
                    health_status["overall_healthy"] = False
                    
            except Exception as e:
                health_status["services"][service_name] = {
                    "healthy": False,
                    "error": str(e)
                }
                health_status["overall_healthy"] = False
        
        return health_status


# 全局服务注册中心实例
_global_service_registry: Optional[ServiceRegistry] = None


def get_service_registry() -> ServiceRegistry:
    """获取全局服务注册中心"""
    global _global_service_registry
    if _global_service_registry is None:
        _global_service_registry = ServiceRegistry()
    return _global_service_registry


async def start_infrastructure_services() -> bool:
    """启动所有基础设施服务"""
    registry = get_service_registry()
    return await registry.start_all_services()


async def stop_infrastructure_services():
    """停止所有基础设施服务"""
    registry = get_service_registry()
    await registry.stop_all_services()


def get_infrastructure_service(service_name: str) -> Optional[BaseInfrastructureService]:
    """获取基础设施服务实例"""
    registry = get_service_registry()
    return registry.get_service(service_name)
