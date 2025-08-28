"""
基础交易引擎 (Base Trading Engine)

从 vnpy-core 的 BaseEngine 迁移而来，提供所有交易引擎的基础功能。
采用更清晰的命名规范和架构设计。
"""

import logging
from typing import Optional, Any, Dict
from abc import ABC, abstractmethod


class BaseTradingEngine(ABC):
    """
    基础交易引擎抽象类
    
    所有具体的交易引擎都应该继承此类，实现以下功能：
    - 引擎生命周期管理
    - 与主引擎的交互
    - 基础配置和状态管理
    """
    
    def __init__(self, main_engine=None, engine_name: str = ""):
        """
        初始化基础交易引擎
        
        Args:
            main_engine: 主交易引擎实例
            engine_name: 引擎名称
        """
        # 主引擎引用
        self.mainTradingEngine = main_engine
        
        # 引擎名称
        self.engineName = engine_name
        
        # 状态标志
        self.isActive = False
        
        # 引擎配置
        self.engineConfig: Dict[str, Any] = {}
        
        # 日志记录器
        self.logger = logging.getLogger(__name__)
        
        # 初始化日志
        self._setup_logging()
        
        # 初始化引擎
        self._init_engine()
    
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
    
    def _init_engine(self):
        """初始化引擎，子类可以重写此方法"""
        self.logger.info(f"初始化交易引擎: {self.engineName}")
    
    @abstractmethod
    def startEngine(self) -> bool:
        """
        启动引擎（抽象方法）
        
        Returns:
            bool: 启动是否成功
        """
        pass
    
    @abstractmethod
    def stopEngine(self) -> bool:
        """
        停止引擎（抽象方法）
        
        Returns:
            bool: 停止是否成功
        """
        pass
    
    @abstractmethod
    def closeEngine(self) -> bool:
        """
        关闭引擎（抽象方法）
        
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
        self.logger.debug(f"设置主引擎引用: {self.engineName}")
    
    def getMainEngine(self):
        """
        获取主引擎引用
        
        Returns:
            主交易引擎实例
        """
        return self.mainTradingEngine
    
    def setEngineName(self, name: str):
        """
        设置引擎名称
        
        Args:
            name: 引擎名称
        """
        self.engineName = name
        self.logger.debug(f"设置引擎名称: {name}")
    
    def getEngineName(self) -> str:
        """
        获取引擎名称
        
        Returns:
            str: 引擎名称
        """
        return self.engineName
    
    def setEngineConfig(self, config: Dict[str, Any]):
        """
        设置引擎配置
        
        Args:
            config: 配置字典
        """
        self.engineConfig.update(config)
        self.logger.debug(f"更新引擎配置: {self.engineName}")
    
    def getEngineConfig(self) -> Dict[str, Any]:
        """
        获取引擎配置
        
        Returns:
            Dict[str, Any]: 配置字典
        """
        return self.engineConfig.copy()
    
    def getConfigValue(self, key: str, default: Any = None) -> Any:
        """
        获取配置值
        
        Args:
            key: 配置键
            default: 默认值
            
        Returns:
            Any: 配置值
        """
        return self.engineConfig.get(key, default)
    
    def setConfigValue(self, key: str, value: Any):
        """
        设置配置值
        
        Args:
            key: 配置键
            value: 配置值
        """
        self.engineConfig[key] = value
        self.logger.debug(f"设置配置值: {key} = {value}")
    
    def isEngineActive(self) -> bool:
        """
        检查引擎是否处于活动状态
        
        Returns:
            bool: 引擎是否活动
        """
        return self.isActive
    
    def getEngineStatus(self) -> Dict[str, Any]:
        """
        获取引擎状态信息
        
        Returns:
            Dict[str, Any]: 状态信息字典
        """
        return {
            'engineName': self.engineName,
            'isActive': self.isActive,
            'hasMainEngine': self.mainTradingEngine is not None,
            'configKeys': list(self.engineConfig.keys())
        }
    
    def logInfo(self, message: str):
        """
        记录信息日志
        
        Args:
            message: 日志消息
        """
        self.logger.info(f"[{self.engineName}] {message}")
    
    def logError(self, message: str):
        """
        记录错误日志
        
        Args:
            message: 日志消息
        """
        self.logger.error(f"[{self.engineName}] {message}")
    
    def logWarning(self, message: str):
        """
        记录警告日志
        
        Args:
            message: 日志消息
        """
        self.logger.warning(f"[{self.engineName}] {message}")
    
    def logDebug(self, message: str):
        """
        记录调试日志
        
        Args:
            message: 日志消息
        """
        self.logger.debug(f"[{self.engineName}] {message}")
    
    def _validate_config(self) -> bool:
        """
        验证引擎配置（子类可以重写此方法）
        
        Returns:
            bool: 配置是否有效
        """
        # 基础验证：检查必要的配置项
        required_keys = self._get_required_config_keys()
        
        for key in required_keys:
            if key not in self.engineConfig:
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
