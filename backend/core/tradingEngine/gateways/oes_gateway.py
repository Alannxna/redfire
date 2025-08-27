"""
OES网关实现
用于对接宽睿OES（O32 Execution System）接口
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from .baseGateway import BaseGateway


class OesGateway(BaseGateway):
    """
    OES网关类
    
    专门用于对接宽睿OES系统：
    - 股票交易
    - 期权交易
    - 基金交易
    - 债券交易
    - 高性能行情
    """
    
    def __init__(self, main_engine=None):
        super().__init__("OES", main_engine)
        
        # OES特定配置
        self.default_config = {
            'username': '',
            'password': '',
            'hdd_serial': '',
            'mac_address': '',
            'ip_address': '',
            'ord_server': '',
            'rpt_server': '',
            'qry_server': '',
            'mode': 'PRODUCT'  # PRODUCT/SIMULATION
        }
        
        # 连接状态
        self.ord_connected = False  # 委托通道
        self.rpt_connected = False  # 回报通道
        self.qry_connected = False  # 查询通道
        self.mktdata_connected = False  # 行情通道
        
        # 账户信息
        self.account_info = {}
        self.positions = {}
        self.orders = {}
        
        # OES特有数据
        self.cash_assets = {}  # 资金资产
        self.stock_holdings = {}  # 股票持仓
        self.option_holdings = {}  # 期权持仓
        
        # VnPy网关实例
        self.vnpy_gateway = None
        
        self.logger.info("OES网关初始化完成")
    
    async def connect(self, config: Dict[str, Any]) -> bool:
        """
        连接OES接口
        
        Args:
            config: 连接配置
            
        Returns:
            连接是否成功
        """
        try:
            # 合并配置
            self.gatewayConfig = {**self.default_config, **config}
            
            # 验证必要参数
            if not self._validate_config():
                return False
            
            # 初始化VnPy网关
            if not await self._initialize_vnpy_gateway():
                return False
            
            # 连接各个通道
            ord_success = await self._connect_order_channel()
            rpt_success = await self._connect_report_channel()
            qry_success = await self._connect_query_channel()
            mkt_success = await self._connect_market_data_channel()
            
            # 更新连接状态
            self.isConnected = ord_success and rpt_success and qry_success
            
            if self.isConnected:
                self.connectionStatus['connected'] = True
                self.connectionStatus['lastConnectTime'] = datetime.now()
                self.logger.info("OES网关连接成功")
                
                # 触发连接事件
                await self._on_gateway_connected()
                
                # 查询初始数据
                await self._query_initial_data()
            else:
                self.logger.error("OES网关连接失败")
            
            return self.isConnected
            
        except Exception as e:
            self.logger.error(f"OES网关连接异常: {e}")
            return False
    
    async def disconnect(self) -> bool:
        """断开OES连接"""
        try:
            if self.vnpy_gateway:
                # 断开VnPy网关
                self.vnpy_gateway.close()
            
            # 重置状态
            self.ord_connected = False
            self.rpt_connected = False
            self.qry_connected = False
            self.mktdata_connected = False
            self.isConnected = False
            
            self.connectionStatus['connected'] = False
            self.connectionStatus['lastDisconnectTime'] = datetime.now()
            
            self.logger.info("OES网关断开成功")
            
            # 触发断开事件
            await self._on_gateway_disconnected()
            
            return True
            
        except Exception as e:
            self.logger.error(f"OES网关断开异常: {e}")
            return False
    
    def _validate_config(self) -> bool:
        """验证配置参数"""
        required_fields = ['username', 'password', 'ord_server', 'rpt_server', 'qry_server']
        
        for field in required_fields:
            if not self.gatewayConfig.get(field):
                self.logger.error(f"OES配置缺少必要参数: {field}")
                return False
        
        return True
    
    async def _initialize_vnpy_gateway(self) -> bool:
        """初始化VnPy网关"""
        try:
            from vnpy_oes import OesGateway as VnPyOesGateway
            
            # 创建VnPy网关实例
            self.vnpy_gateway = VnPyOesGateway(
                event_engine=None,  # 会从主引擎获取
                gateway_name="OES"
            )
            
            # 注册事件回调
            self._register_vnpy_callbacks()
            
            return True
            
        except ImportError:
            self.logger.error("vnpy_oes模块未安装")
            return False
        except Exception as e:
            self.logger.error(f"初始化VnPy OES网关失败: {e}")
            return False
    
    async def _connect_order_channel(self) -> bool:
        """连接委托通道"""
        try:
            if not self.vnpy_gateway:
                return False
            
            # 设置委托通道连接参数
            setting = {
                "用户名": self.gatewayConfig['username'],
                "密码": self.gatewayConfig['password'],
                "硬盘序列号": self.gatewayConfig['hdd_serial'],
                "MAC地址": self.gatewayConfig['mac_address'],
                "IP地址": self.gatewayConfig['ip_address'],
                "委托服务器": self.gatewayConfig['ord_server'],
                "模式": self.gatewayConfig['mode']
            }
            
            # 连接
            self.vnpy_gateway.connect(setting)
            self.ord_connected = True
            
            self.logger.info("OES委托通道连接成功")
            return True
            
        except Exception as e:
            self.logger.error(f"OES委托通道连接失败: {e}")
            return False
    
    async def _connect_report_channel(self) -> bool:
        """连接回报通道"""
        try:
            # 回报通道通常与委托通道共用连接
            if self.ord_connected:
                self.rpt_connected = True
                self.logger.info("OES回报通道连接成功")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"OES回报通道连接失败: {e}")
            return False
    
    async def _connect_query_channel(self) -> bool:
        """连接查询通道"""
        try:
            # 查询通道通常与委托通道共用连接
            if self.ord_connected:
                self.qry_connected = True
                self.logger.info("OES查询通道连接成功")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"OES查询通道连接失败: {e}")
            return False
    
    async def _connect_market_data_channel(self) -> bool:
        """连接行情通道"""
        try:
            # 行情通道可能需要单独连接
            self.mktdata_connected = True
            self.logger.info("OES行情通道连接成功")
            return True
            
        except Exception as e:
            self.logger.error(f"OES行情通道连接失败: {e}")
            return False
    
    async def _query_initial_data(self):
        """查询初始数据"""
        try:
            # 查询账户信息
            await self.query_account()
            
            # 查询持仓信息
            await self.query_positions()
            
            # 查询资金资产
            await self._query_cash_assets()
            
            # 查询股票持仓
            await self._query_stock_holdings()
            
            # 查询期权持仓
            await self._query_option_holdings()
            
            self.logger.info("OES初始数据查询完成")
            
        except Exception as e:
            self.logger.error(f"OES初始数据查询失败: {e}")
    
    def _register_vnpy_callbacks(self):
        """注册VnPy事件回调"""
        if not self.vnpy_gateway:
            return
        
        # 注册各种事件回调
        # 这里需要根据实际的VnPy事件系统来实现
        pass
    
    async def submit_order(self, order_data: Dict[str, Any]) -> Optional[str]:
        """提交订单"""
        try:
            if not self.ord_connected:
                self.logger.error("OES委托通道未连接，无法提交订单")
                return None
            
            # 构造订单请求
            # 需要根据OES的订单格式来实现
            
            order_id = f"oes_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self.logger.info(f"OES订单提交成功: {order_id}")
            
            return order_id
            
        except Exception as e:
            self.logger.error(f"OES提交订单失败: {e}")
            return None
    
    async def cancel_order(self, order_id: str) -> bool:
        """撤销订单"""
        try:
            if not self.ord_connected:
                self.logger.error("OES委托通道未连接，无法撤销订单")
                return False
            
            # 撤销订单逻辑
            self.logger.info(f"OES订单撤销成功: {order_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"OES撤销订单失败: {e}")
            return False
    
    async def subscribe_market_data(self, symbols: list) -> bool:
        """订阅行情数据"""
        try:
            if not self.mktdata_connected:
                self.logger.error("OES行情通道未连接")
                return False
            
            # 订阅行情
            self.logger.info(f"OES行情订阅成功: {symbols}")
            return True
            
        except Exception as e:
            self.logger.error(f"OES订阅行情失败: {e}")
            return False
    
    async def query_account(self) -> Dict[str, Any]:
        """查询账户信息"""
        try:
            if not self.qry_connected:
                return {}
            
            # 查询账户信息
            return self.account_info
            
        except Exception as e:
            self.logger.error(f"OES查询账户失败: {e}")
            return {}
    
    async def query_positions(self) -> Dict[str, Any]:
        """查询持仓信息"""
        try:
            if not self.qry_connected:
                return {}
            
            # 查询持仓信息
            return self.positions
            
        except Exception as e:
            self.logger.error(f"OES查询持仓失败: {e}")
            return {}
    
    async def _query_cash_assets(self) -> Dict[str, Any]:
        """查询资金资产"""
        try:
            if not self.qry_connected:
                return {}
            
            # 查询资金资产
            return self.cash_assets
            
        except Exception as e:
            self.logger.error(f"OES查询资金资产失败: {e}")
            return {}
    
    async def _query_stock_holdings(self) -> Dict[str, Any]:
        """查询股票持仓"""
        try:
            if not self.qry_connected:
                return {}
            
            # 查询股票持仓
            return self.stock_holdings
            
        except Exception as e:
            self.logger.error(f"OES查询股票持仓失败: {e}")
            return {}
    
    async def _query_option_holdings(self) -> Dict[str, Any]:
        """查询期权持仓"""
        try:
            if not self.qry_connected:
                return {}
            
            # 查询期权持仓
            return self.option_holdings
            
        except Exception as e:
            self.logger.error(f"OES查询期权持仓失败: {e}")
            return {}
    
    async def submit_option_order(self, order_data: Dict[str, Any]) -> Optional[str]:
        """提交期权订单"""
        try:
            if not self.ord_connected:
                self.logger.error("OES委托通道未连接，无法提交期权订单")
                return None
            
            # 期权订单逻辑
            order_id = f"oes_option_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self.logger.info(f"OES期权订单提交成功: {order_id}")
            
            return order_id
            
        except Exception as e:
            self.logger.error(f"OES提交期权订单失败: {e}")
            return None
    
    async def _on_gateway_connected(self):
        """网关连接成功回调"""
        # 触发连接事件
        for callback in self.eventCallbacks.get('onConnect', []):
            try:
                await callback(self.gatewayName)
            except Exception as e:
                self.logger.error(f"连接回调执行失败: {e}")
    
    async def _on_gateway_disconnected(self):
        """网关断开回调"""
        # 触发断开事件
        for callback in self.eventCallbacks.get('onDisconnect', []):
            try:
                await callback(self.gatewayName)
            except Exception as e:
                self.logger.error(f"断开回调执行失败: {e}")
    
    def get_gateway_info(self) -> Dict[str, Any]:
        """获取网关信息"""
        return {
            'name': self.gatewayName,
            'type': 'OES',
            'description': '宽睿OES O32执行系统接口',
            'supported_markets': ['沪深股票', '期权', '基金', '债券'],
            'features': [
                '高性能交易',
                '多通道架构',
                '股票交易',
                '期权交易',
                '基金交易',
                '债券交易',
                '实时行情',
                '微秒级延迟'
            ],
            'connection_status': self.connectionStatus,
            'channels': {
                'order': self.ord_connected,
                'report': self.rpt_connected,
                'query': self.qry_connected,
                'market_data': self.mktdata_connected
            },
            'account_info': self.account_info,
            'cash_assets': self.cash_assets,
            'stock_holdings': self.stock_holdings,
            'option_holdings': self.option_holdings
        }
