"""
告警规则服务
==========

负责管理和评估告警规则的具体实现
"""

import asyncio
import uuid
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta

from ....core.common.exceptions import DomainException
from ..entities.alert_rule_entity import AlertRule, AlertSeverity, AlertStatus, AlertCondition
from ..entities.system_metrics_entity import SystemMetrics
from ..repositories.alert_rule_repository import IAlertRuleRepository
from ..repositories.system_metrics_repository import ISystemMetricsRepository


class AlertRuleService:
    """
    告警规则服务
    
    负责管理告警规则，包括：
    - 创建、更新、删除告警规则
    - 评估告警条件
    - 管理告警状态
    - 告警抑制和去重
    """
    
    def __init__(
        self,
        alert_rule_repository: IAlertRuleRepository,
        metrics_repository: ISystemMetricsRepository
    ):
        self._alert_rule_repo = alert_rule_repository
        self._metrics_repo = metrics_repository
        
        # 告警状态跟踪
        self._active_alerts = {}  # rule_id -> alert_state
        self._alert_history = {}  # rule_id -> [alert_events]
        self._suppressed_alerts = {}  # rule_id -> suppression_end_time
        
        # 告警配置
        self._evaluation_interval = 10  # 秒
        self._max_history_size = 1000
        self._default_suppress_duration = 300  # 5分钟
    
    async def create_alert_rule(
        self,
        rule_name: str,
        description: Optional[str],
        service_name: str,
        metric_name: str,
        condition: AlertCondition,
        threshold_value: Union[float, int, str],
        severity: AlertSeverity,
        duration_seconds: int = 60,
        notification_channels: Optional[List[str]] = None
    ) -> AlertRule:
        """
        创建告警规则
        
        Args:
            rule_name: 规则名称
            description: 规则描述
            service_name: 监控的服务名称
            metric_name: 监控的指标名称
            condition: 告警条件
            threshold_value: 阈值
            severity: 严重程度
            duration_seconds: 持续时间（秒）
            notification_channels: 通知渠道
            
        Returns:
            AlertRule: 创建的告警规则
        """
        try:
            rule = AlertRule(
                rule_id=str(uuid.uuid4()),
                rule_name=rule_name,
                description=description,
                service_name=service_name,
                metric_name=metric_name,
                condition=condition,
                threshold_value=threshold_value,
                duration_seconds=duration_seconds,
                severity=severity,
                status=AlertStatus.ACTIVE,
                notification_channels=notification_channels or [],
            )
            
            success = await self._alert_rule_repo.save_alert_rule(rule)
            if not success:
                raise DomainException("告警规则保存失败")
            
            return rule
            
        except Exception as e:
            raise DomainException(f"创建告警规则失败: {e}")
    
    async def update_alert_rule(self, rule: AlertRule) -> AlertRule:
        """
        更新告警规则
        
        Args:
            rule: 告警规则
            
        Returns:
            AlertRule: 更新后的告警规则
        """
        try:
            rule.updated_at = datetime.now()
            
            success = await self._alert_rule_repo.update_alert_rule(rule)
            if not success:
                raise DomainException("告警规则更新失败")
            
            return rule
            
        except Exception as e:
            raise DomainException(f"更新告警规则失败: {e}")
    
    async def delete_alert_rule(self, rule_id: str) -> bool:
        """
        删除告警规则
        
        Args:
            rule_id: 规则ID
            
        Returns:
            bool: 删除是否成功
        """
        try:
            # 清理相关状态
            if rule_id in self._active_alerts:
                del self._active_alerts[rule_id]
            if rule_id in self._alert_history:
                del self._alert_history[rule_id]
            if rule_id in self._suppressed_alerts:
                del self._suppressed_alerts[rule_id]
            
            return await self._alert_rule_repo.delete_alert_rule(rule_id)
            
        except Exception as e:
            raise DomainException(f"删除告警规则失败: {e}")
    
    async def enable_alert_rule(self, rule_id: str) -> bool:
        """
        启用告警规则
        
        Args:
            rule_id: 规则ID
            
        Returns:
            bool: 启用是否成功
        """
        try:
            return await self._alert_rule_repo.enable_alert_rule(rule_id)
        except Exception as e:
            raise DomainException(f"启用告警规则失败: {e}")
    
    async def disable_alert_rule(self, rule_id: str) -> bool:
        """
        禁用告警规则
        
        Args:
            rule_id: 规则ID
            
        Returns:
            bool: 禁用是否成功
        """
        try:
            # 清理活跃告警状态
            if rule_id in self._active_alerts:
                del self._active_alerts[rule_id]
            
            return await self._alert_rule_repo.disable_alert_rule(rule_id)
        except Exception as e:
            raise DomainException(f"禁用告警规则失败: {e}")
    
    async def evaluate_all_alert_rules(self) -> Dict[str, Any]:
        """
        评估所有活跃的告警规则
        
        Returns:
            Dict[str, Any]: 评估结果摘要
        """
        try:
            # 获取所有活跃的告警规则
            active_rules = await self._alert_rule_repo.get_active_alert_rules()
            
            evaluation_results = {
                "total_rules": len(active_rules),
                "triggered_rules": 0,
                "resolved_rules": 0,
                "suppressed_rules": 0,
                "error_rules": 0,
                "evaluation_time": datetime.now().isoformat(),
                "rule_results": []
            }
            
            # 并行评估规则（批量处理以避免性能问题）
            batch_size = 10
            for i in range(0, len(active_rules), batch_size):
                batch = active_rules[i:i + batch_size]
                tasks = [self._evaluate_single_rule(rule) for rule in batch]
                
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for rule, result in zip(batch, batch_results):
                    if isinstance(result, Exception):
                        evaluation_results["error_rules"] += 1
                        evaluation_results["rule_results"].append({
                            "rule_id": rule.rule_id,
                            "rule_name": rule.rule_name,
                            "status": "error",
                            "error": str(result)
                        })
                    else:
                        evaluation_results["rule_results"].append(result)
                        
                        if result["status"] == "triggered":
                            evaluation_results["triggered_rules"] += 1
                        elif result["status"] == "resolved":
                            evaluation_results["resolved_rules"] += 1
                        elif result["status"] == "suppressed":
                            evaluation_results["suppressed_rules"] += 1
            
            return evaluation_results
            
        except Exception as e:
            return {
                "error": str(e),
                "evaluation_time": datetime.now().isoformat()
            }
    
    async def _evaluate_single_rule(self, rule: AlertRule) -> Dict[str, Any]:
        """
        评估单个告警规则
        
        Args:
            rule: 告警规则
            
        Returns:
            Dict[str, Any]: 评估结果
        """
        try:
            # 检查是否被抑制
            if self._is_alert_suppressed(rule.rule_id):
                return {
                    "rule_id": rule.rule_id,
                    "rule_name": rule.rule_name,
                    "status": "suppressed",
                    "message": "告警被抑制中"
                }
            
            # 获取最新的指标数据
            latest_metrics = await self._metrics_repo.get_latest_metrics(
                service_name=rule.service_name,
                metric_name=rule.metric_name
            )
            
            if not latest_metrics:
                return {
                    "rule_id": rule.rule_id,
                    "rule_name": rule.rule_name,
                    "status": "no_data",
                    "message": "没有找到相关指标数据"
                }
            
            latest_metric = latest_metrics[0]
            current_value = latest_metric.value
            
            # 评估告警条件
            condition_met = rule.evaluate_condition(current_value)
            
            # 检查持续时间
            duration_met = await self._check_duration_condition(rule, condition_met)
            
            # 确定告警状态
            current_time = datetime.now()
            
            if condition_met and duration_met:
                # 触发告警
                if rule.rule_id not in self._active_alerts:
                    # 新告警
                    self._active_alerts[rule.rule_id] = {
                        "first_triggered": current_time,
                        "last_triggered": current_time,
                        "trigger_count": 1,
                        "current_value": current_value,
                        "threshold_value": rule.threshold_value
                    }
                    
                    # 更新规则的最后触发时间
                    await self._alert_rule_repo.update_rule_last_triggered(rule.rule_id, current_time)
                    
                    # 记录告警历史
                    self._record_alert_history(rule.rule_id, "triggered", {
                        "current_value": current_value,
                        "threshold_value": rule.threshold_value,
                        "condition": rule.condition.value
                    })
                    
                    # 应用抑制
                    self._apply_alert_suppression(rule.rule_id, rule.suppress_duration_seconds)
                    
                    return {
                        "rule_id": rule.rule_id,
                        "rule_name": rule.rule_name,
                        "status": "triggered",
                        "message": f"告警触发: {rule.metric_name} {rule.condition.value} {rule.threshold_value}",
                        "current_value": current_value,
                        "threshold_value": rule.threshold_value,
                        "severity": rule.severity.value,
                        "first_triggered": current_time.isoformat()
                    }
                else:
                    # 持续告警
                    alert_state = self._active_alerts[rule.rule_id]
                    alert_state["last_triggered"] = current_time
                    alert_state["trigger_count"] += 1
                    alert_state["current_value"] = current_value
                    
                    return {
                        "rule_id": rule.rule_id,
                        "rule_name": rule.rule_name,
                        "status": "active",
                        "message": f"告警持续中: {rule.metric_name} {rule.condition.value} {rule.threshold_value}",
                        "current_value": current_value,
                        "threshold_value": rule.threshold_value,
                        "severity": rule.severity.value,
                        "duration_seconds": (current_time - alert_state["first_triggered"]).total_seconds(),
                        "trigger_count": alert_state["trigger_count"]
                    }
            else:
                # 条件不满足
                if rule.rule_id in self._active_alerts:
                    # 告警恢复
                    alert_state = self._active_alerts[rule.rule_id]
                    del self._active_alerts[rule.rule_id]
                    
                    # 记录恢复历史
                    self._record_alert_history(rule.rule_id, "resolved", {
                        "current_value": current_value,
                        "threshold_value": rule.threshold_value,
                        "duration_seconds": (current_time - alert_state["first_triggered"]).total_seconds()
                    })
                    
                    return {
                        "rule_id": rule.rule_id,
                        "rule_name": rule.rule_name,
                        "status": "resolved",
                        "message": f"告警恢复: {rule.metric_name} 当前值 {current_value}",
                        "current_value": current_value,
                        "threshold_value": rule.threshold_value,
                        "resolved_time": current_time.isoformat()
                    }
                else:
                    # 正常状态
                    return {
                        "rule_id": rule.rule_id,
                        "rule_name": rule.rule_name,
                        "status": "normal",
                        "message": f"指标正常: {rule.metric_name} 当前值 {current_value}",
                        "current_value": current_value,
                        "threshold_value": rule.threshold_value
                    }
                    
        except Exception as e:
            return {
                "rule_id": rule.rule_id,
                "rule_name": rule.rule_name,
                "status": "error",
                "message": f"规则评估错误: {str(e)}"
            }
    
    async def _check_duration_condition(self, rule: AlertRule, condition_met: bool) -> bool:
        """
        检查持续时间条件
        
        Args:
            rule: 告警规则
            condition_met: 条件是否满足
            
        Returns:
            bool: 持续时间条件是否满足
        """
        if rule.duration_seconds <= 0:
            return condition_met
        
        current_time = datetime.now()
        
        # 获取指定持续时间内的指标数据
        start_time = current_time - timedelta(seconds=rule.duration_seconds)
        
        metrics = await self._metrics_repo.get_metrics_by_service(
            service_name=rule.service_name,
            metric_name=rule.metric_name,
            start_time=start_time,
            end_time=current_time
        )
        
        if not metrics:
            return False
        
        # 检查在持续时间内条件是否一直满足
        satisfied_count = 0
        for metric in metrics:
            if rule.evaluate_condition(metric.value):
                satisfied_count += 1
        
        # 如果超过80%的时间点都满足条件，则认为持续时间条件满足
        satisfaction_rate = satisfied_count / len(metrics)
        return satisfaction_rate >= 0.8
    
    def _is_alert_suppressed(self, rule_id: str) -> bool:
        """
        检查告警是否被抑制
        
        Args:
            rule_id: 规则ID
            
        Returns:
            bool: 是否被抑制
        """
        if rule_id not in self._suppressed_alerts:
            return False
        
        suppression_end = self._suppressed_alerts[rule_id]
        if datetime.now() > suppression_end:
            # 抑制期结束，移除抑制状态
            del self._suppressed_alerts[rule_id]
            return False
        
        return True
    
    def _apply_alert_suppression(self, rule_id: str, duration_seconds: int):
        """
        应用告警抑制
        
        Args:
            rule_id: 规则ID
            duration_seconds: 抑制持续时间（秒）
        """
        if duration_seconds > 0:
            suppression_end = datetime.now() + timedelta(seconds=duration_seconds)
            self._suppressed_alerts[rule_id] = suppression_end
    
    def _record_alert_history(self, rule_id: str, event_type: str, details: Dict[str, Any]):
        """
        记录告警历史
        
        Args:
            rule_id: 规则ID
            event_type: 事件类型
            details: 事件详情
        """
        if rule_id not in self._alert_history:
            self._alert_history[rule_id] = []
        
        history_entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "details": details
        }
        
        self._alert_history[rule_id].append(history_entry)
        
        # 限制历史记录大小
        if len(self._alert_history[rule_id]) > self._max_history_size:
            self._alert_history[rule_id] = self._alert_history[rule_id][-self._max_history_size:]
    
    async def get_alert_status_summary(self) -> Dict[str, Any]:
        """
        获取告警状态摘要
        
        Returns:
            Dict[str, Any]: 告警状态摘要
        """
        try:
            # 获取所有告警规则统计
            rule_stats = await self._alert_rule_repo.get_alert_rule_statistics()
            
            # 计算当前活跃告警
            active_alert_count = len(self._active_alerts)
            suppressed_alert_count = len(self._suppressed_alerts)
            
            # 计算不同严重程度的告警数量
            severity_counts = {sev.value: 0 for sev in AlertSeverity}
            
            for rule_id in self._active_alerts:
                rule = await self._alert_rule_repo.get_alert_rule(rule_id)
                if rule:
                    severity_counts[rule.severity.value] += 1
            
            return {
                "summary": {
                    "total_rules": rule_stats.get("total_rules", 0),
                    "active_rules": rule_stats.get("active_rules", 0),
                    "disabled_rules": rule_stats.get("disabled_rules", 0),
                    "active_alerts": active_alert_count,
                    "suppressed_alerts": suppressed_alert_count,
                    "total_alerts_24h": rule_stats.get("total_alerts_24h", 0),
                },
                "severity_breakdown": severity_counts,
                "active_alerts": [
                    {
                        "rule_id": rule_id,
                        "first_triggered": state["first_triggered"].isoformat(),
                        "last_triggered": state["last_triggered"].isoformat(),
                        "trigger_count": state["trigger_count"],
                        "current_value": state["current_value"],
                        "threshold_value": state["threshold_value"],
                        "duration_seconds": (datetime.now() - state["first_triggered"]).total_seconds()
                    }
                    for rule_id, state in self._active_alerts.items()
                ],
                "suppressed_alerts": [
                    {
                        "rule_id": rule_id,
                        "suppression_end": end_time.isoformat(),
                        "remaining_seconds": (end_time - datetime.now()).total_seconds()
                    }
                    for rule_id, end_time in self._suppressed_alerts.items()
                ],
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "last_updated": datetime.now().isoformat()
            }
    
    async def get_alert_history(self, rule_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        获取告警历史
        
        Args:
            rule_id: 规则ID
            limit: 返回数量限制
            
        Returns:
            List[Dict[str, Any]]: 告警历史列表
        """
        if rule_id not in self._alert_history:
            return []
        
        history = self._alert_history[rule_id]
        return history[-limit:] if limit > 0 else history
