"""
研究项目实体
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass, field
from uuid import uuid4
from enum import Enum


class ResearchPhase(str, Enum):
    """研究阶段"""
    IDEA_GENERATION = "idea_generation"
    DATA_EXPLORATION = "data_exploration"
    STRATEGY_DEVELOPMENT = "strategy_development"
    BACKTESTING = "backtesting"
    OPTIMIZATION = "optimization"
    RISK_ANALYSIS = "risk_analysis"
    PRODUCTION_READY = "production_ready"


class ProjectStatus(str, Enum):
    """项目状态"""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


@dataclass
class ResearchMetrics:
    """研究指标"""
    sharpe_ratio: Optional[float] = None
    max_drawdown: Optional[float] = None
    total_return: Optional[float] = None
    win_rate: Optional[float] = None
    profit_factor: Optional[float] = None
    calmar_ratio: Optional[float] = None
    sortino_ratio: Optional[float] = None
    var_95: Optional[float] = None
    cvar_95: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "sharpe_ratio": self.sharpe_ratio,
            "max_drawdown": self.max_drawdown,
            "total_return": self.total_return,
            "win_rate": self.win_rate,
            "profit_factor": self.profit_factor,
            "calmar_ratio": self.calmar_ratio,
            "sortino_ratio": self.sortino_ratio,
            "var_95": self.var_95,
            "cvar_95": self.cvar_95
        }


@dataclass
class ResearchProject:
    """
    研究项目实体
    
    聚合根，管理量化研究项目的完整生命周期
    """
    project_id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    description: str = ""
    phase: ResearchPhase = ResearchPhase.IDEA_GENERATION
    status: ProjectStatus = ProjectStatus.ACTIVE
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    # 研究配置
    symbols: List[str] = field(default_factory=list)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    initial_capital: float = 1000000.0
    
    # 策略代码和配置
    strategy_code: str = ""
    strategy_config: Dict[str, Any] = field(default_factory=dict)
    
    # 研究结果
    metrics: ResearchMetrics = field(default_factory=ResearchMetrics)
    
    # 元数据
    tags: List[str] = field(default_factory=list)
    notes: str = ""
    
    def advance_phase(self) -> None:
        """推进到下一个研究阶段"""
        phases = list(ResearchPhase)
        current_index = phases.index(self.phase)
        
        if current_index < len(phases) - 1:
            self.phase = phases[current_index + 1]
            self.updated_at = datetime.now()
    
    def update_metrics(self, metrics: ResearchMetrics) -> None:
        """更新研究指标"""
        self.metrics = metrics
        self.updated_at = datetime.now()
    
    def add_tag(self, tag: str) -> None:
        """添加标签"""
        if tag not in self.tags:
            self.tags.append(tag)
            self.updated_at = datetime.now()
    
    def remove_tag(self, tag: str) -> None:
        """移除标签"""
        if tag in self.tags:
            self.tags.remove(tag)
            self.updated_at = datetime.now()
    
    def update_strategy(self, code: str, config: Dict[str, Any]) -> None:
        """更新策略代码和配置"""
        self.strategy_code = code
        self.strategy_config = config
        self.updated_at = datetime.now()
    
    def activate(self) -> None:
        """激活项目"""
        self.status = ProjectStatus.ACTIVE
        self.updated_at = datetime.now()
    
    def pause(self) -> None:
        """暂停项目"""
        self.status = ProjectStatus.PAUSED
        self.updated_at = datetime.now()
    
    def complete(self) -> None:
        """完成项目"""
        self.status = ProjectStatus.COMPLETED
        self.phase = ResearchPhase.PRODUCTION_READY
        self.updated_at = datetime.now()
    
    def archive(self) -> None:
        """归档项目"""
        self.status = ProjectStatus.ARCHIVED
        self.updated_at = datetime.now()
    
    @property
    def is_active(self) -> bool:
        """是否为活跃状态"""
        return self.status == ProjectStatus.ACTIVE
    
    @property
    def progress_percentage(self) -> float:
        """计算进度百分比"""
        phases = list(ResearchPhase)
        current_index = phases.index(self.phase)
        return (current_index + 1) / len(phases) * 100
    
    @property
    def has_strategy(self) -> bool:
        """是否包含策略代码"""
        return len(self.strategy_code.strip()) > 0
    
    @property
    def has_symbols(self) -> bool:
        """是否设置了交易品种"""
        return len(self.symbols) > 0
    
    @property
    def duration_days(self) -> Optional[int]:
        """研究时间跨度（天数）"""
        if self.start_date and self.end_date:
            return (self.end_date - self.start_date).days
        return None
