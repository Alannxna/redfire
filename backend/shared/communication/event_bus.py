"""
事件驱动架构
===========

实现分布式事件总线和事件处理
"""

import json
import time
import uuid
import logging
import asyncio
from typing import Dict, List, Any, Optional, Callable, Set
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
import redis.asyncio as redis

logger = logging.getLogger(__name__)


class EventStatus(Enum):
    """事件状态"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


@dataclass
class DomainEvent:
    """领域事件"""
    event_id: str
    event_type: str
    aggregate_id: str
    aggregate_type: str
    payload: Dict[str, Any]
    timestamp: datetime
    version: int = 1
    correlation_id: Optional[str] = None
    causation_id: Optional[str] = None
    service_name: Optional[str] = None
    user_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def create(cls, event_type: str, aggregate_id: str, aggregate_type: str,
               payload: Dict[str, Any], **kwargs) -> "DomainEvent":
        """创建事件"""
        return cls(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            aggregate_id=aggregate_id,
            aggregate_type=aggregate_type,
            payload=payload,
            timestamp=datetime.utcnow(),
            **kwargs
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DomainEvent":
        """从字典创建"""
        data = data.copy()
        if 'timestamp' in data:
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


@dataclass
class EventHandler:
    """事件处理器"""
    handler_id: str
    event_type: str
    handler_func: Callable
    service_name: str
    retries: int = 3
    timeout: float = 30.0
    enabled: bool = True


@dataclass
class EventProcessingResult:
    """事件处理结果"""
    event_id: str
    handler_id: str
    status: EventStatus
    processing_time: float
    error_message: Optional[str] = None
    retry_count: int = 0


class EventStore:
    """事件存储"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.event_stream = "redfire:events"
        self.event_key_prefix = "redfire:event:"
    
    async def save_event(self, event: DomainEvent) -> bool:
        """保存事件"""
        try:
            # 保存到Redis Stream
            event_data = event.to_dict()
            await self.redis.xadd(
                self.event_stream,
                event_data,
                maxlen=1000000  # 保留最近100万个事件
            )
            
            # 保存事件详情
            event_key = f"{self.event_key_prefix}{event.event_id}"
            await self.redis.hset(event_key, mapping=event_data)
            await self.redis.expire(event_key, 86400 * 30)  # 30天过期
            
            logger.debug(f"事件已保存: {event.event_type}#{event.event_id}")
            return True
            
        except Exception as e:
            logger.error(f"保存事件失败 {event.event_id}: {e}")
            return False
    
    async def get_event(self, event_id: str) -> Optional[DomainEvent]:
        """获取事件"""
        try:
            event_key = f"{self.event_key_prefix}{event_id}"
            event_data = await self.redis.hgetall(event_key)
            
            if event_data:
                return DomainEvent.from_dict(event_data)
            return None
            
        except Exception as e:
            logger.error(f"获取事件失败 {event_id}: {e}")
            return None
    
    async def get_events_by_aggregate(self, aggregate_id: str, 
                                    aggregate_type: Optional[str] = None) -> List[DomainEvent]:
        """获取聚合根的所有事件"""
        try:
            # 从Stream中查询
            events = await self.redis.xrange(self.event_stream, count=10000)
            
            result = []
            for event_id, event_data in events:
                if event_data.get('aggregate_id') == aggregate_id:
                    if not aggregate_type or event_data.get('aggregate_type') == aggregate_type:
                        result.append(DomainEvent.from_dict(event_data))
            
            return sorted(result, key=lambda e: e.timestamp)
            
        except Exception as e:
            logger.error(f"获取聚合事件失败 {aggregate_id}: {e}")
            return []


class EventBus:
    """事件总线"""
    
    def __init__(self, redis_url: str, service_name: str):
        self.redis_url = redis_url
        self.service_name = service_name
        self.redis: Optional[redis.Redis] = None
        
        # 事件存储
        self.event_store: Optional[EventStore] = None
        
        # 事件处理器
        self.handlers: Dict[str, List[EventHandler]] = {}
        self.processing_events: Set[str] = set()
        
        # 统计信息
        self.published_events = 0
        self.processed_events = 0
        self.failed_events = 0
        
        # 后台任务
        self._consumer_task: Optional[asyncio.Task] = None
        self._retry_task: Optional[asyncio.Task] = None
    
    async def initialize(self):
        """初始化事件总线"""
        logger.info(f"初始化事件总线 - 服务: {self.service_name}")
        
        # 连接Redis
        self.redis = redis.from_url(self.redis_url, decode_responses=True)
        await self.redis.ping()
        
        # 初始化事件存储
        self.event_store = EventStore(self.redis)
        
        # 创建消费者组
        try:
            await self.redis.xgroup_create(
                "redfire:events",
                f"service_{self.service_name}",
                id='0',
                mkstream=True
            )
        except Exception:
            pass  # 组已存在
        
        # 启动事件消费者
        self._consumer_task = asyncio.create_task(self._event_consumer())
        self._retry_task = asyncio.create_task(self._retry_failed_events())
        
        logger.info("事件总线初始化完成")
    
    def register_handler(self, event_type: str, handler_func: Callable,
                        retries: int = 3, timeout: float = 30.0):
        """注册事件处理器"""
        handler = EventHandler(
            handler_id=f"{self.service_name}_{event_type}_{id(handler_func)}",
            event_type=event_type,
            handler_func=handler_func,
            service_name=self.service_name,
            retries=retries,
            timeout=timeout
        )
        
        if event_type not in self.handlers:
            self.handlers[event_type] = []
        
        self.handlers[event_type].append(handler)
        logger.info(f"注册事件处理器: {event_type} -> {handler.handler_id}")
    
    async def publish_event(self, event: DomainEvent) -> bool:
        """发布事件"""
        try:
            # 设置服务名称
            event.service_name = self.service_name
            
            # 保存事件
            if not await self.event_store.save_event(event):
                return False
            
            self.published_events += 1
            logger.info(f"事件已发布: {event.event_type}#{event.event_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"发布事件失败: {e}")
            return False
    
    async def publish_domain_event(self, event_type: str, aggregate_id: str,
                                 aggregate_type: str, payload: Dict[str, Any],
                                 **kwargs) -> Optional[str]:
        """发布领域事件（便捷方法）"""
        event = DomainEvent.create(
            event_type=event_type,
            aggregate_id=aggregate_id,
            aggregate_type=aggregate_type,
            payload=payload,
            **kwargs
        )
        
        if await self.publish_event(event):
            return event.event_id
        return None
    
    async def _event_consumer(self):
        """事件消费者"""
        consumer_name = f"{self.service_name}_{uuid.uuid4().hex[:8]}"
        
        while True:
            try:
                # 读取事件
                events = await self.redis.xreadgroup(
                    f"service_{self.service_name}",
                    consumer_name,
                    {"redfire:events": ">"},
                    count=10,
                    block=1000
                )
                
                for stream_name, event_list in events:
                    for event_id, event_data in event_list:
                        await self._process_event(event_id, event_data)
                        
            except Exception as e:
                logger.error(f"事件消费错误: {e}")
                await asyncio.sleep(1)
    
    async def _process_event(self, event_id: str, event_data: Dict[str, Any]):
        """处理事件"""
        try:
            # 解析事件
            event = DomainEvent.from_dict(event_data)
            
            # 跳过自己发布的事件（避免循环）
            if event.service_name == self.service_name:
                await self.redis.xack("redfire:events", f"service_{self.service_name}", event_id)
                return
            
            # 检查是否有处理器
            if event.event_type not in self.handlers:
                await self.redis.xack("redfire:events", f"service_{self.service_name}", event_id)
                return
            
            # 防止重复处理
            if event.event_id in self.processing_events:
                return
            
            self.processing_events.add(event.event_id)
            
            try:
                # 执行所有处理器
                handlers = self.handlers[event.event_type]
                for handler in handlers:
                    if handler.enabled:
                        await self._execute_handler(event, handler)
                
                # 确认消息处理完成
                await self.redis.xack("redfire:events", f"service_{self.service_name}", event_id)
                self.processed_events += 1
                
            finally:
                self.processing_events.discard(event.event_id)
                
        except Exception as e:
            logger.error(f"处理事件失败 {event_id}: {e}")
            self.failed_events += 1
    
    async def _execute_handler(self, event: DomainEvent, handler: EventHandler):
        """执行事件处理器"""
        start_time = time.time()
        
        try:
            # 设置超时
            await asyncio.wait_for(
                handler.handler_func(event),
                timeout=handler.timeout
            )
            
            processing_time = time.time() - start_time
            
            # 记录处理结果
            result = EventProcessingResult(
                event_id=event.event_id,
                handler_id=handler.handler_id,
                status=EventStatus.COMPLETED,
                processing_time=processing_time
            )
            
            await self._record_processing_result(result)
            
            logger.debug(f"事件处理成功: {handler.handler_id} -> {event.event_type}")
            
        except asyncio.TimeoutError:
            processing_time = time.time() - start_time
            error_msg = f"处理超时 ({processing_time:.2f}s)"
            
            await self._handle_processing_error(event, handler, error_msg)
            
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = str(e)
            
            await self._handle_processing_error(event, handler, error_msg)
    
    async def _handle_processing_error(self, event: DomainEvent, handler: EventHandler, error_msg: str):
        """处理处理错误"""
        logger.error(f"事件处理失败: {handler.handler_id} -> {event.event_type}: {error_msg}")
        
        # 记录失败结果
        result = EventProcessingResult(
            event_id=event.event_id,
            handler_id=handler.handler_id,
            status=EventStatus.FAILED,
            processing_time=0.0,
            error_message=error_msg
        )
        
        await self._record_processing_result(result)
        
        # TODO: 实现重试机制
    
    async def _record_processing_result(self, result: EventProcessingResult):
        """记录处理结果"""
        try:
            result_key = f"redfire:event_result:{result.event_id}:{result.handler_id}"
            result_data = asdict(result)
            result_data['status'] = result.status.value
            
            await self.redis.hset(result_key, mapping=result_data)
            await self.redis.expire(result_key, 86400 * 7)  # 7天过期
            
        except Exception as e:
            logger.error(f"记录处理结果失败: {e}")
    
    async def _retry_failed_events(self):
        """重试失败的事件"""
        while True:
            try:
                # TODO: 实现重试逻辑
                await asyncio.sleep(60)  # 每分钟检查一次
                
            except Exception as e:
                logger.error(f"重试任务错误: {e}")
                await asyncio.sleep(10)
    
    async def get_event_stats(self) -> Dict[str, Any]:
        """获取事件统计"""
        return {
            "service_name": self.service_name,
            "published_events": self.published_events,
            "processed_events": self.processed_events,
            "failed_events": self.failed_events,
            "registered_handlers": {
                event_type: len(handlers)
                for event_type, handlers in self.handlers.items()
            },
            "processing_events": len(self.processing_events)
        }
    
    async def close(self):
        """关闭事件总线"""
        logger.info("关闭事件总线...")
        
        # 停止后台任务
        if self._consumer_task:
            self._consumer_task.cancel()
        if self._retry_task:
            self._retry_task.cancel()
        
        # 关闭Redis连接
        if self.redis:
            await self.redis.close()
        
        logger.info("事件总线已关闭")


# 具体事件定义
class UserEvents:
    """用户相关事件"""
    
    USER_REGISTERED = "user.registered"
    USER_LOGIN = "user.login"
    USER_LOGOUT = "user.logout"
    USER_PROFILE_UPDATED = "user.profile_updated"


class TradingEvents:
    """交易相关事件"""
    
    ORDER_CREATED = "order.created"
    ORDER_FILLED = "order.filled"
    ORDER_CANCELLED = "order.cancelled"
    POSITION_OPENED = "position.opened"
    POSITION_CLOSED = "position.closed"


class StrategyEvents:
    """策略相关事件"""
    
    STRATEGY_STARTED = "strategy.started"
    STRATEGY_STOPPED = "strategy.stopped"
    STRATEGY_SIGNAL_GENERATED = "strategy.signal_generated"
    STRATEGY_ERROR = "strategy.error"


class DataEvents:
    """数据相关事件"""
    
    MARKET_DATA_RECEIVED = "data.market_data_received"
    PRICE_ALERT_TRIGGERED = "data.price_alert_triggered"
    DATA_QUALITY_ISSUE = "data.quality_issue"
