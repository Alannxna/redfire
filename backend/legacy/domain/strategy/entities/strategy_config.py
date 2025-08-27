"""
策略配置实体
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List

from ..value_objects.strategy_type import StrategyType


@dataclass
class StrategyConfig:
    """策略配置实体"""
    strategy_name: str
    strategy_class: str
    strategy_type: StrategyType
    symbol_list: List[str]
    parameters: Dict[str, Any]
    auto_start: bool = False
    risk_limits: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.risk_limits:
            self.risk_limits = {
                "max_position": 1000000,
                "max_daily_loss": 50000,
                "max_total_loss": 100000
            }
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "strategy_name": self.strategy_name,
            "strategy_class": self.strategy_class,
            "strategy_type": self.strategy_type.value,
            "symbol_list": self.symbol_list,
            "parameters": self.parameters,
            "auto_start": self.auto_start,
            "risk_limits": self.risk_limits
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StrategyConfig":
        """从字典创建"""
        return cls(
            strategy_name=data["strategy_name"],
            strategy_class=data["strategy_class"],
            strategy_type=StrategyType(data["strategy_type"]),
            symbol_list=data["symbol_list"],
            parameters=data["parameters"],
            auto_start=data.get("auto_start", False),
            risk_limits=data.get("risk_limits", {})
        )
