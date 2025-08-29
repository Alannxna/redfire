"""
RedFire 安全监控和告警系统
========================

TODO-15: 安全防护机制优化
提供实时的安全监控、威胁检测和告警功能

功能特性：
- 🔍 实时安全监控
- 🚨 智能威胁检测
- 📊 安全事件分析
- 📢 多渠道告警通知
- 📈 安全指标统计
"""

import asyncio
import json
import logging
import smtplib
import ssl
import time
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
import aiohttp
import redis.asyncio as redis

from .security_config import SecurityConfigManager, SecurityLevel, MonitoringConfig


logger = logging.getLogger(__name__)


class EventType(str, Enum):
    """安全事件类型"""
    AUTHENTICATION_FAILURE = "auth_failure"
    AUTHORIZATION_FAILURE = "authz_failure"
    SQL_INJECTION = "sql_injection"
    XSS_ATTACK = "xss_attack"
    CSRF_ATTACK = "csrf_attack"
    BRUTE_FORCE = "brute_force"
    DDOS_ATTACK = "ddos_attack"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    MALICIOUS_FILE_UPLOAD = "malicious_upload"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    DATA_EXFILTRATION = "data_exfiltration"
    SYSTEM_COMPROMISE = "system_compromise"
    POLICY_VIOLATION = "policy_violation"
    ANOMALY_DETECTED = "anomaly_detected"


class AlertChannel(str, Enum):
    """告警渠道"""
    EMAIL = "email"
    WEBHOOK = "webhook"
    SMS = "sms"
    SLACK = "slack"
    LOG = "log"


@dataclass
class SecurityEvent:
    """安全事件"""
    event_id: str
    event_type: EventType
    severity: SecurityLevel
    timestamp: datetime
    source_ip: str
    user_id: Optional[str]
    user_agent: str
    request_path: str
    event_data: Dict[str, Any]
    risk_score: float
    blocked: bool
    description: str
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['event_type'] = self.event_type.value
        data['severity'] = self.severity.value
        return data


@dataclass
class SecurityAlert:
    """安全告警"""
    alert_id: str
    title: str
    description: str
    severity: SecurityLevel
    events: List[SecurityEvent]
    created_at: datetime
    resolved_at: Optional[datetime] = None
    acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []


class AnomalyDetector:
    """异常检测器"""
    
    def __init__(self, config: SecurityConfigManager):
        self.config = config
        self.redis_client: Optional[redis.Redis] = None
        self._setup_redis()
        
        # 异常检测阈值
        self.login_failure_threshold = 5
        self.unusual_time_threshold = 2  # 标准差倍数
        self.geo_anomaly_threshold = 1000  # 公里
        self.rate_anomaly_threshold = 10  # 正常率的倍数
    
    async def _setup_redis(self):
        """设置Redis连接"""
        try:
            import os
            self.redis_client = redis.Redis(
                host=os.getenv("REDIS_HOST", "localhost"),
                port=int(os.getenv("REDIS_PORT", "6379")),
                decode_responses=True
            )
            await self.redis_client.ping()
        except Exception as e:
            logger.warning(f"异常检测器Redis连接失败: {e}")
            self.redis_client = None
    
    async def detect_anomalies(self, event: SecurityEvent) -> List[SecurityEvent]:
        """检测异常"""
        anomalies = []
        
        # 1. 登录失败异常
        if event.event_type == EventType.AUTHENTICATION_FAILURE:
            if await self._detect_login_failure_anomaly(event):
                anomalies.append(self._create_anomaly_event(
                    event, "login_failure_spike", "检测到异常登录失败尝试"
                ))
        
        # 2. 时间异常
        if await self._detect_time_anomaly(event):
            anomalies.append(self._create_anomaly_event(
                event, "unusual_time", "检测到异常访问时间"
            ))
        
        # 3. 地理位置异常
        if await self._detect_geo_anomaly(event):
            anomalies.append(self._create_anomaly_event(
                event, "geo_anomaly", "检测到异常地理位置访问"
            ))
        
        # 4. 请求频率异常
        if await self._detect_rate_anomaly(event):
            anomalies.append(self._create_anomaly_event(
                event, "rate_anomaly", "检测到异常请求频率"
            ))
        
        # 5. 用户行为异常
        if await self._detect_behavior_anomaly(event):
            anomalies.append(self._create_anomaly_event(
                event, "behavior_anomaly", "检测到异常用户行为"
            ))
        
        return anomalies
    
    async def _detect_login_failure_anomaly(self, event: SecurityEvent) -> bool:
        """检测登录失败异常"""
        if not self.redis_client:
            return False
        
        try:
            key = f"login_failures:{event.source_ip}"
            count = await self.redis_client.incr(key)
            await self.redis_client.expire(key, 300)  # 5分钟窗口
            
            return count >= self.login_failure_threshold
        except Exception:
            return False
    
    async def _detect_time_anomaly(self, event: SecurityEvent) -> bool:
        """检测时间异常"""
        if not event.user_id:
            return False
        
        # 检查是否在异常时间段访问（如深夜）
        hour = event.timestamp.hour
        if hour < 6 or hour > 23:  # 深夜访问
            return True
        
        # 这里可以扩展更复杂的时间模式分析
        return False
    
    async def _detect_geo_anomaly(self, event: SecurityEvent) -> bool:
        """检测地理位置异常"""
        # 这里需要IP地理位置服务
        # 简化实现，检查是否来自异常国家/地区
        if not self.redis_client:
            return False
        
        try:
            # 获取用户历史位置
            if event.user_id:
                key = f"user_locations:{event.user_id}"
                locations = await self.redis_client.smembers(key)
                
                # 如果用户从未从这个IP访问过，可能是异常
                if locations and event.source_ip not in locations:
                    # 这里应该进行地理位置距离计算
                    # 简化为检查IP前缀
                    ip_prefix = ".".join(event.source_ip.split(".")[:2])
                    historical_prefixes = {".".join(loc.split(".")[:2]) for loc in locations}
                    
                    if ip_prefix not in historical_prefixes:
                        return True
                
                # 记录当前位置
                await self.redis_client.sadd(key, event.source_ip)
                await self.redis_client.expire(key, 86400 * 30)  # 30天
        except Exception:
            pass
        
        return False
    
    async def _detect_rate_anomaly(self, event: SecurityEvent) -> bool:
        """检测请求频率异常"""
        if not self.redis_client:
            return False
        
        try:
            key = f"request_rate:{event.source_ip}"
            count = await self.redis_client.incr(key)
            await self.redis_client.expire(key, 60)  # 1分钟窗口
            
            # 如果1分钟内超过100个请求，认为异常
            return count > 100
        except Exception:
            return False
    
    async def _detect_behavior_anomaly(self, event: SecurityEvent) -> bool:
        """检测用户行为异常"""
        if not event.user_id:
            return False
        
        # 检查用户代理异常
        if "bot" in event.user_agent.lower() or len(event.user_agent) < 10:
            return True
        
        # 检查访问路径异常
        suspicious_paths = ["/admin", "/.env", "/wp-admin", "/phpmyadmin"]
        if any(path in event.request_path for path in suspicious_paths):
            return True
        
        return False
    
    def _create_anomaly_event(self, original_event: SecurityEvent, anomaly_type: str, description: str) -> SecurityEvent:
        """创建异常事件"""
        return SecurityEvent(
            event_id=f"anomaly_{int(time.time())}_{anomaly_type}",
            event_type=EventType.ANOMALY_DETECTED,
            severity=SecurityLevel.MEDIUM,
            timestamp=datetime.now(),
            source_ip=original_event.source_ip,
            user_id=original_event.user_id,
            user_agent=original_event.user_agent,
            request_path=original_event.request_path,
            event_data={
                "anomaly_type": anomaly_type,
                "original_event": original_event.event_id,
                "detection_time": datetime.now().isoformat()
            },
            risk_score=0.7,
            blocked=False,
            description=description
        )


class ThreatIntelligence:
    """威胁情报系统"""
    
    def __init__(self):
        self.malicious_ips: set = set()
        self.malicious_domains: set = set()
        self.threat_signatures: List[Dict] = []
        self._last_update = datetime.now()
    
    async def update_threat_intelligence(self):
        """更新威胁情报"""
        if datetime.now() - self._last_update < timedelta(hours=1):
            return  # 1小时内不重复更新
        
        try:
            # 这里可以集成真实的威胁情报源
            # 例如：AbuseIPDB、VirusTotal、Spamhaus等
            await self._update_malicious_ips()
            await self._update_threat_signatures()
            
            self._last_update = datetime.now()
            logger.info("威胁情报更新完成")
        except Exception as e:
            logger.error(f"威胁情报更新失败: {e}")
    
    async def _update_malicious_ips(self):
        """更新恶意IP列表"""
        # 示例：从本地文件或API获取恶意IP
        # 这里使用一些已知的恶意IP示例
        self.malicious_ips.update([
            "192.168.1.100",  # 示例恶意IP
            "10.0.0.100",
        ])
    
    async def _update_threat_signatures(self):
        """更新威胁签名"""
        # 示例威胁签名
        self.threat_signatures = [
            {
                "name": "SQL Injection Pattern",
                "pattern": r"(union|select|insert|delete|drop|create|alter)",
                "severity": "HIGH",
                "category": "sql_injection"
            },
            {
                "name": "XSS Pattern",
                "pattern": r"(<script|javascript:|on\w+\s*=)",
                "severity": "HIGH",
                "category": "xss"
            }
        ]
    
    def is_malicious_ip(self, ip: str) -> bool:
        """检查IP是否恶意"""
        return ip in self.malicious_ips
    
    def is_malicious_domain(self, domain: str) -> bool:
        """检查域名是否恶意"""
        return domain in self.malicious_domains


class AlertManager:
    """告警管理器"""
    
    def __init__(self, config: SecurityConfigManager):
        self.config = config
        self.active_alerts: Dict[str, SecurityAlert] = {}
        self.alert_handlers: Dict[AlertChannel, Callable] = {
            AlertChannel.EMAIL: self._send_email_alert,
            AlertChannel.WEBHOOK: self._send_webhook_alert,
            AlertChannel.SMS: self._send_sms_alert,
            AlertChannel.LOG: self._log_alert,
        }
    
    async def create_alert(self, events: List[SecurityEvent], title: str, description: str) -> SecurityAlert:
        """创建告警"""
        if not events:
            return None
        
        # 计算告警严重程度
        severity = max([event.severity for event in events], 
                      key=lambda x: ["LOW", "MEDIUM", "HIGH", "CRITICAL"].index(x))
        
        alert = SecurityAlert(
            alert_id=f"alert_{int(time.time())}",
            title=title,
            description=description,
            severity=severity,
            events=events,
            created_at=datetime.now(),
            tags=[event.event_type.value for event in events]
        )
        
        self.active_alerts[alert.alert_id] = alert
        
        # 发送告警
        if self.config.monitoring.alert_enabled:
            await self._send_alert(alert)
        
        return alert
    
    async def _send_alert(self, alert: SecurityAlert):
        """发送告警"""
        # 检查严重程度阈值
        severity_levels = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        if severity_levels.index(alert.severity) < severity_levels.index(self.config.monitoring.alert_severity_threshold):
            return
        
        # 发送到各个渠道
        for channel in self.config.monitoring.alert_channels:
            try:
                handler = self.alert_handlers.get(AlertChannel(channel))
                if handler:
                    await handler(alert)
            except Exception as e:
                logger.error(f"发送告警到 {channel} 失败: {e}")
    
    async def _send_email_alert(self, alert: SecurityAlert):
        """发送邮件告警"""
        try:
            import os
            smtp_server = os.getenv("SMTP_SERVER", "localhost")
            smtp_port = int(os.getenv("SMTP_PORT", "587"))
            smtp_username = os.getenv("SMTP_USERNAME")
            smtp_password = os.getenv("SMTP_PASSWORD")
            alert_email = os.getenv("ALERT_EMAIL", "admin@redfire.com")
            
            if not smtp_username or not smtp_password:
                logger.warning("邮件告警配置不完整，跳过邮件发送")
                return
            
            # 创建邮件
            msg = MimeMultipart()
            msg['From'] = smtp_username
            msg['To'] = alert_email
            msg['Subject'] = f"RedFire安全告警: {alert.title}"
            
            # 邮件内容
            body = f"""
安全告警详情：

告警ID: {alert.alert_id}
标题: {alert.title}
严重程度: {alert.severity}
创建时间: {alert.created_at.strftime('%Y-%m-%d %H:%M:%S')}
描述: {alert.description}

相关事件:
"""
            
            for i, event in enumerate(alert.events[:5]):  # 限制显示前5个事件
                body += f"""
事件 {i+1}:
- 类型: {event.event_type.value}
- 来源IP: {event.source_ip}
- 时间: {event.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
- 描述: {event.description}
"""
            
            if len(alert.events) > 5:
                body += f"\n... 还有 {len(alert.events) - 5} 个相关事件"
            
            msg.attach(MimeText(body, 'plain', 'utf-8'))
            
            # 发送邮件
            context = ssl.create_default_context()
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls(context=context)
                server.login(smtp_username, smtp_password)
                server.send_message(msg)
            
            logger.info(f"邮件告警已发送: {alert.alert_id}")
            
        except Exception as e:
            logger.error(f"发送邮件告警失败: {e}")
    
    async def _send_webhook_alert(self, alert: SecurityAlert):
        """发送Webhook告警"""
        try:
            import os
            webhook_url = os.getenv("ALERT_WEBHOOK_URL")
            if not webhook_url:
                return
            
            payload = {
                "alert_id": alert.alert_id,
                "title": alert.title,
                "description": alert.description,
                "severity": alert.severity,
                "created_at": alert.created_at.isoformat(),
                "events": [event.to_dict() for event in alert.events[:10]]  # 限制事件数量
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=payload) as response:
                    if response.status == 200:
                        logger.info(f"Webhook告警已发送: {alert.alert_id}")
                    else:
                        logger.error(f"Webhook告警发送失败: {response.status}")
                        
        except Exception as e:
            logger.error(f"发送Webhook告警失败: {e}")
    
    async def _send_sms_alert(self, alert: SecurityAlert):
        """发送短信告警"""
        # 这里需要集成短信服务提供商API
        # 例如：阿里云短信、腾讯云短信等
        logger.info(f"短信告警: {alert.title} (需要集成短信服务)")
    
    async def _log_alert(self, alert: SecurityAlert):
        """记录告警日志"""
        logger.critical(
            f"安全告警 | ID: {alert.alert_id} | "
            f"标题: {alert.title} | "
            f"严重程度: {alert.severity} | "
            f"事件数: {len(alert.events)}"
        )
    
    def acknowledge_alert(self, alert_id: str, acknowledged_by: str):
        """确认告警"""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.acknowledged = True
            alert.acknowledged_by = acknowledged_by
            logger.info(f"告警 {alert_id} 已被 {acknowledged_by} 确认")
    
    def resolve_alert(self, alert_id: str):
        """解决告警"""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.resolved_at = datetime.now()
            logger.info(f"告警 {alert_id} 已解决")


class SecurityMonitor:
    """安全监控主类"""
    
    def __init__(self, config: SecurityConfigManager):
        self.config = config
        self.redis_client: Optional[redis.Redis] = None
        self._setup_redis()
        
        # 初始化组件
        self.anomaly_detector = AnomalyDetector(config)
        self.threat_intelligence = ThreatIntelligence()
        self.alert_manager = AlertManager(config)
        
        # 事件队列
        self.event_queue: asyncio.Queue = asyncio.Queue()
        self.metrics: Dict[str, Any] = {}
        
        # 启动后台任务
        self._start_background_tasks()
    
    async def _setup_redis(self):
        """设置Redis连接"""
        try:
            import os
            self.redis_client = redis.Redis(
                host=os.getenv("REDIS_HOST", "localhost"),
                port=int(os.getenv("REDIS_PORT", "6379")),
                decode_responses=True
            )
            await self.redis_client.ping()
        except Exception as e:
            logger.warning(f"安全监控器Redis连接失败: {e}")
            self.redis_client = None
    
    def _start_background_tasks(self):
        """启动后台任务"""
        asyncio.create_task(self._process_events())
        asyncio.create_task(self._update_threat_intelligence())
        asyncio.create_task(self._collect_metrics())
    
    async def record_event(self, event: SecurityEvent):
        """记录安全事件"""
        # 添加到队列
        await self.event_queue.put(event)
        
        # 记录到Redis（如果可用）
        if self.redis_client:
            try:
                key = f"security_events:{event.timestamp.strftime('%Y%m%d')}"
                await self.redis_client.lpush(key, json.dumps(event.to_dict()))
                await self.redis_client.expire(key, 86400 * 7)  # 7天过期
            except Exception as e:
                logger.warning(f"Redis记录事件失败: {e}")
    
    async def _process_events(self):
        """处理事件队列"""
        while True:
            try:
                event = await self.event_queue.get()
                
                # 威胁情报检查
                if self.threat_intelligence.is_malicious_ip(event.source_ip):
                    event.risk_score = min(1.0, event.risk_score + 0.3)
                    event.description += " [威胁情报匹配]"
                
                # 异常检测
                anomalies = await self.anomaly_detector.detect_anomalies(event)
                all_events = [event] + anomalies
                
                # 创建告警（如果需要）
                if self._should_create_alert(all_events):
                    await self._create_alert_for_events(all_events)
                
                # 更新指标
                self._update_metrics(event)
                
                # 记录日志
                if self.config.monitoring.security_logging:
                    logger.info(f"安全事件: {event.event_type.value} | {event.source_ip} | {event.description}")
                
                self.event_queue.task_done()
                
            except Exception as e:
                logger.error(f"处理安全事件失败: {e}")
                await asyncio.sleep(1)
    
    def _should_create_alert(self, events: List[SecurityEvent]) -> bool:
        """判断是否应该创建告警"""
        # 高危事件直接告警
        for event in events:
            if event.severity in [SecurityLevel.HIGH, SecurityLevel.CRITICAL]:
                return True
            if event.risk_score >= 0.8:
                return True
        
        # 多个中等威胁事件组合告警
        medium_events = [e for e in events if e.severity == SecurityLevel.MEDIUM]
        if len(medium_events) >= 3:
            return True
        
        return False
    
    async def _create_alert_for_events(self, events: List[SecurityEvent]):
        """为事件创建告警"""
        if not events:
            return
        
        # 确定告警类型和描述
        if len(events) == 1:
            event = events[0]
            title = f"安全事件: {event.event_type.value}"
            description = f"检测到安全威胁: {event.description}"
        else:
            title = f"安全事件组合告警 ({len(events)}个事件)"
            description = f"检测到 {len(events)} 个相关安全事件，可能存在组合攻击"
        
        await self.alert_manager.create_alert(events, title, description)
    
    async def _update_threat_intelligence(self):
        """定期更新威胁情报"""
        while True:
            try:
                await self.threat_intelligence.update_threat_intelligence()
                await asyncio.sleep(3600)  # 每小时更新一次
            except Exception as e:
                logger.error(f"更新威胁情报失败: {e}")
                await asyncio.sleep(300)  # 出错后5分钟重试
    
    async def _collect_metrics(self):
        """收集安全指标"""
        while True:
            try:
                await self._calculate_security_metrics()
                await asyncio.sleep(60)  # 每分钟计算一次
            except Exception as e:
                logger.error(f"收集安全指标失败: {e}")
                await asyncio.sleep(60)
    
    async def _calculate_security_metrics(self):
        """计算安全指标"""
        if not self.redis_client:
            return
        
        try:
            now = datetime.now()
            today_key = f"security_events:{now.strftime('%Y%m%d')}"
            
            # 获取今日事件
            events_data = await self.redis_client.lrange(today_key, 0, -1)
            
            # 统计指标
            total_events = len(events_data)
            event_types = {}
            severity_counts = {}
            
            for event_json in events_data:
                try:
                    event_data = json.loads(event_json)
                    event_type = event_data.get('event_type', 'unknown')
                    severity = event_data.get('severity', 'LOW')
                    
                    event_types[event_type] = event_types.get(event_type, 0) + 1
                    severity_counts[severity] = severity_counts.get(severity, 0) + 1
                except Exception:
                    continue
            
            # 更新指标
            self.metrics.update({
                "total_events_today": total_events,
                "event_types": event_types,
                "severity_distribution": severity_counts,
                "last_updated": now.isoformat(),
                "threat_score": self._calculate_threat_score(severity_counts)
            })
            
            # 存储指标到Redis
            metrics_key = f"security_metrics:{now.strftime('%Y%m%d')}"
            await self.redis_client.set(metrics_key, json.dumps(self.metrics))
            await self.redis_client.expire(metrics_key, 86400 * 30)  # 30天过期
            
        except Exception as e:
            logger.error(f"计算安全指标失败: {e}")
    
    def _calculate_threat_score(self, severity_counts: Dict[str, int]) -> float:
        """计算威胁分数"""
        weights = {
            "LOW": 1,
            "MEDIUM": 3,
            "HIGH": 7,
            "CRITICAL": 15
        }
        
        total_score = sum(
            severity_counts.get(severity, 0) * weight
            for severity, weight in weights.items()
        )
        
        # 归一化到0-1范围
        max_possible_score = 100 * weights["CRITICAL"]  # 假设最大100个严重事件
        return min(1.0, total_score / max_possible_score)
    
    def _update_metrics(self, event: SecurityEvent):
        """更新实时指标"""
        # 这里可以更新实时指标
        pass
    
    async def get_security_dashboard(self) -> Dict[str, Any]:
        """获取安全仪表板数据"""
        return {
            "metrics": self.metrics,
            "active_alerts": len(self.alert_manager.active_alerts),
            "threat_intelligence_status": {
                "malicious_ips": len(self.threat_intelligence.malicious_ips),
                "last_update": self.threat_intelligence._last_update.isoformat(),
            },
            "system_status": "operational"
        }


# 导入依赖
import os
