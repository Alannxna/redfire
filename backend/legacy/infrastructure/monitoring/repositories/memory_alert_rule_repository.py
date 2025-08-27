"""
内存告警规则仓储实现
==================

基于内存的告警规则仓储实现
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import asyncio
from collections import defaultdict

from ....domain.monitoring.repositories.alert_rule_repository import IAlertRuleRepository
from ....domain.monitoring.entities.alert_rule_entity import AlertRule, AlertSeverity, AlertStatus


class InMemoryAlertRuleRepository(IAlertRuleRepository):
    """内存告警规则仓储实现"""
    
    def __init__(self):
        self._rules: Dict[str, AlertRule] = {}
        self._service_rules: Dict[str, List[str]] = defaultdict(list)
        self._metric_rules: Dict[str, List[str]] = defaultdict(list)
        self._severity_rules: Dict[AlertSeverity, List[str]] = defaultdict(list)
        self._status_rules: Dict[AlertStatus, List[str]] = defaultdict(list)
        self._lock = asyncio.Lock()
    
    async def save_alert_rule(self, rule: AlertRule) -> bool:
        """保存告警规则"""
        async with self._lock:
            try:
                self._rules[rule.rule_id] = rule
                self._service_rules[rule.service_name].append(rule.rule_id)
                metric_key = f"{rule.service_name}:{rule.metric_name}"
                self._metric_rules[metric_key].append(rule.rule_id)
                self._severity_rules[rule.severity].append(rule.rule_id)
                self._status_rules[rule.status].append(rule.rule_id)
                return True
            except Exception:
                return False
    
    async def get_alert_rule(self, rule_id: str) -> Optional[AlertRule]:
        """获取告警规则"""
        return self._rules.get(rule_id)
    
    async def get_alert_rules_by_service(
        self, 
        service_name: str,
        status: Optional[AlertStatus] = None
    ) -> List[AlertRule]:
        """获取指定服务的告警规则"""
        rule_ids = self._service_rules.get(service_name, [])
        results = []
        
        for rule_id in rule_ids:
            if rule_id in self._rules:
                rule = self._rules[rule_id]
                if status is None or rule.status == status:
                    results.append(rule)
        
        return results
    
    async def get_alert_rules_by_metric(
        self, 
        service_name: str,
        metric_name: str,
        status: Optional[AlertStatus] = None
    ) -> List[AlertRule]:
        """获取指定指标的告警规则"""
        metric_key = f"{service_name}:{metric_name}"
        rule_ids = self._metric_rules.get(metric_key, [])
        results = []
        
        for rule_id in rule_ids:
            if rule_id in self._rules:
                rule = self._rules[rule_id]
                if status is None or rule.status == status:
                    results.append(rule)
        
        return results
    
    async def get_alert_rules_by_severity(
        self, 
        severity: AlertSeverity,
        status: Optional[AlertStatus] = None
    ) -> List[AlertRule]:
        """获取指定严重程度的告警规则"""
        rule_ids = self._severity_rules.get(severity, [])
        results = []
        
        for rule_id in rule_ids:
            if rule_id in self._rules:
                rule = self._rules[rule_id]
                if status is None or rule.status == status:
                    results.append(rule)
        
        return results
    
    async def get_active_alert_rules(self) -> List[AlertRule]:
        """获取所有激活的告警规则"""
        rule_ids = self._status_rules.get(AlertStatus.ACTIVE, [])
        results = []
        
        for rule_id in rule_ids:
            if rule_id in self._rules:
                results.append(self._rules[rule_id])
        
        return results
    
    async def update_alert_rule(self, rule: AlertRule) -> bool:
        """更新告警规则"""
        async with self._lock:
            if rule.rule_id not in self._rules:
                return False
            
            # 先从旧的索引中移除
            old_rule = self._rules[rule.rule_id]
            self._remove_from_indexes(old_rule)
            
            # 更新规则
            rule.updated_at = datetime.now()
            self._rules[rule.rule_id] = rule
            
            # 重新添加到索引
            self._add_to_indexes(rule)
            
            return True
    
    async def delete_alert_rule(self, rule_id: str) -> bool:
        """删除告警规则"""
        async with self._lock:
            if rule_id not in self._rules:
                return False
            
            rule = self._rules.pop(rule_id)
            self._remove_from_indexes(rule)
            return True
    
    async def update_rule_last_triggered(
        self, 
        rule_id: str, 
        triggered_at: datetime
    ) -> bool:
        """更新规则最后触发时间"""
        if rule_id in self._rules:
            self._rules[rule_id].last_triggered_at = triggered_at
            return True
        return False
    
    async def enable_alert_rule(self, rule_id: str) -> bool:
        """启用告警规则"""
        async with self._lock:
            if rule_id not in self._rules:
                return False
            
            rule = self._rules[rule_id]
            if rule.status != AlertStatus.ACTIVE:
                # 从旧状态索引中移除
                if rule_id in self._status_rules[rule.status]:
                    self._status_rules[rule.status].remove(rule_id)
                
                # 更新状态
                rule.status = AlertStatus.ACTIVE
                rule.updated_at = datetime.now()
                
                # 添加到新状态索引
                self._status_rules[AlertStatus.ACTIVE].append(rule_id)
            
            return True
    
    async def disable_alert_rule(self, rule_id: str) -> bool:
        """禁用告警规则"""
        async with self._lock:
            if rule_id not in self._rules:
                return False
            
            rule = self._rules[rule_id]
            if rule.status != AlertStatus.DISABLED:
                # 从旧状态索引中移除
                if rule_id in self._status_rules[rule.status]:
                    self._status_rules[rule.status].remove(rule_id)
                
                # 更新状态
                rule.status = AlertStatus.DISABLED
                rule.updated_at = datetime.now()
                
                # 添加到新状态索引
                self._status_rules[AlertStatus.DISABLED].append(rule_id)
            
            return True
    
    async def search_alert_rules(
        self,
        query: str,
        status: Optional[AlertStatus] = None,
        severity: Optional[AlertSeverity] = None,
        limit: int = 100
    ) -> List[AlertRule]:
        """搜索告警规则"""
        results = []
        count = 0
        
        for rule in self._rules.values():
            if count >= limit:
                break
            
            # 查询匹配
            if (query.lower() in rule.rule_name.lower() or
                query.lower() in rule.service_name.lower() or
                query.lower() in rule.metric_name.lower() or
                (rule.description and query.lower() in rule.description.lower())):
                
                # 状态过滤
                if status and rule.status != status:
                    continue
                
                # 严重程度过滤
                if severity and rule.severity != severity:
                    continue
                
                results.append(rule)
                count += 1
        
        return results
    
    async def get_alert_rule_statistics(self) -> Dict[str, Any]:
        """获取告警规则统计信息"""
        total_rules = len(self._rules)
        status_counts = defaultdict(int)
        severity_counts = defaultdict(int)
        service_counts = defaultdict(int)
        
        for rule in self._rules.values():
            status_counts[rule.status.value] += 1
            severity_counts[rule.severity.value] += 1
            service_counts[rule.service_name] += 1
        
        return {
            "total_rules": total_rules,
            "status_breakdown": dict(status_counts),
            "severity_breakdown": dict(severity_counts),
            "service_breakdown": dict(service_counts),
            "active_rules": status_counts.get("active", 0),
            "disabled_rules": status_counts.get("disabled", 0),
            "critical_rules": severity_counts.get("critical", 0),
            "high_priority_rules": severity_counts.get("high", 0),
        }
    
    def _add_to_indexes(self, rule: AlertRule):
        """添加到索引"""
        self._service_rules[rule.service_name].append(rule.rule_id)
        metric_key = f"{rule.service_name}:{rule.metric_name}"
        self._metric_rules[metric_key].append(rule.rule_id)
        self._severity_rules[rule.severity].append(rule.rule_id)
        self._status_rules[rule.status].append(rule.rule_id)
    
    def _remove_from_indexes(self, rule: AlertRule):
        """从索引中移除"""
        if rule.rule_id in self._service_rules[rule.service_name]:
            self._service_rules[rule.service_name].remove(rule.rule_id)
        
        metric_key = f"{rule.service_name}:{rule.metric_name}"
        if rule.rule_id in self._metric_rules[metric_key]:
            self._metric_rules[metric_key].remove(rule.rule_id)
        
        if rule.rule_id in self._severity_rules[rule.severity]:
            self._severity_rules[rule.severity].remove(rule.rule_id)
        
        if rule.rule_id in self._status_rules[rule.status]:
            self._status_rules[rule.status].remove(rule.rule_id)
