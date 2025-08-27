"""
引擎管理器 (Engine Manager)

负责管理所有交易引擎的生命周期，包括：
- 引擎注册和注销
- 引擎状态监控
- 引擎配置管理
- 引擎依赖管理
"""

import logging
import threading
import time
from typing import Dict, List, Optional, Any, Callable
from .baseEngine import BaseTradingEngine


class EngineManager:
    """
    引擎管理器类
    
    负责管理所有交易引擎的生命周期和状态
    """
    
    def __init__(self):
        """初始化引擎管理器"""
        # 引擎注册表
        self.registeredEngines: Dict[str, BaseTradingEngine] = {}
        
        # 引擎状态监控
        self.engineStatus: Dict[str, Dict[str, Any]] = {}
        
        # 引擎配置
        self.engineConfigs: Dict[str, Dict[str, Any]] = {}
        
        # 引擎依赖关系
        self.engineDependencies: Dict[str, List[str]] = {}
        
        # 状态监控线程
        self.monitorThread: Optional[threading.Thread] = None
        
        # 监控间隔（秒）
        self.monitorInterval = 5.0
        
        # 停止标志
        self.shouldStop = False
        
        # 日志记录器
        self.logger = logging.getLogger(__name__)
        
        # 初始化日志
        self._setup_logging()
        
        # 启动监控线程
        self._start_monitor_thread()
    
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
    
    def _start_monitor_thread(self):
        """启动监控线程"""
        self.monitorThread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitorThread.start()
        self.logger.info("引擎监控线程已启动")
    
    def _monitor_loop(self):
        """监控循环"""
        while not self.shouldStop:
            try:
                self._update_engine_status()
                time.sleep(self.monitorInterval)
            except Exception as e:
                self.logger.error(f"监控循环异常: {e}")
                time.sleep(self.monitorInterval)
    
    def _update_engine_status(self):
        """更新所有引擎状态"""
        for engine_name, engine in self.registeredEngines.items():
            try:
                status = engine.getEngineStatus()
                self.engineStatus[engine_name] = status
            except Exception as e:
                self.logger.error(f"获取引擎 {engine_name} 状态失败: {e}")
                self.engineStatus[engine_name] = {
                    'engineName': engine_name,
                    'isActive': False,
                    'error': str(e)
                }
    
    def registerEngine(self, engine: BaseTradingEngine, config: Optional[Dict[str, Any]] = None) -> bool:
        """
        注册交易引擎
        
        Args:
            engine: 交易引擎实例
            config: 引擎配置
            
        Returns:
            bool: 注册是否成功
        """
        try:
            engine_name = engine.engineName
            
            if not engine_name:
                self.logger.error("引擎名称不能为空")
                return False
            
            if engine_name in self.registeredEngines:
                self.logger.warning(f"引擎 {engine_name} 已经注册")
                return False
            
            # 注册引擎
            self.registeredEngines[engine_name] = engine
            
            # 保存配置
            if config:
                self.engineConfigs[engine_name] = config.copy()
                engine.setEngineConfig(config)
            
            # 初始化状态
            self.engineStatus[engine_name] = engine.getEngineStatus()
            
            # 初始化依赖关系
            self.engineDependencies[engine_name] = []
            
            self.logger.info(f"引擎 {engine_name} 注册成功")
            return True
            
        except Exception as e:
            self.logger.error(f"注册引擎失败: {e}")
            return False
    
    def unregisterEngine(self, engine_name: str) -> bool:
        """
        注销交易引擎
        
        Args:
            engine_name: 引擎名称
            
        Returns:
            bool: 注销是否成功
        """
        try:
            if engine_name not in self.registeredEngines:
                self.logger.warning(f"引擎 {engine_name} 未注册")
                return False
            
            # 停止引擎
            engine = self.registeredEngines[engine_name]
            if engine.isActive:
                engine.stopEngine()
            
            # 从注册表中移除
            del self.registeredEngines[engine_name]
            
            # 清理相关数据
            if engine_name in self.engineStatus:
                del self.engineStatus[engine_name]
            
            if engine_name in self.engineConfigs:
                del self.engineConfigs[engine_name]
            
            if engine_name in self.engineDependencies:
                del self.engineDependencies[engine_name]
            
            self.logger.info(f"引擎 {engine_name} 注销成功")
            return True
            
        except Exception as e:
            self.logger.error(f"注销引擎失败: {e}")
            return False
    
    def getEngine(self, engine_name: str) -> Optional[BaseTradingEngine]:
        """
        获取指定的引擎
        
        Args:
            engine_name: 引擎名称
            
        Returns:
            Optional[BaseTradingEngine]: 引擎实例，如果不存在则返回None
        """
        return self.registeredEngines.get(engine_name)
    
    def getAllEngines(self) -> Dict[str, BaseTradingEngine]:
        """
        获取所有已注册的引擎
        
        Returns:
            Dict[str, BaseTradingEngine]: 所有引擎的字典
        """
        return self.registeredEngines.copy()
    
    def startEngine(self, engine_name: str) -> bool:
        """
        启动指定的引擎
        
        Args:
            engine_name: 引擎名称
            
        Returns:
            bool: 启动是否成功
        """
        try:
            engine = self.getEngine(engine_name)
            if not engine:
                self.logger.error(f"引擎 {engine_name} 不存在")
                return False
            
            if engine.isActive:
                self.logger.warning(f"引擎 {engine_name} 已经在运行")
                return True
            
            # 检查依赖
            if not self._check_dependencies(engine_name):
                self.logger.error(f"引擎 {engine_name} 的依赖未满足")
                return False
            
            # 启动引擎
            success = engine.startEngine()
            if success:
                self.logger.info(f"引擎 {engine_name} 启动成功")
            else:
                self.logger.error(f"引擎 {engine_name} 启动失败")
            
            return success
            
        except Exception as e:
            self.logger.error(f"启动引擎 {engine_name} 失败: {e}")
            return False
    
    def stopEngine(self, engine_name: str) -> bool:
        """
        停止指定的引擎
        
        Args:
            engine_name: 引擎名称
            
        Returns:
            bool: 停止是否成功
        """
        try:
            engine = self.getEngine(engine_name)
            if not engine:
                self.logger.error(f"引擎 {engine_name} 不存在")
                return False
            
            if not engine.isActive:
                self.logger.warning(f"引擎 {engine_name} 已经停止")
                return True
            
            # 停止引擎
            success = engine.stopEngine()
            if success:
                self.logger.info(f"引擎 {engine_name} 停止成功")
            else:
                self.logger.error(f"引擎 {engine_name} 停止失败")
            
            return success
            
        except Exception as e:
            self.logger.error(f"停止引擎 {engine_name} 失败: {e}")
            return False
    
    def startAllEngines(self) -> Dict[str, bool]:
        """
        启动所有引擎
        
        Returns:
            Dict[str, bool]: 每个引擎的启动结果
        """
        results = {}
        
        for engine_name in self.registeredEngines.keys():
            results[engine_name] = self.startEngine(engine_name)
        
        return results
    
    def stopAllEngines(self) -> Dict[str, bool]:
        """
        停止所有引擎
        
        Returns:
            Dict[str, bool]: 每个引擎的停止结果
        """
        results = {}
        
        for engine_name in self.registeredEngines.keys():
            results[engine_name] = self.stopEngine(engine_name)
        
        return results
    
    def setEngineConfig(self, engine_name: str, config: Dict[str, Any]) -> bool:
        """
        设置引擎配置
        
        Args:
            engine_name: 引擎名称
            config: 配置字典
            
        Returns:
            bool: 设置是否成功
        """
        try:
            engine = self.getEngine(engine_name)
            if not engine:
                self.logger.error(f"引擎 {engine_name} 不存在")
                return False
            
            # 更新配置
            self.engineConfigs[engine_name] = config.copy()
            engine.setEngineConfig(config)
            
            self.logger.info(f"引擎 {engine_name} 配置更新成功")
            return True
            
        except Exception as e:
            self.logger.error(f"设置引擎 {engine_name} 配置失败: {e}")
            return False
    
    def getEngineConfig(self, engine_name: str) -> Optional[Dict[str, Any]]:
        """
        获取引擎配置
        
        Args:
            engine_name: 引擎名称
            
        Returns:
            Optional[Dict[str, Any]]: 引擎配置，如果不存在则返回None
        """
        return self.engineConfigs.get(engine_name)
    
    def setEngineDependency(self, engine_name: str, dependencies: List[str]) -> bool:
        """
        设置引擎依赖关系
        
        Args:
            engine_name: 引擎名称
            dependencies: 依赖的引擎名称列表
            
        Returns:
            bool: 设置是否成功
        """
        try:
            if engine_name not in self.registeredEngines:
                self.logger.error(f"引擎 {engine_name} 不存在")
                return False
            
            # 验证依赖的引擎是否存在
            for dep in dependencies:
                if dep not in self.registeredEngines:
                    self.logger.error(f"依赖引擎 {dep} 不存在")
                    return False
            
            self.engineDependencies[engine_name] = dependencies.copy()
            self.logger.info(f"引擎 {engine_name} 依赖关系设置成功: {dependencies}")
            return True
            
        except Exception as e:
            self.logger.error(f"设置引擎 {engine_name} 依赖关系失败: {e}")
            return False
    
    def _check_dependencies(self, engine_name: str) -> bool:
        """
        检查引擎依赖是否满足
        
        Args:
            engine_name: 引擎名称
            
        Returns:
            bool: 依赖是否满足
        """
        if engine_name not in self.engineDependencies:
            return True
        
        dependencies = self.engineDependencies[engine_name]
        
        for dep in dependencies:
            dep_engine = self.getEngine(dep)
            if not dep_engine or not dep_engine.isActive:
                self.logger.warning(f"引擎 {engine_name} 的依赖 {dep} 未满足")
                return False
        
        return True
    
    def getEngineStatus(self, engine_name: str) -> Optional[Dict[str, Any]]:
        """
        获取引擎状态
        
        Args:
            engine_name: 引擎名称
            
        Returns:
            Optional[Dict[str, Any]]: 引擎状态，如果不存在则返回None
        """
        return self.engineStatus.get(engine_name)
    
    def getAllEngineStatus(self) -> Dict[str, Dict[str, Any]]:
        """
        获取所有引擎状态
        
        Returns:
            Dict[str, Dict[str, Any]]: 所有引擎状态
        """
        return self.engineStatus.copy()
    
    def getActiveEngines(self) -> List[str]:
        """
        获取所有活动的引擎名称
        
        Returns:
            List[str]: 活动引擎名称列表
        """
        active_engines = []
        
        for engine_name, status in self.engineStatus.items():
            if status.get('isActive', False):
                active_engines.append(engine_name)
        
        return active_engines
    
    def getInactiveEngines(self) -> List[str]:
        """
        获取所有非活动的引擎名称
        
        Returns:
            List[str]: 非活动引擎名称列表
        """
        inactive_engines = []
        
        for engine_name, status in self.engineStatus.items():
            if not status.get('isActive', False):
                inactive_engines.append(engine_name)
        
        return inactive_engines
    
    def getManagerStatus(self) -> Dict[str, Any]:
        """
        获取管理器状态
        
        Returns:
            Dict[str, Any]: 管理器状态信息
        """
        return {
            'totalEngines': len(self.registeredEngines),
            'activeEngines': len(self.getActiveEngines()),
            'inactiveEngines': len(self.getInactiveEngines()),
            'monitorThreadAlive': self.monitorThread.is_alive() if self.monitorThread else False,
            'monitorInterval': self.monitorInterval,
            'registeredEngines': list(self.registeredEngines.keys()),
            'activeEngines': self.getActiveEngines(),
            'inactiveEngines': self.getInactiveEngines()
        }
    
    def shutdown(self):
        """关闭引擎管理器"""
        self.logger.info("正在关闭引擎管理器...")
        
        # 停止所有引擎
        self.stopAllEngines()
        
        # 设置停止标志
        self.shouldStop = True
        
        # 等待监控线程结束
        if self.monitorThread and self.monitorThread.is_alive():
            self.monitorThread.join(timeout=5.0)
        
        self.logger.info("引擎管理器已关闭")
