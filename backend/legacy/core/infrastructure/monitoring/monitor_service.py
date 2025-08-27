"""
监控服务

基于新架构重构的综合监控服务，集成指标收集、告警管理和数据存储
"""

import asyncio
import psutil
import time
import json
import uuid
from typing import Dict, List, Any, Optional, Set, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict, field
from enum import Enum
from pathlib import Path

from ...base.infrastructure_service import BaseInfrastructureService, InfrastructureServiceConfig
from ...common.exceptions import InfrastructureException
from ...common.enums import ServiceStatus


class MonitorLevel(Enum):
    """监控级别"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertStatus(Enum):
    """告警状态"""
    ACTIVE = "active"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"


@dataclass
class MetricDataPoint:
    """指标数据点"""
    metric_name: str
    value: float
    timestamp: str
    tags: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AlertRule:
    """告警规则"""
    rule_id: str
    title: str
    description: str
    metric_name: str
    operator: str  # gt, lt, eq
    threshold: float
    level: MonitorLevel
    enabled: bool = True
    service_name: str = "system"


@dataclass
class Alert:
    """告警实例"""
    alert_id: str
    rule_id: str
    title: str
    description: str
    level: MonitorLevel
    metric_name: str
    current_value: float
    threshold: float
    service_name: str
    triggered_at: str
    status: AlertStatus = AlertStatus.ACTIVE
    resolved_at: Optional[str] = None
    notification_count: int = 0
    last_notification: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MonitorServiceConfig(InfrastructureServiceConfig):
    """监控服务配置"""
    metrics_collection_interval: int = 60  # 系统指标收集间隔(秒)
    app_metrics_interval: int = 30  # 应用指标收集间隔(秒)
    alert_evaluation_interval: int = 30  # 告警评估间隔(秒)
    notification_interval: int = 300  # 通知间隔(秒)
    max_metrics_buffer: int = 10000  # 指标缓冲区大小
    data_retention_days: int = 30  # 数据保留天数
    enable_system_metrics: bool = True
    enable_app_metrics: bool = True
    enable_alerts: bool = True


class MonitorService(BaseInfrastructureService):
    """监控服务
    
    提供系统和应用监控、告警管理功能
    """
    
    def __init__(self, config: MonitorServiceConfig):
        super().__init__(config)
        self.config: MonitorServiceConfig = config
        
        # 内部组件
        self.metrics_collector = MetricsCollector(self)
        self.alert_manager = AlertManager(self)
        self.data_storage = DataStorage(self)
        
        # 运行状态
        self._monitor_tasks: List[asyncio.Task] = []
    
    async def _start_impl(self) -> bool:
        """启动监控服务"""
        try:
            self.logger.info("启动监控服务")
            
            # 启动各个组件
            await self.data_storage.initialize()
            
            if self.config.enable_system_metrics or self.config.enable_app_metrics:
                await self.metrics_collector.start()
            
            if self.config.enable_alerts:
                await self.alert_manager.start()
            
            self.logger.info("监控服务启动成功")
            return True
            
        except Exception as e:
            self.logger.error(f"启动监控服务失败: {e}")
            return False
    
    async def _stop_impl(self) -> bool:
        """停止监控服务"""
        try:
            self.logger.info("停止监控服务")
            
            # 停止所有监控任务
            for task in self._monitor_tasks:
                if not task.done():
                    task.cancel()
            
            await asyncio.gather(*self._monitor_tasks, return_exceptions=True)
            self._monitor_tasks.clear()
            
            # 停止各个组件
            await self.metrics_collector.stop()
            await self.alert_manager.stop()
            await self.data_storage.cleanup()
            
            self.logger.info("监控服务停止成功")
            return True
            
        except Exception as e:
            self.logger.error(f"停止监控服务失败: {e}")
            return False
    
    async def _health_check_impl(self) -> Dict[str, Any]:
        """健康检查实现"""
        return {
            "metrics_collector": {
                "running": self.metrics_collector.is_running,
                "buffer_size": self.metrics_collector.get_buffer_size()
            },
            "alert_manager": {
                "running": self.alert_manager.is_running,
                "active_alerts": len(self.alert_manager.get_active_alerts()),
                "rules_count": len(self.alert_manager.alert_rules)
            },
            "data_storage": {
                "initialized": self.data_storage.is_initialized
            }
        }
    
    def get_service_status(self) -> Dict[str, Any]:
        """获取服务状态"""
        return {
            "service_id": self.service_id,
            "status": self.status.value,
            "uptime": self.uptime,
            "components": {
                "metrics_collector": {
                    "running": self.metrics_collector.is_running,
                    "buffer_size": self.metrics_collector.get_buffer_size(),
                    "registered_services": len(self.metrics_collector.registered_services)
                },
                "alert_manager": {
                    "running": self.alert_manager.is_running,
                    "active_alerts": len(self.alert_manager.get_active_alerts()),
                    "alert_rules": len(self.alert_manager.alert_rules)
                }
            }
        }
    
    def get_recent_metrics(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取最近的指标数据"""
        metrics = self.metrics_collector.get_metrics(limit)
        return [asdict(metric) for metric in metrics]
    
    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """获取活跃告警"""
        alerts = self.alert_manager.get_active_alerts()
        return [asdict(alert) for alert in alerts]
    
    def add_custom_metric(self, metric_name: str, value: float, tags: Dict[str, str] = None):
        """添加自定义指标"""
        self.metrics_collector.add_metric(metric_name, value, tags)
    
    def register_service_monitoring(self, service_name: str, health_check_url: str):
        """注册服务监控"""
        self.metrics_collector.register_service(service_name, health_check_url)
    
    def add_alert_rule(self, rule: AlertRule):
        """添加告警规则"""
        self.alert_manager.add_rule(rule)


class MetricsCollector:
    """指标收集器"""
    
    def __init__(self, monitor_service: MonitorService):
        self.monitor_service = monitor_service
        self.config = monitor_service.config
        self.logger = monitor_service.logger
        
        self.is_running = False
        self.metrics_buffer: List[MetricDataPoint] = []
        self.registered_services: Dict[str, str] = {}
        self._collection_tasks: List[asyncio.Task] = []
    
    async def start(self):
        """启动指标收集"""
        if self.is_running:
            return
        
        self.is_running = True
        self.logger.info("启动指标收集器")
        
        # 启动系统指标收集
        if self.config.enable_system_metrics:
            task = asyncio.create_task(self._collect_system_metrics())
            self._collection_tasks.append(task)
            self.monitor_service._monitor_tasks.append(task)
        
        # 启动应用指标收集
        if self.config.enable_app_metrics:
            task = asyncio.create_task(self._collect_app_metrics())
            self._collection_tasks.append(task)
            self.monitor_service._monitor_tasks.append(task)
    
    async def stop(self):
        """停止指标收集"""
        if not self.is_running:
            return
        
        self.is_running = False
        self.logger.info("停止指标收集器")
        
        # 取消收集任务
        for task in self._collection_tasks:
            if not task.done():
                task.cancel()
        
        self._collection_tasks.clear()
    
    async def _collect_system_metrics(self):
        """收集系统指标"""
        while self.is_running:
            try:
                timestamp = datetime.now().isoformat()
                
                # CPU使用率
                cpu_percent = psutil.cpu_percent(interval=1)
                self.add_metric("system.cpu.usage_percent", cpu_percent, {"type": "system"})
                
                # 内存使用率
                memory = psutil.virtual_memory()
                self.add_metric("system.memory.usage_percent", memory.percent, {"type": "system"})
                self.add_metric("system.memory.available_mb", memory.available / 1024 / 1024, {"type": "system"})
                
                # 磁盘使用率
                disk = psutil.disk_usage('/')
                disk_percent = (disk.used / disk.total) * 100
                self.add_metric("system.disk.usage_percent", disk_percent, {"type": "system"})
                
                # 网络I/O
                network = psutil.net_io_counters()
                self.add_metric("system.network.bytes_sent", network.bytes_sent, {"type": "system"})
                self.add_metric("system.network.bytes_recv", network.bytes_recv, {"type": "system"})
                
                # 进程数
                process_count = len(psutil.pids())
                self.add_metric("system.process.count", process_count, {"type": "system"})
                
                await asyncio.sleep(self.config.metrics_collection_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"收集系统指标失败: {e}")
                await asyncio.sleep(10)
    
    async def _collect_app_metrics(self):
        """收集应用指标"""
        while self.is_running:
            try:
                current_process = psutil.Process()
                
                # 应用内存使用
                memory_info = current_process.memory_info()
                self.add_metric("app.memory.rss_mb", memory_info.rss / 1024 / 1024, {"type": "application"})
                self.add_metric("app.memory.vms_mb", memory_info.vms / 1024 / 1024, {"type": "application"})
                
                # 应用CPU使用
                cpu_percent = current_process.cpu_percent()
                self.add_metric("app.cpu.usage_percent", cpu_percent, {"type": "application"})
                
                # 线程数
                thread_count = current_process.num_threads()
                self.add_metric("app.threads.count", thread_count, {"type": "application"})
                
                # 文件描述符数量（非Windows）
                try:
                    fd_count = current_process.num_fds()
                    self.add_metric("app.fds.count", fd_count, {"type": "application"})
                except AttributeError:
                    pass  # Windows不支持
                
                await asyncio.sleep(self.config.app_metrics_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"收集应用指标失败: {e}")
                await asyncio.sleep(10)
    
    def add_metric(self, metric_name: str, value: float, tags: Dict[str, str] = None):
        """添加指标"""
        timestamp = datetime.now().isoformat()
        metric = MetricDataPoint(
            metric_name=metric_name,
            value=value,
            timestamp=timestamp,
            tags=tags or {}
        )
        
        # 添加到缓冲区
        self.metrics_buffer.append(metric)
        
        # 如果缓冲区满了，删除最旧的指标
        if len(self.metrics_buffer) > self.config.max_metrics_buffer:
            self.metrics_buffer = self.metrics_buffer[-self.config.max_metrics_buffer:]
    
    def get_metrics(self, limit: int = 100) -> List[MetricDataPoint]:
        """获取指标数据"""
        return self.metrics_buffer[-limit:] if self.metrics_buffer else []
    
    def get_buffer_size(self) -> int:
        """获取缓冲区大小"""
        return len(self.metrics_buffer)
    
    def register_service(self, service_name: str, health_check_url: str):
        """注册服务监控"""
        self.registered_services[service_name] = health_check_url
        self.logger.info(f"注册服务监控: {service_name}")


class AlertManager:
    """告警管理器"""
    
    def __init__(self, monitor_service: MonitorService):
        self.monitor_service = monitor_service
        self.config = monitor_service.config
        self.logger = monitor_service.logger
        
        self.is_running = False
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_rules: Dict[str, AlertRule] = {}
        self._alert_tasks: List[asyncio.Task] = []
        
        # 加载默认告警规则
        self._load_default_rules()
    
    def _load_default_rules(self):
        """加载默认告警规则"""
        default_rules = [
            AlertRule(
                rule_id="system_cpu_high",
                title="系统CPU使用率过高",
                description="系统CPU使用率达到 {current_value:.1f}%，超过阈值 {threshold:.1f}%",
                metric_name="system.cpu.usage_percent",
                operator="gt",
                threshold=80.0,
                level=MonitorLevel.WARNING
            ),
            AlertRule(
                rule_id="system_memory_high",
                title="系统内存使用率过高",
                description="系统内存使用率达到 {current_value:.1f}%，超过阈值 {threshold:.1f}%",
                metric_name="system.memory.usage_percent",
                operator="gt",
                threshold=85.0,
                level=MonitorLevel.WARNING
            ),
            AlertRule(
                rule_id="system_disk_high",
                title="系统磁盘使用率过高",
                description="系统磁盘使用率达到 {current_value:.1f}%，超过阈值 {threshold:.1f}%",
                metric_name="system.disk.usage_percent",
                operator="gt",
                threshold=90.0,
                level=MonitorLevel.ERROR
            )
        ]
        
        for rule in default_rules:
            self.alert_rules[rule.rule_id] = rule
    
    async def start(self):
        """启动告警管理"""
        if self.is_running:
            return
        
        self.is_running = True
        self.logger.info("启动告警管理器")
        
        # 启动告警评估任务
        task = asyncio.create_task(self._evaluate_alerts())
        self._alert_tasks.append(task)
        self.monitor_service._monitor_tasks.append(task)
        
        # 启动通知发送任务
        task = asyncio.create_task(self._send_notifications())
        self._alert_tasks.append(task)
        self.monitor_service._monitor_tasks.append(task)
    
    async def stop(self):
        """停止告警管理"""
        if not self.is_running:
            return
        
        self.is_running = False
        self.logger.info("停止告警管理器")
        
        # 取消告警任务
        for task in self._alert_tasks:
            if not task.done():
                task.cancel()
        
        self._alert_tasks.clear()
    
    async def _evaluate_alerts(self):
        """评估告警规则"""
        while self.is_running:
            try:
                # 获取最新指标数据
                metrics = self.monitor_service.metrics_collector.get_metrics(1000)
                
                # 按指标名称分组
                metrics_by_name = {}
                for metric in metrics:
                    if metric.metric_name not in metrics_by_name:
                        metrics_by_name[metric.metric_name] = []
                    metrics_by_name[metric.metric_name].append(metric)
                
                # 评估每个告警规则
                for rule_id, rule in self.alert_rules.items():
                    if rule.enabled:
                        await self._evaluate_rule(rule, metrics_by_name)
                
                await asyncio.sleep(self.config.alert_evaluation_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"告警评估失败: {e}")
                await asyncio.sleep(10)
    
    async def _evaluate_rule(self, rule: AlertRule, metrics_by_name: Dict[str, List[MetricDataPoint]]):
        """评估单个告警规则"""
        try:
            metric_data = metrics_by_name.get(rule.metric_name, [])
            if not metric_data:
                return
            
            # 获取最新值
            latest_metric = max(metric_data, key=lambda m: m.timestamp)
            current_value = latest_metric.value
            
            # 检查告警条件
            should_alert = False
            if rule.operator == "gt" and current_value > rule.threshold:
                should_alert = True
            elif rule.operator == "lt" and current_value < rule.threshold:
                should_alert = True
            elif rule.operator == "eq" and abs(current_value - rule.threshold) < 0.001:
                should_alert = True
            
            # 查找现有告警
            existing_alert = None
            for alert in self.active_alerts.values():
                if alert.rule_id == rule.rule_id and alert.status == AlertStatus.ACTIVE:
                    existing_alert = alert
                    break
            
            if should_alert and not existing_alert:
                # 创建新告警
                alert = Alert(
                    alert_id=str(uuid.uuid4()),
                    rule_id=rule.rule_id,
                    title=rule.title,
                    description=rule.description.format(
                        current_value=current_value,
                        threshold=rule.threshold
                    ),
                    level=rule.level,
                    metric_name=rule.metric_name,
                    current_value=current_value,
                    threshold=rule.threshold,
                    service_name=rule.service_name,
                    triggered_at=datetime.now().isoformat()
                )
                self.active_alerts[alert.alert_id] = alert
                self.logger.warning(f"触发告警: {alert.title}")
                
            elif not should_alert and existing_alert:
                # 解决告警
                existing_alert.status = AlertStatus.RESOLVED
                existing_alert.resolved_at = datetime.now().isoformat()
                self.logger.info(f"告警已解决: {existing_alert.title}")
                
        except Exception as e:
            self.logger.error(f"评估告警规则失败 {rule.rule_id}: {e}")
    
    async def _send_notifications(self):
        """发送通知"""
        while self.is_running:
            try:
                for alert in self.active_alerts.values():
                    if alert.status == AlertStatus.ACTIVE and self._should_send_notification(alert):
                        await self._send_alert_notification(alert)
                
                await asyncio.sleep(60)  # 每分钟检查一次
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"发送通知失败: {e}")
                await asyncio.sleep(10)
    
    def _should_send_notification(self, alert: Alert) -> bool:
        """判断是否应该发送通知"""
        if alert.notification_count == 0:
            return True
        
        if alert.last_notification:
            last_time = datetime.fromisoformat(alert.last_notification)
            now = datetime.now()
            # 按配置间隔发送重复告警
            if (now - last_time).total_seconds() > self.config.notification_interval:
                return True
        
        return False
    
    async def _send_alert_notification(self, alert: Alert):
        """发送告警通知"""
        try:
            # 更新通知记录
            alert.notification_count += 1
            alert.last_notification = datetime.now().isoformat()
            
            # 记录告警通知（这里可以扩展支持多种通知渠道）
            self.logger.warning(f"发送告警通知: {alert.title} - {alert.description}")
            
        except Exception as e:
            self.logger.error(f"发送告警通知失败: {e}")
    
    def get_active_alerts(self) -> List[Alert]:
        """获取活跃告警"""
        return [alert for alert in self.active_alerts.values() if alert.status == AlertStatus.ACTIVE]
    
    def add_rule(self, rule: AlertRule):
        """添加告警规则"""
        self.alert_rules[rule.rule_id] = rule
        self.logger.info(f"添加告警规则: {rule.title}")


class DataStorage:
    """数据存储"""
    
    def __init__(self, monitor_service: MonitorService):
        self.monitor_service = monitor_service
        self.config = monitor_service.config
        self.logger = monitor_service.logger
        self.is_initialized = False
    
    async def initialize(self):
        """初始化数据存储"""
        try:
            # 这里可以初始化数据库连接等
            self.is_initialized = True
            self.logger.info("数据存储初始化成功")
        except Exception as e:
            self.logger.error(f"数据存储初始化失败: {e}")
            raise
    
    async def cleanup(self):
        """清理数据存储"""
        try:
            self.is_initialized = False
            self.logger.info("数据存储清理完成")
        except Exception as e:
            self.logger.error(f"数据存储清理失败: {e}")
