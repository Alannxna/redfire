"""
量化策略回测引擎

提供专业的策略回测功能，支持多种回测模式、
历史数据回放、绩效分析和风险评估。
"""

import logging
import asyncio
import pandas as pd
import numpy as np
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


class BacktestMode(Enum):
    """回测模式"""
    TICK = "tick"           # 逐Tick回测
    BAR = "bar"             # 逐K线回测
    EVENT_DRIVEN = "event"  # 事件驱动回测


class SlippageModel(Enum):
    """滑点模型"""
    FIXED = "fixed"         # 固定滑点
    PERCENTAGE = "percentage"  # 百分比滑点
    VOLUME_BASED = "volume"   # 基于成交量的滑点
    MARKET_IMPACT = "impact"  # 市场冲击模型


class CommissionModel(Enum):
    """手续费模型"""
    FIXED = "fixed"         # 固定手续费
    PERCENTAGE = "percentage"  # 百分比手续费
    TIERED = "tiered"       # 分层手续费


@dataclass
class BacktestConfig:
    """回测配置"""
    # 基础配置
    start_date: datetime
    end_date: datetime
    initial_capital: Decimal = Decimal("100000")
    
    # 回测模式
    mode: BacktestMode = BacktestMode.BAR
    frequency: str = "1D"  # 数据频率: 1m, 5m, 1h, 1D等
    
    # 交易成本模型
    commission_model: CommissionModel = CommissionModel.PERCENTAGE
    commission_rate: float = 0.0002
    min_commission: float = 5.0
    
    slippage_model: SlippageModel = SlippageModel.PERCENTAGE
    slippage_rate: float = 0.0001
    
    # 市场配置
    benchmark: Optional[str] = None  # 基准指数
    risk_free_rate: float = 0.03    # 无风险利率
    
    # 回测选项
    enable_short_selling: bool = True
    enable_margin_trading: bool = False
    margin_ratio: float = 1.0
    
    # 性能配置
    max_bars_in_memory: int = 10000
    enable_progress_bar: bool = True
    cache_results: bool = True


@dataclass
class BacktestResult:
    """回测结果"""
    # 基础信息
    start_date: datetime
    end_date: datetime
    total_days: int
    trading_days: int
    
    # 收益指标
    total_return: float = 0.0
    annual_return: float = 0.0
    cumulative_return: float = 0.0
    
    # 风险指标
    volatility: float = 0.0
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    max_drawdown: float = 0.0
    max_drawdown_duration: int = 0
    
    # 交易统计
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0
    
    profit_factor: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    largest_win: float = 0.0
    largest_loss: float = 0.0
    
    # 其他指标
    calmar_ratio: float = 0.0
    information_ratio: float = 0.0
    tracking_error: float = 0.0
    
    # 详细数据
    equity_curve: pd.DataFrame = field(default_factory=pd.DataFrame)
    trades: List[TradeInfo] = field(default_factory=list)
    positions: pd.DataFrame = field(default_factory=pd.DataFrame)
    benchmark_returns: Optional[pd.Series] = None


class BacktestEngine:
    """
    回测引擎
    
    提供完整的策略回测功能，包括历史数据回放、
    订单模拟、绩效分析等。
    """
    
    def __init__(self, config: BacktestConfig):
        """
        初始化回测引擎
        
        Args:
            config: 回测配置
        """
        self.config = config
        self.engine_id = str(uuid.uuid4())
        
        # 日志记录
        self.logger = logging.getLogger(f"backtest_engine.{self.engine_id}")
        
        # 策略管理
        self._strategy: Optional[BaseStrategy] = None
        
        # 数据管理
        self._data_provider: Optional[Callable] = None
        self._market_data: Dict[str, pd.DataFrame] = {}
        self._benchmark_data: Optional[pd.Series] = None
        
        # 回测状态
        self._current_time: datetime = config.start_date
        self._is_running = False
        self._current_bar_index = 0
        
        # 交易记录
        self._orders: List[OrderInfo] = []
        self._trades: List[TradeInfo] = []
        self._positions: Dict[str, PositionInfo] = {}
        self._cash = config.initial_capital
        self._total_value = config.initial_capital
        
        # 绩效记录
        self._equity_curve: List[Tuple[datetime, float]] = []
        self._daily_returns: List[float] = []
        self._benchmark_returns: List[float] = []
        
        # 交易成本计算器
        self._commission_calculator = self._create_commission_calculator()
        self._slippage_calculator = self._create_slippage_calculator()
        
        self.logger.info(f"回测引擎初始化完成: {self.engine_id}")
    
    # ==================== 数据管理 ====================
    
    def set_data_provider(self, provider: Callable[[str, datetime, datetime], pd.DataFrame]):
        """
        设置数据提供器
        
        Args:
            provider: 数据提供函数，返回DataFrame格式的历史数据
        """
        self._data_provider = provider
        self.logger.info("数据提供器设置完成")
    
    def load_data(self, symbols: List[str]) -> bool:
        """
        加载历史数据
        
        Args:
            symbols: 交易品种列表
            
        Returns:
            bool: 是否加载成功
        """
        try:
            if not self._data_provider:
                self.logger.error("未设置数据提供器")
                return False
            
            for symbol in symbols:
                self.logger.info(f"加载数据: {symbol}")
                data = self._data_provider(symbol, self.config.start_date, self.config.end_date)
                
                if data is None or data.empty:
                    self.logger.warning(f"数据为空: {symbol}")
                    continue
                
                # 数据验证和清洗
                data = self._clean_data(data)
                self._market_data[symbol] = data
                
                self.logger.info(f"数据加载完成: {symbol}, {len(data)} 条记录")
            
            # 加载基准数据
            if self.config.benchmark:
                self._load_benchmark_data()
            
            return len(self._market_data) > 0
            
        except Exception as e:
            self.logger.error(f"加载数据失败: {e}")
            return False
    
    def _clean_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """清洗数据"""
        try:
            # 确保必要的列存在
            required_columns = ['open', 'high', 'low', 'close', 'volume']
            for col in required_columns:
                if col not in data.columns:
                    self.logger.error(f"缺少必要列: {col}")
                    return pd.DataFrame()
            
            # 删除空值
            data = data.dropna()
            
            # 确保价格数据为正
            price_columns = ['open', 'high', 'low', 'close']
            for col in price_columns:
                data = data[data[col] > 0]
            
            # 确保价格逻辑正确
            data = data[data['high'] >= data['low']]
            data = data[data['high'] >= data['open']]
            data = data[data['high'] >= data['close']]
            data = data[data['low'] <= data['open']]
            data = data[data['low'] <= data['close']]
            
            # 排序
            data = data.sort_index()
            
            return data
            
        except Exception as e:
            self.logger.error(f"数据清洗失败: {e}")
            return pd.DataFrame()
    
    def _load_benchmark_data(self):
        """加载基准数据"""
        try:
            if not self.config.benchmark or not self._data_provider:
                return
            
            benchmark_data = self._data_provider(
                self.config.benchmark, 
                self.config.start_date, 
                self.config.end_date
            )
            
            if benchmark_data is not None and not benchmark_data.empty:
                self._benchmark_data = benchmark_data['close']
                self.logger.info(f"基准数据加载完成: {self.config.benchmark}")
                
        except Exception as e:
            self.logger.error(f"加载基准数据失败: {e}")
    
    # ==================== 回测执行 ====================
    
    async def run_backtest(self, strategy: BaseStrategy) -> BacktestResult:
        """
        运行回测
        
        Args:
            strategy: 策略实例
            
        Returns:
            BacktestResult: 回测结果
        """
        try:
            self._strategy = strategy
            self._is_running = True
            
            self.logger.info(f"开始回测: {strategy.strategy_name}")
            self.logger.info(f"回测期间: {self.config.start_date} - {self.config.end_date}")
            
            # 重置状态
            self._reset_state()
            
            # 初始化策略
            await strategy.start()
            
            # 执行回测
            if self.config.mode == BacktestMode.BAR:
                await self._run_bar_based_backtest()
            elif self.config.mode == BacktestMode.TICK:
                await self._run_tick_based_backtest()
            else:
                await self._run_event_driven_backtest()
            
            # 停止策略
            await strategy.stop()
            
            # 生成结果
            result = self._generate_result()
            
            self._is_running = False
            self.logger.info("回测完成")
            
            return result
            
        except Exception as e:
            self.logger.error(f"回测执行失败: {e}")
            self._is_running = False
            return BacktestResult(
                start_date=self.config.start_date,
                end_date=self.config.end_date,
                total_days=0,
                trading_days=0
            )
    
    def _reset_state(self):
        """重置回测状态"""
        self._current_time = self.config.start_date
        self._current_bar_index = 0
        self._cash = self.config.initial_capital
        self._total_value = self.config.initial_capital
        
        self._orders.clear()
        self._trades.clear()
        self._positions.clear()
        self._equity_curve.clear()
        self._daily_returns.clear()
        self._benchmark_returns.clear()
    
    async def _run_bar_based_backtest(self):
        """运行K线回测"""
        try:
            # 获取所有日期
            all_dates = set()
            for symbol_data in self._market_data.values():
                all_dates.update(symbol_data.index)
            
            sorted_dates = sorted(all_dates)
            total_bars = len(sorted_dates)
            
            for i, current_date in enumerate(sorted_dates):
                if not self._is_running:
                    break
                
                self._current_time = current_date
                self._current_bar_index = i
                
                # 处理当前时间点的数据
                for symbol, data in self._market_data.items():
                    if current_date in data.index:
                        bar_data = data.loc[current_date]
                        market_data = self._create_market_data(symbol, current_date, bar_data)
                        
                        # 发送数据到策略
                        await self._strategy._on_market_data(market_data)
                
                # 处理订单
                await self._process_pending_orders()
                
                # 更新组合价值
                self._update_portfolio_value()
                
                # 记录权益曲线
                self._equity_curve.append((current_date, float(self._total_value)))
                
                # 显示进度
                if self.config.enable_progress_bar and i % 100 == 0:
                    progress = (i + 1) / total_bars * 100
                    self.logger.info(f"回测进度: {progress:.1f}% ({i+1}/{total_bars})")
                
                # 内存管理
                if len(self._equity_curve) > self.config.max_bars_in_memory:
                    # 可以在这里实现数据清理逻辑
                    pass
                
        except Exception as e:
            self.logger.error(f"K线回测执行异常: {e}")
    
    async def _run_tick_based_backtest(self):
        """运行Tick回测"""
        # Tick回测的实现会更复杂，这里提供基础框架
        self.logger.warning("Tick回测功能尚未实现，使用K线模式")
        await self._run_bar_based_backtest()
    
    async def _run_event_driven_backtest(self):
        """运行事件驱动回测"""
        # 事件驱动回测的实现，这里提供基础框架
        self.logger.warning("事件驱动回测功能尚未实现，使用K线模式")
        await self._run_bar_based_backtest()
    
    def _create_market_data(self, symbol: str, timestamp: datetime, bar_data: pd.Series) -> MarketData:
        """创建市场数据对象"""
        return MarketData(
            symbol=symbol,
            timestamp=timestamp,
            open=float(bar_data['open']),
            high=float(bar_data['high']),
            low=float(bar_data['low']),
            close=float(bar_data['close']),
            volume=float(bar_data['volume'])
        )
    
    # ==================== 订单处理 ====================
    
    async def _process_pending_orders(self):
        """处理待执行订单"""
        try:
            # 获取当前未执行订单
            pending_orders = [order for order in self._orders if order.status == "pending"]
            
            for order in pending_orders:
                success = await self._execute_order(order)
                if success:
                    order.status = "filled"
                else:
                    order.status = "cancelled"
                    
        except Exception as e:
            self.logger.error(f"处理订单异常: {e}")
    
    async def _execute_order(self, order: OrderInfo) -> bool:
        """执行订单"""
        try:
            symbol = order.symbol
            
            # 检查是否有该品种的数据
            if symbol not in self._market_data:
                self.logger.warning(f"无数据执行订单: {symbol}")
                return False
            
            data = self._market_data[symbol]
            if self._current_time not in data.index:
                return False
            
            current_bar = data.loc[self._current_time]
            
            # 计算成交价格
            fill_price = self._calculate_fill_price(order, current_bar)
            if fill_price <= 0:
                return False
            
            # 计算滑点
            fill_price = self._apply_slippage(order, fill_price)
            
            # 计算手续费
            commission = self._calculate_commission(order, fill_price)
            
            # 检查资金是否充足
            if not self._check_sufficient_capital(order, fill_price, commission):
                self.logger.warning(f"资金不足执行订单: {order.order_id}")
                return False
            
            # 更新订单信息
            order.filled_quantity = order.quantity
            order.average_price = Decimal(str(fill_price))
            order.commission = Decimal(str(commission))
            
            # 创建成交记录
            trade = TradeInfo(
                trade_id=str(uuid.uuid4()),
                order_id=order.order_id,
                symbol=symbol,
                side=order.side,
                quantity=order.quantity,
                price=Decimal(str(fill_price)),
                timestamp=self._current_time,
                commission=Decimal(str(commission)),
                strategy_id=order.strategy_id
            )
            
            self._trades.append(trade)
            
            # 更新持仓
            self._update_position(trade)
            
            # 更新现金
            trade_value = float(trade.quantity * trade.price)
            if trade.side == OrderSide.BUY:
                self._cash -= Decimal(str(trade_value + commission))
            else:
                self._cash += Decimal(str(trade_value - commission))
            
            # 通知策略
            if self._strategy:
                await self._strategy._on_trade_filled(trade)
            
            return True
            
        except Exception as e:
            self.logger.error(f"执行订单失败: {e}")
            return False
    
    def _calculate_fill_price(self, order: OrderInfo, bar_data: pd.Series) -> float:
        """计算成交价格"""
        try:
            if order.order_type == OrderType.MARKET:
                # 市价单使用开盘价
                return float(bar_data['open'])
            elif order.order_type == OrderType.LIMIT:
                # 限价单检查是否可以成交
                limit_price = float(order.price)
                high_price = float(bar_data['high'])
                low_price = float(bar_data['low'])
                
                if order.side == OrderSide.BUY:
                    # 买单：限价 >= 最低价时成交
                    if limit_price >= low_price:
                        return min(limit_price, float(bar_data['open']))
                else:
                    # 卖单：限价 <= 最高价时成交
                    if limit_price <= high_price:
                        return max(limit_price, float(bar_data['open']))
                
                return 0  # 无法成交
            else:
                # 其他订单类型
                return float(bar_data['open'])
                
        except Exception as e:
            self.logger.error(f"计算成交价格失败: {e}")
            return 0
    
    def _apply_slippage(self, order: OrderInfo, price: float) -> float:
        """应用滑点"""
        try:
            slippage = self._slippage_calculator(order, price)
            
            if order.side == OrderSide.BUY:
                # 买入时价格上调
                return price * (1 + slippage)
            else:
                # 卖出时价格下调
                return price * (1 - slippage)
                
        except Exception as e:
            self.logger.error(f"计算滑点失败: {e}")
            return price
    
    def _calculate_commission(self, order: OrderInfo, price: float) -> float:
        """计算手续费"""
        try:
            return self._commission_calculator(order, price)
        except Exception as e:
            self.logger.error(f"计算手续费失败: {e}")
            return 0
    
    def _check_sufficient_capital(self, order: OrderInfo, price: float, commission: float) -> bool:
        """检查资金是否充足"""
        try:
            if order.side == OrderSide.BUY:
                required = float(order.quantity) * price + commission
                return float(self._cash) >= required
            else:
                # 卖出订单检查是否有足够持仓
                symbol = order.symbol
                if symbol in self._positions:
                    position = self._positions[symbol]
                    if position.side == PositionSide.LONG:
                        return float(position.quantity) >= float(order.quantity)
                return False
                
        except Exception as e:
            self.logger.error(f"检查资金充足性失败: {e}")
            return False
    
    def _update_position(self, trade: TradeInfo):
        """更新持仓"""
        try:
            symbol = trade.symbol
            
            if symbol not in self._positions:
                # 新建持仓
                side = PositionSide.LONG if trade.side == OrderSide.BUY else PositionSide.SHORT
                position = PositionInfo(
                    symbol=symbol,
                    side=side,
                    quantity=trade.quantity,
                    average_price=trade.price,
                    market_value=trade.quantity * trade.price,
                    unrealized_pnl=Decimal("0"),
                    timestamp=trade.timestamp
                )
                self._positions[symbol] = position
            else:
                # 更新现有持仓
                position = self._positions[symbol]
                
                if trade.side == OrderSide.BUY:
                    if position.side == PositionSide.LONG:
                        # 加多
                        total_cost = position.quantity * position.average_price + trade.quantity * trade.price
                        position.quantity += trade.quantity
                        position.average_price = total_cost / position.quantity
                    else:
                        # 平空
                        if trade.quantity >= position.quantity:
                            # 完全平仓或反手
                            remaining = trade.quantity - position.quantity
                            if remaining > 0:
                                position.side = PositionSide.LONG
                                position.quantity = remaining
                                position.average_price = trade.price
                            else:
                                del self._positions[symbol]
                                return
                        else:
                            position.quantity -= trade.quantity
                else:
                    if position.side == PositionSide.SHORT:
                        # 加空
                        total_cost = position.quantity * position.average_price + trade.quantity * trade.price
                        position.quantity += trade.quantity
                        position.average_price = total_cost / position.quantity
                    else:
                        # 平多
                        if trade.quantity >= position.quantity:
                            # 完全平仓或反手
                            remaining = trade.quantity - position.quantity
                            if remaining > 0:
                                position.side = PositionSide.SHORT
                                position.quantity = remaining
                                position.average_price = trade.price
                            else:
                                del self._positions[symbol]
                                return
                        else:
                            position.quantity -= trade.quantity
                
                # 更新市值
                current_price = self._get_current_price(symbol)
                if current_price > 0:
                    position.market_value = position.quantity * Decimal(str(current_price))
                    
                    # 更新未实现盈亏
                    if position.side == PositionSide.LONG:
                        position.unrealized_pnl = (Decimal(str(current_price)) - position.average_price) * position.quantity
                    else:
                        position.unrealized_pnl = (position.average_price - Decimal(str(current_price))) * position.quantity
                
        except Exception as e:
            self.logger.error(f"更新持仓失败: {e}")
    
    def _get_current_price(self, symbol: str) -> float:
        """获取当前价格"""
        try:
            if (symbol in self._market_data and 
                self._current_time in self._market_data[symbol].index):
                return float(self._market_data[symbol].loc[self._current_time]['close'])
            return 0
        except Exception as e:
            self.logger.error(f"获取当前价格失败: {e}")
            return 0
    
    def _update_portfolio_value(self):
        """更新组合价值"""
        try:
            total_market_value = Decimal("0")
            
            for position in self._positions.values():
                current_price = self._get_current_price(position.symbol)
                if current_price > 0:
                    market_value = position.quantity * Decimal(str(current_price))
                    total_market_value += market_value
            
            self._total_value = self._cash + total_market_value
            
        except Exception as e:
            self.logger.error(f"更新组合价值失败: {e}")
    
    # ==================== 交易成本计算器 ====================
    
    def _create_commission_calculator(self) -> Callable:
        """创建手续费计算器"""
        if self.config.commission_model == CommissionModel.FIXED:
            def fixed_commission(order: OrderInfo, price: float) -> float:
                return self.config.min_commission
            return fixed_commission
        
        elif self.config.commission_model == CommissionModel.PERCENTAGE:
            def percentage_commission(order: OrderInfo, price: float) -> float:
                trade_value = float(order.quantity) * price
                commission = trade_value * self.config.commission_rate
                return max(commission, self.config.min_commission)
            return percentage_commission
        
        else:
            def default_commission(order: OrderInfo, price: float) -> float:
                return 0
            return default_commission
    
    def _create_slippage_calculator(self) -> Callable:
        """创建滑点计算器"""
        if self.config.slippage_model == SlippageModel.FIXED:
            def fixed_slippage(order: OrderInfo, price: float) -> float:
                return self.config.slippage_rate
            return fixed_slippage
        
        elif self.config.slippage_model == SlippageModel.PERCENTAGE:
            def percentage_slippage(order: OrderInfo, price: float) -> float:
                return self.config.slippage_rate
            return percentage_slippage
        
        else:
            def no_slippage(order: OrderInfo, price: float) -> float:
                return 0
            return no_slippage
    
    # ==================== 结果生成 ====================
    
    def _generate_result(self) -> BacktestResult:
        """生成回测结果"""
        try:
            # 基础信息
            total_days = (self.config.end_date - self.config.start_date).days
            trading_days = len(self._equity_curve)
            
            # 转换权益曲线为DataFrame
            if self._equity_curve:
                equity_df = pd.DataFrame(self._equity_curve, columns=['date', 'equity'])
                equity_df.set_index('date', inplace=True)
                
                # 计算日收益率
                equity_df['returns'] = equity_df['equity'].pct_change()
                daily_returns = equity_df['returns'].dropna()
            else:
                equity_df = pd.DataFrame()
                daily_returns = pd.Series()
            
            # 计算收益指标
            total_return = self._calculate_total_return()
            annual_return = self._calculate_annual_return(total_return, trading_days)
            volatility = self._calculate_volatility(daily_returns)
            sharpe_ratio = self._calculate_sharpe_ratio(daily_returns)
            max_drawdown, max_dd_duration = self._calculate_max_drawdown(equity_df)
            
            # 计算交易统计
            trade_stats = self._calculate_trade_statistics()
            
            # 创建结果对象
            result = BacktestResult(
                start_date=self.config.start_date,
                end_date=self.config.end_date,
                total_days=total_days,
                trading_days=trading_days,
                
                total_return=total_return,
                annual_return=annual_return,
                cumulative_return=total_return,
                
                volatility=volatility,
                sharpe_ratio=sharpe_ratio,
                max_drawdown=max_drawdown,
                max_drawdown_duration=max_dd_duration,
                
                **trade_stats,
                
                equity_curve=equity_df,
                trades=self._trades.copy()
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"生成回测结果失败: {e}")
            return BacktestResult(
                start_date=self.config.start_date,
                end_date=self.config.end_date,
                total_days=0,
                trading_days=0
            )
    
    def _calculate_total_return(self) -> float:
        """计算总收益率"""
        try:
            if float(self.config.initial_capital) == 0:
                return 0.0
            
            return (float(self._total_value) - float(self.config.initial_capital)) / float(self.config.initial_capital)
            
        except Exception as e:
            self.logger.error(f"计算总收益率失败: {e}")
            return 0.0
    
    def _calculate_annual_return(self, total_return: float, trading_days: int) -> float:
        """计算年化收益率"""
        try:
            if trading_days <= 0:
                return 0.0
            
            years = trading_days / 252  # 假设每年252个交易日
            if years <= 0:
                return 0.0
            
            return (1 + total_return) ** (1 / years) - 1
            
        except Exception as e:
            self.logger.error(f"计算年化收益率失败: {e}")
            return 0.0
    
    def _calculate_volatility(self, returns: pd.Series) -> float:
        """计算波动率"""
        try:
            if len(returns) == 0:
                return 0.0
            
            return float(returns.std() * np.sqrt(252))  # 年化波动率
            
        except Exception as e:
            self.logger.error(f"计算波动率失败: {e}")
            return 0.0
    
    def _calculate_sharpe_ratio(self, returns: pd.Series) -> float:
        """计算夏普比率"""
        try:
            if len(returns) == 0:
                return 0.0
            
            excess_returns = returns - self.config.risk_free_rate / 252
            if excess_returns.std() == 0:
                return 0.0
            
            return float(excess_returns.mean() / excess_returns.std() * np.sqrt(252))
            
        except Exception as e:
            self.logger.error(f"计算夏普比率失败: {e}")
            return 0.0
    
    def _calculate_max_drawdown(self, equity_df: pd.DataFrame) -> Tuple[float, int]:
        """计算最大回撤"""
        try:
            if equity_df.empty:
                return 0.0, 0
            
            # 计算累计最高净值
            equity_df['cummax'] = equity_df['equity'].cummax()
            
            # 计算回撤
            equity_df['drawdown'] = (equity_df['equity'] - equity_df['cummax']) / equity_df['cummax']
            
            max_drawdown = float(equity_df['drawdown'].min())
            
            # 计算最大回撤持续时间
            max_dd_duration = 0
            current_dd_duration = 0
            
            for dd in equity_df['drawdown']:
                if dd < 0:
                    current_dd_duration += 1
                    max_dd_duration = max(max_dd_duration, current_dd_duration)
                else:
                    current_dd_duration = 0
            
            return abs(max_drawdown), max_dd_duration
            
        except Exception as e:
            self.logger.error(f"计算最大回撤失败: {e}")
            return 0.0, 0
    
    def _calculate_trade_statistics(self) -> Dict[str, Any]:
        """计算交易统计"""
        try:
            if not self._trades:
                return {
                    'total_trades': 0,
                    'winning_trades': 0,
                    'losing_trades': 0,
                    'win_rate': 0.0,
                    'profit_factor': 0.0,
                    'avg_win': 0.0,
                    'avg_loss': 0.0,
                    'largest_win': 0.0,
                    'largest_loss': 0.0
                }
            
            # 计算每笔交易的盈亏
            trade_pnls = []
            for trade in self._trades:
                # 这里需要更复杂的逻辑来计算实际盈亏
                # 暂时使用简化计算
                pnl = float(trade.price * trade.quantity) * (1 if trade.side == OrderSide.SELL else -1)
                trade_pnls.append(pnl)
            
            # 分离盈利和亏损交易
            wins = [pnl for pnl in trade_pnls if pnl > 0]
            losses = [pnl for pnl in trade_pnls if pnl < 0]
            
            total_trades = len(self._trades)
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
            
            return {
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'losing_trades': losing_trades,
                'win_rate': win_rate,
                'profit_factor': profit_factor,
                'avg_win': avg_win,
                'avg_loss': avg_loss,
                'largest_win': largest_win,
                'largest_loss': largest_loss
            }
            
        except Exception as e:
            self.logger.error(f"计算交易统计失败: {e}")
            return {}
    
    # ==================== 公共接口 ====================
    
    async def place_order_for_backtest(self, order: OrderInfo) -> bool:
        """回测中的下单接口"""
        try:
            self._orders.append(order)
            return True
        except Exception as e:
            self.logger.error(f"回测下单失败: {e}")
            return False
    
    def get_current_time(self) -> datetime:
        """获取当前回测时间"""
        return self._current_time
    
    def get_current_cash(self) -> Decimal:
        """获取当前现金"""
        return self._cash
    
    def get_current_value(self) -> Decimal:
        """获取当前总价值"""
        return self._total_value
    
    def get_positions(self) -> Dict[str, PositionInfo]:
        """获取当前持仓"""
        return self._positions.copy()
    
    def get_trades(self) -> List[TradeInfo]:
        """获取交易记录"""
        return self._trades.copy()
