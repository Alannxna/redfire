"""
内存服务状态仓储实现
==================

基于内存的服务状态仓储实现
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import asyncio
from collections import defaultdict

from ....domain.monitoring.repositories.service_status_repository import IServiceStatusRepository
from ....domain.monitoring.entities.service_status_entity import ServiceStatus, ServiceHealth, ServiceType


class InMemoryServiceStatusRepository(IServiceStatusRepository):
    """内存服务状态仓储实现"""
    
    def __init__(self):
        self._services: Dict[str, ServiceStatus] = {}
        self._name_to_id: Dict[str, str] = {}
        self._health_services: Dict[ServiceHealth, List[str]] = defaultdict(list)
        self._type_services: Dict[ServiceType, List[str]] = defaultdict(list)
        self._lock = asyncio.Lock()
    
    async def save_service_status(self, status: ServiceStatus) -> bool:
        """保存服务状态"""
        async with self._lock:
            try:
                self._services[status.service_id] = status
                self._name_to_id[status.service_name] = status.service_id
                self._health_services[status.health_status].append(status.service_id)
                self._type_services[status.service_type].append(status.service_id)
                return True
            except Exception:
                return False
    
    async def get_service_status(self, service_id: str) -> Optional[ServiceStatus]:
        """获取服务状态"""
        return self._services.get(service_id)
    
    async def get_service_status_by_name(self, service_name: str) -> Optional[ServiceStatus]:
        """根据名称获取服务状态"""
        service_id = self._name_to_id.get(service_name)
        if service_id:
            return self._services.get(service_id)
        return None
    
    async def get_all_service_statuses(self) -> List[ServiceStatus]:
        """获取所有服务状态"""
        return list(self._services.values())
    
    async def get_services_by_health(self, health: ServiceHealth) -> List[ServiceStatus]:
        """根据健康状态获取服务"""
        service_ids = self._health_services.get(health, [])
        return [self._services[sid] for sid in service_ids if sid in self._services]
    
    async def get_services_by_type(self, service_type: ServiceType) -> List[ServiceStatus]:
        """根据服务类型获取服务"""
        service_ids = self._type_services.get(service_type, [])
        return [self._services[sid] for sid in service_ids if sid in self._services]
    
    async def update_service_status(self, status: ServiceStatus) -> bool:
        """更新服务状态"""
        async with self._lock:
            if status.service_id not in self._services:
                return False
            
            # 先从旧的索引中移除
            old_status = self._services[status.service_id]
            self._remove_from_indexes(old_status)
            
            # 更新状态
            status.last_check_time = datetime.now()
            self._services[status.service_id] = status
            
            # 重新添加到索引
            self._add_to_indexes(status)
            
            return True
    
    async def update_service_health(
        self, 
        service_id: str, 
        health: ServiceHealth,
        message: Optional[str] = None
    ) -> bool:
        """更新服务健康状态"""
        async with self._lock:
            if service_id not in self._services:
                return False
            
            service = self._services[service_id]
            
            # 从旧的健康状态索引中移除
            if service_id in self._health_services[service.health_status]:
                self._health_services[service.health_status].remove(service_id)
            
            # 更新健康状态
            service.health_status = health
            service.last_check_time = datetime.now()
            if message:
                service.status_message = message
            
            # 添加到新的健康状态索引
            self._health_services[health].append(service_id)
            
            return True
    
    async def update_service_metrics(
        self, 
        service_id: str, 
        metrics: Dict[str, Any]
    ) -> bool:
        """更新服务指标"""
        if service_id not in self._services:
            return False
        
        service = self._services[service_id]
        
        # 更新性能指标
        if "response_time_ms" in metrics:
            service.response_time_ms = metrics["response_time_ms"]
        if "cpu_usage_percent" in metrics:
            service.cpu_usage_percent = metrics["cpu_usage_percent"]
        if "memory_usage_percent" in metrics:
            service.memory_usage_percent = metrics["memory_usage_percent"]
        if "active_connections" in metrics:
            service.active_connections = metrics["active_connections"]
        
        service.last_check_time = datetime.now()
        return True
    
    async def increment_request_count(
        self, 
        service_id: str, 
        success: bool = True
    ) -> bool:
        """增加请求计数"""
        if service_id not in self._services:
            return False
        
        service = self._services[service_id]
        service.total_requests += 1
        
        if success:
            service.successful_requests += 1
        else:
            service.failed_requests += 1
            service.last_error_time = datetime.now()
        
        return True
    
    async def record_service_error(
        self, 
        service_id: str, 
        error_message: str,
        error_time: Optional[datetime] = None
    ) -> bool:
        """记录服务错误"""
        if service_id not in self._services:
            return False
        
        service = self._services[service_id]
        service.error_message = error_message
        service.last_error_time = error_time or datetime.now()
        service.failed_requests += 1
        
        return True
    
    async def delete_service_status(self, service_id: str) -> bool:
        """删除服务状态"""
        async with self._lock:
            if service_id not in self._services:
                return False
            
            service = self._services.pop(service_id)
            self._remove_from_indexes(service)
            
            # 从名称映射中移除
            if service.service_name in self._name_to_id:
                del self._name_to_id[service.service_name]
            
            return True
    
    async def get_service_dependencies(self, service_id: str) -> List[str]:
        """获取服务依赖"""
        service = self._services.get(service_id)
        return service.dependencies if service else []
    
    async def get_service_dependents(self, service_id: str) -> List[str]:
        """获取依赖此服务的服务"""
        service = self._services.get(service_id)
        return service.dependents if service else []
    
    async def search_services(
        self,
        query: str,
        health: Optional[ServiceHealth] = None,
        service_type: Optional[ServiceType] = None,
        limit: int = 100
    ) -> List[ServiceStatus]:
        """搜索服务"""
        results = []
        count = 0
        
        for service in self._services.values():
            if count >= limit:
                break
            
            # 查询匹配
            if (query.lower() in service.service_name.lower() or
                query.lower() in service.service_id.lower() or
                any(query.lower() in tag.lower() for tag in service.tags)):
                
                # 健康状态过滤
                if health and service.health_status != health:
                    continue
                
                # 服务类型过滤
                if service_type and service.service_type != service_type:
                    continue
                
                results.append(service)
                count += 1
        
        return results
    
    async def get_service_statistics(self) -> Dict[str, Any]:
        """获取服务统计信息"""
        total_services = len(self._services)
        health_counts = defaultdict(int)
        type_counts = defaultdict(int)
        
        total_requests = 0
        total_successful = 0
        total_failed = 0
        
        for service in self._services.values():
            health_counts[service.health_status.value] += 1
            type_counts[service.service_type.value] += 1
            total_requests += service.total_requests
            total_successful += service.successful_requests
            total_failed += service.failed_requests
        
        overall_success_rate = (total_successful / total_requests * 100) if total_requests > 0 else 100
        
        return {
            "total_services": total_services,
            "health_breakdown": dict(health_counts),
            "type_breakdown": dict(type_counts),
            "healthy_services": health_counts.get("healthy", 0),
            "unhealthy_services": health_counts.get("unhealthy", 0),
            "degraded_services": health_counts.get("degraded", 0),
            "total_requests": total_requests,
            "total_successful_requests": total_successful,
            "total_failed_requests": total_failed,
            "overall_success_rate": overall_success_rate,
            "overall_error_rate": 100 - overall_success_rate
        }
    
    def _add_to_indexes(self, service: ServiceStatus):
        """添加到索引"""
        self._name_to_id[service.service_name] = service.service_id
        self._health_services[service.health_status].append(service.service_id)
        self._type_services[service.service_type].append(service.service_id)
    
    def _remove_from_indexes(self, service: ServiceStatus):
        """从索引中移除"""
        if service.service_id in self._health_services[service.health_status]:
            self._health_services[service.health_status].remove(service.service_id)
        
        if service.service_id in self._type_services[service.service_type]:
            self._type_services[service.service_type].remove(service.service_id)
