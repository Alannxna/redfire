"""
VnPy官方引擎适配器

提供VnPy官方引擎与自定义交易引擎的统一集成层，确保两者可以无缝协作。
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any, Callable
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

from ..eventEngine import EventTradingEngine
from ..mainEngine import MainTradingEngine


class VnPyIntegrationMode(Enum):
    """VnPy集成模式"""
    STANDALONE = "standalone"      # 独立模式，使用VnPy官方引擎
    HYBRID = "hybrid"             # 混合模式，集成到自定义引擎
    ADAPTER = "adapter"           # 适配器模式，作为网关使用


@dataclass
class VnPyConfig:
    """VnPy配置"""
    mode: VnPyIntegrationMode = VnPyIntegrationMode.HYBRID
    vnpy_path: Optional[str] = None
    data_folder: str = ".vntrader"
    apps: List[str] = None
    gateways: List[str] = None
    auto_connect: bool = False
    log_level: str = "INFO"
    
    def __post_init__(self):
        if self.apps is None:
            self.apps = ["CtaStrategy", "PortfolioStrategy", "SpreadTrading"]
        if self.gateways is None:
            self.gateways = []


class VnPyEngineAdapter:
    """
    VnPy引擎适配器
    
    负责在自定义交易引擎和VnPy官方引擎之间建立桥梁，
    确保两者可以协同工作而不产生冲突。
    """
    
    def __init__(self, main_engine: MainTradingEngine, config: VnPyConfig):
        self.main_engine = main_engine
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # VnPy组件
        self.vnpy_main_engine = None
        self.vnpy_event_engine = None
        self.vnpy_apps: Dict[str, Any] = {}
        self.vnpy_gateways: Dict[str, Any] = {}
        
        # 适配器状态
        self.is_initialized = False
        self.is_running = False
        
        # 事件映射
        self.event_mappings: Dict[str, str] = {}
        self.event_handlers: Dict[str, List[Callable]] = {}
        
        # 初始化事件映射
        self._setup_event_mappings()
    
    def _setup_event_mappings(self):
        """设置事件映射"""
        # VnPy事件类型到自定义事件类型的映射
        self.event_mappings = {
            # 交易事件
            "eOrder": "order_update",
            "eTrade": "trade_update", 
            "ePosition": "position_update",
            "eAccount": "account_update",
            
            # 行情事件
            "eTick": "tick_data",
            "eBar": "bar_data",
            
            # 策略事件
            "eStrategyLog": "strategy_log",
            "eStrategyUpdate": "strategy_update",
            
            # 系统事件
            "eGatewayLog": "gateway_log",
            "eGatewayUpdate": "gateway_update"
        }
    
    async def initialize(self) -> bool:
        """初始化VnPy适配器"""
        try:
            self.logger.info("初始化VnPy引擎适配器...")
            
            # 设置VnPy路径
            if not await self._setup_vnpy_environment():
                return False
            
            # 创建VnPy引擎
            if not await self._create_vnpy_engines():
                return False
            
            # 设置事件桥接
            await self._setup_event_bridge()
            
            # 初始化应用
            await self._initialize_vnpy_apps()
            
            # 初始化网关
            await self._initialize_vnpy_gateways()
            
            self.is_initialized = True
            self.logger.info("VnPy引擎适配器初始化完成")
            return True
            
        except Exception as e:
            self.logger.error(f"VnPy适配器初始化失败: {e}")
            return False
    
    async def _setup_vnpy_environment(self) -> bool:
        """设置VnPy环境"""
        try:
            import sys
            from pathlib import Path
            
            # 添加VnPy路径到Python路径
            if self.config.vnpy_path:
                vnpy_path = Path(self.config.vnpy_path).resolve()
                if vnpy_path.exists():
                    if str(vnpy_path) not in sys.path:
                        sys.path.insert(0, str(vnpy_path))
                    self.logger.info(f"VnPy路径已设置: {vnpy_path}")
                else:
                    self.logger.warning(f"VnPy路径不存在: {vnpy_path}")
            
            # 设置数据目录
            data_folder = Path(self.config.data_folder)
            data_folder.mkdir(parents=True, exist_ok=True)
            
            return True
            
        except Exception as e:
            self.logger.error(f"VnPy环境设置失败: {e}")
            return False
    
    async def _create_vnpy_engines(self) -> bool:
        """创建VnPy引擎"""
        try:
            # 导入VnPy模块
            from vnpy.event import EventEngine
            from vnpy.trader.engine import MainEngine
            
            # 创建VnPy事件引擎
            self.vnpy_event_engine = EventEngine()
            
            # 创建VnPy主引擎
            self.vnpy_main_engine = MainEngine(self.vnpy_event_engine)
            
            self.logger.info("VnPy引擎创建成功")
            return True
            
        except ImportError as e:
            self.logger.error(f"VnPy模块导入失败: {e}")
            return False
        except Exception as e:
            self.logger.error(f"VnPy引擎创建失败: {e}")
            return False
    
    async def _setup_event_bridge(self):
        """设置事件桥接"""
        try:
            # 注册VnPy事件到自定义事件引擎的桥接
            for vnpy_event, custom_event in self.event_mappings.items():
                self.vnpy_event_engine.register(
                    vnpy_event,
                    lambda event, ce=custom_event: self._forward_vnpy_event(event, ce)
                )
            
            # 注册自定义事件到VnPy事件引擎的桥接
            for custom_event, vnpy_event in self.event_mappings.items():
                self.main_engine.eventTradingEngine.registerHandler(
                    custom_event,
                    lambda data, ve=vnpy_event: self._forward_custom_event(data, ve)
                )
            
            self.logger.info("事件桥接设置完成")
            
        except Exception as e:
            self.logger.error(f"事件桥接设置失败: {e}")
    
    def _forward_vnpy_event(self, vnpy_event, custom_event_type: str):
        """转发VnPy事件到自定义事件引擎"""
        try:
            # 转换事件数据格式
            event_data = self._convert_vnpy_event_data(vnpy_event)
            
            # 发送到自定义事件引擎
            self.main_engine.eventTradingEngine.putEvent(custom_event_type, event_data)
            
        except Exception as e:
            self.logger.error(f"转发VnPy事件失败: {e}")
    
    def _forward_custom_event(self, event_data, vnpy_event_type: str):
        """转发自定义事件到VnPy事件引擎"""
        try:
            # 转换事件数据格式
            vnpy_event_data = self._convert_custom_event_data(event_data)
            
            # 发送到VnPy事件引擎
            if self.vnpy_event_engine:
                from vnpy.event import Event
                vnpy_event = Event(vnpy_event_type, vnpy_event_data)
                self.vnpy_event_engine.put(vnpy_event)
            
        except Exception as e:
            self.logger.error(f"转发自定义事件失败: {e}")
    
    def _convert_vnpy_event_data(self, vnpy_event) -> Dict[str, Any]:
        """转换VnPy事件数据格式"""
        try:
            # 基础转换逻辑
            if hasattr(vnpy_event, 'data'):
                data = vnpy_event.data
                if hasattr(data, '__dict__'):
                    return data.__dict__
                else:
                    return {'data': data}
            else:
                return {'event': str(vnpy_event)}
        except Exception:
            return {'raw_event': str(vnpy_event)}
    
    def _convert_custom_event_data(self, event_data) -> Any:
        """转换自定义事件数据格式"""
        try:
            # 简单转换，VnPy通常接受字典或对象
            if isinstance(event_data, dict):
                return event_data
            else:
                return {'data': event_data}
        except Exception:
            return event_data
    
    async def _initialize_vnpy_apps(self):
        """初始化VnPy应用"""
        for app_name in self.config.apps:
            try:
                app_module = None
                
                # 导入应用模块
                if app_name == "CtaStrategy":
                    from vnpy_ctastrategy import CtaStrategyApp
                    app_module = CtaStrategyApp
                elif app_name == "PortfolioStrategy":
                    from vnpy_portfoliostrategy import PortfolioStrategyApp
                    app_module = PortfolioStrategyApp
                elif app_name == "SpreadTrading":
                    from vnpy_spreadtrading import SpreadTradingApp
                    app_module = SpreadTradingApp
                elif app_name == "AlgoTrading":
                    from vnpy_algotrading import AlgoTradingApp
                    app_module = AlgoTradingApp
                elif app_name == "DataManager":
                    from vnpy_datamanager import DataManagerApp
                    app_module = DataManagerApp
                elif app_name == "RiskManager":
                    from vnpy_riskmanager import RiskManagerApp
                    app_module = RiskManagerApp
                
                if app_module:
                    # 添加应用到VnPy引擎
                    app_engine = self.vnpy_main_engine.add_app(app_module)
                    self.vnpy_apps[app_name] = app_engine
                    self.logger.info(f"VnPy应用 {app_name} 初始化成功")
                else:
                    self.logger.warning(f"未知的VnPy应用: {app_name}")
                    
            except ImportError:
                self.logger.warning(f"VnPy应用 {app_name} 不可用")
            except Exception as e:
                self.logger.error(f"VnPy应用 {app_name} 初始化失败: {e}")
    
    async def _initialize_vnpy_gateways(self):
        """初始化VnPy网关"""
        for gateway_name in self.config.gateways:
            try:
                gateway_module = None
                
                # 导入网关模块
                if gateway_name == "CTP":
                    from vnpy_ctp import CtpGateway
                    gateway_module = CtpGateway
                elif gateway_name == "CTPMini":
                    from vnpy_ctpmini import CtpminiGateway
                    gateway_module = CtpminiGateway
                elif gateway_name == "CTPTest":
                    from vnpy_ctptest import CtptestGateway
                    gateway_module = CtptestGateway
                elif gateway_name == "XTP":
                    from vnpy_xtp import XtpGateway
                    gateway_module = XtpGateway
                elif gateway_name == "OES":
                    from vnpy_oes import OesGateway
                    gateway_module = OesGateway
                elif gateway_name == "IB":
                    from vnpy_ib import IbGateway
                    gateway_module = IbGateway
                elif gateway_name == "Binance":
                    from vnpy_binance import BinanceGateway
                    gateway_module = BinanceGateway
                
                if gateway_module:
                    # 添加网关到VnPy引擎
                    self.vnpy_main_engine.add_gateway(gateway_module)
                    self.vnpy_gateways[gateway_name] = gateway_module
                    self.logger.info(f"VnPy网关 {gateway_name} 添加成功")
                else:
                    self.logger.warning(f"未知的VnPy网关: {gateway_name}")
                    
            except ImportError:
                self.logger.warning(f"VnPy网关 {gateway_name} 不可用")
            except Exception as e:
                self.logger.error(f"VnPy网关 {gateway_name} 初始化失败: {e}")
    
    async def start(self) -> bool:
        """启动VnPy适配器"""
        try:
            if not self.is_initialized:
                self.logger.error("VnPy适配器未初始化")
                return False
            
            if self.is_running:
                self.logger.warning("VnPy适配器已经运行")
                return True
            
            self.logger.info("启动VnPy适配器...")
            
            # 启动VnPy事件引擎
            if self.vnpy_event_engine:
                self.vnpy_event_engine.start()
            
            # 自动连接网关
            if self.config.auto_connect:
                await self._auto_connect_gateways()
            
            self.is_running = True
            self.logger.info("VnPy适配器启动成功")
            return True
            
        except Exception as e:
            self.logger.error(f"VnPy适配器启动失败: {e}")
            return False
    
    async def stop(self) -> bool:
        """停止VnPy适配器"""
        try:
            if not self.is_running:
                self.logger.warning("VnPy适配器未运行")
                return True
            
            self.logger.info("停止VnPy适配器...")
            
            # 停止所有网关连接
            await self._disconnect_all_gateways()
            
            # 停止VnPy事件引擎
            if self.vnpy_event_engine:
                self.vnpy_event_engine.stop()
            
            # 关闭VnPy主引擎
            if self.vnpy_main_engine:
                self.vnpy_main_engine.close()
            
            self.is_running = False
            self.logger.info("VnPy适配器已停止")
            return True
            
        except Exception as e:
            self.logger.error(f"VnPy适配器停止失败: {e}")
            return False
    
    async def _auto_connect_gateways(self):
        """自动连接网关"""
        # 这里可以实现自动连接逻辑
        # 从配置文件读取连接参数并建立连接
        pass
    
    async def _disconnect_all_gateways(self):
        """断开所有网关连接"""
        if self.vnpy_main_engine:
            try:
                # 断开所有网关连接
                for gateway_name in self.vnpy_gateways:
                    self.vnpy_main_engine.disconnect(gateway_name)
                    self.logger.info(f"网关 {gateway_name} 已断开")
            except Exception as e:
                self.logger.error(f"断开网关连接失败: {e}")
    
    def get_vnpy_app(self, app_name: str) -> Optional[Any]:
        """获取VnPy应用实例"""
        return self.vnpy_apps.get(app_name)
    
    def get_vnpy_main_engine(self) -> Optional[Any]:
        """获取VnPy主引擎实例"""
        return self.vnpy_main_engine
    
    def get_status(self) -> Dict[str, Any]:
        """获取适配器状态"""
        return {
            'is_initialized': self.is_initialized,
            'is_running': self.is_running,
            'mode': self.config.mode.value,
            'apps': list(self.vnpy_apps.keys()),
            'gateways': list(self.vnpy_gateways.keys()),
            'vnpy_available': self.vnpy_main_engine is not None
        }
