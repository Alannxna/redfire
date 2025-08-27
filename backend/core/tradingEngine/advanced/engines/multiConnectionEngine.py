"""
多连接引擎 - MultiConnectionEngine

实现多网关连接管理，包括：
1. 多网关连接 - 同时连接多个交易网关
2. 连接池管理 - 动态管理连接数量
3. 负载均衡 - 智能分配交易负载
4. 故障转移 - 自动故障检测和恢复
5. 性能监控 - 实时性能指标监控

作者: RedFire团队
创建时间: 2024年9月2日
"""

import time
import threading
from typing import Dict, List, Optional, Type, Any, Callable
from dataclasses import dataclass
from enum import Enum
from collections import defaultdict, deque

from ...baseEngine import BaseEngine
from ...mainEngine import MainTradingEngine
from ...eventEngine import EventTradingEngine
from ...gatewayInterface.baseGateway import BaseGatewayInterface
from ..managers.connectionManager import ConnectionManager, ConnectionConfig, ConnectionType
from ..utils.engineUtils import EngineUtils


class ConnectionStrategy(Enum):
    """连接策略枚举"""
    ACTIVE_ACTIVE = "active_active"      # 主备模式
    ACTIVE_STANDBY = "active_standby"    # 主备模式
    LOAD_BALANCE = "load_balance"        # 负载均衡模式
    FAILOVER = "failover"                # 故障转移模式


@dataclass
class GatewayConfig:
    """网关配置"""
    gateway_class: Type[BaseGatewayInterface]
    gateway_name: str
    weight: float = 1.0
    max_connections: int = 10
    min_connections: int = 2
    priority: int = 0
    is_primary: bool = False
    auto_reconnect: bool = True
    connection_timeout: float = 30.0


class MultiConnectionEngine(BaseEngine):
    """
    多连接引擎
    
    管理多个网关连接，提供负载均衡和故障转移功能
    """
    
    def __init__(self, main_engine: MainTradingEngine, event_engine: EventTradingEngine, engine_name: str = "MultiConnectionEngine"):
        super().__init__(main_engine, event_engine, engine_name)
        
        # 网关配置
        self.gateway_configs: Dict[str, GatewayConfig] = {}
        self.active_gateways: Dict[str, BaseGatewayInterface] = {}
        
        # 连接策略
        self.connection_strategy = ConnectionStrategy.LOAD_BALANCE
        self.primary_gateway: Optional[str] = None
        
        # 负载均衡
        self.load_balance_enabled = True
        self.current_gateway_index = 0
        self.gateway_usage_stats: Dict[str, Dict[str, Any]] = defaultdict(dict)
        
        # 故障转移
        self.failover_enabled = True
        self.failover_threshold = 3
        self.gateway_health_status: Dict[str, bool] = {}
        
        # 连接管理器
        self.connection_manager = ConnectionManager(main_engine, event_engine)
        
        # 工具类
        self.utils = EngineUtils()
        
        # 初始化
        self._init_multi_connection_engine()
    
    def _init_multi_connection_engine(self):
        """初始化多连接引擎"""
        self.logInfo("初始化多连接引擎")
        
        # 启动健康监控
        if self.failover_enabled:
            self._start_health_monitoring()
    
    def add_gateway(self, config: GatewayConfig) -> BaseGatewayInterface:
        """
        添加网关
        
        参数:
            config: 网关配置
            
        返回:
            创建的网关实例
        """
        # 创建网关实例
        gateway = self.main_engine.add_gateway(config.gateway_class, config.gateway_name)
        
        # 存储配置和实例
        self.gateway_configs[config.gateway_name] = config
        self.active_gateways[config.gateway_name] = gateway
        
        # 初始化健康状态
        self.gateway_health_status[config.gateway_name] = True
        
        # 设置主网关
        if config.is_primary:
            self.primary_gateway = config.gateway_name
        
        # 创建连接池
        connection_config = ConnectionConfig(
            gateway_name=config.gateway_name,
            connection_type=ConnectionType.TRADING,
            max_connections=config.max_connections,
            min_connections=config.min_connections,
            connection_timeout=config.connection_timeout
        )
        
        self.connection_manager.create_connection_pool(connection_config)
        
        self.logInfo(f"添加网关 {config.gateway_name}，权重: {config.weight}")
        return gateway
    
    def remove_gateway(self, gateway_name: str):
        """
        移除网关
        
        参数:
            gateway_name: 网关名称
        """
        if gateway_name in self.active_gateways:
            # 关闭网关
            gateway = self.active_gateways[gateway_name]
            gateway.close()
            
            # 清理相关数据
            del self.active_gateways[gateway_name]
            del self.gateway_configs[gateway_name]
            del self.gateway_health_status[gateway_name]
            
            # 如果移除的是主网关，重新选择主网关
            if self.primary_gateway == gateway_name:
                self._select_new_primary_gateway()
            
            self.logInfo(f"移除网关 {gateway_name}")
    
    def _select_new_primary_gateway(self):
        """选择新的主网关"""
        if not self.active_gateways:
            self.primary_gateway = None
            return
        
        # 按优先级和权重选择
        candidates = []
        for name, config in self.gateway_configs.items():
            if name in self.active_gateways and self.gateway_health_status.get(name, False):
                candidates.append((name, config.priority, config.weight))
        
        if candidates:
            # 按优先级排序，优先级相同时按权重排序
            candidates.sort(key=lambda x: (-x[1], -x[2]))
            self.primary_gateway = candidates[0][0]
            self.logInfo(f"选择新的主网关: {self.primary_gateway}")
    
    def get_optimal_gateway(self, strategy: Optional[ConnectionStrategy] = None) -> Optional[str]:
        """
        获取最优网关
        
        参数:
            strategy: 连接策略，如果为None则使用默认策略
            
        返回:
            最优网关名称
        """
        strategy = strategy or self.connection_strategy
        
        if strategy == ConnectionStrategy.ACTIVE_ACTIVE:
            return self._get_active_active_gateway()
        elif strategy == ConnectionStrategy.ACTIVE_STANDBY:
            return self._get_active_standby_gateway()
        elif strategy == ConnectionStrategy.LOAD_BALANCE:
            return self._get_load_balance_gateway()
        elif strategy == ConnectionStrategy.FAILOVER:
            return self._get_failover_gateway()
        else:
            return self._get_default_gateway()
    
    def _get_active_active_gateway(self) -> Optional[str]:
        """获取主备模式网关"""
        # 优先返回主网关
        if self.primary_gateway and self.gateway_health_status.get(self.primary_gateway, False):
            return self.primary_gateway
        
        # 返回第一个健康的网关
        for name, is_healthy in self.gateway_health_status.items():
            if is_healthy:
                return name
        
        return None
    
    def _get_active_standby_gateway(self) -> Optional[str]:
        """获取主备模式网关"""
        # 只返回主网关
        if self.primary_gateway and self.gateway_health_status.get(self.primary_gateway, False):
            return self.primary_gateway
        
        return None
    
    def _get_load_balance_gateway(self) -> Optional[str]:
        """获取负载均衡网关"""
        healthy_gateways = [name for name, is_healthy in self.gateway_health_status.items() if is_healthy]
        
        if not healthy_gateways:
            return None
        
        # 轮询选择
        self.current_gateway_index = (self.current_gateway_index + 1) % len(healthy_gateways)
        selected_gateway = healthy_gateways[self.current_gateway_index]
        
        # 更新使用统计
        self._update_gateway_usage(selected_gateway)
        
        return selected_gateway
    
    def _get_failover_gateway(self) -> Optional[str]:
        """获取故障转移网关"""
        # 优先返回主网关
        if self.primary_gateway and self.gateway_health_status.get(self.primary_gateway, False):
            return self.primary_gateway
        
        # 按优先级选择备用网关
        candidates = []
        for name, config in self.gateway_configs.items():
            if name in self.active_gateways and self.gateway_health_status.get(name, False):
                candidates.append((name, config.priority))
        
        if candidates:
            candidates.sort(key=lambda x: -x[1])  # 按优先级降序
            return candidates[0][0]
        
        return None
    
    def _get_default_gateway(self) -> Optional[str]:
        """获取默认网关"""
        # 返回第一个可用的网关
        for name in self.active_gateways:
            if self.gateway_health_status.get(name, False):
                return name
        
        return None
    
    def _update_gateway_usage(self, gateway_name: str):
        """更新网关使用统计"""
        current_time = time.time()
        
        if gateway_name not in self.gateway_usage_stats:
            self.gateway_usage_stats[gateway_name] = {
                "total_requests": 0,
                "last_used": current_time,
                "response_times": deque(maxlen=100)
            }
        
        stats = self.gateway_usage_stats[gateway_name]
        stats["total_requests"] += 1
        stats["last_used"] = current_time
    
    def execute_on_gateway(self, operation: str, gateway_name: Optional[str] = None, 
                          *args, **kwargs) -> Any:
        """
        在指定网关上执行操作
        
        参数:
            operation: 操作名称
            gateway_name: 网关名称，如果为None则自动选择
            *args: 位置参数
            **kwargs: 关键字参数
            
        返回:
            操作结果
        """
        # 选择网关
        if gateway_name is None:
            gateway_name = self.get_optimal_gateway()
        
        if not gateway_name or gateway_name not in self.active_gateways:
            raise ValueError(f"无效的网关名称: {gateway_name}")
        
        gateway = self.active_gateways[gateway_name]
        
        # 检查网关健康状态
        if not self.gateway_health_status.get(gateway_name, False):
            raise RuntimeError(f"网关 {gateway_name} 不健康")
        
        try:
            # 执行操作
            if hasattr(gateway, operation):
                method = getattr(gateway, operation)
                if callable(method):
                    result = method(*args, **kwargs)
                    
                    # 更新使用统计
                    self._update_gateway_usage(gateway_name)
                    
                    return result
                else:
                    raise AttributeError(f"网关 {gateway_name} 的 {operation} 不是可调用方法")
            else:
                raise AttributeError(f"网关 {gateway_name} 没有 {operation} 方法")
        
        except Exception as e:
            # 记录错误并更新健康状态
            self.logError(f"在网关 {gateway_name} 上执行 {operation} 失败: {e}")
            self._update_gateway_health(gateway_name, False)
            raise
    
    def _start_health_monitoring(self):
        """启动健康监控"""
        def health_check_loop():
            while self.failover_enabled:
                try:
                    self._check_all_gateways_health()
                    time.sleep(10)  # 每10秒检查一次
                except Exception as e:
                    self.logError(f"健康监控异常: {e}")
        
        health_thread = threading.Thread(target=health_check_loop, daemon=True)
        health_thread.start()
        self.logInfo("启动网关健康监控")
    
    def _check_all_gateways_health(self):
        """检查所有网关的健康状态"""
        for gateway_name in list(self.active_gateways.keys()):
            try:
                is_healthy = self._check_gateway_health(gateway_name)
                self._update_gateway_health(gateway_name, is_healthy)
            except Exception as e:
                self.logError(f"检查网关 {gateway_name} 健康状态异常: {e}")
                self._update_gateway_health(gateway_name, False)
    
    def _check_gateway_health(self, gateway_name: str) -> bool:
        """检查单个网关的健康状态"""
        gateway = self.active_gateways.get(gateway_name)
        if not gateway:
            return False
        
        try:
            # 这里可以实现具体的健康检查逻辑
            # 比如检查连接状态、发送心跳等
            
            # 简单的健康检查：检查网关是否有基本属性
            has_required_attrs = all(hasattr(gateway, attr) for attr in ['is_connected', 'get_status'])
            
            if has_required_attrs:
                # 检查连接状态
                if hasattr(gateway, 'is_connected') and callable(gateway.is_connected):
                    return gateway.is_connected()
                else:
                    return True  # 如果没有连接检查方法，认为健康
            
            return has_required_attrs
        
        except Exception as e:
            self.logError(f"检查网关 {gateway_name} 健康状态失败: {e}")
            return False
    
    def _update_gateway_health(self, gateway_name: str, is_healthy: bool):
        """更新网关健康状态"""
        old_status = self.gateway_health_status.get(gateway_name, True)
        self.gateway_health_status[gateway_name] = is_healthy
        
        if old_status != is_healthy:
            if is_healthy:
                self.logInfo(f"网关 {gateway_name} 恢复健康")
            else:
                self.logWarning(f"网关 {gateway_name} 健康状态异常")
                
                # 如果主网关不健康，选择新的主网关
                if gateway_name == self.primary_gateway:
                    self._select_new_primary_gateway()
    
    def get_multi_connection_stats(self) -> Dict[str, Any]:
        """获取多连接引擎统计信息"""
        return {
            "total_gateways": len(self.active_gateways),
            "healthy_gateways": sum(self.gateway_health_status.values()),
            "primary_gateway": self.primary_gateway,
            "connection_strategy": self.connection_strategy.value,
            "gateway_health": dict(self.gateway_health_status),
            "gateway_usage": dict(self.gateway_usage_stats),
            "connection_manager_stats": self.connection_manager.get_connection_manager_stats()
        }
    
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
        """关闭多连接引擎"""
        self.logInfo("关闭多连接引擎")
        
        # 关闭所有网关
        for gateway_name, gateway in self.active_gateways.items():
            try:
                gateway.close()
            except Exception as e:
                self.logError(f"关闭网关 {gateway_name} 异常: {e}")
        
        # 关闭连接管理器
        self.connection_manager.close()
        
        self.failover_enabled = False
        super().close()
