"""
统一监控服务

集成所有监控组件：
- DomesticGatewayMonitor (专业交易监控)
- PrometheusExporter (指标导出)
- HealthChecker (健康检查)
- AlertManager (告警管理)
- 基于monitor_config.py的配置管理
"""

import asyncio
import time
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import logging

from .prometheus_exporter import prometheus_exporter
from .health_check import health_checker, HealthStatus
from .alert_system import alert_manager
from config.backend.monitor_config import (
    MONITORED_SERVICES_DETAILED,
    SYSTEM_METRICS_CONFIG,
    APPLICATION_METRICS_CONFIG,
    BUSINESS_METRICS_CONFIG
)

# 尝试导入DomesticGatewayMonitor
try:
    from backend.core.tradingEngine.monitoring.domestic_gateway_monitor import DomesticGatewayMonitor
    DOMESTIC_GATEWAY_AVAILABLE = True
except ImportError:
    DOMESTIC_GATEWAY_AVAILABLE = False
    DomesticGatewayMonitor = None

logger = logging.getLogger(__name__)


@dataclass
class MonitoringStatus:
    """监控系统状态"""
    system_health: str
    active_alerts: int
    services_up: int
    services_total: int
    last_update: datetime
    components: Dict[str, bool]


class UnifiedMonitor:
    """
    统一监控服务
    
    整合所有监控组件，提供统一的监控数据收集、处理和报告功能。
    """
    
    def __init__(self):
        self.running = False
        self.domestic_gateway_monitor = None
        self.last_metrics = {}
        self.monitoring_tasks = []
        
        # 初始化DomesticGatewayMonitor
        if DOMESTIC_GATEWAY_AVAILABLE:
            try:
                self.domestic_gateway_monitor = DomesticGatewayMonitor()
                logger.info("DomesticGatewayMonitor已初始化")
            except Exception as e:
                logger.warning(f"DomesticGatewayMonitor初始化失败: {e}")
                self.domestic_gateway_monitor = None
        else:
            logger.info("DomesticGatewayMonitor不可用，跳过专业交易监控")
    
    async def collect_all_metrics(self) -> Dict[str, Any]:
        """收集所有监控指标"""
        all_metrics = {
            'timestamp': datetime.now().isoformat(),
            'system': {},
            'services': {},
            'business': {},
            'alerts': {},
            'domestic_gateway': {}
        }
        
        try:
            # 1. 收集系统和健康指标
            prometheus_metrics = await prometheus_exporter.collect_all_metrics()
            all_metrics['system'] = prometheus_metrics.get('system', [])
            all_metrics['services'] = prometheus_metrics.get('health', [])
            
            # 2. 收集服务健康状态
            system_health = await health_checker.check_all_services()
            all_metrics['services_health'] = {
                'overall_status': system_health.overall_status.value,
                'summary': system_health.summary,
                'services': [
                    {
                        'service': result.service_id,
                        'status': result.status.value,
                        'response_time_ms': result.response_time_ms,
                        'error': result.error_message
                    }
                    for result in system_health.services
                ]
            }
            
            # 3. 收集DomesticGatewayMonitor指标
            if self.domestic_gateway_monitor:
                try:
                    # 获取性能指标
                    performance_metrics = self.domestic_gateway_monitor.get_performance_summary()
                    all_metrics['domestic_gateway']['performance'] = performance_metrics
                    
                    # 获取活跃告警
                    active_alerts = self.domestic_gateway_monitor.get_active_alerts()
                    all_metrics['domestic_gateway']['alerts'] = [
                        {
                            'rule_id': alert.rule_id,
                            'message': alert.message,
                            'level': alert.level.value,
                            'timestamp': alert.timestamp.isoformat(),
                            'count': alert.count
                        }
                        for alert in active_alerts
                    ]
                    
                    # 获取统计信息
                    stats = self.domestic_gateway_monitor.get_statistics()
                    all_metrics['domestic_gateway']['statistics'] = stats
                    
                except Exception as e:
                    logger.error(f"收集DomesticGatewayMonitor指标失败: {e}")
                    all_metrics['domestic_gateway']['error'] = str(e)
            
            # 4. 收集告警信息
            alert_summary = alert_manager.get_alert_summary()
            all_metrics['alerts'] = alert_summary
            
            # 5. 转换为数值指标用于告警评估
            numeric_metrics = self._extract_numeric_metrics(all_metrics)
            
            # 6. 处理告警
            triggered_alerts = await alert_manager.process_metrics(numeric_metrics)
            if triggered_alerts:
                all_metrics['triggered_alerts'] = [
                    {
                        'name': alert.name,
                        'level': alert.level.value,
                        'metric': alert.metric_name,
                        'value': alert.current_value,
                        'threshold': alert.threshold_value
                    }
                    for alert in triggered_alerts
                ]
            
            self.last_metrics = all_metrics
            
        except Exception as e:
            logger.error(f"收集监控指标时出错: {e}")
            all_metrics['error'] = str(e)
        
        return all_metrics
    
    def _extract_numeric_metrics(self, all_metrics: Dict[str, Any]) -> Dict[str, float]:
        """从复杂指标结构中提取数值指标用于告警评估"""
        numeric_metrics = {}
        
        try:
            # 从系统指标中提取
            for metric in all_metrics.get('system', []):
                if isinstance(metric, dict) and 'name' in metric and 'value' in metric:
                    numeric_metrics[metric['name']] = float(metric['value'])
            
            # 从服务健康状态中提取
            services_health = all_metrics.get('services_health', {})
            if 'summary' in services_health:
                summary = services_health['summary']
                total = summary.get('total', 0)
                healthy = summary.get('healthy', 0)
                
                if total > 0:
                    numeric_metrics['service_availability'] = (healthy / total) * 100
                    numeric_metrics['unhealthy_services'] = summary.get('unhealthy', 0)
            
            # 从DomesticGateway指标中提取
            dg_metrics = all_metrics.get('domestic_gateway', {})
            if 'performance' in dg_metrics:
                perf = dg_metrics['performance']
                if isinstance(perf, dict):
                    for key, value in perf.items():
                        if isinstance(value, (int, float)):
                            numeric_metrics[f'gateway_{key}'] = float(value)
            
            # 从统计信息中提取
            if 'statistics' in dg_metrics:
                stats = dg_metrics['statistics']
                if isinstance(stats, dict):
                    for key, value in stats.items():
                        if isinstance(value, (int, float)):
                            numeric_metrics[f'gateway_stats_{key}'] = float(value)
            
            # 告警相关指标
            alerts = all_metrics.get('alerts', {})
            if isinstance(alerts, dict):
                numeric_metrics['active_alerts'] = alerts.get('total_active', 0)
                
                by_level = alerts.get('by_level', {})
                for level, count in by_level.items():
                    numeric_metrics[f'alerts_{level}'] = count
            
        except Exception as e:
            logger.error(f"提取数值指标时出错: {e}")
        
        return numeric_metrics
    
    async def get_monitoring_status(self) -> MonitoringStatus:
        """获取监控系统状态摘要"""
        try:
            # 获取最新指标
            if not self.last_metrics:
                await self.collect_all_metrics()
            
            # 服务健康状态
            services_health = self.last_metrics.get('services_health', {})
            summary = services_health.get('summary', {})
            
            services_total = summary.get('total', 0)
            services_up = summary.get('healthy', 0)
            
            # 系统整体健康状态
            if services_total == 0:
                system_health = "unknown"
            elif services_up == services_total:
                system_health = "healthy"
            elif services_up >= services_total * 0.8:  # 80%以上服务正常
                system_health = "warning"
            else:
                system_health = "critical"
            
            # 活跃告警数量
            alerts = self.last_metrics.get('alerts', {})
            active_alerts = alerts.get('total_active', 0)
            
            # 组件状态
            components = {
                'prometheus_exporter': True,
                'health_checker': True,
                'alert_manager': True,
                'domestic_gateway_monitor': self.domestic_gateway_monitor is not None
            }
            
            return MonitoringStatus(
                system_health=system_health,
                active_alerts=active_alerts,
                services_up=services_up,
                services_total=services_total,
                last_update=datetime.now(),
                components=components
            )
            
        except Exception as e:
            logger.error(f"获取监控状态时出错: {e}")
            return MonitoringStatus(
                system_health="error",
                active_alerts=0,
                services_up=0,
                services_total=0,
                last_update=datetime.now(),
                components={'error': str(e)}
            )
    
    async def start_monitoring(self, 
                              collection_interval: int = 30,
                              health_check_interval: int = 60,
                              alert_evaluation_interval: int = 60):
        """
        启动统一监控服务
        
        Args:
            collection_interval: 指标收集间隔(秒)
            health_check_interval: 健康检查间隔(秒)  
            alert_evaluation_interval: 告警评估间隔(秒)
        """
        if self.running:
            logger.warning("监控服务已在运行")
            return
        
        self.running = True
        logger.info("启动RedFire统一监控服务")
        
        # 启动各个监控组件
        tasks = []
        
        # 1. Prometheus指标收集
        tasks.append(asyncio.create_task(
            prometheus_exporter.start_collection_loop(collection_interval),
            name="prometheus_collection"
        ))
        
        # 2. 健康检查
        tasks.append(asyncio.create_task(
            health_checker.start_periodic_checks(health_check_interval),
            name="health_checks"
        ))
        
        # 3. DomesticGatewayMonitor
        if self.domestic_gateway_monitor:
            try:
                tasks.append(asyncio.create_task(
                    self.domestic_gateway_monitor.start_monitoring(),
                    name="domestic_gateway_monitor"
                ))
                logger.info("DomesticGatewayMonitor监控已启动")
            except Exception as e:
                logger.error(f"启动DomesticGatewayMonitor失败: {e}")
        
        # 4. 统一指标收集和告警评估
        tasks.append(asyncio.create_task(
            self._unified_monitoring_loop(alert_evaluation_interval),
            name="unified_monitoring"
        ))
        
        self.monitoring_tasks = tasks
        
        try:
            # 等待所有任务完成
            await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            logger.info("监控服务被取消")
        except Exception as e:
            logger.error(f"监控服务出错: {e}")
        finally:
            self.running = False
    
    async def _unified_monitoring_loop(self, interval: int):
        """统一监控循环"""
        logger.info(f"启动统一监控循环，间隔: {interval}秒")
        
        while self.running:
            try:
                start_time = time.time()
                
                # 收集所有指标
                metrics = await self.collect_all_metrics()
                
                # 记录收集统计
                collection_time = time.time() - start_time
                
                logger.debug(f"统一监控数据收集完成，耗时: {collection_time:.2f}秒")
                
                # 等待下次收集
                await asyncio.sleep(max(0, interval - collection_time))
                
            except Exception as e:
                logger.error(f"统一监控循环出错: {e}")
                await asyncio.sleep(interval)
    
    async def stop_monitoring(self):
        """停止监控服务"""
        if not self.running:
            return
        
        self.running = False
        logger.info("停止RedFire统一监控服务")
        
        # 取消所有监控任务
        for task in self.monitoring_tasks:
            if not task.done():
                task.cancel()
        
        # 等待任务完成
        if self.monitoring_tasks:
            await asyncio.gather(*self.monitoring_tasks, return_exceptions=True)
        
        # 停止DomesticGatewayMonitor
        if self.domestic_gateway_monitor:
            try:
                await self.domestic_gateway_monitor.stop_monitoring()
            except Exception as e:
                logger.error(f"停止DomesticGatewayMonitor失败: {e}")
        
        logger.info("统一监控服务已停止")
    
    def get_metrics_for_api(self) -> Dict[str, Any]:
        """获取用于API响应的监控指标"""
        if not self.last_metrics:
            return {'error': '暂无监控数据', 'timestamp': datetime.now().isoformat()}
        
        # 简化指标数据用于API响应
        api_metrics = {
            'timestamp': self.last_metrics.get('timestamp'),
            'system_health': self.last_metrics.get('services_health', {}).get('overall_status'),
            'services_summary': self.last_metrics.get('services_health', {}).get('summary'),
            'active_alerts': self.last_metrics.get('alerts', {}).get('total_active', 0),
            'components': {
                'prometheus': True,
                'health_check': True,
                'alert_manager': True,
                'domestic_gateway': self.domestic_gateway_monitor is not None
            }
        }
        
        # 添加关键指标
        if 'domestic_gateway' in self.last_metrics:
            dg_data = self.last_metrics['domestic_gateway']
            if 'performance' in dg_data:
                api_metrics['trading_performance'] = dg_data['performance']
        
        return api_metrics


# 全局统一监控实例
unified_monitor = UnifiedMonitor()


# FastAPI端点辅助函数
async def get_monitoring_metrics() -> Dict[str, Any]:
    """获取监控指标 (FastAPI端点使用)"""
    return unified_monitor.get_metrics_for_api()


async def get_monitoring_status() -> Dict[str, Any]:
    """获取监控状态 (FastAPI端点使用)"""
    status = await unified_monitor.get_monitoring_status()
    return asdict(status)


if __name__ == "__main__":
    # 测试代码
    async def main():
        monitor = UnifiedMonitor()
        
        print("收集统一监控指标...")
        metrics = await monitor.collect_all_metrics()
        
        print(f"\n监控数据摘要:")
        print(f"- 时间戳: {metrics.get('timestamp')}")
        print(f"- 系统指标数量: {len(metrics.get('system', []))}")
        print(f"- 服务健康状态: {metrics.get('services_health', {}).get('overall_status')}")
        print(f"- 活跃告警: {metrics.get('alerts', {}).get('total_active', 0)}")
        
        if 'domestic_gateway' in metrics:
            dg_data = metrics['domestic_gateway']
            print(f"- DomesticGateway状态: {'正常' if 'performance' in dg_data else '异常'}")
        
        print(f"\n监控状态:")
        status = await monitor.get_monitoring_status()
        print(f"- 系统健康: {status.system_health}")
        print(f"- 服务状态: {status.services_up}/{status.services_total}")
        print(f"- 组件状态: {status.components}")
    
    asyncio.run(main())
