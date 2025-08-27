"""
简化监控服务实现
用于测试和开发环境
"""

from typing import Dict, Any, Optional
from .monitor_service import MonitorService


class SimpleMonitorService(MonitorService):
    """简化的监控服务实现"""
    
    def __init__(self):
        # 创建默认配置
        from ...base.infrastructure_service import InfrastructureServiceConfig
        config = InfrastructureServiceConfig(
            service_name="simple_monitor"
        )
        super().__init__(config)
        self._metrics: Dict[str, Any] = {}
        self._connected = False
    
    def _create_connection_impl(self) -> Any:
        """创建连接实现"""
        self._connected = True
        return {"status": "connected", "type": "simple"}
    
    def _close_connection_impl(self) -> None:
        """关闭连接实现"""
        self._connected = False
    
    def record_metric(self, name: str, value: Any, tags: Optional[Dict[str, str]] = None) -> None:
        """记录指标"""
        self._metrics[name] = {
            "value": value,
            "tags": tags or {},
            "timestamp": self._get_current_timestamp()
        }
    
    def get_metric(self, name: str) -> Optional[Dict[str, Any]]:
        """获取指标"""
        return self._metrics.get(name)
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """获取所有指标"""
        return self._metrics.copy()
    
    def is_healthy(self) -> bool:
        """检查服务健康状态"""
        return self._connected
    
    def clear_metrics(self) -> None:
        """清空指标"""
        self._metrics.clear()
