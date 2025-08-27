"""
健康检查仓储接口
==============

定义健康检查数据的仓储操作接口
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..entities.health_check_entity import HealthCheckResult, HealthStatus


class IHealthCheckRepository(ABC):
    """健康检查仓储接口"""
    
    @abstractmethod
    async def save_health_check_result(self, result: HealthCheckResult) -> bool:
        """
        保存健康检查结果
        
        Args:
            result: 健康检查结果
            
        Returns:
            bool: 保存是否成功
        """
        pass
    
    @abstractmethod
    async def get_health_check_result(self, check_id: str) -> Optional[HealthCheckResult]:
        """
        获取健康检查结果
        
        Args:
            check_id: 检查ID
            
        Returns:
            Optional[HealthCheckResult]: 健康检查结果
        """
        pass
    
    @abstractmethod
    async def get_health_check_results_by_service(
        self, 
        service_name: str,
        limit: int = 100
    ) -> List[HealthCheckResult]:
        """
        获取指定服务的健康检查结果
        
        Args:
            service_name: 服务名称
            limit: 结果数量限制
            
        Returns:
            List[HealthCheckResult]: 健康检查结果列表
        """
        pass
    
    @abstractmethod
    async def get_health_check_results_by_component(
        self, 
        service_name: str,
        component_name: str,
        limit: int = 100
    ) -> List[HealthCheckResult]:
        """
        获取指定组件的健康检查结果
        
        Args:
            service_name: 服务名称
            component_name: 组件名称
            limit: 结果数量限制
            
        Returns:
            List[HealthCheckResult]: 健康检查结果列表
        """
        pass
    
    @abstractmethod
    async def get_health_check_results_by_status(
        self, 
        status: HealthStatus,
        limit: int = 100
    ) -> List[HealthCheckResult]:
        """
        获取指定状态的健康检查结果
        
        Args:
            status: 健康状态
            limit: 结果数量限制
            
        Returns:
            List[HealthCheckResult]: 健康检查结果列表
        """
        pass
    
    @abstractmethod
    async def get_health_check_results_by_time_range(
        self,
        start_time: datetime,
        end_time: datetime,
        service_name: Optional[str] = None,
        component_name: Optional[str] = None
    ) -> List[HealthCheckResult]:
        """
        获取指定时间范围的健康检查结果
        
        Args:
            start_time: 开始时间
            end_time: 结束时间
            service_name: 服务名称（可选）
            component_name: 组件名称（可选）
            
        Returns:
            List[HealthCheckResult]: 健康检查结果列表
        """
        pass
    
    @abstractmethod
    async def get_latest_health_check_results(
        self,
        service_name: Optional[str] = None
    ) -> List[HealthCheckResult]:
        """
        获取最新的健康检查结果
        
        Args:
            service_name: 服务名称（可选）
            
        Returns:
            List[HealthCheckResult]: 最新的健康检查结果列表
        """
        pass
    
    @abstractmethod
    async def delete_old_health_check_results(
        self,
        before_time: datetime
    ) -> int:
        """
        删除指定时间之前的健康检查结果
        
        Args:
            before_time: 时间阈值
            
        Returns:
            int: 删除的记录数
        """
        pass
    
    @abstractmethod
    async def get_health_check_statistics(
        self,
        service_name: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        获取健康检查统计信息
        
        Args:
            service_name: 服务名称（可选）
            start_time: 开始时间（可选）
            end_time: 结束时间（可选）
            
        Returns:
            Dict[str, Any]: 统计信息
        """
        pass
