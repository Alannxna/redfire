"""
国内券商网关监控和告警系统
提供实时监控、性能分析、告警通知等功能
"""

import asyncio
import logging
import time
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import statistics
from collections import deque, defaultdict

from ..adapters.domestic_gateways_adapter import GatewayStatus, DomesticGatewayType


class AlertLevel(Enum):
    """告警级别"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class MetricType(Enum):
    """指标类型"""
    LATENCY = "latency"
    THROUGHPUT = "throughput"
    ERROR_RATE = "error_rate"
    CONNECTION_STATUS = "connection_status"
    ORDER_SUCCESS_RATE = "order_success_rate"


@dataclass
class AlertRule:
    """告警规则"""
    name: str
    metric_type: MetricType
    condition: str  # >, <, >=, <=, ==, !=
    threshold: float
    level: AlertLevel
    enabled: bool = True
    consecutive_violations: int = 1  # 连续违规次数后触发告警
    cooldown_seconds: int = 300  # 告警冷却时间


@dataclass
class Alert:
    """告警信息"""
    id: str
    rule_name: str
    gateway_name: str
    level: AlertLevel
    message: str
    metric_value: float
    threshold: float
    timestamp: datetime
    resolved: bool = False
    resolved_timestamp: Optional[datetime] = None


@dataclass
class PerformanceMetrics:
    """性能指标"""
    gateway_name: str
    timestamp: datetime
    
    # 延迟指标 (毫秒)
    avg_latency: float = 0.0
    min_latency: float = 0.0
    max_latency: float = 0.0
    p95_latency: float = 0.0
    p99_latency: float = 0.0
    
    # 吞吐量指标
    orders_per_second: float = 0.0
    trades_per_second: float = 0.0
    quotes_per_second: float = 0.0
    
    # 成功率指标
    order_success_rate: float = 100.0
    connection_uptime: float = 100.0
    
    # 错误指标
    error_count: int = 0
    error_rate: float = 0.0
    
    # 连接指标
    connection_count: int = 0
    disconnection_count: int = 0


class DomesticGatewayMonitor:
    """
    国内券商网关监控系统
    
    功能:
    - 实时性能监控
    - 告警规则管理
    - 告警通知
    - 性能数据收集和分析
    - 健康状态检查
    """
    
    def __init__(self, monitor_interval: int = 5):
        self.monitor_interval = monitor_interval
        self.logger = logging.getLogger(f"{__name__}.GatewayMonitor")
        
        # 监控状态
        self.is_monitoring = False
        self.monitor_task: Optional[asyncio.Task] = None
        
        # 性能数据存储 (网关名 -> 指标队列)
        self.metrics_history: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=1000)  # 保留最近1000个数据点
        )
        
        # 延迟数据存储 (网关名 -> 延迟队列)
        self.latency_data: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=1000)
        )
        
        # 告警规则
        self.alert_rules: Dict[str, AlertRule] = {}
        self.active_alerts: Dict[str, Alert] = {}  # alert_id -> Alert
        self.alert_history: List[Alert] = []
        
        # 违规计数器 (规则名 -> 网关名 -> 计数)
        self.violation_counters: Dict[str, Dict[str, int]] = defaultdict(
            lambda: defaultdict(int)
        )
        
        # 告警回调
        self.alert_callbacks: List[Callable[[Alert], None]] = []
        
        # 统计数据
        self.stats: Dict[str, Any] = {}
        
        # 初始化默认告警规则
        self._initialize_default_rules()
        
        self.logger.info("国内券商网关监控系统初始化完成")
    
    def _initialize_default_rules(self):
        """初始化默认告警规则"""
        default_rules = [
            AlertRule(
                name="high_latency",
                metric_type=MetricType.LATENCY,
                condition=">=",
                threshold=100.0,  # 100ms
                level=AlertLevel.WARNING,
                consecutive_violations=3
            ),
            AlertRule(
                name="critical_latency",
                metric_type=MetricType.LATENCY,
                condition=">=",
                threshold=500.0,  # 500ms
                level=AlertLevel.CRITICAL,
                consecutive_violations=2
            ),
            AlertRule(
                name="low_order_success_rate",
                metric_type=MetricType.ORDER_SUCCESS_RATE,
                condition="<",
                threshold=95.0,  # 95%
                level=AlertLevel.ERROR,
                consecutive_violations=2
            ),
            AlertRule(
                name="high_error_rate",
                metric_type=MetricType.ERROR_RATE,
                condition=">=",
                threshold=5.0,  # 5%
                level=AlertLevel.ERROR,
                consecutive_violations=3
            ),
            AlertRule(
                name="connection_lost",
                metric_type=MetricType.CONNECTION_STATUS,
                condition="==",
                threshold=0.0,  # 断开连接
                level=AlertLevel.CRITICAL,
                consecutive_violations=1
            )
        ]
        
        for rule in default_rules:
            self.alert_rules[rule.name] = rule
    
    async def start_monitoring(self):
        """启动监控"""
        if self.is_monitoring:
            self.logger.warning("监控已在运行")
            return
        
        self.is_monitoring = True
        self.monitor_task = asyncio.create_task(self._monitoring_loop())
        self.logger.info("监控系统启动")
    
    async def stop_monitoring(self):
        """停止监控"""
        if not self.is_monitoring:
            return
        
        self.is_monitoring = False
        
        if self.monitor_task and not self.monitor_task.done():
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("监控系统停止")
    
    async def _monitoring_loop(self):
        """监控主循环"""
        while self.is_monitoring:
            try:
                await asyncio.sleep(self.monitor_interval)
                
                # 执行监控检查
                await self._perform_monitoring_checks()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"监控循环异常: {e}")
    
    async def _perform_monitoring_checks(self):
        """执行监控检查"""
        # 这里需要从适配器获取当前状态
        # 在实际使用时需要注入适配器实例
        pass
    
    def record_latency(self, gateway_name: str, latency_ms: float):
        """记录延迟数据"""
        self.latency_data[gateway_name].append({
            'timestamp': datetime.now(),
            'latency': latency_ms
        })
        
        # 检查延迟告警
        self._check_latency_alerts(gateway_name, latency_ms)
    
    def record_order_result(self, gateway_name: str, success: bool):
        """记录订单结果"""
        # 更新统计数据
        if gateway_name not in self.stats:
            self.stats[gateway_name] = {
                'total_orders': 0,
                'successful_orders': 0,
                'failed_orders': 0
            }
        
        self.stats[gateway_name]['total_orders'] += 1
        if success:
            self.stats[gateway_name]['successful_orders'] += 1
        else:
            self.stats[gateway_name]['failed_orders'] += 1
        
        # 计算成功率
        total = self.stats[gateway_name]['total_orders']
        successful = self.stats[gateway_name]['successful_orders']
        success_rate = (successful / total) * 100 if total > 0 else 0
        
        # 检查成功率告警
        self._check_metric_alerts(gateway_name, MetricType.ORDER_SUCCESS_RATE, success_rate)
    
    def record_error(self, gateway_name: str, error_type: str, error_msg: str):
        """记录错误"""
        # 更新错误统计
        if gateway_name not in self.stats:
            self.stats[gateway_name] = {'errors': []}
        
        if 'errors' not in self.stats[gateway_name]:
            self.stats[gateway_name]['errors'] = []
        
        self.stats[gateway_name]['errors'].append({
            'timestamp': datetime.now(),
            'type': error_type,
            'message': error_msg
        })
        
        # 计算错误率
        error_rate = self._calculate_error_rate(gateway_name)
        self._check_metric_alerts(gateway_name, MetricType.ERROR_RATE, error_rate)
    
    def record_connection_status(self, gateway_name: str, connected: bool):
        """记录连接状态"""
        status_value = 1.0 if connected else 0.0
        self._check_metric_alerts(gateway_name, MetricType.CONNECTION_STATUS, status_value)
    
    def update_performance_metrics(self, gateway_name: str, status: GatewayStatus):
        """更新性能指标"""
        try:
            # 计算延迟统计
            latency_stats = self._calculate_latency_statistics(gateway_name)
            
            # 计算吞吐量
            throughput_stats = self._calculate_throughput_statistics(gateway_name)
            
            # 创建性能指标对象
            metrics = PerformanceMetrics(
                gateway_name=gateway_name,
                timestamp=datetime.now(),
                avg_latency=latency_stats.get('avg', 0.0),
                min_latency=latency_stats.get('min', 0.0),
                max_latency=latency_stats.get('max', 0.0),
                p95_latency=latency_stats.get('p95', 0.0),
                p99_latency=latency_stats.get('p99', 0.0),
                orders_per_second=throughput_stats.get('orders_per_second', 0.0),
                order_success_rate=self._calculate_success_rate(gateway_name),
                error_rate=self._calculate_error_rate(gateway_name),
                error_count=status.error_count,
                connection_uptime=self._calculate_uptime(gateway_name)
            )
            
            # 存储到历史记录
            self.metrics_history[gateway_name].append(metrics)
            
        except Exception as e:
            self.logger.error(f"更新性能指标失败 {gateway_name}: {e}")
    
    def _calculate_latency_statistics(self, gateway_name: str) -> Dict[str, float]:
        """计算延迟统计"""
        latency_queue = self.latency_data[gateway_name]
        
        if not latency_queue:
            return {'avg': 0.0, 'min': 0.0, 'max': 0.0, 'p95': 0.0, 'p99': 0.0}
        
        # 获取最近5分钟的数据
        cutoff_time = datetime.now() - timedelta(minutes=5)
        recent_latencies = [
            item['latency'] for item in latency_queue
            if item['timestamp'] >= cutoff_time
        ]
        
        if not recent_latencies:
            return {'avg': 0.0, 'min': 0.0, 'max': 0.0, 'p95': 0.0, 'p99': 0.0}
        
        recent_latencies.sort()
        
        return {
            'avg': statistics.mean(recent_latencies),
            'min': min(recent_latencies),
            'max': max(recent_latencies),
            'p95': self._percentile(recent_latencies, 0.95),
            'p99': self._percentile(recent_latencies, 0.99)
        }
    
    def _calculate_throughput_statistics(self, gateway_name: str) -> Dict[str, float]:
        """计算吞吐量统计"""
        # 简化实现，实际需要基于时间窗口计算
        return {
            'orders_per_second': 0.0,
            'trades_per_second': 0.0,
            'quotes_per_second': 0.0
        }
    
    def _calculate_success_rate(self, gateway_name: str) -> float:
        """计算成功率"""
        if gateway_name not in self.stats:
            return 100.0
        
        stats = self.stats[gateway_name]
        total = stats.get('total_orders', 0)
        successful = stats.get('successful_orders', 0)
        
        return (successful / total) * 100 if total > 0 else 100.0
    
    def _calculate_error_rate(self, gateway_name: str) -> float:
        """计算错误率"""
        if gateway_name not in self.stats:
            return 0.0
        
        # 计算最近5分钟的错误率
        cutoff_time = datetime.now() - timedelta(minutes=5)
        errors = self.stats[gateway_name].get('errors', [])
        
        recent_errors = [
            error for error in errors
            if error['timestamp'] >= cutoff_time
        ]
        
        # 简化计算，实际需要基于总请求数
        return len(recent_errors) * 2.0  # 假设每个错误代表2%的错误率
    
    def _calculate_uptime(self, gateway_name: str) -> float:
        """计算连接正常运行时间百分比"""
        # 简化实现，实际需要基于连接状态历史
        return 99.5
    
    def _percentile(self, data: List[float], percentile: float) -> float:
        """计算百分位数"""
        if not data:
            return 0.0
        
        index = int(len(data) * percentile)
        if index >= len(data):
            index = len(data) - 1
        
        return data[index]
    
    def _check_latency_alerts(self, gateway_name: str, latency_ms: float):
        """检查延迟告警"""
        for rule_name, rule in self.alert_rules.items():
            if rule.metric_type == MetricType.LATENCY and rule.enabled:
                self._check_single_alert_rule(rule, gateway_name, latency_ms)
    
    def _check_metric_alerts(self, gateway_name: str, metric_type: MetricType, value: float):
        """检查指标告警"""
        for rule_name, rule in self.alert_rules.items():
            if rule.metric_type == metric_type and rule.enabled:
                self._check_single_alert_rule(rule, gateway_name, value)
    
    def _check_single_alert_rule(self, rule: AlertRule, gateway_name: str, value: float):
        """检查单个告警规则"""
        try:
            # 评估条件
            violated = self._evaluate_condition(value, rule.condition, rule.threshold)
            
            if violated:
                # 增加违规计数
                self.violation_counters[rule.name][gateway_name] += 1
                
                # 检查是否达到连续违规次数
                if self.violation_counters[rule.name][gateway_name] >= rule.consecutive_violations:
                    self._trigger_alert(rule, gateway_name, value)
                    # 重置计数器
                    self.violation_counters[rule.name][gateway_name] = 0
            else:
                # 重置违规计数
                self.violation_counters[rule.name][gateway_name] = 0
                
                # 检查是否需要解决告警
                self._resolve_alert(rule.name, gateway_name)
                
        except Exception as e:
            self.logger.error(f"检查告警规则失败 {rule.name}: {e}")
    
    def _evaluate_condition(self, value: float, condition: str, threshold: float) -> bool:
        """评估告警条件"""
        if condition == ">":
            return value > threshold
        elif condition == ">=":
            return value >= threshold
        elif condition == "<":
            return value < threshold
        elif condition == "<=":
            return value <= threshold
        elif condition == "==":
            return value == threshold
        elif condition == "!=":
            return value != threshold
        else:
            return False
    
    def _trigger_alert(self, rule: AlertRule, gateway_name: str, value: float):
        """触发告警"""
        alert_id = f"{rule.name}_{gateway_name}_{int(time.time())}"
        
        # 检查冷却时间
        if self._is_in_cooldown(rule.name, gateway_name):
            return
        
        alert = Alert(
            id=alert_id,
            rule_name=rule.name,
            gateway_name=gateway_name,
            level=rule.level,
            message=f"{gateway_name} {rule.metric_type.value} {rule.condition} {rule.threshold} (actual: {value})",
            metric_value=value,
            threshold=rule.threshold,
            timestamp=datetime.now()
        )
        
        # 存储告警
        self.active_alerts[alert_id] = alert
        self.alert_history.append(alert)
        
        # 通知回调
        self._notify_alert_callbacks(alert)
        
        self.logger.warning(f"告警触发: {alert.message}")
    
    def _resolve_alert(self, rule_name: str, gateway_name: str):
        """解决告警"""
        # 查找需要解决的告警
        alerts_to_resolve = [
            alert for alert in self.active_alerts.values()
            if alert.rule_name == rule_name and alert.gateway_name == gateway_name and not alert.resolved
        ]
        
        for alert in alerts_to_resolve:
            alert.resolved = True
            alert.resolved_timestamp = datetime.now()
            
            # 从活跃告警中移除
            if alert.id in self.active_alerts:
                del self.active_alerts[alert.id]
            
            self.logger.info(f"告警解决: {alert.message}")
    
    def _is_in_cooldown(self, rule_name: str, gateway_name: str) -> bool:
        """检查是否在冷却时间内"""
        # 查找最近的告警
        recent_alerts = [
            alert for alert in self.alert_history
            if (alert.rule_name == rule_name and 
                alert.gateway_name == gateway_name and
                (datetime.now() - alert.timestamp).total_seconds() < 
                self.alert_rules[rule_name].cooldown_seconds)
        ]
        
        return len(recent_alerts) > 0
    
    def _notify_alert_callbacks(self, alert: Alert):
        """通知告警回调"""
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                self.logger.error(f"告警回调执行失败: {e}")
    
    # 公共接口方法
    def add_alert_rule(self, rule: AlertRule):
        """添加告警规则"""
        self.alert_rules[rule.name] = rule
        self.logger.info(f"添加告警规则: {rule.name}")
    
    def remove_alert_rule(self, rule_name: str):
        """移除告警规则"""
        if rule_name in self.alert_rules:
            del self.alert_rules[rule_name]
            self.logger.info(f"移除告警规则: {rule_name}")
    
    def enable_alert_rule(self, rule_name: str):
        """启用告警规则"""
        if rule_name in self.alert_rules:
            self.alert_rules[rule_name].enabled = True
    
    def disable_alert_rule(self, rule_name: str):
        """禁用告警规则"""
        if rule_name in self.alert_rules:
            self.alert_rules[rule_name].enabled = False
    
    def add_alert_callback(self, callback: Callable[[Alert], None]):
        """添加告警回调"""
        self.alert_callbacks.append(callback)
    
    def get_active_alerts(self) -> List[Alert]:
        """获取活跃告警"""
        return list(self.active_alerts.values())
    
    def get_alert_history(self, limit: int = 100) -> List[Alert]:
        """获取告警历史"""
        return self.alert_history[-limit:]
    
    def get_performance_metrics(self, gateway_name: str, limit: int = 100) -> List[PerformanceMetrics]:
        """获取性能指标"""
        return list(self.metrics_history[gateway_name])[-limit:]
    
    def get_gateway_statistics(self, gateway_name: str) -> Dict[str, Any]:
        """获取网关统计信息"""
        if gateway_name not in self.stats:
            return {}
        
        stats = self.stats[gateway_name].copy()
        
        # 添加计算指标
        stats['success_rate'] = self._calculate_success_rate(gateway_name)
        stats['error_rate'] = self._calculate_error_rate(gateway_name)
        stats['uptime'] = self._calculate_uptime(gateway_name)
        
        # 添加延迟统计
        latency_stats = self._calculate_latency_statistics(gateway_name)
        stats['latency_statistics'] = latency_stats
        
        return stats
    
    def get_all_statistics(self) -> Dict[str, Dict[str, Any]]:
        """获取所有网关统计信息"""
        all_stats = {}
        
        for gateway_name in self.stats.keys():
            all_stats[gateway_name] = self.get_gateway_statistics(gateway_name)
        
        return all_stats
    
    def reset_statistics(self, gateway_name: Optional[str] = None):
        """重置统计数据"""
        if gateway_name:
            if gateway_name in self.stats:
                self.stats[gateway_name] = {}
            if gateway_name in self.metrics_history:
                self.metrics_history[gateway_name].clear()
            if gateway_name in self.latency_data:
                self.latency_data[gateway_name].clear()
        else:
            self.stats.clear()
            self.metrics_history.clear()
            self.latency_data.clear()
        
        self.logger.info(f"统计数据重置: {gateway_name or '全部'}")


# 告警通知处理器
class AlertNotificationHandler:
    """告警通知处理器"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.AlertNotificationHandler")
        self.notification_methods: List[Callable[[Alert], None]] = []
    
    def add_notification_method(self, method: Callable[[Alert], None]):
        """添加通知方法"""
        self.notification_methods.append(method)
    
    def handle_alert(self, alert: Alert):
        """处理告警通知"""
        for method in self.notification_methods:
            try:
                method(alert)
            except Exception as e:
                self.logger.error(f"通知方法执行失败: {e}")
    
    def log_notification(self, alert: Alert):
        """日志通知"""
        level_map = {
            AlertLevel.INFO: logging.INFO,
            AlertLevel.WARNING: logging.WARNING,
            AlertLevel.ERROR: logging.ERROR,
            AlertLevel.CRITICAL: logging.CRITICAL
        }
        
        self.logger.log(
            level_map.get(alert.level, logging.INFO),
            f"告警通知: [{alert.level.value.upper()}] {alert.message}"
        )
    
    def email_notification(self, alert: Alert):
        """邮件通知 (示例实现)"""
        # 实际实现需要配置SMTP服务器
        self.logger.info(f"邮件告警: {alert.message}")
    
    def webhook_notification(self, alert: Alert):
        """Webhook通知 (示例实现)"""
        # 实际实现需要发送HTTP请求
        self.logger.info(f"Webhook告警: {alert.message}")


# 全局监控实例
gateway_monitor = DomesticGatewayMonitor()
alert_handler = AlertNotificationHandler()

# 注册默认通知方法
alert_handler.add_notification_method(alert_handler.log_notification)
gateway_monitor.add_alert_callback(alert_handler.handle_alert)


def get_gateway_monitor() -> DomesticGatewayMonitor:
    """获取网关监控实例"""
    return gateway_monitor


def get_alert_handler() -> AlertNotificationHandler:
    """获取告警处理器实例"""
    return alert_handler
