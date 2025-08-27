"""
策略状态值对象
"""

from enum import Enum


class StrategyStatus(str, Enum):
    """策略状态"""
    INACTIVE = "inactive"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"
