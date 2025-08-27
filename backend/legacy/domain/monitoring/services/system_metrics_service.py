"""
系统指标服务
==========

负责收集和管理系统性能指标的具体实现
"""

import psutil
import time
import uuid
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta

from ....core.common.exceptions import DomainException
from ..entities.system_metrics_entity import (
    SystemMetrics, MetricType, MetricUnit,
    CPUMetrics, MemoryMetrics, DiskMetrics, NetworkMetrics
)
from ..repositories.system_metrics_repository import ISystemMetricsRepository


class SystemMetricsService:
    """
    系统指标服务
    
    负责收集各种系统性能指标，包括：
    - CPU使用率
    - 内存使用情况
    - 磁盘I/O和使用率
    - 网络流量
    - 自定义应用指标
    """
    
    def __init__(self, metrics_repository: ISystemMetricsRepository):
        self._metrics_repo = metrics_repository
        
        # 指标收集配置
        self._collection_interval = 10  # 秒
        self._batch_size = 100
        self._retention_hours = 72
        
        # 网络统计基线
        self._network_baseline = None
        self._last_network_check = None
    
    async def collect_cpu_metrics(self, service_name: str) -> CPUMetrics:
        """
        收集CPU指标
        
        Args:
            service_name: 服务名称
            
        Returns:
            CPUMetrics: CPU指标
        """
        try:
            # 获取CPU使用率（1秒间隔）
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # 获取每个核心的使用率
            cpu_per_core = psutil.cpu_percent(interval=None, percpu=True)
            
            # 获取CPU频率
            cpu_freq = psutil.cpu_freq()
            
            # 获取负载平均值（仅在类Unix系统上可用）
            load_avg = None
            try:
                load_avg = psutil.getloadavg()
            except AttributeError:
                # Windows系统没有getloadavg
                pass
            
            metric = CPUMetrics(
                metric_id=str(uuid.uuid4()),
                service_name=service_name,
                value=cpu_percent,
                labels={
                    "metric_category": "system",
                    "resource_type": "cpu"
                },
                metadata={
                    "cpu_count": psutil.cpu_count(),
                    "cpu_count_logical": psutil.cpu_count(logical=True),
                    "cpu_per_core": cpu_per_core,
                    "cpu_freq_current": cpu_freq.current if cpu_freq else None,
                    "cpu_freq_min": cpu_freq.min if cpu_freq else None,
                    "cpu_freq_max": cpu_freq.max if cpu_freq else None,
                    "load_avg_1min": load_avg[0] if load_avg else None,
                    "load_avg_5min": load_avg[1] if load_avg else None,
                    "load_avg_15min": load_avg[2] if load_avg else None,
                },
                min_value=0.0,
                max_value=100.0,
                avg_value=cpu_percent
            )
            
            await self._metrics_repo.save_metric(metric)
            return metric
            
        except Exception as e:
            raise DomainException(f"CPU指标收集失败: {e}")
    
    async def collect_memory_metrics(self, service_name: str) -> MemoryMetrics:
        """
        收集内存指标
        
        Args:
            service_name: 服务名称
            
        Returns:
            MemoryMetrics: 内存指标
        """
        try:
            # 获取虚拟内存信息
            memory = psutil.virtual_memory()
            
            # 获取交换内存信息
            swap = psutil.swap_memory()
            
            metric = MemoryMetrics(
                metric_id=str(uuid.uuid4()),
                service_name=service_name,
                value=memory.percent,
                labels={
                    "metric_category": "system",
                    "resource_type": "memory"
                },
                metadata={
                    "total_gb": memory.total / (1024**3),
                    "available_gb": memory.available / (1024**3),
                    "used_gb": memory.used / (1024**3),
                    "free_gb": memory.free / (1024**3),
                    "active_gb": getattr(memory, 'active', 0) / (1024**3),
                    "inactive_gb": getattr(memory, 'inactive', 0) / (1024**3),
                    "buffers_gb": getattr(memory, 'buffers', 0) / (1024**3),
                    "cached_gb": getattr(memory, 'cached', 0) / (1024**3),
                    "swap_total_gb": swap.total / (1024**3),
                    "swap_used_gb": swap.used / (1024**3),
                    "swap_free_gb": swap.free / (1024**3),
                    "swap_percent": swap.percent,
                },
                min_value=0.0,
                max_value=100.0,
                avg_value=memory.percent
            )
            
            await self._metrics_repo.save_metric(metric)
            return metric
            
        except Exception as e:
            raise DomainException(f"内存指标收集失败: {e}")
    
    async def collect_disk_metrics(self, service_name: str, path: str = '/') -> DiskMetrics:
        """
        收集磁盘指标
        
        Args:
            service_name: 服务名称
            path: 磁盘路径
            
        Returns:
            DiskMetrics: 磁盘指标
        """
        try:
            # 获取磁盘使用情况
            disk_usage = psutil.disk_usage(path)
            
            # 获取磁盘I/O统计
            disk_io = psutil.disk_io_counters()
            
            # 获取所有磁盘分区
            partitions = psutil.disk_partitions()
            
            metric = DiskMetrics(
                metric_id=str(uuid.uuid4()),
                service_name=service_name,
                value=disk_usage.percent,
                labels={
                    "metric_category": "system",
                    "resource_type": "disk",
                    "disk_path": path
                },
                metadata={
                    "total_gb": disk_usage.total / (1024**3),
                    "used_gb": disk_usage.used / (1024**3),
                    "free_gb": disk_usage.free / (1024**3),
                    "read_count": disk_io.read_count if disk_io else 0,
                    "write_count": disk_io.write_count if disk_io else 0,
                    "read_bytes": disk_io.read_bytes if disk_io else 0,
                    "write_bytes": disk_io.write_bytes if disk_io else 0,
                    "read_time": disk_io.read_time if disk_io else 0,
                    "write_time": disk_io.write_time if disk_io else 0,
                    "partitions": [
                        {
                            "device": p.device,
                            "mountpoint": p.mountpoint,
                            "fstype": p.fstype,
                            "opts": p.opts
                        } for p in partitions
                    ]
                },
                min_value=0.0,
                max_value=100.0,
                avg_value=disk_usage.percent
            )
            
            await self._metrics_repo.save_metric(metric)
            return metric
            
        except Exception as e:
            raise DomainException(f"磁盘指标收集失败: {e}")
    
    async def collect_network_metrics(self, service_name: str) -> NetworkMetrics:
        """
        收集网络指标
        
        Args:
            service_name: 服务名称
            
        Returns:
            NetworkMetrics: 网络指标
        """
        try:
            # 获取网络I/O统计
            net_io = psutil.net_io_counters()
            current_time = time.time()
            
            # 计算网络速率
            bytes_sent_rate = 0
            bytes_recv_rate = 0
            
            if self._network_baseline and self._last_network_check:
                time_diff = current_time - self._last_network_check
                if time_diff > 0:
                    bytes_sent_diff = net_io.bytes_sent - self._network_baseline['bytes_sent']
                    bytes_recv_diff = net_io.bytes_recv - self._network_baseline['bytes_recv']
                    bytes_sent_rate = bytes_sent_diff / time_diff
                    bytes_recv_rate = bytes_recv_diff / time_diff
            
            # 更新基线
            self._network_baseline = {
                'bytes_sent': net_io.bytes_sent,
                'bytes_recv': net_io.bytes_recv
            }
            self._last_network_check = current_time
            
            # 获取网络连接信息
            connections = psutil.net_connections()
            active_connections = len([c for c in connections if c.status == 'ESTABLISHED'])
            
            # 计算总网络流量（发送+接收）
            total_rate = bytes_sent_rate + bytes_recv_rate
            
            metric = NetworkMetrics(
                metric_id=str(uuid.uuid4()),
                service_name=service_name,
                value=total_rate,
                labels={
                    "metric_category": "system",
                    "resource_type": "network"
                },
                metadata={
                    "bytes_sent": net_io.bytes_sent,
                    "bytes_recv": net_io.bytes_recv,
                    "packets_sent": net_io.packets_sent,
                    "packets_recv": net_io.packets_recv,
                    "errin": net_io.errin,
                    "errout": net_io.errout,
                    "dropin": net_io.dropin,
                    "dropout": net_io.dropout,
                    "bytes_sent_rate": bytes_sent_rate,
                    "bytes_recv_rate": bytes_recv_rate,
                    "active_connections": active_connections,
                    "total_connections": len(connections),
                },
                min_value=0.0
            )
            
            await self._metrics_repo.save_metric(metric)
            return metric
            
        except Exception as e:
            raise DomainException(f"网络指标收集失败: {e}")
    
    async def collect_process_metrics(self, service_name: str, process_name: Optional[str] = None) -> SystemMetrics:
        """
        收集进程指标
        
        Args:
            service_name: 服务名称
            process_name: 进程名称（可选）
            
        Returns:
            SystemMetrics: 进程指标
        """
        try:
            # 如果指定了进程名称，查找该进程
            target_processes = []
            
            if process_name:
                for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                    try:
                        if process_name.lower() in proc.info['name'].lower():
                            target_processes.append(proc)
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
            else:
                # 获取当前进程
                target_processes = [psutil.Process()]
            
            if not target_processes:
                raise DomainException(f"未找到进程: {process_name}")
            
            # 汇总进程指标
            total_cpu = 0
            total_memory = 0
            total_memory_rss = 0
            process_count = len(target_processes)
            process_details = []
            
            for proc in target_processes:
                try:
                    proc_info = proc.as_dict([
                        'pid', 'name', 'cpu_percent', 'memory_percent', 
                        'memory_info', 'num_threads', 'create_time'
                    ])
                    
                    total_cpu += proc_info.get('cpu_percent', 0) or 0
                    total_memory += proc_info.get('memory_percent', 0) or 0
                    
                    memory_info = proc_info.get('memory_info')
                    if memory_info:
                        total_memory_rss += memory_info.rss
                    
                    process_details.append({
                        'pid': proc_info.get('pid'),
                        'name': proc_info.get('name'),
                        'cpu_percent': proc_info.get('cpu_percent', 0),
                        'memory_percent': proc_info.get('memory_percent', 0),
                        'memory_rss_mb': memory_info.rss / (1024**2) if memory_info else 0,
                        'num_threads': proc_info.get('num_threads', 0),
                        'create_time': proc_info.get('create_time'),
                    })
                    
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # 计算平均值
            avg_cpu = total_cpu / process_count if process_count > 0 else 0
            avg_memory = total_memory / process_count if process_count > 0 else 0
            
            metric = SystemMetrics(
                metric_id=str(uuid.uuid4()),
                service_name=service_name,
                metric_name="process_cpu_usage",
                metric_type=MetricType.GAUGE,
                metric_unit=MetricUnit.PERCENTAGE,
                value=avg_cpu,
                labels={
                    "metric_category": "process",
                    "resource_type": "cpu",
                    "process_name": process_name or "current"
                },
                metadata={
                    "process_count": process_count,
                    "total_cpu_percent": total_cpu,
                    "avg_cpu_percent": avg_cpu,
                    "total_memory_percent": total_memory,
                    "avg_memory_percent": avg_memory,
                    "total_memory_rss_mb": total_memory_rss / (1024**2),
                    "process_details": process_details,
                }
            )
            
            await self._metrics_repo.save_metric(metric)
            return metric
            
        except Exception as e:
            raise DomainException(f"进程指标收集失败: {e}")
    
    async def collect_all_system_metrics(self, service_name: str) -> List[SystemMetrics]:
        """
        收集所有系统指标
        
        Args:
            service_name: 服务名称
            
        Returns:
            List[SystemMetrics]: 系统指标列表
        """
        try:
            metrics = []
            
            # 并行收集各种指标
            cpu_metric = await self.collect_cpu_metrics(service_name)
            metrics.append(cpu_metric)
            
            memory_metric = await self.collect_memory_metrics(service_name)
            metrics.append(memory_metric)
            
            disk_metric = await self.collect_disk_metrics(service_name)
            metrics.append(disk_metric)
            
            network_metric = await self.collect_network_metrics(service_name)
            metrics.append(network_metric)
            
            process_metric = await self.collect_process_metrics(service_name)
            metrics.append(process_metric)
            
            return metrics
            
        except Exception as e:
            raise DomainException(f"系统指标收集失败: {e}")
    
    async def create_custom_metric(
        self, 
        service_name: str,
        metric_name: str,
        metric_type: MetricType,
        metric_unit: MetricUnit,
        value: Union[float, int],
        labels: Optional[Dict[str, str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> SystemMetrics:
        """
        创建自定义指标
        
        Args:
            service_name: 服务名称
            metric_name: 指标名称
            metric_type: 指标类型
            metric_unit: 指标单位
            value: 指标值
            labels: 标签（可选）
            metadata: 元数据（可选）
            
        Returns:
            SystemMetrics: 系统指标
        """
        try:
            metric = SystemMetrics(
                metric_id=str(uuid.uuid4()),
                service_name=service_name,
                metric_name=metric_name,
                metric_type=metric_type,
                metric_unit=metric_unit,
                value=value,
                labels=labels or {},
                metadata=metadata or {}
            )
            
            await self._metrics_repo.save_metric(metric)
            return metric
            
        except Exception as e:
            raise DomainException(f"自定义指标创建失败: {e}")
    
    async def get_metrics_summary(
        self, 
        service_name: Optional[str] = None,
        time_range_hours: int = 1
    ) -> Dict[str, Any]:
        """
        获取指标摘要
        
        Args:
            service_name: 服务名称（可选）
            time_range_hours: 时间范围（小时）
            
        Returns:
            Dict[str, Any]: 指标摘要
        """
        try:
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=time_range_hours)
            
            # 获取指定时间范围的指标
            metrics = await self._metrics_repo.get_metrics_by_service(
                service_name, 
                start_time=start_time, 
                end_time=end_time
            ) if service_name else []
            
            # 按指标名称分组
            metrics_by_name = {}
            for metric in metrics:
                name = metric.metric_name
                if name not in metrics_by_name:
                    metrics_by_name[name] = []
                metrics_by_name[name].append(metric)
            
            # 计算统计信息
            summary = {
                "time_range": {
                    "start_time": start_time.isoformat(),
                    "end_time": end_time.isoformat(),
                    "duration_hours": time_range_hours
                },
                "total_metrics": len(metrics),
                "metric_types": {},
                "service_summary": {},
                "latest_values": {}
            }
            
            # 按指标类型统计
            for metric in metrics:
                metric_type = metric.metric_type.value
                if metric_type not in summary["metric_types"]:
                    summary["metric_types"][metric_type] = 0
                summary["metric_types"][metric_type] += 1
            
            # 计算每个指标的统计信息
            for name, metric_list in metrics_by_name.items():
                values = [m.value for m in metric_list if isinstance(m.value, (int, float))]
                
                if values:
                    summary["latest_values"][name] = {
                        "current_value": metric_list[-1].value,
                        "min_value": min(values),
                        "max_value": max(values),
                        "avg_value": sum(values) / len(values),
                        "count": len(values),
                        "unit": metric_list[-1].metric_unit.value,
                        "last_updated": metric_list[-1].timestamp.isoformat()
                    }
            
            # 按服务分组统计
            if not service_name:
                services = set(m.service_name for m in metrics)
                for svc in services:
                    svc_metrics = [m for m in metrics if m.service_name == svc]
                    summary["service_summary"][svc] = {
                        "metric_count": len(svc_metrics),
                        "last_updated": max(m.timestamp for m in svc_metrics).isoformat() if svc_metrics else None
                    }
            
            return summary
            
        except Exception as e:
            return {
                "error": str(e),
                "time_range": {
                    "start_time": (datetime.now() - timedelta(hours=time_range_hours)).isoformat(),
                    "end_time": datetime.now().isoformat(),
                    "duration_hours": time_range_hours
                }
            }
