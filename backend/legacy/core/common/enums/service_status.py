"""
统一服务状态枚举
================

全项目唯一的服务状态定义，所有服务必须使用此枚举
"""

from enum import Enum


class ServiceStatus(Enum):
    """统一的服务状态枚举 - 全项目唯一定义"""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    PAUSED = "paused"
    ERROR = "error"

    def __str__(self):
        return self.value

    @property
    def is_active(self) -> bool:
        """判断服务是否处于活跃状态"""
        return self in [ServiceStatus.STARTING, ServiceStatus.RUNNING]

    @property
    def is_stopped(self) -> bool:
        """判断服务是否已停止"""
        return self == ServiceStatus.STOPPED

    @property
    def is_running(self) -> bool:
        """判断服务是否正在运行"""
        return self == ServiceStatus.RUNNING

    @property
    def has_error(self) -> bool:
        """判断服务是否有错误"""
        return self == ServiceStatus.ERROR
