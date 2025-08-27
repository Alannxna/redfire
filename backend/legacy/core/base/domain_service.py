"""
领域服务基类
============

所有领域服务的基类，提供领域特有的功能和接口
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from .service_base import BaseService, ServiceConfig


@dataclass
class DomainServiceConfig(ServiceConfig):
    """领域服务配置"""
    domain_name: str = ""
    event_sourcing: bool = False
    cqrs_enabled: bool = False
    aggregate_roots: List[str] = None
    
    def __post_init__(self):
        if self.aggregate_roots is None:
            self.aggregate_roots = []


class BaseDomainService(BaseService, ABC):
    """
    领域服务基类
    
    提供领域驱动设计(DDD)相关的功能：
    - 聚合根管理
    - 领域事件处理
    - 事件溯源支持
    - CQRS模式支持
    """
    
    def __init__(self, config: DomainServiceConfig):
        super().__init__(config)
        self.domain_config = config
        
        # 领域事件相关
        self.domain_events: List[Dict[str, Any]] = []
        self.event_handlers: Dict[str, List] = {}
        
        # 聚合根注册表
        self.aggregate_registry: Dict[str, Any] = {}
        
        self.logger.info(f"领域服务 {config.domain_name} 初始化完成")
    
    async def publish_domain_event(self, event_type: str, event_data: Dict[str, Any]):
        """
        发布领域事件
        
        Args:
            event_type: 事件类型
            event_data: 事件数据
        """
        event = {
            "event_type": event_type,
            "event_data": event_data,
            "timestamp": self._get_current_timestamp(),
            "service_id": self.service_id,
            "domain": self.domain_config.domain_name
        }
        
        # 添加到事件列表
        self.domain_events.append(event)
        
        # 处理事件
        await self._handle_domain_event(event)
        
        self.logger.debug(f"发布领域事件: {event_type}")
    
    async def subscribe_to_domain_event(self, event_type: str, handler):
        """
        订阅领域事件
        
        Args:
            event_type: 事件类型
            handler: 事件处理器
        """
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        
        self.event_handlers[event_type].append(handler)
        self.logger.debug(f"订阅领域事件: {event_type}")
    
    async def register_aggregate_root(self, aggregate_type: str, aggregate_instance: Any):
        """
        注册聚合根
        
        Args:
            aggregate_type: 聚合类型
            aggregate_instance: 聚合实例
        """
        self.aggregate_registry[aggregate_type] = aggregate_instance
        self.logger.debug(f"注册聚合根: {aggregate_type}")
    
    def get_aggregate_root(self, aggregate_type: str) -> Optional[Any]:
        """
        获取聚合根
        
        Args:
            aggregate_type: 聚合类型
            
        Returns:
            聚合根实例或None
        """
        return self.aggregate_registry.get(aggregate_type)
    
    async def _handle_domain_event(self, event: Dict[str, Any]):
        """
        处理领域事件
        
        Args:
            event: 事件对象
        """
        event_type = event["event_type"]
        
        # 调用注册的事件处理器
        if event_type in self.event_handlers:
            for handler in self.event_handlers[event_type]:
                try:
                    await handler(event)
                except Exception as e:
                    self.logger.error(f"领域事件处理失败: {event_type}, 错误: {e}")
        
        # 调用子类的事件处理方法
        await self._process_domain_event(event)
    
    def _get_current_timestamp(self) -> str:
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    async def get_domain_metrics(self) -> Dict[str, Any]:
        """
        获取领域特定的监控指标
        
        Returns:
            Dict[str, Any]: 领域指标
        """
        return {
            "domain_name": self.domain_config.domain_name,
            "total_events": len(self.domain_events),
            "registered_aggregates": len(self.aggregate_registry),
            "event_types": list(set(event["event_type"] for event in self.domain_events)),
            "aggregate_types": list(self.aggregate_registry.keys())
        }
    
    async def _health_check_impl(self) -> Dict[str, Any]:
        """领域服务健康检查实现"""
        domain_metrics = await self.get_domain_metrics()
        
        return {
            "domain_healthy": True,
            "domain_metrics": domain_metrics,
            "event_sourcing_enabled": self.domain_config.event_sourcing,
            "cqrs_enabled": self.domain_config.cqrs_enabled
        }
    
    # 子类需要实现的抽象方法
    @abstractmethod
    async def _process_domain_event(self, event: Dict[str, Any]):
        """
        处理领域事件的具体实现
        
        Args:
            event: 事件对象
        """
        pass
    
    @abstractmethod
    async def get_domain_state(self) -> Dict[str, Any]:
        """
        获取领域状态
        
        Returns:
            Dict[str, Any]: 领域状态
        """
        pass
