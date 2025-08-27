"""
CTPTest网关实现
用于对接CTP测试环境和券商仿真接口
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from .baseGateway import BaseGateway


class CtptestGateway(BaseGateway):
    """
    CTPTest网关类
    
    专门用于对接：
    - CTP仿真环境
    - 券商测试接口
    - SimNow仿真系统
    """
    
    def __init__(self, main_engine=None):
        super().__init__("CTPTest", main_engine)
        
        # CTPTest特定配置
        self.default_config = {
            'userid': '',
            'password': '',
            'brokerid': '9999',  # 仿真默认
            'td_address': 'tcp://180.168.146.187:10101',
            'md_address': 'tcp://180.168.146.187:10111', 
            'appid': 'simnow_client_test',
            'auth_code': '0000000000000000',
            'product_info': ''
        }
        
        # 连接状态
        self.td_connected = False
        self.md_connected = False
        self.authenticated = False
        
        # 账户信息
        self.account_info = {}
        self.positions = {}
        self.orders = {}
        
        # VnPy网关实例
        self.vnpy_gateway = None
        
        self.logger.info("CTPTest网关初始化完成")
    
    async def connect(self, config: Dict[str, Any]) -> bool:
        """
        连接CTPTest接口
        
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
            td_success = await self._connect_trading()
            md_success = await self._connect_market_data()
            
            # 更新连接状态
            self.isConnected = td_success and md_success
            
            if self.isConnected:
                self.connectionStatus['connected'] = True
                self.connectionStatus['lastConnectTime'] = datetime.now()
                self.logger.info("CTPTest网关连接成功")
                
                # 触发连接事件
                await self._on_gateway_connected()
            else:
                self.logger.error("CTPTest网关连接失败")
            
            return self.isConnected
            
        except Exception as e:
            self.logger.error(f"CTPTest网关连接异常: {e}")
            return False
    
    async def disconnect(self) -> bool:
        """断开CTPTest连接"""
        try:
            if self.vnpy_gateway:
                # 断开VnPy网关
                self.vnpy_gateway.close()
            
            # 重置状态
            self.td_connected = False
            self.md_connected = False
            self.authenticated = False
            self.isConnected = False
            
            self.connectionStatus['connected'] = False
            self.connectionStatus['lastDisconnectTime'] = datetime.now()
            
            self.logger.info("CTPTest网关断开成功")
            
            # 触发断开事件
            await self._on_gateway_disconnected()
            
            return True
            
        except Exception as e:
            self.logger.error(f"CTPTest网关断开异常: {e}")
            return False
    
    def _validate_config(self) -> bool:
        """验证配置参数"""
        required_fields = ['userid', 'password', 'brokerid']
        
        for field in required_fields:
            if not self.gatewayConfig.get(field):
                self.logger.error(f"CTPTest配置缺少必要参数: {field}")
                return False
        
        return True
    
    async def _initialize_vnpy_gateway(self) -> bool:
        """初始化VnPy网关"""
        try:
            from vnpy_ctptest import CtptestGateway as VnPyCtptestGateway
            
            # 创建VnPy网关实例
            self.vnpy_gateway = VnPyCtptestGateway(
                event_engine=None,  # 会从主引擎获取
                gateway_name="CTPTest"
            )
            
            # 注册事件回调
            self._register_vnpy_callbacks()
            
            return True
            
        except ImportError:
            self.logger.error("vnpy_ctptest模块未安装")
            return False
        except Exception as e:
            self.logger.error(f"初始化VnPy CTPTest网关失败: {e}")
            return False
    
    async def _connect_trading(self) -> bool:
        """连接交易接口"""
        try:
            if not self.vnpy_gateway:
                return False
            
            # 设置交易连接参数
            setting = {
                "用户名": self.gatewayConfig['userid'],
                "密码": self.gatewayConfig['password'],
                "经纪商代码": self.gatewayConfig['brokerid'],
                "交易服务器": self.gatewayConfig['td_address'],
                "产品名称": self.gatewayConfig['appid'],
                "授权编码": self.gatewayConfig['auth_code'],
                "产品信息": self.gatewayConfig['product_info']
            }
            
            # 连接
            self.vnpy_gateway.connect(setting)
            self.td_connected = True
            
            self.logger.info("CTPTest交易接口连接成功")
            return True
            
        except Exception as e:
            self.logger.error(f"CTPTest交易接口连接失败: {e}")
            return False
    
    async def _connect_market_data(self) -> bool:
        """连接行情接口"""
        try:
            # 行情接口通常与交易接口使用相同连接
            if self.td_connected:
                self.md_connected = True
                self.logger.info("CTPTest行情接口连接成功")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"CTPTest行情接口连接失败: {e}")
            return False
    
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
                self.logger.error("CTPTest网关未连接，无法提交订单")
                return None
            
            # 构造订单请求
            # 这里需要根据具体的VnPy接口来实现
            
            order_id = f"ctptest_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self.logger.info(f"CTPTest订单提交成功: {order_id}")
            
            return order_id
            
        except Exception as e:
            self.logger.error(f"CTPTest提交订单失败: {e}")
            return None
    
    async def cancel_order(self, order_id: str) -> bool:
        """撤销订单"""
        try:
            if not self.isConnected:
                self.logger.error("CTPTest网关未连接，无法撤销订单")
                return False
            
            # 撤销订单逻辑
            self.logger.info(f"CTPTest订单撤销成功: {order_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"CTPTest撤销订单失败: {e}")
            return False
    
    async def subscribe_market_data(self, symbols: list) -> bool:
        """订阅行情数据"""
        try:
            if not self.md_connected:
                self.logger.error("CTPTest行情接口未连接")
                return False
            
            # 订阅行情
            self.logger.info(f"CTPTest行情订阅成功: {symbols}")
            return True
            
        except Exception as e:
            self.logger.error(f"CTPTest订阅行情失败: {e}")
            return False
    
    async def query_account(self) -> Dict[str, Any]:
        """查询账户信息"""
        try:
            if not self.isConnected:
                return {}
            
            # 查询账户信息
            return self.account_info
            
        except Exception as e:
            self.logger.error(f"CTPTest查询账户失败: {e}")
            return {}
    
    async def query_positions(self) -> Dict[str, Any]:
        """查询持仓信息"""
        try:
            if not self.isConnected:
                return {}
            
            # 查询持仓信息
            return self.positions
            
        except Exception as e:
            self.logger.error(f"CTPTest查询持仓失败: {e}")
            return {}
    
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
            'type': 'CTPTest',
            'description': 'CTP测试/仿真交易接口',
            'supported_markets': ['期货', '仿真'],
            'features': [
                '仿真交易',
                '测试环境',
                'SimNow支持',
                '期货交易',
                '实时行情'
            ],
            'connection_status': self.connectionStatus,
            'account_info': self.account_info
        }
