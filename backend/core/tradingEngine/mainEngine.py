"""
主交易引擎 (Main Trading Engine)

从 vnpy-core 的 MainEngine 迁移而来，负责管理所有交易引擎组件。
采用更清晰的命名规范和架构设计。
"""

import logging
from typing import Dict, List, Optional, Any
from .eventEngine import EventTradingEngine
from .baseEngine import BaseTradingEngine
from .appBase import BaseTradingApp
from .engineManager import EngineManager
from .pluginManager import PluginManager
from .adapters import VnPyEngineAdapter, VnPyConfig
from .strategies import IndependentStrategyEngine
from .events import DistributedEventEngine, RedisEventTransport, EventBridge


class MainTradingEngine:
    """
    主交易引擎类
    
    负责管理所有交易引擎组件，包括：
    - 事件引擎
    - 交易引擎
    - 网关接口
    - 交易应用
    """
    
    def __init__(self, event_engine: Optional[EventTradingEngine] = None, 
                 vnpy_config: Optional[VnPyConfig] = None,
                 redis_url: Optional[str] = None,
                 service_name: str = "trading_engine"):
        """
        初始化主交易引擎
        
        Args:
            event_engine: 事件引擎实例，如果为None则创建新的实例
            vnpy_config: VnPy配置，如果提供则启用VnPy集成
            redis_url: Redis连接URL，如果提供则启用分布式事件
            service_name: 服务名称，用于分布式事件识别
        """
        # 核心组件
        self.eventTradingEngine = event_engine or EventTradingEngine()
        self.engineManager = EngineManager()
        self.pluginManager = PluginManager()
        
        # 引擎集合
        self.tradingEngines: Dict[str, BaseTradingEngine] = {}
        self.gatewayInterfaces: Dict[str, Any] = {}
        self.tradingApps: Dict[str, BaseTradingApp] = {}
        
        # VnPy集成
        self.vnpy_adapter: Optional[VnPyEngineAdapter] = None
        if vnpy_config:
            self.vnpy_adapter = VnPyEngineAdapter(self, vnpy_config)
        
        # 独立策略引擎
        self.strategy_engine = IndependentStrategyEngine(self)
        
        # 分布式事件引擎
        self.distributed_event_engine: Optional[DistributedEventEngine] = None
        self.event_bridge: Optional[EventBridge] = None
        if redis_url:
            transport = RedisEventTransport(redis_url)
            self.distributed_event_engine = DistributedEventEngine(service_name, transport)
            self.event_bridge = EventBridge(self.eventTradingEngine, self.distributed_event_engine)
        
        # 状态标志
        self.isActive = False
        
        # 日志记录器
        self.logger = logging.getLogger(__name__)
        
        # 初始化日志
        self._setup_logging()
    
    def _setup_logging(self):
        """设置日志记录"""
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    async def startEngine(self) -> bool:
        """
        启动主交易引擎
        
        Returns:
            bool: 启动是否成功
        """
        try:
            self.logger.info("正在启动主交易引擎...")
            
            # 启动事件引擎
            if not self.eventTradingEngine.isActive:
                self.eventTradingEngine.startEngine()
            
            # 初始化并启动VnPy适配器
            if self.vnpy_adapter:
                self.logger.info("初始化VnPy适配器...")
                if await self.vnpy_adapter.initialize():
                    await self.vnpy_adapter.start()
                    self.logger.info("VnPy适配器启动成功")
                else:
                    self.logger.warning("VnPy适配器初始化失败，继续运行其他组件")
            
            # 启动独立策略引擎
            await self.strategy_engine.start()
            self.logger.info("独立策略引擎启动成功")
            
            # 启动分布式事件引擎
            if self.distributed_event_engine:
                await self.distributed_event_engine.initialize()
                self.logger.info("分布式事件引擎启动成功")
            
            # 启动事件桥接器
            if self.event_bridge:
                await self.event_bridge.start()
                self.logger.info("事件桥接器启动成功")
            
            # 启动所有交易引擎
            for engine_name, engine in self.tradingEngines.items():
                if not engine.isActive:
                    engine.startEngine()
                    self.logger.info(f"交易引擎 {engine_name} 已启动")
            
            # 启动所有交易应用
            for app_name, app in self.tradingApps.items():
                if not app.isActive:
                    app.startApp()
                    self.logger.info(f"交易应用 {app_name} 已启动")
            
            self.isActive = True
            self.logger.info("主交易引擎启动成功")
            return True
            
        except Exception as e:
            self.logger.error(f"启动主交易引擎失败: {e}")
            return False
    
    async def stopEngine(self) -> bool:
        """
        停止主交易引擎
        
        Returns:
            bool: 停止是否成功
        """
        try:
            self.logger.info("正在停止主交易引擎...")
            
            # 停止事件桥接器
            if self.event_bridge:
                await self.event_bridge.stop()
                self.logger.info("事件桥接器已停止")
            
            # 停止分布式事件引擎
            if self.distributed_event_engine:
                await self.distributed_event_engine.close()
                self.logger.info("分布式事件引擎已停止")
            
            # 停止独立策略引擎
            await self.strategy_engine.stop()
            self.logger.info("独立策略引擎已停止")
            
            # 停止VnPy适配器
            if self.vnpy_adapter:
                await self.vnpy_adapter.stop()
                self.logger.info("VnPy适配器已停止")
            
            # 停止所有交易应用
            for app_name, app in self.tradingApps.items():
                if app.isActive:
                    app.stopApp()
                    self.logger.info(f"交易应用 {app_name} 已停止")
            
            # 停止所有交易引擎
            for engine_name, engine in self.tradingEngines.items():
                if engine.isActive:
                    engine.stopEngine()
                    self.logger.info(f"交易引擎 {engine_name} 已停止")
            
            # 停止事件引擎
            if self.eventTradingEngine.isActive:
                self.eventTradingEngine.stopEngine()
            
            self.isActive = False
            self.logger.info("主交易引擎已停止")
            return True
            
        except Exception as e:
            self.logger.error(f"停止主交易引擎失败: {e}")
            return False
    
    def addTradingEngine(self, engine: BaseTradingEngine) -> bool:
        """
        添加交易引擎
        
        Args:
            engine: 要添加的交易引擎实例
            
        Returns:
            bool: 添加是否成功
        """
        try:
            if engine.engineName in self.tradingEngines:
                self.logger.warning(f"交易引擎 {engine.engineName} 已存在")
                return False
            
            # 设置主引擎引用
            engine.mainTradingEngine = self
            
            # 添加到引擎集合
            self.tradingEngines[engine.engineName] = engine
            
            # 如果主引擎已启动，则启动新添加的引擎
            if self.isActive:
                engine.startEngine()
            
            self.logger.info(f"交易引擎 {engine.engineName} 添加成功")
            return True
            
        except Exception as e:
            self.logger.error(f"添加交易引擎失败: {e}")
            return False
    
    def removeTradingEngine(self, engine_name: str) -> bool:
        """
        移除交易引擎
        
        Args:
            engine_name: 要移除的引擎名称
            
        Returns:
            bool: 移除是否成功
        """
        try:
            if engine_name not in self.tradingEngines:
                self.logger.warning(f"交易引擎 {engine_name} 不存在")
                return False
            
            engine = self.tradingEngines[engine_name]
            
            # 停止引擎
            if engine.isActive:
                engine.stopEngine()
            
            # 从集合中移除
            del self.tradingEngines[engine_name]
            
            self.logger.info(f"交易引擎 {engine_name} 移除成功")
            return True
            
        except Exception as e:
            self.logger.error(f"移除交易引擎失败: {e}")
            return False
    
    def getTradingEngine(self, engine_name: str) -> Optional[BaseTradingEngine]:
        """
        获取指定的交易引擎
        
        Args:
            engine_name: 引擎名称
            
        Returns:
            Optional[BaseTradingEngine]: 交易引擎实例，如果不存在则返回None
        """
        return self.tradingEngines.get(engine_name)
    
    def getAllTradingEngines(self) -> Dict[str, BaseTradingEngine]:
        """
        获取所有交易引擎
        
        Returns:
            Dict[str, BaseTradingEngine]: 所有交易引擎的字典
        """
        return self.tradingEngines.copy()
    
    def addGatewayInterface(self, gateway_name: str, gateway_instance: Any) -> bool:
        """
        添加网关接口
        
        Args:
            gateway_name: 网关名称
            gateway_instance: 网关实例
            
        Returns:
            bool: 添加是否成功
        """
        try:
            if gateway_name in self.gatewayInterfaces:
                self.logger.warning(f"网关接口 {gateway_name} 已存在")
                return False
            
            self.gatewayInterfaces[gateway_name] = gateway_instance
            self.logger.info(f"网关接口 {gateway_name} 添加成功")
            return True
            
        except Exception as e:
            self.logger.error(f"添加网关接口失败: {e}")
            return False
    
    def removeGatewayInterface(self, gateway_name: str) -> bool:
        """
        移除网关接口
        
        Args:
            gateway_name: 要移除的网关名称
            
        Returns:
            bool: 移除是否成功
        """
        try:
            if gateway_name not in self.gatewayInterfaces:
                self.logger.warning(f"网关接口 {gateway_name} 不存在")
                return False
            
            del self.gatewayInterfaces[gateway_name]
            self.logger.info(f"网关接口 {gateway_name} 移除成功")
            return True
            
        except Exception as e:
            self.logger.error(f"移除网关接口失败: {e}")
            return False
    
    def getGatewayInterface(self, gateway_name: str) -> Optional[Any]:
        """
        获取指定的网关接口
        
        Args:
            gateway_name: 网关名称
            
        Returns:
            Optional[Any]: 网关实例，如果不存在则返回None
        """
        return self.gatewayInterfaces.get(gateway_name)
    
    def getAllGatewayInterfaces(self) -> Dict[str, Any]:
        """
        获取所有网关接口
        
        Returns:
            Dict[str, Any]: 所有网关接口的字典
        """
        return self.gatewayInterfaces.copy()
    
    def addTradingApp(self, app: BaseTradingApp) -> bool:
        """
        添加交易应用
        
        Args:
            app: 要添加的交易应用实例
            
        Returns:
            bool: 添加是否成功
        """
        try:
            if app.appName in self.tradingApps:
                self.logger.warning(f"交易应用 {app.appName} 已存在")
                return False
            
            # 设置主引擎引用
            app.mainTradingEngine = self
            
            # 添加到应用集合
            self.tradingApps[app.appName] = app
            
            # 如果主引擎已启动，则启动新添加的应用
            if self.isActive:
                app.startApp()
            
            self.logger.info(f"交易应用 {app.appName} 添加成功")
            return True
            
        except Exception as e:
            self.logger.error(f"添加交易应用失败: {e}")
            return False
    
    def removeTradingApp(self, app_name: str) -> bool:
        """
        移除交易应用
        
        Args:
            app_name: 要移除的应用名称
            
        Returns:
            bool: 移除是否成功
        """
        try:
            if app_name not in self.tradingApps:
                self.logger.warning(f"交易应用 {app_name} 不存在")
                return False
            
            app = self.tradingApps[app_name]
            
            # 停止应用
            if app.isActive:
                app.stopApp()
            
            # 从集合中移除
            del self.tradingApps[app_name]
            
            self.logger.info(f"交易应用 {app_name} 移除成功")
            return True
            
        except Exception as e:
            self.logger.error(f"移除交易应用失败: {e}")
            return False
    
    def getTradingApp(self, app_name: str) -> Optional[BaseTradingApp]:
        """
        获取指定的交易应用
        
        Args:
            app_name: 应用名称
            
        Returns:
            Optional[BaseTradingApp]: 交易应用实例，如果不存在则返回None
        """
        return self.tradingApps.get(app_name)
    
    def getAllTradingApps(self) -> Dict[str, BaseTradingApp]:
        """
        获取所有交易应用
        
        Returns:
            Dict[str, BaseTradingApp]: 所有交易应用的字典
        """
        return self.tradingApps.copy()
    
    def getStatus(self) -> Dict[str, Any]:
        """
        获取引擎状态信息
        
        Returns:
            Dict[str, Any]: 状态信息字典
        """
        status = {
            'isActive': self.isActive,
            'eventEngineActive': self.eventTradingEngine.isActive,
            'engineCount': len(self.tradingEngines),
            'gatewayCount': len(self.gatewayInterfaces),
            'appCount': len(self.tradingApps),
            'engines': {name: engine.isActive for name, engine in self.tradingEngines.items()},
            'apps': {name: app.isActive for name, app in self.tradingApps.items()}
        }
        
        # 添加VnPy适配器状态
        if self.vnpy_adapter:
            status['vnpy_adapter'] = self.vnpy_adapter.get_status()
        else:
            status['vnpy_adapter'] = None
        
        # 添加策略引擎状态
        status['strategy_engine'] = self.strategy_engine.get_engine_status()
        
        # 添加分布式事件引擎状态
        if self.distributed_event_engine:
            status['distributed_event_engine'] = self.distributed_event_engine.get_status()
        else:
            status['distributed_event_engine'] = None
        
        # 添加事件桥接器状态
        if self.event_bridge:
            status['event_bridge'] = self.event_bridge.get_status()
        else:
            status['event_bridge'] = None
            
        return status
    
    # ==================== VnPy集成方法 ====================
    
    def getVnPyAdapter(self) -> Optional[VnPyEngineAdapter]:
        """
        获取VnPy适配器实例
        
        Returns:
            Optional[VnPyEngineAdapter]: VnPy适配器实例，如果未启用则返回None
        """
        return self.vnpy_adapter
    
    def getVnPyMainEngine(self) -> Optional[Any]:
        """
        获取VnPy主引擎实例
        
        Returns:
            Optional[Any]: VnPy主引擎实例，如果未启用则返回None
        """
        return self.vnpy_adapter.get_vnpy_main_engine() if self.vnpy_adapter else None
    
    def getVnPyApp(self, app_name: str) -> Optional[Any]:
        """
        获取VnPy应用实例
        
        Args:
            app_name: 应用名称
            
        Returns:
            Optional[Any]: VnPy应用实例，如果未找到则返回None
        """
        return self.vnpy_adapter.get_vnpy_app(app_name) if self.vnpy_adapter else None
    
    def isVnPyEnabled(self) -> bool:
        """
        检查VnPy是否已启用
        
        Returns:
            bool: VnPy是否已启用
        """
        return self.vnpy_adapter is not None and self.vnpy_adapter.is_initialized
    
    # ==================== 策略引擎方法 ====================
    
    def getStrategyEngine(self) -> IndependentStrategyEngine:
        """
        获取独立策略引擎实例
        
        Returns:
            IndependentStrategyEngine: 策略引擎实例
        """
        return self.strategy_engine
    
    async def addStrategy(self, strategy_config) -> bool:
        """
        添加策略
        
        Args:
            strategy_config: 策略配置
            
        Returns:
            bool: 添加是否成功
        """
        return await self.strategy_engine.add_strategy(strategy_config)
    
    async def removeStrategy(self, strategy_id: str) -> bool:
        """
        移除策略
        
        Args:
            strategy_id: 策略ID
            
        Returns:
            bool: 移除是否成功
        """
        return await self.strategy_engine.remove_strategy(strategy_id)
    
    async def startStrategy(self, strategy_id: str) -> bool:
        """
        启动策略
        
        Args:
            strategy_id: 策略ID
            
        Returns:
            bool: 启动是否成功
        """
        return await self.strategy_engine.start_strategy(strategy_id)
    
    async def stopStrategy(self, strategy_id: str) -> bool:
        """
        停止策略
        
        Args:
            strategy_id: 策略ID
            
        Returns:
            bool: 停止是否成功
        """
        return await self.strategy_engine.stop_strategy(strategy_id)
    
    def getStrategyStatus(self, strategy_id: str) -> Optional[Dict[str, Any]]:
        """
        获取策略状态
        
        Args:
            strategy_id: 策略ID
            
        Returns:
            Optional[Dict[str, Any]]: 策略状态，如果未找到则返回None
        """
        return self.strategy_engine.get_strategy_status(strategy_id)
    
    def getAllStrategiesStatus(self) -> Dict[str, Dict[str, Any]]:
        """
        获取所有策略状态
        
        Returns:
            Dict[str, Dict[str, Any]]: 所有策略的状态字典
        """
        return self.strategy_engine.get_all_strategies_status()
    
    async def broadcastEventToStrategies(self, event_type: str, event_data: Any):
        """
        广播事件到策略
        
        Args:
            event_type: 事件类型
            event_data: 事件数据
        """
        await self.strategy_engine.broadcast_event(event_type, event_data)
    
    def subscribeStrategyEvent(self, strategy_id: str, event_type: str):
        """
        订阅策略事件
        
        Args:
            strategy_id: 策略ID
            event_type: 事件类型
        """
        self.strategy_engine.subscribe_event(strategy_id, event_type)
    
    def unsubscribeStrategyEvent(self, strategy_id: str, event_type: str):
        """
        取消订阅策略事件
        
        Args:
            strategy_id: 策略ID
            event_type: 事件类型
        """
        self.strategy_engine.unsubscribe_event(strategy_id, event_type)
    
    # ==================== 分布式事件引擎方法 ====================
    
    def getDistributedEventEngine(self) -> Optional[DistributedEventEngine]:
        """
        获取分布式事件引擎实例
        
        Returns:
            Optional[DistributedEventEngine]: 分布式事件引擎实例，如果未启用则返回None
        """
        return self.distributed_event_engine
    
    def getEventBridge(self) -> Optional[EventBridge]:
        """
        获取事件桥接器实例
        
        Returns:
            Optional[EventBridge]: 事件桥接器实例，如果未启用则返回None
        """
        return self.event_bridge
    
    async def publishDistributedEvent(self, event_type: str, data: Dict[str, Any], **kwargs) -> Optional[str]:
        """
        发布分布式事件
        
        Args:
            event_type: 事件类型
            data: 事件数据
            **kwargs: 其他参数
            
        Returns:
            Optional[str]: 事件ID，如果未启用分布式事件则返回None
        """
        if self.distributed_event_engine:
            return await self.distributed_event_engine.publish_event(event_type, data, **kwargs)
        return None
    
    async def registerDistributedEventHandler(self, handler_id: str, handler_func: Callable,
                                            event_types: List[str], **kwargs) -> bool:
        """
        注册分布式事件处理器
        
        Args:
            handler_id: 处理器ID
            handler_func: 处理函数
            event_types: 事件类型列表
            **kwargs: 其他配置参数
            
        Returns:
            bool: 注册是否成功
        """
        if self.distributed_event_engine:
            return await self.distributed_event_engine.register_handler(
                handler_id, handler_func, event_types, **kwargs
            )
        return False
    
    async def unregisterDistributedEventHandler(self, handler_id: str) -> bool:
        """
        注销分布式事件处理器
        
        Args:
            handler_id: 处理器ID
            
        Returns:
            bool: 注销是否成功
        """
        if self.distributed_event_engine:
            return await self.distributed_event_engine.unregister_handler(handler_id)
        return False
    
    def enableEventMapping(self, local_event_type: str, distributed_event_type: str):
        """
        启用事件映射
        
        Args:
            local_event_type: 本地事件类型
            distributed_event_type: 分布式事件类型
        """
        if self.event_bridge:
            self.event_bridge.enable_mapping(local_event_type, distributed_event_type)
    
    def disableEventMapping(self, local_event_type: str, distributed_event_type: str):
        """
        禁用事件映射
        
        Args:
            local_event_type: 本地事件类型
            distributed_event_type: 分布式事件类型
        """
        if self.event_bridge:
            self.event_bridge.disable_mapping(local_event_type, distributed_event_type)
    
    def isDistributedEventEnabled(self) -> bool:
        """
        检查分布式事件是否已启用
        
        Returns:
            bool: 分布式事件是否已启用
        """
        return self.distributed_event_engine is not None and self.distributed_event_engine.is_active
