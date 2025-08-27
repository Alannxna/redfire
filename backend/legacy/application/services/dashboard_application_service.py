"""
仪表盘应用服务
==============

处理系统监控和服务状态相关的业务逻辑
"""

# 标准库导入
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

# 第三方库导入
import psutil

# 核心层导入
from ...core.infrastructure.service_registry import get_service_registry

# 应用层内部导入
from .base_application_service import BaseApplicationService


class DashboardApplicationService(BaseApplicationService):
    """仪表盘应用服务"""
    
    def __init__(self):
        # 注意：仪表盘服务不依赖命令和查询总线，传入None
        super().__init__(command_bus=None, query_bus=None)
        self._logger = logging.getLogger(self.__class__.__name__)
    
    def get_service_info(self) -> Dict[str, Any]:
        """获取服务信息"""
        return {
            "service_name": "DashboardApplicationService",
            "description": "系统监控和服务状态管理应用服务",
            "version": "1.0.0",
            "capabilities": [
                "system_monitoring",
                "service_health_check",
                "performance_metrics",
                "alert_management"
            ]
        }
    
    async def get_system_info(self) -> Dict[str, Any]:
        """获取系统信息"""
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # 内存使用情况
            memory = psutil.virtual_memory()
            
            # 磁盘使用情况
            disk_usage = psutil.disk_usage('/')
            
            # 系统启动时间
            boot_time = psutil.boot_time()
            uptime = datetime.now().timestamp() - boot_time
            
            return {
                'cpu_percent': cpu_percent,
                'memory': {
                    'total': memory.total,
                    'available': memory.available,
                    'percent': memory.percent,
                    'used': memory.used
                },
                'disk': {
                    'total': disk_usage.total,
                    'free': disk_usage.free,
                    'used': disk_usage.used,
                    'percent': (disk_usage.used / disk_usage.total) * 100
                },
                'uptime': uptime,
                'last_check': datetime.now().isoformat()
            }
            
        except Exception as e:
            self._logger.error(f"获取系统信息失败: {e}")
            raise
    
    async def get_dashboard_overview(self) -> Dict[str, Any]:
        """获取仪表盘概览信息"""
        try:
            # 获取系统信息
            system_info = await self.get_system_info()
            
            # 获取服务状态统计（这里简化处理，实际应该从服务注册中心获取）
            service_stats = await self._get_service_statistics()
            
            # 确定系统健康状态
            system_health = await self._determine_system_health(system_info, service_stats)
            
            overview = {
                'total_services': service_stats['total'],
                'online_services': service_stats['online'],
                'offline_services': service_stats['offline'],
                'partial_services': service_stats['partial'],
                'system_health': system_health,
                'uptime': system_info['uptime'],
                'cpu_usage': system_info['cpu_percent'],
                'memory_usage': system_info['memory']['percent'],
                'disk_usage': system_info['disk']['percent'],
                'last_update': datetime.now().isoformat()
            }
            
            return overview
            
        except Exception as e:
            self._logger.error(f"获取仪表盘概览失败: {e}")
            raise
    
    async def get_service_health_summary(self) -> Dict[str, Any]:
        """获取服务健康状态摘要"""
        try:
            service_registry = get_service_registry()
            if service_registry:
                # 从服务注册中心获取健康状态
                health_status = await service_registry.health_check_all()
                return health_status
            else:
                # 服务注册中心未初始化时的默认状态
                return {
                    'overall_healthy': True,
                    'services': {},
                    'message': '服务注册中心未初始化'
                }
        except Exception as e:
            self._logger.warning(f"获取服务健康状态摘要失败: {e}")
            return {
                'overall_healthy': False,
                'services': {},
                'error': str(e)
            }
    
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        try:
            # CPU详细信息
            cpu_times = psutil.cpu_times_percent(interval=1)
            cpu_freq = psutil.cpu_freq()
            
            # 内存详细信息
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            # 磁盘IO
            disk_io = psutil.disk_io_counters()
            
            # 网络IO
            net_io = psutil.net_io_counters()
            
            # 进程信息
            process_count = len(psutil.pids())
            
            return {
                'cpu': {
                    'percent': psutil.cpu_percent(),
                    'times': {
                        'user': cpu_times.user,
                        'system': cpu_times.system,
                        'idle': cpu_times.idle
                    },
                    'frequency': {
                        'current': cpu_freq.current if cpu_freq else 0,
                        'min': cpu_freq.min if cpu_freq else 0,
                        'max': cpu_freq.max if cpu_freq else 0
                    },
                    'core_count': psutil.cpu_count()
                },
                'memory': {
                    'virtual': {
                        'total': memory.total,
                        'used': memory.used,
                        'available': memory.available,
                        'percent': memory.percent
                    },
                    'swap': {
                        'total': swap.total,
                        'used': swap.used,
                        'free': swap.free,
                        'percent': swap.percent
                    }
                },
                'disk': {
                    'io': {
                        'read_count': disk_io.read_count if disk_io else 0,
                        'write_count': disk_io.write_count if disk_io else 0,
                        'read_bytes': disk_io.read_bytes if disk_io else 0,
                        'write_bytes': disk_io.write_bytes if disk_io else 0
                    }
                },
                'network': {
                    'io': {
                        'bytes_sent': net_io.bytes_sent if net_io else 0,
                        'bytes_recv': net_io.bytes_recv if net_io else 0,
                        'packets_sent': net_io.packets_sent if net_io else 0,
                        'packets_recv': net_io.packets_recv if net_io else 0
                    }
                },
                'processes': {
                    'count': process_count
                },
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self._logger.error(f"获取性能指标失败: {e}")
            raise
    
    async def get_alerts(self) -> List[Dict[str, Any]]:
        """获取系统告警"""
        try:
            alerts = []
            
            # 检查系统资源告警
            system_info = await self.get_system_info()
            
            # CPU告警
            if system_info['cpu_percent'] > 80:
                alerts.append({
                    'alert_id': f"cpu_high_{datetime.now().timestamp()}",
                    'service_id': 'system',
                    'alert_type': 'high_cpu_usage',
                    'severity': 'high' if system_info['cpu_percent'] > 90 else 'medium',
                    'title': 'CPU使用率过高',
                    'message': f"CPU使用率超过阈值，当前值: {system_info['cpu_percent']:.1f}%",
                    'created_at': datetime.now().isoformat(),
                    'status': 'active'
                })
            
            # 内存告警
            memory_percent = system_info['memory']['percent']
            if memory_percent > 85:
                alerts.append({
                    'alert_id': f"memory_high_{datetime.now().timestamp()}",
                    'service_id': 'system',
                    'alert_type': 'high_memory_usage',
                    'severity': 'high' if memory_percent > 95 else 'medium',
                    'title': '内存使用率过高',
                    'message': f"内存使用率超过阈值，当前值: {memory_percent:.1f}%",
                    'created_at': datetime.now().isoformat(),
                    'status': 'active'
                })
            
            # 磁盘告警
            disk_percent = system_info['disk']['percent']
            if disk_percent > 90:
                alerts.append({
                    'alert_id': f"disk_high_{datetime.now().timestamp()}",
                    'service_id': 'system',
                    'alert_type': 'high_disk_usage',
                    'severity': 'high' if disk_percent > 95 else 'medium',
                    'title': '磁盘使用率过高',
                    'message': f"磁盘使用率超过阈值，当前值: {disk_percent:.1f}%",
                    'created_at': datetime.now().isoformat(),
                    'status': 'active'
                })
            
            return alerts
            
        except Exception as e:
            self._logger.error(f"获取告警信息失败: {e}")
            return []
    
    async def _get_service_statistics(self) -> Dict[str, int]:
        """获取服务状态统计"""
        try:
            # 这里简化处理，实际应该从服务发现或注册中心获取
            # 目前返回预定义的服务数量统计
            return {
                'total': 7,  # 预定义的服务总数
                'online': 1,  # 当前后端服务在线
                'offline': 5,  # 其他服务离线
                'partial': 1   # 部分服务
            }
        except Exception as e:
            self._logger.warning(f"获取服务统计失败: {e}")
            return {
                'total': 0,
                'online': 0,
                'offline': 0,
                'partial': 0
            }
    
    async def _determine_system_health(self, system_info: Dict[str, Any], 
                                     service_stats: Dict[str, int]) -> str:
        """确定系统健康状态"""
        try:
            # 检查系统资源
            cpu_ok = system_info['cpu_percent'] < 80
            memory_ok = system_info['memory']['percent'] < 85
            disk_ok = system_info['disk']['percent'] < 90
            
            # 检查服务状态
            services_ok = service_stats['online'] > 0 and service_stats['offline'] == 0
            
            if cpu_ok and memory_ok and disk_ok and services_ok:
                return 'healthy'
            elif cpu_ok and memory_ok and disk_ok:
                return 'warning'
            else:
                return 'critical'
                
        except Exception as e:
            self._logger.error(f"确定系统健康状态失败: {e}")
            return 'unknown'
