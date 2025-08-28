"""
负载均衡引擎 - LoadBalancingEngine

实现智能负载均衡，包括：
1. 多种负载均衡算法 - 轮询、加权、最少连接等
2. 动态负载调整 - 根据性能指标自动调整
3. 健康检查 - 实时监控网关健康状态
4. 性能优化 - 自动优化负载分配策略
5. 统计报告 - 详细的负载均衡统计信息

作者: RedFire团队
创建时间: 2024年9月2日
"""

import time
import threading
import random
from typing import Dict, List, Optional, Any, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
import statistics

from ...baseEngine import BaseEngine
from ...mainEngine import MainTradingEngine
from ...eventEngine import EventTradingEngine
from ...gatewayInterface.baseGateway import BaseGatewayInterface
from ..utils.engineUtils import EngineUtils


class LoadBalanceAlgorithm(Enum):
    """负载均衡算法枚举"""
    ROUND_ROBIN = "round_robin"           # 轮询
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"  # 加权轮询
    LEAST_CONNECTIONS = "least_connections"  # 最少连接数
    LEAST_RESPONSE_TIME = "least_response_time"  # 最少响应时间
    WEIGHTED_LEAST_CONNECTIONS = "weighted_least_connections"  # 加权最少连接数
    CONSISTENT_HASH = "consistent_hash"    # 一致性哈希
    RANDOM = "random"                      # 随机
    CUSTOM = "custom"                      # 自定义算法


@dataclass
class GatewayLoadInfo:
    """网关负载信息"""
    gateway_name: str
    current_connections: int = 0
    max_connections: int = 100
    response_time: float = 0.0
    error_rate: float = 0.0
    weight: float = 1.0
    priority: int = 0
    is_healthy: bool = True
    last_used: float = 0.0
    total_requests: int = 0
    success_requests: int = 0
    response_times: deque = field(default_factory=lambda: deque(maxlen=100))
    
    @property
    def connection_usage(self) -> float:
        """连接使用率"""
        return self.current_connections / self.max_connections if self.max_connections > 0 else 0.0
    
    @property
    def success_rate(self) -> float:
        """成功率"""
        return self.success_requests / self.total_requests if self.total_requests > 0 else 1.0
    
    @property
    def avg_response_time(self) -> float:
        """平均响应时间"""
        if self.response_times:
            return statistics.mean(self.response_times)
        return 0.0
    
    @property
    def load_score(self) -> float:
        """负载评分（越低越好）"""
        # 综合考虑连接使用率、响应时间、错误率等因素
        connection_score = self.connection_usage * 0.4
        response_score = min(self.avg_response_time / 1000.0, 1.0) * 0.3  # 假设1秒为满分
        error_score = self.error_rate * 0.3
        
        return connection_score + response_score + error_score


class LoadBalancingEngine(BaseEngine):
    """
    负载均衡引擎
    
    实现智能负载均衡，自动优化负载分配
    """
    
    def __init__(self, main_engine: MainTradingEngine, event_engine: EventTradingEngine, engine_name: str = "LoadBalancingEngine"):
        super().__init__(main_engine, event_engine, engine_name)
        
        # 负载均衡配置
        self.algorithm = LoadBalanceAlgorithm.WEIGHTED_LEAST_CONNECTIONS
        self.auto_adjust_enabled = True
        self.adjustment_interval = 30.0  # 30秒调整一次
        
        # 网关负载信息
        self.gateway_loads: Dict[str, GatewayLoadInfo] = {}
        self.gateway_locks: Dict[str, threading.Lock] = {}
        
        # 负载均衡统计
        self.load_balance_stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "algorithm_changes": 0,
            "last_algorithm_change": 0.0
        }
        
        # 性能监控
        self.performance_thresholds = {
            "max_response_time": 1000.0,  # 最大响应时间（毫秒）
            "max_error_rate": 0.1,        # 最大错误率
            "max_connection_usage": 0.8   # 最大连接使用率
        }
        
        # 工具类
        self.utils = EngineUtils()
        
        # 初始化
        self._init_load_balancing_engine()
    
    def _init_load_balancing_engine(self):
        """初始化负载均衡引擎"""
        self.logInfo("初始化负载均衡引擎")
        
        # 启动自动调整
        if self.auto_adjust_enabled:
            self._start_auto_adjustment()
    
    def register_gateway(self, gateway_name: str, max_connections: int = 100, 
                        weight: float = 1.0, priority: int = 0):
        """
        注册网关
        
        参数:
            gateway_name: 网关名称
            max_connections: 最大连接数
            weight: 权重
            priority: 优先级
        """
        if gateway_name not in self.gateway_loads:
            load_info = GatewayLoadInfo(
                gateway_name=gateway_name,
                max_connections=max_connections,
                weight=weight,
                priority=priority
            )
            
            self.gateway_loads[gateway_name] = load_info
            self.gateway_locks[gateway_name] = threading.Lock()
            
            self.logInfo(f"注册网关 {gateway_name}，最大连接数: {max_connections}，权重: {weight}")
    
    def unregister_gateway(self, gateway_name: str):
        """
        注销网关
        
        参数:
            gateway_name: 网关名称
        """
        if gateway_name in self.gateway_loads:
            del self.gateway_loads[gateway_name]
            del self.gateway_locks[gateway_name]
            self.logInfo(f"注销网关 {gateway_name}")
    
    def get_optimal_gateway(self, algorithm: Optional[LoadBalanceAlgorithm] = None) -> Optional[str]:
        """
        获取最优网关
        
        参数:
            algorithm: 负载均衡算法，如果为None则使用默认算法
            
        返回:
            最优网关名称
        """
        algorithm = algorithm or self.algorithm
        
        if not self.gateway_loads:
            return None
        
        # 过滤健康的网关
        healthy_gateways = [name for name, load_info in self.gateway_loads.items() 
                          if load_info.is_healthy]
        
        if not healthy_gateways:
            return None
        
        if algorithm == LoadBalanceAlgorithm.ROUND_ROBIN:
            return self._round_robin_selection(healthy_gateways)
        elif algorithm == LoadBalanceAlgorithm.WEIGHTED_ROUND_ROBIN:
            return self._weighted_round_robin_selection(healthy_gateways)
        elif algorithm == LoadBalanceAlgorithm.LEAST_CONNECTIONS:
            return self._least_connections_selection(healthy_gateways)
        elif algorithm == LoadBalanceAlgorithm.LEAST_RESPONSE_TIME:
            return self._least_response_time_selection(healthy_gateways)
        elif algorithm == LoadBalanceAlgorithm.WEIGHTED_LEAST_CONNECTIONS:
            return self._weighted_least_connections_selection(healthy_gateways)
        elif algorithm == LoadBalanceAlgorithm.CONSISTENT_HASH:
            return self._consistent_hash_selection(healthy_gateways)
        elif algorithm == LoadBalanceAlgorithm.RANDOM:
            return self._random_selection(healthy_gateways)
        else:
            return self._custom_selection(healthy_gateways)
    
    def _round_robin_selection(self, healthy_gateways: List[str]) -> str:
        """轮询选择"""
        # 这里可以实现更复杂的轮询逻辑
        return random.choice(healthy_gateways)
    
    def _weighted_round_robin_selection(self, healthy_gateways: List[str]) -> str:
        """加权轮询选择"""
        # 简化的加权轮询实现
        total_weight = sum(self.gateway_loads[name].weight for name in healthy_gateways)
        
        if total_weight <= 0:
            return random.choice(healthy_gateways)
        
        # 按权重随机选择
        rand_val = random.uniform(0, total_weight)
        current_weight = 0
        
        for gateway_name in healthy_gateways:
            current_weight += self.gateway_loads[gateway_name].weight
            if rand_val <= current_weight:
                return gateway_name
        
        return healthy_gateways[-1]
    
    def _least_connections_selection(self, healthy_gateways: List[str]) -> str:
        """最少连接数选择"""
        min_connections = float('inf')
        selected_gateway = healthy_gateways[0]
        
        for gateway_name in healthy_gateways:
            load_info = self.gateway_loads[gateway_name]
            if load_info.current_connections < min_connections:
                min_connections = load_info.current_connections
                selected_gateway = gateway_name
        
        return selected_gateway
    
    def _least_response_time_selection(self, healthy_gateways: List[str]) -> str:
        """最少响应时间选择"""
        min_response_time = float('inf')
        selected_gateway = healthy_gateways[0]
        
        for gateway_name in healthy_gateways:
            load_info = self.gateway_loads[gateway_name]
            avg_response_time = load_info.avg_response_time
            
            if avg_response_time > 0 and avg_response_time < min_response_time:
                min_response_time = avg_response_time
                selected_gateway = gateway_name
        
        return selected_gateway
    
    def _weighted_least_connections_selection(self, healthy_gateways: List[str]) -> str:
        """加权最少连接数选择"""
        best_score = float('inf')
        selected_gateway = healthy_gateways[0]
        
        for gateway_name in healthy_gateways:
            load_info = self.gateway_loads[gateway_name]
            
            # 计算加权负载评分
            weighted_score = load_info.load_score / load_info.weight
            
            if weighted_score < best_score:
                best_score = weighted_score
                selected_gateway = gateway_name
        
        return selected_gateway
    
    def _consistent_hash_selection(self, healthy_gateways: List[str]) -> str:
        """一致性哈希选择"""
        # 简化的哈希选择，基于请求ID或时间戳
        if not healthy_gateways:
            return None
        
        # 使用时间戳作为哈希键
        hash_key = int(time.time() * 1000)
        index = hash_key % len(healthy_gateways)
        return healthy_gateways[index]
    
    def _random_selection(self, healthy_gateways: List[str]) -> str:
        """随机选择"""
        return random.choice(healthy_gateways)
    
    def _custom_selection(self, healthy_gateways: List[str]) -> str:
        """自定义选择算法"""
        # 这里可以实现自定义的选择逻辑
        return self._weighted_least_connections_selection(healthy_gateways)
    
    def update_gateway_metrics(self, gateway_name: str, response_time: float = None,
                              success: bool = True, connection_count: int = None):
        """
        更新网关指标
        
        参数:
            gateway_name: 网关名称
            response_time: 响应时间
            success: 是否成功
            connection_count: 当前连接数
        """
        if gateway_name not in self.gateway_loads:
            return
        
        with self.gateway_locks[gateway_name]:
            load_info = self.gateway_loads[gateway_name]
            
            # 更新请求统计
            load_info.total_requests += 1
            if success:
                load_info.success_requests += 1
            
            # 更新响应时间
            if response_time is not None:
                load_info.response_times.append(response_time)
                load_info.response_time = response_time
            
            # 更新连接数
            if connection_count is not None:
                load_info.current_connections = connection_count
            
            # 更新最后使用时间
            load_info.last_used = time.time()
            
            # 计算错误率
            load_info.error_rate = 1.0 - load_info.success_rate
    
    def set_gateway_health(self, gateway_name: str, is_healthy: bool):
        """
        设置网关健康状态
        
        参数:
            gateway_name: 网关名称
            is_healthy: 是否健康
        """
        if gateway_name in self.gateway_loads:
            self.gateway_loads[gateway_name].is_healthy = is_healthy
            
            if is_healthy:
                self.logInfo(f"网关 {gateway_name} 恢复健康")
            else:
                self.logWarning(f"网关 {gateway_name} 健康状态异常")
    
    def _start_auto_adjustment(self):
        """启动自动调整"""
        def adjustment_loop():
            while self.auto_adjust_enabled:
                try:
                    self._auto_adjust_load_balance()
                    time.sleep(self.adjustment_interval)
                except Exception as e:
                    self.logError(f"自动调整异常: {e}")
        
        adjustment_thread = threading.Thread(target=adjustment_loop, daemon=True)
        adjustment_thread.start()
        self.logInfo("启动负载均衡自动调整")
    
    def _auto_adjust_load_balance(self):
        """自动调整负载均衡"""
        # 分析当前性能
        performance_analysis = self._analyze_performance()
        
        # 根据性能分析调整算法
        if performance_analysis["needs_improvement"]:
            new_algorithm = self._select_better_algorithm(performance_analysis)
            
            if new_algorithm != self.algorithm:
                old_algorithm = self.algorithm
                self.algorithm = new_algorithm
                self.load_balance_stats["algorithm_changes"] += 1
                self.load_balance_stats["last_algorithm_change"] = time.time()
                
                self.logInfo(f"负载均衡算法从 {old_algorithm.value} 调整为 {new_algorithm.value}")
    
    def _analyze_performance(self) -> Dict[str, Any]:
        """分析性能"""
        analysis = {
            "needs_improvement": False,
            "issues": [],
            "recommendations": []
        }
        
        # 检查响应时间
        avg_response_times = []
        for load_info in self.gateway_loads.values():
            if load_info.avg_response_time > 0:
                avg_response_times.append(load_info.avg_response_time)
        
        if avg_response_times:
            overall_avg_response_time = statistics.mean(avg_response_times)
            if overall_avg_response_time > self.performance_thresholds["max_response_time"]:
                analysis["needs_improvement"] = True
                analysis["issues"].append("响应时间过高")
                analysis["recommendations"].append("考虑切换到响应时间优先的算法")
        
        # 检查错误率
        high_error_gateways = [name for name, load_info in self.gateway_loads.items()
                             if load_info.error_rate > self.performance_thresholds["max_error_rate"]]
        
        if high_error_gateways:
            analysis["needs_improvement"] = True
            analysis["issues"].append(f"网关 {', '.join(high_error_gateways)} 错误率过高")
            analysis["recommendations"].append("检查网关健康状态，考虑故障转移")
        
        # 检查连接使用率
        high_usage_gateways = [name for name, load_info in self.gateway_loads.items()
                             if load_info.connection_usage > self.performance_thresholds["max_connection_usage"]]
        
        if high_usage_gateways:
            analysis["needs_improvement"] = True
            analysis["issues"].append(f"网关 {', '.join(high_usage_gateways)} 连接使用率过高")
            analysis["recommendations"].append("考虑切换到最少连接数算法")
        
        return analysis
    
    def _select_better_algorithm(self, performance_analysis: Dict[str, Any]) -> LoadBalanceAlgorithm:
        """选择更好的算法"""
        issues = performance_analysis.get("issues", [])
        
        if "响应时间过高" in str(issues):
            return LoadBalanceAlgorithm.LEAST_RESPONSE_TIME
        elif "连接使用率过高" in str(issues):
            return LoadBalanceAlgorithm.LEAST_CONNECTIONS
        elif "错误率过高" in str(issues):
            return LoadBalanceAlgorithm.WEIGHTED_LEAST_CONNECTIONS
        else:
            return LoadBalanceAlgorithm.WEIGHTED_LEAST_CONNECTIONS
    
    def get_load_balance_stats(self) -> Dict[str, Any]:
        """获取负载均衡统计信息"""
        gateway_stats = {}
        for name, load_info in self.gateway_loads.items():
            gateway_stats[name] = {
                "current_connections": load_info.current_connections,
                "max_connections": load_info.max_connections,
                "connection_usage": load_info.connection_usage,
                "avg_response_time": load_info.avg_response_time,
                "error_rate": load_info.error_rate,
                "success_rate": load_info.success_rate,
                "weight": load_info.weight,
                "priority": load_info.priority,
                "is_healthy": load_info.is_healthy,
                "total_requests": load_info.total_requests,
                "success_requests": load_info.success_requests,
                "load_score": load_info.load_score
            }
        
        return {
            "algorithm": self.algorithm.value,
            "auto_adjust_enabled": self.auto_adjust_enabled,
            "gateway_loads": gateway_stats,
            "load_balance_stats": dict(self.load_balance_stats),
            "performance_thresholds": dict(self.performance_thresholds)
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
        """关闭负载均衡引擎"""
        self.logInfo("关闭负载均衡引擎")
        self.auto_adjust_enabled = False
        super().close()
