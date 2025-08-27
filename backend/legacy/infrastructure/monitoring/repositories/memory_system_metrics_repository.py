"""
内存系统指标仓储实现
==================

基于内存的系统指标仓储实现
"""

from typing import List, Optional, Dict, Any, Union
from datetime import datetime
import asyncio
from collections import defaultdict

from ....domain.monitoring.repositories.system_metrics_repository import ISystemMetricsRepository
from ....domain.monitoring.entities.system_metrics_entity import SystemMetrics, MetricType


class InMemorySystemMetricsRepository(ISystemMetricsRepository):
    """内存系统指标仓储实现"""
    
    def __init__(self):
        self._metrics: Dict[str, SystemMetrics] = {}
        self._service_metrics: Dict[str, List[str]] = defaultdict(list)
        self._type_metrics: Dict[MetricType, List[str]] = defaultdict(list)
        self._lock = asyncio.Lock()
    
    async def save_metric(self, metric: SystemMetrics) -> bool:
        """保存系统指标"""
        async with self._lock:
            try:
                self._metrics[metric.metric_id] = metric
                self._service_metrics[metric.service_name].append(metric.metric_id)
                self._type_metrics[metric.metric_type].append(metric.metric_id)
                
                # 限制记录数量
                max_records = 10000
                if len(self._service_metrics[metric.service_name]) > max_records:
                    oldest_id = self._service_metrics[metric.service_name].pop(0)
                    if oldest_id in self._metrics:
                        self._metrics.pop(oldest_id)
                
                return True
            except Exception:
                return False
    
    async def save_metrics_batch(self, metrics: List[SystemMetrics]) -> bool:
        """批量保存系统指标"""
        for metric in metrics:
            success = await self.save_metric(metric)
            if not success:
                return False
        return True
    
    async def get_metric(self, metric_id: str) -> Optional[SystemMetrics]:
        """获取系统指标"""
        return self._metrics.get(metric_id)
    
    async def get_metrics_by_service(
        self, 
        service_name: str,
        metric_name: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 1000
    ) -> List[SystemMetrics]:
        """获取指定服务的系统指标"""
        metric_ids = self._service_metrics.get(service_name, [])
        results = []
        
        for metric_id in reversed(metric_ids[-limit:]):
            if metric_id in self._metrics:
                metric = self._metrics[metric_id]
                
                # 指标名称过滤
                if metric_name and metric.metric_name != metric_name:
                    continue
                
                # 时间范围过滤
                if start_time and metric.timestamp < start_time:
                    continue
                if end_time and metric.timestamp > end_time:
                    continue
                
                results.append(metric)
        
        return results
    
    async def get_metrics_by_type(
        self, 
        metric_type: MetricType,
        service_name: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 1000
    ) -> List[SystemMetrics]:
        """获取指定类型的系统指标"""
        metric_ids = self._type_metrics.get(metric_type, [])
        results = []
        
        for metric_id in reversed(metric_ids[-limit:]):
            if metric_id in self._metrics:
                metric = self._metrics[metric_id]
                
                # 服务名称过滤
                if service_name and metric.service_name != service_name:
                    continue
                
                # 时间范围过滤
                if start_time and metric.timestamp < start_time:
                    continue
                if end_time and metric.timestamp > end_time:
                    continue
                
                results.append(metric)
        
        return results
    
    async def get_latest_metrics(
        self,
        service_name: Optional[str] = None,
        metric_name: Optional[str] = None
    ) -> List[SystemMetrics]:
        """获取最新的系统指标"""
        latest_by_service_metric = {}
        
        for metric in self._metrics.values():
            # 服务名称过滤
            if service_name and metric.service_name != service_name:
                continue
            
            # 指标名称过滤
            if metric_name and metric.metric_name != metric_name:
                continue
            
            key = f"{metric.service_name}:{metric.metric_name}"
            if (key not in latest_by_service_metric or 
                metric.timestamp > latest_by_service_metric[key].timestamp):
                latest_by_service_metric[key] = metric
        
        return list(latest_by_service_metric.values())
    
    async def get_metrics_aggregated(
        self,
        service_name: str,
        metric_name: str,
        start_time: datetime,
        end_time: datetime,
        aggregation_window: str = "1m"
    ) -> List[Dict[str, Any]]:
        """获取聚合的系统指标"""
        # 简化实现，返回基本聚合数据
        metrics = await self.get_metrics_by_service(
            service_name, metric_name, start_time, end_time
        )
        
        if not metrics:
            return []
        
        values = [m.value for m in metrics if isinstance(m.value, (int, float))]
        if not values:
            return []
        
        return [{
            "timestamp": end_time.isoformat(),
            "min": min(values),
            "max": max(values),
            "avg": sum(values) / len(values),
            "count": len(values)
        }]
    
    async def get_metric_statistics(
        self,
        service_name: str,
        metric_name: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """获取指标统计信息"""
        metrics = await self.get_metrics_by_service(
            service_name, metric_name, start_time, end_time
        )
        
        if not metrics:
            return {"count": 0}
        
        values = [m.value for m in metrics if isinstance(m.value, (int, float))]
        if not values:
            return {"count": len(metrics), "numeric_values": 0}
        
        return {
            "count": len(metrics),
            "numeric_values": len(values),
            "min": min(values),
            "max": max(values),
            "avg": sum(values) / len(values),
            "first_timestamp": min(m.timestamp for m in metrics).isoformat(),
            "last_timestamp": max(m.timestamp for m in metrics).isoformat()
        }
    
    async def delete_old_metrics(
        self,
        before_time: datetime,
        service_name: Optional[str] = None
    ) -> int:
        """删除指定时间之前的指标数据"""
        async with self._lock:
            to_delete = []
            
            for metric_id, metric in self._metrics.items():
                if metric.timestamp < before_time:
                    if service_name is None or metric.service_name == service_name:
                        to_delete.append(metric_id)
            
            for metric_id in to_delete:
                metric = self._metrics.pop(metric_id)
                # 从索引中移除
                if metric_id in self._service_metrics[metric.service_name]:
                    self._service_metrics[metric.service_name].remove(metric_id)
                if metric_id in self._type_metrics[metric.metric_type]:
                    self._type_metrics[metric.metric_type].remove(metric_id)
            
            return len(to_delete)
    
    async def get_metric_values_range(
        self,
        service_name: str,
        metric_name: str,
        start_time: datetime,
        end_time: datetime
    ) -> Dict[str, Union[float, int]]:
        """获取指标值的范围信息"""
        metrics = await self.get_metrics_by_service(
            service_name, metric_name, start_time, end_time
        )
        
        values = [m.value for m in metrics if isinstance(m.value, (int, float))]
        if not values:
            return {"min": 0, "max": 0, "avg": 0}
        
        return {
            "min": min(values),
            "max": max(values),
            "avg": sum(values) / len(values)
        }
    
    async def search_metrics(
        self,
        query: str,
        labels: Optional[Dict[str, str]] = None,
        limit: int = 100
    ) -> List[SystemMetrics]:
        """搜索系统指标"""
        results = []
        count = 0
        
        for metric in self._metrics.values():
            if count >= limit:
                break
            
            # 简单的查询匹配
            if (query.lower() in metric.service_name.lower() or 
                query.lower() in metric.metric_name.lower()):
                
                # 标签过滤
                if labels:
                    label_match = all(
                        metric.labels.get(k) == v for k, v in labels.items()
                    )
                    if not label_match:
                        continue
                
                results.append(metric)
                count += 1
        
        return results
