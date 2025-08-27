"""
策略仓储接口
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime

from src.domain.strategy.entities.strategy_entity import (
    StrategyInstance, StrategyConfiguration, RiskEvent, StrategyStatus, StrategyType
)


class StrategyInstanceRepository(ABC):
    """策略实例仓储接口"""
    
    @abstractmethod
    async def save(self, instance: StrategyInstance) -> StrategyInstance:
        """保存策略实例"""
        pass
    
    @abstractmethod
    async def update(self, instance: StrategyInstance) -> StrategyInstance:
        """更新策略实例"""
        pass
    
    @abstractmethod
    async def find_by_id(self, instance_id: str) -> Optional[StrategyInstance]:
        """根据ID查找策略实例"""
        pass
    
    @abstractmethod
    async def find_by_strategy_name(self, strategy_name: str) -> List[StrategyInstance]:
        """根据策略名称查找实例"""
        pass
    
    @abstractmethod
    async def find_by_status(self, status: StrategyStatus) -> List[StrategyInstance]:
        """根据状态查找策略实例"""
        pass
    
    @abstractmethod
    async def find_by_type(self, strategy_type: StrategyType) -> List[StrategyInstance]:
        """根据类型查找策略实例"""
        pass
    
    @abstractmethod
    async def find_all(self, limit: int = 100, offset: int = 0) -> List[StrategyInstance]:
        """查找所有策略实例"""
        pass
    
    @abstractmethod
    async def find_running_instances(self) -> List[StrategyInstance]:
        """查找所有运行中的策略实例"""
        pass
    
    @abstractmethod
    async def delete(self, instance_id: str) -> bool:
        """删除策略实例"""
        pass
    
    @abstractmethod
    async def get_instance_statistics(self) -> Dict[str, Any]:
        """获取策略实例统计信息"""
        pass


class StrategyConfigurationRepository(ABC):
    """策略配置仓储接口"""
    
    @abstractmethod
    async def save(self, config: StrategyConfiguration) -> StrategyConfiguration:
        """保存策略配置"""
        pass
    
    @abstractmethod
    async def update(self, config: StrategyConfiguration) -> StrategyConfiguration:
        """更新策略配置"""
        pass
    
    @abstractmethod
    async def find_by_name(self, strategy_name: str) -> Optional[StrategyConfiguration]:
        """根据名称查找策略配置"""
        pass
    
    @abstractmethod
    async def find_by_type(self, strategy_type: StrategyType) -> List[StrategyConfiguration]:
        """根据类型查找策略配置"""
        pass
    
    @abstractmethod
    async def find_auto_start_configs(self) -> List[StrategyConfiguration]:
        """查找自动启动的策略配置"""
        pass
    
    @abstractmethod
    async def find_all(self, limit: int = 100, offset: int = 0) -> List[StrategyConfiguration]:
        """查找所有策略配置"""
        pass
    
    @abstractmethod
    async def delete(self, strategy_name: str) -> bool:
        """删除策略配置"""
        pass
    
    @abstractmethod
    async def get_config_statistics(self) -> Dict[str, Any]:
        """获取策略配置统计信息"""
        pass


class RiskEventRepository(ABC):
    """风险事件仓储接口"""
    
    @abstractmethod
    async def save(self, event: RiskEvent) -> RiskEvent:
        """保存风险事件"""
        pass
    
    @abstractmethod
    async def find_by_instance_id(self, instance_id: str) -> List[RiskEvent]:
        """根据策略实例ID查找风险事件"""
        pass
    
    @abstractmethod
    async def find_by_strategy_name(self, strategy_name: str) -> List[RiskEvent]:
        """根据策略名称查找风险事件"""
        pass
    
    @abstractmethod
    async def find_by_severity(self, severity: str) -> List[RiskEvent]:
        """根据严重级别查找风险事件"""
        pass
    
    @abstractmethod
    async def find_unresolved_events(self) -> List[RiskEvent]:
        """查找未解决的风险事件"""
        pass
    
    @abstractmethod
    async def find_recent_events(self, hours: int = 24) -> List[RiskEvent]:
        """查找最近的风险事件"""
        pass
    
    @abstractmethod
    async def mark_resolved(self, event_id: str) -> bool:
        """标记风险事件为已解决"""
        pass
    
    @abstractmethod
    async def cleanup_old_events(self, days: int = 30) -> int:
        """清理旧的风险事件"""
        pass
    
    @abstractmethod
    async def get_event_statistics(self) -> Dict[str, Any]:
        """获取风险事件统计信息"""
        pass
