"""
回测实体
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass, field
from uuid import uuid4
from enum import Enum
import json


class BacktestStatus(str, Enum):
    """回测状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class BacktestType(str, Enum):
    """回测类型"""
    SINGLE_STRATEGY = "single_strategy"
    PORTFOLIO = "portfolio"
    OPTIMIZATION = "optimization"
    WALK_FORWARD = "walk_forward"
    MONTE_CARLO = "monte_carlo"


@dataclass
class BacktestConfiguration:
    """回测配置"""
    start_date: datetime
    end_date: datetime
    initial_capital: float
    symbols: List[str]
    benchmark: Optional[str] = None
    commission: float = 0.0003
    slippage: float = 0.0001
    max_position_size: float = 1.0
    risk_free_rate: float = 0.03
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "initial_capital": self.initial_capital,
            "symbols": self.symbols,
            "benchmark": self.benchmark,
            "commission": self.commission,
            "slippage": self.slippage,
            "max_position_size": self.max_position_size,
            "risk_free_rate": self.risk_free_rate
        }


@dataclass
class BacktestResult:
    """回测结果"""
    total_return: float = 0.0
    annual_return: float = 0.0
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    calmar_ratio: float = 0.0
    max_drawdown: float = 0.0
    max_drawdown_duration: int = 0
    volatility: float = 0.0
    skewness: float = 0.0
    kurtosis: float = 0.0
    var_95: float = 0.0
    cvar_95: float = 0.0
    
    # 交易统计
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    profit_factor: float = 0.0
    
    # 时间序列数据
    equity_curve: List[Dict[str, Any]] = field(default_factory=list)
    trade_list: List[Dict[str, Any]] = field(default_factory=list)
    daily_returns: List[float] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "performance_metrics": {
                "total_return": self.total_return,
                "annual_return": self.annual_return,
                "sharpe_ratio": self.sharpe_ratio,
                "sortino_ratio": self.sortino_ratio,
                "calmar_ratio": self.calmar_ratio,
                "max_drawdown": self.max_drawdown,
                "max_drawdown_duration": self.max_drawdown_duration,
                "volatility": self.volatility,
                "skewness": self.skewness,
                "kurtosis": self.kurtosis,
                "var_95": self.var_95,
                "cvar_95": self.cvar_95
            },
            "trade_statistics": {
                "total_trades": self.total_trades,
                "winning_trades": self.winning_trades,
                "losing_trades": self.losing_trades,
                "win_rate": self.win_rate,
                "avg_win": self.avg_win,
                "avg_loss": self.avg_loss,
                "profit_factor": self.profit_factor
            },
            "time_series": {
                "equity_curve": self.equity_curve,
                "trade_list": self.trade_list,
                "daily_returns": self.daily_returns
            }
        }


@dataclass
class Backtest:
    """
    回测实体
    
    管理策略回测的完整生命周期
    """
    backtest_id: str = field(default_factory=lambda: str(uuid4()))
    project_id: str = ""
    name: str = ""
    description: str = ""
    backtest_type: BacktestType = BacktestType.SINGLE_STRATEGY
    status: BacktestStatus = BacktestStatus.PENDING
    
    # 时间信息
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # 配置和代码
    configuration: Optional[BacktestConfiguration] = None
    strategy_code: str = ""
    strategy_config: Dict[str, Any] = field(default_factory=dict)
    
    # 结果和错误
    result: Optional[BacktestResult] = None
    error_message: Optional[str] = None
    progress: float = 0.0
    
    # 元数据
    tags: List[str] = field(default_factory=list)
    
    def start(self) -> None:
        """开始回测"""
        self.status = BacktestStatus.RUNNING
        self.started_at = datetime.now()
        self.progress = 0.0
    
    def complete(self, result: BacktestResult) -> None:
        """完成回测"""
        self.status = BacktestStatus.COMPLETED
        self.completed_at = datetime.now()
        self.result = result
        self.progress = 100.0
    
    def fail(self, error_message: str) -> None:
        """回测失败"""
        self.status = BacktestStatus.FAILED
        self.completed_at = datetime.now()
        self.error_message = error_message
    
    def cancel(self) -> None:
        """取消回测"""
        self.status = BacktestStatus.CANCELLED
        self.completed_at = datetime.now()
    
    def update_progress(self, progress: float) -> None:
        """更新进度"""
        self.progress = max(0.0, min(100.0, progress))
    
    @property
    def is_running(self) -> bool:
        """是否正在运行"""
        return self.status == BacktestStatus.RUNNING
    
    @property
    def is_completed(self) -> bool:
        """是否已完成"""
        return self.status == BacktestStatus.COMPLETED
    
    @property
    def is_failed(self) -> bool:
        """是否失败"""
        return self.status == BacktestStatus.FAILED
    
    @property
    def duration_seconds(self) -> Optional[float]:
        """运行时长（秒）"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        elif self.started_at:
            return (datetime.now() - self.started_at).total_seconds()
        return None
    
    @property
    def has_result(self) -> bool:
        """是否有结果"""
        return self.result is not None
    
    def get_summary(self) -> Dict[str, Any]:
        """获取回测摘要"""
        summary = {
            "backtest_id": self.backtest_id,
            "name": self.name,
            "status": self.status.value,
            "progress": self.progress,
            "created_at": self.created_at.isoformat(),
            "duration_seconds": self.duration_seconds
        }
        
        if self.result:
            summary["performance"] = {
                "total_return": self.result.total_return,
                "sharpe_ratio": self.result.sharpe_ratio,
                "max_drawdown": self.result.max_drawdown,
                "win_rate": self.result.win_rate
            }
        
        if self.error_message:
            summary["error"] = self.error_message
        
        return summary
