"""
告警规则仓储接口
==============

定义告警规则数据的仓储操作接口
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..entities.alert_rule_entity import AlertRule, AlertSeverity, AlertStatus


class IAlertRuleRepository(ABC):
    """告警规则仓储接口"""
    
    @abstractmethod
    async def save_alert_rule(self, rule: AlertRule) -> bool:
        """
        保存告警规则
        
        Args:
            rule: 告警规则
            
        Returns:
            bool: 保存是否成功
        """
        pass
    
    @abstractmethod
    async def get_alert_rule(self, rule_id: str) -> Optional[AlertRule]:
        """
        获取告警规则
        
        Args:
            rule_id: 规则ID
            
        Returns:
            Optional[AlertRule]: 告警规则
        """
        pass
    
    @abstractmethod
    async def get_alert_rules_by_service(
        self, 
        service_name: str,
        status: Optional[AlertStatus] = None
    ) -> List[AlertRule]:
        """
        获取指定服务的告警规则
        
        Args:
            service_name: 服务名称
            status: 规则状态（可选）
            
        Returns:
            List[AlertRule]: 告警规则列表
        """
        pass
    
    @abstractmethod
    async def get_alert_rules_by_metric(
        self, 
        service_name: str,
        metric_name: str,
        status: Optional[AlertStatus] = None
    ) -> List[AlertRule]:
        """
        获取指定指标的告警规则
        
        Args:
            service_name: 服务名称
            metric_name: 指标名称
            status: 规则状态（可选）
            
        Returns:
            List[AlertRule]: 告警规则列表
        """
        pass
    
    @abstractmethod
    async def get_alert_rules_by_severity(
        self, 
        severity: AlertSeverity,
        status: Optional[AlertStatus] = None
    ) -> List[AlertRule]:
        """
        获取指定严重程度的告警规则
        
        Args:
            severity: 严重程度
            status: 规则状态（可选）
            
        Returns:
            List[AlertRule]: 告警规则列表
        """
        pass
    
    @abstractmethod
    async def get_active_alert_rules(self) -> List[AlertRule]:
        """
        获取所有激活的告警规则
        
        Returns:
            List[AlertRule]: 激活的告警规则列表
        """
        pass
    
    @abstractmethod
    async def update_alert_rule(self, rule: AlertRule) -> bool:
        """
        更新告警规则
        
        Args:
            rule: 告警规则
            
        Returns:
            bool: 更新是否成功
        """
        pass
    
    @abstractmethod
    async def delete_alert_rule(self, rule_id: str) -> bool:
        """
        删除告警规则
        
        Args:
            rule_id: 规则ID
            
        Returns:
            bool: 删除是否成功
        """
        pass
    
    @abstractmethod
    async def update_rule_last_triggered(
        self, 
        rule_id: str, 
        triggered_at: datetime
    ) -> bool:
        """
        更新规则最后触发时间
        
        Args:
            rule_id: 规则ID
            triggered_at: 触发时间
            
        Returns:
            bool: 更新是否成功
        """
        pass
    
    @abstractmethod
    async def enable_alert_rule(self, rule_id: str) -> bool:
        """
        启用告警规则
        
        Args:
            rule_id: 规则ID
            
        Returns:
            bool: 启用是否成功
        """
        pass
    
    @abstractmethod
    async def disable_alert_rule(self, rule_id: str) -> bool:
        """
        禁用告警规则
        
        Args:
            rule_id: 规则ID
            
        Returns:
            bool: 禁用是否成功
        """
        pass
    
    @abstractmethod
    async def search_alert_rules(
        self,
        query: str,
        status: Optional[AlertStatus] = None,
        severity: Optional[AlertSeverity] = None,
        limit: int = 100
    ) -> List[AlertRule]:
        """
        搜索告警规则
        
        Args:
            query: 搜索查询
            status: 规则状态（可选）
            severity: 严重程度（可选）
            limit: 结果数量限制
            
        Returns:
            List[AlertRule]: 搜索结果
        """
        pass
    
    @abstractmethod
    async def get_alert_rule_statistics(self) -> Dict[str, Any]:
        """
        获取告警规则统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        pass
