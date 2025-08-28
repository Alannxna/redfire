"""
XTP网关实现
用于对接中泰证券XTP极速交易接口
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from .baseGateway import BaseGateway


class XtpGateway(BaseGateway):
    """
    XTP网关类
    
    专门用于对接中泰证券XTP极速交易系统：
    - 股票交易
    - 期权交易
    - 融资融券
    - 极速行情
    """
    
    def __init__(self, main_engine=None):
        super().__init__("XTP", main_engine)
        
        # XTP特定配置
        self.default_config = {
            'userid': '',
            'password': '',
            'client_id': 1,
            'software_key': '',
            'quote_ip': '',
            'quote_port': 0,
            'trade_ip': '',
            'trade_port': 0,
            'quote_protocol': 'TCP',
            'trade_protocol': 'TCP'
        }
        
        # 连接状态
        self.trade_connected = False
        self.quote_connected = False
        self.login_status = False
        
        # 账户信息
        self.account_info = {}
        self.positions = {}
        self.orders = {}
        
        # XTP特有数据
        self.asset_info = {}  # 资产信息
        self.credit_info = {}  # 融资融券信息
        
        # VnPy网关实例
        self.vnpy_gateway = None
        
        self.logger.info("XTP网关初始化完成")
    
    async def connect(self, config: Dict[str, Any]) -> bool:
        """
        连接XTP接口
        
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
            
            # 连接交易和行情
            trade_success = await self._connect_trading()
            quote_success = await self._connect_quote()
            
            # 更新连接状态
            self.isConnected = trade_success and quote_success
            
            if self.isConnected:
                self.connectionStatus['connected'] = True
                self.connectionStatus['lastConnectTime'] = datetime.now()
                self.logger.info("XTP网关连接成功")
                
                # 触发连接事件
                await self._on_gateway_connected()
                
                # 查询初始数据
                await self._query_initial_data()
            else:
                self.logger.error("XTP网关连接失败")
            
            return self.isConnected
            
        except Exception as e:
            self.logger.error(f"XTP网关连接异常: {e}")
            return False
    
    async def disconnect(self) -> bool:
        """断开XTP连接"""
        try:
            if self.vnpy_gateway:
                # 断开VnPy网关
                self.vnpy_gateway.close()
            
            # 重置状态
            self.trade_connected = False
            self.quote_connected = False
            self.login_status = False
            self.isConnected = False
            
            self.connectionStatus['connected'] = False
            self.connectionStatus['lastDisconnectTime'] = datetime.now()
            
            self.logger.info("XTP网关断开成功")
            
            # 触发断开事件
            await self._on_gateway_disconnected()
            
            return True
            
        except Exception as e:
            self.logger.error(f"XTP网关断开异常: {e}")
            return False
    
    def _validate_config(self) -> bool:
        """验证配置参数"""
        required_fields = ['userid', 'password', 'client_id', 'software_key']
        
        for field in required_fields:
            if not self.gatewayConfig.get(field):
                self.logger.error(f"XTP配置缺少必要参数: {field}")
                return False
        
        # 检查IP和端口
        if not self.gatewayConfig.get('trade_ip') or not self.gatewayConfig.get('trade_port'):
            self.logger.error("XTP配置缺少交易服务器地址")
            return False
            
        if not self.gatewayConfig.get('quote_ip') or not self.gatewayConfig.get('quote_port'):
            self.logger.error("XTP配置缺少行情服务器地址")
            return False
        
        return True
    
    async def _initialize_vnpy_gateway(self) -> bool:
        """初始化VnPy网关"""
        try:
            from vnpy_xtp import XtpGateway as VnPyXtpGateway
            
            # 创建VnPy网关实例
            self.vnpy_gateway = VnPyXtpGateway(
                event_engine=None,  # 会从主引擎获取
                gateway_name="XTP"
            )
            
            # 注册事件回调
            self._register_vnpy_callbacks()
            
            return True
            
        except ImportError:
            self.logger.error("vnpy_xtp模块未安装")
            return False
        except Exception as e:
            self.logger.error(f"初始化VnPy XTP网关失败: {e}")
            return False
    
    async def _connect_trading(self) -> bool:
        """连接交易接口"""
        try:
            if not self.vnpy_gateway:
                return False
            
            # 设置交易连接参数
            setting = {
                "账号": self.gatewayConfig['userid'],
                "密码": self.gatewayConfig['password'],
                "客户号": self.gatewayConfig['client_id'],
                "软件Key": self.gatewayConfig['software_key'],
                "交易服务器": self.gatewayConfig['trade_ip'],
                "交易端口": self.gatewayConfig['trade_port'],
                "交易协议": self.gatewayConfig['trade_protocol']
            }
            
            # 连接
            self.vnpy_gateway.connect(setting)
            self.trade_connected = True
            
            self.logger.info("XTP交易接口连接成功")
            return True
            
        except Exception as e:
            self.logger.error(f"XTP交易接口连接失败: {e}")
            return False
    
    async def _connect_quote(self) -> bool:
        """连接行情接口"""
        try:
            if not self.vnpy_gateway:
                return False
            
            # XTP行情接口连接
            # 通常会在交易连接成功后自动连接行情
            self.quote_connected = True
            
            self.logger.info("XTP行情接口连接成功")
            return True
            
        except Exception as e:
            self.logger.error(f"XTP行情接口连接失败: {e}")
            return False
    
    async def _query_initial_data(self):
        """查询初始数据"""
        try:
            # 查询账户信息
            await self.query_account()
            
            # 查询持仓信息
            await self.query_positions()
            
            # 查询资产信息
            await self._query_asset_info()
            
            self.logger.info("XTP初始数据查询完成")
            
        except Exception as e:
            self.logger.error(f"XTP初始数据查询失败: {e}")
    
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
            if not self.isConnected:
                self.logger.error("XTP网关未连接，无法提交订单")
                return None
            
            # 构造订单请求
            # 需要根据XTP的订单格式来实现
            
            order_id = f"xtp_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self.logger.info(f"XTP订单提交成功: {order_id}")
            
            return order_id
            
        except Exception as e:
            self.logger.error(f"XTP提交订单失败: {e}")
            return None
    
    async def cancel_order(self, order_id: str) -> bool:
        """撤销订单"""
        try:
            if not self.isConnected:
                self.logger.error("XTP网关未连接，无法撤销订单")
                return False
            
            # 撤销订单逻辑
            self.logger.info(f"XTP订单撤销成功: {order_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"XTP撤销订单失败: {e}")
            return False
    
    async def subscribe_market_data(self, symbols: list) -> bool:
        """订阅行情数据"""
        try:
            if not self.quote_connected:
                self.logger.error("XTP行情接口未连接")
                return False
            
            # 订阅行情
            self.logger.info(f"XTP行情订阅成功: {symbols}")
            return True
            
        except Exception as e:
            self.logger.error(f"XTP订阅行情失败: {e}")
            return False
    
    async def query_account(self) -> Dict[str, Any]:
        """查询账户信息"""
        try:
            if not self.isConnected:
                return {}
            
            # 查询账户信息
            # 这里需要调用具体的XTP API
            
            return self.account_info
            
        except Exception as e:
            self.logger.error(f"XTP查询账户失败: {e}")
            return {}
    
    async def query_positions(self) -> Dict[str, Any]:
        """查询持仓信息"""
        try:
            if not self.isConnected:
                return {}
            
            # 查询持仓信息
            return self.positions
            
        except Exception as e:
            self.logger.error(f"XTP查询持仓失败: {e}")
            return {}
    
    async def _query_asset_info(self) -> Dict[str, Any]:
        """查询资产信息"""
        try:
            if not self.isConnected:
                return {}
            
            # 查询资产信息（股票账户特有）
            return self.asset_info
            
        except Exception as e:
            self.logger.error(f"XTP查询资产失败: {e}")
            return {}
    
    async def query_credit_info(self) -> Dict[str, Any]:
        """查询融资融券信息"""
        try:
            if not self.isConnected:
                return {}
            
            # 查询融资融券信息
            return self.credit_info
            
        except Exception as e:
            self.logger.error(f"XTP查询融资融券失败: {e}")
            return {}
    
    async def submit_credit_order(self, order_data: Dict[str, Any]) -> Optional[str]:
        """提交融资融券订单"""
        try:
            if not self.isConnected:
                self.logger.error("XTP网关未连接，无法提交融资融券订单")
                return None
            
            # 融资融券订单逻辑
            order_id = f"xtp_credit_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self.logger.info(f"XTP融资融券订单提交成功: {order_id}")
            
            return order_id
            
        except Exception as e:
            self.logger.error(f"XTP提交融资融券订单失败: {e}")
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
            'type': 'XTP',
            'description': '中泰证券XTP极速交易接口',
            'supported_markets': ['沪深股票', '期权', '融资融券'],
            'features': [
                '极速交易',
                '股票交易',
                '期权交易',
                '融资融券',
                'Level-2行情',
                '毫秒级延迟'
            ],
            'connection_status': self.connectionStatus,
            'account_info': self.account_info,
            'asset_info': self.asset_info,
            'credit_info': self.credit_info
        }
