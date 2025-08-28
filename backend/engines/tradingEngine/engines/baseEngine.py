"""
基础引擎 (Base Engine)

engines子模块中的基础引擎类，继承自BaseTradingEngine。
提供所有具体引擎的基础实现。
"""

from ..baseEngine import BaseTradingEngine
from typing import Dict, Any, Optional


class BaseEngine(BaseTradingEngine):
    """
    基础引擎类
    
    继承自BaseTradingEngine，提供所有具体引擎的基础实现。
    子类应该重写抽象方法来实现具体的功能。
    """
    
    def __init__(self, main_engine=None, engine_name: str = ""):
        """
        初始化基础引擎
        
        Args:
            main_engine: 主交易引擎实例
            engine_name: 引擎名称
        """
        super().__init__(main_engine, engine_name)
        
        # 引擎特定的配置
        self.engineSpecificConfig: Dict[str, Any] = {}
        
        # 引擎状态
        self.engineState: Dict[str, Any] = {}
        
        # 初始化引擎特定配置
        self._init_engine_specific_config()
    
    def _init_engine_specific_config(self):
        """初始化引擎特定配置，子类可以重写此方法"""
        pass
    
    def startEngine(self) -> bool:
        """
        启动引擎
        
        Returns:
            bool: 启动是否成功
        """
        try:
            # 调用启动前钩子
            if not self._pre_start_hook():
                self.logError("启动前钩子检查失败")
                return False
            
            # 验证配置
            if not self._validate_config():
                self.logError("引擎配置验证失败")
                return False
            
            # 执行启动逻辑
            success = self._do_start_engine()
            
            if success:
                # 调用启动后钩子
                self._post_start_hook()
                self.isActive = True
                self.logInfo("引擎启动成功")
            else:
                self.logError("引擎启动失败")
            
            return success
            
        except Exception as e:
            self.logError(f"启动引擎异常: {e}")
            return False
    
    def stopEngine(self) -> bool:
        """
        停止引擎
        
        Returns:
            bool: 停止是否成功
        """
        try:
            # 调用停止前钩子
            if not self._pre_stop_hook():
                self.logError("停止前钩子检查失败")
                return False
            
            # 执行停止逻辑
            success = self._do_stop_engine()
            
            if success:
                # 调用停止后钩子
                self._post_stop_hook()
                self.isActive = False
                self.logInfo("引擎停止成功")
            else:
                self.logError("引擎停止失败")
            
            return success
            
        except Exception as e:
            self.logError(f"停止引擎异常: {e}")
            return False
    
    def closeEngine(self) -> bool:
        """
        关闭引擎
        
        Returns:
            bool: 关闭是否成功
        """
        try:
            # 调用关闭前钩子
            if not self._pre_close_hook():
                self.logError("关闭前钩子检查失败")
                return False
            
            # 先停止引擎
            if self.isActive:
                self.stopEngine()
            
            # 执行关闭逻辑
            success = self._do_close_engine()
            
            if success:
                # 调用关闭后钩子
                self._post_close_hook()
                self.logInfo("引擎关闭成功")
            else:
                self.logError("引擎关闭失败")
            
            return success
            
        except Exception as e:
            self.logError(f"关闭引擎异常: {e}")
            return False
    
    def _do_start_engine(self) -> bool:
        """
        执行启动引擎的具体逻辑（抽象方法）
        
        Returns:
            bool: 启动是否成功
        """
        # 子类必须实现此方法
        raise NotImplementedError("子类必须实现 _do_start_engine 方法")
    
    def _do_stop_engine(self) -> bool:
        """
        执行停止引擎的具体逻辑（抽象方法）
        
        Returns:
            bool: 停止是否成功
        """
        # 子类必须实现此方法
        raise NotImplementedError("子类必须实现 _do_stop_engine 方法")
    
    def _do_close_engine(self) -> bool:
        """
        执行关闭引擎的具体逻辑（抽象方法）
        
        Returns:
            bool: 关闭是否成功
        """
        # 子类必须实现此方法
        raise NotImplementedError("子类必须实现 _do_close_engine 方法")
    
    def setEngineSpecificConfig(self, config: Dict[str, Any]):
        """
        设置引擎特定配置
        
        Args:
            config: 配置字典
        """
        self.engineSpecificConfig.update(config)
        self.logDebug(f"更新引擎特定配置: {config}")
    
    def getEngineSpecificConfig(self) -> Dict[str, Any]:
        """
        获取引擎特定配置
        
        Returns:
            Dict[str, Any]: 配置字典
        """
        return self.engineSpecificConfig.copy()
    
    def setEngineState(self, key: str, value: Any):
        """
        设置引擎状态
        
        Args:
            key: 状态键
            value: 状态值
        """
        self.engineState[key] = value
        self.logDebug(f"设置引擎状态: {key} = {value}")
    
    def getEngineState(self, key: str, default: Any = None) -> Any:
        """
        获取引擎状态
        
        Args:
            key: 状态键
            default: 默认值
            
        Returns:
            Any: 状态值
        """
        return self.engineState.get(key, default)
    
    def getAllEngineState(self) -> Dict[str, Any]:
        """
        获取所有引擎状态
        
        Returns:
            Dict[str, Any]: 所有状态
        """
        return self.engineState.copy()
    
    def clearEngineState(self):
        """清空引擎状态"""
        self.engineState.clear()
        self.logDebug("引擎状态已清空")
    
    def getEngineStatus(self) -> Dict[str, Any]:
        """
        获取引擎状态信息（重写父类方法）
        
        Returns:
            Dict[str, Any]: 状态信息字典
        """
        base_status = super().getEngineStatus()
        
        # 添加引擎特定信息
        engine_status = {
            **base_status,
            'engineSpecificConfigKeys': list(self.engineSpecificConfig.keys()),
            'engineStateKeys': list(self.engineState.keys()),
            'engineType': self.__class__.__name__
        }
        
        return engine_status
    
    def _get_required_config_keys(self) -> list:
        """
        获取必要的配置键列表（子类可以重写此方法）
        
        Returns:
            list: 必要的配置键列表
        """
        # 基础引擎不需要特殊配置
        return []
    
    def _validate_engine_specific_config(self) -> bool:
        """
        验证引擎特定配置（子类可以重写此方法）
        
        Returns:
            bool: 配置是否有效
        """
        # 基础实现：总是返回True
        return True
    
    def _validate_config(self) -> bool:
        """
        验证引擎配置（重写父类方法）
        
        Returns:
            bool: 配置是否有效
        """
        # 先验证基础配置
        if not super()._validate_config():
            return False
        
        # 再验证引擎特定配置
        return self._validate_engine_specific_config()
