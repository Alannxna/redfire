"""
VnPy集成管理器
负责VnPy系统的集成和管理
"""

import logging
import os
import sys
from pathlib import Path
from typing import Optional, Any

logger = logging.getLogger(__name__)


class VnPyIntegrationManager:
    """VnPy集成管理器"""
    
    def __init__(self):
        self.vnpy_available = False
        self.main_engine = None
        self.vnpy_core_path = None
        self.apps = {}
    
    async def initialize(self) -> bool:
        """初始化VnPy集成"""
        try:
            # 设置VnPy路径
            if not await self._setup_vnpy_paths():
                logger.warning("VnPy路径设置失败，使用模拟模式")
                return False
            
            # 初始化VnPy主引擎
            if not await self._initialize_main_engine():
                logger.warning("VnPy主引擎初始化失败，使用模拟模式")
                return False
            
            # 初始化应用
            await self._initialize_apps()
            
            self.vnpy_available = True
            logger.info("VnPy集成初始化完成")
            return True
            
        except Exception as e:
            logger.error(f"VnPy集成初始化失败: {e}")
            return False
    
    async def _setup_vnpy_paths(self) -> bool:
        """设置VnPy路径"""
        try:
            # 检查环境变量
            vnpy_core_path = os.getenv("VNPY_CORE_PATH")
            if not vnpy_core_path:
                # 尝试自动检测
                possible_paths = [
                    "../vnpy-core",
                    "../../vnpy-core", 
                    "./vnpy-core",
                    "../vnpy/vnpy"
                ]
                
                for path in possible_paths:
                    test_path = Path(path).resolve()
                    if test_path.exists() and (test_path / "__init__.py").exists():
                        vnpy_core_path = str(test_path)
                        break
            
            if not vnpy_core_path:
                logger.error("未找到VnPy核心路径")
                return False
            
            # 添加到Python路径
            vnpy_core_path = str(Path(vnpy_core_path).resolve())
            if vnpy_core_path not in sys.path:
                sys.path.insert(0, vnpy_core_path)
            
            self.vnpy_core_path = vnpy_core_path
            logger.info(f"VnPy核心路径设置为: {vnpy_core_path}")
            return True
            
        except Exception as e:
            logger.error(f"VnPy路径设置失败: {e}")
            return False
    
    async def _initialize_main_engine(self) -> bool:
        """初始化主引擎"""
        try:
            from vnpy.event import EventEngine
            from vnpy.trader.engine import MainEngine
            from vnpy.trader.ui import MainWindow, create_qapp
            
            # 创建事件引擎
            event_engine = EventEngine()
            
            # 创建主引擎
            self.main_engine = MainEngine(event_engine)
            
            # 添加网关（如果需要）
            # self.main_engine.add_gateway(CtpGateway)
            
            logger.info("VnPy主引擎初始化完成")
            return True
            
        except ImportError as e:
            logger.warning(f"VnPy主引擎导入失败: {e}")
            return False
        except Exception as e:
            logger.error(f"VnPy主引擎初始化失败: {e}")
            return False
    
    async def _initialize_apps(self) -> None:
        """初始化应用"""
        try:
            # 初始化CTA策略应用
            try:
                from vnpy_ctastrategy import CtaStrategyApp
                cta_engine = self.main_engine.add_app(CtaStrategyApp)
                self.apps["cta_strategy"] = cta_engine
                logger.info("CTA策略应用初始化完成")
            except ImportError:
                logger.warning("CTA策略应用不可用")
            
            # 初始化组合策略应用
            try:
                from vnpy_portfoliostrategy import PortfolioStrategyApp
                portfolio_engine = self.main_engine.add_app(PortfolioStrategyApp)
                self.apps["portfolio_strategy"] = portfolio_engine
                logger.info("组合策略应用初始化完成")
            except ImportError:
                logger.warning("组合策略应用不可用")
            
            # 初始化价差交易应用
            try:
                from vnpy_spreadtrading import SpreadTradingApp
                spread_engine = self.main_engine.add_app(SpreadTradingApp)
                self.apps["spread_trading"] = spread_engine
                logger.info("价差交易应用初始化完成")
            except ImportError:
                logger.warning("价差交易应用不可用")
                
        except Exception as e:
            logger.error(f"应用初始化失败: {e}")
    
    def get_app(self, app_name: str) -> Optional[Any]:
        """获取应用"""
        return self.apps.get(app_name)
    
    def get_vnpy_core_path(self) -> Optional[str]:
        """获取VnPy核心路径"""
        return self.vnpy_core_path
    
    def is_available(self) -> bool:
        """检查VnPy是否可用"""
        return self.vnpy_available
    
    async def shutdown(self) -> None:
        """关闭VnPy集成"""
        if self.main_engine:
            try:
                # 停止所有应用
                for app_name, app in self.apps.items():
                    if hasattr(app, 'close'):
                        app.close()
                
                # 关闭主引擎
                self.main_engine.close()
                logger.info("VnPy集成关闭完成")
                
            except Exception as e:
                logger.error(f"VnPy集成关闭失败: {e}")
