"""
Kafka Message Queue Service
===========================

Kafka消息队列服务，提供生产者、消费者、主题管理等功能。
支持消息路由、分区策略、批量处理、错误处理等高级特性。
"""

import logging
import json
import asyncio
import time
from typing import Any, Dict, List, Optional, Callable, Union, Tuple
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import threading
from concurrent.futures import ThreadPoolExecutor

try:
    from kafka import KafkaProducer, KafkaConsumer, KafkaAdminClient
    from kafka.admin import ConfigResource, ConfigResourceType, NewTopic
    from kafka.errors import KafkaError, TopicAlreadyExistsError
    KAFKA_AVAILABLE = True
except ImportError:
    KAFKA_AVAILABLE = False

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """消息类型"""
    MARKET_DATA = "MARKET_DATA"
    TRADE_ORDER = "TRADE_ORDER"
    POSITION_UPDATE = "POSITION_UPDATE"
    RISK_ALERT = "RISK_ALERT"
    SETTLEMENT = "SETTLEMENT"
    SYSTEM_EVENT = "SYSTEM_EVENT"


class CompressionType(Enum):
    """压缩类型"""
    NONE = "none"
    GZIP = "gzip"
    SNAPPY = "snappy"
    LZ4 = "lz4"
    ZSTD = "zstd"


@dataclass
class Message:
    """消息数据结构"""
    key: Optional[str] = None
    value: Any = None
    headers: Optional[Dict[str, str]] = None
    partition: Optional[int] = None
    offset: Optional[int] = None
    timestamp: Optional[datetime] = None
    message_type: Optional[MessageType] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "key": self.key,
            "value": self.value,
            "headers": self.headers,
            "partition": self.partition,
            "offset": self.offset,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "message_type": self.message_type.value if self.message_type else None
        }


@dataclass
class TopicConfig:
    """主题配置"""
    name: str
    num_partitions: int = 3
    replication_factor: int = 1
    retention_ms: int = 86400000  # 24小时
    compression_type: CompressionType = CompressionType.GZIP
    cleanup_policy: str = "delete"  # delete 或 compact
    min_insync_replicas: int = 1
    
    def to_kafka_config(self) -> Dict[str, str]:
        """转换为Kafka配置"""
        return {
            "retention.ms": str(self.retention_ms),
            "compression.type": self.compression_type.value,
            "cleanup.policy": self.cleanup_policy,
            "min.insync.replicas": str(self.min_insync_replicas)
        }


@dataclass
class ProducerStats:
    """生产者统计"""
    messages_sent: int = 0
    messages_failed: int = 0
    bytes_sent: int = 0
    last_send_time: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "messages_sent": self.messages_sent,
            "messages_failed": self.messages_failed,
            "bytes_sent": self.bytes_sent,
            "last_send_time": self.last_send_time.isoformat() if self.last_send_time else None
        }


@dataclass
class ConsumerStats:
    """消费者统计"""
    messages_consumed: int = 0
    messages_processed: int = 0
    messages_failed: int = 0
    last_consume_time: Optional[datetime] = None
    lag: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "messages_consumed": self.messages_consumed,
            "messages_processed": self.messages_processed,
            "messages_failed": self.messages_failed,
            "last_consume_time": self.last_consume_time.isoformat() if self.last_consume_time else None,
            "lag": self.lag
        }


class KafkaProducerService:
    """Kafka生产者服务"""
    
    def __init__(
        self,
        bootstrap_servers: List[str],
        client_id: str = "redfire_producer",
        compression_type: CompressionType = CompressionType.GZIP,
        batch_size: int = 16384,
        linger_ms: int = 5,
        retries: int = 3,
        acks: str = "1"
    ):
        self.bootstrap_servers = bootstrap_servers
        self.client_id = client_id
        self.compression_type = compression_type
        self.batch_size = batch_size
        self.linger_ms = linger_ms
        self.retries = retries
        self.acks = acks
        
        self._producer: Optional[KafkaProducer] = None
        self._stats = ProducerStats()
        self._is_running = False
        
        if not KAFKA_AVAILABLE:
            logger.warning("Kafka未安装，生产者服务将被禁用")
    
    async def start(self) -> bool:
        """启动生产者"""
        if not KAFKA_AVAILABLE:
            return False
        
        try:
            self._producer = KafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                client_id=self.client_id,
                compression_type=self.compression_type.value,
                batch_size=self.batch_size,
                linger_ms=self.linger_ms,
                retries=self.retries,
                acks=self.acks,
                value_serializer=lambda x: json.dumps(x, default=str).encode('utf-8'),
                key_serializer=lambda x: x.encode('utf-8') if x else None
            )
            
            self._is_running = True
            logger.info("Kafka生产者启动成功")
            return True
            
        except Exception as e:
            logger.error(f"Kafka生产者启动失败: {e}")
            return False
    
    async def stop(self) -> None:
        """停止生产者"""
        try:
            if self._producer:
                self._producer.close(timeout=10)
                self._producer = None
            
            self._is_running = False
            logger.info("Kafka生产者已停止")
            
        except Exception as e:
            logger.error(f"Kafka生产者停止失败: {e}")
    
    async def send_message(
        self,
        topic: str,
        message: Union[Message, Dict[str, Any]],
        partition: Optional[int] = None,
        timeout: int = 30
    ) -> bool:
        """发送消息"""
        if not self._producer or not self._is_running:
            logger.error("生产者未启动")
            return False
        
        try:
            # 处理消息格式
            if isinstance(message, Message):
                key = message.key
                value = message.value
                headers = message.headers
                partition = partition or message.partition
            else:
                key = message.get("key")
                value = message.get("value")
                headers = message.get("headers")
            
            # 发送消息
            future = self._producer.send(
                topic=topic,
                key=key,
                value=value,
                partition=partition,
                headers=headers
            )
            
            # 等待发送完成
            record_metadata = future.get(timeout=timeout)
            
            # 更新统计
            self._stats.messages_sent += 1
            self._stats.bytes_sent += len(json.dumps(value, default=str).encode('utf-8'))
            self._stats.last_send_time = datetime.now()
            
            logger.debug(f"消息发送成功: {topic}:{record_metadata.partition}:{record_metadata.offset}")
            return True
            
        except Exception as e:
            logger.error(f"消息发送失败: {e}")
            self._stats.messages_failed += 1
            return False
    
    async def send_batch(
        self,
        topic: str,
        messages: List[Union[Message, Dict[str, Any]]],
        timeout: int = 60
    ) -> Tuple[int, int]:
        """批量发送消息"""
        if not self._producer or not self._is_running:
            logger.error("生产者未启动")
            return 0, len(messages)
        
        success_count = 0
        failed_count = 0
        
        try:
            futures = []
            
            # 发送所有消息
            for message in messages:
                try:
                    if isinstance(message, Message):
                        key = message.key
                        value = message.value
                        headers = message.headers
                        partition = message.partition
                    else:
                        key = message.get("key")
                        value = message.get("value")
                        headers = message.get("headers")
                        partition = message.get("partition")
                    
                    future = self._producer.send(
                        topic=topic,
                        key=key,
                        value=value,
                        partition=partition,
                        headers=headers
                    )
                    futures.append(future)
                    
                except Exception as e:
                    logger.error(f"批量发送单条消息失败: {e}")
                    failed_count += 1
            
            # 等待所有消息发送完成
            for future in futures:
                try:
                    future.get(timeout=timeout)
                    success_count += 1
                except Exception as e:
                    logger.error(f"批量发送等待失败: {e}")
                    failed_count += 1
            
            # 更新统计
            self._stats.messages_sent += success_count
            self._stats.messages_failed += failed_count
            self._stats.last_send_time = datetime.now()
            
            logger.info(f"批量发送完成: 成功 {success_count}, 失败 {failed_count}")
            return success_count, failed_count
            
        except Exception as e:
            logger.error(f"批量发送失败: {e}")
            return success_count, len(messages) - success_count
    
    def get_stats(self) -> ProducerStats:
        """获取统计信息"""
        return self._stats
    
    def reset_stats(self) -> None:
        """重置统计信息"""
        self._stats = ProducerStats()


class KafkaConsumerService:
    """Kafka消费者服务"""
    
    def __init__(
        self,
        bootstrap_servers: List[str],
        group_id: str,
        topics: List[str],
        client_id: str = "redfire_consumer",
        auto_offset_reset: str = "latest",
        enable_auto_commit: bool = True,
        auto_commit_interval_ms: int = 1000,
        max_poll_records: int = 500,
        max_poll_interval_ms: int = 300000
    ):
        self.bootstrap_servers = bootstrap_servers
        self.group_id = group_id
        self.topics = topics
        self.client_id = client_id
        self.auto_offset_reset = auto_offset_reset
        self.enable_auto_commit = enable_auto_commit
        self.auto_commit_interval_ms = auto_commit_interval_ms
        self.max_poll_records = max_poll_records
        self.max_poll_interval_ms = max_poll_interval_ms
        
        self._consumer: Optional[KafkaConsumer] = None
        self._stats = ConsumerStats()
        self._message_handlers: Dict[str, Callable] = {}
        self._is_running = False
        self._consume_thread: Optional[threading.Thread] = None
        self._executor = ThreadPoolExecutor(max_workers=10)
        
        if not KAFKA_AVAILABLE:
            logger.warning("Kafka未安装，消费者服务将被禁用")
    
    async def start(self) -> bool:
        """启动消费者"""
        if not KAFKA_AVAILABLE:
            return False
        
        try:
            self._consumer = KafkaConsumer(
                *self.topics,
                bootstrap_servers=self.bootstrap_servers,
                group_id=self.group_id,
                client_id=self.client_id,
                auto_offset_reset=self.auto_offset_reset,
                enable_auto_commit=self.enable_auto_commit,
                auto_commit_interval_ms=self.auto_commit_interval_ms,
                max_poll_records=self.max_poll_records,
                max_poll_interval_ms=self.max_poll_interval_ms,
                value_deserializer=lambda x: json.loads(x.decode('utf-8')),
                key_deserializer=lambda x: x.decode('utf-8') if x else None
            )
            
            self._is_running = True
            
            # 启动消费线程
            self._consume_thread = threading.Thread(target=self._consume_loop, daemon=True)
            self._consume_thread.start()
            
            logger.info(f"Kafka消费者启动成功: 主题 {self.topics}, 组 {self.group_id}")
            return True
            
        except Exception as e:
            logger.error(f"Kafka消费者启动失败: {e}")
            return False
    
    async def stop(self) -> None:
        """停止消费者"""
        try:
            self._is_running = False
            
            if self._consumer:
                self._consumer.close()
                self._consumer = None
            
            if self._consume_thread and self._consume_thread.is_alive():
                self._consume_thread.join(timeout=10)
            
            self._executor.shutdown(wait=True, timeout=10)
            
            logger.info("Kafka消费者已停止")
            
        except Exception as e:
            logger.error(f"Kafka消费者停止失败: {e}")
    
    def register_handler(
        self,
        topic: str,
        handler: Callable[[Message], Any]
    ) -> None:
        """注册消息处理器"""
        self._message_handlers[topic] = handler
        logger.info(f"已注册主题处理器: {topic}")
    
    def _consume_loop(self) -> None:
        """消费循环"""
        logger.info("开始消费消息")
        
        while self._is_running and self._consumer:
            try:
                # 拉取消息
                message_batch = self._consumer.poll(timeout_ms=1000)
                
                if not message_batch:
                    continue
                
                # 处理消息
                for topic_partition, records in message_batch.items():
                    topic = topic_partition.topic
                    
                    for record in records:
                        try:
                            # 创建消息对象
                            message = Message(
                                key=record.key,
                                value=record.value,
                                headers=dict(record.headers) if record.headers else None,
                                partition=record.partition,
                                offset=record.offset,
                                timestamp=datetime.fromtimestamp(record.timestamp / 1000) if record.timestamp else None
                            )
                            
                            # 更新统计
                            self._stats.messages_consumed += 1
                            self._stats.last_consume_time = datetime.now()
                            
                            # 异步处理消息
                            if topic in self._message_handlers:
                                self._executor.submit(self._handle_message, topic, message)
                            else:
                                logger.warning(f"未找到主题处理器: {topic}")
                            
                        except Exception as e:
                            logger.error(f"处理消息失败: {e}")
                            self._stats.messages_failed += 1
                
            except Exception as e:
                logger.error(f"消费循环失败: {e}")
                time.sleep(1)  # 避免快速重试
        
        logger.info("消费循环结束")
    
    def _handle_message(self, topic: str, message: Message) -> None:
        """处理单条消息"""
        try:
            handler = self._message_handlers.get(topic)
            if handler:
                if asyncio.iscoroutinefunction(handler):
                    # 异步处理器需要在新的事件循环中运行
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        loop.run_until_complete(handler(message))
                    finally:
                        loop.close()
                else:
                    handler(message)
                
                self._stats.messages_processed += 1
            
        except Exception as e:
            logger.error(f"消息处理器执行失败: {e}")
            self._stats.messages_failed += 1
    
    def get_stats(self) -> ConsumerStats:
        """获取统计信息"""
        return self._stats
    
    def reset_stats(self) -> None:
        """重置统计信息"""
        self._stats = ConsumerStats()


class KafkaTopicManager:
    """Kafka主题管理器"""
    
    def __init__(self, bootstrap_servers: List[str]):
        self.bootstrap_servers = bootstrap_servers
        self._admin_client: Optional[KafkaAdminClient] = None
        
        if not KAFKA_AVAILABLE:
            logger.warning("Kafka未安装，主题管理器将被禁用")
    
    async def connect(self) -> bool:
        """连接到Kafka"""
        if not KAFKA_AVAILABLE:
            return False
        
        try:
            self._admin_client = KafkaAdminClient(
                bootstrap_servers=self.bootstrap_servers,
                client_id="redfire_admin"
            )
            
            logger.info("Kafka管理客户端连接成功")
            return True
            
        except Exception as e:
            logger.error(f"Kafka管理客户端连接失败: {e}")
            return False
    
    async def disconnect(self) -> None:
        """断开连接"""
        if self._admin_client:
            self._admin_client.close()
            self._admin_client = None
    
    async def create_topic(self, topic_config: TopicConfig) -> bool:
        """创建主题"""
        if not self._admin_client:
            logger.error("管理客户端未连接")
            return False
        
        try:
            # 创建新主题
            new_topic = NewTopic(
                name=topic_config.name,
                num_partitions=topic_config.num_partitions,
                replication_factor=topic_config.replication_factor,
                topic_configs=topic_config.to_kafka_config()
            )
            
            # 执行创建
            future_map = self._admin_client.create_topics([new_topic])
            
            # 等待完成
            for topic, future in future_map.items():
                try:
                    future.result()  # 等待操作完成
                    logger.info(f"主题创建成功: {topic}")
                    return True
                except TopicAlreadyExistsError:
                    logger.warning(f"主题已存在: {topic}")
                    return True
                except Exception as e:
                    logger.error(f"主题创建失败: {topic}, {e}")
                    return False
            
            return False
            
        except Exception as e:
            logger.error(f"创建主题失败: {e}")
            return False
    
    async def delete_topic(self, topic_name: str) -> bool:
        """删除主题"""
        if not self._admin_client:
            logger.error("管理客户端未连接")
            return False
        
        try:
            future_map = self._admin_client.delete_topics([topic_name])
            
            for topic, future in future_map.items():
                try:
                    future.result()
                    logger.info(f"主题删除成功: {topic}")
                    return True
                except Exception as e:
                    logger.error(f"主题删除失败: {topic}, {e}")
                    return False
            
            return False
            
        except Exception as e:
            logger.error(f"删除主题失败: {e}")
            return False
    
    async def list_topics(self) -> List[str]:
        """列出所有主题"""
        if not self._admin_client:
            logger.error("管理客户端未连接")
            return []
        
        try:
            metadata = self._admin_client.list_topics()
            return list(metadata.topics.keys())
            
        except Exception as e:
            logger.error(f"列出主题失败: {e}")
            return []
    
    async def get_topic_config(self, topic_name: str) -> Dict[str, str]:
        """获取主题配置"""
        if not self._admin_client:
            logger.error("管理客户端未连接")
            return {}
        
        try:
            resource = ConfigResource(ConfigResourceType.TOPIC, topic_name)
            config_map = self._admin_client.describe_configs([resource])
            
            config = config_map.get(resource)
            if config:
                return {key: entry.value for key, entry in config.configs.items()}
            
            return {}
            
        except Exception as e:
            logger.error(f"获取主题配置失败: {e}")
            return {}
    
    async def create_default_topics(self) -> None:
        """创建默认主题"""
        try:
            default_topics = [
                TopicConfig(
                    name="market_data",
                    num_partitions=6,
                    retention_ms=3600000,  # 1小时
                    compression_type=CompressionType.LZ4
                ),
                TopicConfig(
                    name="trade_orders",
                    num_partitions=3,
                    retention_ms=604800000,  # 7天
                    compression_type=CompressionType.GZIP
                ),
                TopicConfig(
                    name="position_updates",
                    num_partitions=3,
                    retention_ms=86400000,  # 1天
                    compression_type=CompressionType.GZIP
                ),
                TopicConfig(
                    name="risk_alerts",
                    num_partitions=2,
                    retention_ms=2592000000,  # 30天
                    compression_type=CompressionType.GZIP
                ),
                TopicConfig(
                    name="settlement_events",
                    num_partitions=2,
                    retention_ms=2592000000,  # 30天
                    compression_type=CompressionType.GZIP
                ),
                TopicConfig(
                    name="system_events",
                    num_partitions=1,
                    retention_ms=604800000,  # 7天
                    compression_type=CompressionType.GZIP
                )
            ]
            
            for topic_config in default_topics:
                await self.create_topic(topic_config)
            
            logger.info("默认主题创建完成")
            
        except Exception as e:
            logger.error(f"创建默认主题失败: {e}")


class KafkaMessageService:
    """Kafka消息服务统一接口"""
    
    def __init__(
        self,
        bootstrap_servers: List[str] = ["localhost:9092"],
        client_id_prefix: str = "redfire"
    ):
        self.bootstrap_servers = bootstrap_servers
        self.client_id_prefix = client_id_prefix
        
        self.producer_service = KafkaProducerService(
            bootstrap_servers=bootstrap_servers,
            client_id=f"{client_id_prefix}_producer"
        )
        
        self.topic_manager = KafkaTopicManager(bootstrap_servers)
        
        self._consumer_services: Dict[str, KafkaConsumerService] = {}
        self._is_running = False
    
    async def start(self) -> bool:
        """启动消息服务"""
        try:
            # 连接主题管理器
            topic_connected = await self.topic_manager.connect()
            if topic_connected:
                # 创建默认主题
                await self.topic_manager.create_default_topics()
            
            # 启动生产者
            producer_started = await self.producer_service.start()
            
            self._is_running = True
            logger.info("Kafka消息服务启动成功")
            
            return producer_started
            
        except Exception as e:
            logger.error(f"Kafka消息服务启动失败: {e}")
            return False
    
    async def stop(self) -> None:
        """停止消息服务"""
        try:
            self._is_running = False
            
            # 停止所有消费者
            for consumer in self._consumer_services.values():
                await consumer.stop()
            self._consumer_services.clear()
            
            # 停止生产者
            await self.producer_service.stop()
            
            # 断开主题管理器
            await self.topic_manager.disconnect()
            
            logger.info("Kafka消息服务已停止")
            
        except Exception as e:
            logger.error(f"Kafka消息服务停止失败: {e}")
    
    async def create_consumer(
        self,
        group_id: str,
        topics: List[str],
        **kwargs
    ) -> Optional[KafkaConsumerService]:
        """创建消费者"""
        try:
            consumer_service = KafkaConsumerService(
                bootstrap_servers=self.bootstrap_servers,
                group_id=group_id,
                topics=topics,
                client_id=f"{self.client_id_prefix}_consumer_{group_id}",
                **kwargs
            )
            
            started = await consumer_service.start()
            if started:
                self._consumer_services[group_id] = consumer_service
                return consumer_service
            
            return None
            
        except Exception as e:
            logger.error(f"创建消费者失败: {e}")
            return None
    
    async def send_message(
        self,
        topic: str,
        message: Union[Message, Dict[str, Any]],
        **kwargs
    ) -> bool:
        """发送消息"""
        return await self.producer_service.send_message(topic, message, **kwargs)
    
    async def send_batch(
        self,
        topic: str,
        messages: List[Union[Message, Dict[str, Any]]],
        **kwargs
    ) -> Tuple[int, int]:
        """批量发送消息"""
        return await self.producer_service.send_batch(topic, messages, **kwargs)
    
    async def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        try:
            stats = {
                "is_running": self._is_running,
                "producer_stats": self.producer_service.get_stats().to_dict(),
                "consumer_stats": {},
                "topics": await self.topic_manager.list_topics(),
                "timestamp": datetime.now().isoformat()
            }
            
            # 添加消费者统计
            for group_id, consumer in self._consumer_services.items():
                stats["consumer_stats"][group_id] = consumer.get_stats().to_dict()
            
            return stats
            
        except Exception as e:
            logger.error(f"获取Kafka统计失败: {e}")
            return {"error": str(e)}


# 全局消息服务实例
_message_service: Optional[KafkaMessageService] = None


async def get_message_service() -> KafkaMessageService:
    """获取全局消息服务实例"""
    global _message_service
    
    if _message_service is None:
        _message_service = KafkaMessageService()
        await _message_service.start()
    
    return _message_service


# 消息发布订阅装饰器
def message_handler(topic: str, group_id: str = "default"):
    """消息处理器装饰器"""
    def decorator(func):
        async def setup_handler():
            service = await get_message_service()
            consumer = await service.create_consumer(group_id, [topic])
            if consumer:
                consumer.register_handler(topic, func)
        
        # 注册处理器
        asyncio.create_task(setup_handler())
        return func
    
    return decorator


async def publish_message(
    topic: str,
    message: Union[Message, Dict[str, Any]],
    **kwargs
) -> bool:
    """发布消息"""
    service = await get_message_service()
    return await service.send_message(topic, message, **kwargs)
