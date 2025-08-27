"""
策略领域实体
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid


class StrategyStatus(str, Enum):
    """策略状态"""
    INACTIVE = "inactive"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


class StrategyType(str, Enum):
    """策略类型"""
    CTA = "cta"
    PORTFOLIO = "portfolio"
    SPREAD = "spread"
    OPTION = "option"
    SCRIPT = "script"
    CUSTOM = "custom"


@dataclass
class StrategyPerformance:
    """策略绩效数据"""
    total_pnl: float = 0.0
    daily_pnl: float = 0.0
    position_pnl: float = 0.0
    trading_pnl: float = 0.0
    total_trades: int = 0
    win_rate: float = 0.0
    max_drawdown: float = 0.0
    sharpe_ratio: float = 0.0
    updated_at: datetime = field(default_factory=datetime.now)
    
    def update_metrics(self, metrics: Dict[str, Any]) -> None:
        """更新绩效指标"""
        for key, value in metrics.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "total_pnl": self.total_pnl,
            "daily_pnl": self.daily_pnl,
            "position_pnl": self.position_pnl,
            "trading_pnl": self.trading_pnl,
            "total_trades": self.total_trades,
            "win_rate": self.win_rate,
            "max_drawdown": self.max_drawdown,
            "sharpe_ratio": self.sharpe_ratio,
            "updated_at": self.updated_at.isoformat()
        }


@dataclass
class RiskLimits:
    """风险限制配置"""
    max_position: float = 1000000
    max_daily_loss: float = 50000
    max_total_loss: float = 100000
    position_limits: Dict[str, float] = field(default_factory=dict)
    time_limits: Dict[str, str] = field(default_factory=dict)
    
    def check_position_limit(self, symbol: str, target_pos: float) -> bool:
        """检查持仓限制"""
        max_pos = self.position_limits.get(symbol, self.max_position)
        return abs(target_pos) <= max_pos
    
    def check_pnl_limit(self, current_pnl: float) -> bool:
        """检查盈亏限制"""
        return current_pnl > -self.max_daily_loss
    
    def check_time_limit(self) -> bool:
        """检查时间限制"""
        if not self.time_limits:
            return True
        
        start_time = self.time_limits.get("start_time")
        end_time = self.time_limits.get("end_time")
        
        if start_time and end_time:
            now = datetime.now()
            start_dt = datetime.strptime(start_time, "%H:%M:%S").time()
            end_dt = datetime.strptime(end_time, "%H:%M:%S").time()
            current_time = now.time()
            
            return start_dt <= current_time <= end_dt
        
        return True


@dataclass
class StrategyConfiguration:
    """策略配置"""
    strategy_name: str
    strategy_class: str
    strategy_type: StrategyType
    symbol_list: List[str]
    parameters: Dict[str, Any]
    auto_start: bool = False
    risk_limits: RiskLimits = field(default_factory=RiskLimits)
    
    def __post_init__(self):
        if isinstance(self.risk_limits, dict):
            self.risk_limits = RiskLimits(**self.risk_limits)
    
    def validate(self) -> List[str]:
        """验证配置的有效性"""
        errors = []
        
        if not self.strategy_name:
            errors.append("策略名称不能为空")
        
        if not self.strategy_class:
            errors.append("策略类不能为空")
        
        if not self.symbol_list:
            errors.append("交易品种列表不能为空")
        
        if not isinstance(self.parameters, dict):
            errors.append("参数必须是字典类型")
        
        return errors
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "strategy_name": self.strategy_name,
            "strategy_class": self.strategy_class,
            "strategy_type": self.strategy_type.value,
            "symbol_list": self.symbol_list,
            "parameters": self.parameters,
            "auto_start": self.auto_start,
            "risk_limits": self.risk_limits.__dict__
        }


@dataclass
class StrategyInstance:
    """策略实例"""
    instance_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    configuration: StrategyConfiguration = None
    status: StrategyStatus = StrategyStatus.INACTIVE
    performance: StrategyPerformance = field(default_factory=StrategyPerformance)
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    stopped_at: Optional[datetime] = None
    error_message: Optional[str] = None
    vnpy_strategy_object: Any = None  # VnPy策略对象引用
    
    def start(self) -> None:
        """启动策略"""
        if self.status != StrategyStatus.INACTIVE:
            raise ValueError(f"策略状态错误，无法启动: {self.status}")
        
        self.status = StrategyStatus.STARTING
        self.started_at = datetime.now()
        self.error_message = None
    
    def mark_running(self) -> None:
        """标记为运行中"""
        if self.status != StrategyStatus.STARTING:
            raise ValueError(f"策略状态错误，无法标记为运行中: {self.status}")
        
        self.status = StrategyStatus.RUNNING
    
    def stop(self) -> None:
        """停止策略"""
        if self.status not in [StrategyStatus.RUNNING, StrategyStatus.STARTING]:
            raise ValueError(f"策略状态错误，无法停止: {self.status}")
        
        self.status = StrategyStatus.STOPPING
    
    def mark_stopped(self) -> None:
        """标记为已停止"""
        if self.status != StrategyStatus.STOPPING:
            raise ValueError(f"策略状态错误，无法标记为已停止: {self.status}")
        
        self.status = StrategyStatus.STOPPED
        self.stopped_at = datetime.now()
    
    def mark_error(self, error_message: str) -> None:
        """标记为错误状态"""
        self.status = StrategyStatus.ERROR
        self.error_message = error_message
    
    def update_performance(self, metrics: Dict[str, Any]) -> None:
        """更新绩效数据"""
        self.performance.update_metrics(metrics)
    
    def check_risk_limits(self) -> bool:
        """检查风险限制"""
        if not self.configuration:
            return False
        
        # 检查时间限制
        if not self.configuration.risk_limits.check_time_limit():
            return False
        
        # 检查盈亏限制
        if not self.configuration.risk_limits.check_pnl_limit(self.performance.daily_pnl):
            return False
        
        return True
    
    def can_start(self) -> bool:
        """检查是否可以启动"""
        return (
            self.status == StrategyStatus.INACTIVE and
            self.configuration is not None and
            len(self.configuration.validate()) == 0
        )
    
    def can_stop(self) -> bool:
        """检查是否可以停止"""
        return self.status in [StrategyStatus.RUNNING, StrategyStatus.STARTING]
    
    def is_running(self) -> bool:
        """检查是否正在运行"""
        return self.status == StrategyStatus.RUNNING
    
    def is_active(self) -> bool:
        """检查是否处于活跃状态"""
        return self.status in [StrategyStatus.STARTING, StrategyStatus.RUNNING, StrategyStatus.STOPPING]
    
    def get_runtime_duration(self) -> Optional[int]:
        """获取运行时长（秒）"""
        if not self.started_at:
            return None
        
        end_time = self.stopped_at or datetime.now()
        return int((end_time - self.started_at).total_seconds())
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "instance_id": self.instance_id,
            "configuration": self.configuration.to_dict() if self.configuration else None,
            "status": self.status.value,
            "performance": self.performance.to_dict(),
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "stopped_at": self.stopped_at.isoformat() if self.stopped_at else None,
            "error_message": self.error_message,
            "runtime_duration": self.get_runtime_duration()
        }


@dataclass
class RiskEvent:
    """风险事件"""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    instance_id: str = ""
    strategy_name: str = ""
    event_type: str = ""
    description: str = ""
    severity: str = "warning"  # info, warning, error, critical
    action_taken: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    resolved: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "event_id": self.event_id,
            "instance_id": self.instance_id,
            "strategy_name": self.strategy_name,
            "event_type": self.event_type,
            "description": self.description,
            "severity": self.severity,
            "action_taken": self.action_taken,
            "timestamp": self.timestamp.isoformat(),
            "resolved": self.resolved
        }
