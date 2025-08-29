"""
模拟网关 (Simulation Gateway)

提供模拟的交易功能，用于测试和开发。
"""

import logging
import time
import uuid
from typing import Dict, List, Optional, Any
from .baseGateway import BaseGateway


class SimGateway(BaseGateway):
    """
    模拟网关类
    
    提供模拟的交易功能，包括：
    - 模拟连接和认证
    - 模拟订单管理
    - 模拟仓位管理
    - 模拟市场数据
    """
    
    def __init__(self, gateway_name: str = "SimGateway", main_engine=None):
        """
        初始化模拟网关
        
        Args:
            gateway_name: 网关名称
            main_engine: 主交易引擎实例
        """
        super().__init__(gateway_name, main_engine)
        
        # 模拟配置
        self.simConfig = {
            'simulationMode': True,
            'delayTime': 0.1,  # 模拟延迟时间（秒）
            'randomErrors': False,  # 是否随机产生错误
            'errorRate': 0.01  # 错误率
        }
        
        # 模拟数据
        self.simOrders: Dict[str, Dict[str, Any]] = {}
        self.simPositions: Dict[str, Dict[str, Any]] = {}
        self.simAccount: Dict[str, Any] = {
            'balance': 1000000.0,
            'available': 1000000.0,
            'frozen': 0.0,
            'commission': 0.0
        }
        
        # 模拟市场数据
        self.simMarketData: Dict[str, Dict[str, Any]] = {}
        
        # 订单计数器
        self.orderCounter = 0
        
        # 初始化模拟数据
        self._init_sim_data()
    
    def _init_sim_data(self):
        """初始化模拟数据"""
        # 初始化一些模拟仓位
        self.simPositions = {
            'BTC': {
                'symbol': 'BTC',
                'side': 'LONG',
                'quantity': 0,
                'avg_price': 0.0,
                'pnl': 0.0
            },
            'ETH': {
                'symbol': 'ETH',
                'side': 'LONG',
                'quantity': 0,
                'avg_price': 0.0,
                'pnl': 0.0
            }
        }
        
        # 初始化模拟市场数据
        self.simMarketData = {
            'BTC': {
                'symbol': 'BTC',
                'last_price': 50000.0,
                'bid_price': 49999.0,
                'ask_price': 50001.0,
                'volume': 1000.0,
                'timestamp': time.time()
            },
            'ETH': {
                'symbol': 'ETH',
                'last_price': 3000.0,
                'bid_price': 2999.0,
                'ask_price': 3001.0,
                'volume': 5000.0,
                'timestamp': time.time()
            }
        }
        
        self.logger.info("模拟数据初始化完成")
    
    def connect(self) -> bool:
        """
        连接模拟网关
        
        Returns:
            bool: 连接是否成功
        """
        try:
            self.logger.info("正在连接模拟网关...")
            
            # 模拟连接延迟
            time.sleep(self.simConfig['delayTime'])
            
            # 模拟连接成功
            self._updateConnectionStatus(True, False)
            self._triggerEvent('onConnect', {'gateway': self.gatewayName})
            
            self.logger.info("模拟网关连接成功")
            return True
            
        except Exception as e:
            self.logger.error(f"连接模拟网关失败: {e}")
            self._updateConnectionStatus(False, False, str(e))
            return False
    
    def disconnect(self) -> bool:
        """
        断开模拟网关连接
        
        Returns:
            bool: 断开是否成功
        """
        try:
            self.logger.info("正在断开模拟网关连接...")
            
            # 模拟断开延迟
            time.sleep(self.simConfig['delayTime'])
            
            # 模拟断开成功
            self._updateConnectionStatus(False, False)
            self._triggerEvent('onDisconnect', {'gateway': self.gatewayName})
            
            self.logger.info("模拟网关连接已断开")
            return True
            
        except Exception as e:
            self.logger.error(f"断开模拟网关连接失败: {e}")
            return False
    
    def authenticate(self) -> bool:
        """
        认证模拟网关
        
        Returns:
            bool: 认证是否成功
        """
        try:
            if not self.isConnected:
                self.logger.error("网关未连接，无法认证")
                return False
            
            self.logger.info("正在认证模拟网关...")
            
            # 模拟认证延迟
            time.sleep(self.simConfig['delayTime'])
            
            # 模拟认证成功
            self._updateConnectionStatus(True, True)
            self._triggerEvent('onAuthenticate', {'gateway': self.gatewayName})
            
            self.logger.info("模拟网关认证成功")
            return True
            
        except Exception as e:
            self.logger.error(f"认证模拟网关失败: {e}")
            self._updateConnectionStatus(True, False, str(e))
            return False
    
    def sendOrder(self, order_data: Dict[str, Any]) -> str:
        """
        发送模拟订单
        
        Args:
            order_data: 订单数据
            
        Returns:
            str: 订单ID
        """
        try:
            if not self.isGatewayReady():
                self.logger.error("网关未就绪，无法发送订单")
                return ""
            
            # 生成订单ID
            order_id = f"SIM_{self.orderCounter:06d}"
            self.orderCounter += 1
            
            # 创建订单记录
            order = {
                'order_id': order_id,
                'symbol': order_data.get('symbol', ''),
                'side': order_data.get('side', 'BUY'),
                'order_type': order_data.get('order_type', 'LIMIT'),
                'price': order_data.get('price', 0.0),
                'quantity': order_data.get('quantity', 0.0),
                'status': 'PENDING',
                'timestamp': time.time(),
                'gateway': self.gatewayName
            }
            
            # 保存订单
            self.simOrders[order_id] = order
            
            # 模拟订单处理延迟
            time.sleep(self.simConfig['delayTime'])
            
            # 模拟订单状态更新
            self._simulate_order_update(order_id)
            
            # 触发订单事件
            self._triggerEvent('onOrder', order)
            
            self.logger.info(f"模拟订单发送成功: {order_id}")
            return order_id
            
        except Exception as e:
            self.logger.error(f"发送模拟订单失败: {e}")
            return ""
    
    def cancelOrder(self, order_id: str) -> bool:
        """
        取消模拟订单
        
        Args:
            order_id: 订单ID
            
        Returns:
            bool: 取消是否成功
        """
        try:
            if not self.isGatewayReady():
                self.logger.error("网关未就绪，无法取消订单")
                return False
            
            if order_id not in self.simOrders:
                self.logger.error(f"订单 {order_id} 不存在")
                return False
            
            order = self.simOrders[order_id]
            
            # 检查订单状态
            if order['status'] in ['FILLED', 'CANCELLED']:
                self.logger.warning(f"订单 {order_id} 状态为 {order['status']}，无法取消")
                return False
            
            # 模拟取消延迟
            time.sleep(self.simConfig['delayTime'])
            
            # 更新订单状态
            order['status'] = 'CANCELLED'
            order['cancel_time'] = time.time()
            
            # 触发订单事件
            self._triggerEvent('onOrder', order)
            
            self.logger.info(f"模拟订单取消成功: {order_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"取消模拟订单失败: {e}")
            return False
    
    def queryOrder(self, order_id: str) -> Optional[Dict[str, Any]]:
        """
        查询模拟订单
        
        Args:
            order_id: 订单ID
            
        Returns:
            Optional[Dict[str, Any]]: 订单信息
        """
        try:
            if not self.isGatewayReady():
                self.logger.error("网关未就绪，无法查询订单")
                return None
            
            if order_id not in self.simOrders:
                self.logger.warning(f"订单 {order_id} 不存在")
                return None
            
            return self.simOrders[order_id].copy()
            
        except Exception as e:
            self.logger.error(f"查询模拟订单失败: {e}")
            return None
    
    def queryPosition(self, symbol: str = "") -> List[Dict[str, Any]]:
        """
        查询模拟仓位
        
        Args:
            symbol: 交易品种，如果为空则查询所有仓位
            
        Returns:
            List[Dict[str, Any]]: 仓位信息列表
        """
        try:
            if not self.isGatewayReady():
                self.logger.error("网关未就绪，无法查询仓位")
                return []
            
            if symbol:
                if symbol in self.simPositions:
                    return [self.simPositions[symbol].copy()]
                else:
                    return []
            else:
                return [pos.copy() for pos in self.simPositions.values()]
                
        except Exception as e:
            self.logger.error(f"查询模拟仓位失败: {e}")
            return []
    
    def queryAccount(self) -> Optional[Dict[str, Any]]:
        """
        查询模拟账户信息
        
        Returns:
            Optional[Dict[str, Any]]: 账户信息
        """
        try:
            if not self.isGatewayReady():
                self.logger.error("网关未就绪，无法查询账户")
                return None
            
            return self.simAccount.copy()
            
        except Exception as e:
            self.logger.error(f"查询模拟账户失败: {e}")
            return None
    
    def subscribeMarketData(self, symbol: str) -> bool:
        """
        订阅模拟市场数据
        
        Args:
            symbol: 交易品种
            
        Returns:
            bool: 订阅是否成功
        """
        try:
            if not self.isGatewayReady():
                self.logger.error("网关未就绪，无法订阅市场数据")
                return False
            
            if symbol not in self.simMarketData:
                self.logger.warning(f"交易品种 {symbol} 不存在")
                return False
            
            self.logger.info(f"订阅模拟市场数据成功: {symbol}")
            return True
            
        except Exception as e:
            self.logger.error(f"订阅模拟市场数据失败: {e}")
            return False
    
    def unsubscribeMarketData(self, symbol: str) -> bool:
        """
        取消订阅模拟市场数据
        
        Args:
            symbol: 交易品种
            
        Returns:
            bool: 取消订阅是否成功
        """
        try:
            if not self.isGatewayReady():
                self.logger.error("网关未就绪，无法取消订阅市场数据")
                return False
            
            self.logger.info(f"取消订阅模拟市场数据成功: {symbol}")
            return True
            
        except Exception as e:
            self.logger.error(f"取消订阅模拟市场数据失败: {e}")
            return False
    
    def _simulate_order_update(self, order_id: str):
        """模拟订单状态更新"""
        try:
            order = self.simOrders[order_id]
            
            # 模拟订单成交
            if order['status'] == 'PENDING':
                # 随机决定是否成交
                import random
                if random.random() < 0.8:  # 80%概率成交
                    order['status'] = 'FILLED'
                    order['fill_time'] = time.time()
                    order['fill_price'] = order['price']
                    
                    # 更新仓位
                    self._update_position(order)
                    
                    # 触发成交事件
                    trade_data = {
                        'order_id': order_id,
                        'symbol': order['symbol'],
                        'side': order['side'],
                        'price': order['fill_price'],
                        'quantity': order['quantity'],
                        'timestamp': order['fill_time'],
                        'gateway': self.gatewayName
                    }
                    self._triggerEvent('onTrade', trade_data)
                    
                    # 更新账户
                    self._update_account(order)
            
        except Exception as e:
            self.logger.error(f"模拟订单状态更新失败: {e}")
    
    def _update_position(self, order: Dict[str, Any]):
        """更新仓位"""
        try:
            symbol = order['symbol']
            side = order['side']
            quantity = order['quantity']
            price = order['fill_price']
            
            if symbol not in self.simPositions:
                self.simPositions[symbol] = {
                    'symbol': symbol,
                    'side': 'LONG',
                    'quantity': 0,
                    'avg_price': 0.0,
                    'pnl': 0.0
                }
            
            position = self.simPositions[symbol]
            
            if side == 'BUY':
                # 买入，增加多头仓位
                if position['side'] == 'SHORT':
                    # 如果之前是空头，先平仓
                    if position['quantity'] > 0:
                        # 计算平仓盈亏
                        pnl = (position['avg_price'] - price) * position['quantity']
                        position['pnl'] += pnl
                
                # 更新仓位
                total_cost = position['quantity'] * position['avg_price'] + quantity * price
                total_quantity = position['quantity'] + quantity
                position['quantity'] = total_quantity
                position['avg_price'] = total_cost / total_quantity if total_quantity > 0 else 0
                position['side'] = 'LONG'
                
            else:  # SELL
                # 卖出，增加空头仓位
                if position['side'] == 'LONG':
                    # 如果之前是多头，先平仓
                    if position['quantity'] > 0:
                        # 计算平仓盈亏
                        pnl = (price - position['avg_price']) * min(position['quantity'], quantity)
                        position['pnl'] += pnl
                
                # 更新仓位
                total_cost = position['quantity'] * position['avg_price'] + quantity * price
                total_quantity = position['quantity'] + quantity
                position['quantity'] = total_quantity
                position['avg_price'] = total_cost / total_quantity if total_quantity > 0 else 0
                position['side'] = 'SHORT'
            
            # 触发仓位事件
            self._triggerEvent('onPosition', position.copy())
            
        except Exception as e:
            self.logger.error(f"更新仓位失败: {e}")
    
    def _update_account(self, order: Dict[str, Any]):
        """更新账户"""
        try:
            # 计算手续费（假设为0.1%）
            commission_rate = 0.001
            commission = order['quantity'] * order['fill_price'] * commission_rate
            
            # 更新账户余额
            self.simAccount['commission'] += commission
            self.simAccount['available'] -= commission
            
            # 触发账户事件
            self._triggerEvent('onAccount', self.simAccount.copy())
            
        except Exception as e:
            self.logger.error(f"更新账户失败: {e}")
    
    def updateMarketData(self, symbol: str, market_data: Dict[str, Any]):
        """
        更新模拟市场数据
        
        Args:
            symbol: 交易品种
            market_data: 市场数据
        """
        try:
            if symbol in self.simMarketData:
                self.simMarketData[symbol].update(market_data)
                self.simMarketData[symbol]['timestamp'] = time.time()
                
                # 触发行情事件
                self._triggerEvent('onTick', self.simMarketData[symbol].copy())
                
        except Exception as e:
            self.logger.error(f"更新模拟市场数据失败: {e}")
    
    def getSimulationStatus(self) -> Dict[str, Any]:
        """
        获取模拟状态
        
        Returns:
            Dict[str, Any]: 模拟状态信息
        """
        return {
            'gatewayName': self.gatewayName,
            'isConnected': self.isConnected,
            'isAuthenticated': self.isAuthenticated,
            'orderCount': len(self.simOrders),
            'positionCount': len(self.simPositions),
            'accountBalance': self.simAccount['balance'],
            'simConfig': self.simConfig.copy()
        }
    
    def resetSimulation(self):
        """重置模拟数据"""
        try:
            # 清空订单
            self.simOrders.clear()
            
            # 重置仓位
            self._init_sim_data()
            
            # 重置账户
            self.simAccount = {
                'balance': 1000000.0,
                'available': 1000000.0,
                'frozen': 0.0,
                'commission': 0.0
            }
            
            # 重置订单计数器
            self.orderCounter = 0
            
            self.logger.info("模拟数据已重置")
            
        except Exception as e:
            self.logger.error(f"重置模拟数据失败: {e}")
    
    def getStatus(self) -> Dict[str, Any]:
        """
        获取网关状态
        
        Returns:
            Dict[str, Any]: 状态信息字典
        """
        return {
            **super().getStatus(),
            'simulationStatus': self.getSimulationStatus()
        }
