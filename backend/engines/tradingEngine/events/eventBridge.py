"""
事件桥接器

在本地事件引擎和分布式事件引擎之间建立桥梁，
实现本地事件的分布式传播和远程事件的本地处理。
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass
from enum import Enum

from ..eventEngine import EventTradingEngine
from .distributedEventEngine import DistributedEventEngine, DistributedEvent, EventDeliveryMode


class BridgeDirection(Enum):
    """桥接方向"""
    LOCAL_TO_DISTRIBUTED = "local_to_distributed"    # 本地到分布式
    DISTRIBUTED_TO_LOCAL = "distributed_to_local"    # 分布式到本地
    BIDIRECTIONAL = "bidirectional"                  # 双向


@dataclass
class EventMapping:
    """事件映射配置"""
    local_event_type: str
    distributed_event_type: str
    direction: BridgeDirection = BridgeDirection.BIDIRECTIONAL
    delivery_mode: EventDeliveryMode = EventDeliveryMode.FANOUT
    transform_func: Optional[callable] = None
    filter_func: Optional[callable] = None
    enabled: bool = True


class EventBridge:
    """
    事件桥接器
    
    负责在本地事件引擎和分布式事件引擎之间转发事件，
    支持事件转换、过滤和路由。
    """
    
    def __init__(self, local_engine: EventTradingEngine, 
                 distributed_engine: DistributedEventEngine):
        self.local_engine = local_engine
        self.distributed_engine = distributed_engine
        self.logger = logging.getLogger(__name__)
        
        # 事件映射配置
        self.event_mappings: Dict[str, EventMapping] = {}
        
        # 桥接状态
        self.is_active = False
        self.bridge_handlers: Dict[str, str] = {}  # handler_id映射
        
        # 过滤器 - 避免循环转发
        self.processed_local_events: Set[str] = set()
        self.processed_distributed_events: Set[str] = set()
        self.max_cache_size = 1000
        
        # 统计信息
        self.stats = {
            'local_to_distributed': 0,
            'distributed_to_local': 0,
            'filtered_events': 0,
            'transform_errors': 0,
            'bridge_errors': 0
        }
        
        # 默认事件映射
        self._setup_default_mappings()
    
    def _setup_default_mappings(self):
        """设置默认事件映射"""
        default_mappings = [
            # 交易相关事件
            EventMapping("order_update", "trading.order_update"),
            EventMapping("trade_update", "trading.trade_update"),
            EventMapping("position_update", "trading.position_update"),
            EventMapping("account_update", "trading.account_update"),
            
            # 行情相关事件
            EventMapping("tick_data", "market.tick_data"),
            EventMapping("bar_data", "market.bar_data"),
            EventMapping("depth_data", "market.depth_data"),
            
            # 策略相关事件
            EventMapping("strategy_log", "strategy.log"),
            EventMapping("strategy_update", "strategy.update"),
            EventMapping("strategy_signal", "strategy.signal"),
            
            # 系统相关事件
            EventMapping("gateway_log", "system.gateway_log"),
            EventMapping("gateway_update", "system.gateway_update"),
            EventMapping("engine_status", "system.engine_status"),
            
            # 风控相关事件
            EventMapping("risk_warning", "risk.warning"),
            EventMapping("risk_limit", "risk.limit"),
            EventMapping("risk_violation", "risk.violation")
        ]
        
        for mapping in default_mappings:
            self.add_event_mapping(mapping)
    
    def add_event_mapping(self, mapping: EventMapping):
        """添加事件映射"""
        key = f"{mapping.local_event_type}:{mapping.distributed_event_type}"
        self.event_mappings[key] = mapping
        self.logger.info(f"添加事件映射: {mapping.local_event_type} <-> {mapping.distributed_event_type}")
    
    def remove_event_mapping(self, local_event_type: str, distributed_event_type: str):
        """移除事件映射"""
        key = f"{local_event_type}:{distributed_event_type}"
        if key in self.event_mappings:
            del self.event_mappings[key]
            self.logger.info(f"移除事件映射: {local_event_type} <-> {distributed_event_type}")
    
    async def start(self) -> bool:
        """启动事件桥接"""
        try:
            if self.is_active:
                self.logger.warning("事件桥接器已经运行")
                return True
            
            self.logger.info("启动事件桥接器...")
            
            # 注册本地事件处理器
            await self._register_local_handlers()
            
            # 注册分布式事件处理器
            await self._register_distributed_handlers()
            
            self.is_active = True
            self.logger.info("事件桥接器启动成功")
            return True
            
        except Exception as e:
            self.logger.error(f"启动事件桥接器失败: {e}")
            return False
    
    async def stop(self) -> bool:
        """停止事件桥接"""
        try:
            if not self.is_active:
                self.logger.warning("事件桥接器未运行")
                return True
            
            self.logger.info("停止事件桥接器...")
            
            # 注销处理器
            await self._unregister_handlers()
            
            self.is_active = False
            self.logger.info("事件桥接器已停止")
            return True
            
        except Exception as e:
            self.logger.error(f"停止事件桥接器失败: {e}")
            return False
    
    async def _register_local_handlers(self):
        """注册本地事件处理器"""
        for mapping in self.event_mappings.values():
            if not mapping.enabled:
                continue
            
            if mapping.direction in [BridgeDirection.LOCAL_TO_DISTRIBUTED, 
                                   BridgeDirection.BIDIRECTIONAL]:
                
                # 注册本地事件处理器
                handler_id = f"bridge_local_{mapping.local_event_type}"
                success = self.local_engine.registerHandler(
                    mapping.local_event_type,
                    lambda data, m=mapping: asyncio.create_task(
                        self._handle_local_event(data, m)
                    )
                )
                
                if success:
                    self.bridge_handlers[handler_id] = mapping.local_event_type
                    self.logger.debug(f"注册本地事件处理器: {mapping.local_event_type}")
    
    async def _register_distributed_handlers(self):
        """注册分布式事件处理器"""
        for mapping in self.event_mappings.values():
            if not mapping.enabled:
                continue
            
            if mapping.direction in [BridgeDirection.DISTRIBUTED_TO_LOCAL,
                                   BridgeDirection.BIDIRECTIONAL]:
                
                # 注册分布式事件处理器
                handler_id = f"bridge_distributed_{mapping.distributed_event_type}"
                success = await self.distributed_engine.register_handler(
                    handler_id,
                    lambda event, m=mapping: asyncio.create_task(
                        self._handle_distributed_event(event, m)
                    ),
                    [mapping.distributed_event_type]
                )
                
                if success:
                    self.bridge_handlers[handler_id] = mapping.distributed_event_type
                    self.logger.debug(f"注册分布式事件处理器: {mapping.distributed_event_type}")
    
    async def _unregister_handlers(self):
        """注销所有处理器"""
        for handler_id, event_type in self.bridge_handlers.items():
            try:
                if handler_id.startswith("bridge_local_"):
                    # 注销本地处理器（需要实现unregisterHandler方法）
                    # self.local_engine.unregisterHandler(event_type, handler)
                    pass
                elif handler_id.startswith("bridge_distributed_"):
                    # 注销分布式处理器
                    await self.distributed_engine.unregister_handler(handler_id)
            except Exception as e:
                self.logger.error(f"注销处理器失败: {handler_id} - {e}")
        
        self.bridge_handlers.clear()
    
    async def _handle_local_event(self, event_data: Any, mapping: EventMapping):
        """处理本地事件"""
        try:
            # 生成事件标识（用于去重）
            event_id = f"local_{mapping.local_event_type}_{hash(str(event_data))}"
            
            # 检查是否已处理
            if event_id in self.processed_local_events:
                return
            
            self.processed_local_events.add(event_id)
            self._cleanup_cache(self.processed_local_events)
            
            # 应用过滤器
            if mapping.filter_func and not mapping.filter_func(event_data):
                self.stats['filtered_events'] += 1
                return
            
            # 转换数据
            try:
                if mapping.transform_func:
                    transformed_data = mapping.transform_func(event_data)
                else:
                    transformed_data = self._default_local_transform(event_data)
            except Exception as e:
                self.logger.error(f"转换本地事件数据失败: {e}")
                self.stats['transform_errors'] += 1
                return
            
            # 发布到分布式事件引擎
            await self.distributed_engine.publish_event(
                mapping.distributed_event_type,
                transformed_data,
                delivery_mode=mapping.delivery_mode
            )
            
            self.stats['local_to_distributed'] += 1
            self.logger.debug(f"本地事件已转发: {mapping.local_event_type} -> {mapping.distributed_event_type}")
            
        except Exception as e:
            self.stats['bridge_errors'] += 1
            self.logger.error(f"处理本地事件失败: {e}")
    
    async def _handle_distributed_event(self, event: DistributedEvent, mapping: EventMapping):
        """处理分布式事件"""
        try:
            # 检查是否已处理
            if event.event_id in self.processed_distributed_events:
                return
            
            self.processed_distributed_events.add(event.event_id)
            self._cleanup_cache(self.processed_distributed_events)
            
            # 应用过滤器
            if mapping.filter_func and not mapping.filter_func(event.data):
                self.stats['filtered_events'] += 1
                return
            
            # 转换数据
            try:
                if mapping.transform_func:
                    transformed_data = mapping.transform_func(event.data)
                else:
                    transformed_data = self._default_distributed_transform(event.data)
            except Exception as e:
                self.logger.error(f"转换分布式事件数据失败: {e}")
                self.stats['transform_errors'] += 1
                return
            
            # 发布到本地事件引擎
            self.local_engine.putEvent(mapping.local_event_type, transformed_data)
            
            self.stats['distributed_to_local'] += 1
            self.logger.debug(f"分布式事件已转发: {mapping.distributed_event_type} -> {mapping.local_event_type}")
            
        except Exception as e:
            self.stats['bridge_errors'] += 1
            self.logger.error(f"处理分布式事件失败: {e}")
    
    def _default_local_transform(self, event_data: Any) -> Dict[str, Any]:
        """默认本地事件数据转换"""
        if isinstance(event_data, dict):
            return event_data
        elif hasattr(event_data, '__dict__'):
            return event_data.__dict__
        else:
            return {'data': event_data}
    
    def _default_distributed_transform(self, event_data: Dict[str, Any]) -> Any:
        """默认分布式事件数据转换"""
        return event_data
    
    def _cleanup_cache(self, cache: Set[str]):
        """清理缓存"""
        if len(cache) > self.max_cache_size:
            # 清理一半的缓存
            items_to_remove = list(cache)[:self.max_cache_size // 2]
            for item in items_to_remove:
                cache.discard(item)
    
    def get_status(self) -> Dict[str, Any]:
        """获取桥接器状态"""
        return {
            'is_active': self.is_active,
            'mappings_count': len(self.event_mappings),
            'active_handlers': len(self.bridge_handlers),
            'cache_sizes': {
                'local_events': len(self.processed_local_events),
                'distributed_events': len(self.processed_distributed_events)
            },
            'stats': self.stats.copy(),
            'mappings': {
                key: {
                    'local_event': mapping.local_event_type,
                    'distributed_event': mapping.distributed_event_type,
                    'direction': mapping.direction.value,
                    'enabled': mapping.enabled
                }
                for key, mapping in self.event_mappings.items()
            }
        }
    
    def enable_mapping(self, local_event_type: str, distributed_event_type: str):
        """启用事件映射"""
        key = f"{local_event_type}:{distributed_event_type}"
        if key in self.event_mappings:
            self.event_mappings[key].enabled = True
            self.logger.info(f"启用事件映射: {key}")
    
    def disable_mapping(self, local_event_type: str, distributed_event_type: str):
        """禁用事件映射"""
        key = f"{local_event_type}:{distributed_event_type}"
        if key in self.event_mappings:
            self.event_mappings[key].enabled = False
            self.logger.info(f"禁用事件映射: {key}")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self.stats.copy()
