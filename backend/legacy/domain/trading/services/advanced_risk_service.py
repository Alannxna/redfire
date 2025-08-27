"""
Advanced Risk Management Service
================================

高级风险管理服务，提供VaR计算、压力测试、实时监控、自动控制等功能。
"""

import logging
import math
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from decimal import Decimal
from dataclasses import dataclass, field
from enum import Enum

from ..entities.position_entity import Position
from ..entities.account_entity import Account
from ..entities.order_entity import Order
from ..entities.trade_entity import Trade
from ..enums import Direction, OrderStatus, PositionStatus

logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """风险等级"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class VaRMethod(Enum):
    """VaR计算方法"""
    HISTORICAL = "HISTORICAL"
    PARAMETRIC = "PARAMETRIC"
    MONTE_CARLO = "MONTE_CARLO"


@dataclass
class VaRResult:
    """VaR计算结果"""
    var_value: Decimal
    confidence_level: float
    time_horizon: int
    method: VaRMethod
    portfolio_value: Decimal
    expected_shortfall: Optional[Decimal] = None
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "var_value": float(self.var_value),
            "confidence_level": self.confidence_level,
            "time_horizon": self.time_horizon,
            "method": self.method.value,
            "portfolio_value": float(self.portfolio_value),
            "expected_shortfall": float(self.expected_shortfall) if self.expected_shortfall else None,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class StressTestScenario:
    """压力测试情景"""
    scenario_id: str
    name: str
    description: str
    market_shocks: Dict[str, Decimal]  # symbol -> price_change_ratio
    correlation_changes: Optional[Dict[str, float]] = None
    volatility_multiplier: float = 1.0
    create_time: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "scenario_id": self.scenario_id,
            "name": self.name,
            "description": self.description,
            "market_shocks": {k: float(v) for k, v in self.market_shocks.items()},
            "correlation_changes": self.correlation_changes,
            "volatility_multiplier": self.volatility_multiplier,
            "create_time": self.create_time.isoformat()
        }


@dataclass
class StressTestResult:
    """压力测试结果"""
    scenario_id: str
    portfolio_pnl: Decimal
    position_impacts: Dict[str, Decimal]
    risk_metrics: Dict[str, Decimal]
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "scenario_id": self.scenario_id,
            "portfolio_pnl": float(self.portfolio_pnl),
            "position_impacts": {k: float(v) for k, v in self.position_impacts.items()},
            "risk_metrics": {k: float(v) for k, v in self.risk_metrics.items()},
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class RiskAlert:
    """风险告警"""
    alert_id: str
    alert_type: str
    severity: RiskLevel
    message: str
    details: Dict[str, Any]
    triggered_time: datetime = field(default_factory=datetime.now)
    acknowledged: bool = False
    resolved: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "alert_id": self.alert_id,
            "alert_type": self.alert_type,
            "severity": self.severity.value,
            "message": self.message,
            "details": self.details,
            "triggered_time": self.triggered_time.isoformat(),
            "acknowledged": self.acknowledged,
            "resolved": self.resolved
        }


class AdvancedRiskService:
    """高级风险管理服务"""
    
    def __init__(self):
        self._price_history: Dict[str, List[Tuple[datetime, Decimal]]] = {}
        self._correlation_matrix: Dict[str, Dict[str, float]] = {}
        self._volatilities: Dict[str, float] = {}
        self._stress_scenarios: Dict[str, StressTestScenario] = {}
        self._var_results: List[VaRResult] = []
        self._stress_results: List[StressTestResult] = []
        self._risk_alerts: List[RiskAlert] = []
        self._risk_limits: Dict[str, Dict[str, Any]] = {}
        self._monitoring_enabled = True
        
        # 默认风险限额
        self._default_limits = {
            "max_var_ratio": Decimal("0.05"),  # VaR不超过总资产5%
            "max_single_position_ratio": Decimal("0.2"),  # 单一持仓不超过20%
            "max_sector_concentration": Decimal("0.4"),  # 行业集中度不超过40%
            "max_correlation_exposure": Decimal("0.6"),  # 相关性敞口不超过60%
        }
    
    # ==================== VaR计算 ====================
    
    async def calculate_historical_var(
        self,
        positions: List[Position],
        confidence_level: float = 0.95,
        time_horizon: int = 1,
        lookback_days: int = 252
    ) -> VaRResult:
        """计算历史模拟VaR"""
        try:
            # 获取投资组合价值
            portfolio_value = sum(
                pos.total_volume * pos.long_avg_price 
                for pos in positions 
                if pos.status == PositionStatus.ACTIVE
            )
            
            if portfolio_value == 0:
                return VaRResult(
                    var_value=Decimal("0"),
                    confidence_level=confidence_level,
                    time_horizon=time_horizon,
                    method=VaRMethod.HISTORICAL,
                    portfolio_value=portfolio_value
                )
            
            # 计算历史收益率
            historical_returns = await self._calculate_portfolio_returns(
                positions, lookback_days
            )
            
            if len(historical_returns) < 30:  # 需要足够的历史数据
                logger.warning("历史数据不足，无法计算准确的VaR")
                return VaRResult(
                    var_value=Decimal("0"),
                    confidence_level=confidence_level,
                    time_horizon=time_horizon,
                    method=VaRMethod.HISTORICAL,
                    portfolio_value=portfolio_value
                )
            
            # 排序并找到分位数
            sorted_returns = sorted(historical_returns)
            percentile_index = int((1 - confidence_level) * len(sorted_returns))
            var_return = sorted_returns[percentile_index]
            
            # 计算VaR值
            var_value = abs(portfolio_value * Decimal(str(var_return)) * Decimal(str(math.sqrt(time_horizon))))
            
            # 计算期望损失 (CVaR)
            tail_returns = sorted_returns[:percentile_index + 1]
            expected_shortfall = None
            if tail_returns:
                avg_tail_return = sum(tail_returns) / len(tail_returns)
                expected_shortfall = abs(portfolio_value * Decimal(str(avg_tail_return)) * Decimal(str(math.sqrt(time_horizon))))
            
            result = VaRResult(
                var_value=var_value,
                confidence_level=confidence_level,
                time_horizon=time_horizon,
                method=VaRMethod.HISTORICAL,
                portfolio_value=portfolio_value,
                expected_shortfall=expected_shortfall
            )
            
            self._var_results.append(result)
            logger.info(f"历史模拟VaR计算完成: {float(var_value):.2f}")
            
            return result
            
        except Exception as e:
            logger.error(f"历史模拟VaR计算失败: {e}")
            return VaRResult(
                var_value=Decimal("0"),
                confidence_level=confidence_level,
                time_horizon=time_horizon,
                method=VaRMethod.HISTORICAL,
                portfolio_value=Decimal("0")
            )
    
    async def calculate_parametric_var(
        self,
        positions: List[Position],
        confidence_level: float = 0.95,
        time_horizon: int = 1
    ) -> VaRResult:
        """计算参数VaR（假设正态分布）"""
        try:
            # 获取投资组合价值
            portfolio_value = sum(
                pos.total_volume * pos.long_avg_price 
                for pos in positions 
                if pos.status == PositionStatus.ACTIVE
            )
            
            if portfolio_value == 0:
                return VaRResult(
                    var_value=Decimal("0"),
                    confidence_level=confidence_level,
                    time_horizon=time_horizon,
                    method=VaRMethod.PARAMETRIC,
                    portfolio_value=portfolio_value
                )
            
            # 计算投资组合的预期收益率和标准差
            expected_return, portfolio_std = await self._calculate_portfolio_stats(positions)
            
            # 计算Z分数
            z_score = self._get_z_score(confidence_level)
            
            # 计算VaR
            var_return = expected_return - (z_score * portfolio_std)
            var_value = abs(portfolio_value * Decimal(str(var_return)) * Decimal(str(math.sqrt(time_horizon))))
            
            result = VaRResult(
                var_value=var_value,
                confidence_level=confidence_level,
                time_horizon=time_horizon,
                method=VaRMethod.PARAMETRIC,
                portfolio_value=portfolio_value
            )
            
            self._var_results.append(result)
            logger.info(f"参数VaR计算完成: {float(var_value):.2f}")
            
            return result
            
        except Exception as e:
            logger.error(f"参数VaR计算失败: {e}")
            return VaRResult(
                var_value=Decimal("0"),
                confidence_level=confidence_level,
                time_horizon=time_horizon,
                method=VaRMethod.PARAMETRIC,
                portfolio_value=Decimal("0")
            )
    
    async def calculate_monte_carlo_var(
        self,
        positions: List[Position],
        confidence_level: float = 0.95,
        time_horizon: int = 1,
        simulations: int = 10000
    ) -> VaRResult:
        """计算蒙特卡洛VaR"""
        try:
            # 获取投资组合价值
            portfolio_value = sum(
                pos.total_volume * pos.long_avg_price 
                for pos in positions 
                if pos.status == PositionStatus.ACTIVE
            )
            
            if portfolio_value == 0:
                return VaRResult(
                    var_value=Decimal("0"),
                    confidence_level=confidence_level,
                    time_horizon=time_horizon,
                    method=VaRMethod.MONTE_CARLO,
                    portfolio_value=portfolio_value
                )
            
            # 模拟投资组合收益率
            simulated_returns = await self._monte_carlo_simulation(
                positions, simulations, time_horizon
            )
            
            if not simulated_returns:
                return VaRResult(
                    var_value=Decimal("0"),
                    confidence_level=confidence_level,
                    time_horizon=time_horizon,
                    method=VaRMethod.MONTE_CARLO,
                    portfolio_value=portfolio_value
                )
            
            # 计算VaR
            sorted_returns = sorted(simulated_returns)
            percentile_index = int((1 - confidence_level) * len(sorted_returns))
            var_return = sorted_returns[percentile_index]
            
            var_value = abs(portfolio_value * Decimal(str(var_return)))
            
            # 计算期望损失
            tail_returns = sorted_returns[:percentile_index + 1]
            expected_shortfall = None
            if tail_returns:
                avg_tail_return = sum(tail_returns) / len(tail_returns)
                expected_shortfall = abs(portfolio_value * Decimal(str(avg_tail_return)))
            
            result = VaRResult(
                var_value=var_value,
                confidence_level=confidence_level,
                time_horizon=time_horizon,
                method=VaRMethod.MONTE_CARLO,
                portfolio_value=portfolio_value,
                expected_shortfall=expected_shortfall
            )
            
            self._var_results.append(result)
            logger.info(f"蒙特卡洛VaR计算完成: {float(var_value):.2f}")
            
            return result
            
        except Exception as e:
            logger.error(f"蒙特卡洛VaR计算失败: {e}")
            return VaRResult(
                var_value=Decimal("0"),
                confidence_level=confidence_level,
                time_horizon=time_horizon,
                method=VaRMethod.MONTE_CARLO,
                portfolio_value=Decimal("0")
            )
    
    async def _calculate_portfolio_returns(
        self,
        positions: List[Position],
        lookback_days: int
    ) -> List[float]:
        """计算投资组合历史收益率"""
        try:
            # 这里简化处理，实际应该从价格历史数据计算
            # 模拟一些历史收益率数据
            returns = []
            for i in range(lookback_days):
                # 生成模拟的日收益率
                daily_return = np.random.normal(0.001, 0.02)  # 平均0.1%，标准差2%
                returns.append(daily_return)
            
            return returns
            
        except Exception as e:
            logger.error(f"投资组合收益率计算失败: {e}")
            return []
    
    async def _calculate_portfolio_stats(
        self,
        positions: List[Position]
    ) -> Tuple[float, float]:
        """计算投资组合统计特征"""
        try:
            # 简化计算，实际应该考虑相关性矩阵
            expected_return = 0.001  # 日预期收益率0.1%
            portfolio_std = 0.02  # 日标准差2%
            
            return expected_return, portfolio_std
            
        except Exception as e:
            logger.error(f"投资组合统计计算失败: {e}")
            return 0.0, 0.0
    
    async def _monte_carlo_simulation(
        self,
        positions: List[Position],
        simulations: int,
        time_horizon: int
    ) -> List[float]:
        """蒙特卡洛模拟"""
        try:
            returns = []
            
            for _ in range(simulations):
                # 模拟时间区间内的收益率
                cumulative_return = 0
                for _ in range(time_horizon):
                    daily_return = np.random.normal(0.001, 0.02)
                    cumulative_return += daily_return
                
                returns.append(cumulative_return)
            
            return returns
            
        except Exception as e:
            logger.error(f"蒙特卡洛模拟失败: {e}")
            return []
    
    def _get_z_score(self, confidence_level: float) -> float:
        """获取正态分布Z分数"""
        z_scores = {
            0.90: 1.28,
            0.95: 1.65,
            0.99: 2.33,
            0.999: 3.09
        }
        return z_scores.get(confidence_level, 1.65)
    
    # ==================== 压力测试 ====================
    
    async def add_stress_scenario(self, scenario: StressTestScenario) -> None:
        """添加压力测试情景"""
        try:
            self._stress_scenarios[scenario.scenario_id] = scenario
            logger.info(f"压力测试情景已添加: {scenario.name}")
            
        except Exception as e:
            logger.error(f"添加压力测试情景失败: {e}")
            raise
    
    async def run_stress_test(
        self,
        scenario_id: str,
        positions: List[Position],
        market_data: Dict[str, Decimal]
    ) -> StressTestResult:
        """运行压力测试"""
        try:
            scenario = self._stress_scenarios.get(scenario_id)
            if not scenario:
                raise ValueError(f"压力测试情景不存在: {scenario_id}")
            
            # 计算当前投资组合价值
            current_portfolio_value = sum(
                pos.total_volume * market_data.get(pos.symbol, pos.long_avg_price)
                for pos in positions
                if pos.status == PositionStatus.ACTIVE
            )
            
            # 应用市场冲击
            shocked_prices = {}
            for symbol, current_price in market_data.items():
                shock = scenario.market_shocks.get(symbol, Decimal("0"))
                shocked_price = current_price * (Decimal("1") + shock)
                shocked_prices[symbol] = shocked_price
            
            # 计算压力测试后的投资组合价值
            stressed_portfolio_value = sum(
                pos.total_volume * shocked_prices.get(pos.symbol, pos.long_avg_price)
                for pos in positions
                if pos.status == PositionStatus.ACTIVE
            )
            
            # 计算盈亏
            portfolio_pnl = stressed_portfolio_value - current_portfolio_value
            
            # 计算每个持仓的影响
            position_impacts = {}
            for pos in positions:
                if pos.status == PositionStatus.ACTIVE:
                    current_value = pos.total_volume * market_data.get(pos.symbol, pos.long_avg_price)
                    stressed_value = pos.total_volume * shocked_prices.get(pos.symbol, pos.long_avg_price)
                    impact = stressed_value - current_value
                    position_impacts[pos.symbol] = impact
            
            # 计算风险指标
            risk_metrics = {
                "portfolio_pnl_ratio": portfolio_pnl / current_portfolio_value if current_portfolio_value > 0 else Decimal("0"),
                "max_position_loss": min(position_impacts.values()) if position_impacts else Decimal("0"),
                "stressed_var_multiplier": abs(portfolio_pnl) / current_portfolio_value if current_portfolio_value > 0 else Decimal("0")
            }
            
            result = StressTestResult(
                scenario_id=scenario_id,
                portfolio_pnl=portfolio_pnl,
                position_impacts=position_impacts,
                risk_metrics=risk_metrics
            )
            
            self._stress_results.append(result)
            logger.info(f"压力测试完成: {scenario.name}, PnL: {float(portfolio_pnl):.2f}")
            
            return result
            
        except Exception as e:
            logger.error(f"压力测试运行失败: {e}")
            return StressTestResult(
                scenario_id=scenario_id,
                portfolio_pnl=Decimal("0"),
                position_impacts={},
                risk_metrics={}
            )
    
    async def create_default_scenarios(self) -> None:
        """创建默认压力测试情景"""
        try:
            # 股市暴跌情景
            crash_scenario = StressTestScenario(
                scenario_id="MARKET_CRASH",
                name="市场暴跌",
                description="股票市场下跌20%的极端情景",
                market_shocks={
                    "default": Decimal("-0.20")  # 所有股票下跌20%
                }
            )
            await self.add_stress_scenario(crash_scenario)
            
            # 利率上升情景
            rate_scenario = StressTestScenario(
                scenario_id="RATE_RISE",
                name="利率上升",
                description="利率上升300bp的情景",
                market_shocks={
                    "bonds": Decimal("-0.15"),  # 债券下跌15%
                    "banks": Decimal("0.05")    # 银行股上涨5%
                }
            )
            await self.add_stress_scenario(rate_scenario)
            
            # 新兴市场危机情景
            em_scenario = StressTestScenario(
                scenario_id="EM_CRISIS",
                name="新兴市场危机",
                description="新兴市场资产大幅下跌的情景",
                market_shocks={
                    "em_stocks": Decimal("-0.30"),
                    "em_bonds": Decimal("-0.25"),
                    "usd": Decimal("0.10")  # 美元上涨10%
                }
            )
            await self.add_stress_scenario(em_scenario)
            
            logger.info("默认压力测试情景创建完成")
            
        except Exception as e:
            logger.error(f"创建默认压力测试情景失败: {e}")
    
    # ==================== 实时风险监控 ====================
    
    async def monitor_real_time_risk(
        self,
        positions: List[Position],
        accounts: List[Account],
        market_data: Dict[str, Decimal]
    ) -> List[RiskAlert]:
        """实时风险监控"""
        try:
            if not self._monitoring_enabled:
                return []
            
            alerts = []
            
            # VaR监控
            var_alerts = await self._monitor_var_limits(positions)
            alerts.extend(var_alerts)
            
            # 持仓集中度监控
            concentration_alerts = await self._monitor_concentration(positions, market_data)
            alerts.extend(concentration_alerts)
            
            # 账户风险监控
            account_alerts = await self._monitor_account_risk(accounts)
            alerts.extend(account_alerts)
            
            # 相关性风险监控
            correlation_alerts = await self._monitor_correlation_risk(positions, market_data)
            alerts.extend(correlation_alerts)
            
            # 保存新告警
            for alert in alerts:
                self._risk_alerts.append(alert)
            
            if alerts:
                logger.warning(f"生成风险告警 {len(alerts)} 条")
            
            return alerts
            
        except Exception as e:
            logger.error(f"实时风险监控失败: {e}")
            return []
    
    async def _monitor_var_limits(self, positions: List[Position]) -> List[RiskAlert]:
        """监控VaR限额"""
        alerts = []
        
        try:
            # 计算当前VaR
            var_result = await self.calculate_historical_var(positions)
            
            # 检查VaR限额
            max_var_ratio = self._default_limits["max_var_ratio"]
            var_ratio = var_result.var_value / var_result.portfolio_value if var_result.portfolio_value > 0 else Decimal("0")
            
            if var_ratio > max_var_ratio:
                alert = RiskAlert(
                    alert_id=f"VAR_LIMIT_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    alert_type="VAR_LIMIT_BREACH",
                    severity=RiskLevel.HIGH,
                    message=f"VaR比例超限: {float(var_ratio * 100):.2f}% > {float(max_var_ratio * 100):.2f}%",
                    details={
                        "var_value": float(var_result.var_value),
                        "portfolio_value": float(var_result.portfolio_value),
                        "var_ratio": float(var_ratio),
                        "limit_ratio": float(max_var_ratio)
                    }
                )
                alerts.append(alert)
            
        except Exception as e:
            logger.error(f"VaR限额监控失败: {e}")
        
        return alerts
    
    async def _monitor_concentration(
        self,
        positions: List[Position],
        market_data: Dict[str, Decimal]
    ) -> List[RiskAlert]:
        """监控持仓集中度"""
        alerts = []
        
        try:
            # 计算总持仓价值
            total_value = sum(
                pos.total_volume * market_data.get(pos.symbol, pos.long_avg_price)
                for pos in positions
                if pos.status == PositionStatus.ACTIVE
            )
            
            if total_value == 0:
                return alerts
            
            # 检查单一持仓集中度
            max_single_ratio = self._default_limits["max_single_position_ratio"]
            
            for pos in positions:
                if pos.status == PositionStatus.ACTIVE:
                    position_value = pos.total_volume * market_data.get(pos.symbol, pos.long_avg_price)
                    concentration_ratio = position_value / total_value
                    
                    if concentration_ratio > max_single_ratio:
                        alert = RiskAlert(
                            alert_id=f"CONCENTRATION_{pos.symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                            alert_type="CONCENTRATION_RISK",
                            severity=RiskLevel.MEDIUM,
                            message=f"单一持仓集中度过高: {pos.symbol} {float(concentration_ratio * 100):.2f}%",
                            details={
                                "symbol": pos.symbol,
                                "position_value": float(position_value),
                                "total_value": float(total_value),
                                "concentration_ratio": float(concentration_ratio),
                                "limit_ratio": float(max_single_ratio)
                            }
                        )
                        alerts.append(alert)
            
        except Exception as e:
            logger.error(f"集中度监控失败: {e}")
        
        return alerts
    
    async def _monitor_account_risk(self, accounts: List[Account]) -> List[RiskAlert]:
        """监控账户风险"""
        alerts = []
        
        try:
            for account in accounts:
                # 检查账户风险度
                if account.risk_degree > Decimal("0.9"):  # 风险度超过90%
                    alert = RiskAlert(
                        alert_id=f"ACCOUNT_RISK_{account.account_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                        alert_type="ACCOUNT_RISK",
                        severity=RiskLevel.CRITICAL,
                        message=f"账户风险度过高: {account.account_id} {float(account.risk_degree * 100):.2f}%",
                        details={
                            "account_id": account.account_id,
                            "risk_degree": float(account.risk_degree),
                            "balance": float(account.balance),
                            "margin": float(account.margin),
                            "available": float(account.available)
                        }
                    )
                    alerts.append(alert)
                
                # 检查可用资金
                if account.available < 0:
                    alert = RiskAlert(
                        alert_id=f"MARGIN_CALL_{account.account_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                        alert_type="MARGIN_CALL",
                        severity=RiskLevel.CRITICAL,
                        message=f"保证金不足: {account.account_id} 可用资金 {float(account.available):.2f}",
                        details={
                            "account_id": account.account_id,
                            "available": float(account.available),
                            "balance": float(account.balance),
                            "margin": float(account.margin)
                        }
                    )
                    alerts.append(alert)
            
        except Exception as e:
            logger.error(f"账户风险监控失败: {e}")
        
        return alerts
    
    async def _monitor_correlation_risk(
        self,
        positions: List[Position],
        market_data: Dict[str, Decimal]
    ) -> List[RiskAlert]:
        """监控相关性风险"""
        alerts = []
        
        try:
            # 简化的相关性风险检查
            # 实际应该计算持仓之间的相关性
            active_positions = [pos for pos in positions if pos.status == PositionStatus.ACTIVE]
            
            if len(active_positions) > 10:  # 持仓过于分散可能导致相关性风险
                alert = RiskAlert(
                    alert_id=f"CORRELATION_RISK_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    alert_type="CORRELATION_RISK",
                    severity=RiskLevel.MEDIUM,
                    message=f"持仓数量过多，可能存在相关性风险: {len(active_positions)} 个持仓",
                    details={
                        "position_count": len(active_positions),
                        "symbols": [pos.symbol for pos in active_positions]
                    }
                )
                alerts.append(alert)
            
        except Exception as e:
            logger.error(f"相关性风险监控失败: {e}")
        
        return alerts
    
    # ==================== 自动风险控制 ====================
    
    async def auto_risk_control(
        self,
        order: Order,
        positions: List[Position],
        accounts: List[Account],
        market_data: Dict[str, Decimal]
    ) -> Tuple[bool, List[str]]:
        """自动风险控制"""
        try:
            control_actions = []
            allow_order = True
            
            # 检查VaR限制
            var_check = await self._check_var_control(order, positions, market_data)
            if not var_check[0]:
                allow_order = False
                control_actions.extend(var_check[1])
            
            # 检查集中度限制
            concentration_check = await self._check_concentration_control(
                order, positions, market_data
            )
            if not concentration_check[0]:
                allow_order = False
                control_actions.extend(concentration_check[1])
            
            # 检查账户风险限制
            account_check = await self._check_account_control(order, accounts)
            if not account_check[0]:
                allow_order = False
                control_actions.extend(account_check[1])
            
            return allow_order, control_actions
            
        except Exception as e:
            logger.error(f"自动风险控制失败: {e}")
            return False, [f"风险控制系统错误: {str(e)}"]
    
    async def _check_var_control(
        self,
        order: Order,
        positions: List[Position],
        market_data: Dict[str, Decimal]
    ) -> Tuple[bool, List[str]]:
        """检查VaR控制"""
        try:
            # 模拟添加新订单后的持仓
            simulated_positions = positions.copy()
            
            # 简化处理：假设订单完全成交
            if order.offset.value == "OPEN":
                # 查找现有持仓或创建新持仓
                existing_pos = next(
                    (pos for pos in simulated_positions if pos.symbol == order.symbol), None
                )
                
                if existing_pos:
                    # 更新现有持仓
                    if order.direction.value == "LONG":
                        existing_pos.long_volume += order.volume
                    else:
                        existing_pos.short_volume += order.volume
                else:
                    # 创建新持仓
                    new_pos = Position(
                        symbol=order.symbol,
                        exchange=order.exchange,
                        user_id=order.user_id
                    )
                    new_pos.update_position(
                        order.direction.value, order.volume, order.price or Decimal("100"), True
                    )
                    simulated_positions.append(new_pos)
            
            # 计算新的VaR
            var_result = await self.calculate_historical_var(simulated_positions)
            max_var_ratio = self._default_limits["max_var_ratio"]
            var_ratio = var_result.var_value / var_result.portfolio_value if var_result.portfolio_value > 0 else Decimal("0")
            
            if var_ratio > max_var_ratio:
                return False, [f"订单将导致VaR超限: {float(var_ratio * 100):.2f}% > {float(max_var_ratio * 100):.2f}%"]
            
            return True, []
            
        except Exception as e:
            logger.error(f"VaR控制检查失败: {e}")
            return False, [f"VaR控制检查失败: {str(e)}"]
    
    async def _check_concentration_control(
        self,
        order: Order,
        positions: List[Position],
        market_data: Dict[str, Decimal]
    ) -> Tuple[bool, List[str]]:
        """检查集中度控制"""
        try:
            # 计算当前总持仓价值
            total_value = sum(
                pos.total_volume * market_data.get(pos.symbol, pos.long_avg_price)
                for pos in positions
                if pos.status == PositionStatus.ACTIVE
            )
            
            # 计算新订单的价值
            order_value = order.volume * (order.price or Decimal("100"))
            new_total_value = total_value + order_value
            
            # 检查单一持仓集中度
            existing_pos = next(
                (pos for pos in positions if pos.symbol == order.symbol and pos.status == PositionStatus.ACTIVE), 
                None
            )
            
            current_symbol_value = 0
            if existing_pos:
                current_symbol_value = existing_pos.total_volume * market_data.get(order.symbol, existing_pos.long_avg_price)
            
            new_symbol_value = current_symbol_value + order_value
            concentration_ratio = new_symbol_value / new_total_value if new_total_value > 0 else Decimal("0")
            
            max_single_ratio = self._default_limits["max_single_position_ratio"]
            if concentration_ratio > max_single_ratio:
                return False, [f"订单将导致单一持仓集中度超限: {order.symbol} {float(concentration_ratio * 100):.2f}% > {float(max_single_ratio * 100):.2f}%"]
            
            return True, []
            
        except Exception as e:
            logger.error(f"集中度控制检查失败: {e}")
            return False, [f"集中度控制检查失败: {str(e)}"]
    
    async def _check_account_control(
        self,
        order: Order,
        accounts: List[Account]
    ) -> Tuple[bool, List[str]]:
        """检查账户控制"""
        try:
            # 查找订单对应的账户
            account = next(
                (acc for acc in accounts if acc.user_id == order.user_id), None
            )
            
            if not account:
                return False, ["找不到对应账户"]
            
            # 检查账户状态
            if not account.is_active or not account.is_trading:
                return False, ["账户状态不允许交易"]
            
            # 检查风险度
            if account.risk_degree > Decimal("0.95"):  # 风险度超过95%
                return False, [f"账户风险度过高: {float(account.risk_degree * 100):.2f}%"]
            
            # 检查可用资金（简化计算）
            required_amount = order.volume * (order.price or Decimal("100"))
            if account.available < required_amount:
                return False, [f"可用资金不足: 需要 {float(required_amount):.2f}, 可用 {float(account.available):.2f}"]
            
            return True, []
            
        except Exception as e:
            logger.error(f"账户控制检查失败: {e}")
            return False, [f"账户控制检查失败: {str(e)}"]
    
    # ==================== 查询接口 ====================
    
    async def get_var_results(
        self,
        method: Optional[VaRMethod] = None,
        limit: Optional[int] = None
    ) -> List[VaRResult]:
        """获取VaR计算结果"""
        try:
            results = self._var_results
            
            if method:
                results = [r for r in results if r.method == method]
            
            if limit:
                results = results[-limit:]
            
            return results
            
        except Exception as e:
            logger.error(f"获取VaR结果失败: {e}")
            return []
    
    async def get_stress_results(
        self,
        scenario_id: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[StressTestResult]:
        """获取压力测试结果"""
        try:
            results = self._stress_results
            
            if scenario_id:
                results = [r for r in results if r.scenario_id == scenario_id]
            
            if limit:
                results = results[-limit:]
            
            return results
            
        except Exception as e:
            logger.error(f"获取压力测试结果失败: {e}")
            return []
    
    async def get_risk_alerts(
        self,
        severity: Optional[RiskLevel] = None,
        alert_type: Optional[str] = None,
        unresolved_only: bool = False
    ) -> List[RiskAlert]:
        """获取风险告警"""
        try:
            alerts = self._risk_alerts
            
            if severity:
                alerts = [a for a in alerts if a.severity == severity]
            
            if alert_type:
                alerts = [a for a in alerts if a.alert_type == alert_type]
            
            if unresolved_only:
                alerts = [a for a in alerts if not a.resolved]
            
            return alerts
            
        except Exception as e:
            logger.error(f"获取风险告警失败: {e}")
            return []
    
    async def get_risk_summary(self) -> Dict[str, Any]:
        """获取风险摘要"""
        try:
            latest_var = self._var_results[-1] if self._var_results else None
            unresolved_alerts = [a for a in self._risk_alerts if not a.resolved]
            
            alert_counts_by_severity = {}
            for level in RiskLevel:
                count = len([a for a in unresolved_alerts if a.severity == level])
                alert_counts_by_severity[level.value] = count
            
            return {
                "monitoring_enabled": self._monitoring_enabled,
                "latest_var": latest_var.to_dict() if latest_var else None,
                "total_stress_scenarios": len(self._stress_scenarios),
                "total_stress_results": len(self._stress_results),
                "unresolved_alerts": len(unresolved_alerts),
                "alert_counts_by_severity": alert_counts_by_severity,
                "risk_limits": {k: float(v) if isinstance(v, Decimal) else v for k, v in self._default_limits.items()},
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"获取风险摘要失败: {e}")
            return {"error": str(e)}
    
    # ==================== 配置管理 ====================
    
    async def set_monitoring_enabled(self, enabled: bool) -> None:
        """设置监控状态"""
        self._monitoring_enabled = enabled
        logger.info(f"风险监控状态: {'启用' if enabled else '禁用'}")
    
    async def update_risk_limits(self, limits: Dict[str, Any]) -> None:
        """更新风险限额"""
        try:
            for key, value in limits.items():
                if key in self._default_limits:
                    self._default_limits[key] = Decimal(str(value))
            
            logger.info("风险限额已更新")
            
        except Exception as e:
            logger.error(f"更新风险限额失败: {e}")
            raise
