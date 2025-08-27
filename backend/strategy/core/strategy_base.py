"""
量化策略基础框架

提供统一的策略开发基类，规范化策略接口和生命周期管理。
"""

import logging
import asyncio
import uuid
from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from decimal import Decimal


class StrategyState(Enum):
    """策略状态枚举"""
    UNKNOWN = "unknown"
    INITIALIZING = "initializing"
    INITIALIZED = "initialized"
    STARTING = "starting"
    RUNNING = "running"
    PAUSING = "pausing"
    PAUSED = "paused"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"
    CRASHED = "crashed"


class StrategyType(Enum):
    """策略类型枚举"""
    CTA = "cta"                    # 商品交易顾问策略
    ARBITRAGE = "arbitrage"        # 套利策略
    MARKET_MAKING = "market_making"  # 做市策略
    PAIRS_TRADING = "pairs_trading"  # 配对交易
    MOMENTUM = "momentum"          # 动量策略
    MEAN_REVERSION = "mean_reversion"  # 均值回归
    STATISTICAL = "statistical"   # 统计套利
    ML_BASED = "ml_based"         # 机器学习策略
    CUSTOM = "custom"             # 自定义策略


class OrderSide(Enum):
    """订单方向"""
    BUY = "buy"
    SELL = "sell"


class OrderType(Enum):
    """订单类型"""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class PositionSide(Enum):
    """持仓方向"""
    LONG = "long"
    SHORT = "short"
    NET = "net"


@dataclass
class StrategyConfig:
    """策略配置"""
    strategy_id: str
    strategy_name: str
    strategy_type: StrategyType
    
    # 基础配置
    symbols: List[str] = field(default_factory=list)
    timeframes: List[str] = field(default_factory=lambda: ["1m"])
    
    # 资金配置
    initial_capital: Decimal = Decimal("100000")
    max_position_size: Decimal = Decimal("0.1")  # 最大仓位比例
    max_leverage: float = 1.0
    
    # 风险控制
    max_drawdown: float = 0.05      # 最大回撤
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    position_timeout: Optional[int] = None  # 持仓超时(秒)
    
    # 交易配置
    commission_rate: float = 0.0002  # 手续费率
    slippage: float = 0.0001        # 滑点
    min_order_size: Decimal = Decimal("10")
    
    # 策略参数
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    # 运行配置
    enable_backtest: bool = False
    enable_live_trading: bool = False
    enable_paper_trading: bool = True
    auto_start: bool = False
    restart_on_error: bool = True
    max_restart_attempts: int = 3
    
    # 监控配置
    enable_monitoring: bool = True
    performance_update_interval: int = 60  # 秒
    log_level: str = "INFO"


@dataclass
class MarketData:
    """市场数据"""
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    amount: Optional[float] = None
    
    # Tick数据
    bid: Optional[float] = None
    ask: Optional[float] = None
    bid_size: Optional[float] = None
    ask_size: Optional[float] = None
    
    # 技术指标缓存
    indicators: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OrderInfo:
    """订单信息"""
    order_id: str
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: Decimal
    price: Optional[Decimal] = None
    stop_price: Optional[Decimal] = None
    status: str = "pending"
    timestamp: datetime = field(default_factory=datetime.now)
    filled_quantity: Decimal = Decimal("0")
    average_price: Optional[Decimal] = None
    commission: Decimal = Decimal("0")
    
    # 策略信息
    strategy_id: str = ""
    strategy_tag: str = ""


@dataclass
class TradeInfo:
    """成交信息"""
    trade_id: str
    order_id: str
    symbol: str
    side: OrderSide
    quantity: Decimal
    price: Decimal
    timestamp: datetime = field(default_factory=datetime.now)
    commission: Decimal = Decimal("0")
    
    # 策略信息
    strategy_id: str = ""


@dataclass
class PositionInfo:
    """持仓信息"""
    symbol: str
    side: PositionSide
    quantity: Decimal
    average_price: Decimal
    market_value: Decimal
    unrealized_pnl: Decimal
    realized_pnl: Decimal = Decimal("0")
    timestamp: datetime = field(default_factory=datetime.now)


class BaseStrategy(ABC):
    """
    量化策略基类
    
    所有策略都应该继承此类并实现抽象方法。
    提供完整的策略生命周期管理和事件处理机制。
    """
    
    def __init__(self, config: StrategyConfig):
        """
        初始化策略
        
        Args:
            config: 策略配置
        """
        self.config = config
        self.strategy_id = config.strategy_id
        self.strategy_name = config.strategy_name
        self.strategy_type = config.strategy_type
        
        # 状态管理
        self._state = StrategyState.UNKNOWN
        self._start_time: Optional[datetime] = None
        self._stop_time: Optional[datetime] = None
        self._error_count = 0
        self._restart_count = 0
        
        # 日志记录
        self.logger = logging.getLogger(f"strategy.{self.strategy_id}")
        self.logger.setLevel(getattr(logging, config.log_level.upper()))
        
        # 数据管理
        self._market_data: Dict[str, MarketData] = {}
        self._historical_data: Dict[str, pd.DataFrame] = {}
        self._indicators: Dict[str, Dict[str, Any]] = {}
        
        # 交易管理
        self._orders: Dict[str, OrderInfo] = {}
        self._trades: List[TradeInfo] = []
        self._positions: Dict[str, PositionInfo] = {}
        self._account_balance = config.initial_capital
        self._available_balance = config.initial_capital
        
        # 绩效统计
        self._performance_stats: Dict[str, Any] = {}
        self._daily_returns: List[float] = []
        self._equity_curve: List[tuple] = []
        
        # 风险控制
        self._daily_loss = Decimal("0")
        self._max_drawdown_reached = False
        self._position_sizes: Dict[str, Decimal] = {}
        
        # 回调函数
        self._event_callbacks: Dict[str, List[Callable]] = {
            "on_data": [],
            "on_order": [],
            "on_trade": [],
            "on_position": [],
            "on_error": [],
            "on_timer": []
        }
        
        # 定时器
        self._timers: Dict[str, asyncio.Task] = {}
        
        # 初始化策略
        self._state = StrategyState.INITIALIZING
        self._initialize()
        self._state = StrategyState.INITIALIZED
        
        self.logger.info(f"策略 {self.strategy_name} 初始化完成")
    
    def _initialize(self):
        """内部初始化方法"""
        # 初始化技术指标
        for symbol in self.config.symbols:
            self._indicators[symbol] = {}
            self._position_sizes[symbol] = Decimal("0")
    
    @property
    def state(self) -> StrategyState:
        """获取策略状态"""
        return self._state
    
    @property
    def is_running(self) -> bool:
        """策略是否正在运行"""
        return self._state == StrategyState.RUNNING
    
    @property
    def account_balance(self) -> Decimal:
        """账户余额"""
        return self._account_balance
    
    @property
    def available_balance(self) -> Decimal:
        """可用余额"""
        return self._available_balance
    
    @property
    def total_pnl(self) -> Decimal:
        """总盈亏"""
        realized_pnl = sum(trade.price * trade.quantity * (1 if trade.side == OrderSide.SELL else -1) 
                          for trade in self._trades)
        unrealized_pnl = sum(pos.unrealized_pnl for pos in self._positions.values())
        return realized_pnl + unrealized_pnl
    
    @property
    def performance_stats(self) -> Dict[str, Any]:
        """绩效统计"""
        return self._performance_stats.copy()
    
    # ==================== 生命周期方法 ====================
    
    async def start(self) -> bool:
        """启动策略"""
        try:
            if self._state == StrategyState.RUNNING:
                self.logger.warning("策略已经在运行")
                return True
            
            self._state = StrategyState.STARTING
            self.logger.info(f"启动策略: {self.strategy_name}")
            
            # 重置统计数据
            self._start_time = datetime.now()
            self._error_count = 0
            self._daily_loss = Decimal("0")
            self._max_drawdown_reached = False
            
            # 调用用户定义的启动逻辑
            await self.on_start()
            
            # 启动定时器
            await self._start_timers()
            
            self._state = StrategyState.RUNNING
            self.logger.info(f"策略 {self.strategy_name} 启动成功")
            return True
            
        except Exception as e:
            self._state = StrategyState.ERROR
            self.logger.error(f"策略启动失败: {e}")
            await self._handle_error(e)
            return False
    
    async def stop(self) -> bool:
        """停止策略"""
        try:
            if self._state == StrategyState.STOPPED:
                self.logger.warning("策略已经停止")
                return True
            
            self._state = StrategyState.STOPPING
            self.logger.info(f"停止策略: {self.strategy_name}")
            
            # 停止定时器
            await self._stop_timers()
            
            # 调用用户定义的停止逻辑
            await self.on_stop()
            
            # 记录停止时间
            self._stop_time = datetime.now()
            
            # 生成最终报告
            await self._generate_final_report()
            
            self._state = StrategyState.STOPPED
            self.logger.info(f"策略 {self.strategy_name} 停止成功")
            return True
            
        except Exception as e:
            self._state = StrategyState.ERROR
            self.logger.error(f"策略停止失败: {e}")
            return False
    
    async def pause(self) -> bool:
        """暂停策略"""
        try:
            if self._state != StrategyState.RUNNING:
                self.logger.warning("策略未在运行，无法暂停")
                return False
            
            self._state = StrategyState.PAUSING
            await self.on_pause()
            self._state = StrategyState.PAUSED
            
            self.logger.info(f"策略 {self.strategy_name} 已暂停")
            return True
            
        except Exception as e:
            self.logger.error(f"策略暂停失败: {e}")
            return False
    
    async def resume(self) -> bool:
        """恢复策略"""
        try:
            if self._state != StrategyState.PAUSED:
                self.logger.warning("策略未暂停，无法恢复")
                return False
            
            await self.on_resume()
            self._state = StrategyState.RUNNING
            
            self.logger.info(f"策略 {self.strategy_name} 已恢复")
            return True
            
        except Exception as e:
            self.logger.error(f"策略恢复失败: {e}")
            return False
    
    # ==================== 抽象方法 ====================
    
    @abstractmethod
    async def on_start(self):
        """策略启动时调用"""
        pass
    
    @abstractmethod
    async def on_stop(self):
        """策略停止时调用"""
        pass
    
    @abstractmethod
    async def on_tick(self, data: MarketData):
        """处理实时行情数据"""
        pass
    
    @abstractmethod
    async def on_bar(self, data: MarketData):
        """处理K线数据"""
        pass
    
    async def on_pause(self):
        """策略暂停时调用（可选重写）"""
        pass
    
    async def on_resume(self):
        """策略恢复时调用（可选重写）"""
        pass
    
    async def on_order_update(self, order: OrderInfo):
        """订单状态更新时调用（可选重写）"""
        pass
    
    async def on_trade_update(self, trade: TradeInfo):
        """成交更新时调用（可选重写）"""
        pass
    
    async def on_position_update(self, position: PositionInfo):
        """持仓更新时调用（可选重写）"""
        pass
    
    async def on_timer(self, timer_name: str):
        """定时器触发时调用（可选重写）"""
        pass
    
    async def on_error(self, error: Exception):
        """错误处理（可选重写）"""
        pass
    
    # ==================== 交易方法 ====================
    
    async def buy(self, symbol: str, quantity: Union[Decimal, float], 
                  price: Optional[Union[Decimal, float]] = None,
                  order_type: OrderType = OrderType.MARKET,
                  tag: str = "") -> str:
        """买入"""
        return await self._place_order(symbol, OrderSide.BUY, quantity, price, order_type, tag)
    
    async def sell(self, symbol: str, quantity: Union[Decimal, float],
                   price: Optional[Union[Decimal, float]] = None,
                   order_type: OrderType = OrderType.MARKET,
                   tag: str = "") -> str:
        """卖出"""
        return await self._place_order(symbol, OrderSide.SELL, quantity, price, order_type, tag)
    
    async def close_position(self, symbol: str, ratio: float = 1.0) -> List[str]:
        """平仓"""
        order_ids = []
        
        if symbol in self._positions:
            position = self._positions[symbol]
            close_quantity = position.quantity * Decimal(str(ratio))
            
            if position.side == PositionSide.LONG:
                order_id = await self.sell(symbol, close_quantity, tag="close_long")
            elif position.side == PositionSide.SHORT:
                order_id = await self.buy(symbol, close_quantity, tag="close_short")
            
            if order_id:
                order_ids.append(order_id)
        
        return order_ids
    
    async def close_all_positions(self) -> List[str]:
        """平所有仓"""
        order_ids = []
        for symbol in list(self._positions.keys()):
            symbol_orders = await self.close_position(symbol)
            order_ids.extend(symbol_orders)
        return order_ids
    
    async def _place_order(self, symbol: str, side: OrderSide, 
                          quantity: Union[Decimal, float],
                          price: Optional[Union[Decimal, float]] = None,
                          order_type: OrderType = OrderType.MARKET,
                          tag: str = "") -> str:
        """下单"""
        try:
            # 风险检查
            if not await self._check_risk_before_order(symbol, side, quantity):
                return ""
            
            # 创建订单
            order_id = str(uuid.uuid4())
            order = OrderInfo(
                order_id=order_id,
                symbol=symbol,
                side=side,
                order_type=order_type,
                quantity=Decimal(str(quantity)),
                price=Decimal(str(price)) if price else None,
                strategy_id=self.strategy_id,
                strategy_tag=tag
            )
            
            # 保存订单
            self._orders[order_id] = order
            
            # 发送订单（这里应该连接到实际的交易接口）
            success = await self._send_order_to_exchange(order)
            
            if success:
                self.logger.info(f"下单成功: {side.value} {quantity} {symbol} @ {price}")
                return order_id
            else:
                del self._orders[order_id]
                return ""
                
        except Exception as e:
            self.logger.error(f"下单失败: {e}")
            return ""
    
    async def _send_order_to_exchange(self, order: OrderInfo) -> bool:
        """发送订单到交易所（模拟实现）"""
        # 这里应该实现真实的交易所接口
        # 目前为模拟实现
        await asyncio.sleep(0.1)  # 模拟网络延迟
        
        # 模拟成交
        order.status = "filled"
        order.filled_quantity = order.quantity
        order.average_price = order.price or self._get_current_price(order.symbol)
        
        # 触发成交事件
        trade = TradeInfo(
            trade_id=str(uuid.uuid4()),
            order_id=order.order_id,
            symbol=order.symbol,
            side=order.side,
            quantity=order.quantity,
            price=order.average_price,
            strategy_id=self.strategy_id
        )
        
        await self._on_trade_filled(trade)
        return True
    
    def _get_current_price(self, symbol: str) -> Decimal:
        """获取当前价格"""
        if symbol in self._market_data:
            return Decimal(str(self._market_data[symbol].close))
        return Decimal("0")
    
    # ==================== 风险控制 ====================
    
    async def _check_risk_before_order(self, symbol: str, side: OrderSide, 
                                     quantity: Union[Decimal, float]) -> bool:
        """下单前风险检查"""
        try:
            quantity = Decimal(str(quantity))
            
            # 检查可用余额
            required_margin = quantity * self._get_current_price(symbol)
            if required_margin > self._available_balance:
                self.logger.warning(f"余额不足: 需要 {required_margin}, 可用 {self._available_balance}")
                return False
            
            # 检查最大仓位
            current_position = self._position_sizes.get(symbol, Decimal("0"))
            if side == OrderSide.BUY:
                new_position = current_position + quantity
            else:
                new_position = current_position - quantity
            
            max_position = self.config.initial_capital * Decimal(str(self.config.max_position_size))
            if abs(new_position * self._get_current_price(symbol)) > max_position:
                self.logger.warning(f"超出最大仓位限制")
                return False
            
            # 检查最大回撤
            if self._max_drawdown_reached:
                self.logger.warning(f"达到最大回撤限制，停止交易")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"风险检查失败: {e}")
            return False
    
    # ==================== 事件处理 ====================
    
    async def _on_market_data(self, data: MarketData):
        """处理市场数据"""
        try:
            if self._state != StrategyState.RUNNING:
                return
            
            # 更新市场数据
            self._market_data[data.symbol] = data
            
            # 更新持仓盈亏
            await self._update_position_pnl(data)
            
            # 检查风险控制
            await self._check_risk_controls()
            
            # 调用策略逻辑
            if hasattr(data, 'bid') and data.bid is not None:
                # Tick数据
                await self.on_tick(data)
            else:
                # K线数据
                await self.on_bar(data)
                
        except Exception as e:
            await self._handle_error(e)
    
    async def _on_trade_filled(self, trade: TradeInfo):
        """处理成交"""
        try:
            self._trades.append(trade)
            
            # 更新持仓
            await self._update_position(trade)
            
            # 更新余额
            trade_value = trade.quantity * trade.price
            if trade.side == OrderSide.BUY:
                self._available_balance -= trade_value
            else:
                self._available_balance += trade_value
            
            # 调用用户回调
            await self.on_trade_update(trade)
            
            self.logger.info(f"成交: {trade.side.value} {trade.quantity} {trade.symbol} @ {trade.price}")
            
        except Exception as e:
            await self._handle_error(e)
    
    async def _update_position(self, trade: TradeInfo):
        """更新持仓"""
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
                unrealized_pnl=Decimal("0")
            )
            self._positions[symbol] = position
        else:
            # 更新现有持仓
            position = self._positions[symbol]
            
            if trade.side == OrderSide.BUY:
                # 买入
                if position.side == PositionSide.SHORT:
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
                        # 部分平仓
                        position.quantity -= trade.quantity
                else:
                    # 加多
                    total_value = position.quantity * position.average_price + trade.quantity * trade.price
                    position.quantity += trade.quantity
                    position.average_price = total_value / position.quantity
            else:
                # 卖出
                if position.side == PositionSide.LONG:
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
                        # 部分平仓
                        position.quantity -= trade.quantity
                else:
                    # 加空
                    total_value = position.quantity * position.average_price + trade.quantity * trade.price
                    position.quantity += trade.quantity
                    position.average_price = total_value / position.quantity
            
            # 更新市值
            current_price = self._get_current_price(symbol)
            position.market_value = position.quantity * current_price
        
        # 更新持仓大小缓存
        if symbol in self._positions:
            pos = self._positions[symbol]
            self._position_sizes[symbol] = pos.quantity if pos.side == PositionSide.LONG else -pos.quantity
        else:
            self._position_sizes[symbol] = Decimal("0")
    
    async def _update_position_pnl(self, data: MarketData):
        """更新持仓盈亏"""
        symbol = data.symbol
        if symbol in self._positions:
            position = self._positions[symbol]
            current_price = Decimal(str(data.close))
            
            if position.side == PositionSide.LONG:
                position.unrealized_pnl = (current_price - position.average_price) * position.quantity
            else:
                position.unrealized_pnl = (position.average_price - current_price) * position.quantity
            
            position.market_value = position.quantity * current_price
    
    async def _check_risk_controls(self):
        """检查风险控制"""
        # 检查最大回撤
        total_pnl = self.total_pnl
        if total_pnl < 0:
            drawdown = abs(float(total_pnl)) / float(self.config.initial_capital)
            if drawdown > self.config.max_drawdown:
                self._max_drawdown_reached = True
                await self.close_all_positions()
                self.logger.warning(f"达到最大回撤 {drawdown:.2%}，强制平仓")
    
    # ==================== 定时器管理 ====================
    
    def add_timer(self, name: str, interval: float, callback: Optional[Callable] = None):
        """添加定时器"""
        async def timer_task():
            while self._state == StrategyState.RUNNING:
                try:
                    if callback:
                        await callback()
                    else:
                        await self.on_timer(name)
                    await asyncio.sleep(interval)
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    self.logger.error(f"定时器 {name} 执行异常: {e}")
        
        self._timers[name] = asyncio.create_task(timer_task())
    
    async def _start_timers(self):
        """启动定时器"""
        # 添加性能统计定时器
        self.add_timer("performance", self.config.performance_update_interval, 
                      self._update_performance_stats)
    
    async def _stop_timers(self):
        """停止定时器"""
        for timer in self._timers.values():
            timer.cancel()
        self._timers.clear()
    
    # ==================== 绩效统计 ====================
    
    async def _update_performance_stats(self):
        """更新绩效统计"""
        try:
            current_time = datetime.now()
            total_pnl = self.total_pnl
            
            # 计算收益率
            if self.config.initial_capital > 0:
                total_return = float(total_pnl) / float(self.config.initial_capital)
            else:
                total_return = 0.0
            
            # 计算年化收益率
            if self._start_time:
                days = (current_time - self._start_time).days + 1
                annual_return = total_return * 365 / days if days > 0 else 0.0
            else:
                annual_return = 0.0
            
            # 更新权益曲线
            self._equity_curve.append((current_time, float(self.config.initial_capital + total_pnl)))
            
            # 计算其他指标
            trade_count = len(self._trades)
            winning_trades = len([t for t in self._trades if self._calculate_trade_pnl(t) > 0])
            win_rate = winning_trades / trade_count if trade_count > 0 else 0.0
            
            self._performance_stats = {
                "timestamp": current_time,
                "total_pnl": float(total_pnl),
                "total_return": total_return,
                "annual_return": annual_return,
                "trade_count": trade_count,
                "winning_trades": winning_trades,
                "losing_trades": trade_count - winning_trades,
                "win_rate": win_rate,
                "current_positions": len(self._positions),
                "account_balance": float(self._account_balance),
                "available_balance": float(self._available_balance),
                "equity": float(self.config.initial_capital + total_pnl)
            }
            
        except Exception as e:
            self.logger.error(f"更新绩效统计失败: {e}")
    
    def _calculate_trade_pnl(self, trade: TradeInfo) -> float:
        """计算单笔交易盈亏"""
        # 这里需要更复杂的逻辑来计算实际盈亏
        # 暂时返回0
        return 0.0
    
    # ==================== 错误处理 ====================
    
    async def _handle_error(self, error: Exception):
        """错误处理"""
        self._error_count += 1
        self.logger.error(f"策略执行异常 (第{self._error_count}次): {error}")
        
        # 调用用户错误处理
        try:
            await self.on_error(error)
        except Exception as e:
            self.logger.error(f"用户错误处理异常: {e}")
        
        # 检查是否需要重启
        if (self.config.restart_on_error and 
            self._restart_count < self.config.max_restart_attempts):
            
            self._restart_count += 1
            self.logger.info(f"尝试重启策略 (第{self._restart_count}次)")
            
            await self.stop()
            await asyncio.sleep(5)  # 等待5秒
            await self.start()
        else:
            self._state = StrategyState.CRASHED
            self.logger.error("策略崩溃，无法恢复")
    
    async def _generate_final_report(self):
        """生成最终报告"""
        try:
            await self._update_performance_stats()
            
            self.logger.info("=== 策略执行报告 ===")
            self.logger.info(f"策略名称: {self.strategy_name}")
            self.logger.info(f"运行时间: {self._start_time} - {self._stop_time}")
            
            if self._performance_stats:
                stats = self._performance_stats
                self.logger.info(f"总收益: {stats.get('total_pnl', 0):.4f}")
                self.logger.info(f"收益率: {stats.get('total_return', 0):.2%}")
                self.logger.info(f"年化收益: {stats.get('annual_return', 0):.2%}")
                self.logger.info(f"交易次数: {stats.get('trade_count', 0)}")
                self.logger.info(f"胜率: {stats.get('win_rate', 0):.2%}")
            
            self.logger.info("==================")
            
        except Exception as e:
            self.logger.error(f"生成最终报告失败: {e}")
    
    # ==================== 工具方法 ====================
    
    def log_info(self, message: str):
        """记录信息日志"""
        self.logger.info(message)
    
    def log_warning(self, message: str):
        """记录警告日志"""
        self.logger.warning(message)
    
    def log_error(self, message: str):
        """记录错误日志"""
        self.logger.error(message)
    
    def get_position(self, symbol: str) -> Optional[PositionInfo]:
        """获取持仓信息"""
        return self._positions.get(symbol)
    
    def get_all_positions(self) -> Dict[str, PositionInfo]:
        """获取所有持仓"""
        return self._positions.copy()
    
    def get_order(self, order_id: str) -> Optional[OrderInfo]:
        """获取订单信息"""
        return self._orders.get(order_id)
    
    def get_all_orders(self) -> Dict[str, OrderInfo]:
        """获取所有订单"""
        return self._orders.copy()
    
    def get_trades(self) -> List[TradeInfo]:
        """获取成交记录"""
        return self._trades.copy()
    
    def get_market_data(self, symbol: str) -> Optional[MarketData]:
        """获取市场数据"""
        return self._market_data.get(symbol)
