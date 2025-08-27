"""
服务状态仓储接口
==============

定义服务状态数据的仓储操作接口
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..entities.service_status_entity import ServiceStatus, ServiceHealth, ServiceType


class IServiceStatusRepository(ABC):
    """服务状态仓储接口"""
    
    @abstractmethod
    async def save_service_status(self, status: ServiceStatus) -> bool:
        """
        保存服务状态
        
        Args:
            status: 服务状态
            
        Returns:
            bool: 保存是否成功
        """
        pass
    
    @abstractmethod
    async def get_service_status(self, service_id: str) -> Optional[ServiceStatus]:
        """
        获取服务状态
        
        Args:
            service_id: 服务ID
            
        Returns:
            Optional[ServiceStatus]: 服务状态
        """
        pass
    
    @abstractmethod
    async def get_service_status_by_name(self, service_name: str) -> Optional[ServiceStatus]:
        """
        根据名称获取服务状态
        
        Args:
            service_name: 服务名称
            
        Returns:
            Optional[ServiceStatus]: 服务状态
        """
        pass
    
    @abstractmethod
    async def get_all_service_statuses(self) -> List[ServiceStatus]:
        """
        获取所有服务状态
        
        Returns:
            List[ServiceStatus]: 服务状态列表
        """
        pass
    
    @abstractmethod
    async def get_services_by_health(self, health: ServiceHealth) -> List[ServiceStatus]:
        """
        根据健康状态获取服务
        
        Args:
            health: 健康状态
            
        Returns:
            List[ServiceStatus]: 服务状态列表
        """
        pass
    
    @abstractmethod
    async def get_services_by_type(self, service_type: ServiceType) -> List[ServiceStatus]:
        """
        根据服务类型获取服务
        
        Args:
            service_type: 服务类型
            
        Returns:
            List[ServiceStatus]: 服务状态列表
        """
        pass
    
    @abstractmethod
    async def update_service_status(self, status: ServiceStatus) -> bool:
        """
        更新服务状态
        
        Args:
            status: 服务状态
            
        Returns:
            bool: 更新是否成功
        """
        pass
    
    @abstractmethod
    async def update_service_health(
        self, 
        service_id: str, 
        health: ServiceHealth,
        message: Optional[str] = None
    ) -> bool:
        """
        更新服务健康状态
        
        Args:
            service_id: 服务ID
            health: 健康状态
            message: 状态消息（可选）
            
        Returns:
            bool: 更新是否成功
        """
        pass
    
    @abstractmethod
    async def update_service_metrics(
        self, 
        service_id: str, 
        metrics: Dict[str, Any]
    ) -> bool:
        """
        更新服务指标
        
        Args:
            service_id: 服务ID
            metrics: 指标数据
            
        Returns:
            bool: 更新是否成功
        """
        pass
    
    @abstractmethod
    async def increment_request_count(
        self, 
        service_id: str, 
        success: bool = True
    ) -> bool:
        """
        增加请求计数
        
        Args:
            service_id: 服务ID
            success: 是否成功
            
        Returns:
            bool: 更新是否成功
        """
        pass
    
    @abstractmethod
    async def record_service_error(
        self, 
        service_id: str, 
        error_message: str,
        error_time: Optional[datetime] = None
    ) -> bool:
        """
        记录服务错误
        
        Args:
            service_id: 服务ID
            error_message: 错误消息
            error_time: 错误时间（可选）
            
        Returns:
            bool: 记录是否成功
        """
        pass
    
    @abstractmethod
    async def delete_service_status(self, service_id: str) -> bool:
        """
        删除服务状态
        
        Args:
            service_id: 服务ID
            
        Returns:
            bool: 删除是否成功
        """
        pass
    
    @abstractmethod
    async def get_service_dependencies(self, service_id: str) -> List[str]:
        """
        获取服务依赖
        
        Args:
            service_id: 服务ID
            
        Returns:
            List[str]: 依赖的服务ID列表
        """
        pass
    
    @abstractmethod
    async def get_service_dependents(self, service_id: str) -> List[str]:
        """
        获取依赖此服务的服务
        
        Args:
            service_id: 服务ID
            
        Returns:
            List[str]: 依赖此服务的服务ID列表
        """
        pass
    
    @abstractmethod
    async def search_services(
        self,
        query: str,
        health: Optional[ServiceHealth] = None,
        service_type: Optional[ServiceType] = None,
        limit: int = 100
    ) -> List[ServiceStatus]:
        """
        搜索服务
        
        Args:
            query: 搜索查询
            health: 健康状态（可选）
            service_type: 服务类型（可选）
            limit: 结果数量限制
            
        Returns:
            List[ServiceStatus]: 搜索结果
        """
        pass
    
    @abstractmethod
    async def get_service_statistics(self) -> Dict[str, Any]:
        """
        获取服务统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        pass
