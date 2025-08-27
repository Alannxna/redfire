"""
VnPy策略适配器
提供与VnPy策略引擎的集成
"""

import logging
import importlib.util
import sys
from pathlib import Path
from typing import Dict, Any, Optional, Type

from backend.src.domain.strategy.entities.strategy_config import StrategyConfig
from backend.src.domain.strategy.value_objects.strategy_type import StrategyType
from backend.src.infrastructure.vnpy.vnpy_integration_manager import VnPyIntegrationManager

logger = logging.getLogger(__name__)


class VnPyStrategyAdapter:
    """VnPy策略适配器"""
    
    def __init__(self):
        self.integration_manager = VnPyIntegrationManager()
        self.vnpy_available = False
        
        # 策略引擎
        self.cta_engine = None
        self.portfolio_engine = None
        self.spread_engine = None
    
    async def initialize(self) -> None:
        """初始化适配器"""
        logger.info("VnPy策略适配器初始化开始")
        
        try:
            # 初始化VnPy集成
            self.vnpy_available = await self.integration_manager.initialize()
            
            if self.vnpy_available:
                # 获取各种策略引擎
                self.cta_engine = self.integration_manager.get_app("cta_strategy")
                self.portfolio_engine = self.integration_manager.get_app("portfolio_strategy")
                self.spread_engine = self.integration_manager.get_app("spread_trading")
                
                logger.info("VnPy策略引擎初始化完成")
            else:
                logger.warning("VnPy不可用，将使用模拟模式")
                
        except Exception as e:
            logger.error(f"VnPy策略适配器初始化失败: {e}")
            self.vnpy_available = False
    
    def load_strategy_class(self, strategy_class_name: str, strategy_type: StrategyType) -> Optional[Type]:
        """加载策略类"""
        if not self.vnpy_available:
            return self._get_mock_strategy_class(strategy_class_name)
        
        try:
            if strategy_type == StrategyType.CTA:
                return self._load_cta_strategy_class(strategy_class_name)
            elif strategy_type == StrategyType.PORTFOLIO:
                return self._load_portfolio_strategy_class(strategy_class_name)
            elif strategy_type == StrategyType.SPREAD:
                return self._load_spread_strategy_class(strategy_class_name)
            else:
                return self._load_custom_strategy_class(strategy_class_name)
                
        except Exception as e:
            logger.error(f"策略类加载失败 {strategy_class_name}: {e}")
            return None
    
    def _load_cta_strategy_class(self, strategy_class_name: str) -> Optional[Type]:
        """加载CTA策略类"""
        try:
            # 尝试从vnpy-core导入策略
            vnpy_core_path = self.integration_manager.get_vnpy_core_path()
            if vnpy_core_path:
                # 构建策略文件路径
                strategy_file = Path(vnpy_core_path) / "app" / "cta_strategy" / "strategies" / f"{strategy_class_name.lower()}.py"
                
                if strategy_file.exists():
                    # 动态导入策略模块
                    spec = importlib.util.spec_from_file_location(strategy_class_name, strategy_file)
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    
                    # 获取策略类
                    strategy_class = getattr(module, strategy_class_name, None)
                    if strategy_class:
                        return strategy_class
            
            # 尝试从已安装的vnpy包导入
            from vnpy_ctastrategy import CtaTemplate
            
            # 这里可以添加更多策略类的导入逻辑
            # 目前返回基础模板
            return CtaTemplate
            
        except ImportError as e:
            logger.warning(f"CTA策略导入失败: {e}")
            return None
    
    def _load_portfolio_strategy_class(self, strategy_class_name: str) -> Optional[Type]:
        """加载组合策略类"""
        try:
            from vnpy_portfoliostrategy import StrategyTemplate
            return StrategyTemplate
        except ImportError:
            return None
    
    def _load_spread_strategy_class(self, strategy_class_name: str) -> Optional[Type]:
        """加载价差策略类"""
        try:
            from vnpy_spreadtrading import SpreadStrategyTemplate
            return SpreadStrategyTemplate
        except ImportError:
            return None
    
    def _load_custom_strategy_class(self, strategy_class_name: str) -> Optional[Type]:
        """加载自定义策略类"""
        # 从用户自定义目录加载策略
        custom_path = Path("./custom_strategies")
        if custom_path.exists():
            for py_file in custom_path.glob("*.py"):
                try:
                    spec = importlib.util.spec_from_file_location(py_file.stem, py_file)
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    
                    strategy_class = getattr(module, strategy_class_name, None)
                    if strategy_class:
                        return strategy_class
                except Exception as e:
                    logger.error(f"自定义策略加载失败 {py_file}: {e}")
        
        return None
    
    def _get_mock_strategy_class(self, strategy_class_name: str) -> Type:
        """获取模拟策略类"""
        class MockStrategy:
            def __init__(self, strategy_engine, strategy_name: str, vt_symbol: str, setting: dict):
                self.strategy_engine = strategy_engine
                self.strategy_name = strategy_name
                self.vt_symbol = vt_symbol
                self.setting = setting
                self.trading = False
                self.pos = 0
                self.parameters = []
                self.variables = []
                
            def on_init(self):
                """初始化"""
                pass
                
            def on_start(self):
                """启动"""
                self.trading = True
                
            def on_stop(self):
                """停止"""
                self.trading = False
                
            def on_tick(self, tick):
                """Tick推送"""
                pass
                
            def on_bar(self, bar):
                """K线推送"""
                pass
                
            def on_trade(self, trade):
                """成交推送"""
                pass
                
            def on_order(self, order):
                """委托推送"""
                pass
                
            def on_stop_order(self, stop_order):
                """停止单推送"""
                pass
        
        return MockStrategy
    
    async def add_strategy(self, config: StrategyConfig) -> bool:
        """添加策略"""
        try:
            # 加载策略类
            strategy_class = self.load_strategy_class(config.strategy_class, config.strategy_type)
            if not strategy_class:
                logger.error(f"策略类加载失败: {config.strategy_class}")
                return False
            
            # 根据策略类型添加到相应引擎
            if config.strategy_type == StrategyType.CTA and self.cta_engine:
                for symbol in config.symbol_list:
                    self.cta_engine.add_strategy(
                        class_name=config.strategy_class,
                        strategy_name=f"{config.strategy_name}_{symbol}",
                        vt_symbol=symbol,
                        setting=config.parameters
                    )
            elif config.strategy_type == StrategyType.PORTFOLIO and self.portfolio_engine:
                self.portfolio_engine.add_strategy(
                    class_name=config.strategy_class,
                    strategy_name=config.strategy_name,
                    setting=config.parameters
                )
            elif config.strategy_type == StrategyType.SPREAD and self.spread_engine:
                # 价差交易策略需要特殊处理
                pass
            
            return True
            
        except Exception as e:
            logger.error(f"策略添加失败: {e}")
            return False
    
    async def start_strategy(self, strategy_name: str, strategy_type: StrategyType) -> bool:
        """启动策略"""
        try:
            if strategy_type == StrategyType.CTA and self.cta_engine:
                self.cta_engine.start_strategy(strategy_name)
            elif strategy_type == StrategyType.PORTFOLIO and self.portfolio_engine:
                self.portfolio_engine.start_strategy(strategy_name)
            elif strategy_type == StrategyType.SPREAD and self.spread_engine:
                self.spread_engine.start_strategy(strategy_name)
            
            return True
            
        except Exception as e:
            logger.error(f"策略启动失败 {strategy_name}: {e}")
            return False
    
    async def stop_strategy(self, strategy_name: str, strategy_type: StrategyType) -> bool:
        """停止策略"""
        try:
            if strategy_type == StrategyType.CTA and self.cta_engine:
                self.cta_engine.stop_strategy(strategy_name)
            elif strategy_type == StrategyType.PORTFOLIO and self.portfolio_engine:
                self.portfolio_engine.stop_strategy(strategy_name)
            elif strategy_type == StrategyType.SPREAD and self.spread_engine:
                self.spread_engine.stop_strategy(strategy_name)
            
            return True
            
        except Exception as e:
            logger.error(f"策略停止失败 {strategy_name}: {e}")
            return False
    
    def get_strategy_data(self, strategy_name: str, strategy_type: StrategyType) -> Dict[str, Any]:
        """获取策略数据"""
        try:
            if strategy_type == StrategyType.CTA and self.cta_engine:
                return self.cta_engine.get_strategy_data(strategy_name)
            elif strategy_type == StrategyType.PORTFOLIO and self.portfolio_engine:
                return self.portfolio_engine.get_strategy_data(strategy_name)
            elif strategy_type == StrategyType.SPREAD and self.spread_engine:
                return self.spread_engine.get_strategy_data(strategy_name)
        except:
            pass
        
        return {}
