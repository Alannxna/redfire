"""
量化策略风险管理模块

提供全面的风险控制功能，包括：
- 实时风险监控和预警
- 多层次风险限制
- 智能止损和止盈
- 压力测试和情景分析
- 风险指标计算和报告
"""

import logging
import asyncio
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple, Union, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from decimal import Decimal
import uuid

from .strategy_base import (
    BaseStrategy, StrategyConfig, MarketData, OrderInfo, TradeInfo, 
    PositionInfo, OrderSide, OrderType, PositionSide
)


class RiskLevel(Enum):
    """风险等级"""
    LOW = "low"
    MEDIUM = "medium"  
    HIGH = "high"
    CRITICAL = "critical"


class RiskType(Enum):
    """风险类型"""
    MARKET_RISK = "market"          # 市场风险
    CREDIT_RISK = "credit"          # 信用风险
    LIQUIDITY_RISK = "liquidity"    # 流动性风险
    OPERATIONAL_RISK = "operational" # 操作风险
    MODEL_RISK = "model"            # 模型风险
    CONCENTRATION_RISK = "concentration"  # 集中度风险


class RiskAction(Enum):
    """风险处置动作"""
    NONE = "none"
    WARNING = "warning"
    REDUCE_POSITION = "reduce_position"
    CLOSE_POSITION = "close_position"
    STOP_TRADING = "stop_trading"
    EMERGENCY_STOP = "emergency_stop"


@dataclass
class RiskLimit:
    """风险限额"""
    limit_id: str
    limit_name: str
    risk_type: RiskType
    limit_value: float
    current_value: float = 0.0
    threshold_warning: float = 0.8    # 警告阈值
    threshold_critical: float = 0.95  # 严重阈值
    action_warning: RiskAction = RiskAction.WARNING
    action_critical: RiskAction = RiskAction.CLOSE_POSITION
    enabled: bool = True


@dataclass
class RiskEvent:
    """风险事件"""
    event_id: str
    timestamp: datetime
    risk_type: RiskType
    risk_level: RiskLevel
    strategy_id: str
    symbol: str
    description: str
    current_value: float
    limit_value: float
    action_taken: RiskAction
    resolved: bool = False
    resolution_time: Optional[datetime] = None


@dataclass
class RiskConfig:
    """风险管理配置"""
    # 全局风险限制
    max_total_exposure: float = 1.0      # 最大总敞口比例
    max_single_position: float = 0.1     # 单个头寸最大比例
    max_sector_exposure: float = 0.3     # 单个行业最大敞口
    max_daily_loss: float = 0.02         # 单日最大亏损
    max_drawdown: float = 0.05           # 最大回撤
    
    # 杠杆控制
    max_leverage: float = 3.0
    margin_call_threshold: float = 0.3   # 追保阈值
    
    # 流动性风险
    min_cash_ratio: float = 0.05         # 最小现金比例
    max_position_size_ratio: float = 0.1  # 最大持仓占成交量比例
    
    # VaR设置
    var_confidence_level: float = 0.95   # VaR置信度
    var_holding_period: int = 1          # VaR持有期（天）
    var_history_days: int = 252          # VaR历史数据天数
    
    # 监控频率
    monitoring_interval: int = 60        # 监控间隔（秒）
    stress_test_interval: int = 3600     # 压力测试间隔（秒）
    
    # 告警配置
    enable_email_alerts: bool = True
    enable_sms_alerts: bool = False
    alert_recipients: List[str] = field(default_factory=list)


class RiskManager:
    """
    风险管理器
    
    负责实时监控策略风险，执行风险控制措施，
    生成风险报告和预警。
    """
    
    def __init__(self, config: Optional[RiskConfig] = None):
        """
        初始化风险管理器
        
        Args:
            config: 风险管理配置
        """
        self.config = config or RiskConfig()
        self.manager_id = str(uuid.uuid4())
        
        # 日志记录
        self.logger = logging.getLogger(f"risk_manager.{self.manager_id}")
        
        # 策略管理
        self._strategies: Dict[str, BaseStrategy] = {}
        self._strategy_limits: Dict[str, List[RiskLimit]] = {}
        
        # 风险限额
        self._global_limits: List[RiskLimit] = []
        self._current_risks: Dict[str, float] = {}
        
        # 风险事件
        self._risk_events: List[RiskEvent] = []
        self._active_events: Dict[str, RiskEvent] = {}
        
        # 市场数据
        self._market_data: Dict[str, MarketData] = {}
        self._price_history: Dict[str, List[float]] = {}
        
        # 风险计算缓存
        self._var_cache: Dict[str, Tuple[datetime, float]] = {}
        self._correlation_matrix: Optional[pd.DataFrame] = None
        self._beta_cache: Dict[str, float] = {}
        
        # 监控任务
        self._monitoring_task: Optional[asyncio.Task] = None
        self._stress_test_task: Optional[asyncio.Task] = None
        self._is_monitoring = False
        
        # 回调函数
        self._risk_callbacks: Dict[RiskLevel, List[Callable]] = {
            RiskLevel.LOW: [],
            RiskLevel.MEDIUM: [],
            RiskLevel.HIGH: [],
            RiskLevel.CRITICAL: []
        }
        
        # 初始化全局限额
        self._initialize_global_limits()
        
        self.logger.info(f"风险管理器初始化完成: {self.manager_id}")
    
    def _initialize_global_limits(self):
        """初始化全局风险限额"""
        # 总敞口限制
        self._global_limits.append(RiskLimit(
            limit_id="global_exposure",
            limit_name="总敞口限制",
            risk_type=RiskType.MARKET_RISK,
            limit_value=self.config.max_total_exposure,
            action_warning=RiskAction.WARNING,
            action_critical=RiskAction.REDUCE_POSITION
        ))
        
        # 单日亏损限制
        self._global_limits.append(RiskLimit(
            limit_id="daily_loss",
            limit_name="单日亏损限制",
            risk_type=RiskType.MARKET_RISK,
            limit_value=self.config.max_daily_loss,
            action_warning=RiskAction.WARNING,
            action_critical=RiskAction.STOP_TRADING
        ))
        
        # 最大回撤限制
        self._global_limits.append(RiskLimit(
            limit_id="max_drawdown",
            limit_name="最大回撤限制",
            risk_type=RiskType.MARKET_RISK,
            limit_value=self.config.max_drawdown,
            action_warning=RiskAction.WARNING,
            action_critical=RiskAction.EMERGENCY_STOP
        ))
        
        # 杠杆限制
        self._global_limits.append(RiskLimit(
            limit_id="leverage",
            limit_name="杠杆限制",
            risk_type=RiskType.MARKET_RISK,
            limit_value=self.config.max_leverage,
            action_warning=RiskAction.WARNING,
            action_critical=RiskAction.REDUCE_POSITION
        ))
        
        # 现金比例限制
        self._global_limits.append(RiskLimit(
            limit_id="cash_ratio",
            limit_name="现金比例限制",
            risk_type=RiskType.LIQUIDITY_RISK,
            limit_value=self.config.min_cash_ratio,
            action_warning=RiskAction.WARNING,
            action_critical=RiskAction.REDUCE_POSITION
        ))
    
    # ==================== 策略管理 ====================
    
    def add_strategy(self, strategy: BaseStrategy) -> bool:
        """添加策略到风险监控"""
        try:
            strategy_id = strategy.strategy_id
            
            if strategy_id in self._strategies:
                self.logger.warning(f"策略已存在: {strategy_id}")
                return False
            
            self._strategies[strategy_id] = strategy
            self._strategy_limits[strategy_id] = []
            
            # 为策略创建默认风险限额
            self._create_strategy_limits(strategy)
            
            self.logger.info(f"策略添加到风险监控: {strategy_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"添加策略失败: {e}")
            return False
    
    def remove_strategy(self, strategy_id: str) -> bool:
        """从风险监控移除策略"""
        try:
            if strategy_id not in self._strategies:
                self.logger.warning(f"策略不存在: {strategy_id}")
                return False
            
            del self._strategies[strategy_id]
            if strategy_id in self._strategy_limits:
                del self._strategy_limits[strategy_id]
            
            # 清理相关风险事件
            self._cleanup_strategy_events(strategy_id)
            
            self.logger.info(f"策略从风险监控移除: {strategy_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"移除策略失败: {e}")
            return False
    
    def _create_strategy_limits(self, strategy: BaseStrategy):
        """为策略创建风险限额"""
        try:
            strategy_id = strategy.strategy_id
            
            # 单个策略仓位限制
            self._strategy_limits[strategy_id].append(RiskLimit(
                limit_id=f"{strategy_id}_position",
                limit_name=f"策略{strategy_id}仓位限制",
                risk_type=RiskType.CONCENTRATION_RISK,
                limit_value=self.config.max_single_position,
                action_warning=RiskAction.WARNING,
                action_critical=RiskAction.REDUCE_POSITION
            ))
            
            # 策略日亏损限制
            daily_loss_limit = min(self.config.max_daily_loss, 
                                 float(strategy.config.max_drawdown or 0.02))
            self._strategy_limits[strategy_id].append(RiskLimit(
                limit_id=f"{strategy_id}_daily_loss",
                limit_name=f"策略{strategy_id}日亏损限制",
                risk_type=RiskType.MARKET_RISK,
                limit_value=daily_loss_limit,
                action_warning=RiskAction.WARNING,
                action_critical=RiskAction.CLOSE_POSITION
            ))
            
        except Exception as e:
            self.logger.error(f"创建策略风险限额失败: {e}")
    
    # ==================== 风险监控 ====================
    
    async def start_monitoring(self) -> bool:
        """启动风险监控"""
        try:
            if self._is_monitoring:
                self.logger.warning("风险监控已在运行")
                return True
            
            self._is_monitoring = True
            
            # 启动监控任务
            self._monitoring_task = asyncio.create_task(self._monitor_risks())
            self._stress_test_task = asyncio.create_task(self._stress_testing())
            
            self.logger.info("风险监控启动成功")
            return True
            
        except Exception as e:
            self.logger.error(f"启动风险监控失败: {e}")
            return False
    
    async def stop_monitoring(self) -> bool:
        """停止风险监控"""
        try:
            self._is_monitoring = False
            
            if self._monitoring_task:
                self._monitoring_task.cancel()
            if self._stress_test_task:
                self._stress_test_task.cancel()
            
            self.logger.info("风险监控停止")
            return True
            
        except Exception as e:
            self.logger.error(f"停止风险监控失败: {e}")
            return False
    
    async def _monitor_risks(self):
        """风险监控主循环"""
        try:
            while self._is_monitoring:
                # 更新市场数据
                await self._update_risk_metrics()
                
                # 检查全局风险限额
                await self._check_global_limits()
                
                # 检查策略风险限额
                await self._check_strategy_limits()
                
                # 计算高级风险指标
                await self._calculate_advanced_metrics()
                
                # 检查风险事件
                await self._check_risk_events()
                
                await asyncio.sleep(self.config.monitoring_interval)
                
        except asyncio.CancelledError:
            pass
        except Exception as e:
            self.logger.error(f"风险监控异常: {e}")
    
    async def _update_risk_metrics(self):
        """更新风险指标"""
        try:
            # 计算总敞口
            total_exposure = self._calculate_total_exposure()
            self._current_risks["total_exposure"] = total_exposure
            
            # 计算杠杆比率
            leverage = self._calculate_leverage()
            self._current_risks["leverage"] = leverage
            
            # 计算现金比例
            cash_ratio = self._calculate_cash_ratio()
            self._current_risks["cash_ratio"] = cash_ratio
            
            # 计算单日损失
            daily_loss = self._calculate_daily_loss()
            self._current_risks["daily_loss"] = daily_loss
            
            # 计算回撤
            drawdown = self._calculate_current_drawdown()
            self._current_risks["drawdown"] = drawdown
            
        except Exception as e:
            self.logger.error(f"更新风险指标失败: {e}")
    
    def _calculate_total_exposure(self) -> float:
        """计算总敞口"""
        try:
            total_exposure = 0.0
            total_capital = 0.0
            
            for strategy in self._strategies.values():
                strategy_capital = float(strategy.config.initial_capital)
                total_capital += strategy_capital
                
                for position in strategy.get_all_positions().values():
                    position_value = float(position.market_value)
                    total_exposure += abs(position_value)
            
            if total_capital > 0:
                return total_exposure / total_capital
            return 0.0
            
        except Exception as e:
            self.logger.error(f"计算总敞口失败: {e}")
            return 0.0
    
    def _calculate_leverage(self) -> float:
        """计算杠杆比率"""
        try:
            total_position_value = 0.0
            total_equity = 0.0
            
            for strategy in self._strategies.values():
                equity = float(strategy.account_balance)
                total_equity += equity
                
                for position in strategy.get_all_positions().values():
                    position_value = float(position.market_value)
                    total_position_value += abs(position_value)
            
            if total_equity > 0:
                return total_position_value / total_equity
            return 0.0
            
        except Exception as e:
            self.logger.error(f"计算杠杆比率失败: {e}")
            return 0.0
    
    def _calculate_cash_ratio(self) -> float:
        """计算现金比例"""
        try:
            total_cash = 0.0
            total_assets = 0.0
            
            for strategy in self._strategies.values():
                cash = float(strategy.available_balance)
                total_balance = float(strategy.account_balance)
                
                total_cash += cash
                total_assets += total_balance
            
            if total_assets > 0:
                return total_cash / total_assets
            return 0.0
            
        except Exception as e:
            self.logger.error(f"计算现金比例失败: {e}")
            return 0.0
    
    def _calculate_daily_loss(self) -> float:
        """计算单日损失"""
        try:
            total_daily_pnl = 0.0
            total_capital = 0.0
            
            today = datetime.now().date()
            
            for strategy in self._strategies.values():
                capital = float(strategy.config.initial_capital)
                total_capital += capital
                
                # 计算今日盈亏
                daily_pnl = 0.0
                for trade in strategy.get_trades():
                    if trade.timestamp.date() == today:
                        trade_pnl = float(trade.price * trade.quantity)
                        if trade.side == OrderSide.SELL:
                            daily_pnl += trade_pnl
                        else:
                            daily_pnl -= trade_pnl
                
                total_daily_pnl += daily_pnl
            
            if total_capital > 0:
                return abs(total_daily_pnl) / total_capital
            return 0.0
            
        except Exception as e:
            self.logger.error(f"计算单日损失失败: {e}")
            return 0.0
    
    def _calculate_current_drawdown(self) -> float:
        """计算当前回撤"""
        try:
            total_current_value = 0.0
            total_peak_value = 0.0
            
            for strategy in self._strategies.values():
                current_value = float(strategy.account_balance)
                total_current_value += current_value
                
                # 获取历史最高净值
                peak_value = float(strategy.config.initial_capital)
                for equity_point in strategy._equity_curve:
                    peak_value = max(peak_value, equity_point[1])
                
                total_peak_value += peak_value
            
            if total_peak_value > 0:
                drawdown = (total_peak_value - total_current_value) / total_peak_value
                return max(0.0, drawdown)
            return 0.0
            
        except Exception as e:
            self.logger.error(f"计算回撤失败: {e}")
            return 0.0
    
    # ==================== 风险限额检查 ====================
    
    async def _check_global_limits(self):
        """检查全局风险限额"""
        try:
            for limit in self._global_limits:
                if not limit.enabled:
                    continue
                
                current_value = self._current_risks.get(limit.limit_id.replace("global_", ""), 0.0)
                limit.current_value = current_value
                
                # 检查是否违反限额
                if self._is_limit_violated(limit):
                    await self._handle_limit_violation(limit, "", "")
                    
        except Exception as e:
            self.logger.error(f"检查全局风险限额失败: {e}")
    
    async def _check_strategy_limits(self):
        """检查策略风险限额"""
        try:
            for strategy_id, limits in self._strategy_limits.items():
                if strategy_id not in self._strategies:
                    continue
                
                strategy = self._strategies[strategy_id]
                
                for limit in limits:
                    if not limit.enabled:
                        continue
                    
                    # 计算当前值
                    current_value = self._calculate_strategy_risk_value(strategy, limit)
                    limit.current_value = current_value
                    
                    # 检查是否违反限额
                    if self._is_limit_violated(limit):
                        await self._handle_limit_violation(limit, strategy_id, "")
                        
        except Exception as e:
            self.logger.error(f"检查策略风险限额失败: {e}")
    
    def _calculate_strategy_risk_value(self, strategy: BaseStrategy, limit: RiskLimit) -> float:
        """计算策略的风险指标值"""
        try:
            if "position" in limit.limit_id:
                # 仓位比例
                total_position_value = 0.0
                for position in strategy.get_all_positions().values():
                    total_position_value += float(position.market_value)
                
                if float(strategy.account_balance) > 0:
                    return total_position_value / float(strategy.account_balance)
                return 0.0
                
            elif "daily_loss" in limit.limit_id:
                # 单日亏损
                today = datetime.now().date()
                daily_pnl = 0.0
                
                for trade in strategy.get_trades():
                    if trade.timestamp.date() == today:
                        trade_pnl = float(trade.price * trade.quantity)
                        if trade.side == OrderSide.SELL:
                            daily_pnl += trade_pnl
                        else:
                            daily_pnl -= trade_pnl
                
                if float(strategy.config.initial_capital) > 0:
                    return abs(daily_pnl) / float(strategy.config.initial_capital)
                return 0.0
            
            return 0.0
            
        except Exception as e:
            self.logger.error(f"计算策略风险值失败: {e}")
            return 0.0
    
    def _is_limit_violated(self, limit: RiskLimit) -> bool:
        """检查限额是否被违反"""
        try:
            if limit.limit_id in ["cash_ratio"]:
                # 现金比例是下限
                return limit.current_value < limit.limit_value
            else:
                # 其他都是上限
                return limit.current_value > limit.limit_value
                
        except Exception as e:
            self.logger.error(f"检查限额违反失败: {e}")
            return False
    
    async def _handle_limit_violation(self, limit: RiskLimit, strategy_id: str, symbol: str):
        """处理限额违反"""
        try:
            # 确定风险等级
            ratio = limit.current_value / limit.limit_value
            if ratio >= limit.threshold_critical:
                risk_level = RiskLevel.CRITICAL
                action = limit.action_critical
            elif ratio >= limit.threshold_warning:
                risk_level = RiskLevel.MEDIUM
                action = limit.action_warning
            else:
                risk_level = RiskLevel.LOW
                action = RiskAction.NONE
            
            # 创建风险事件
            event = RiskEvent(
                event_id=str(uuid.uuid4()),
                timestamp=datetime.now(),
                risk_type=limit.risk_type,
                risk_level=risk_level,
                strategy_id=strategy_id,
                symbol=symbol,
                description=f"{limit.limit_name}违反: {limit.current_value:.4f} > {limit.limit_value:.4f}",
                current_value=limit.current_value,
                limit_value=limit.limit_value,
                action_taken=action
            )
            
            # 记录事件
            self._risk_events.append(event)
            self._active_events[event.event_id] = event
            
            # 执行风险处置
            await self._execute_risk_action(action, strategy_id, symbol, event)
            
            # 触发回调
            await self._trigger_risk_callback(risk_level, event)
            
            self.logger.warning(f"风险限额违反: {event.description}")
            
        except Exception as e:
            self.logger.error(f"处理限额违反失败: {e}")
    
    async def _execute_risk_action(self, action: RiskAction, strategy_id: str, 
                                 symbol: str, event: RiskEvent):
        """执行风险处置动作"""
        try:
            if action == RiskAction.NONE:
                return
            
            elif action == RiskAction.WARNING:
                self.logger.warning(f"风险警告: {event.description}")
                
            elif action == RiskAction.REDUCE_POSITION:
                if strategy_id in self._strategies:
                    strategy = self._strategies[strategy_id]
                    if symbol:
                        # 减少特定品种仓位
                        await strategy.close_position(symbol, ratio=0.5)
                    else:
                        # 减少所有仓位
                        for pos_symbol in strategy.get_all_positions().keys():
                            await strategy.close_position(pos_symbol, ratio=0.3)
                
            elif action == RiskAction.CLOSE_POSITION:
                if strategy_id in self._strategies:
                    strategy = self._strategies[strategy_id]
                    if symbol:
                        await strategy.close_position(symbol)
                    else:
                        await strategy.close_all_positions()
                
            elif action == RiskAction.STOP_TRADING:
                if strategy_id in self._strategies:
                    strategy = self._strategies[strategy_id]
                    await strategy.pause()
                
            elif action == RiskAction.EMERGENCY_STOP:
                # 紧急停止所有策略
                for strategy in self._strategies.values():
                    await strategy.close_all_positions()
                    await strategy.stop()
            
            self.logger.info(f"风险处置执行: {action.value} for {strategy_id}")
            
        except Exception as e:
            self.logger.error(f"执行风险处置失败: {e}")
    
    # ==================== 高级风险指标 ====================
    
    async def _calculate_advanced_metrics(self):
        """计算高级风险指标"""
        try:
            # 计算VaR
            await self._calculate_var()
            
            # 计算相关性
            await self._calculate_correlations()
            
            # 计算Beta值
            await self._calculate_betas()
            
        except Exception as e:
            self.logger.error(f"计算高级风险指标失败: {e}")
    
    async def _calculate_var(self):
        """计算Value at Risk"""
        try:
            for strategy_id, strategy in self._strategies.items():
                # 获取历史收益率
                returns = self._get_strategy_returns(strategy)
                
                if len(returns) < 30:  # 数据不足
                    continue
                
                # 计算VaR
                var_value = np.percentile(returns, (1 - self.config.var_confidence_level) * 100)
                
                # 缓存结果
                self._var_cache[strategy_id] = (datetime.now(), var_value)
                self._current_risks[f"{strategy_id}_var"] = abs(var_value)
                
        except Exception as e:
            self.logger.error(f"计算VaR失败: {e}")
    
    def _get_strategy_returns(self, strategy: BaseStrategy) -> List[float]:
        """获取策略历史收益率"""
        try:
            returns = []
            if hasattr(strategy, '_daily_returns'):
                returns = strategy._daily_returns[-self.config.var_history_days:]
            return returns
        except Exception as e:
            self.logger.error(f"获取策略收益率失败: {e}")
            return []
    
    async def _calculate_correlations(self):
        """计算策略间相关性"""
        try:
            if len(self._strategies) < 2:
                return
            
            # 收集所有策略的收益率数据
            returns_data = {}
            for strategy_id, strategy in self._strategies.items():
                returns = self._get_strategy_returns(strategy)
                if len(returns) >= 30:
                    returns_data[strategy_id] = returns
            
            if len(returns_data) >= 2:
                # 构建收益率DataFrame
                min_length = min(len(returns) for returns in returns_data.values())
                df_data = {}
                for strategy_id, returns in returns_data.items():
                    df_data[strategy_id] = returns[-min_length:]
                
                df = pd.DataFrame(df_data)
                self._correlation_matrix = df.corr()
                
        except Exception as e:
            self.logger.error(f"计算相关性失败: {e}")
    
    async def _calculate_betas(self):
        """计算Beta值"""
        try:
            if not self._benchmark_data:
                return
            
            # 获取基准收益率
            benchmark_returns = self._benchmark_data.pct_change().dropna()
            
            for strategy_id, strategy in self._strategies.items():
                returns = self._get_strategy_returns(strategy)
                
                if len(returns) >= 30:
                    # 计算Beta
                    returns_series = pd.Series(returns[-len(benchmark_returns):])
                    covariance = returns_series.cov(benchmark_returns)
                    variance = benchmark_returns.var()
                    
                    if variance > 0:
                        beta = covariance / variance
                        self._beta_cache[strategy_id] = beta
                        
        except Exception as e:
            self.logger.error(f"计算Beta失败: {e}")
    
    # ==================== 压力测试 ====================
    
    async def _stress_testing(self):
        """压力测试任务"""
        try:
            while self._is_monitoring:
                await self._run_stress_scenarios()
                await asyncio.sleep(self.config.stress_test_interval)
                
        except asyncio.CancelledError:
            pass
        except Exception as e:
            self.logger.error(f"压力测试异常: {e}")
    
    async def _run_stress_scenarios(self):
        """运行压力测试情景"""
        try:
            # 市场下跌情景
            await self._test_market_shock(-0.1)  # 10%下跌
            await self._test_market_shock(-0.2)  # 20%下跌
            
            # 波动率冲击
            await self._test_volatility_shock(2.0)  # 波动率翻倍
            
            # 流动性危机
            await self._test_liquidity_crisis()
            
        except Exception as e:
            self.logger.error(f"运行压力测试失败: {e}")
    
    async def _test_market_shock(self, shock_magnitude: float):
        """测试市场冲击情景"""
        try:
            self.logger.info(f"压力测试: 市场冲击 {shock_magnitude:.1%}")
            
            total_impact = 0.0
            
            for strategy in self._strategies.values():
                strategy_impact = 0.0
                
                for position in strategy.get_all_positions().values():
                    position_value = float(position.market_value)
                    
                    if position.side == PositionSide.LONG:
                        impact = position_value * shock_magnitude
                    else:
                        impact = -position_value * shock_magnitude
                    
                    strategy_impact += impact
                
                total_impact += strategy_impact
                
                # 检查策略是否能承受冲击
                strategy_capital = float(strategy.account_balance)
                impact_ratio = abs(strategy_impact) / strategy_capital if strategy_capital > 0 else 0
                
                if impact_ratio > 0.2:  # 超过20%损失
                    self.logger.warning(f"策略 {strategy.strategy_id} 在压力测试中损失 {impact_ratio:.2%}")
            
        except Exception as e:
            self.logger.error(f"市场冲击测试失败: {e}")
    
    async def _test_volatility_shock(self, volatility_multiplier: float):
        """测试波动率冲击"""
        try:
            self.logger.info(f"压力测试: 波动率冲击 {volatility_multiplier}x")
            
            # 计算各策略在高波动率环境下的风险
            for strategy in self._strategies.values():
                if strategy.strategy_id in self._var_cache:
                    current_var = self._var_cache[strategy.strategy_id][1]
                    stressed_var = current_var * volatility_multiplier
                    
                    # 检查是否超过风险承受能力
                    if abs(stressed_var) > 0.05:  # 超过5%的VaR
                        self.logger.warning(f"策略 {strategy.strategy_id} 在波动率冲击下VaR: {stressed_var:.2%}")
                        
        except Exception as e:
            self.logger.error(f"波动率冲击测试失败: {e}")
    
    async def _test_liquidity_crisis(self):
        """测试流动性危机"""
        try:
            self.logger.info("压力测试: 流动性危机")
            
            for strategy in self._strategies.values():
                cash_ratio = float(strategy.available_balance) / float(strategy.account_balance)
                
                if cash_ratio < 0.1:  # 现金比例过低
                    self.logger.warning(f"策略 {strategy.strategy_id} 流动性不足: 现金比例 {cash_ratio:.2%}")
                    
        except Exception as e:
            self.logger.error(f"流动性危机测试失败: {e}")
    
    # ==================== 事件处理 ====================
    
    async def _check_risk_events(self):
        """检查风险事件状态"""
        try:
            resolved_events = []
            
            for event_id, event in self._active_events.items():
                if self._is_event_resolved(event):
                    event.resolved = True
                    event.resolution_time = datetime.now()
                    resolved_events.append(event_id)
                    
                    self.logger.info(f"风险事件已解决: {event.description}")
            
            # 清理已解决的事件
            for event_id in resolved_events:
                del self._active_events[event_id]
                
        except Exception as e:
            self.logger.error(f"检查风险事件失败: {e}")
    
    def _is_event_resolved(self, event: RiskEvent) -> bool:
        """检查风险事件是否已解决"""
        try:
            # 检查相关风险指标是否恢复正常
            if event.risk_type == RiskType.MARKET_RISK:
                current_value = self._current_risks.get("total_exposure", 0)
                return current_value < event.limit_value * 0.9  # 恢复到限额的90%以下
            
            return False
            
        except Exception as e:
            self.logger.error(f"检查事件解决状态失败: {e}")
            return False
    
    def _cleanup_strategy_events(self, strategy_id: str):
        """清理策略相关的风险事件"""
        try:
            events_to_remove = []
            
            for event_id, event in self._active_events.items():
                if event.strategy_id == strategy_id:
                    events_to_remove.append(event_id)
            
            for event_id in events_to_remove:
                del self._active_events[event_id]
                
        except Exception as e:
            self.logger.error(f"清理策略事件失败: {e}")
    
    # ==================== 回调和通知 ====================
    
    def add_risk_callback(self, risk_level: RiskLevel, callback: Callable):
        """添加风险回调函数"""
        self._risk_callbacks[risk_level].append(callback)
    
    async def _trigger_risk_callback(self, risk_level: RiskLevel, event: RiskEvent):
        """触发风险回调"""
        try:
            for callback in self._risk_callbacks[risk_level]:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event)
                else:
                    callback(event)
                    
        except Exception as e:
            self.logger.error(f"触发风险回调失败: {e}")
    
    # ==================== 查询接口 ====================
    
    def get_current_risks(self) -> Dict[str, float]:
        """获取当前风险指标"""
        return self._current_risks.copy()
    
    def get_risk_events(self, active_only: bool = False) -> List[RiskEvent]:
        """获取风险事件"""
        if active_only:
            return list(self._active_events.values())
        return self._risk_events.copy()
    
    def get_strategy_limits(self, strategy_id: str) -> List[RiskLimit]:
        """获取策略风险限额"""
        return self._strategy_limits.get(strategy_id, []).copy()
    
    def get_global_limits(self) -> List[RiskLimit]:
        """获取全局风险限额"""
        return self._global_limits.copy()
    
    def get_var_values(self) -> Dict[str, float]:
        """获取VaR值"""
        var_values = {}
        for strategy_id, (timestamp, var_value) in self._var_cache.items():
            # 只返回最近计算的VaR
            if (datetime.now() - timestamp).seconds < 3600:  # 1小时内
                var_values[strategy_id] = var_value
        return var_values
    
    def get_correlation_matrix(self) -> Optional[pd.DataFrame]:
        """获取相关性矩阵"""
        return self._correlation_matrix.copy() if self._correlation_matrix is not None else None
    
    def get_beta_values(self) -> Dict[str, float]:
        """获取Beta值"""
        return self._beta_cache.copy()
    
    # ==================== 报告生成 ====================
    
    def generate_risk_report(self) -> Dict[str, Any]:
        """生成风险报告"""
        try:
            report = {
                "timestamp": datetime.now(),
                "summary": {
                    "total_strategies": len(self._strategies),
                    "active_events": len(self._active_events),
                    "total_events": len(self._risk_events),
                    "monitoring_status": self._is_monitoring
                },
                "current_risks": self._current_risks.copy(),
                "global_limits": [
                    {
                        "limit_name": limit.limit_name,
                        "current_value": limit.current_value,
                        "limit_value": limit.limit_value,
                        "utilization": limit.current_value / limit.limit_value if limit.limit_value > 0 else 0
                    }
                    for limit in self._global_limits
                ],
                "active_events": [
                    {
                        "event_id": event.event_id,
                        "risk_type": event.risk_type.value,
                        "risk_level": event.risk_level.value,
                        "strategy_id": event.strategy_id,
                        "description": event.description,
                        "timestamp": event.timestamp
                    }
                    for event in self._active_events.values()
                ],
                "var_values": self.get_var_values(),
                "beta_values": self.get_beta_values()
            }
            
            return report
            
        except Exception as e:
            self.logger.error(f"生成风险报告失败: {e}")
            return {}
    
    async def update_market_data(self, data: MarketData):
        """更新市场数据"""
        try:
            self._market_data[data.symbol] = data
            
            # 更新价格历史
            if data.symbol not in self._price_history:
                self._price_history[data.symbol] = []
            
            self._price_history[data.symbol].append(data.close)
            
            # 限制历史数据长度
            if len(self._price_history[data.symbol]) > 1000:
                self._price_history[data.symbol] = self._price_history[data.symbol][-500:]
                
        except Exception as e:
            self.logger.error(f"更新市场数据失败: {e}")
    
    # ==================== 预交易风险检查 ====================
    
    async def check_order_risk(self, order: OrderInfo, strategy: BaseStrategy) -> Tuple[bool, str]:
        """检查订单风险"""
        try:
            # 检查仓位限制
            position_check = await self._check_position_risk(order, strategy)
            if not position_check[0]:
                return position_check
            
            # 检查集中度风险
            concentration_check = await self._check_concentration_risk(order, strategy)
            if not concentration_check[0]:
                return concentration_check
            
            # 检查流动性风险
            liquidity_check = await self._check_liquidity_risk(order)
            if not liquidity_check[0]:
                return liquidity_check
            
            return True, "风险检查通过"
            
        except Exception as e:
            self.logger.error(f"订单风险检查失败: {e}")
            return False, f"风险检查异常: {e}"
    
    async def _check_position_risk(self, order: OrderInfo, strategy: BaseStrategy) -> Tuple[bool, str]:
        """检查仓位风险"""
        try:
            # 计算新订单后的总仓位
            current_position = strategy.get_position(order.symbol)
            current_size = float(current_position.quantity) if current_position else 0.0
            
            if order.side == OrderSide.BUY:
                new_size = current_size + float(order.quantity)
            else:
                new_size = current_size - float(order.quantity)
            
            # 检查单个品种仓位限制
            position_value = abs(new_size) * float(order.price or 0)
            capital = float(strategy.account_balance)
            
            if capital > 0:
                position_ratio = position_value / capital
                if position_ratio > self.config.max_single_position:
                    return False, f"单个品种仓位超限: {position_ratio:.2%} > {self.config.max_single_position:.2%}"
            
            return True, "仓位风险检查通过"
            
        except Exception as e:
            self.logger.error(f"仓位风险检查失败: {e}")
            return False, f"仓位风险检查异常: {e}"
    
    async def _check_concentration_risk(self, order: OrderInfo, strategy: BaseStrategy) -> Tuple[bool, str]:
        """检查集中度风险"""
        try:
            # 检查总敞口
            total_exposure = self._calculate_total_exposure()
            if total_exposure > self.config.max_total_exposure:
                return False, f"总敞口超限: {total_exposure:.2%} > {self.config.max_total_exposure:.2%}"
            
            return True, "集中度风险检查通过"
            
        except Exception as e:
            self.logger.error(f"集中度风险检查失败: {e}")
            return False, f"集中度风险检查异常: {e}"
    
    async def _check_liquidity_risk(self, order: OrderInfo) -> Tuple[bool, str]:
        """检查流动性风险"""
        try:
            # 检查市场数据可用性
            if order.symbol not in self._market_data:
                return False, f"缺少市场数据: {order.symbol}"
            
            market_data = self._market_data[order.symbol]
            
            # 检查成交量
            if market_data.volume <= 0:
                return False, f"缺少成交量数据: {order.symbol}"
            
            # 检查订单大小与成交量的比例
            order_value = float(order.quantity) * market_data.close
            volume_value = market_data.volume * market_data.close
            
            if volume_value > 0:
                size_ratio = order_value / volume_value
                if size_ratio > self.config.max_position_size_ratio:
                    return False, f"订单过大: {size_ratio:.2%} > {self.config.max_position_size_ratio:.2%}"
            
            return True, "流动性风险检查通过"
            
        except Exception as e:
            self.logger.error(f"流动性风险检查失败: {e}")
            return False, f"流动性风险检查异常: {e}"
