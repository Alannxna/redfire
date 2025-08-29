"""
量化策略绩效分析系统

提供全面的策略绩效分析功能，包括：
- 实时绩效监控和计算
- 多维度绩效指标体系
- 基准比较和归因分析
- 风险调整收益计算
- 绩效报告生成
- 历史绩效追踪
"""

import logging
import asyncio
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from decimal import Decimal
import uuid
from scipy import stats
import math

from .strategy_base import (
    BaseStrategy, StrategyConfig, MarketData, OrderInfo, TradeInfo, 
    PositionInfo, OrderSide, OrderType, PositionSide
)


class PerformanceFrequency(Enum):
    """绩效计算频率"""
    REALTIME = "realtime"    # 实时
    MINUTELY = "minutely"    # 分钟级
    HOURLY = "hourly"        # 小时级
    DAILY = "daily"          # 日级
    WEEKLY = "weekly"        # 周级
    MONTHLY = "monthly"      # 月级


class BenchmarkType(Enum):
    """基准类型"""
    INDEX = "index"          # 指数基准
    STRATEGY = "strategy"    # 策略基准
    RISK_FREE = "risk_free"  # 无风险利率
    CUSTOM = "custom"        # 自定义基准


@dataclass
class PerformanceMetrics:
    """绩效指标"""
    # 基础收益指标
    total_return: float = 0.0
    annual_return: float = 0.0
    daily_return: float = 0.0
    cumulative_return: float = 0.0
    
    # 风险指标
    volatility: float = 0.0
    downside_volatility: float = 0.0
    tracking_error: float = 0.0
    
    # 风险调整收益
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    calmar_ratio: float = 0.0
    information_ratio: float = 0.0
    treynor_ratio: float = 0.0
    
    # 回撤指标
    max_drawdown: float = 0.0
    max_drawdown_duration: int = 0
    recovery_factor: float = 0.0
    pain_index: float = 0.0
    
    # 交易指标
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0
    
    # 盈亏指标
    profit_factor: float = 0.0
    expectancy: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    largest_win: float = 0.0
    largest_loss: float = 0.0
    
    # 稳定性指标
    stability: float = 0.0
    tail_ratio: float = 0.0
    skewness: float = 0.0
    kurtosis: float = 0.0
    
    # 其他指标
    alpha: float = 0.0
    beta: float = 0.0
    r_squared: float = 0.0
    var_95: float = 0.0
    cvar_95: float = 0.0


@dataclass
class PerformanceConfig:
    """绩效分析配置"""
    # 基准配置
    benchmark_symbol: Optional[str] = None
    benchmark_type: BenchmarkType = BenchmarkType.INDEX
    risk_free_rate: float = 0.03
    
    # 计算配置
    frequency: PerformanceFrequency = PerformanceFrequency.DAILY
    lookback_period: int = 252  # 回看期（交易日）
    
    # VaR配置
    var_confidence_level: float = 0.95
    var_method: str = "historical"  # historical, parametric, monte_carlo
    
    # 基准比较
    enable_benchmark_comparison: bool = True
    enable_sector_comparison: bool = False
    
    # 报告配置
    enable_detailed_analysis: bool = True
    generate_charts: bool = True
    export_format: str = "html"  # html, pdf, excel
    
    # 实时更新
    update_interval: int = 300  # 更新间隔（秒）
    enable_realtime_alerts: bool = True
    
    # 历史保存
    save_history: bool = True
    history_retention_days: int = 365


class PerformanceAnalyzer:
    """
    绩效分析器
    
    提供全面的策略绩效分析功能，包括实时监控、
    指标计算、基准比较和报告生成。
    """
    
    def __init__(self, config: Optional[PerformanceConfig] = None):
        """
        初始化绩效分析器
        
        Args:
            config: 绩效分析配置
        """
        self.config = config or PerformanceConfig()
        self.analyzer_id = str(uuid.uuid4())
        
        # 日志记录
        self.logger = logging.getLogger(f"performance_analyzer.{self.analyzer_id}")
        
        # 策略管理
        self._strategies: Dict[str, BaseStrategy] = {}
        self._strategy_metrics: Dict[str, PerformanceMetrics] = {}
        
        # 数据管理
        self._price_data: Dict[str, pd.DataFrame] = {}
        self._benchmark_data: Optional[pd.Series] = None
        self._market_data: Dict[str, MarketData] = {}
        
        # 绩效数据
        self._equity_curves: Dict[str, pd.DataFrame] = {}
        self._returns_series: Dict[str, pd.Series] = {}
        self._drawdown_series: Dict[str, pd.Series] = {}
        
        # 交易分析
        self._trade_analysis: Dict[str, Dict[str, Any]] = {}
        self._position_analysis: Dict[str, Dict[str, Any]] = {}
        
        # 基准比较
        self._benchmark_returns: Optional[pd.Series] = None
        self._alpha_beta_cache: Dict[str, Tuple[float, float]] = {}
        
        # 监控任务
        self._monitoring_task: Optional[asyncio.Task] = None
        self._is_monitoring = False
        
        # 历史记录
        self._performance_history: Dict[str, List[Dict[str, Any]]] = {}
        
        self.logger.info(f"绩效分析器初始化完成: {self.analyzer_id}")
    
    # ==================== 策略管理 ====================
    
    def add_strategy(self, strategy: BaseStrategy) -> bool:
        """添加策略到绩效分析"""
        try:
            strategy_id = strategy.strategy_id
            
            if strategy_id in self._strategies:
                self.logger.warning(f"策略已存在: {strategy_id}")
                return False
            
            self._strategies[strategy_id] = strategy
            self._strategy_metrics[strategy_id] = PerformanceMetrics()
            self._equity_curves[strategy_id] = pd.DataFrame()
            self._returns_series[strategy_id] = pd.Series(dtype=float)
            self._drawdown_series[strategy_id] = pd.Series(dtype=float)
            self._trade_analysis[strategy_id] = {}
            self._position_analysis[strategy_id] = {}
            self._performance_history[strategy_id] = []
            
            self.logger.info(f"策略添加到绩效分析: {strategy_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"添加策略失败: {e}")
            return False
    
    def remove_strategy(self, strategy_id: str) -> bool:
        """从绩效分析移除策略"""
        try:
            if strategy_id not in self._strategies:
                self.logger.warning(f"策略不存在: {strategy_id}")
                return False
            
            # 清理策略数据
            del self._strategies[strategy_id]
            del self._strategy_metrics[strategy_id]
            del self._equity_curves[strategy_id]
            del self._returns_series[strategy_id]
            del self._drawdown_series[strategy_id]
            del self._trade_analysis[strategy_id]
            del self._position_analysis[strategy_id]
            del self._performance_history[strategy_id]
            
            if strategy_id in self._alpha_beta_cache:
                del self._alpha_beta_cache[strategy_id]
            
            self.logger.info(f"策略从绩效分析移除: {strategy_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"移除策略失败: {e}")
            return False
    
    # ==================== 数据管理 ====================
    
    def set_benchmark_data(self, benchmark_data: pd.Series):
        """设置基准数据"""
        try:
            self._benchmark_data = benchmark_data.copy()
            self._benchmark_returns = benchmark_data.pct_change().dropna()
            
            self.logger.info("基准数据设置完成")
            
        except Exception as e:
            self.logger.error(f"设置基准数据失败: {e}")
    
    async def update_market_data(self, data: MarketData):
        """更新市场数据"""
        try:
            self._market_data[data.symbol] = data
            
            # 更新价格历史
            if data.symbol not in self._price_data:
                self._price_data[data.symbol] = pd.DataFrame()
            
            # 添加新数据点
            new_row = pd.DataFrame({
                'timestamp': [data.timestamp],
                'open': [data.open],
                'high': [data.high],
                'low': [data.low],
                'close': [data.close],
                'volume': [data.volume]
            })
            new_row.set_index('timestamp', inplace=True)
            
            self._price_data[data.symbol] = pd.concat([self._price_data[data.symbol], new_row])
            
            # 限制历史数据长度
            if len(self._price_data[data.symbol]) > 10000:
                self._price_data[data.symbol] = self._price_data[data.symbol].tail(5000)
                
        except Exception as e:
            self.logger.error(f"更新市场数据失败: {e}")
    
    # ==================== 绩效监控 ====================
    
    async def start_monitoring(self) -> bool:
        """启动绩效监控"""
        try:
            if self._is_monitoring:
                self.logger.warning("绩效监控已在运行")
                return True
            
            self._is_monitoring = True
            self._monitoring_task = asyncio.create_task(self._monitor_performance())
            
            self.logger.info("绩效监控启动成功")
            return True
            
        except Exception as e:
            self.logger.error(f"启动绩效监控失败: {e}")
            return False
    
    async def stop_monitoring(self) -> bool:
        """停止绩效监控"""
        try:
            self._is_monitoring = False
            
            if self._monitoring_task:
                self._monitoring_task.cancel()
            
            self.logger.info("绩效监控停止")
            return True
            
        except Exception as e:
            self.logger.error(f"停止绩效监控失败: {e}")
            return False
    
    async def _monitor_performance(self):
        """绩效监控主循环"""
        try:
            while self._is_monitoring:
                # 更新所有策略的绩效指标
                for strategy_id in self._strategies.keys():
                    await self._update_strategy_performance(strategy_id)
                
                # 保存历史记录
                if self.config.save_history:
                    await self._save_performance_history()
                
                await asyncio.sleep(self.config.update_interval)
                
        except asyncio.CancelledError:
            pass
        except Exception as e:
            self.logger.error(f"绩效监控异常: {e}")
    
    async def _update_strategy_performance(self, strategy_id: str):
        """更新策略绩效"""
        try:
            if strategy_id not in self._strategies:
                return
            
            strategy = self._strategies[strategy_id]
            
            # 更新权益曲线
            await self._update_equity_curve(strategy_id, strategy)
            
            # 计算收益率序列
            await self._update_returns_series(strategy_id)
            
            # 计算回撤序列
            await self._update_drawdown_series(strategy_id)
            
            # 分析交易数据
            await self._analyze_trades(strategy_id, strategy)
            
            # 计算绩效指标
            metrics = await self._calculate_performance_metrics(strategy_id, strategy)
            self._strategy_metrics[strategy_id] = metrics
            
        except Exception as e:
            self.logger.error(f"更新策略绩效失败 {strategy_id}: {e}")
    
    async def _update_equity_curve(self, strategy_id: str, strategy: BaseStrategy):
        """更新权益曲线"""
        try:
            current_time = datetime.now()
            current_equity = float(strategy.account_balance)
            
            # 添加新的权益点
            new_point = pd.DataFrame({
                'timestamp': [current_time],
                'equity': [current_equity],
                'total_pnl': [float(strategy.total_pnl)],
                'unrealized_pnl': [sum(float(pos.unrealized_pnl) for pos in strategy.get_all_positions().values())],
                'cash': [float(strategy.available_balance)]
            })
            new_point.set_index('timestamp', inplace=True)
            
            if self._equity_curves[strategy_id].empty:
                self._equity_curves[strategy_id] = new_point
            else:
                self._equity_curves[strategy_id] = pd.concat([self._equity_curves[strategy_id], new_point])
            
            # 限制数据长度
            if len(self._equity_curves[strategy_id]) > 10000:
                self._equity_curves[strategy_id] = self._equity_curves[strategy_id].tail(5000)
                
        except Exception as e:
            self.logger.error(f"更新权益曲线失败: {e}")
    
    async def _update_returns_series(self, strategy_id: str):
        """更新收益率序列"""
        try:
            equity_curve = self._equity_curves[strategy_id]
            
            if len(equity_curve) < 2:
                return
            
            # 计算收益率
            returns = equity_curve['equity'].pct_change().dropna()
            self._returns_series[strategy_id] = returns
            
        except Exception as e:
            self.logger.error(f"更新收益率序列失败: {e}")
    
    async def _update_drawdown_series(self, strategy_id: str):
        """更新回撤序列"""
        try:
            equity_curve = self._equity_curves[strategy_id]
            
            if equity_curve.empty:
                return
            
            # 计算回撤
            peak = equity_curve['equity'].cummax()
            drawdown = (equity_curve['equity'] - peak) / peak
            self._drawdown_series[strategy_id] = drawdown
            
        except Exception as e:
            self.logger.error(f"更新回撤序列失败: {e}")
    
    # ==================== 绩效指标计算 ====================
    
    async def _calculate_performance_metrics(self, strategy_id: str, strategy: BaseStrategy) -> PerformanceMetrics:
        """计算绩效指标"""
        try:
            metrics = PerformanceMetrics()
            
            returns = self._returns_series[strategy_id]
            equity_curve = self._equity_curves[strategy_id]
            
            if len(returns) < 2:
                return metrics
            
            # 基础收益指标
            metrics.total_return = self._calculate_total_return(equity_curve)
            metrics.annual_return = self._calculate_annual_return(returns)
            metrics.daily_return = returns.mean()
            metrics.cumulative_return = (1 + returns).cumprod().iloc[-1] - 1 if len(returns) > 0 else 0
            
            # 风险指标
            metrics.volatility = self._calculate_volatility(returns)
            metrics.downside_volatility = self._calculate_downside_volatility(returns)
            metrics.tracking_error = self._calculate_tracking_error(returns)
            
            # 风险调整收益
            metrics.sharpe_ratio = self._calculate_sharpe_ratio(returns)
            metrics.sortino_ratio = self._calculate_sortino_ratio(returns)
            metrics.calmar_ratio = self._calculate_calmar_ratio(metrics.annual_return, metrics.max_drawdown)
            metrics.information_ratio = self._calculate_information_ratio(returns)
            
            # 回撤指标
            drawdown_metrics = self._calculate_drawdown_metrics(self._drawdown_series[strategy_id])
            metrics.max_drawdown = drawdown_metrics['max_drawdown']
            metrics.max_drawdown_duration = drawdown_metrics['max_duration']
            metrics.recovery_factor = drawdown_metrics['recovery_factor']
            metrics.pain_index = drawdown_metrics['pain_index']
            
            # 交易指标
            trade_metrics = await self._calculate_trade_metrics(strategy_id, strategy)
            metrics.total_trades = trade_metrics['total_trades']
            metrics.winning_trades = trade_metrics['winning_trades']
            metrics.losing_trades = trade_metrics['losing_trades']
            metrics.win_rate = trade_metrics['win_rate']
            metrics.profit_factor = trade_metrics['profit_factor']
            metrics.expectancy = trade_metrics['expectancy']
            metrics.avg_win = trade_metrics['avg_win']
            metrics.avg_loss = trade_metrics['avg_loss']
            metrics.largest_win = trade_metrics['largest_win']
            metrics.largest_loss = trade_metrics['largest_loss']
            
            # 稳定性指标
            metrics.stability = self._calculate_stability(returns)
            metrics.tail_ratio = self._calculate_tail_ratio(returns)
            metrics.skewness = self._calculate_skewness(returns)
            metrics.kurtosis = self._calculate_kurtosis(returns)
            
            # Alpha/Beta
            if self._benchmark_returns is not None and len(self._benchmark_returns) > 0:
                alpha_beta = self._calculate_alpha_beta(returns)
                metrics.alpha = alpha_beta['alpha']
                metrics.beta = alpha_beta['beta']
                metrics.r_squared = alpha_beta['r_squared']
            
            # VaR
            var_metrics = self._calculate_var(returns)
            metrics.var_95 = var_metrics['var_95']
            metrics.cvar_95 = var_metrics['cvar_95']
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"计算绩效指标失败: {e}")
            return PerformanceMetrics()
    
    def _calculate_total_return(self, equity_curve: pd.DataFrame) -> float:
        """计算总收益率"""
        try:
            if equity_curve.empty:
                return 0.0
            
            initial_equity = equity_curve['equity'].iloc[0]
            final_equity = equity_curve['equity'].iloc[-1]
            
            if initial_equity > 0:
                return (final_equity - initial_equity) / initial_equity
            return 0.0
            
        except Exception as e:
            self.logger.error(f"计算总收益率失败: {e}")
            return 0.0
    
    def _calculate_annual_return(self, returns: pd.Series) -> float:
        """计算年化收益率"""
        try:
            if len(returns) == 0:
                return 0.0
            
            # 根据数据频率确定年化因子
            if self.config.frequency == PerformanceFrequency.DAILY:
                periods_per_year = 252
            elif self.config.frequency == PerformanceFrequency.HOURLY:
                periods_per_year = 252 * 24
            elif self.config.frequency == PerformanceFrequency.MINUTELY:
                periods_per_year = 252 * 24 * 60
            else:
                periods_per_year = 252
            
            mean_return = returns.mean()
            return mean_return * periods_per_year
            
        except Exception as e:
            self.logger.error(f"计算年化收益率失败: {e}")
            return 0.0
    
    def _calculate_volatility(self, returns: pd.Series) -> float:
        """计算波动率"""
        try:
            if len(returns) < 2:
                return 0.0
            
            # 年化波动率
            if self.config.frequency == PerformanceFrequency.DAILY:
                periods_per_year = 252
            elif self.config.frequency == PerformanceFrequency.HOURLY:
                periods_per_year = 252 * 24
            else:
                periods_per_year = 252
            
            return returns.std() * math.sqrt(periods_per_year)
            
        except Exception as e:
            self.logger.error(f"计算波动率失败: {e}")
            return 0.0
    
    def _calculate_downside_volatility(self, returns: pd.Series) -> float:
        """计算下行波动率"""
        try:
            if len(returns) < 2:
                return 0.0
            
            # 只考虑负收益
            downside_returns = returns[returns < 0]
            
            if len(downside_returns) == 0:
                return 0.0
            
            if self.config.frequency == PerformanceFrequency.DAILY:
                periods_per_year = 252
            else:
                periods_per_year = 252
            
            return downside_returns.std() * math.sqrt(periods_per_year)
            
        except Exception as e:
            self.logger.error(f"计算下行波动率失败: {e}")
            return 0.0
    
    def _calculate_tracking_error(self, returns: pd.Series) -> float:
        """计算跟踪误差"""
        try:
            if (self._benchmark_returns is None or 
                len(self._benchmark_returns) == 0 or 
                len(returns) == 0):
                return 0.0
            
            # 对齐数据
            common_index = returns.index.intersection(self._benchmark_returns.index)
            if len(common_index) < 2:
                return 0.0
            
            strategy_returns = returns.loc[common_index]
            benchmark_returns = self._benchmark_returns.loc[common_index]
            
            # 计算超额收益
            excess_returns = strategy_returns - benchmark_returns
            
            if self.config.frequency == PerformanceFrequency.DAILY:
                periods_per_year = 252
            else:
                periods_per_year = 252
            
            return excess_returns.std() * math.sqrt(periods_per_year)
            
        except Exception as e:
            self.logger.error(f"计算跟踪误差失败: {e}")
            return 0.0
    
    def _calculate_sharpe_ratio(self, returns: pd.Series) -> float:
        """计算夏普比率"""
        try:
            if len(returns) < 2:
                return 0.0
            
            excess_returns = returns - self.config.risk_free_rate / 252
            
            if excess_returns.std() == 0:
                return 0.0
            
            return excess_returns.mean() / excess_returns.std() * math.sqrt(252)
            
        except Exception as e:
            self.logger.error(f"计算夏普比率失败: {e}")
            return 0.0
    
    def _calculate_sortino_ratio(self, returns: pd.Series) -> float:
        """计算索提诺比率"""
        try:
            if len(returns) < 2:
                return 0.0
            
            excess_returns = returns - self.config.risk_free_rate / 252
            downside_returns = excess_returns[excess_returns < 0]
            
            if len(downside_returns) == 0 or downside_returns.std() == 0:
                return 0.0
            
            return excess_returns.mean() / downside_returns.std() * math.sqrt(252)
            
        except Exception as e:
            self.logger.error(f"计算索提诺比率失败: {e}")
            return 0.0
    
    def _calculate_calmar_ratio(self, annual_return: float, max_drawdown: float) -> float:
        """计算卡尔马比率"""
        try:
            if max_drawdown == 0:
                return 0.0
            
            return annual_return / abs(max_drawdown)
            
        except Exception as e:
            self.logger.error(f"计算卡尔马比率失败: {e}")
            return 0.0
    
    def _calculate_information_ratio(self, returns: pd.Series) -> float:
        """计算信息比率"""
        try:
            if (self._benchmark_returns is None or 
                len(self._benchmark_returns) == 0 or 
                len(returns) == 0):
                return 0.0
            
            # 对齐数据
            common_index = returns.index.intersection(self._benchmark_returns.index)
            if len(common_index) < 2:
                return 0.0
            
            strategy_returns = returns.loc[common_index]
            benchmark_returns = self._benchmark_returns.loc[common_index]
            
            # 计算超额收益
            excess_returns = strategy_returns - benchmark_returns
            
            if excess_returns.std() == 0:
                return 0.0
            
            return excess_returns.mean() / excess_returns.std() * math.sqrt(252)
            
        except Exception as e:
            self.logger.error(f"计算信息比率失败: {e}")
            return 0.0
    
    def _calculate_drawdown_metrics(self, drawdown_series: pd.Series) -> Dict[str, float]:
        """计算回撤指标"""
        try:
            if drawdown_series.empty:
                return {
                    'max_drawdown': 0.0,
                    'max_duration': 0,
                    'recovery_factor': 0.0,
                    'pain_index': 0.0
                }
            
            # 最大回撤
            max_drawdown = abs(drawdown_series.min())
            
            # 最大回撤持续时间
            max_duration = 0
            current_duration = 0
            
            for dd in drawdown_series:
                if dd < 0:
                    current_duration += 1
                    max_duration = max(max_duration, current_duration)
                else:
                    current_duration = 0
            
            # 恢复因子（总收益/最大回撤）
            total_return = (drawdown_series.iloc[-1] + 1) if len(drawdown_series) > 0 else 0
            recovery_factor = total_return / max_drawdown if max_drawdown > 0 else 0
            
            # 痛苦指数（平均回撤）
            pain_index = abs(drawdown_series[drawdown_series < 0].mean()) if len(drawdown_series[drawdown_series < 0]) > 0 else 0
            
            return {
                'max_drawdown': max_drawdown,
                'max_duration': max_duration,
                'recovery_factor': recovery_factor,
                'pain_index': pain_index
            }
            
        except Exception as e:
            self.logger.error(f"计算回撤指标失败: {e}")
            return {
                'max_drawdown': 0.0,
                'max_duration': 0,
                'recovery_factor': 0.0,
                'pain_index': 0.0
            }
    
    async def _calculate_trade_metrics(self, strategy_id: str, strategy: BaseStrategy) -> Dict[str, Any]:
        """计算交易指标"""
        try:
            trades = strategy.get_trades()
            
            if not trades:
                return {
                    'total_trades': 0,
                    'winning_trades': 0,
                    'losing_trades': 0,
                    'win_rate': 0.0,
                    'profit_factor': 0.0,
                    'expectancy': 0.0,
                    'avg_win': 0.0,
                    'avg_loss': 0.0,
                    'largest_win': 0.0,
                    'largest_loss': 0.0
                }
            
            # 计算每笔交易的盈亏
            trade_pnls = []
            for trade in trades:
                # 简化的盈亏计算，实际应该更复杂
                pnl = float(trade.price * trade.quantity) * (1 if trade.side == OrderSide.SELL else -1)
                trade_pnls.append(pnl)
            
            # 分离盈利和亏损交易
            wins = [pnl for pnl in trade_pnls if pnl > 0]
            losses = [pnl for pnl in trade_pnls if pnl < 0]
            
            total_trades = len(trades)
            winning_trades = len(wins)
            losing_trades = len(losses)
            
            win_rate = winning_trades / total_trades if total_trades > 0 else 0.0
            
            gross_profit = sum(wins) if wins else 0.0
            gross_loss = abs(sum(losses)) if losses else 0.0
            profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0.0
            
            avg_win = sum(wins) / len(wins) if wins else 0.0
            avg_loss = sum(losses) / len(losses) if losses else 0.0
            
            largest_win = max(wins) if wins else 0.0
            largest_loss = min(losses) if losses else 0.0
            
            # 期望值
            expectancy = avg_win * win_rate + avg_loss * (1 - win_rate)
            
            return {
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'losing_trades': losing_trades,
                'win_rate': win_rate,
                'profit_factor': profit_factor,
                'expectancy': expectancy,
                'avg_win': avg_win,
                'avg_loss': avg_loss,
                'largest_win': largest_win,
                'largest_loss': largest_loss
            }
            
        except Exception as e:
            self.logger.error(f"计算交易指标失败: {e}")
            return {}
    
    def _calculate_stability(self, returns: pd.Series) -> float:
        """计算稳定性指标"""
        try:
            if len(returns) < 10:
                return 0.0
            
            # 累积收益曲线
            cumulative_returns = (1 + returns).cumprod()
            
            # 对时间序列进行线性回归
            x = np.arange(len(cumulative_returns))
            slope, intercept, r_value, p_value, std_err = stats.linregress(x, cumulative_returns)
            
            # R²作为稳定性指标
            return r_value ** 2
            
        except Exception as e:
            self.logger.error(f"计算稳定性失败: {e}")
            return 0.0
    
    def _calculate_tail_ratio(self, returns: pd.Series) -> float:
        """计算尾部比率"""
        try:
            if len(returns) < 20:
                return 0.0
            
            # 右尾（95分位数）与左尾（5分位数）的比率
            right_tail = np.percentile(returns, 95)
            left_tail = np.percentile(returns, 5)
            
            if left_tail < 0:
                return right_tail / abs(left_tail)
            return 0.0
            
        except Exception as e:
            self.logger.error(f"计算尾部比率失败: {e}")
            return 0.0
    
    def _calculate_skewness(self, returns: pd.Series) -> float:
        """计算偏度"""
        try:
            if len(returns) < 3:
                return 0.0
            
            return stats.skew(returns)
            
        except Exception as e:
            self.logger.error(f"计算偏度失败: {e}")
            return 0.0
    
    def _calculate_kurtosis(self, returns: pd.Series) -> float:
        """计算峰度"""
        try:
            if len(returns) < 4:
                return 0.0
            
            return stats.kurtosis(returns)
            
        except Exception as e:
            self.logger.error(f"计算峰度失败: {e}")
            return 0.0
    
    def _calculate_alpha_beta(self, returns: pd.Series) -> Dict[str, float]:
        """计算Alpha和Beta"""
        try:
            if (self._benchmark_returns is None or 
                len(self._benchmark_returns) == 0 or 
                len(returns) < 10):
                return {'alpha': 0.0, 'beta': 0.0, 'r_squared': 0.0}
            
            # 对齐数据
            common_index = returns.index.intersection(self._benchmark_returns.index)
            if len(common_index) < 10:
                return {'alpha': 0.0, 'beta': 0.0, 'r_squared': 0.0}
            
            strategy_returns = returns.loc[common_index]
            benchmark_returns = self._benchmark_returns.loc[common_index]
            
            # 线性回归
            slope, intercept, r_value, p_value, std_err = stats.linregress(
                benchmark_returns, strategy_returns
            )
            
            # Beta是斜率，Alpha是截距（年化）
            beta = slope
            alpha = intercept * 252  # 年化Alpha
            r_squared = r_value ** 2
            
            return {
                'alpha': alpha,
                'beta': beta,
                'r_squared': r_squared
            }
            
        except Exception as e:
            self.logger.error(f"计算Alpha/Beta失败: {e}")
            return {'alpha': 0.0, 'beta': 0.0, 'r_squared': 0.0}
    
    def _calculate_var(self, returns: pd.Series) -> Dict[str, float]:
        """计算VaR和CVaR"""
        try:
            if len(returns) < 20:
                return {'var_95': 0.0, 'cvar_95': 0.0}
            
            # VaR (Value at Risk)
            var_95 = np.percentile(returns, (1 - self.config.var_confidence_level) * 100)
            
            # CVaR (Conditional VaR) - 超过VaR的平均损失
            tail_losses = returns[returns <= var_95]
            cvar_95 = tail_losses.mean() if len(tail_losses) > 0 else var_95
            
            return {
                'var_95': abs(var_95),
                'cvar_95': abs(cvar_95)
            }
            
        except Exception as e:
            self.logger.error(f"计算VaR失败: {e}")
            return {'var_95': 0.0, 'cvar_95': 0.0}
    
    # ==================== 交易分析 ====================
    
    async def _analyze_trades(self, strategy_id: str, strategy: BaseStrategy):
        """分析交易数据"""
        try:
            trades = strategy.get_trades()
            
            if not trades:
                self._trade_analysis[strategy_id] = {}
                return
            
            # 按品种分组分析
            symbol_analysis = {}
            for trade in trades:
                symbol = trade.symbol
                if symbol not in symbol_analysis:
                    symbol_analysis[symbol] = {
                        'trades': [],
                        'total_volume': 0.0,
                        'total_turnover': 0.0
                    }
                
                symbol_analysis[symbol]['trades'].append(trade)
                symbol_analysis[symbol]['total_volume'] += float(trade.quantity)
                symbol_analysis[symbol]['total_turnover'] += float(trade.price * trade.quantity)
            
            # 时间分析
            time_analysis = self._analyze_trade_timing(trades)
            
            # 持仓时间分析
            holding_analysis = self._analyze_holding_periods(trades)
            
            self._trade_analysis[strategy_id] = {
                'symbol_analysis': symbol_analysis,
                'time_analysis': time_analysis,
                'holding_analysis': holding_analysis,
                'last_update': datetime.now()
            }
            
        except Exception as e:
            self.logger.error(f"分析交易数据失败: {e}")
    
    def _analyze_trade_timing(self, trades: List[TradeInfo]) -> Dict[str, Any]:
        """分析交易时间分布"""
        try:
            if not trades:
                return {}
            
            # 按小时统计
            hour_counts = {}
            for trade in trades:
                hour = trade.timestamp.hour
                hour_counts[hour] = hour_counts.get(hour, 0) + 1
            
            # 按星期统计
            weekday_counts = {}
            for trade in trades:
                weekday = trade.timestamp.weekday()
                weekday_counts[weekday] = weekday_counts.get(weekday, 0) + 1
            
            return {
                'hour_distribution': hour_counts,
                'weekday_distribution': weekday_counts
            }
            
        except Exception as e:
            self.logger.error(f"分析交易时间失败: {e}")
            return {}
    
    def _analyze_holding_periods(self, trades: List[TradeInfo]) -> Dict[str, Any]:
        """分析持仓时间"""
        try:
            # 这里需要更复杂的逻辑来匹配买卖对
            # 暂时返回空字典
            return {}
            
        except Exception as e:
            self.logger.error(f"分析持仓时间失败: {e}")
            return {}
    
    # ==================== 历史记录 ====================
    
    async def _save_performance_history(self):
        """保存绩效历史"""
        try:
            current_time = datetime.now()
            
            for strategy_id, metrics in self._strategy_metrics.items():
                history_record = {
                    'timestamp': current_time,
                    'metrics': {
                        'total_return': metrics.total_return,
                        'annual_return': metrics.annual_return,
                        'volatility': metrics.volatility,
                        'sharpe_ratio': metrics.sharpe_ratio,
                        'max_drawdown': metrics.max_drawdown,
                        'win_rate': metrics.win_rate,
                        'total_trades': metrics.total_trades
                    }
                }
                
                self._performance_history[strategy_id].append(history_record)
                
                # 清理过期历史
                cutoff_date = current_time - timedelta(days=self.config.history_retention_days)
                self._performance_history[strategy_id] = [
                    record for record in self._performance_history[strategy_id]
                    if record['timestamp'] > cutoff_date
                ]
                
        except Exception as e:
            self.logger.error(f"保存绩效历史失败: {e}")
    
    # ==================== 查询接口 ====================
    
    def get_strategy_metrics(self, strategy_id: str) -> Optional[PerformanceMetrics]:
        """获取策略绩效指标"""
        return self._strategy_metrics.get(strategy_id)
    
    def get_all_metrics(self) -> Dict[str, PerformanceMetrics]:
        """获取所有策略绩效指标"""
        return self._strategy_metrics.copy()
    
    def get_equity_curve(self, strategy_id: str) -> Optional[pd.DataFrame]:
        """获取权益曲线"""
        return self._equity_curves.get(strategy_id)
    
    def get_returns_series(self, strategy_id: str) -> Optional[pd.Series]:
        """获取收益率序列"""
        return self._returns_series.get(strategy_id)
    
    def get_drawdown_series(self, strategy_id: str) -> Optional[pd.Series]:
        """获取回撤序列"""
        return self._drawdown_series.get(strategy_id)
    
    def get_trade_analysis(self, strategy_id: str) -> Dict[str, Any]:
        """获取交易分析"""
        return self._trade_analysis.get(strategy_id, {})
    
    def get_performance_history(self, strategy_id: str) -> List[Dict[str, Any]]:
        """获取绩效历史"""
        return self._performance_history.get(strategy_id, []).copy()
    
    # ==================== 比较分析 ====================
    
    def compare_strategies(self, strategy_ids: List[str]) -> Dict[str, Any]:
        """比较多个策略"""
        try:
            if len(strategy_ids) < 2:
                return {}
            
            comparison = {
                'strategies': strategy_ids,
                'metrics_comparison': {},
                'correlation_matrix': None,
                'ranking': {}
            }
            
            # 指标比较
            for metric_name in ['total_return', 'annual_return', 'volatility', 'sharpe_ratio', 'max_drawdown']:
                comparison['metrics_comparison'][metric_name] = {}
                for strategy_id in strategy_ids:
                    if strategy_id in self._strategy_metrics:
                        metrics = self._strategy_metrics[strategy_id]
                        comparison['metrics_comparison'][metric_name][strategy_id] = getattr(metrics, metric_name, 0.0)
            
            # 收益率相关性
            returns_data = {}
            for strategy_id in strategy_ids:
                if strategy_id in self._returns_series and not self._returns_series[strategy_id].empty:
                    returns_data[strategy_id] = self._returns_series[strategy_id]
            
            if len(returns_data) >= 2:
                # 对齐数据
                min_length = min(len(returns) for returns in returns_data.values())
                aligned_data = {}
                for strategy_id, returns in returns_data.items():
                    aligned_data[strategy_id] = returns.tail(min_length)
                
                correlation_df = pd.DataFrame(aligned_data).corr()
                comparison['correlation_matrix'] = correlation_df.to_dict()
            
            # 综合排名
            ranking_scores = {}
            for strategy_id in strategy_ids:
                if strategy_id in self._strategy_metrics:
                    metrics = self._strategy_metrics[strategy_id]
                    # 简单的综合评分（实际应该更复杂）
                    score = (metrics.sharpe_ratio * 0.3 + 
                            metrics.annual_return * 0.3 - 
                            metrics.max_drawdown * 0.2 + 
                            metrics.win_rate * 0.2)
                    ranking_scores[strategy_id] = score
            
            # 按评分排序
            sorted_ranking = sorted(ranking_scores.items(), key=lambda x: x[1], reverse=True)
            comparison['ranking'] = {strategy_id: rank + 1 for rank, (strategy_id, score) in enumerate(sorted_ranking)}
            
            return comparison
            
        except Exception as e:
            self.logger.error(f"策略比较失败: {e}")
            return {}
    
    # ==================== 报告生成 ====================
    
    def generate_performance_report(self, strategy_id: str) -> Dict[str, Any]:
        """生成绩效报告"""
        try:
            if strategy_id not in self._strategies:
                return {}
            
            strategy = self._strategies[strategy_id]
            metrics = self._strategy_metrics.get(strategy_id, PerformanceMetrics())
            
            report = {
                'strategy_info': {
                    'strategy_id': strategy_id,
                    'strategy_name': strategy.strategy_name,
                    'strategy_type': strategy.strategy_type.value,
                    'start_time': strategy._start_time,
                    'symbols': strategy.config.symbols,
                    'initial_capital': float(strategy.config.initial_capital)
                },
                'summary_metrics': {
                    'total_return': metrics.total_return,
                    'annual_return': metrics.annual_return,
                    'volatility': metrics.volatility,
                    'sharpe_ratio': metrics.sharpe_ratio,
                    'max_drawdown': metrics.max_drawdown,
                    'win_rate': metrics.win_rate,
                    'total_trades': metrics.total_trades
                },
                'detailed_metrics': {
                    'risk_metrics': {
                        'volatility': metrics.volatility,
                        'downside_volatility': metrics.downside_volatility,
                        'max_drawdown': metrics.max_drawdown,
                        'max_drawdown_duration': metrics.max_drawdown_duration,
                        'var_95': metrics.var_95,
                        'cvar_95': metrics.cvar_95
                    },
                    'return_metrics': {
                        'total_return': metrics.total_return,
                        'annual_return': metrics.annual_return,
                        'cumulative_return': metrics.cumulative_return,
                        'daily_return': metrics.daily_return
                    },
                    'risk_adjusted_metrics': {
                        'sharpe_ratio': metrics.sharpe_ratio,
                        'sortino_ratio': metrics.sortino_ratio,
                        'calmar_ratio': metrics.calmar_ratio,
                        'information_ratio': metrics.information_ratio
                    },
                    'trading_metrics': {
                        'total_trades': metrics.total_trades,
                        'winning_trades': metrics.winning_trades,
                        'losing_trades': metrics.losing_trades,
                        'win_rate': metrics.win_rate,
                        'profit_factor': metrics.profit_factor,
                        'expectancy': metrics.expectancy
                    }
                },
                'trade_analysis': self.get_trade_analysis(strategy_id),
                'timestamp': datetime.now()
            }
            
            return report
            
        except Exception as e:
            self.logger.error(f"生成绩效报告失败: {e}")
            return {}
    
    def get_monitoring_status(self) -> Dict[str, Any]:
        """获取监控状态"""
        return {
            'is_monitoring': self._is_monitoring,
            'strategies_count': len(self._strategies),
            'last_update': datetime.now(),
            'config': {
                'update_interval': self.config.update_interval,
                'frequency': self.config.frequency.value,
                'benchmark_symbol': self.config.benchmark_symbol
            }
        }
