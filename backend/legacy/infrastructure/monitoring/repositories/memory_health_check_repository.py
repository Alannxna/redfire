"""
内存健康检查仓储实现
==================

基于内存的健康检查仓储实现
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import asyncio
from collections import defaultdict

from ....domain.monitoring.repositories.health_check_repository import IHealthCheckRepository
from ....domain.monitoring.entities.health_check_entity import HealthCheckResult, HealthStatus


class InMemoryHealthCheckRepository(IHealthCheckRepository):
    """
    内存健康检查仓储实现
    
    基于内存存储的健康检查仓储，适用于开发和测试环境
    """
    
    def __init__(self):
        self._health_checks: Dict[str, HealthCheckResult] = {}
        self._service_checks: Dict[str, List[str]] = defaultdict(list)
        self._component_checks: Dict[str, List[str]] = defaultdict(list)
        self._status_checks: Dict[HealthStatus, List[str]] = defaultdict(list)
        self._lock = asyncio.Lock()
    
    async def save_health_check_result(self, result: HealthCheckResult) -> bool:
        """保存健康检查结果"""
        async with self._lock:
            try:
                self._health_checks[result.check_id] = result
                
                # 更新索引
                self._service_checks[result.service_name].append(result.check_id)
                component_key = f"{result.service_name}:{result.component_name}"
                self._component_checks[component_key].append(result.check_id)
                self._status_checks[result.status].append(result.check_id)
                
                # 限制每个服务保存的检查记录数量
                max_records_per_service = 1000
                if len(self._service_checks[result.service_name]) > max_records_per_service:
                    # 移除最旧的记录
                    oldest_id = self._service_checks[result.service_name].pop(0)
                    if oldest_id in self._health_checks:
                        old_result = self._health_checks.pop(oldest_id)
                        # 从其他索引中移除
                        self._remove_from_indexes(old_result)
                
                return True
                
            except Exception:
                return False
    
    async def get_health_check_result(self, check_id: str) -> Optional[HealthCheckResult]:
        """获取健康检查结果"""
        return self._health_checks.get(check_id)
    
    async def get_health_check_results_by_service(
        self, 
        service_name: str,
        limit: int = 100
    ) -> List[HealthCheckResult]:
        """获取指定服务的健康检查结果"""
        check_ids = self._service_checks.get(service_name, [])
        results = []
        
        for check_id in reversed(check_ids[-limit:]):  # 最新的记录在前
            if check_id in self._health_checks:
                results.append(self._health_checks[check_id])
        
        return results
    
    async def get_health_check_results_by_component(
        self, 
        service_name: str,
        component_name: str,
        limit: int = 100
    ) -> List[HealthCheckResult]:
        """获取指定组件的健康检查结果"""
        component_key = f"{service_name}:{component_name}"
        check_ids = self._component_checks.get(component_key, [])
        results = []
        
        for check_id in reversed(check_ids[-limit:]):  # 最新的记录在前
            if check_id in self._health_checks:
                results.append(self._health_checks[check_id])
        
        return results
    
    async def get_health_check_results_by_status(
        self, 
        status: HealthStatus,
        limit: int = 100
    ) -> List[HealthCheckResult]:
        """获取指定状态的健康检查结果"""
        check_ids = self._status_checks.get(status, [])
        results = []
        
        for check_id in reversed(check_ids[-limit:]):  # 最新的记录在前
            if check_id in self._health_checks:
                results.append(self._health_checks[check_id])
        
        return results
    
    async def get_health_check_results_by_time_range(
        self,
        start_time: datetime,
        end_time: datetime,
        service_name: Optional[str] = None,
        component_name: Optional[str] = None
    ) -> List[HealthCheckResult]:
        """获取指定时间范围的健康检查结果"""
        results = []
        
        for result in self._health_checks.values():
            # 时间范围过滤
            if not (start_time <= result.timestamp <= end_time):
                continue
            
            # 服务名称过滤
            if service_name and result.service_name != service_name:
                continue
            
            # 组件名称过滤
            if component_name and result.component_name != component_name:
                continue
            
            results.append(result)
        
        # 按时间排序
        results.sort(key=lambda x: x.timestamp, reverse=True)
        return results
    
    async def get_latest_health_check_results(
        self,
        service_name: Optional[str] = None
    ) -> List[HealthCheckResult]:
        """获取最新的健康检查结果"""
        if service_name:
            # 获取指定服务的最新结果
            service_results = await self.get_health_check_results_by_service(service_name, limit=50)
            
            # 按组件分组，每个组件只保留最新的结果
            latest_by_component = {}
            for result in service_results:
                component_key = f"{result.service_name}:{result.component_name}"
                if (component_key not in latest_by_component or 
                    result.timestamp > latest_by_component[component_key].timestamp):
                    latest_by_component[component_key] = result
            
            return list(latest_by_component.values())
        else:
            # 获取所有服务的最新结果
            latest_by_service_component = {}
            
            for result in self._health_checks.values():
                component_key = f"{result.service_name}:{result.component_name}"
                if (component_key not in latest_by_service_component or 
                    result.timestamp > latest_by_service_component[component_key].timestamp):
                    latest_by_service_component[component_key] = result
            
            return list(latest_by_service_component.values())
    
    async def delete_old_health_check_results(
        self,
        before_time: datetime
    ) -> int:
        """删除指定时间之前的健康检查结果"""
        async with self._lock:
            deleted_count = 0
            to_delete = []
            
            for check_id, result in self._health_checks.items():
                if result.timestamp < before_time:
                    to_delete.append((check_id, result))
            
            for check_id, result in to_delete:
                self._health_checks.pop(check_id)
                self._remove_from_indexes(result)
                deleted_count += 1
            
            return deleted_count
    
    async def get_health_check_statistics(
        self,
        service_name: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """获取健康检查统计信息"""
        results = []
        
        if start_time and end_time:
            results = await self.get_health_check_results_by_time_range(
                start_time, end_time, service_name
            )
        elif service_name:
            results = await self.get_health_check_results_by_service(service_name)
        else:
            results = list(self._health_checks.values())
        
        if not results:
            return {
                "total_checks": 0,
                "status_breakdown": {},
                "service_breakdown": {},
                "component_breakdown": {},
                "avg_response_time_ms": 0,
                "time_range": {
                    "start": start_time.isoformat() if start_time else None,
                    "end": end_time.isoformat() if end_time else None
                }
            }
        
        # 状态统计
        status_counts = defaultdict(int)
        service_counts = defaultdict(int)
        component_counts = defaultdict(int)
        response_times = []
        
        for result in results:
            status_counts[result.status.value] += 1
            service_counts[result.service_name] += 1
            component_counts[f"{result.service_name}:{result.component_name}"] += 1
            response_times.append(result.response_time_ms)
        
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        return {
            "total_checks": len(results),
            "status_breakdown": dict(status_counts),
            "service_breakdown": dict(service_counts),
            "component_breakdown": dict(component_counts),
            "avg_response_time_ms": avg_response_time,
            "time_range": {
                "start": start_time.isoformat() if start_time else None,
                "end": end_time.isoformat() if end_time else None
            }
        }
    
    def _remove_from_indexes(self, result: HealthCheckResult):
        """从索引中移除结果"""
        # 从服务索引中移除
        if result.check_id in self._service_checks[result.service_name]:
            self._service_checks[result.service_name].remove(result.check_id)
        
        # 从组件索引中移除
        component_key = f"{result.service_name}:{result.component_name}"
        if result.check_id in self._component_checks[component_key]:
            self._component_checks[component_key].remove(result.check_id)
        
        # 从状态索引中移除
        if result.check_id in self._status_checks[result.status]:
            self._status_checks[result.status].remove(result.check_id)
