"""
国内券商交易接口统一适配器
专门用于管理和协调vnpy_ctptest、vnpy_xtp、vnpy_oes等国内券商接口
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from ..gateways.baseGateway import BaseGateway
from ..gateways.ctptest_gateway import CtptestGateway
from ..gateways.xtp_gateway import XtpGateway
from ..gateways.oes_gateway import OesGateway


class DomesticGatewayType(Enum):
    """国内券商网关类型"""
    CTPTEST = "ctptest"  # CTP测试/仿真
    XTP = "xtp"          # 中泰证券XTP
    OES = "oes"          # 宽睿OES


@dataclass
class DomesticGatewayConfig:
    """国内券商网关配置"""
    
    # 启用的网关
    enabled_gateways: List[DomesticGatewayType] = field(default_factory=list)
    
    # 各网关具体配置
    ctptest_config: Dict[str, Any] = field(default_factory=dict)
    xtp_config: Dict[str, Any] = field(default_factory=dict)
    oes_config: Dict[str, Any] = field(default_factory=dict)
    
    # 通用配置
    enable_auto_reconnect: bool = True
    reconnect_interval: int = 5
    max_reconnect_attempts: int = 10
    heartbeat_interval: int = 30
    
    # 性能配置
    order_timeout: int = 30
    query_timeout: int = 10
    max_concurrent_orders: int = 100
    
    # 监控配置
    enable_monitoring: bool = True
    alert_on_disconnect: bool = True
    alert_on_high_latency: bool = True
    latency_threshold_ms: int = 100


@dataclass
class GatewayStatus:
    """网关状态信息"""
    name: str
    type: DomesticGatewayType
    connected: bool = False
    authenticated: bool = False
    last_heartbeat: Optional[datetime] = None
    last_connect_time: Optional[datetime] = None
    last_disconnect_time: Optional[datetime] = None
    error_count: int = 0
    last_error: Optional[str] = None
    
    # 性能指标
    avg_latency_ms: float = 0.0
    orders_count: int = 0
    successful_orders: int = 0
    failed_orders: int = 0


class DomesticGatewaysAdapter:
    """
    国内券商交易接口统一适配器
    
    负责管理和协调多个国内券商接口：
    - vnpy_ctptest: CTP测试/仿真交易
    - vnpy_xtp: 中泰证券极速交易
    - vnpy_oes: 宽睿OES高性能交易
    """
    
    def __init__(self, main_engine=None):
        self.main_engine = main_engine
        self.logger = logging.getLogger(f"{__name__}.DomesticGatewaysAdapter")
        
        # 配置管理
        self.config: Optional[DomesticGatewayConfig] = None
        
        # 网关实例管理
        self.gateways: Dict[str, BaseGateway] = {}
        self.gateway_status: Dict[str, GatewayStatus] = {}
        
        # 连接状态
        self.is_initialized = False
        self.active_gateways: List[str] = []
        
        # 事件回调
        self.event_callbacks: Dict[str, List] = {
            'on_gateway_connected': [],
            'on_gateway_disconnected': [],
            'on_order_update': [],
            'on_trade_update': [],
            'on_position_update': [],
            'on_account_update': [],
            'on_error': []
        }
        
        # 监控数据
        self.performance_metrics: Dict[str, Any] = {}
        self.reconnection_tasks: Dict[str, asyncio.Task] = {}
        
        self.logger.info("国内券商接口适配器初始化完成")
    
    async def initialize(self, config: DomesticGatewayConfig) -> bool:
        """
        初始化适配器
        
        Args:
            config: 配置对象
            
        Returns:
            初始化是否成功
        """
        try:
            self.config = config
            
            # 创建网关实例
            await self._create_gateway_instances()
            
            # 初始化监控系统
            if config.enable_monitoring:
                await self._initialize_monitoring()
            
            self.is_initialized = True
            self.logger.info("国内券商接口适配器初始化成功")
            
            return True
            
        except Exception as e:
            self.logger.error(f"适配器初始化失败: {e}")
            return False
    
    async def _create_gateway_instances(self):
        """创建网关实例"""
        if not self.config:
            return
        
        for gateway_type in self.config.enabled_gateways:
            try:
                gateway = None
                config = {}
                
                if gateway_type == DomesticGatewayType.CTPTEST:
                    gateway = CtptestGateway(self.main_engine)
                    config = self.config.ctptest_config
                    
                elif gateway_type == DomesticGatewayType.XTP:
                    gateway = XtpGateway(self.main_engine)
                    config = self.config.xtp_config
                    
                elif gateway_type == DomesticGatewayType.OES:
                    gateway = OesGateway(self.main_engine)
                    config = self.config.oes_config
                
                if gateway:
                    gateway_name = gateway.gatewayName
                    self.gateways[gateway_name] = gateway
                    
                    # 初始化状态
                    self.gateway_status[gateway_name] = GatewayStatus(
                        name=gateway_name,
                        type=gateway_type
                    )
                    
                    # 注册事件回调
                    await self._register_gateway_callbacks(gateway)
                    
                    self.logger.info(f"创建网关实例: {gateway_name}")
                    
            except Exception as e:
                self.logger.error(f"创建网关实例失败 {gateway_type}: {e}")
    
    async def _register_gateway_callbacks(self, gateway: BaseGateway):
        """注册网关事件回调"""
        # 连接事件
        gateway.on('onConnect', self._on_gateway_connected)
        gateway.on('onDisconnect', self._on_gateway_disconnected)
        
        # 交易事件
        gateway.on('onOrder', self._on_order_update)
        gateway.on('onTrade', self._on_trade_update)
        
        # 账户事件
        gateway.on('onPosition', self._on_position_update)
        gateway.on('onAccount', self._on_account_update)
        
        # 错误事件
        gateway.on('onError', self._on_gateway_error)
    
    async def connect_all_gateways(self) -> Dict[str, bool]:
        """连接所有启用的网关"""
        if not self.is_initialized:
            self.logger.error("适配器未初始化")
            return {}
        
        connection_results = {}
        
        # 并发连接所有网关
        connection_tasks = []
        for gateway_name, gateway in self.gateways.items():
            task = asyncio.create_task(
                self._connect_single_gateway(gateway_name, gateway)
            )
            connection_tasks.append((gateway_name, task))
        
        # 等待所有连接完成
        for gateway_name, task in connection_tasks:
            try:
                result = await task
                connection_results[gateway_name] = result
                
                if result:
                    self.active_gateways.append(gateway_name)
                    self.logger.info(f"网关连接成功: {gateway_name}")
                else:
                    self.logger.error(f"网关连接失败: {gateway_name}")
                    
            except Exception as e:
                self.logger.error(f"网关连接异常 {gateway_name}: {e}")
                connection_results[gateway_name] = False
        
        # 启动重连监控
        if self.config.enable_auto_reconnect:
            await self._start_reconnection_monitoring()
        
        return connection_results
    
    async def _connect_single_gateway(self, gateway_name: str, gateway: BaseGateway) -> bool:
        """连接单个网关"""
        try:
            # 获取对应配置
            config = {}
            if gateway_name == "CTPTEST":
                config = self.config.ctptest_config
            elif gateway_name == "XTP":
                config = self.config.xtp_config
            elif gateway_name == "OES":
                config = self.config.oes_config
            
            # 连接网关
            success = await gateway.connect(config)
            
            # 更新状态
            status = self.gateway_status[gateway_name]
            status.connected = success
            if success:
                status.last_connect_time = datetime.now()
                status.error_count = 0
            
            return success
            
        except Exception as e:
            self.logger.error(f"连接网关失败 {gateway_name}: {e}")
            
            # 更新错误状态
            status = self.gateway_status[gateway_name]
            status.connected = False
            status.error_count += 1
            status.last_error = str(e)
            
            return False
    
    async def disconnect_all_gateways(self) -> Dict[str, bool]:
        """断开所有网关连接"""
        disconnection_results = {}
        
        # 停止重连监控
        await self._stop_reconnection_monitoring()
        
        # 并发断开所有网关
        disconnection_tasks = []
        for gateway_name, gateway in self.gateways.items():
            if gateway_name in self.active_gateways:
                task = asyncio.create_task(gateway.disconnect())
                disconnection_tasks.append((gateway_name, task))
        
        # 等待所有断开完成
        for gateway_name, task in disconnection_tasks:
            try:
                result = await task
                disconnection_results[gateway_name] = result
                
                if result:
                    self.active_gateways.remove(gateway_name)
                    self.logger.info(f"网关断开成功: {gateway_name}")
                    
                    # 更新状态
                    status = self.gateway_status[gateway_name]
                    status.connected = False
                    status.last_disconnect_time = datetime.now()
                    
            except Exception as e:
                self.logger.error(f"网关断开异常 {gateway_name}: {e}")
                disconnection_results[gateway_name] = False
        
        return disconnection_results
    
    async def submit_order(self, order_data: Dict[str, Any], 
                          gateway_name: Optional[str] = None) -> Optional[str]:
        """
        提交订单
        
        Args:
            order_data: 订单数据
            gateway_name: 指定网关名称，为空则自动选择
            
        Returns:
            订单ID
        """
        try:
            # 选择网关
            if gateway_name:
                if gateway_name not in self.active_gateways:
                    self.logger.error(f"指定网关不可用: {gateway_name}")
                    return None
                selected_gateway = gateway_name
            else:
                selected_gateway = await self._select_best_gateway_for_order(order_data)
                if not selected_gateway:
                    self.logger.error("没有可用的网关")
                    return None
            
            # 提交订单
            gateway = self.gateways[selected_gateway]
            order_id = await gateway.submit_order(order_data)
            
            if order_id:
                # 更新统计
                status = self.gateway_status[selected_gateway]
                status.orders_count += 1
                
                self.logger.info(f"订单提交成功: {order_id} via {selected_gateway}")
            
            return order_id
            
        except Exception as e:
            self.logger.error(f"提交订单失败: {e}")
            return None
    
    async def cancel_order(self, order_id: str, 
                          gateway_name: Optional[str] = None) -> bool:
        """
        撤销订单
        
        Args:
            order_id: 订单ID
            gateway_name: 指定网关名称，为空则自动查找
            
        Returns:
            撤销是否成功
        """
        try:
            # 查找订单所在网关
            if gateway_name:
                if gateway_name not in self.active_gateways:
                    self.logger.error(f"指定网关不可用: {gateway_name}")
                    return False
                target_gateway = gateway_name
            else:
                target_gateway = await self._find_gateway_for_order(order_id)
                if not target_gateway:
                    self.logger.error(f"找不到订单所在网关: {order_id}")
                    return False
            
            # 撤销订单
            gateway = self.gateways[target_gateway]
            success = await gateway.cancel_order(order_id)
            
            if success:
                self.logger.info(f"订单撤销成功: {order_id} via {target_gateway}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"撤销订单失败: {e}")
            return False
    
    async def subscribe_market_data(self, symbols: List[str], 
                                  gateway_names: Optional[List[str]] = None) -> Dict[str, bool]:
        """
        订阅行情数据
        
        Args:
            symbols: 合约列表
            gateway_names: 指定网关列表，为空则使用所有网关
            
        Returns:
            各网关订阅结果
        """
        subscription_results = {}
        
        # 确定订阅网关
        if gateway_names:
            target_gateways = [name for name in gateway_names if name in self.active_gateways]
        else:
            target_gateways = self.active_gateways.copy()
        
        # 并发订阅
        subscription_tasks = []
        for gateway_name in target_gateways:
            gateway = self.gateways[gateway_name]
            task = asyncio.create_task(gateway.subscribe_market_data(symbols))
            subscription_tasks.append((gateway_name, task))
        
        # 等待订阅完成
        for gateway_name, task in subscription_tasks:
            try:
                result = await task
                subscription_results[gateway_name] = result
                
                if result:
                    self.logger.info(f"行情订阅成功: {symbols} via {gateway_name}")
                
            except Exception as e:
                self.logger.error(f"行情订阅失败 {gateway_name}: {e}")
                subscription_results[gateway_name] = False
        
        return subscription_results
    
    async def _select_best_gateway_for_order(self, order_data: Dict[str, Any]) -> Optional[str]:
        """为订单选择最佳网关"""
        if not self.active_gateways:
            return None
        
        # 简单策略：选择延迟最低的网关
        best_gateway = None
        best_latency = float('inf')
        
        for gateway_name in self.active_gateways:
            status = self.gateway_status[gateway_name]
            if status.connected and status.avg_latency_ms < best_latency:
                best_latency = status.avg_latency_ms
                best_gateway = gateway_name
        
        return best_gateway
    
    async def _find_gateway_for_order(self, order_id: str) -> Optional[str]:
        """查找订单所在网关"""
        # 这里需要根据实际的订单管理机制来实现
        # 可能需要查询各个网关的订单记录
        
        for gateway_name in self.active_gateways:
            # 实际实现中需要查询网关的订单记录
            # 这里简化处理
            pass
        
        return self.active_gateways[0] if self.active_gateways else None
    
    async def _start_reconnection_monitoring(self):
        """启动重连监控"""
        if not self.config.enable_auto_reconnect:
            return
        
        for gateway_name in self.gateways.keys():
            task = asyncio.create_task(self._monitor_gateway_connection(gateway_name))
            self.reconnection_tasks[gateway_name] = task
    
    async def _stop_reconnection_monitoring(self):
        """停止重连监控"""
        for task in self.reconnection_tasks.values():
            if not task.done():
                task.cancel()
        
        self.reconnection_tasks.clear()
    
    async def _monitor_gateway_connection(self, gateway_name: str):
        """监控网关连接状态"""
        while True:
            try:
                await asyncio.sleep(self.config.reconnect_interval)
                
                status = self.gateway_status.get(gateway_name)
                if not status or status.connected:
                    continue
                
                # 检查是否需要重连
                if status.error_count < self.config.max_reconnect_attempts:
                    self.logger.info(f"尝试重连网关: {gateway_name}")
                    
                    gateway = self.gateways[gateway_name]
                    success = await self._connect_single_gateway(gateway_name, gateway)
                    
                    if success:
                        self.active_gateways.append(gateway_name)
                        self.logger.info(f"网关重连成功: {gateway_name}")
                    else:
                        self.logger.warning(f"网关重连失败: {gateway_name}")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"重连监控异常 {gateway_name}: {e}")
    
    async def _initialize_monitoring(self):
        """初始化监控系统"""
        # 启动性能监控
        asyncio.create_task(self._performance_monitoring_loop())
        
        # 启动健康检查
        asyncio.create_task(self._health_check_loop())
    
    async def _performance_monitoring_loop(self):
        """性能监控循环"""
        while True:
            try:
                await asyncio.sleep(60)  # 每分钟监控一次
                
                for gateway_name, status in self.gateway_status.items():
                    if status.connected:
                        # 更新性能指标
                        await self._update_performance_metrics(gateway_name, status)
                        
                        # 检查告警条件
                        await self._check_performance_alerts(gateway_name, status)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"性能监控异常: {e}")
    
    async def _health_check_loop(self):
        """健康检查循环"""
        while True:
            try:
                await asyncio.sleep(self.config.heartbeat_interval)
                
                for gateway_name in self.active_gateways:
                    await self._perform_health_check(gateway_name)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"健康检查异常: {e}")
    
    async def _update_performance_metrics(self, gateway_name: str, status: GatewayStatus):
        """更新性能指标"""
        # 实际实现中需要收集各种性能数据
        pass
    
    async def _check_performance_alerts(self, gateway_name: str, status: GatewayStatus):
        """检查性能告警"""
        if (self.config.alert_on_high_latency and 
            status.avg_latency_ms > self.config.latency_threshold_ms):
            await self._trigger_alert("high_latency", gateway_name, status)
    
    async def _perform_health_check(self, gateway_name: str):
        """执行健康检查"""
        # 实际实现中需要ping网关或执行简单查询
        status = self.gateway_status[gateway_name]
        status.last_heartbeat = datetime.now()
    
    async def _trigger_alert(self, alert_type: str, gateway_name: str, status: GatewayStatus):
        """触发告警"""
        self.logger.warning(f"告警触发: {alert_type} for {gateway_name}")
        
        # 调用告警回调
        for callback in self.event_callbacks.get('on_error', []):
            try:
                await callback(alert_type, gateway_name, status)
            except Exception as e:
                self.logger.error(f"告警回调执行失败: {e}")
    
    # 事件回调方法
    async def _on_gateway_connected(self, gateway_name: str):
        """网关连接回调"""
        self.logger.info(f"网关连接事件: {gateway_name}")
        
        for callback in self.event_callbacks.get('on_gateway_connected', []):
            try:
                await callback(gateway_name)
            except Exception as e:
                self.logger.error(f"连接回调执行失败: {e}")
    
    async def _on_gateway_disconnected(self, gateway_name: str):
        """网关断开回调"""
        self.logger.warning(f"网关断开事件: {gateway_name}")
        
        # 从活跃列表移除
        if gateway_name in self.active_gateways:
            self.active_gateways.remove(gateway_name)
        
        # 更新状态
        if gateway_name in self.gateway_status:
            self.gateway_status[gateway_name].connected = False
            self.gateway_status[gateway_name].last_disconnect_time = datetime.now()
        
        # 触发告警
        if self.config.alert_on_disconnect:
            await self._trigger_alert("gateway_disconnected", gateway_name, 
                                     self.gateway_status.get(gateway_name))
        
        for callback in self.event_callbacks.get('on_gateway_disconnected', []):
            try:
                await callback(gateway_name)
            except Exception as e:
                self.logger.error(f"断开回调执行失败: {e}")
    
    async def _on_order_update(self, order_data: Dict[str, Any]):
        """订单更新回调"""
        for callback in self.event_callbacks.get('on_order_update', []):
            try:
                await callback(order_data)
            except Exception as e:
                self.logger.error(f"订单更新回调执行失败: {e}")
    
    async def _on_trade_update(self, trade_data: Dict[str, Any]):
        """成交更新回调"""
        for callback in self.event_callbacks.get('on_trade_update', []):
            try:
                await callback(trade_data)
            except Exception as e:
                self.logger.error(f"成交更新回调执行失败: {e}")
    
    async def _on_position_update(self, position_data: Dict[str, Any]):
        """持仓更新回调"""
        for callback in self.event_callbacks.get('on_position_update', []):
            try:
                await callback(position_data)
            except Exception as e:
                self.logger.error(f"持仓更新回调执行失败: {e}")
    
    async def _on_account_update(self, account_data: Dict[str, Any]):
        """账户更新回调"""
        for callback in self.event_callbacks.get('on_account_update', []):
            try:
                await callback(account_data)
            except Exception as e:
                self.logger.error(f"账户更新回调执行失败: {e}")
    
    async def _on_gateway_error(self, error_data: Dict[str, Any]):
        """网关错误回调"""
        gateway_name = error_data.get('gateway', 'unknown')
        error_msg = error_data.get('message', 'unknown error')
        
        self.logger.error(f"网关错误: {gateway_name} - {error_msg}")
        
        # 更新错误计数
        if gateway_name in self.gateway_status:
            status = self.gateway_status[gateway_name]
            status.error_count += 1
            status.last_error = error_msg
        
        for callback in self.event_callbacks.get('on_error', []):
            try:
                await callback(error_data)
            except Exception as e:
                self.logger.error(f"错误回调执行失败: {e}")
    
    # 公共接口方法
    def on(self, event: str, callback):
        """注册事件回调"""
        if event in self.event_callbacks:
            self.event_callbacks[event].append(callback)
    
    def get_gateway_status(self) -> Dict[str, GatewayStatus]:
        """获取所有网关状态"""
        return self.gateway_status.copy()
    
    def get_active_gateways(self) -> List[str]:
        """获取活跃网关列表"""
        return self.active_gateways.copy()
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        return self.performance_metrics.copy()
    
    async def get_all_accounts(self) -> Dict[str, Dict[str, Any]]:
        """获取所有网关的账户信息"""
        accounts = {}
        
        for gateway_name in self.active_gateways:
            try:
                gateway = self.gateways[gateway_name]
                account_info = await gateway.query_account()
                accounts[gateway_name] = account_info
            except Exception as e:
                self.logger.error(f"查询账户信息失败 {gateway_name}: {e}")
        
        return accounts
    
    async def get_all_positions(self) -> Dict[str, Dict[str, Any]]:
        """获取所有网关的持仓信息"""
        positions = {}
        
        for gateway_name in self.active_gateways:
            try:
                gateway = self.gateways[gateway_name]
                position_info = await gateway.query_positions()
                positions[gateway_name] = position_info
            except Exception as e:
                self.logger.error(f"查询持仓信息失败 {gateway_name}: {e}")
        
        return positions