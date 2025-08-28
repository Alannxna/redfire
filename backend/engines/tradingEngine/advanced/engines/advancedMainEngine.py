"""
高级主引擎 - AdvancedMainEngine

基于vnpy-core的MainEngine实现，添加了以下高级功能：
1. 多连接管理 - 支持多个网关连接
2. 负载均衡 - 智能分配交易负载
3. 故障转移 - 自动故障检测和恢复
4. 性能监控 - 实时性能指标监控
5. 资源管理 - 智能资源分配和回收

作者: RedFire团队
创建时间: 2024年9月2日
"""

import os
import time
import threading
from typing import Dict, List, Optional, Type, Callable, Any
from collections import defaultdict
from dataclasses import dataclass
from enum import Enum

from ...baseEngine import BaseEngine
from ...mainEngine import MainTradingEngine
from ...eventEngine import EventTradingEngine
from ...gatewayInterface.baseGateway import BaseGatewayInterface


class ConnectionStatus(Enum):
    """连接状态枚举"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    AUTHENTICATED = "authenticated"
    TRADING = "trading"
    ERROR = "error"


class LoadBalanceStrategy(Enum):
    """负载均衡策略枚举"""
    ROUND_ROBIN = "round_robin"           # 轮询
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"  # 加权轮询
    LEAST_CONNECTIONS = "least_connections"  # 最少连接数
    RESPONSE_TIME = "response_time"        # 响应时间
    CUSTOM = "custom"                      # 自定义策略


@dataclass
class ConnectionInfo:
    """连接信息数据类"""
    gateway_name: str
    status: ConnectionStatus
    connect_time: Optional[float] = None
    last_heartbeat: Optional[float] = None
    response_time: Optional[float] = None
    error_count: int = 0
    weight: float = 1.0
    max_connections: int = 10
    current_connections: int = 0


class AdvancedMainEngine(BaseEngine):
    """
    高级主引擎
    
    继承自BaseEngine，提供增强的交易引擎功能
    """
    
    def __init__(self, main_engine: MainTradingEngine, event_engine: EventTradingEngine, engine_name: str = "AdvancedMainEngine"):
        super().__init__(main_engine, event_engine, engine_name)
        
        # 连接管理
        self.connections: Dict[str, ConnectionInfo] = {}
        self.connection_locks: Dict[str, threading.Lock] = {}
        
        # 负载均衡
        self.load_balance_strategy = LoadBalanceStrategy.WEIGHTED_ROUND_ROBIN
        self.current_gateway_index = 0
        self.gateway_weights: Dict[str, float] = {}
        
        # 性能监控
        self.performance_metrics = defaultdict(list)
        self.monitoring_enabled = True
        
        # 故障转移
        self.failover_enabled = True
        self.auto_reconnect = True
        self.max_reconnect_attempts = 3
        
        # 初始化
        self._init_advanced_features()
    
    def _init_advanced_features(self):
        """初始化高级功能"""
        self.logInfo("初始化高级主引擎功能")
        
        # 启动监控线程
        if self.monitoring_enabled:
            self._start_monitoring_thread()
        
        # 启动故障检测线程
        if self.failover_enabled:
            self._start_failover_thread()
    
    def add_gateway_with_monitoring(self, gateway_class: Type[BaseGatewayInterface], 
                                  gateway_name: str = "", 
                                  weight: float = 1.0,
                                  max_connections: int = 10) -> BaseGatewayInterface:
        """
        添加带监控的网关
        
        参数:
            gateway_class: 网关类
            gateway_name: 网关名称
            weight: 负载均衡权重
            max_connections: 最大连接数
            
        返回:
            创建的网关实例
        """
        # 使用父类方法添加网关
        gateway = self.main_engine.add_gateway(gateway_class, gateway_name)
        
        # 创建连接信息
        connection_info = ConnectionInfo(
            gateway_name=gateway_name or gateway_class.__name__,
            status=ConnectionStatus.DISCONNECTED,
            weight=weight,
            max_connections=max_connections
        )
        
        # 存储连接信息
        self.connections[gateway_name or gateway_class.__name__] = connection_info
        self.connection_locks[gateway_name or gateway_class.__name__] = threading.Lock()
        self.gateway_weights[gateway_name or gateway_class.__name__] = weight
        
        self.logInfo(f"添加网关 {gateway_name or gateway_class.__name__}，权重: {weight}")
        return gateway
    
    def get_optimal_gateway(self, strategy: Optional[LoadBalanceStrategy] = None) -> Optional[str]:
        """
        获取最优网关
        
        参数:
            strategy: 负载均衡策略，如果为None则使用默认策略
            
        返回:
            最优网关名称
        """
        if not self.connections:
            return None
        
        strategy = strategy or self.load_balance_strategy
        
        if strategy == LoadBalanceStrategy.ROUND_ROBIN:
            return self._round_robin_selection()
        elif strategy == LoadBalanceStrategy.WEIGHTED_ROUND_ROBIN:
            return self._weighted_round_robin_selection()
        elif strategy == LoadBalanceStrategy.LEAST_CONNECTIONS:
            return self._least_connections_selection()
        elif strategy == LoadBalanceStrategy.RESPONSE_TIME:
            return self._response_time_selection()
        else:
            return self._custom_selection()
    
    def _round_robin_selection(self) -> str:
        """轮询选择"""
        gateway_names = list(self.connections.keys())
        if not gateway_names:
            return ""
        
        self.current_gateway_index = (self.current_gateway_index + 1) % len(gateway_names)
        return gateway_names[self.current_gateway_index]
    
    def _weighted_round_robin_selection(self) -> str:
        """加权轮询选择"""
        # 简化的加权轮询实现
        total_weight = sum(self.gateway_weights.values())
        if total_weight <= 0:
            return self._round_robin_selection()
        
        # 这里可以实现更复杂的加权轮询算法
        return self._round_robin_selection()
    
    def _least_connections_selection(self) -> str:
        """最少连接数选择"""
        min_connections = float('inf')
        selected_gateway = ""
        
        for gateway_name, conn_info in self.connections.items():
            if (conn_info.status == ConnectionStatus.TRADING and 
                conn_info.current_connections < min_connections):
                min_connections = conn_info.current_connections
                selected_gateway = gateway_name
        
        return selected_gateway or list(self.connections.keys())[0]
    
    def _response_time_selection(self) -> str:
        """响应时间选择"""
        min_response_time = float('inf')
        selected_gateway = ""
        
        for gateway_name, conn_info in self.connections.items():
            if (conn_info.status == ConnectionStatus.TRADING and 
                conn_info.response_time is not None and
                conn_info.response_time < min_response_time):
                min_response_time = conn_info.response_time
                selected_gateway = gateway_name
        
        return selected_gateway or list(self.connections.keys())[0]
    
    def _custom_selection(self) -> str:
        """自定义选择策略"""
        # 可以在这里实现自定义的选择逻辑
        return self._weighted_round_robin_selection()
    
    def update_connection_status(self, gateway_name: str, status: ConnectionStatus, 
                               response_time: Optional[float] = None):
        """
        更新连接状态
        
        参数:
            gateway_name: 网关名称
            status: 新状态
            response_time: 响应时间
        """
        if gateway_name not in self.connections:
            return
        
        with self.connection_locks[gateway_name]:
            conn_info = self.connections[gateway_name]
            old_status = conn_info.status
            conn_info.status = status
            
            if status == ConnectionStatus.CONNECTED:
                conn_info.connect_time = time.time()
                conn_info.error_count = 0
            elif status == ConnectionStatus.ERROR:
                conn_info.error_count += 1
            
            if response_time is not None:
                conn_info.response_time = response_time
            
            self.logInfo(f"网关 {gateway_name} 状态从 {old_status.value} 更新为 {status.value}")
    
    def get_connection_stats(self) -> Dict[str, Dict[str, Any]]:
        """
        获取连接统计信息
        
        返回:
            连接统计信息字典
        """
        stats = {}
        for gateway_name, conn_info in self.connections.items():
            stats[gateway_name] = {
                "status": conn_info.status.value,
                "connect_time": conn_info.connect_time,
                "last_heartbeat": conn_info.last_heartbeat,
                "response_time": conn_info.response_time,
                "error_count": conn_info.error_count,
                "weight": conn_info.weight,
                "current_connections": conn_info.current_connections,
                "max_connections": conn_info.max_connections
            }
        return stats
    
    def _start_monitoring_thread(self):
        """启动监控线程"""
        def monitor_loop():
            while self.monitoring_enabled:
                try:
                    self._collect_performance_metrics()
                    time.sleep(5)  # 每5秒收集一次指标
                except Exception as e:
                    self.logError(f"监控线程异常: {e}")
        
        monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        monitor_thread.start()
        self.logInfo("启动性能监控线程")
    
    def _start_failover_thread(self):
        """启动故障转移线程"""
        def failover_loop():
            while self.failover_enabled:
                try:
                    self._check_connection_health()
                    time.sleep(10)  # 每10秒检查一次连接健康状态
                except Exception as e:
                    self.logError(f"故障转移线程异常: {e}")
        
        failover_thread = threading.Thread(target=failover_loop, daemon=True)
        failover_thread.start()
        self.logInfo("启动故障转移线程")
    
    def _collect_performance_metrics(self):
        """收集性能指标"""
        for gateway_name, conn_info in self.connections.items():
            if conn_info.response_time is not None:
                self.performance_metrics[gateway_name].append(conn_info.response_time)
                
                # 只保留最近100个指标
                if len(self.performance_metrics[gateway_name]) > 100:
                    self.performance_metrics[gateway_name] = self.performance_metrics[gateway_name][-100:]
    
    def _check_connection_health(self):
        """检查连接健康状态"""
        current_time = time.time()
        
        for gateway_name, conn_info in self.connections.items():
            # 检查心跳超时
            if (conn_info.last_heartbeat and 
                current_time - conn_info.last_heartbeat > 30):  # 30秒心跳超时
                self.logWarning(f"网关 {gateway_name} 心跳超时")
                self.update_connection_status(gateway_name, ConnectionStatus.ERROR)
                
                # 尝试自动重连
                if self.auto_reconnect and conn_info.error_count < self.max_reconnect_attempts:
                    self._attempt_reconnect(gateway_name)
    
    def _attempt_reconnect(self, gateway_name: str):
        """尝试重连"""
        self.logInfo(f"尝试重连网关 {gateway_name}")
        # 这里可以实现具体的重连逻辑
        pass
    
    def logInfo(self, message: str):
        """记录信息日志"""
        self.main_engine.logInfo(f"[{self.engine_name}] {message}")
    
    def logWarning(self, message: str):
        """记录警告日志"""
        self.main_engine.logWarning(f"[{self.engine_name}] {message}")
    
    def logError(self, message: str):
        """记录错误日志"""
        self.main_engine.logError(f"[{self.engine_name}] {message}")
    
    def close(self):
        """关闭引擎"""
        self.logInfo("关闭高级主引擎")
        self.monitoring_enabled = False
        self.failover_enabled = False
        super().close()
