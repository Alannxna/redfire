"""
健康检查服务
==========

负责执行系统健康检查的具体实现
"""

import asyncio
import time
import psutil
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid

from ....core.common.exceptions import DomainException
from ..entities.health_check_entity import HealthCheckResult, HealthStatus
from ..entities.service_status_entity import ServiceHealth
from ..repositories.health_check_repository import IHealthCheckRepository
from ..repositories.service_status_repository import IServiceStatusRepository


class HealthCheckService:
    """
    健康检查服务
    
    负责执行各种类型的健康检查，包括：
    - 服务状态检查
    - 系统资源检查
    - 依赖服务检查
    - 数据库连接检查
    """
    
    def __init__(
        self,
        health_check_repository: IHealthCheckRepository,
        service_status_repository: IServiceStatusRepository
    ):
        self._health_check_repo = health_check_repository
        self._service_status_repo = service_status_repository
        
        # 健康检查配置
        self._timeout_seconds = 30
        self._critical_cpu_threshold = 90.0
        self._critical_memory_threshold = 90.0
        self._critical_disk_threshold = 95.0
    
    async def perform_system_health_check(self, service_name: str = "system") -> HealthCheckResult:
        """
        执行系统健康检查
        
        Args:
            service_name: 服务名称
            
        Returns:
            HealthCheckResult: 健康检查结果
        """
        check_id = str(uuid.uuid4())
        start_time = time.time()
        
        try:
            # 检查系统资源
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # 判断健康状态
            status = HealthStatus.HEALTHY
            messages = []
            
            if cpu_percent > self._critical_cpu_threshold:
                status = HealthStatus.UNHEALTHY
                messages.append(f"CPU使用率过高: {cpu_percent:.1f}%")
            elif cpu_percent > 70:
                status = HealthStatus.DEGRADED
                messages.append(f"CPU使用率较高: {cpu_percent:.1f}%")
            
            if memory.percent > self._critical_memory_threshold:
                status = HealthStatus.UNHEALTHY if status != HealthStatus.UNHEALTHY else status
                messages.append(f"内存使用率过高: {memory.percent:.1f}%")
            elif memory.percent > 80:
                status = HealthStatus.DEGRADED if status == HealthStatus.HEALTHY else status
                messages.append(f"内存使用率较高: {memory.percent:.1f}%")
            
            if disk.percent > self._critical_disk_threshold:
                status = HealthStatus.UNHEALTHY if status != HealthStatus.UNHEALTHY else status
                messages.append(f"磁盘使用率过高: {disk.percent:.1f}%")
            elif disk.percent > 85:
                status = HealthStatus.DEGRADED if status == HealthStatus.HEALTHY else status
                messages.append(f"磁盘使用率较高: {disk.percent:.1f}%")
            
            response_time = (time.time() - start_time) * 1000
            
            result = HealthCheckResult(
                check_id=check_id,
                service_name=service_name,
                component_name="system_resources",
                status=status,
                response_time_ms=response_time,
                message="; ".join(messages) if messages else "系统资源正常",
                metadata={
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "memory_available_gb": memory.available / (1024**3),
                    "disk_percent": disk.percent,
                    "disk_free_gb": disk.free / (1024**3),
                }
            )
            
            # 保存结果
            await self._health_check_repo.save_health_check_result(result)
            
            return result
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            
            result = HealthCheckResult(
                check_id=check_id,
                service_name=service_name,
                component_name="system_resources",
                status=HealthStatus.UNHEALTHY,
                response_time_ms=response_time,
                message="系统健康检查失败",
                error_details=str(e)
            )
            
            await self._health_check_repo.save_health_check_result(result)
            return result
    
    async def perform_service_health_check(self, service_name: str) -> HealthCheckResult:
        """
        执行服务健康检查
        
        Args:
            service_name: 服务名称
            
        Returns:
            HealthCheckResult: 健康检查结果
        """
        check_id = str(uuid.uuid4())
        start_time = time.time()
        
        try:
            # 获取服务状态
            service_status = await self._service_status_repo.get_service_status_by_name(service_name)
            
            if not service_status:
                response_time = (time.time() - start_time) * 1000
                
                result = HealthCheckResult(
                    check_id=check_id,
                    service_name=service_name,
                    component_name="service_status",
                    status=HealthStatus.UNKNOWN,
                    response_time_ms=response_time,
                    message="服务未注册",
                    error_details=f"服务 {service_name} 未在服务注册表中找到"
                )
                
                await self._health_check_repo.save_health_check_result(result)
                return result
            
            # 转换服务健康状态到检查状态
            status_mapping = {
                ServiceHealth.HEALTHY: HealthStatus.HEALTHY,
                ServiceHealth.DEGRADED: HealthStatus.DEGRADED,
                ServiceHealth.UNHEALTHY: HealthStatus.UNHEALTHY,
                ServiceHealth.MAINTENANCE: HealthStatus.DEGRADED,
                ServiceHealth.UNKNOWN: HealthStatus.UNKNOWN,
            }
            
            response_time = (time.time() - start_time) * 1000
            
            result = HealthCheckResult(
                check_id=check_id,
                service_name=service_name,
                component_name="service_status",
                status=status_mapping.get(service_status.health_status, HealthStatus.UNKNOWN),
                response_time_ms=response_time,
                message=service_status.status_message or f"服务状态: {service_status.health_status.value}",
                error_details=service_status.error_message,
                metadata={
                    "service_type": service_status.service_type.value,
                    "version": service_status.version,
                    "uptime_seconds": service_status.uptime_seconds,
                    "last_check_time": service_status.last_check_time.isoformat(),
                    "cpu_usage_percent": service_status.cpu_usage_percent,
                    "memory_usage_percent": service_status.memory_usage_percent,
                    "active_connections": service_status.active_connections,
                    "success_rate": service_status.get_success_rate(),
                    "error_rate": service_status.get_error_rate(),
                },
                dependencies=service_status.dependencies
            )
            
            await self._health_check_repo.save_health_check_result(result)
            return result
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            
            result = HealthCheckResult(
                check_id=check_id,
                service_name=service_name,
                component_name="service_status",
                status=HealthStatus.UNHEALTHY,
                response_time_ms=response_time,
                message="服务健康检查失败",
                error_details=str(e)
            )
            
            await self._health_check_repo.save_health_check_result(result)
            return result
    
    async def perform_dependency_health_check(
        self, 
        service_name: str, 
        dependencies: List[str]
    ) -> HealthCheckResult:
        """
        执行依赖服务健康检查
        
        Args:
            service_name: 服务名称
            dependencies: 依赖的服务列表
            
        Returns:
            HealthCheckResult: 健康检查结果
        """
        check_id = str(uuid.uuid4())
        start_time = time.time()
        
        try:
            dependency_results = []
            overall_status = HealthStatus.HEALTHY
            
            for dep_service in dependencies:
                dep_result = await self.perform_service_health_check(dep_service)
                dependency_results.append({
                    "service": dep_service,
                    "status": dep_result.status.value,
                    "message": dep_result.message,
                    "response_time_ms": dep_result.response_time_ms
                })
                
                # 更新整体状态
                if dep_result.status == HealthStatus.UNHEALTHY:
                    overall_status = HealthStatus.UNHEALTHY
                elif dep_result.status == HealthStatus.DEGRADED and overall_status == HealthStatus.HEALTHY:
                    overall_status = HealthStatus.DEGRADED
                elif dep_result.status == HealthStatus.UNKNOWN and overall_status == HealthStatus.HEALTHY:
                    overall_status = HealthStatus.DEGRADED
            
            response_time = (time.time() - start_time) * 1000
            
            # 生成状态消息
            healthy_count = sum(1 for r in dependency_results if r["status"] == "healthy")
            total_count = len(dependency_results)
            
            if healthy_count == total_count:
                message = f"所有 {total_count} 个依赖服务正常"
            else:
                unhealthy_count = total_count - healthy_count
                message = f"{unhealthy_count}/{total_count} 个依赖服务异常"
            
            result = HealthCheckResult(
                check_id=check_id,
                service_name=service_name,
                component_name="dependencies",
                status=overall_status,
                response_time_ms=response_time,
                message=message,
                metadata={
                    "dependency_results": dependency_results,
                    "healthy_count": healthy_count,
                    "total_count": total_count,
                },
                dependencies=dependencies
            )
            
            await self._health_check_repo.save_health_check_result(result)
            return result
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            
            result = HealthCheckResult(
                check_id=check_id,
                service_name=service_name,
                component_name="dependencies",
                status=HealthStatus.UNHEALTHY,
                response_time_ms=response_time,
                message="依赖健康检查失败",
                error_details=str(e),
                dependencies=dependencies
            )
            
            await self._health_check_repo.save_health_check_result(result)
            return result
    
    async def perform_comprehensive_health_check(self, service_name: str) -> List[HealthCheckResult]:
        """
        执行综合健康检查
        
        Args:
            service_name: 服务名称
            
        Returns:
            List[HealthCheckResult]: 健康检查结果列表
        """
        results = []
        
        try:
            # 并行执行多种健康检查
            tasks = [
                self.perform_system_health_check(service_name),
                self.perform_service_health_check(service_name)
            ]
            
            # 如果服务有依赖，也检查依赖
            service_status = await self._service_status_repo.get_service_status_by_name(service_name)
            if service_status and service_status.dependencies:
                tasks.append(
                    self.perform_dependency_health_check(service_name, service_status.dependencies)
                )
            
            # 等待所有检查完成
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 处理异常情况
            processed_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    error_result = HealthCheckResult(
                        check_id=str(uuid.uuid4()),
                        service_name=service_name,
                        component_name=f"check_{i}",
                        status=HealthStatus.UNHEALTHY,
                        response_time_ms=0,
                        message="健康检查异常",
                        error_details=str(result)
                    )
                    processed_results.append(error_result)
                else:
                    processed_results.append(result)
            
            return processed_results
            
        except Exception as e:
            # 如果整个检查过程失败，返回一个错误结果
            error_result = HealthCheckResult(
                check_id=str(uuid.uuid4()),
                service_name=service_name,
                component_name="comprehensive_check",
                status=HealthStatus.UNHEALTHY,
                response_time_ms=0,
                message="综合健康检查失败",
                error_details=str(e)
            )
            return [error_result]
    
    async def get_health_summary(self, service_name: Optional[str] = None) -> Dict[str, Any]:
        """
        获取健康检查摘要
        
        Args:
            service_name: 服务名称（可选）
            
        Returns:
            Dict[str, Any]: 健康检查摘要
        """
        try:
            # 获取最新的健康检查结果
            latest_results = await self._health_check_repo.get_latest_health_check_results(service_name)
            
            # 按服务和组件分组
            service_health = {}
            overall_status = HealthStatus.HEALTHY
            
            for result in latest_results:
                service = result.service_name
                if service not in service_health:
                    service_health[service] = {
                        "service_name": service,
                        "overall_status": HealthStatus.HEALTHY,
                        "components": {},
                        "last_check": None,
                        "issues": []
                    }
                
                # 更新组件状态
                service_health[service]["components"][result.component_name] = {
                    "status": result.status,
                    "message": result.message,
                    "response_time_ms": result.response_time_ms,
                    "timestamp": result.timestamp
                }
                
                # 更新服务整体状态
                if result.status == HealthStatus.UNHEALTHY:
                    service_health[service]["overall_status"] = HealthStatus.UNHEALTHY
                    overall_status = HealthStatus.UNHEALTHY
                elif (result.status == HealthStatus.DEGRADED and 
                      service_health[service]["overall_status"] == HealthStatus.HEALTHY):
                    service_health[service]["overall_status"] = HealthStatus.DEGRADED
                    if overall_status == HealthStatus.HEALTHY:
                        overall_status = HealthStatus.DEGRADED
                
                # 更新最后检查时间
                if (service_health[service]["last_check"] is None or 
                    result.timestamp > service_health[service]["last_check"]):
                    service_health[service]["last_check"] = result.timestamp
                
                # 收集问题
                if result.status != HealthStatus.HEALTHY:
                    service_health[service]["issues"].append({
                        "component": result.component_name,
                        "status": result.status.value,
                        "message": result.message,
                        "error_details": result.error_details
                    })
            
            # 统计信息
            total_services = len(service_health)
            healthy_services = sum(1 for s in service_health.values() 
                                 if s["overall_status"] == HealthStatus.HEALTHY)
            degraded_services = sum(1 for s in service_health.values() 
                                  if s["overall_status"] == HealthStatus.DEGRADED)
            unhealthy_services = sum(1 for s in service_health.values() 
                                   if s["overall_status"] == HealthStatus.UNHEALTHY)
            
            return {
                "overall_status": overall_status.value,
                "summary": {
                    "total_services": total_services,
                    "healthy_services": healthy_services,
                    "degraded_services": degraded_services,
                    "unhealthy_services": unhealthy_services,
                    "health_percentage": (healthy_services / total_services * 100) if total_services > 0 else 100
                },
                "services": list(service_health.values()),
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "overall_status": HealthStatus.UNKNOWN.value,
                "error": str(e),
                "last_updated": datetime.now().isoformat()
            }
