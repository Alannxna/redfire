"""
连接管理器 - ConnectionManager

负责管理所有网关连接，包括：
1. 连接池管理 - 创建、销毁、复用连接
2. 故障转移 - 自动故障检测和恢复
3. 健康监控 - 连接状态监控和告警
4. 负载均衡 - 智能连接分配

作者: RedFire团队
创建时间: 2024年9月2日
"""

import time
import threading
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum
from collections import deque
import queue

from ...baseEngine import BaseEngine
from ...mainEngine import MainTradingEngine
from ...eventEngine import EventTradingEngine


class ConnectionType(Enum):
    """连接类型枚举"""
    TRADING = "trading"      # 交易连接
    MARKET_DATA = "market_data"  # 行情数据连接
    QUERY = "query"          # 查询连接
    STREAMING = "streaming"  # 流式数据连接


class ConnectionHealth(Enum):
    """连接健康状态枚举"""
    HEALTHY = "healthy"      # 健康
    WARNING = "warning"      # 警告
    CRITICAL = "critical"    # 严重
    DEAD = "dead"            # 死亡


@dataclass
class ConnectionConfig:
    """连接配置"""
    gateway_name: str
    connection_type: ConnectionType
    max_connections: int = 10
    min_connections: int = 2
    connection_timeout: float = 30.0
    heartbeat_interval: float = 10.0
    retry_interval: float = 5.0
    max_retries: int = 3
    weight: float = 1.0


@dataclass
class ConnectionInstance:
    """连接实例"""
    connection_id: str
    gateway_name: str
    connection_type: ConnectionType
    created_time: float
    last_used_time: float
    last_heartbeat: float
    health_status: ConnectionHealth
    is_active: bool = True
    error_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


class ConnectionPool:
    """连接池"""
    
    def __init__(self, config: ConnectionConfig):
        self.config = config
        self.connections: Dict[str, ConnectionInstance] = {}
        self.available_connections: queue.Queue = queue.Queue()
        self.connection_lock = threading.Lock()
        self.health_check_thread = None
        self.running = False
        
        # 初始化连接池
        self._init_pool()
    
    def _init_pool(self):
        """初始化连接池"""
        for i in range(self.config.min_connections):
            self._create_connection()
    
    def _create_connection(self) -> Optional[ConnectionInstance]:
        """创建新连接"""
        try:
            connection_id = f"{self.config.gateway_name}_{self.config.connection_type.value}_{len(self.connections)}"
            connection = ConnectionInstance(
                connection_id=connection_id,
                gateway_name=self.config.gateway_name,
                connection_type=self.config.connection_type,
                created_time=time.time(),
                last_used_time=time.time(),
                last_heartbeat=time.time(),
                health_status=ConnectionHealth.HEALTHY
            )
            
            with self.connection_lock:
                self.connections[connection_id] = connection
                self.available_connections.put(connection_id)
            
            return connection
        except Exception as e:
            print(f"创建连接失败: {e}")
            return None
    
    def get_connection(self, timeout: float = 5.0) -> Optional[ConnectionInstance]:
        """
        获取可用连接
        
        参数:
            timeout: 超时时间
            
        返回:
            连接实例或None
        """
        try:
            # 尝试从可用连接队列获取
            connection_id = self.available_connections.get(timeout=timeout)
            connection = self.connections.get(connection_id)
            
            if connection and connection.is_active:
                connection.last_used_time = time.time()
                return connection
            
            # 如果没有可用连接，尝试创建新连接
            if len(self.connections) < self.config.max_connections:
                return self._create_connection()
            
            return None
        except queue.Empty:
            return None
    
    def return_connection(self, connection: ConnectionInstance):
        """
        归还连接到连接池
        
        参数:
            connection: 要归还的连接
        """
        if connection.connection_id in self.connections:
            connection.last_used_time = time.time()
            self.available_connections.put(connection.connection_id)
    
    def remove_connection(self, connection_id: str):
        """
        移除连接
        
        参数:
            connection_id: 连接ID
        """
        with self.connection_lock:
            if connection_id in self.connections:
                del self.connections[connection_id]
    
    def start_health_check(self):
        """启动健康检查"""
        if self.health_check_thread and self.health_check_thread.is_alive():
            return
        
        self.running = True
        self.health_check_thread = threading.Thread(target=self._health_check_loop, daemon=True)
        self.health_check_thread.start()
    
    def stop_health_check(self):
        """停止健康检查"""
        self.running = False
        if self.health_check_thread:
            self.health_check_thread.join(timeout=5.0)
    
    def _health_check_loop(self):
        """健康检查循环"""
        while self.running:
            try:
                self._check_all_connections()
                time.sleep(self.config.heartbeat_interval)
            except Exception as e:
                print(f"健康检查异常: {e}")
    
    def _check_all_connections(self):
        """检查所有连接的健康状态"""
        current_time = time.time()
        
        for connection_id, connection in list(self.connections.items()):
            # 检查心跳超时
            if current_time - connection.last_heartbeat > self.config.heartbeat_interval * 2:
                connection.health_status = ConnectionHealth.WARNING
                connection.error_count += 1
            
            # 检查连接是否死亡
            if connection.error_count >= self.config.max_retries:
                connection.health_status = ConnectionHealth.DEAD
                connection.is_active = False
                self.remove_connection(connection_id)
                
                # 尝试创建新连接
                if len(self.connections) < self.config.max_connections:
                    self._create_connection()
    
    def get_pool_stats(self) -> Dict[str, Any]:
        """获取连接池统计信息"""
        with self.connection_lock:
            total_connections = len(self.connections)
            active_connections = sum(1 for c in self.connections.values() if c.is_active)
            available_connections = self.available_connections.qsize()
            
            return {
                "total_connections": total_connections,
                "active_connections": active_connections,
                "available_connections": available_connections,
                "max_connections": self.config.max_connections,
                "min_connections": self.config.min_connections,
                "connection_type": self.config.connection_type.value,
                "gateway_name": self.config.gateway_name
            }


class ConnectionManager(BaseEngine):
    """
    连接管理器
    
    管理所有网关连接的生命周期
    """
    
    def __init__(self, main_engine: MainTradingEngine, event_engine: EventTradingEngine, engine_name: str = "ConnectionManager"):
        super().__init__(main_engine, event_engine, engine_name)
        
        # 连接池管理
        self.connection_pools: Dict[str, ConnectionPool] = {}
        self.pool_configs: Dict[str, ConnectionConfig] = {}
        
        # 故障转移配置
        self.failover_enabled = True
        self.auto_reconnect = True
        self.failover_threshold = 3
        
        # 健康监控
        self.health_monitoring_enabled = True
        self.health_check_interval = 10.0
        
        # 统计信息
        self.connection_stats = {}
        self.performance_metrics = {}
        
        # 初始化
        self._init_connection_manager()
    
    def _init_connection_manager(self):
        """初始化连接管理器"""
        self.logInfo("初始化连接管理器")
        
        if self.health_monitoring_enabled:
            self._start_health_monitoring()
    
    def create_connection_pool(self, config: ConnectionConfig) -> ConnectionPool:
        """
        创建连接池
        
        参数:
            config: 连接配置
            
        返回:
            连接池实例
        """
        pool_key = f"{config.gateway_name}_{config.connection_type.value}"
        
        if pool_key in self.connection_pools:
            self.logWarning(f"连接池 {pool_key} 已存在")
            return self.connection_pools[pool_key]
        
        # 创建连接池
        connection_pool = ConnectionPool(config)
        self.connection_pools[pool_key] = connection_pool
        self.pool_configs[pool_key] = config
        
        # 启动健康检查
        connection_pool.start_health_check()
        
        self.logInfo(f"创建连接池 {pool_key}，最大连接数: {config.max_connections}")
        return connection_pool
    
    def get_connection_pool(self, gateway_name: str, connection_type: ConnectionType) -> Optional[ConnectionPool]:
        """
        获取连接池
        
        参数:
            gateway_name: 网关名称
            connection_type: 连接类型
            
        返回:
            连接池实例或None
        """
        pool_key = f"{gateway_name}_{connection_type.value}"
        return self.connection_pools.get(pool_key)
    
    def get_optimal_connection(self, gateway_name: str, connection_type: ConnectionType, 
                             strategy: str = "least_used") -> Optional[ConnectionInstance]:
        """
        获取最优连接
        
        参数:
            gateway_name: 网关名称
            connection_type: 连接类型
            strategy: 选择策略
            
        返回:
            连接实例或None
        """
        pool = self.get_connection_pool(gateway_name, connection_type)
        if not pool:
            return None
        
        if strategy == "least_used":
            return self._get_least_used_connection(pool)
        elif strategy == "round_robin":
            return self._get_round_robin_connection(pool)
        elif strategy == "health_based":
            return self._get_health_based_connection(pool)
        else:
            return pool.get_connection()
    
    def _get_least_used_connection(self, pool: ConnectionPool) -> Optional[ConnectionInstance]:
        """获取最少使用的连接"""
        connections = list(pool.connections.values())
        if not connections:
            return None
        
        # 按最后使用时间排序，选择最久未使用的
        connections.sort(key=lambda x: x.last_used_time)
        return connections[0]
    
    def _get_round_robin_connection(self, pool: ConnectionPool) -> Optional[ConnectionInstance]:
        """轮询获取连接"""
        return pool.get_connection()
    
    def _get_health_based_connection(self, pool: ConnectionPool) -> Optional[ConnectionInstance]:
        """基于健康状态获取连接"""
        connections = [c for c in pool.connections.values() if c.is_active]
        if not connections:
            return None
        
        # 按健康状态排序，优先选择健康的连接
        connections.sort(key=lambda x: (x.health_status.value, x.error_count))
        return connections[0]
    
    def monitor_connection_health(self, gateway_name: str, connection_type: ConnectionType):
        """
        监控连接健康状态
        
        参数:
            gateway_name: 网关名称
            connection_type: 连接类型
        """
        pool = self.get_connection_pool(gateway_name, connection_type)
        if not pool:
            return
        
        stats = pool.get_pool_stats()
        self.connection_stats[f"{gateway_name}_{connection_type.value}"] = stats
        
        # 检查是否需要故障转移
        if self.failover_enabled and stats["active_connections"] == 0:
            self._trigger_failover(gateway_name, connection_type)
    
    def _trigger_failover(self, gateway_name: str, connection_type: ConnectionType):
        """
        触发故障转移
        
        参数:
            gateway_name: 网关名称
            connection_type: 连接类型
        """
        self.logWarning(f"触发故障转移: {gateway_name} {connection_type.value}")
        
        # 这里可以实现具体的故障转移逻辑
        # 比如切换到备用网关、重新创建连接等
        
        if self.auto_reconnect:
            self._attempt_reconnect(gateway_name, connection_type)
    
    def _attempt_reconnect(self, gateway_name: str, connection_type: ConnectionType):
        """
        尝试重连
        
        参数:
            gateway_name: 网关名称
            connection_type: 连接类型
        """
        self.logInfo(f"尝试重连: {gateway_name} {connection_type.value}")
        
        # 重新创建连接池
        config = self.pool_configs.get(f"{gateway_name}_{connection_type.value}")
        if config:
            # 移除旧的连接池
            pool_key = f"{gateway_name}_{connection_type.value}"
            if pool_key in self.connection_pools:
                old_pool = self.connection_pools[pool_key]
                old_pool.stop_health_check()
                del self.connection_pools[pool_key]
            
            # 创建新的连接池
            self.create_connection_pool(config)
    
    def _start_health_monitoring(self):
        """启动健康监控"""
        def monitoring_loop():
            while self.health_monitoring_enabled:
                try:
                    # 监控所有连接池
                    for pool_key, pool in self.connection_pools.items():
                        gateway_name, connection_type_str = pool_key.split("_", 1)
                        connection_type = ConnectionType(connection_type_str)
                        self.monitor_connection_health(gateway_name, connection_type)
                    
                    time.sleep(self.health_check_interval)
                except Exception as e:
                    self.logError(f"健康监控异常: {e}")
        
        monitoring_thread = threading.Thread(target=monitoring_loop, daemon=True)
        monitoring_thread.start()
        self.logInfo("启动连接健康监控")
    
    def get_connection_manager_stats(self) -> Dict[str, Any]:
        """获取连接管理器统计信息"""
        stats = {
            "total_pools": len(self.connection_pools),
            "connection_pools": {},
            "failover_enabled": self.failover_enabled,
            "auto_reconnect": self.auto_reconnect,
            "health_monitoring": self.health_monitoring_enabled
        }
        
        for pool_key, pool in self.connection_pools.items():
            stats["connection_pools"][pool_key] = pool.get_pool_stats()
        
        return stats
    
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
        """关闭连接管理器"""
        self.logInfo("关闭连接管理器")
        
        # 停止所有连接池的健康检查
        for pool in self.connection_pools.values():
            pool.stop_health_check()
        
        # 清空连接池
        self.connection_pools.clear()
        
        self.health_monitoring_enabled = False
        super().close()
