"""
Prometheus指标导出器

基于现有监控配置的统一指标导出系统，集成DomesticGatewayMonitor和系统监控。
"""

import asyncio
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import logging
import psutil
import json

# Prometheus客户端
try:
    from prometheus_client import Counter, Histogram, Gauge, Info, generate_latest, CONTENT_TYPE_LATEST
except ImportError:
    # 如果没有安装prometheus_client，提供模拟实现
    class Counter:
        def __init__(self, *args, **kwargs):
            self._value = 0
        def inc(self, amount=1):
            self._value += amount
        def labels(self, **kwargs):
            return self
    
    class Histogram:
        def __init__(self, *args, **kwargs):
            pass
        def observe(self, amount):
            pass
        def labels(self, **kwargs):
            return self
    
    class Gauge:
        def __init__(self, *args, **kwargs):
            self._value = 0
        def set(self, value):
            self._value = value
        def labels(self, **kwargs):
            return self
    
    class Info:
        def __init__(self, *args, **kwargs):
            pass
        def info(self, data):
            pass
    
    def generate_latest():
        return b"# Prometheus metrics mock\n"
    
    CONTENT_TYPE_LATEST = "text/plain"

from config.backend.monitor_config import (
    MONITORED_SERVICES_DETAILED,
    SYSTEM_METRICS_CONFIG,
    APPLICATION_METRICS_CONFIG,
    ALERT_RULES_CONFIG
)

logger = logging.getLogger(__name__)


@dataclass
class MetricValue:
    """指标值数据类"""
    name: str
    value: float
    labels: Dict[str, str]
    timestamp: datetime
    help_text: str = ""


class PrometheusExporter:
    """
    Prometheus指标导出器
    
    集成现有监控配置，提供统一的指标收集和导出功能。
    """
    
    def __init__(self):
        self.metrics_registry = {}
        self.last_collection_time = time.time()
        self._setup_metrics()
        
    def _setup_metrics(self):
        """设置Prometheus指标"""
        
        # 系统指标
        self.system_metrics = {
            'cpu_usage': Gauge('system_cpu_usage_percent', 'CPU使用率百分比'),
            'memory_usage': Gauge('system_memory_usage_percent', '内存使用率百分比'),
            'memory_available': Gauge('system_memory_available_bytes', '可用内存字节数'),
            'disk_usage': Gauge('system_disk_usage_percent', '磁盘使用率百分比', ['mount_point']),
            'disk_free': Gauge('system_disk_free_bytes', '磁盘可用空间字节数', ['mount_point']),
            'network_bytes_sent': Counter('system_network_bytes_sent_total', '网络发送字节数总计', ['interface']),
            'network_bytes_recv': Counter('system_network_bytes_recv_total', '网络接收字节数总计', ['interface']),
            'load_average': Gauge('system_load_average', '系统负载平均值', ['period']),
        }
        
        # 应用指标
        self.application_metrics = {
            'request_total': Counter('http_requests_total', 'HTTP请求总数', ['method', 'endpoint', 'status']),
            'request_duration': Histogram('http_request_duration_seconds', 'HTTP请求持续时间', ['method', 'endpoint']),
            'active_connections': Gauge('active_connections_total', '活跃连接数', ['service']),
            'error_rate': Gauge('error_rate_percent', '错误率百分比', ['service']),
            'response_time': Histogram('response_time_seconds', '响应时间秒数', ['service', 'endpoint']),
        }
        
        # 业务指标 (基于VnPy和交易系统)
        self.business_metrics = {
            'trading_orders_total': Counter('trading_orders_total', '交易订单总数', ['gateway', 'symbol', 'direction']),
            'trading_volume': Counter('trading_volume_total', '交易量总计', ['gateway', 'symbol']),
            'gateway_latency': Histogram('gateway_latency_seconds', '网关延迟秒数', ['gateway', 'operation']),
            'gateway_connection_status': Gauge('gateway_connection_status', '网关连接状态', ['gateway']),
            'strategy_pnl': Gauge('strategy_pnl_total', '策略盈亏总计', ['strategy_name']),
            'position_value': Gauge('position_value_total', '持仓价值总计', ['symbol', 'direction']),
        }
        
        # 服务健康指标
        self.health_metrics = {
            'service_up': Gauge('service_up', '服务状态 (1=up, 0=down)', ['service', 'instance']),
            'service_response_time': Histogram('service_health_check_duration_seconds', '服务健康检查响应时间', ['service']),
            'service_last_check': Gauge('service_last_health_check_timestamp', '最后健康检查时间戳', ['service']),
        }
        
        # 系统信息
        self.info_metrics = {
            'build_info': Info('build_info', '构建信息'),
            'system_info': Info('system_info', '系统信息'),
        }
        
        # 设置系统信息
        self.info_metrics['build_info'].info({
            'version': '2.0.0',
            'build_date': datetime.now().strftime('%Y-%m-%d'),
            'component': 'redfire-monitoring'
        })
        
        self.info_metrics['system_info'].info({
            'platform': psutil.LINUX if hasattr(psutil, 'LINUX') else 'unknown',
            'python_version': '3.8+',
            'monitoring_system': 'prometheus'
        })
    
    async def collect_system_metrics(self) -> List[MetricValue]:
        """收集系统指标"""
        metrics = []
        
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            self.system_metrics['cpu_usage'].set(cpu_percent)
            metrics.append(MetricValue(
                name='cpu_usage',
                value=cpu_percent,
                labels={},
                timestamp=datetime.now(),
                help_text='CPU使用率百分比'
            ))
            
            # 内存信息
            memory = psutil.virtual_memory()
            self.system_metrics['memory_usage'].set(memory.percent)
            self.system_metrics['memory_available'].set(memory.available)
            
            metrics.extend([
                MetricValue('memory_usage', memory.percent, {}, datetime.now(), '内存使用率百分比'),
                MetricValue('memory_available', memory.available, {}, datetime.now(), '可用内存字节数'),
            ])
            
            # 磁盘信息
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    mount_point = partition.mountpoint
                    
                    self.system_metrics['disk_usage'].labels(mount_point=mount_point).set(
                        (usage.used / usage.total) * 100
                    )
                    self.system_metrics['disk_free'].labels(mount_point=mount_point).set(usage.free)
                    
                    metrics.extend([
                        MetricValue('disk_usage', (usage.used / usage.total) * 100, 
                                  {'mount_point': mount_point}, datetime.now(), '磁盘使用率百分比'),
                        MetricValue('disk_free', usage.free, 
                                  {'mount_point': mount_point}, datetime.now(), '磁盘可用空间字节数'),
                    ])
                except (PermissionError, FileNotFoundError):
                    continue
            
            # 网络信息
            network = psutil.net_io_counters(pernic=True)
            for interface, stats in network.items():
                if interface != 'lo':  # 跳过回环接口
                    self.system_metrics['network_bytes_sent'].labels(interface=interface).inc(
                        stats.bytes_sent - getattr(self, f'_last_bytes_sent_{interface}', 0)
                    )
                    self.system_metrics['network_bytes_recv'].labels(interface=interface).inc(
                        stats.bytes_recv - getattr(self, f'_last_bytes_recv_{interface}', 0)
                    )
                    
                    # 保存上次的值
                    setattr(self, f'_last_bytes_sent_{interface}', stats.bytes_sent)
                    setattr(self, f'_last_bytes_recv_{interface}', stats.bytes_recv)
            
            # 系统负载
            if hasattr(psutil, 'getloadavg'):
                load_avg = psutil.getloadavg()
                for i, period in enumerate(['1min', '5min', '15min']):
                    self.system_metrics['load_average'].labels(period=period).set(load_avg[i])
                    metrics.append(MetricValue(
                        'load_average', load_avg[i], {'period': period}, 
                        datetime.now(), f'{period}系统负载平均值'
                    ))
            
        except Exception as e:
            logger.error(f"收集系统指标时出错: {e}")
        
        return metrics
    
    async def collect_service_health_metrics(self) -> List[MetricValue]:
        """收集服务健康指标"""
        metrics = []
        
        for service_id, config in MONITORED_SERVICES_DETAILED.items():
            try:
                # 模拟健康检查 (实际应该调用真实的健康检查接口)
                is_healthy = await self._check_service_health(service_id, config)
                
                self.health_metrics['service_up'].labels(
                    service=service_id, 
                    instance=f"localhost:{config['port']}"
                ).set(1 if is_healthy else 0)
                
                self.health_metrics['service_last_check'].labels(service=service_id).set(time.time())
                
                metrics.append(MetricValue(
                    name='service_up',
                    value=1 if is_healthy else 0,
                    labels={'service': service_id, 'instance': f"localhost:{config['port']}"},
                    timestamp=datetime.now(),
                    help_text='服务健康状态'
                ))
                
            except Exception as e:
                logger.error(f"检查服务 {service_id} 健康状态时出错: {e}")
                self.health_metrics['service_up'].labels(
                    service=service_id, 
                    instance=f"localhost:{config['port']}"
                ).set(0)
        
        return metrics
    
    async def _check_service_health(self, service_id: str, config: Dict[str, Any]) -> bool:
        """
        检查单个服务的健康状态
        
        Args:
            service_id: 服务ID
            config: 服务配置
            
        Returns:
            bool: 服务是否健康
        """
        try:
            import aiohttp
            
            health_config = config.get('health_check', {})
            endpoint = health_config.get('endpoint', '/health')
            timeout = health_config.get('timeout', 5)
            
            url = f"http://localhost:{config['port']}{endpoint}"
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
                start_time = time.time()
                async with session.get(url) as response:
                    duration = time.time() - start_time
                    
                    # 记录响应时间
                    self.health_metrics['service_response_time'].labels(service=service_id).observe(duration)
                    
                    return response.status == 200
                    
        except Exception as e:
            logger.debug(f"服务 {service_id} 健康检查失败: {e}")
            return False
    
    async def collect_business_metrics(self) -> List[MetricValue]:
        """
        收集业务指标
        
        这里应该集成DomesticGatewayMonitor和其他业务监控组件
        """
        metrics = []
        
        try:
            # 模拟业务指标收集
            # 实际应该从DomesticGatewayMonitor或其他监控组件获取数据
            
            # 网关连接状态
            for gateway in ['ctptest', 'xtp', 'oes']:
                # 模拟连接状态 (实际应该从真实的网关获取)
                status = 1  # 假设连接正常
                self.business_metrics['gateway_connection_status'].labels(gateway=gateway).set(status)
                
                metrics.append(MetricValue(
                    name='gateway_connection_status',
                    value=status,
                    labels={'gateway': gateway},
                    timestamp=datetime.now(),
                    help_text='网关连接状态'
                ))
            
            # 模拟交易指标
            self.business_metrics['trading_orders_total'].labels(
                gateway='ctptest', symbol='rb2501', direction='long'
            ).inc(0)  # 不增加，只是确保指标存在
            
        except Exception as e:
            logger.error(f"收集业务指标时出错: {e}")
        
        return metrics
    
    async def collect_all_metrics(self) -> Dict[str, List[MetricValue]]:
        """收集所有指标"""
        all_metrics = {
            'system': await self.collect_system_metrics(),
            'health': await self.collect_service_health_metrics(),
            'business': await self.collect_business_metrics(),
        }
        
        self.last_collection_time = time.time()
        return all_metrics
    
    def get_metrics_endpoint(self) -> str:
        """获取Prometheus指标格式的数据"""
        return generate_latest().decode('utf-8')
    
    def get_content_type(self) -> str:
        """获取内容类型"""
        return CONTENT_TYPE_LATEST
    
    async def start_collection_loop(self, interval: int = 30):
        """
        启动指标收集循环
        
        Args:
            interval: 收集间隔(秒)
        """
        logger.info(f"启动Prometheus指标收集循环，间隔: {interval}秒")
        
        while True:
            try:
                start_time = time.time()
                metrics = await self.collect_all_metrics()
                
                collection_time = time.time() - start_time
                logger.debug(f"指标收集完成，耗时: {collection_time:.2f}秒，"
                           f"收集到 {sum(len(m) for m in metrics.values())} 个指标")
                
                # 等待下次收集
                await asyncio.sleep(max(0, interval - collection_time))
                
            except Exception as e:
                logger.error(f"指标收集循环出错: {e}")
                await asyncio.sleep(interval)


# 全局实例
prometheus_exporter = PrometheusExporter()


async def get_prometheus_metrics() -> str:
    """
    获取Prometheus格式的指标数据
    
    这个函数可以被FastAPI或其他Web框架调用
    """
    # 确保最新的指标被收集
    await prometheus_exporter.collect_all_metrics()
    return prometheus_exporter.get_metrics_endpoint()


if __name__ == "__main__":
    # 测试代码
    async def main():
        exporter = PrometheusExporter()
        
        print("收集指标中...")
        metrics = await exporter.collect_all_metrics()
        
        for category, metric_list in metrics.items():
            print(f"\n{category.upper()} 指标:")
            for metric in metric_list[:5]:  # 只显示前5个
                print(f"  {metric.name}: {metric.value} {metric.labels}")
        
        print(f"\nPrometheus格式输出:")
        print(exporter.get_metrics_endpoint()[:500] + "...")
    
    asyncio.run(main())
