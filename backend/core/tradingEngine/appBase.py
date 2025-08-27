"""
基础交易应用 (Base Trading App)

从 vnpy-core 的 BaseApp 迁移而来，提供所有交易应用的基础功能。
采用更清晰的命名规范和架构设计。
"""

import logging
from typing import Optional, Any, Dict
from abc import ABC, abstractmethod


class BaseTradingApp(ABC):
    """
    基础交易应用抽象类
    
    所有具体的交易应用都应该继承此类，实现以下功能：
    - 应用生命周期管理
    - 与主引擎的交互
    - 基础配置和状态管理
    """
    
    def __init__(self, main_engine=None, app_name: str = ""):
        """
        初始化基础交易应用
        
        Args:
            main_engine: 主交易引擎实例
            app_name: 应用名称
        """
        # 主引擎引用
        self.mainTradingEngine = main_engine
        
        # 应用名称
        self.appName = app_name
        
        # 状态标志
        self.isActive = False
        
        # 应用配置
        self.appConfig: Dict[str, Any] = {}
        
        # 日志记录器
        self.logger = logging.getLogger(__name__)
        
        # 初始化日志
        self._setup_logging()
        
        # 初始化应用
        self._init_app()
    
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
    
    def _init_app(self):
        """初始化应用，子类可以重写此方法"""
        self.logger.info(f"初始化交易应用: {self.appName}")
    
    @abstractmethod
    def startApp(self) -> bool:
        """
        启动应用（抽象方法）
        
        Returns:
            bool: 启动是否成功
        """
        pass
    
    @abstractmethod
    def stopApp(self) -> bool:
        """
        停止应用（抽象方法）
        
        Returns:
            bool: 停止是否成功
        """
        pass
    
    @abstractmethod
    def closeApp(self) -> bool:
        """
        关闭应用（抽象方法）
        
        Returns:
            bool: 关闭是否成功
        """
        pass
    
    def setMainEngine(self, main_engine):
        """
        设置主引擎引用
        
        Args:
            main_engine: 主交易引擎实例
        """
        self.mainTradingEngine = main_engine
        self.logger.debug(f"设置主引擎引用: {self.appName}")
    
    def getMainEngine(self):
        """
        获取主引擎引用
        
        Returns:
            主交易引擎实例
        """
        return self.mainTradingEngine
    
    def setAppName(self, name: str):
        """
        设置应用名称
        
        Args:
            name: 应用名称
        """
        self.appName = name
        self.logger.debug(f"设置应用名称: {name}")
    
    def getAppName(self) -> str:
        """
        获取应用名称
        
        Returns:
            str: 应用名称
        """
        return self.appName
    
    def setAppConfig(self, config: Dict[str, Any]):
        """
        设置应用配置
        
        Args:
            config: 配置字典
        """
        self.appConfig.update(config)
        self.logger.debug(f"更新应用配置: {self.appName}")
    
    def getAppConfig(self) -> Dict[str, Any]:
        """
        获取应用配置
        
        Returns:
            Dict[str, Any]: 配置字典
        """
        return self.appConfig.copy()
    
    def getConfigValue(self, key: str, default: Any = None) -> Any:
        """
        获取配置值
        
        Args:
            key: 配置键
            default: 默认值
            
        Returns:
            Any: 配置值
        """
        return self.appConfig.get(key, default)
    
    def setConfigValue(self, key: str, value: Any):
        """
        设置配置值
        
        Args:
            key: 配置键
            value: 配置值
        """
        self.appConfig[key] = value
        self.logger.debug(f"设置配置值: {key} = {value}")
    
    def isAppActive(self) -> bool:
        """
        检查应用是否处于活动状态
        
        Returns:
            bool: 应用是否活动
        """
        return self.isActive
    
    def getAppStatus(self) -> Dict[str, Any]:
        """
        获取应用状态信息
        
        Returns:
            Dict[str, Any]: 状态信息字典
        """
        return {
            'appName': self.appName,
            'isActive': self.isActive,
            'hasMainEngine': self.mainTradingEngine is not None,
            'configKeys': list(self.appConfig.keys())
        }
    
    def logInfo(self, message: str):
        """
        记录信息日志
        
        Args:
            message: 日志消息
        """
        self.logger.info(f"[{self.appName}] {message}")
    
    def logError(self, message: str):
        """
        记录错误日志
        
        Args:
            message: 日志消息
        """
        self.logger.error(f"[{self.appName}] {message}")
    
    def logWarning(self, message: str):
        """
        记录警告日志
        
        Args:
            message: 日志消息
        """
        self.logger.warning(f"[{self.appName}] {message}")
    
    def logDebug(self, message: str):
        """
        记录调试日志
        
        Args:
            message: 日志消息
        """
        self.logger.debug(f"[{self.appName}] {message}")
    
    def _validate_config(self) -> bool:
        """
        验证应用配置（子类可以重写此方法）
        
        Returns:
            bool: 配置是否有效
        """
        # 基础验证：检查必要的配置项
        required_keys = self._get_required_config_keys()
        
        for key in required_keys:
            if key not in self.appConfig:
                self.logError(f"缺少必要的配置项: {key}")
                return False
        
        return True
    
    def _get_required_config_keys(self) -> list:
        """
        获取必要的配置键列表（子类可以重写此方法）
        
        Returns:
            list: 必要的配置键列表
        """
        return []
    
    def _pre_start_hook(self) -> bool:
        """
        启动前的钩子函数（子类可以重写此方法）
        
        Returns:
            bool: 是否允许启动
        """
        return True
    
    def _post_start_hook(self):
        """启动后的钩子函数（子类可以重写此方法）"""
        pass
    
    def _pre_stop_hook(self) -> bool:
        """
        停止前的钩子函数（子类可以重写此方法）
        
        Returns:
            bool: 是否允许停止
        """
        return True
    
    def _post_stop_hook(self):
        """停止后的钩子函数（子类可以重写此方法）"""
        pass
    
    def _pre_close_hook(self) -> bool:
        """
        关闭前的钩子函数（子类可以重写此方法）
        
        Returns:
            bool: 是否允许关闭
        """
        return True
    
    def _post_close_hook(self):
        """关闭后的钩子函数（子类可以重写此方法）"""
        pass
    
    def getEventEngine(self):
        """
        获取事件引擎实例
        
        Returns:
            事件引擎实例
        """
        if self.mainTradingEngine:
            return self.mainTradingEngine.eventTradingEngine
        return None
    
    def putEvent(self, event_type: str, data: Any = None) -> bool:
        """
        向事件引擎发送事件
        
        Args:
            event_type: 事件类型
            data: 事件数据
            
        Returns:
            bool: 发送是否成功
        """
        event_engine = self.getEventEngine()
        if event_engine:
            return event_engine.putEvent(event_type, data)
        else:
            self.logError("无法获取事件引擎，事件发送失败")
            return False
    
    def registerHandler(self, event_type: str, handler) -> bool:
        """
        注册事件处理器
        
        Args:
            event_type: 事件类型
            handler: 事件处理函数
            
        Returns:
            bool: 注册是否成功
        """
        event_engine = self.getEventEngine()
        if event_engine:
            return event_engine.registerHandler(event_type, handler)
        else:
            self.logError("无法获取事件引擎，处理器注册失败")
            return False
    
    def unregisterHandler(self, event_type: str, handler) -> bool:
        """
        注销事件处理器
        
        Args:
            event_type: 事件类型
            handler: 事件处理函数
            
        Returns:
            bool: 注销是否成功
        """
        event_engine = self.getEventEngine()
        if event_engine:
            return event_engine.unregisterHandler(event_type, handler)
        else:
            self.logError("无法获取事件引擎，处理器注销失败")
            return False
