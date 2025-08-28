"""
策略管理应用 (Strategy Manager App)

负责管理交易策略，包括：
- 策略加载和注册
- 策略参数配置
- 策略执行控制
- 策略性能监控
"""

import logging
import time
import importlib
import inspect
from typing import Dict, List, Optional, Any, Callable, Type
from pathlib import Path
from ..appBase import BaseTradingApp


class StrategyInfo:
    """策略信息类"""
    
    def __init__(self, name: str, class_name: str, file_path: str, description: str = ""):
        """
        初始化策略信息
        
        Args:
            name: 策略名称
            class_name: 策略类名
            file_path: 策略文件路径
            description: 策略描述
        """
        self.name = name
        self.className = class_name
        self.filePath = file_path
        self.description = description
        self.loadTime = time.time()
        self.isLoaded = False
        self.isRunning = False
        self.errorMessage = ""
        self.parameters: Dict[str, Any] = {}
        self.performance: Dict[str, Any] = {}


class StrategyManagerApp(BaseTradingApp):
    """
    策略管理应用类
    
    负责管理所有交易策略
    """
    
    def __init__(self, main_engine=None, app_name: str = "StrategyManager"):
        """
        初始化策略管理应用
        
        Args:
            main_engine: 主交易引擎实例
            app_name: 应用名称
        """
        super().__init__(main_engine, app_name)
        
        # 策略配置
        self.strategyConfig = {
            'strategyDir': './strategies',
            'autoReload': True,
            'maxStrategies': 100,
            'defaultParameters': {},
            'performanceTracking': True
        }
        
        # 已加载的策略
        self.loadedStrategies: Dict[str, Any] = {}
        
        # 策略信息
        self.strategyInfo: Dict[str, StrategyInfo] = {}
        
        # 策略实例
        self.strategyInstances: Dict[str, Any] = {}
        
        # 策略性能监控
        self.performanceMonitor: Dict[str, Dict[str, Any]] = {}
        
        # 策略事件处理器
        self.strategyEventHandlers: Dict[str, List[Callable]] = {}
        
        # 初始化策略目录
        self._init_strategy_directory()
        
        # 扫描策略
        self._scan_strategies()
    
    def _init_strategy_directory(self):
        """初始化策略目录"""
        try:
            strategy_dir = Path(self.strategyConfig['strategyDir'])
            strategy_dir.mkdir(exist_ok=True)
            
            # 创建示例策略文件
            self._create_sample_strategy()
            
            self.logger.info("策略目录初始化完成")
            
        except Exception as e:
            self.logger.error(f"初始化策略目录失败: {e}")
    
    def _create_sample_strategy(self):
        """创建示例策略文件"""
        sample_file = Path(self.strategyConfig['strategyDir']) / "sample_strategy.py"
        
        if not sample_file.exists():
            sample_content = '''"""
示例策略 (Sample Strategy)

这是一个示例策略，展示了如何创建自定义交易策略。
"""

from typing import Dict, Any, Optional
import logging


class SampleStrategy:
    """
    示例策略类
    
    继承此类并实现必要的方法来创建自定义策略
    """
    
    def __init__(self, name: str, parameters: Dict[str, Any] = None):
        """
        初始化策略
        
        Args:
            name: 策略名称
            parameters: 策略参数
        """
        self.name = name
        self.parameters = parameters or {}
        self.logger = logging.getLogger(f"Strategy.{name}")
        self.isRunning = False
        
        # 策略状态
        self.position = 0
        self.lastPrice = 0
        self.tradeCount = 0
        
        # 初始化策略
        self._init_strategy()
    
    def _init_strategy(self):
        """初始化策略"""
        self.logger.info(f"策略 {self.name} 初始化完成")
    
    def start(self):
        """启动策略"""
        if not self.isRunning:
            self.isRunning = True
            self.logger.info(f"策略 {self.name} 已启动")
    
    def stop(self):
        """停止策略"""
        if self.isRunning:
            self.isRunning = False
            self.logger.info(f"策略 {self.name} 已停止")
    
    def onTick(self, tick_data: Dict[str, Any]):
        """
        处理行情数据
        
        Args:
            tick_data: 行情数据
        """
        if not self.isRunning:
            return
        
        # 这里实现策略逻辑
        self.logger.debug(f"收到行情数据: {tick_data}")
    
    def onTrade(self, trade_data: Dict[str, Any]):
        """
        处理成交数据
        
        Args:
            trade_data: 成交数据
        """
        if not self.isRunning:
            return
        
        # 这里实现成交处理逻辑
        self.logger.info(f"收到成交数据: {trade_data}")
        self.tradeCount += 1
    
    def onOrder(self, order_data: Dict[str, Any]):
        """
        处理订单数据
        
        Args:
            order_data: 订单数据
        """
        if not self.isRunning:
            return
        
        # 这里实现订单处理逻辑
        self.logger.info(f"收到订单数据: {order_data}")
    
    def getStatus(self) -> Dict[str, Any]:
        """
        获取策略状态
        
        Returns:
            Dict[str, Any]: 状态信息字典
        """
        return {
            'name': self.name,
            'isRunning': self.isRunning,
            'position': self.position,
            'lastPrice': self.lastPrice,
            'tradeCount': self.tradeCount,
            'parameters': self.parameters
        }
'''
            
            with open(sample_file, 'w', encoding='utf-8') as f:
                f.write(sample_content)
            
            self.logger.info("示例策略文件已创建")
    
    def _scan_strategies(self):
        """扫描策略目录"""
        try:
            strategy_dir = Path(self.strategyConfig['strategyDir'])
            if not strategy_dir.exists():
                return
            
            for item in strategy_dir.iterdir():
                if item.is_file() and item.suffix == '.py' and not item.name.startswith('__'):
                    strategy_name = item.stem
                    if strategy_name not in self.strategyInfo:
                        strategy_info = StrategyInfo(
                            name=strategy_name,
                            class_name=f"{strategy_name.capitalize()}Strategy",
                            file_path=str(item),
                            description=f"策略文件: {item.name}"
                        )
                        self.strategyInfo[strategy_name] = strategy_info
            
            self.logger.info(f"发现 {len(self.strategyInfo)} 个策略文件")
            
        except Exception as e:
            self.logger.error(f"扫描策略失败: {e}")
    
    def startApp(self) -> bool:
        """
        启动策略管理应用
        
        Returns:
            bool: 启动是否成功
        """
        try:
            if self.isActive:
                self.logger.warning("策略管理应用已经在运行")
                return True
            
            self.logger.info("正在启动策略管理应用...")
            
            # 启动策略监控
            self._start_strategy_monitoring()
            
            self.isActive = True
            self.logger.info("策略管理应用启动成功")
            return True
            
        except Exception as e:
            self.logger.error(f"启动策略管理应用失败: {e}")
            return False
    
    def stopApp(self) -> bool:
        """
        停止策略管理应用
        
        Returns:
            bool: 停止是否成功
        """
        try:
            if not self.isActive:
                self.logger.warning("策略管理应用已经停止")
                return True
            
            self.logger.info("正在停止策略管理应用...")
            
            # 停止所有策略
            self._stop_all_strategies()
            
            # 停止策略监控
            self._stop_strategy_monitoring()
            
            self.isActive = False
            self.logger.info("策略管理应用已停止")
            return True
            
        except Exception as e:
            self.logger.error(f"停止策略管理应用失败: {e}")
            return False
    
    def closeApp(self) -> bool:
        """
        关闭策略管理应用
        
        Returns:
            bool: 关闭是否成功
        """
        try:
            if self.isActive:
                self.stopApp()
            
            # 清理资源
            self._cleanup()
            
            self.logger.info("策略管理应用已关闭")
            return True
            
        except Exception as e:
            self.logger.error(f"关闭策略管理应用失败: {e}")
            return False
    
    def _start_strategy_monitoring(self):
        """启动策略监控"""
        self.logger.info("策略监控已启动")
    
    def _stop_strategy_monitoring(self):
        """停止策略监控"""
        self.logger.info("策略监控已停止")
    
    def _stop_all_strategies(self):
        """停止所有策略"""
        for strategy_name, strategy_instance in self.strategyInstances.items():
            try:
                if hasattr(strategy_instance, 'stop'):
                    strategy_instance.stop()
                    self.logger.info(f"策略 {strategy_name} 已停止")
            except Exception as e:
                self.logger.error(f"停止策略 {strategy_name} 失败: {e}")
    
    def _cleanup(self):
        """清理资源"""
        self.strategyInstances.clear()
        self.performanceMonitor.clear()
    
    def loadStrategy(self, strategy_name: str) -> bool:
        """
        加载策略
        
        Args:
            strategy_name: 策略名称
            
        Returns:
            bool: 加载是否成功
        """
        try:
            if strategy_name in self.loadedStrategies:
                self.logger.warning(f"策略 {strategy_name} 已经加载")
                return True
            
            if strategy_name not in self.strategyInfo:
                self.logger.error(f"策略 {strategy_name} 不存在")
                return False
            
            strategy_info = self.strategyInfo[strategy_name]
            
            # 动态加载策略模块
            spec = importlib.util.spec_from_file_location(strategy_name, strategy_info.filePath)
            if not spec or not spec.loader:
                raise ImportError(f"无法加载策略模块: {strategy_name}")
            
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # 查找策略类
            strategy_class = None
            for name, obj in inspect.getmembers(module):
                if inspect.isclass(obj) and name.endswith('Strategy'):
                    strategy_class = obj
                    break
            
            if not strategy_class:
                raise ImportError(f"策略模块 {strategy_name} 中未找到策略类")
            
            # 保存策略信息
            self.loadedStrategies[strategy_name] = strategy_class
            strategy_info.isLoaded = True
            strategy_info.className = strategy_class.__name__
            
            self.logger.info(f"策略 {strategy_name} 加载成功")
            return True
            
        except Exception as e:
            self.logger.error(f"加载策略 {strategy_name} 失败: {e}")
            if strategy_name in self.strategyInfo:
                self.strategyInfo[strategy_name].errorMessage = str(e)
            return False
    
    def createStrategyInstance(self, strategy_name: str, instance_name: str, parameters: Dict[str, Any] = None) -> bool:
        """
        创建策略实例
        
        Args:
            strategy_name: 策略名称
            instance_name: 实例名称
            parameters: 策略参数
            
        Returns:
            bool: 创建是否成功
        """
        try:
            if strategy_name not in self.loadedStrategies:
                if not self.loadStrategy(strategy_name):
                    return False
            
            strategy_class = self.loadedStrategies[strategy_name]
            
            # 创建策略实例
            strategy_instance = strategy_class(instance_name, parameters or {})
            
            # 保存实例
            self.strategyInstances[instance_name] = strategy_instance
            
            # 初始化性能监控
            self.performanceMonitor[instance_name] = {
                'startTime': time.time(),
                'tradeCount': 0,
                'pnl': 0.0,
                'maxDrawdown': 0.0,
                'lastUpdate': time.time()
            }
            
            self.logger.info(f"策略实例 {instance_name} 创建成功")
            return True
            
        except Exception as e:
            self.logger.error(f"创建策略实例 {instance_name} 失败: {e}")
            return False
    
    def startStrategy(self, instance_name: str) -> bool:
        """
        启动策略实例
        
        Args:
            instance_name: 实例名称
            
        Returns:
            bool: 启动是否成功
        """
        try:
            if instance_name not in self.strategyInstances:
                self.logger.error(f"策略实例 {instance_name} 不存在")
                return False
            
            strategy_instance = self.strategyInstances[instance_name]
            
            if hasattr(strategy_instance, 'start'):
                strategy_instance.start()
                
                # 更新状态
                if instance_name in self.strategyInfo:
                    self.strategyInfo[instance_name].isRunning = True
                
                self.logger.info(f"策略实例 {instance_name} 启动成功")
                return True
            else:
                self.logger.error(f"策略实例 {instance_name} 没有 start 方法")
                return False
                
        except Exception as e:
            self.logger.error(f"启动策略实例 {instance_name} 失败: {e}")
            return False
    
    def stopStrategy(self, instance_name: str) -> bool:
        """
        停止策略实例
        
        Args:
            instance_name: 实例名称
            
        Returns:
            bool: 停止是否成功
        """
        try:
            if instance_name not in self.strategyInstances:
                self.logger.error(f"策略实例 {instance_name} 不存在")
                return False
            
            strategy_instance = self.strategyInstances[instance_name]
            
            if hasattr(strategy_instance, 'stop'):
                strategy_instance.stop()
                
                # 更新状态
                if instance_name in self.strategyInfo:
                    self.strategyInfo[instance_name].isRunning = False
                
                self.logger.info(f"策略实例 {instance_name} 停止成功")
                return True
            else:
                self.logger.error(f"策略实例 {instance_name} 没有 stop 方法")
                return False
                
        except Exception as e:
            self.logger.error(f"停止策略实例 {instance_name} 失败: {e}")
            return False
    
    def removeStrategyInstance(self, instance_name: str) -> bool:
        """
        移除策略实例
        
        Args:
            instance_name: 实例名称
            
        Returns:
            bool: 移除是否成功
        """
        try:
            if instance_name not in self.strategyInstances:
                self.logger.warning(f"策略实例 {instance_name} 不存在")
                return True
            
            # 先停止策略
            self.stopStrategy(instance_name)
            
            # 移除实例
            del self.strategyInstances[instance_name]
            
            # 移除性能监控
            if instance_name in self.performanceMonitor:
                del self.performanceMonitor[instance_name]
            
            self.logger.info(f"策略实例 {instance_name} 移除成功")
            return True
            
        except Exception as e:
            self.logger.error(f"移除策略实例 {instance_name} 失败: {e}")
            return False
    
    def getStrategyInstance(self, instance_name: str) -> Optional[Any]:
        """
        获取策略实例
        
        Args:
            instance_name: 实例名称
            
        Returns:
            Optional[Any]: 策略实例，如果不存在则返回None
        """
        return self.strategyInstances.get(instance_name)
    
    def getAllStrategyInstances(self) -> Dict[str, Any]:
        """
        获取所有策略实例
        
        Returns:
            Dict[str, Any]: 所有策略实例的字典
        """
        return self.strategyInstances.copy()
    
    def updateStrategyPerformance(self, instance_name: str, performance_data: Dict[str, Any]):
        """
        更新策略性能数据
        
        Args:
            instance_name: 实例名称
            performance_data: 性能数据
        """
        if instance_name in self.performanceMonitor:
            monitor = self.performanceMonitor[instance_name]
            monitor.update(performance_data)
            monitor['lastUpdate'] = time.time()
    
    def getStrategyPerformance(self, instance_name: str) -> Dict[str, Any]:
        """
        获取策略性能数据
        
        Args:
            instance_name: 实例名称
            
        Returns:
            Dict[str, Any]: 性能数据字典
        """
        return self.performanceMonitor.get(instance_name, {}).copy()
    
    def getAllStrategyPerformance(self) -> Dict[str, Dict[str, Any]]:
        """
        获取所有策略性能数据
        
        Returns:
            Dict[str, Dict[str, Any]]: 所有策略性能数据
        """
        return {name: data.copy() for name, data in self.performanceMonitor.items()}
    
    def getStrategyList(self) -> List[Dict[str, Any]]:
        """
        获取策略列表
        
        Returns:
            List[Dict[str, Any]]: 策略信息列表
        """
        return [
            {
                'name': info.name,
                'className': info.className,
                'description': info.description,
                'isLoaded': info.isLoaded,
                'isRunning': info.isRunning,
                'loadTime': info.loadTime,
                'errorMessage': info.errorMessage
            }
            for info in self.strategyInfo.values()
        ]
    
    def getStatus(self) -> Dict[str, Any]:
        """
        获取应用状态
        
        Returns:
            Dict[str, Any]: 状态信息字典
        """
        return {
            'appName': self.appName,
            'isActive': self.isActive,
            'strategyConfig': self.strategyConfig.copy(),
            'totalStrategies': len(self.strategyInfo),
            'loadedStrategies': len(self.loadedStrategies),
            'runningInstances': len([i for i in self.strategyInstances.values() if hasattr(i, 'isRunning') and i.isRunning]),
            'strategyList': self.getStrategyList()
        }
