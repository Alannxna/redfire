"""
系统指标仓储接口
==============

定义系统指标数据的仓储操作接口
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Union
from datetime import datetime

from ..entities.system_metrics_entity import SystemMetrics, MetricType


class ISystemMetricsRepository(ABC):
    """系统指标仓储接口"""
    
    @abstractmethod
    async def save_metric(self, metric: SystemMetrics) -> bool:
        """
        保存系统指标
        
        Args:
            metric: 系统指标
            
        Returns:
            bool: 保存是否成功
        """
        pass
    
    @abstractmethod
    async def save_metrics_batch(self, metrics: List[SystemMetrics]) -> bool:
        """
        批量保存系统指标
        
        Args:
            metrics: 系统指标列表
            
        Returns:
            bool: 保存是否成功
        """
        pass
    
    @abstractmethod
    async def get_metric(self, metric_id: str) -> Optional[SystemMetrics]:
        """
        获取系统指标
        
        Args:
            metric_id: 指标ID
            
        Returns:
            Optional[SystemMetrics]: 系统指标
        """
        pass
    
    @abstractmethod
    async def get_metrics_by_service(
        self, 
        service_name: str,
        metric_name: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 1000
    ) -> List[SystemMetrics]:
        """
        获取指定服务的系统指标
        
        Args:
            service_name: 服务名称
            metric_name: 指标名称（可选）
            start_time: 开始时间（可选）
            end_time: 结束时间（可选）
            limit: 结果数量限制
            
        Returns:
            List[SystemMetrics]: 系统指标列表
        """
        pass
    
    @abstractmethod
    async def get_metrics_by_type(
        self, 
        metric_type: MetricType,
        service_name: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 1000
    ) -> List[SystemMetrics]:
        """
        获取指定类型的系统指标
        
        Args:
            metric_type: 指标类型
            service_name: 服务名称（可选）
            start_time: 开始时间（可选）
            end_time: 结束时间（可选）
            limit: 结果数量限制
            
        Returns:
            List[SystemMetrics]: 系统指标列表
        """
        pass
    
    @abstractmethod
    async def get_latest_metrics(
        self,
        service_name: Optional[str] = None,
        metric_name: Optional[str] = None
    ) -> List[SystemMetrics]:
        """
        获取最新的系统指标
        
        Args:
            service_name: 服务名称（可选）
            metric_name: 指标名称（可选）
            
        Returns:
            List[SystemMetrics]: 最新的系统指标列表
        """
        pass
    
    @abstractmethod
    async def get_metrics_aggregated(
        self,
        service_name: str,
        metric_name: str,
        start_time: datetime,
        end_time: datetime,
        aggregation_window: str = "1m"  # 1m, 5m, 1h, 1d
    ) -> List[Dict[str, Any]]:
        """
        获取聚合的系统指标
        
        Args:
            service_name: 服务名称
            metric_name: 指标名称
            start_time: 开始时间
            end_time: 结束时间
            aggregation_window: 聚合窗口
            
        Returns:
            List[Dict[str, Any]]: 聚合指标数据
        """
        pass
    
    @abstractmethod
    async def get_metric_statistics(
        self,
        service_name: str,
        metric_name: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        获取指标统计信息
        
        Args:
            service_name: 服务名称
            metric_name: 指标名称
            start_time: 开始时间（可选）
            end_time: 结束时间（可选）
            
        Returns:
            Dict[str, Any]: 统计信息
        """
        pass
    
    @abstractmethod
    async def delete_old_metrics(
        self,
        before_time: datetime,
        service_name: Optional[str] = None
    ) -> int:
        """
        删除指定时间之前的指标数据
        
        Args:
            before_time: 时间阈值
            service_name: 服务名称（可选）
            
        Returns:
            int: 删除的记录数
        """
        pass
    
    @abstractmethod
    async def get_metric_values_range(
        self,
        service_name: str,
        metric_name: str,
        start_time: datetime,
        end_time: datetime
    ) -> Dict[str, Union[float, int]]:
        """
        获取指标值的范围信息
        
        Args:
            service_name: 服务名称
            metric_name: 指标名称
            start_time: 开始时间
            end_time: 结束时间
            
        Returns:
            Dict[str, Union[float, int]]: 范围信息（min, max, avg）
        """
        pass
    
    @abstractmethod
    async def search_metrics(
        self,
        query: str,
        labels: Optional[Dict[str, str]] = None,
        limit: int = 100
    ) -> List[SystemMetrics]:
        """
        搜索系统指标
        
        Args:
            query: 搜索查询
            labels: 标签过滤（可选）
            limit: 结果数量限制
            
        Returns:
            List[SystemMetrics]: 搜索结果
        """
        pass
