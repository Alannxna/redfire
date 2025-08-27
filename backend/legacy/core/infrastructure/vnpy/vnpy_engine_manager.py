"""
VnPy引擎管理器
=============

负责VnPy主引擎和事件引擎的生命周期管理
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime

from .vnpy_path_manager import get_path_manager

logger = logging.getLogger(__name__)


class VnPyEngineManager:
    """VnPy引擎管理器"""
    
    def __init__(self):
        self.path_manager = get_path_manager()
        
        # 引擎实例
        self._main_engine: Optional[Any] = None
        self._event_engine: Optional[Any] = None
        
        # 状态管理
        self._engine_started = False
        self._gateways_connected: Dict[str, bool] = {}
        self._event_handlers: Dict[str, List[Callable]] = {}
        
        # 尝试导入VnPy模块
        self._vnpy_available = self._check_vnpy_availability()
    
    def _check_vnpy_availability(self) -> bool:
        """检查VnPy是否可用"""
        try:
            # 确保路径已设置
            self.path_manager.setup_paths()
            
            # 尝试导入VnPy核心模块
            from vnpy.event import EventEngine
            from vnpy.trader.engine import MainEngine
            
            logger.info("VnPy核心模块导入成功")
            return True
            
        except ImportError as e:
            logger.warning(f"VnPy核心模块导入失败: {e}")
            return False
        except Exception as e:
            logger.error(f"VnPy可用性检查失败: {e}")
            return False
    
    def is_vnpy_available(self) -> bool:
        """检查VnPy是否可用"""
        return self._vnpy_available
    
    async def start_engines(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """
        启动VnPy引擎
        
        Args:
            config: 引擎配置
            
        Returns:
            启动是否成功
        """
        if not self._vnpy_available:
            logger.error("VnPy不可用，无法启动引擎")
            return False
        
        if self._engine_started:
            logger.warning("VnPy引擎已经启动")
            return True
        
        try:
            logger.info("启动VnPy引擎...")
            
            # 导入VnPy模块
            from vnpy.event import EventEngine
            from vnpy.trader.engine import MainEngine
            
            # 创建事件引擎
            self._event_engine = EventEngine()
            
            # 创建主引擎
            self._main_engine = MainEngine(self._event_engine)
            
            # 注册事件处理器
            self._register_event_handlers()
            
            self._engine_started = True
            logger.info("VnPy引擎启动成功")
            
            return True
            
        except Exception as e:
            logger.error(f"VnPy引擎启动失败: {e}")
            return False
    
    async def stop_engines(self) -> bool:
        """
        停止VnPy引擎
        
        Returns:
            停止是否成功
        """
        if not self._engine_started:
            logger.warning("VnPy引擎未启动")
            return True
        
        try:
            logger.info("停止VnPy引擎...")
            
            # 断开所有网关连接
            await self._disconnect_all_gateways()
            
            # 停止主引擎
            if self._main_engine:
                self._main_engine.close()
                self._main_engine = None
            
            # 停止事件引擎
            if self._event_engine:
                self._event_engine.stop()
                self._event_engine = None
            
            # 清理状态
            self._engine_started = False
            self._gateways_connected.clear()
            self._event_handlers.clear()
            
            logger.info("VnPy引擎停止成功")
            return True
            
        except Exception as e:
            logger.error(f"VnPy引擎停止失败: {e}")
            return False
    
    def _register_event_handlers(self):
        """注册事件处理器"""
        if not self._event_engine:
            return
        
        try:
            from vnpy.trader.event import (
                EVENT_TICK, EVENT_ORDER, EVENT_TRADE,
                EVENT_POSITION, EVENT_ACCOUNT, EVENT_LOG
            )
            
            # 注册核心事件处理器
            self._event_engine.register(EVENT_TICK, self._on_tick_event)
            self._event_engine.register(EVENT_ORDER, self._on_order_event)
            self._event_engine.register(EVENT_TRADE, self._on_trade_event)
            self._event_engine.register(EVENT_POSITION, self._on_position_event)
            self._event_engine.register(EVENT_ACCOUNT, self._on_account_event)
            self._event_engine.register(EVENT_LOG, self._on_log_event)
            
            logger.info("VnPy事件处理器注册完成")
            
        except Exception as e:
            logger.error(f"VnPy事件处理器注册失败: {e}")
    
    def _on_tick_event(self, event):
        """处理Tick事件"""
        # 可以添加自定义的Tick处理逻辑
        pass
    
    def _on_order_event(self, event):
        """处理订单事件"""
        # 可以添加自定义的订单处理逻辑
        pass
    
    def _on_trade_event(self, event):
        """处理成交事件"""
        # 可以添加自定义的成交处理逻辑
        pass
    
    def _on_position_event(self, event):
        """处理持仓事件"""
        # 可以添加自定义的持仓处理逻辑
        pass
    
    def _on_account_event(self, event):
        """处理账户事件"""
        # 可以添加自定义的账户处理逻辑
        pass
    
    def _on_log_event(self, event):
        """处理日志事件"""
        # 转发VnPy日志到Backend日志系统
        log_data = event.data
        if hasattr(log_data, 'msg') and hasattr(log_data, 'level'):
            level = getattr(logging, log_data.level.upper(), logging.INFO)
            logger.log(level, f"[VnPy] {log_data.msg}")
    
    async def connect_gateway(self, gateway_name: str, gateway_setting: Dict[str, Any]) -> bool:
        """
        连接交易网关
        
        Args:
            gateway_name: 网关名称
            gateway_setting: 网关设置
            
        Returns:
            连接是否成功
        """
        if not self._main_engine:
            logger.error("主引擎未启动，无法连接网关")
            return False
        
        try:
            # 添加网关
            self._main_engine.add_gateway(gateway_name)
            
            # 连接网关
            self._main_engine.connect(gateway_setting, gateway_name)
            
            self._gateways_connected[gateway_name] = True
            logger.info(f"网关 {gateway_name} 连接成功")
            
            return True
            
        except Exception as e:
            logger.error(f"网关 {gateway_name} 连接失败: {e}")
            self._gateways_connected[gateway_name] = False
            return False
    
    async def disconnect_gateway(self, gateway_name: str) -> bool:
        """
        断开交易网关
        
        Args:
            gateway_name: 网关名称
            
        Returns:
            断开是否成功
        """
        if not self._main_engine:
            logger.warning("主引擎未启动")
            return True
        
        try:
            self._main_engine.disconnect(gateway_name)
            self._gateways_connected[gateway_name] = False
            logger.info(f"网关 {gateway_name} 断开成功")
            
            return True
            
        except Exception as e:
            logger.error(f"网关 {gateway_name} 断开失败: {e}")
            return False
    
    async def _disconnect_all_gateways(self):
        """断开所有网关连接"""
        for gateway_name in list(self._gateways_connected.keys()):
            if self._gateways_connected[gateway_name]:
                await self.disconnect_gateway(gateway_name)
    
    def get_main_engine(self):
        """获取主引擎实例"""
        return self._main_engine
    
    def get_event_engine(self):
        """获取事件引擎实例"""
        return self._event_engine
    
    def is_engine_started(self) -> bool:
        """检查引擎是否已启动"""
        return self._engine_started
    
    def get_connected_gateways(self) -> List[str]:
        """获取已连接的网关列表"""
        return [name for name, connected in self._gateways_connected.items() if connected]
    
    def get_engine_status(self) -> Dict[str, Any]:
        """获取引擎状态"""
        return {
            "vnpy_available": self._vnpy_available,
            "engine_started": self._engine_started,
            "main_engine_active": self._main_engine is not None,
            "event_engine_active": self._event_engine is not None,
            "connected_gateways": self.get_connected_gateways(),
            "total_gateways": len(self._gateways_connected)
        }
    
    def add_event_handler(self, event_type: str, handler: Callable):
        """
        添加自定义事件处理器
        
        Args:
            event_type: 事件类型
            handler: 处理器函数
        """
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        
        self._event_handlers[event_type].append(handler)
        
        # 如果事件引擎已启动，立即注册
        if self._event_engine:
            self._event_engine.register(event_type, handler)
        
        logger.info(f"添加事件处理器: {event_type}")
    
    def remove_event_handler(self, event_type: str, handler: Callable):
        """
        移除自定义事件处理器
        
        Args:
            event_type: 事件类型
            handler: 处理器函数
        """
        if event_type in self._event_handlers:
            try:
                self._event_handlers[event_type].remove(handler)
                
                # 如果事件引擎已启动，取消注册
                if self._event_engine:
                    self._event_engine.unregister(event_type, handler)
                
                logger.info(f"移除事件处理器: {event_type}")
                
            except ValueError:
                logger.warning(f"事件处理器不存在: {event_type}")


# 全局引擎管理器实例
_engine_manager: Optional[VnPyEngineManager] = None


def get_engine_manager() -> VnPyEngineManager:
    """获取全局引擎管理器实例"""
    global _engine_manager
    if _engine_manager is None:
        _engine_manager = VnPyEngineManager()
    return _engine_manager

