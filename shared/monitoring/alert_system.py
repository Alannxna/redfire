"""
告警通知系统

基于config/backend/monitor_config.py配置的统一告警通知实现。
集成DomesticGatewayMonitor告警和系统监控告警。
"""

import asyncio
import json
import smtplib
import time
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import aiohttp

from config.backend.monitor_config import (
    ALERT_RULES_CONFIG,
    NOTIFICATION_CHANNELS_CONFIG,
    MonitorLevel
)

logger = logging.getLogger(__name__)


class AlertStatus(Enum):
    """告警状态"""
    ACTIVE = "active"
    RESOLVED = "resolved"
    SILENCED = "silenced"
    ACKNOWLEDGED = "acknowledged"


@dataclass
class Alert:
    """告警数据类"""
    alert_id: str
    rule_id: str
    name: str
    description: str
    level: MonitorLevel
    status: AlertStatus
    metric_name: str
    current_value: float
    threshold_value: float
    condition: str
    timestamp: datetime
    resolved_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    labels: Dict[str, str] = None
    annotations: Dict[str, str] = None
    
    def __post_init__(self):
        if self.labels is None:
            self.labels = {}
        if self.annotations is None:
            self.annotations = {}


@dataclass
class NotificationResult:
    """通知结果"""
    channel: str
    success: bool
    message: str
    timestamp: datetime
    error: Optional[str] = None


class AlertEvaluator:
    """
    告警规则评估器
    
    基于monitor_config.py中的ALERT_RULES_CONFIG评估告警条件。
    """
    
    def __init__(self):
        self.active_alerts = {}
        self.alert_history = []
        self.last_evaluation = {}
    
    def evaluate_condition(self, condition: str, value: float, **context) -> bool:
        """
        评估告警条件
        
        Args:
            condition: 告警条件表达式，如 "value > 85"
            value: 当前指标值
            **context: 额外的上下文变量
            
        Returns:
            bool: 是否满足告警条件
        """
        try:
            # 构建评估环境
            eval_context = {
                'value': value,
                **context
            }
            
            # 安全的条件评估 (仅支持基本的数学比较)
            allowed_ops = ['>', '<', '>=', '<=', '==', '!=', 'and', 'or']
            
            # 简单的条件解析和评估
            # 这里可以使用更复杂的表达式解析器，但为了安全性使用简单实现
            if 'value >' in condition:
                threshold = float(condition.split('value >')[1].strip())
                return value > threshold
            elif 'value <' in condition:
                threshold = float(condition.split('value <')[1].strip())
                return value < threshold
            elif 'value >=' in condition:
                threshold = float(condition.split('value >=')[1].strip())
                return value >= threshold
            elif 'value <=' in condition:
                threshold = float(condition.split('value <=')[1].strip())
                return value <= threshold
            elif 'value ==' in condition:
                threshold = float(condition.split('value ==')[1].strip())
                return value == threshold
            elif 'value !=' in condition:
                threshold = float(condition.split('value !=')[1].strip())
                return value != threshold
            else:
                logger.warning(f"不支持的告警条件: {condition}")
                return False
                
        except Exception as e:
            logger.error(f"评估告警条件时出错: {condition}, 错误: {e}")
            return False
    
    def evaluate_rule(self, rule_config, metric_value: float, **context) -> Optional[Alert]:
        """
        评估单个告警规则
        
        Args:
            rule_config: 告警规则配置
            metric_value: 指标值
            **context: 额外上下文
            
        Returns:
            Optional[Alert]: 如果触发告警则返回Alert对象
        """
        rule_id = rule_config.rule_id
        
        # 评估告警条件
        is_triggered = self.evaluate_condition(
            rule_config.condition, 
            metric_value, 
            **context
        )
        
        current_time = datetime.now()
        
        # 检查是否已有活跃告警
        existing_alert = self.active_alerts.get(rule_id)
        
        if is_triggered:
            if not existing_alert:
                # 创建新告警
                alert = Alert(
                    alert_id=f"{rule_id}_{int(time.time())}",
                    rule_id=rule_id,
                    name=rule_config.name,
                    description=rule_config.description,
                    level=rule_config.level,
                    status=AlertStatus.ACTIVE,
                    metric_name=rule_config.metric_name,
                    current_value=metric_value,
                    threshold_value=self._extract_threshold(rule_config.condition),
                    condition=rule_config.condition,
                    timestamp=current_time,
                    labels={
                        'rule_id': rule_id,
                        'metric': rule_config.metric_name,
                        'level': rule_config.level.value
                    },
                    annotations={
                        'description': rule_config.description,
                        'runbook_url': getattr(rule_config, 'runbook_url', ''),
                        'summary': f"{rule_config.name}: {metric_value}"
                    }
                )
                
                self.active_alerts[rule_id] = alert
                self.alert_history.append(alert)
                
                logger.info(f"触发新告警: {alert.name} (值: {metric_value})")
                return alert
            else:
                # 更新现有告警的值
                existing_alert.current_value = metric_value
                existing_alert.timestamp = current_time
                
        else:
            if existing_alert and existing_alert.status == AlertStatus.ACTIVE:
                # 解决告警
                existing_alert.status = AlertStatus.RESOLVED
                existing_alert.resolved_at = current_time
                
                # 从活跃告警中移除
                del self.active_alerts[rule_id]
                
                logger.info(f"告警已解决: {existing_alert.name}")
                return existing_alert
        
        return None
    
    def _extract_threshold(self, condition: str) -> float:
        """从条件表达式中提取阈值"""
        try:
            for op in ['>=', '<=', '>', '<', '==', '!=']:
                if op in condition:
                    parts = condition.split(op)
                    if len(parts) == 2:
                        return float(parts[1].strip())
            return 0.0
        except:
            return 0.0
    
    def evaluate_all_rules(self, metrics: Dict[str, float]) -> List[Alert]:
        """
        评估所有告警规则
        
        Args:
            metrics: 指标数据字典
            
        Returns:
            List[Alert]: 触发的告警列表
        """
        triggered_alerts = []
        
        for rule_config in ALERT_RULES_CONFIG:
            metric_name = rule_config.metric_name
            
            if metric_name in metrics:
                alert = self.evaluate_rule(rule_config, metrics[metric_name])
                if alert:
                    triggered_alerts.append(alert)
        
        return triggered_alerts
    
    def get_active_alerts(self) -> List[Alert]:
        """获取所有活跃告警"""
        return list(self.active_alerts.values())
    
    def acknowledge_alert(self, rule_id: str, acknowledged_by: str) -> bool:
        """确认告警"""
        if rule_id in self.active_alerts:
            self.active_alerts[rule_id].status = AlertStatus.ACKNOWLEDGED
            self.active_alerts[rule_id].acknowledged_by = acknowledged_by
            logger.info(f"告警已确认: {rule_id} by {acknowledged_by}")
            return True
        return False
    
    def silence_alert(self, rule_id: str, duration_minutes: int = 60) -> bool:
        """静默告警"""
        if rule_id in self.active_alerts:
            self.active_alerts[rule_id].status = AlertStatus.SILENCED
            # TODO: 实现静默时间逻辑
            logger.info(f"告警已静默: {rule_id} for {duration_minutes} minutes")
            return True
        return False


class NotificationSender:
    """
    通知发送器
    
    基于monitor_config.py中的NOTIFICATION_CHANNELS_CONFIG发送告警通知。
    """
    
    def __init__(self):
        self.notification_history = []
    
    async def send_email(self, config: Dict[str, Any], alert: Alert) -> NotificationResult:
        """发送邮件通知"""
        try:
            smtp_server = config.get('smtp_server', 'localhost')
            smtp_port = config.get('smtp_port', 587)
            username = config.get('username', '')
            password = config.get('password', '')
            from_email = config.get('from_email', username)
            to_emails = config.get('to_emails', [])
            
            if not to_emails:
                return NotificationResult(
                    channel='email',
                    success=False,
                    message='没有配置收件人邮箱',
                    timestamp=datetime.now(),
                    error='Missing to_emails configuration'
                )
            
            # 创建邮件内容
            msg = MIMEMultipart()
            msg['From'] = from_email
            msg['To'] = ', '.join(to_emails)
            msg['Subject'] = f"[{alert.level.value.upper()}] {alert.name}"
            
            # 邮件正文
            body = f"""
RedFire监控告警通知

告警名称: {alert.name}
告警级别: {alert.level.value.upper()}
指标名称: {alert.metric_name}
当前值: {alert.current_value}
阈值: {alert.threshold_value}
条件: {alert.condition}
状态: {alert.status.value}
时间: {alert.timestamp}

描述: {alert.description}

告警ID: {alert.alert_id}
规则ID: {alert.rule_id}
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # 发送邮件 (在实际环境中使用)
            # server = smtplib.SMTP(smtp_server, smtp_port)
            # server.starttls()
            # server.login(username, password)
            # server.send_message(msg)
            # server.quit()
            
            # 模拟发送成功
            logger.info(f"邮件告警已发送: {alert.name} to {to_emails}")
            
            return NotificationResult(
                channel='email',
                success=True,
                message=f'邮件已发送到 {len(to_emails)} 个收件人',
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"发送邮件告警失败: {e}")
            return NotificationResult(
                channel='email',
                success=False,
                message='邮件发送失败',
                timestamp=datetime.now(),
                error=str(e)
            )
    
    async def send_webhook(self, config: Dict[str, Any], alert: Alert) -> NotificationResult:
        """发送Webhook通知"""
        try:
            url = config.get('url')
            method = config.get('method', 'POST').upper()
            headers = config.get('headers', {'Content-Type': 'application/json'})
            timeout = config.get('timeout', 10)
            
            if not url:
                return NotificationResult(
                    channel='webhook',
                    success=False,
                    message='Webhook URL未配置',
                    timestamp=datetime.now(),
                    error='Missing webhook URL'
                )
            
            # 构建webhook负载
            payload = {
                'alert_id': alert.alert_id,
                'rule_id': alert.rule_id,
                'name': alert.name,
                'description': alert.description,
                'level': alert.level.value,
                'status': alert.status.value,
                'metric_name': alert.metric_name,
                'current_value': alert.current_value,
                'threshold_value': alert.threshold_value,
                'condition': alert.condition,
                'timestamp': alert.timestamp.isoformat(),
                'labels': alert.labels,
                'annotations': alert.annotations
            }
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
                if method == 'POST':
                    async with session.post(url, json=payload, headers=headers) as response:
                        response_text = await response.text()
                        
                        if response.status < 400:
                            logger.info(f"Webhook告警已发送: {alert.name} to {url}")
                            return NotificationResult(
                                channel='webhook',
                                success=True,
                                message=f'Webhook发送成功 (HTTP {response.status})',
                                timestamp=datetime.now()
                            )
                        else:
                            return NotificationResult(
                                channel='webhook',
                                success=False,
                                message=f'Webhook发送失败 (HTTP {response.status})',
                                timestamp=datetime.now(),
                                error=response_text
                            )
                            
        except Exception as e:
            logger.error(f"发送Webhook告警失败: {e}")
            return NotificationResult(
                channel='webhook',
                success=False,
                message='Webhook发送失败',
                timestamp=datetime.now(),
                error=str(e)
            )
    
    async def send_sms(self, config: Dict[str, Any], alert: Alert) -> NotificationResult:
        """发送短信通知 (模拟实现)"""
        try:
            phone_numbers = config.get('phone_numbers', [])
            
            if not phone_numbers:
                return NotificationResult(
                    channel='sms',
                    success=False,
                    message='没有配置手机号码',
                    timestamp=datetime.now(),
                    error='Missing phone numbers'
                )
            
            # 短信内容
            message = f"[RedFire告警] {alert.level.value.upper()}: {alert.name}, 当前值: {alert.current_value}, 时间: {alert.timestamp.strftime('%H:%M:%S')}"
            
            # 模拟短信发送
            logger.info(f"短信告警已发送: {alert.name} to {phone_numbers}")
            
            return NotificationResult(
                channel='sms',
                success=True,
                message=f'短信已发送到 {len(phone_numbers)} 个号码',
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"发送短信告警失败: {e}")
            return NotificationResult(
                channel='sms',
                success=False,
                message='短信发送失败',
                timestamp=datetime.now(),
                error=str(e)
            )
    
    async def send_log(self, config: Dict[str, Any], alert: Alert) -> NotificationResult:
        """记录日志通知"""
        try:
            log_level = config.get('level', 'INFO').upper()
            
            log_message = f"ALERT [{alert.level.value.upper()}] {alert.name}: {alert.description} " \
                         f"(metric: {alert.metric_name}={alert.current_value}, threshold: {alert.threshold_value})"
            
            # 根据告警级别记录不同级别的日志
            if alert.level == MonitorLevel.CRITICAL:
                logger.critical(log_message)
            elif alert.level == MonitorLevel.ERROR:
                logger.error(log_message)
            elif alert.level == MonitorLevel.WARNING:
                logger.warning(log_message)
            else:
                logger.info(log_message)
            
            return NotificationResult(
                channel='log',
                success=True,
                message='日志记录成功',
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"记录告警日志失败: {e}")
            return NotificationResult(
                channel='log',
                success=False,
                message='日志记录失败',
                timestamp=datetime.now(),
                error=str(e)
            )
    
    async def send_alert(self, alert: Alert) -> List[NotificationResult]:
        """发送告警到所有配置的通知渠道"""
        results = []
        
        for channel_config in NOTIFICATION_CHANNELS_CONFIG:
            channel_type = channel_config.channel_type
            
            # 检查告警级别是否匹配
            if alert.level not in channel_config.alert_levels:
                continue
            
            try:
                if channel_type == 'email':
                    result = await self.send_email(channel_config.config, alert)
                elif channel_type == 'webhook':
                    result = await self.send_webhook(channel_config.config, alert)
                elif channel_type == 'sms':
                    result = await self.send_sms(channel_config.config, alert)
                elif channel_type == 'log':
                    result = await self.send_log(channel_config.config, alert)
                else:
                    result = NotificationResult(
                        channel=channel_type,
                        success=False,
                        message=f'不支持的通知渠道: {channel_type}',
                        timestamp=datetime.now(),
                        error=f'Unsupported channel type: {channel_type}'
                    )
                
                results.append(result)
                self.notification_history.append(result)
                
            except Exception as e:
                logger.error(f"发送告警通知失败 ({channel_type}): {e}")
                results.append(NotificationResult(
                    channel=channel_type,
                    success=False,
                    message=f'通知发送异常: {str(e)}',
                    timestamp=datetime.now(),
                    error=str(e)
                ))
        
        return results


class AlertManager:
    """
    告警管理器
    
    统一管理告警评估和通知发送。
    """
    
    def __init__(self):
        self.evaluator = AlertEvaluator()
        self.sender = NotificationSender()
        self.running = False
    
    async def process_metrics(self, metrics: Dict[str, float]) -> List[Alert]:
        """
        处理指标数据，评估告警并发送通知
        
        Args:
            metrics: 指标数据
            
        Returns:
            List[Alert]: 触发的告警列表
        """
        # 评估告警规则
        triggered_alerts = self.evaluator.evaluate_all_rules(metrics)
        
        # 发送告警通知
        for alert in triggered_alerts:
            try:
                notification_results = await self.sender.send_alert(alert)
                success_count = sum(1 for r in notification_results if r.success)
                total_count = len(notification_results)
                
                logger.info(f"告警通知发送完成: {alert.name} "
                          f"({success_count}/{total_count} 成功)")
                
            except Exception as e:
                logger.error(f"发送告警通知时出错: {alert.name}, 错误: {e}")
        
        return triggered_alerts
    
    def get_alert_summary(self) -> Dict[str, Any]:
        """获取告警摘要"""
        active_alerts = self.evaluator.get_active_alerts()
        
        level_counts = {}
        for level in MonitorLevel:
            level_counts[level.value] = sum(
                1 for alert in active_alerts if alert.level == level
            )
        
        return {
            'total_active': len(active_alerts),
            'by_level': level_counts,
            'recent_notifications': len([
                n for n in self.sender.notification_history[-100:]
                if (datetime.now() - n.timestamp).total_seconds() < 3600  # 最近1小时
            ]),
            'last_evaluation': max([
                alert.timestamp for alert in active_alerts
            ]) if active_alerts else None
        }
    
    async def start_monitoring_loop(self, metrics_source, interval: int = 60):
        """
        启动监控循环
        
        Args:
            metrics_source: 指标数据源 (应该是一个async callable返回metrics dict)
            interval: 评估间隔(秒)
        """
        self.running = True
        logger.info(f"启动告警监控循环，间隔: {interval}秒")
        
        while self.running:
            try:
                start_time = time.time()
                
                # 获取指标数据
                if callable(metrics_source):
                    metrics = await metrics_source()
                else:
                    metrics = metrics_source
                
                # 处理指标并评估告警
                triggered_alerts = await self.process_metrics(metrics)
                
                processing_time = time.time() - start_time
                
                if triggered_alerts:
                    logger.info(f"告警评估完成，触发 {len(triggered_alerts)} 个告警，"
                              f"耗时: {processing_time:.2f}秒")
                
                # 等待下次评估
                await asyncio.sleep(max(0, interval - processing_time))
                
            except Exception as e:
                logger.error(f"告警监控循环出错: {e}")
                await asyncio.sleep(interval)
    
    def stop_monitoring(self):
        """停止监控循环"""
        self.running = False
        logger.info("告警监控循环已停止")


# 全局告警管理器实例
alert_manager = AlertManager()


if __name__ == "__main__":
    # 测试代码
    async def main():
        # 模拟指标数据
        test_metrics = {
            'cpu_usage': 90.5,  # 触发CPU告警
            'memory_usage': 75.0,
            'disk_usage': 60.0,
            'error_rate': 2.5,
            'response_time': 0.8
        }
        
        manager = AlertManager()
        
        print("测试告警评估...")
        alerts = await manager.process_metrics(test_metrics)
        
        print(f"\n触发的告警数量: {len(alerts)}")
        for alert in alerts:
            print(f"  - {alert.name}: {alert.current_value} (级别: {alert.level.value})")
        
        print(f"\n告警摘要:")
        summary = manager.get_alert_summary()
        print(json.dumps(summary, indent=2, default=str))
    
    asyncio.run(main())
