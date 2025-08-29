"""
基础网关接口 (Base Gateway Interface)

定义所有交易网关的通用接口和基础功能。
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Callable
from ..baseEngine import BaseTradingEngine


class BaseGateway(ABC):
    """
    基础网关接口抽象类
    
    所有具体的交易网关都应该继承此类，实现以下功能：
    - 连接管理
    - 订单管理
    - 仓位查询
    - 市场数据订阅
    - 事件回调
    """
    
    def __init__(self, gateway_name: str, main_engine=None):
        """
        初始化基础网关
        
        Args:
            gateway_name: 网关名称
            main_engine: 主交易引擎实例
        """
        self.gatewayName = gateway_name
        self.mainTradingEngine = main_engine
        
        # 状态标志
        self.isConnected = False
        self.isAuthenticated = False
        
        # 网关配置
        self.gatewayConfig: Dict[str, Any] = {}
        
        # 连接状态
        self.connectionStatus = {
            'connected': False,
            'authenticated': False,
            'lastConnectTime': None,
            'lastDisconnectTime': None,
            'errorMessage': ''
        }
        
        # 事件回调函数
        self.eventCallbacks: Dict[str, List[Callable]] = {
            'onConnect': [],
            'onDisconnect': [],
            'onAuthenticate': [],
            'onOrder': [],
            'onTrade': [],
            'onPosition': [],
            'onAccount': [],
            'onTick': [],
            'onError': []
        }
        
        # 日志记录器
        self.logger = logging.getLogger(f"Gateway.{gateway_name}")
        
        # 初始化日志
        self._setup_logging()
        
        # 初始化网关
        self._init_gateway()
    
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
    
    def _init_gateway(self):
        """初始化网关，子类可以重写此方法"""
        self.logger.info(f"初始化网关: {self.gatewayName}")
    
    @abstractmethod
    def connect(self) -> bool:
        """
        连接网关（抽象方法）
        
        Returns:
            bool: 连接是否成功
        """
        pass
    
    @abstractmethod
    def disconnect(self) -> bool:
        """
        断开网关连接（抽象方法）
        
        Returns:
            bool: 断开是否成功
        """
        pass
    
    @abstractmethod
    def authenticate(self) -> bool:
        """
        认证网关（抽象方法）
        
        Returns:
            bool: 认证是否成功
        """
        pass
    
    @abstractmethod
    def sendOrder(self, order_data: Dict[str, Any]) -> str:
        """
        发送订单（抽象方法）
        
        Args:
            order_data: 订单数据
            
        Returns:
            str: 订单ID，如果失败则返回空字符串
        """
        pass
    
    @abstractmethod
    def cancelOrder(self, order_id: str) -> bool:
        """
        取消订单（抽象方法）
        
        Args:
            order_id: 订单ID
            
        Returns:
            bool: 取消是否成功
        """
        pass
    
    @abstractmethod
    def queryOrder(self, order_id: str) -> Optional[Dict[str, Any]]:
        """
        查询订单（抽象方法）
        
        Args:
            order_id: 订单ID
            
        Returns:
            Optional[Dict[str, Any]]: 订单信息，如果不存在则返回None
        """
        pass
    
    @abstractmethod
    def queryPosition(self, symbol: str = "") -> List[Dict[str, Any]]:
        """
        查询仓位（抽象方法）
        
        Args:
            symbol: 交易品种，如果为空则查询所有仓位
            
        Returns:
            List[Dict[str, Any]]: 仓位信息列表
        """
        pass
    
    @abstractmethod
    def queryAccount(self) -> Optional[Dict[str, Any]]:
        """
        查询账户信息（抽象方法）
        
        Returns:
            Optional[Dict[str, Any]]: 账户信息，如果查询失败则返回None
        """
        pass
    
    @abstractmethod
    def subscribeMarketData(self, symbol: str) -> bool:
        """
        订阅市场数据（抽象方法）
        
        Args:
            symbol: 交易品种
            
        Returns:
            bool: 订阅是否成功
        """
        pass
    
    @abstractmethod
    def unsubscribeMarketData(self, symbol: str) -> bool:
        """
        取消订阅市场数据（抽象方法）
        
        Args:
            symbol: 交易品种
            
        Returns:
            bool: 取消订阅是否成功
        """
        pass
    
    def setGatewayConfig(self, config: Dict[str, Any]) -> bool:
        """
        设置网关配置
        
        Args:
            config: 配置字典
            
        Returns:
            bool: 设置是否成功
        """
        try:
            self.gatewayConfig.update(config)
            self.logger.info("网关配置已更新")
            return True
            
        except Exception as e:
            self.logger.error(f"设置网关配置失败: {e}")
            return False
    
    def getGatewayConfig(self) -> Dict[str, Any]:
        """
        获取网关配置
        
        Returns:
            Dict[str, Any]: 配置字典
        """
        return self.gatewayConfig.copy()
    
    def registerCallback(self, event_type: str, callback: Callable) -> bool:
        """
        注册事件回调函数
        
        Args:
            event_type: 事件类型
            callback: 回调函数
            
        Returns:
            bool: 注册是否成功
        """
        try:
            if event_type in self.eventCallbacks:
                if callback not in self.eventCallbacks[event_type]:
                    self.eventCallbacks[event_type].append(callback)
                    self.logger.debug(f"事件回调注册成功: {event_type} -> {callback.__name__}")
                return True
            else:
                self.logger.error(f"未知的事件类型: {event_type}")
                return False
                
        except Exception as e:
            self.logger.error(f"注册事件回调失败: {e}")
            return False
    
    def unregisterCallback(self, event_type: str, callback: Callable) -> bool:
        """
        注销事件回调函数
        
        Args:
            event_type: 事件类型
            callback: 回调函数
            
        Returns:
            bool: 注销是否成功
        """
        try:
            if event_type in self.eventCallbacks:
                if callback in self.eventCallbacks[event_type]:
                    self.eventCallbacks[event_type].remove(callback)
                    self.logger.debug(f"事件回调注销成功: {event_type} -> {callback.__name__}")
                    return True
            return False
            
        except Exception as e:
            self.logger.error(f"注销事件回调失败: {e}")
            return False
    
    def _triggerEvent(self, event_type: str, event_data: Any = None):
        """
        触发事件
        
        Args:
            event_type: 事件类型
            event_data: 事件数据
        """
        try:
            if event_type in self.eventCallbacks:
                callbacks = self.eventCallbacks[event_type]
                
                for callback in callbacks:
                    try:
                        callback(event_data)
                    except Exception as e:
                        self.logger.error(f"事件回调执行异常: {event_type} -> {callback.__name__}: {e}")
            
            # 发送事件到主引擎（如果可用）
            if self.mainTradingEngine and hasattr(self.mainTradingEngine, 'eventTradingEngine'):
                self.mainTradingEngine.eventTradingEngine.putEvent(f"gateway_{event_type}", {
                    'gateway': self.gatewayName,
                    'data': event_data
                })
                
        except Exception as e:
            self.logger.error(f"触发事件失败: {event_type} - {e}")
    
    def _updateConnectionStatus(self, connected: bool, authenticated: bool = None, error_message: str = ""):
        """
        更新连接状态
        
        Args:
            connected: 是否已连接
            authenticated: 是否已认证
            error_message: 错误信息
        """
        self.connectionStatus['connected'] = connected
        self.connectionStatus['errorMessage'] = error_message
        
        if connected:
            self.connectionStatus['lastConnectTime'] = self._get_current_time()
            self.isConnected = True
        else:
            self.connectionStatus['lastDisconnectTime'] = self._get_current_time()
            self.isConnected = False
            if authenticated is not None:
                self.connectionStatus['authenticated'] = False
                self.isAuthenticated = False
        
        if authenticated is not None:
            self.connectionStatus['authenticated'] = authenticated
            self.isAuthenticated = authenticated
    
    def _get_current_time(self) -> float:
        """获取当前时间戳"""
        import time
        return time.time()
    
    def getConnectionStatus(self) -> Dict[str, Any]:
        """
        获取连接状态
        
        Returns:
            Dict[str, Any]: 连接状态字典
        """
        return self.connectionStatus.copy()
    
    def isGatewayReady(self) -> bool:
        """
        检查网关是否就绪
        
        Returns:
            bool: 网关是否就绪
        """
        return self.isConnected and self.isAuthenticated
    
    def getGatewayInfo(self) -> Dict[str, Any]:
        """
        获取网关信息
        
        Returns:
            Dict[str, Any]: 网关信息字典
        """
        return {
            'gatewayName': self.gatewayName,
            'gatewayType': self.__class__.__name__,
            'isConnected': self.isConnected,
            'isAuthenticated': self.isAuthenticated,
            'connectionStatus': self.getConnectionStatus(),
            'gatewayConfig': self.getGatewayConfig()
        }
    
    def logInfo(self, message: str):
        """记录信息日志"""
        self.logger.info(message)
    
    def logError(self, message: str):
        """记录错误日志"""
        self.logger.error(message)
    
    def logWarning(self, message: str):
        """记录警告日志"""
        self.logger.warning(message)
    
    def logDebug(self, message: str):
        """记录调试日志"""
        self.logger.debug(message)
