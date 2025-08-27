"""
服务健康检查系统

基于config/backend/monitor_config.py配置的统一健康检查实现。
"""

import asyncio
import time
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import logging
import aiohttp
import psutil

from config.backend.monitor_config import (
    MONITORED_SERVICES_DETAILED,
    SYSTEM_METRICS_CONFIG,
    ALERT_RULES_CONFIG
)

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """健康状态枚举"""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    WARNING = "warning"
    UNKNOWN = "unknown"


@dataclass
class HealthCheckResult:
    """健康检查结果"""
    service_id: str
    status: HealthStatus
    response_time_ms: float
    timestamp: datetime
    details: Dict[str, Any]
    error_message: Optional[str] = None


@dataclass
class SystemHealth:
    """系统健康状态"""
    overall_status: HealthStatus
    services: List[HealthCheckResult]
    system_metrics: Dict[str, Any]
    timestamp: datetime
    summary: Dict[str, int]


class HealthChecker:
    """
    健康检查器
    
    基于monitor_config.py配置实现统一的服务健康检查。
    """
    
    def __init__(self):
        self.check_history = {}
        self.last_check_time = {}
        self.consecutive_failures = {}
        
    async def check_service_health(self, service_id: str, config: Dict[str, Any]) -> HealthCheckResult:
        """
        检查单个服务健康状态
        
        Args:
            service_id: 服务ID
            config: 服务配置
            
        Returns:
            HealthCheckResult: 健康检查结果
        """
        start_time = time.time()
        
        try:
            health_config = config.get('health_check', {})
            endpoint = health_config.get('endpoint', '/health')
            timeout = health_config.get('timeout', 5)
            port = config.get('port')
            
            if not port:
                return HealthCheckResult(
                    service_id=service_id,
                    status=HealthStatus.UNKNOWN,
                    response_time_ms=0,
                    timestamp=datetime.now(),
                    details={'error': '缺少端口配置'},
                    error_message="服务配置中缺少端口信息"
                )
            
            url = f"http://localhost:{port}{endpoint}"
            
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=timeout)
            ) as session:
                async with session.get(url) as response:
                    response_time = (time.time() - start_time) * 1000
                    
                    # 尝试解析响应内容
                    try:
                        content = await response.text()
                        if response.content_type == 'application/json':
                            details = await response.json()
                        else:
                            details = {'response': content[:200]}  # 限制响应内容长度
                    except Exception:
                        details = {'response': 'Unable to parse response'}
                    
                    # 确定健康状态
                    if response.status == 200:
                        status = HealthStatus.HEALTHY
                        error_message = None
                    elif 200 <= response.status < 300:
                        status = HealthStatus.WARNING
                        error_message = f"HTTP {response.status}"
                    else:
                        status = HealthStatus.UNHEALTHY
                        error_message = f"HTTP {response.status}"
                    
                    details.update({
                        'http_status': response.status,
                        'content_type': response.content_type,
                        'response_time_ms': response_time
                    })
                    
                    # 重置连续失败计数
                    if status == HealthStatus.HEALTHY:
                        self.consecutive_failures[service_id] = 0
                    else:
                        self.consecutive_failures[service_id] = self.consecutive_failures.get(service_id, 0) + 1
                    
                    return HealthCheckResult(
                        service_id=service_id,
                        status=status,
                        response_time_ms=response_time,
                        timestamp=datetime.now(),
                        details=details,
                        error_message=error_message
                    )
                    
        except asyncio.TimeoutError:
            response_time = (time.time() - start_time) * 1000
            self.consecutive_failures[service_id] = self.consecutive_failures.get(service_id, 0) + 1
            
            return HealthCheckResult(
                service_id=service_id,
                status=HealthStatus.UNHEALTHY,
                response_time_ms=response_time,
                timestamp=datetime.now(),
                details={'timeout': timeout},
                error_message=f"请求超时 ({timeout}s)"
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            self.consecutive_failures[service_id] = self.consecutive_failures.get(service_id, 0) + 1
            
            return HealthCheckResult(
                service_id=service_id,
                status=HealthStatus.UNHEALTHY,
                response_time_ms=response_time,
                timestamp=datetime.now(),
                details={'exception': str(e)},
                error_message=str(e)
            )
    
    async def collect_system_metrics(self) -> Dict[str, Any]:
        """收集系统指标"""
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # 内存信息
            memory = psutil.virtual_memory()
            
            # 磁盘信息
            disk_usage = {}
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    disk_usage[partition.mountpoint] = {
                        'total': usage.total,
                        'used': usage.used,
                        'free': usage.free,
                        'percent': (usage.used / usage.total) * 100
                    }
                except (PermissionError, FileNotFoundError):
                    continue
            
            # 系统负载 (Linux)
            load_avg = None
            if hasattr(psutil, 'getloadavg'):
                try:
                    load_avg = psutil.getloadavg()
                except:
                    pass
            
            return {
                'cpu': {
                    'percent': cpu_percent,
                    'count': psutil.cpu_count()
                },
                'memory': {
                    'total': memory.total,
                    'available': memory.available,
                    'percent': memory.percent,
                    'used': memory.used
                },
                'disk': disk_usage,
                'load_average': load_avg,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"收集系统指标时出错: {e}")
            return {'error': str(e), 'timestamp': datetime.now().isoformat()}
    
    async def check_all_services(self) -> SystemHealth:
        """检查所有服务的健康状态"""
        service_results = []
        
        # 并行检查所有服务
        tasks = []
        for service_id, config in MONITORED_SERVICES_DETAILED.items():
            task = self.check_service_health(service_id, config)
            tasks.append(task)
        
        if tasks:
            service_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 处理异常结果
            processed_results = []
            for i, result in enumerate(service_results):
                if isinstance(result, Exception):
                    service_id = list(MONITORED_SERVICES_DETAILED.keys())[i]
                    processed_results.append(HealthCheckResult(
                        service_id=service_id,
                        status=HealthStatus.UNHEALTHY,
                        response_time_ms=0,
                        timestamp=datetime.now(),
                        details={'exception': str(result)},
                        error_message=f"健康检查异常: {result}"
                    ))
                else:
                    processed_results.append(result)
            
            service_results = processed_results
        
        # 收集系统指标
        system_metrics = await self.collect_system_metrics()
        
        # 计算总体状态
        status_counts = {status: 0 for status in HealthStatus}
        for result in service_results:
            status_counts[result.status] += 1
        
        # 确定总体健康状态
        if status_counts[HealthStatus.UNHEALTHY] > 0:
            overall_status = HealthStatus.UNHEALTHY
        elif status_counts[HealthStatus.WARNING] > 0:
            overall_status = HealthStatus.WARNING
        elif status_counts[HealthStatus.HEALTHY] > 0:
            overall_status = HealthStatus.HEALTHY
        else:
            overall_status = HealthStatus.UNKNOWN
        
        return SystemHealth(
            overall_status=overall_status,
            services=service_results,
            system_metrics=system_metrics,
            timestamp=datetime.now(),
            summary={
                'total': len(service_results),
                'healthy': status_counts[HealthStatus.HEALTHY],
                'unhealthy': status_counts[HealthStatus.UNHEALTHY],
                'warning': status_counts[HealthStatus.WARNING],
                'unknown': status_counts[HealthStatus.UNKNOWN]
            }
        )
    
    def get_service_history(self, service_id: str, hours: int = 24) -> List[HealthCheckResult]:
        """
        获取服务的健康检查历史
        
        Args:
            service_id: 服务ID
            hours: 历史小时数
            
        Returns:
            List[HealthCheckResult]: 健康检查历史记录
        """
        if service_id not in self.check_history:
            return []
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [
            result for result in self.check_history[service_id]
            if result.timestamp >= cutoff_time
        ]
    
    def add_to_history(self, result: HealthCheckResult):
        """添加健康检查结果到历史记录"""
        if result.service_id not in self.check_history:
            self.check_history[result.service_id] = []
        
        self.check_history[result.service_id].append(result)
        
        # 保持历史记录在合理大小 (最多保留1000条)
        if len(self.check_history[result.service_id]) > 1000:
            self.check_history[result.service_id] = self.check_history[result.service_id][-1000:]
    
    async def start_periodic_checks(self, interval: int = 30):
        """
        启动周期性健康检查
        
        Args:
            interval: 检查间隔(秒)
        """
        logger.info(f"启动周期性健康检查，间隔: {interval}秒")
        
        while True:
            try:
                start_time = time.time()
                system_health = await self.check_all_services()
                
                # 保存历史记录
                for result in system_health.services:
                    self.add_to_history(result)
                
                check_time = time.time() - start_time
                logger.info(f"健康检查完成，耗时: {check_time:.2f}秒，"
                          f"状态: {system_health.summary}")
                
                # 等待下次检查
                await asyncio.sleep(max(0, interval - check_time))
                
            except Exception as e:
                logger.error(f"周期性健康检查出错: {e}")
                await asyncio.sleep(interval)


# 全局健康检查器实例
health_checker = HealthChecker()


# FastAPI端点辅助函数
async def get_health_status() -> Dict[str, Any]:
    """获取健康状态 (FastAPI端点使用)"""
    system_health = await health_checker.check_all_services()
    
    return {
        'status': system_health.overall_status.value,
        'timestamp': system_health.timestamp.isoformat(),
        'summary': system_health.summary,
        'services': [
            {
                'service': result.service_id,
                'status': result.status.value,
                'response_time_ms': result.response_time_ms,
                'error': result.error_message
            }
            for result in system_health.services
        ],
        'system': system_health.system_metrics
    }


async def get_service_health(service_id: str) -> Dict[str, Any]:
    """获取特定服务的健康状态"""
    if service_id not in MONITORED_SERVICES_DETAILED:
        return {
            'error': f'未找到服务: {service_id}',
            'available_services': list(MONITORED_SERVICES_DETAILED.keys())
        }
    
    config = MONITORED_SERVICES_DETAILED[service_id]
    result = await health_checker.check_service_health(service_id, config)
    
    return {
        'service': service_id,
        'status': result.status.value,
        'response_time_ms': result.response_time_ms,
        'timestamp': result.timestamp.isoformat(),
        'details': result.details,
        'error': result.error_message,
        'consecutive_failures': health_checker.consecutive_failures.get(service_id, 0)
    }


if __name__ == "__main__":
    # 测试代码
    async def main():
        checker = HealthChecker()
        
        print("执行健康检查...")
        system_health = await checker.check_all_services()
        
        print(f"\n总体状态: {system_health.overall_status.value}")
        print(f"检查时间: {system_health.timestamp}")
        print(f"服务统计: {system_health.summary}")
        
        print(f"\n服务详情:")
        for result in system_health.services:
            print(f"  {result.service_id}: {result.status.value} "
                  f"({result.response_time_ms:.1f}ms)")
            if result.error_message:
                print(f"    错误: {result.error_message}")
        
        print(f"\n系统指标:")
        metrics = system_health.system_metrics
        if 'cpu' in metrics:
            print(f"  CPU: {metrics['cpu']['percent']:.1f}%")
        if 'memory' in metrics:
            print(f"  内存: {metrics['memory']['percent']:.1f}%")
    
    asyncio.run(main())
