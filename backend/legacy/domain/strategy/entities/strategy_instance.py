"""
策略实例实体
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional

from .strategy_config import StrategyConfig
from ..value_objects.strategy_status import StrategyStatus


@dataclass
class StrategyInstance:
    """策略实例实体"""
    instance_id: str
    config: StrategyConfig
    status: StrategyStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    stopped_at: Optional[datetime] = None
    strategy_object: Any = None  # 实际的策略对象
    performance: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.performance:
            self.performance = {
                "total_pnl": 0.0,
                "daily_pnl": 0.0,
                "position_pnl": 0.0,
                "trading_pnl": 0.0,
                "total_trades": 0,
                "win_rate": 0.0
            }
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "instance_id": self.instance_id,
            "config": self.config.to_dict(),
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "stopped_at": self.stopped_at.isoformat() if self.stopped_at else None,
            "performance": self.performance
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StrategyInstance":
        """从字典创建"""
        return cls(
            instance_id=data["instance_id"],
            config=StrategyConfig.from_dict(data["config"]),
            status=StrategyStatus(data["status"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            started_at=datetime.fromisoformat(data["started_at"]) if data.get("started_at") else None,
            stopped_at=datetime.fromisoformat(data["stopped_at"]) if data.get("stopped_at") else None,
            performance=data.get("performance", {})
        )
