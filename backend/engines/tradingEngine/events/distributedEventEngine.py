"""
分布式事件引擎

提供跨服务的事件传递和处理能力，支持微服务架构中的事件通信。
"""

import logging
import asyncio
import json
import time
from typing import Dict, List, Optional, Any, Callable, Set
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
from abc import ABC, abstractmethod

import redis.asyncio as redis


class EventDeliveryMode(Enum):
    """事件传递模式"""
    DIRECT = "direct"           # 直接传递
    FANOUT = "fanout"          # 广播
    TOPIC = "topic"            # 主题订阅
    QUEUE = "queue"            # 队列模式


class EventPriority(Enum):
    """事件优先级"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class DistributedEvent:
    """分布式事件"""
    event_id: str
    event_type: str
    source_service: str
    target_service: Optional[str] = None
    delivery_mode: EventDeliveryMode = EventDeliveryMode.FANOUT
    priority: EventPriority = EventPriority.NORMAL
    data: Dict[str, Any] = None
    timestamp: float = None
    expire_time: Optional[float] = None
    retry_count: int = 0
    max_retries: int = 3
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()
        if self.data is None:
            self.data = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data['delivery_mode'] = self.delivery_mode.value
        data['priority'] = self.priority.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DistributedEvent':
        """从字典创建"""
        if 'delivery_mode' in data:
            data['delivery_mode'] = EventDeliveryMode(data['delivery_mode'])
        if 'priority' in data:
            data['priority'] = EventPriority(data['priority'])
        return cls(**data)
    
    def is_expired(self) -> bool:
        """检查是否已过期"""
        if self.expire_time is None:
            return False
        return time.time() > self.expire_time
    
    def should_retry(self) -> bool:
        """检查是否应该重试"""
        return self.retry_count < self.max_retries


@dataclass
class EventHandler:
    """事件处理器"""
    handler_id: str
    handler_func: Callable
    event_types: List[str]
    service_name: str
    enabled: bool = True
    max_concurrent: int = 10
    timeout: float = 30.0
    retry_count: int = 3
    
    def matches_event(self, event: DistributedEvent) -> bool:
        """检查是否匹配事件"""
        if not self.enabled:
            return False
        
        # 检查事件类型
        if self.event_types and event.event_type not in self.event_types:
            return False
        
        # 检查目标服务
        if event.target_service and event.target_service != self.service_name:
            return False
        
        return True


class EventTransport(ABC):
    """事件传输抽象类"""
    
    @abstractmethod
    async def initialize(self):
        """初始化传输层"""
        pass
    
    @abstractmethod
    async def publish(self, event: DistributedEvent):
        """发布事件"""
        pass
    
    @abstractmethod
    async def subscribe(self, event_types: List[str], handler: Callable):
        """订阅事件"""
        pass
    
    @abstractmethod
    async def unsubscribe(self, event_types: List[str], handler: Callable):
        """取消订阅"""
        pass
    
    @abstractmethod
    async def close(self):
        """关闭传输层"""
        pass


class RedisEventTransport(EventTransport):
    """Redis事件传输实现"""
    
    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self.redis_client: Optional[redis.Redis] = None
        self.pubsub = None
        self.logger = logging.getLogger(__name__)
        
        # 订阅管理
        self.subscriptions: Dict[str, List[Callable]] = {}
        self.consumer_task: Optional[asyncio.Task] = None
        self.is_running = False
        
        # 统计信息
        self.published_count = 0
        self.consumed_count = 0
        self.error_count = 0
    
    async def initialize(self):
        """初始化Redis连接"""
        try:
            self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
            await self.redis_client.ping()
            
            self.pubsub = self.redis_client.pubsub()
            self.is_running = True
            
            # 启动消费者任务
            self.consumer_task = asyncio.create_task(self._consumer_loop())
            
            self.logger.info("Redis事件传输初始化完成")
            
        except Exception as e:
            self.logger.error(f"Redis事件传输初始化失败: {e}")
            raise
    
    async def publish(self, event: DistributedEvent):
        """发布事件到Redis"""
        try:
            if not self.redis_client:
                raise RuntimeError("Redis客户端未初始化")
            
            # 构建频道名
            if event.delivery_mode == EventDeliveryMode.DIRECT:
                channel = f"redfire:events:direct:{event.target_service}"
            elif event.delivery_mode == EventDeliveryMode.TOPIC:
                channel = f"redfire:events:topic:{event.event_type}"
            else:  # FANOUT
                channel = "redfire:events:fanout"
            
            # 序列化事件
            event_data = json.dumps(event.to_dict())
            
            # 发布到Redis
            await self.redis_client.publish(channel, event_data)
            
            # 同时存储到流中以确保可靠性
            stream_key = f"redfire:events:stream:{event.event_type}"
            await self.redis_client.xadd(
                stream_key,
                event.to_dict(),
                maxlen=10000  # 保留最近10000个事件
            )
            
            self.published_count += 1
            self.logger.debug(f"事件已发布: {event.event_id} -> {channel}")
            
        except Exception as e:
            self.error_count += 1
            self.logger.error(f"发布事件失败: {e}")
            raise
    
    async def subscribe(self, event_types: List[str], handler: Callable):
        """订阅事件类型"""
        try:
            for event_type in event_types:
                # 订阅不同的频道
                channels = [
                    "redfire:events:fanout",  # 广播频道
                    f"redfire:events:topic:{event_type}"  # 主题频道
                ]
                
                for channel in channels:
                    await self.pubsub.subscribe(channel)
                    
                    if event_type not in self.subscriptions:
                        self.subscriptions[event_type] = []
                    
                    if handler not in self.subscriptions[event_type]:
                        self.subscriptions[event_type].append(handler)
            
            self.logger.info(f"已订阅事件类型: {event_types}")
            
        except Exception as e:
            self.logger.error(f"订阅事件失败: {e}")
            raise
    
    async def unsubscribe(self, event_types: List[str], handler: Callable):
        """取消订阅事件类型"""
        try:
            for event_type in event_types:
                if event_type in self.subscriptions:
                    if handler in self.subscriptions[event_type]:
                        self.subscriptions[event_type].remove(handler)
                    
                    # 如果没有处理器了，取消频道订阅
                    if not self.subscriptions[event_type]:
                        channels = [
                            "redfire:events:fanout",
                            f"redfire:events:topic:{event_type}"
                        ]
                        
                        for channel in channels:
                            await self.pubsub.unsubscribe(channel)
                        
                        del self.subscriptions[event_type]
            
            self.logger.info(f"已取消订阅事件类型: {event_types}")
            
        except Exception as e:
            self.logger.error(f"取消订阅事件失败: {e}")
    
    async def _consumer_loop(self):
        """消费者循环"""
        self.logger.info("Redis事件消费者循环启动")
        
        try:
            while self.is_running:
                try:
                    # 获取消息
                    message = await self.pubsub.get_message(timeout=1.0)
                    
                    if message and message['type'] == 'message':
                        await self._process_message(message)
                        self.consumed_count += 1
                
                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    self.logger.error(f"处理消息异常: {e}")
                    self.error_count += 1
                    await asyncio.sleep(1)
        
        except Exception as e:
            self.logger.error(f"消费者循环异常: {e}")
        
        finally:
            self.logger.info("Redis事件消费者循环已停止")
    
    async def _process_message(self, message):
        """处理接收到的消息"""
        try:
            # 解析事件
            event_data = json.loads(message['data'])
            event = DistributedEvent.from_dict(event_data)
            
            # 检查是否过期
            if event.is_expired():
                self.logger.debug(f"事件已过期: {event.event_id}")
                return
            
            # 查找匹配的处理器
            handlers = self.subscriptions.get(event.event_type, [])
            
            # 并发执行处理器
            if handlers:
                tasks = [
                    asyncio.create_task(self._execute_handler(handler, event))
                    for handler in handlers
                ]
                await asyncio.gather(*tasks, return_exceptions=True)
        
        except Exception as e:
            self.logger.error(f"处理消息失败: {e}")
    
    async def _execute_handler(self, handler: Callable, event: DistributedEvent):
        """执行事件处理器"""
        try:
            if asyncio.iscoroutinefunction(handler):
                await handler(event)
            else:
                handler(event)
        
        except Exception as e:
            self.logger.error(f"执行事件处理器失败: {e}")
    
    async def close(self):
        """关闭Redis连接"""
        try:
            self.is_running = False
            
            if self.consumer_task:
                self.consumer_task.cancel()
                try:
                    await self.consumer_task
                except asyncio.CancelledError:
                    pass
            
            if self.pubsub:
                await self.pubsub.close()
            
            if self.redis_client:
                await self.redis_client.close()
            
            self.logger.info("Redis事件传输已关闭")
            
        except Exception as e:
            self.logger.error(f"关闭Redis事件传输失败: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            'published_count': self.published_count,
            'consumed_count': self.consumed_count,
            'error_count': self.error_count,
            'subscriptions': {
                event_type: len(handlers)
                for event_type, handlers in self.subscriptions.items()
            }
        }


class DistributedEventEngine:
    """
    分布式事件引擎
    
    支持跨服务的事件发布和订阅，提供可靠的事件传递机制。
    """
    
    def __init__(self, service_name: str, transport: EventTransport):
        self.service_name = service_name
        self.transport = transport
        self.logger = logging.getLogger(__name__)
        
        # 处理器管理
        self.handlers: Dict[str, EventHandler] = {}
        
        # 事件缓存（用于去重）
        self.processed_events: Set[str] = set()
        self.max_cache_size = 10000
        
        # 状态
        self.is_active = False
        self.start_time: Optional[float] = None
        
        # 统计信息
        self.stats = {
            'published_events': 0,
            'processed_events': 0,
            'failed_events': 0,
            'duplicate_events': 0
        }
        
        # 性能监控
        self.performance_monitor: Optional[asyncio.Task] = None
    
    async def initialize(self) -> bool:
        """初始化分布式事件引擎"""
        try:
            self.logger.info(f"初始化分布式事件引擎 - 服务: {self.service_name}")
            
            # 初始化传输层
            await self.transport.initialize()
            
            # 启动性能监控
            self.performance_monitor = asyncio.create_task(self._performance_monitor_loop())
            
            self.is_active = True
            self.start_time = time.time()
            
            self.logger.info("分布式事件引擎初始化完成")
            return True
            
        except Exception as e:
            self.logger.error(f"分布式事件引擎初始化失败: {e}")
            return False
    
    async def publish_event(self, event_type: str, data: Dict[str, Any],
                          target_service: Optional[str] = None,
                          delivery_mode: EventDeliveryMode = EventDeliveryMode.FANOUT,
                          priority: EventPriority = EventPriority.NORMAL,
                          expire_seconds: Optional[int] = None) -> str:
        """
        发布事件
        
        Args:
            event_type: 事件类型
            data: 事件数据
            target_service: 目标服务（可选）
            delivery_mode: 传递模式
            priority: 优先级
            expire_seconds: 过期时间（秒）
            
        Returns:
            str: 事件ID
        """
        try:
            # 创建事件
            event = DistributedEvent(
                event_id=str(uuid.uuid4()),
                event_type=event_type,
                source_service=self.service_name,
                target_service=target_service,
                delivery_mode=delivery_mode,
                priority=priority,
                data=data,
                expire_time=time.time() + expire_seconds if expire_seconds else None
            )
            
            # 发布事件
            await self.transport.publish(event)
            
            self.stats['published_events'] += 1
            self.logger.debug(f"事件已发布: {event.event_id} - {event_type}")
            
            return event.event_id
            
        except Exception as e:
            self.stats['failed_events'] += 1
            self.logger.error(f"发布事件失败: {e}")
            raise
    
    async def register_handler(self, handler_id: str, handler_func: Callable,
                             event_types: List[str], **kwargs) -> bool:
        """
        注册事件处理器
        
        Args:
            handler_id: 处理器ID
            handler_func: 处理函数
            event_types: 事件类型列表
            **kwargs: 其他配置参数
            
        Returns:
            bool: 注册是否成功
        """
        try:
            if handler_id in self.handlers:
                self.logger.warning(f"处理器已存在: {handler_id}")
                return False
            
            # 创建处理器
            handler = EventHandler(
                handler_id=handler_id,
                handler_func=handler_func,
                event_types=event_types,
                service_name=self.service_name,
                **kwargs
            )
            
            # 注册处理器
            self.handlers[handler_id] = handler
            
            # 订阅事件类型
            await self.transport.subscribe(event_types, self._handle_distributed_event)
            
            self.logger.info(f"事件处理器已注册: {handler_id} - {event_types}")
            return True
            
        except Exception as e:
            self.logger.error(f"注册事件处理器失败: {e}")
            return False
    
    async def unregister_handler(self, handler_id: str) -> bool:
        """
        注销事件处理器
        
        Args:
            handler_id: 处理器ID
            
        Returns:
            bool: 注销是否成功
        """
        try:
            if handler_id not in self.handlers:
                self.logger.warning(f"处理器不存在: {handler_id}")
                return False
            
            handler = self.handlers[handler_id]
            
            # 取消订阅
            await self.transport.unsubscribe(handler.event_types, self._handle_distributed_event)
            
            # 移除处理器
            del self.handlers[handler_id]
            
            self.logger.info(f"事件处理器已注销: {handler_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"注销事件处理器失败: {e}")
            return False
    
    async def _handle_distributed_event(self, event: DistributedEvent):
        """处理分布式事件"""
        try:
            # 检查是否已处理过（去重）
            if event.event_id in self.processed_events:
                self.stats['duplicate_events'] += 1
                return
            
            # 记录为已处理
            self.processed_events.add(event.event_id)
            
            # 清理缓存
            if len(self.processed_events) > self.max_cache_size:
                # 清理一半的缓存
                events_to_remove = list(self.processed_events)[:self.max_cache_size // 2]
                for event_id in events_to_remove:
                    self.processed_events.discard(event_id)
            
            # 查找匹配的处理器
            matching_handlers = [
                handler for handler in self.handlers.values()
                if handler.matches_event(event)
            ]
            
            # 执行处理器
            if matching_handlers:
                tasks = [
                    asyncio.create_task(self._execute_handler(handler, event))
                    for handler in matching_handlers
                ]
                await asyncio.gather(*tasks, return_exceptions=True)
            
            self.stats['processed_events'] += 1
            
        except Exception as e:
            self.stats['failed_events'] += 1
            self.logger.error(f"处理分布式事件失败: {e}")
    
    async def _execute_handler(self, handler: EventHandler, event: DistributedEvent):
        """执行事件处理器"""
        try:
            if asyncio.iscoroutinefunction(handler.handler_func):
                await asyncio.wait_for(
                    handler.handler_func(event),
                    timeout=handler.timeout
                )
            else:
                handler.handler_func(event)
                
        except asyncio.TimeoutError:
            self.logger.error(f"处理器执行超时: {handler.handler_id}")
        except Exception as e:
            self.logger.error(f"处理器执行异常: {handler.handler_id} - {e}")
    
    async def _performance_monitor_loop(self):
        """性能监控循环"""
        self.logger.info("分布式事件引擎性能监控启动")
        
        last_stats = self.stats.copy()
        
        try:
            while self.is_active:
                await asyncio.sleep(60)  # 每分钟监控一次
                
                # 计算性能指标
                current_stats = self.stats.copy()
                
                published_rate = current_stats['published_events'] - last_stats['published_events']
                processed_rate = current_stats['processed_events'] - last_stats['processed_events']
                
                self.logger.info(
                    f"事件引擎性能 - 发布: {published_rate}/min, "
                    f"处理: {processed_rate}/min, "
                    f"失败: {current_stats['failed_events']}, "
                    f"重复: {current_stats['duplicate_events']}"
                )
                
                last_stats = current_stats
        
        except Exception as e:
            self.logger.error(f"性能监控异常: {e}")
    
    async def close(self):
        """关闭分布式事件引擎"""
        try:
            self.logger.info("关闭分布式事件引擎...")
            
            self.is_active = False
            
            # 停止性能监控
            if self.performance_monitor:
                self.performance_monitor.cancel()
                try:
                    await self.performance_monitor
                except asyncio.CancelledError:
                    pass
            
            # 关闭传输层
            await self.transport.close()
            
            self.logger.info("分布式事件引擎已关闭")
            
        except Exception as e:
            self.logger.error(f"关闭分布式事件引擎失败: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """获取引擎状态"""
        return {
            'service_name': self.service_name,
            'is_active': self.is_active,
            'start_time': self.start_time,
            'uptime_seconds': time.time() - self.start_time if self.start_time else 0,
            'handlers_count': len(self.handlers),
            'processed_events_cache_size': len(self.processed_events),
            'stats': self.stats.copy(),
            'transport_stats': self.transport.get_stats() if hasattr(self.transport, 'get_stats') else {}
        }
