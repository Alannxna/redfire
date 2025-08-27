"""
Enhanced Risk Management Service
===============================

增强的风险管理服务，扩展压力测试和实时监控功能。
在高级风险服务基础上增加历史情景回测、更全面的监控指标等。
"""

import logging
import math
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime, timedelta
from decimal import Decimal
from dataclasses import dataclass, field
from enum import Enum

from .advanced_risk_service import (
    AdvancedRiskService, VaRResult, StressTestScenario, StressTestResult,
    RiskAlert, RiskLevel, VaRMethod
)
from ..entities.position_entity import Position
from ..entities.account_entity import Account
from ..entities.order_entity import Order
from ..entities.trade_entity import Trade
from ..enums import Direction, OrderStatus, PositionStatus

logger = logging.getLogger(__name__)


class ScenarioType(Enum):
    """情景类型"""
    HISTORICAL = "HISTORICAL"
    SYNTHETIC = "SYNTHETIC"
    REGULATORY = "REGULATORY"
    CUSTOM = "CUSTOM"


class MonitoringFrequency(Enum):
    """监控频率"""
    REAL_TIME = "REAL_TIME"
    MINUTE = "MINUTE"
    HOUR = "HOUR"
    DAILY = "DAILY"


@dataclass
class HistoricalScenario:
    """历史情景"""
    scenario_id: str
    name: str
    description: str
    start_date: datetime
    end_date: datetime
    scenario_type: ScenarioType
    market_returns: Dict[str, List[float]]  # symbol -> returns
    volatility_data: Dict[str, float]
    correlation_data: Dict[str, Dict[str, float]]
    create_time: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "scenario_id": self.scenario_id,
            "name": self.name,
            "description": self.description,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "scenario_type": self.scenario_type.value,
            "market_returns": self.market_returns,
            "volatility_data": self.volatility_data,
            "correlation_data": self.correlation_data,
            "create_time": self.create_time.isoformat()
        }


@dataclass
class BacktestResult:
    """回测结果"""
    scenario_id: str
    total_pnl: Decimal
    max_drawdown: Decimal
    max_gain: Decimal
    var_breaches: int
    sharpe_ratio: float
    daily_pnl: List[Decimal]
    risk_metrics: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "scenario_id": self.scenario_id,
            "total_pnl": float(self.total_pnl),
            "max_drawdown": float(self.max_drawdown),
            "max_gain": float(self.max_gain),
            "var_breaches": self.var_breaches,
            "sharpe_ratio": self.sharpe_ratio,
            "daily_pnl": [float(pnl) for pnl in self.daily_pnl],
            "risk_metrics": self.risk_metrics,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class RiskMetrics:
    """风险指标"""
    var_95: Decimal
    var_99: Decimal
    expected_shortfall: Decimal
    max_drawdown: Decimal
    volatility: float
    beta: float
    correlation_risk: float
    concentration_risk: float
    liquidity_risk: float
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "var_95": float(self.var_95),
            "var_99": float(self.var_99),
            "expected_shortfall": float(self.expected_shortfall),
            "max_drawdown": float(self.max_drawdown),
            "volatility": self.volatility,
            "beta": self.beta,
            "correlation_risk": self.correlation_risk,
            "concentration_risk": self.concentration_risk,
            "liquidity_risk": self.liquidity_risk,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class MonitoringRule:
    """监控规则"""
    rule_id: str
    name: str
    description: str
    metric_name: str
    threshold: Decimal
    comparison: str  # >, <, >=, <=, ==
    severity: RiskLevel
    frequency: MonitoringFrequency
    enabled: bool = True
    create_time: datetime = field(default_factory=datetime.now)
    
    def evaluate(self, value: Decimal) -> bool:
        """评估规则"""
        try:
            if self.comparison == ">":
                return value > self.threshold
            elif self.comparison == "<":
                return value < self.threshold
            elif self.comparison == ">=":
                return value >= self.threshold
            elif self.comparison == "<=":
                return value <= self.threshold
            elif self.comparison == "==":
                return value == self.threshold
            return False
        except:
            return False
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "rule_id": self.rule_id,
            "name": self.name,
            "description": self.description,
            "metric_name": self.metric_name,
            "threshold": float(self.threshold),
            "comparison": self.comparison,
            "severity": self.severity.value,
            "frequency": self.frequency.value,
            "enabled": self.enabled,
            "create_time": self.create_time.isoformat()
        }


class EnhancedRiskService(AdvancedRiskService):
    """增强的风险管理服务"""
    
    def __init__(self):
        super().__init__()
        
        # 历史情景数据
        self._historical_scenarios: Dict[str, HistoricalScenario] = {}
        self._backtest_results: List[BacktestResult] = []
        
        # 实时监控
        self._monitoring_rules: Dict[str, MonitoringRule] = {}
        self._risk_metrics_history: List[RiskMetrics] = []
        self._monitoring_enabled = True
        
        # 市场数据缓存
        self._market_data_cache: Dict[str, List[Tuple[datetime, Decimal]]] = {}
        
        # 初始化默认监控规则
        self._init_default_monitoring_rules()
    
    def _init_default_monitoring_rules(self) -> None:
        """初始化默认监控规则"""
        try:
            default_rules = [
                MonitoringRule(
                    rule_id="VAR_95_LIMIT",
                    name="VaR 95%限额",
                    description="VaR 95%不得超过总资产的5%",
                    metric_name="var_95_ratio",
                    threshold=Decimal("0.05"),
                    comparison=">",
                    severity=RiskLevel.HIGH,
                    frequency=MonitoringFrequency.REAL_TIME
                ),
                MonitoringRule(
                    rule_id="MAX_DRAWDOWN",
                    name="最大回撤限制",
                    description="最大回撤不得超过10%",
                    metric_name="max_drawdown",
                    threshold=Decimal("0.10"),
                    comparison=">",
                    severity=RiskLevel.CRITICAL,
                    frequency=MonitoringFrequency.REAL_TIME
                ),
                MonitoringRule(
                    rule_id="CONCENTRATION_RISK",
                    name="集中度风险",
                    description="单一持仓不得超过20%",
                    metric_name="max_position_ratio",
                    threshold=Decimal("0.20"),
                    comparison=">",
                    severity=RiskLevel.MEDIUM,
                    frequency=MonitoringFrequency.MINUTE
                ),
                MonitoringRule(
                    rule_id="CORRELATION_RISK",
                    name="相关性风险",
                    description="高相关性持仓敞口不得超过60%",
                    metric_name="correlation_exposure",
                    threshold=Decimal("0.60"),
                    comparison=">",
                    severity=RiskLevel.MEDIUM,
                    frequency=MonitoringFrequency.HOUR
                ),
                MonitoringRule(
                    rule_id="LIQUIDITY_RISK",
                    name="流动性风险",
                    description="流动性风险评分不得超过0.7",
                    metric_name="liquidity_score",
                    threshold=Decimal("0.70"),
                    comparison=">",
                    severity=RiskLevel.HIGH,
                    frequency=MonitoringFrequency.MINUTE
                )
            ]
            
            for rule in default_rules:
                self._monitoring_rules[rule.rule_id] = rule
            
            logger.info(f"初始化默认监控规则: {len(default_rules)}条")
            
        except Exception as e:
            logger.error(f"初始化默认监控规则失败: {e}")
    
    # ==================== 历史情景回测 ====================
    
    async def create_historical_scenario(
        self,
        scenario_id: str,
        name: str,
        description: str,
        start_date: datetime,
        end_date: datetime,
        scenario_type: ScenarioType = ScenarioType.HISTORICAL
    ) -> HistoricalScenario:
        """创建历史情景"""
        try:
            # 获取历史市场数据
            market_returns = await self._get_historical_returns(start_date, end_date)
            volatility_data = await self._calculate_historical_volatility(start_date, end_date)
            correlation_data = await self._calculate_historical_correlation(start_date, end_date)
            
            scenario = HistoricalScenario(
                scenario_id=scenario_id,
                name=name,
                description=description,
                start_date=start_date,
                end_date=end_date,
                scenario_type=scenario_type,
                market_returns=market_returns,
                volatility_data=volatility_data,
                correlation_data=correlation_data
            )
            
            self._historical_scenarios[scenario_id] = scenario
            logger.info(f"历史情景创建成功: {name}")
            
            return scenario
            
        except Exception as e:
            logger.error(f"创建历史情景失败: {e}")
            raise
    
    async def run_historical_backtest(
        self,
        scenario_id: str,
        positions: List[Position],
        initial_portfolio_value: Decimal
    ) -> BacktestResult:
        """运行历史回测"""
        try:
            scenario = self._historical_scenarios.get(scenario_id)
            if not scenario:
                raise ValueError(f"历史情景不存在: {scenario_id}")
            
            # 计算每日盈亏
            daily_pnl = []
            cumulative_pnl = Decimal("0")
            max_drawdown = Decimal("0")
            max_gain = Decimal("0")
            var_breaches = 0
            
            # 获取历史收益率数据
            symbols = [pos.symbol for pos in positions if pos.status == PositionStatus.ACTIVE]
            common_symbols = set(symbols) & set(scenario.market_returns.keys())
            
            if not common_symbols:
                logger.warning("回测中没有找到匹配的历史数据")
                return BacktestResult(
                    scenario_id=scenario_id,
                    total_pnl=Decimal("0"),
                    max_drawdown=Decimal("0"),
                    max_gain=Decimal("0"),
                    var_breaches=0,
                    sharpe_ratio=0.0,
                    daily_pnl=[],
                    risk_metrics={}
                )
            
            # 获取最短的历史数据长度
            min_length = min(len(scenario.market_returns[symbol]) for symbol in common_symbols)
            
            # 逐日计算
            for day in range(min_length):
                day_pnl = Decimal("0")
                
                # 计算每个持仓的当日盈亏
                for pos in positions:
                    if pos.status == PositionStatus.ACTIVE and pos.symbol in common_symbols:
                        returns = scenario.market_returns[pos.symbol]
                        if day < len(returns):
                            daily_return = Decimal(str(returns[day]))
                            position_value = pos.total_volume * pos.long_avg_price
                            position_pnl = position_value * daily_return
                            day_pnl += position_pnl
                
                daily_pnl.append(day_pnl)
                cumulative_pnl += day_pnl
                
                # 更新最大回撤和最大收益
                if cumulative_pnl > max_gain:
                    max_gain = cumulative_pnl
                
                drawdown = max_gain - cumulative_pnl
                if drawdown > max_drawdown:
                    max_drawdown = drawdown
                
                # 检查VaR突破（简化处理）
                if abs(day_pnl) > initial_portfolio_value * Decimal("0.05"):  # 假设VaR为5%
                    var_breaches += 1
            
            # 计算夏普比率
            if daily_pnl:
                returns_array = np.array([float(pnl) for pnl in daily_pnl])
                mean_return = np.mean(returns_array)
                std_return = np.std(returns_array)
                sharpe_ratio = mean_return / std_return if std_return > 0 else 0.0
            else:
                sharpe_ratio = 0.0
            
            # 计算风险指标
            risk_metrics = await self._calculate_backtest_risk_metrics(
                daily_pnl, initial_portfolio_value
            )
            
            result = BacktestResult(
                scenario_id=scenario_id,
                total_pnl=cumulative_pnl,
                max_drawdown=max_drawdown,
                max_gain=max_gain,
                var_breaches=var_breaches,
                sharpe_ratio=sharpe_ratio,
                daily_pnl=daily_pnl,
                risk_metrics=risk_metrics
            )
            
            self._backtest_results.append(result)
            logger.info(f"历史回测完成: {scenario.name}, 总盈亏: {float(cumulative_pnl):.2f}")
            
            return result
            
        except Exception as e:
            logger.error(f"历史回测失败: {e}")
            return BacktestResult(
                scenario_id=scenario_id,
                total_pnl=Decimal("0"),
                max_drawdown=Decimal("0"),
                max_gain=Decimal("0"),
                var_breaches=0,
                sharpe_ratio=0.0,
                daily_pnl=[],
                risk_metrics={}
            )
    
    async def _get_historical_returns(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, List[float]]:
        """获取历史收益率数据"""
        try:
            # 这里应该从实际的数据源获取历史数据
            # 现在使用模拟数据
            symbols = ["AAPL", "MSFT", "GOOGL", "TSLA", "AMZN"]
            market_returns = {}
            
            days = (end_date - start_date).days
            
            for symbol in symbols:
                # 生成模拟的历史收益率
                returns = []
                for _ in range(days):
                    # 使用正态分布生成收益率
                    daily_return = np.random.normal(0.001, 0.02)  # 均值0.1%，标准差2%
                    returns.append(daily_return)
                
                market_returns[symbol] = returns
            
            return market_returns
            
        except Exception as e:
            logger.error(f"获取历史收益率失败: {e}")
            return {}
    
    async def _calculate_historical_volatility(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, float]:
        """计算历史波动率"""
        try:
            # 模拟历史波动率数据
            symbols = ["AAPL", "MSFT", "GOOGL", "TSLA", "AMZN"]
            volatility_data = {}
            
            for symbol in symbols:
                # 生成模拟的历史波动率
                volatility = np.random.uniform(0.15, 0.35)  # 15%-35%的年化波动率
                volatility_data[symbol] = volatility
            
            return volatility_data
            
        except Exception as e:
            logger.error(f"计算历史波动率失败: {e}")
            return {}
    
    async def _calculate_historical_correlation(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Dict[str, float]]:
        """计算历史相关性"""
        try:
            # 模拟相关性矩阵
            symbols = ["AAPL", "MSFT", "GOOGL", "TSLA", "AMZN"]
            correlation_data = {}
            
            for symbol1 in symbols:
                correlation_data[symbol1] = {}
                for symbol2 in symbols:
                    if symbol1 == symbol2:
                        correlation_data[symbol1][symbol2] = 1.0
                    else:
                        # 生成0.3-0.8之间的相关性
                        correlation = np.random.uniform(0.3, 0.8)
                        correlation_data[symbol1][symbol2] = correlation
            
            return correlation_data
            
        except Exception as e:
            logger.error(f"计算历史相关性失败: {e}")
            return {}
    
    async def _calculate_backtest_risk_metrics(
        self,
        daily_pnl: List[Decimal],
        portfolio_value: Decimal
    ) -> Dict[str, Any]:
        """计算回测风险指标"""
        try:
            if not daily_pnl:
                return {}
            
            pnl_array = np.array([float(pnl) for pnl in daily_pnl])
            
            # 计算VaR
            var_95 = np.percentile(pnl_array, 5)
            var_99 = np.percentile(pnl_array, 1)
            
            # 计算期望损失
            tail_losses = pnl_array[pnl_array <= var_95]
            expected_shortfall = np.mean(tail_losses) if len(tail_losses) > 0 else 0
            
            # 计算最大回撤
            cumulative_pnl = np.cumsum(pnl_array)
            running_max = np.maximum.accumulate(cumulative_pnl)
            drawdown = running_max - cumulative_pnl
            max_drawdown = np.max(drawdown)
            
            # 计算波动率
            volatility = np.std(pnl_array)
            
            return {
                "var_95": abs(var_95),
                "var_99": abs(var_99),
                "expected_shortfall": abs(expected_shortfall),
                "max_drawdown": max_drawdown,
                "volatility": volatility,
                "mean_pnl": np.mean(pnl_array),
                "std_pnl": np.std(pnl_array),
                "skewness": float(pd.Series(pnl_array).skew()) if len(pnl_array) > 2 else 0,
                "kurtosis": float(pd.Series(pnl_array).kurtosis()) if len(pnl_array) > 3 else 0
            }
            
        except Exception as e:
            logger.error(f"计算回测风险指标失败: {e}")
            return {}
    
    # ==================== 增强的实时监控 ====================
    
    async def add_monitoring_rule(self, rule: MonitoringRule) -> None:
        """添加监控规则"""
        try:
            self._monitoring_rules[rule.rule_id] = rule
            logger.info(f"监控规则已添加: {rule.name}")
            
        except Exception as e:
            logger.error(f"添加监控规则失败: {e}")
            raise
    
    async def remove_monitoring_rule(self, rule_id: str) -> bool:
        """移除监控规则"""
        try:
            if rule_id in self._monitoring_rules:
                del self._monitoring_rules[rule_id]
                logger.info(f"监控规则已移除: {rule_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"移除监控规则失败: {e}")
            return False
    
    async def calculate_comprehensive_risk_metrics(
        self,
        positions: List[Position],
        accounts: List[Account],
        market_data: Dict[str, Decimal]
    ) -> RiskMetrics:
        """计算综合风险指标"""
        try:
            # 计算投资组合价值
            portfolio_value = sum(
                pos.total_volume * market_data.get(pos.symbol, pos.long_avg_price)
                for pos in positions
                if pos.status == PositionStatus.ACTIVE
            )
            
            if portfolio_value == 0:
                return RiskMetrics(
                    var_95=Decimal("0"),
                    var_99=Decimal("0"),
                    expected_shortfall=Decimal("0"),
                    max_drawdown=Decimal("0"),
                    volatility=0.0,
                    beta=0.0,
                    correlation_risk=0.0,
                    concentration_risk=0.0,
                    liquidity_risk=0.0
                )
            
            # 计算VaR
            var_95_result = await self.calculate_historical_var(positions, 0.95)
            var_99_result = await self.calculate_historical_var(positions, 0.99)
            
            # 计算最大回撤
            max_drawdown = await self._calculate_current_drawdown(accounts)
            
            # 计算其他风险指标
            volatility = await self._calculate_portfolio_volatility(positions, market_data)
            beta = await self._calculate_portfolio_beta(positions, market_data)
            correlation_risk = await self._calculate_correlation_risk(positions, market_data)
            concentration_risk = await self._calculate_concentration_risk(positions, market_data)
            liquidity_risk = await self._calculate_liquidity_risk(positions, market_data)
            
            risk_metrics = RiskMetrics(
                var_95=var_95_result.var_value,
                var_99=var_99_result.var_value,
                expected_shortfall=var_95_result.expected_shortfall or Decimal("0"),
                max_drawdown=max_drawdown,
                volatility=volatility,
                beta=beta,
                correlation_risk=correlation_risk,
                concentration_risk=concentration_risk,
                liquidity_risk=liquidity_risk
            )
            
            # 保存到历史记录
            self._risk_metrics_history.append(risk_metrics)
            
            return risk_metrics
            
        except Exception as e:
            logger.error(f"计算综合风险指标失败: {e}")
            return RiskMetrics(
                var_95=Decimal("0"),
                var_99=Decimal("0"),
                expected_shortfall=Decimal("0"),
                max_drawdown=Decimal("0"),
                volatility=0.0,
                beta=0.0,
                correlation_risk=0.0,
                concentration_risk=0.0,
                liquidity_risk=0.0
            )
    
    async def run_comprehensive_monitoring(
        self,
        positions: List[Position],
        accounts: List[Account],
        market_data: Dict[str, Decimal]
    ) -> List[RiskAlert]:
        """运行综合监控"""
        try:
            if not self._monitoring_enabled:
                return []
            
            alerts = []
            
            # 计算风险指标
            risk_metrics = await self.calculate_comprehensive_risk_metrics(
                positions, accounts, market_data
            )
            
            # 计算额外的监控指标
            monitoring_metrics = await self._calculate_monitoring_metrics(
                positions, accounts, market_data, risk_metrics
            )
            
            # 检查所有监控规则
            for rule_id, rule in self._monitoring_rules.items():
                if not rule.enabled:
                    continue
                
                metric_value = monitoring_metrics.get(rule.metric_name)
                if metric_value is not None and rule.evaluate(metric_value):
                    alert = RiskAlert(
                        alert_id=f"{rule_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                        alert_type=rule.metric_name.upper(),
                        severity=rule.severity,
                        message=f"{rule.name}: {rule.description} (当前值: {float(metric_value):.4f}, 限制: {float(rule.threshold):.4f})",
                        details={
                            "rule_id": rule_id,
                            "metric_name": rule.metric_name,
                            "current_value": float(metric_value),
                            "threshold": float(rule.threshold),
                            "comparison": rule.comparison
                        }
                    )
                    alerts.append(alert)
            
            # 保存新告警
            for alert in alerts:
                self._risk_alerts.append(alert)
            
            if alerts:
                logger.warning(f"综合监控生成告警 {len(alerts)} 条")
            
            return alerts
            
        except Exception as e:
            logger.error(f"综合监控运行失败: {e}")
            return []
    
    async def _calculate_monitoring_metrics(
        self,
        positions: List[Position],
        accounts: List[Account],
        market_data: Dict[str, Decimal],
        risk_metrics: RiskMetrics
    ) -> Dict[str, Decimal]:
        """计算监控指标"""
        try:
            # 计算投资组合价值
            portfolio_value = sum(
                pos.total_volume * market_data.get(pos.symbol, pos.long_avg_price)
                for pos in positions
                if pos.status == PositionStatus.ACTIVE
            )
            
            metrics = {}
            
            if portfolio_value > 0:
                # VaR比率
                metrics["var_95_ratio"] = risk_metrics.var_95 / portfolio_value
                metrics["var_99_ratio"] = risk_metrics.var_99 / portfolio_value
                
                # 最大持仓比例
                max_position_value = max(
                    (pos.total_volume * market_data.get(pos.symbol, pos.long_avg_price)
                     for pos in positions if pos.status == PositionStatus.ACTIVE),
                    default=Decimal("0")
                )
                metrics["max_position_ratio"] = max_position_value / portfolio_value
            else:
                metrics["var_95_ratio"] = Decimal("0")
                metrics["var_99_ratio"] = Decimal("0")
                metrics["max_position_ratio"] = Decimal("0")
            
            # 其他指标
            metrics["max_drawdown"] = risk_metrics.max_drawdown
            metrics["correlation_exposure"] = Decimal(str(risk_metrics.correlation_risk))
            metrics["concentration_risk"] = Decimal(str(risk_metrics.concentration_risk))
            metrics["liquidity_score"] = Decimal(str(risk_metrics.liquidity_risk))
            
            # 账户相关指标
            if accounts:
                avg_risk_degree = sum(acc.risk_degree for acc in accounts) / len(accounts)
                metrics["avg_risk_degree"] = avg_risk_degree
                
                min_available = min(acc.available for acc in accounts)
                metrics["min_available_funds"] = min_available
            
            return metrics
            
        except Exception as e:
            logger.error(f"计算监控指标失败: {e}")
            return {}
    
    async def _calculate_current_drawdown(self, accounts: List[Account]) -> Decimal:
        """计算当前回撤"""
        try:
            if not accounts:
                return Decimal("0")
            
            # 简化计算：使用账户余额变化
            total_balance = sum(acc.balance for acc in accounts)
            total_initial = sum(acc.initial_capital for acc in accounts if hasattr(acc, 'initial_capital'))
            
            if total_initial > 0:
                return max(Decimal("0"), (total_initial - total_balance) / total_initial)
            
            return Decimal("0")
            
        except Exception as e:
            logger.error(f"计算当前回撤失败: {e}")
            return Decimal("0")
    
    async def _calculate_portfolio_volatility(
        self,
        positions: List[Position],
        market_data: Dict[str, Decimal]
    ) -> float:
        """计算投资组合波动率"""
        try:
            # 简化计算：基于历史价格数据
            returns = []
            for pos in positions:
                if pos.status == PositionStatus.ACTIVE:
                    # 模拟获取历史收益率
                    historical_returns = np.random.normal(0.001, 0.02, 30)  # 30天数据
                    returns.extend(historical_returns)
            
            if returns:
                return float(np.std(returns) * np.sqrt(252))  # 年化波动率
            
            return 0.0
            
        except Exception as e:
            logger.error(f"计算投资组合波动率失败: {e}")
            return 0.0
    
    async def _calculate_portfolio_beta(
        self,
        positions: List[Position],
        market_data: Dict[str, Decimal]
    ) -> float:
        """计算投资组合Beta"""
        try:
            # 简化计算：假设市场Beta
            # 实际应该根据个股Beta和权重计算
            if positions:
                return 1.2  # 模拟Beta值
            return 0.0
            
        except Exception as e:
            logger.error(f"计算投资组合Beta失败: {e}")
            return 0.0
    
    async def _calculate_correlation_risk(
        self,
        positions: List[Position],
        market_data: Dict[str, Decimal]
    ) -> float:
        """计算相关性风险"""
        try:
            # 简化计算：基于持仓数量和行业集中度
            active_positions = [pos for pos in positions if pos.status == PositionStatus.ACTIVE]
            
            if len(active_positions) <= 1:
                return 0.0
            
            # 假设相关性随持仓数量减少而增加
            correlation_risk = 1.0 / len(active_positions)
            return min(correlation_risk, 1.0)
            
        except Exception as e:
            logger.error(f"计算相关性风险失败: {e}")
            return 0.0
    
    async def _calculate_concentration_risk(
        self,
        positions: List[Position],
        market_data: Dict[str, Decimal]
    ) -> float:
        """计算集中度风险"""
        try:
            total_value = sum(
                pos.total_volume * market_data.get(pos.symbol, pos.long_avg_price)
                for pos in positions
                if pos.status == PositionStatus.ACTIVE
            )
            
            if total_value == 0:
                return 0.0
            
            # 计算赫芬达尔指数
            hhi = sum(
                ((pos.total_volume * market_data.get(pos.symbol, pos.long_avg_price)) / total_value) ** 2
                for pos in positions
                if pos.status == PositionStatus.ACTIVE
            )
            
            return float(hhi)
            
        except Exception as e:
            logger.error(f"计算集中度风险失败: {e}")
            return 0.0
    
    async def _calculate_liquidity_risk(
        self,
        positions: List[Position],
        market_data: Dict[str, Decimal]
    ) -> float:
        """计算流动性风险"""
        try:
            # 简化计算：基于持仓规模和假设的流动性
            total_value = sum(
                pos.total_volume * market_data.get(pos.symbol, pos.long_avg_price)
                for pos in positions
                if pos.status == PositionStatus.ACTIVE
            )
            
            if total_value == 0:
                return 0.0
            
            # 假设大额持仓流动性风险更高
            liquidity_risk = min(float(total_value) / 10000000, 1.0)  # 1000万为基准
            return liquidity_risk
            
        except Exception as e:
            logger.error(f"计算流动性风险失败: {e}")
            return 0.0
    
    # ==================== 查询接口 ====================
    
    async def get_historical_scenarios(self) -> List[HistoricalScenario]:
        """获取历史情景列表"""
        try:
            return list(self._historical_scenarios.values())
            
        except Exception as e:
            logger.error(f"获取历史情景失败: {e}")
            return []
    
    async def get_backtest_results(
        self,
        scenario_id: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[BacktestResult]:
        """获取回测结果"""
        try:
            results = self._backtest_results
            
            if scenario_id:
                results = [r for r in results if r.scenario_id == scenario_id]
            
            if limit:
                results = results[-limit:]
            
            return results
            
        except Exception as e:
            logger.error(f"获取回测结果失败: {e}")
            return []
    
    async def get_monitoring_rules(self) -> List[MonitoringRule]:
        """获取监控规则"""
        try:
            return list(self._monitoring_rules.values())
            
        except Exception as e:
            logger.error(f"获取监控规则失败: {e}")
            return []
    
    async def get_risk_metrics_history(
        self,
        limit: Optional[int] = None
    ) -> List[RiskMetrics]:
        """获取风险指标历史"""
        try:
            history = self._risk_metrics_history
            
            if limit:
                history = history[-limit:]
            
            return history
            
        except Exception as e:
            logger.error(f"获取风险指标历史失败: {e}")
            return []
    
    async def get_enhanced_risk_summary(self) -> Dict[str, Any]:
        """获取增强风险摘要"""
        try:
            base_summary = await self.get_risk_summary()
            
            latest_metrics = self._risk_metrics_history[-1] if self._risk_metrics_history else None
            latest_backtest = self._backtest_results[-1] if self._backtest_results else None
            
            enhanced_summary = {
                **base_summary,
                "historical_scenarios": len(self._historical_scenarios),
                "backtest_results": len(self._backtest_results),
                "monitoring_rules": len(self._monitoring_rules),
                "active_monitoring_rules": len([r for r in self._monitoring_rules.values() if r.enabled]),
                "risk_metrics_history_length": len(self._risk_metrics_history),
                "latest_risk_metrics": latest_metrics.to_dict() if latest_metrics else None,
                "latest_backtest": latest_backtest.to_dict() if latest_backtest else None
            }
            
            return enhanced_summary
            
        except Exception as e:
            logger.error(f"获取增强风险摘要失败: {e}")
            return {"error": str(e)}
