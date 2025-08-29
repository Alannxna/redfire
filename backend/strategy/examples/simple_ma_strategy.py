"""
简单移动平均策略示例

演示如何使用RedFire策略框架开发基础的趋势跟随策略。
"""

from typing import Dict, List
from collections import deque
from datetime import datetime

from ..core.strategy_base import (
    BaseStrategy, StrategyConfig, StrategyType, MarketData, OrderSide
)


class SimpleMAStrategy(BaseStrategy):
    """
    简单移动平均策略
    
    基于短期和长期移动平均线的交叉信号进行交易。
    当短期均线上穿长期均线时买入，下穿时卖出。
    """
    
    def __init__(self, config: StrategyConfig):
        super().__init__(config)
        
        # 策略参数
        self.short_window = config.parameters.get('short_window', 5)
        self.long_window = config.parameters.get('long_window', 20)
        self.position_size = config.parameters.get('position_size', 100)
        
        # 数据存储
        self.price_data: Dict[str, deque] = {}
        self.short_ma_data: Dict[str, deque] = {}
        self.long_ma_data: Dict[str, deque] = {}
        
        # 信号状态
        self.last_signals: Dict[str, str] = {}
        
        # 初始化每个品种的数据结构
        for symbol in self.config.symbols:
            self.price_data[symbol] = deque(maxlen=self.long_window)
            self.short_ma_data[symbol] = deque(maxlen=100)
            self.long_ma_data[symbol] = deque(maxlen=100)
            self.last_signals[symbol] = None
        
        self.log_info(f"策略初始化完成 - 短期窗口: {self.short_window}, 长期窗口: {self.long_window}")
    
    async def on_start(self):
        """策略启动"""
        self.log_info(f"移动平均策略启动 - 交易品种: {self.config.symbols}")
        
        # 重置统计数据
        for symbol in self.config.symbols:
            self.price_data[symbol].clear()
            self.short_ma_data[symbol].clear()
            self.long_ma_data[symbol].clear()
            self.last_signals[symbol] = None
    
    async def on_stop(self):
        """策略停止"""
        self.log_info("移动平均策略停止")
        
        # 平仓所有持仓
        positions = self.get_all_positions()
        for symbol in positions.keys():
            await self.close_position(symbol)
            self.log_info(f"平仓: {symbol}")
        
        # 输出最终统计
        self._log_performance_summary()
    
    async def on_tick(self, data: MarketData):
        """处理tick数据"""
        try:
            symbol = data.symbol
            
            if symbol not in self.config.symbols:
                return
            
            price = data.close
            if price <= 0:
                return
            
            # 添加价格数据
            self.price_data[symbol].append(price)
            
            # 计算移动平均线
            if len(self.price_data[symbol]) >= self.long_window:
                await self._calculate_indicators(symbol)
                await self._check_signals(symbol, data)
        
        except Exception as e:
            self.log_error(f"处理tick数据异常: {e}")
    
    async def on_bar(self, data: MarketData):
        """处理K线数据"""
        # 使用收盘价进行计算
        await self.on_tick(data)
    
    async def _calculate_indicators(self, symbol: str):
        """计算技术指标"""
        try:
            price_list = list(self.price_data[symbol])
            
            # 计算短期移动平均
            if len(price_list) >= self.short_window:
                short_ma = sum(price_list[-self.short_window:]) / self.short_window
                self.short_ma_data[symbol].append(short_ma)
            
            # 计算长期移动平均
            if len(price_list) >= self.long_window:
                long_ma = sum(price_list[-self.long_window:]) / self.long_window
                self.long_ma_data[symbol].append(long_ma)
        
        except Exception as e:
            self.log_error(f"计算指标异常: {e}")
    
    async def _check_signals(self, symbol: str, data: MarketData):
        """检查交易信号"""
        try:
            short_ma_data = self.short_ma_data[symbol]
            long_ma_data = self.long_ma_data[symbol]
            
            if len(short_ma_data) < 2 or len(long_ma_data) < 2:
                return
            
            short_ma_current = short_ma_data[-1]
            short_ma_previous = short_ma_data[-2]
            long_ma_current = long_ma_data[-1]
            long_ma_previous = long_ma_data[-2]
            
            # 金叉信号 - 短期均线上穿长期均线
            if (short_ma_previous <= long_ma_previous and 
                short_ma_current > long_ma_current and 
                self.last_signals[symbol] != 'buy'):
                
                await self._generate_buy_signal(symbol, data)
                self.last_signals[symbol] = 'buy'
            
            # 死叉信号 - 短期均线下穿长期均线
            elif (short_ma_previous >= long_ma_previous and 
                  short_ma_current < long_ma_current and 
                  self.last_signals[symbol] != 'sell'):
                
                await self._generate_sell_signal(symbol, data)
                self.last_signals[symbol] = 'sell'
        
        except Exception as e:
            self.log_error(f"检查信号异常: {e}")
    
    async def _generate_buy_signal(self, symbol: str, data: MarketData):
        """生成买入信号"""
        try:
            position = self.get_position(symbol)
            current_price = data.close
            
            if not position:
                # 开多仓
                order_id = await self.buy(symbol, self.position_size, price=current_price)
                if order_id:
                    self.log_info(f"开多仓 - {symbol} @ {current_price:.4f}, 数量: {self.position_size}")
                    self._log_signal_details(symbol, "买入", current_price)
            elif position.side.value == "short":
                # 平空开多
                await self.close_position(symbol)
                order_id = await self.buy(symbol, self.position_size, price=current_price)
                if order_id:
                    self.log_info(f"平空开多 - {symbol} @ {current_price:.4f}")
        
        except Exception as e:
            self.log_error(f"生成买入信号异常: {e}")
    
    async def _generate_sell_signal(self, symbol: str, data: MarketData):
        """生成卖出信号"""
        try:
            position = self.get_position(symbol)
            current_price = data.close
            
            if not position:
                # 开空仓（如果支持做空）
                if self.config.enable_short_selling:
                    order_id = await self.sell(symbol, self.position_size, price=current_price)
                    if order_id:
                        self.log_info(f"开空仓 - {symbol} @ {current_price:.4f}, 数量: {self.position_size}")
                        self._log_signal_details(symbol, "卖出", current_price)
            elif position.side.value == "long":
                # 平多仓
                await self.close_position(symbol)
                self.log_info(f"平多仓 - {symbol} @ {current_price:.4f}")
                
                # 如果支持做空，继续开空
                if self.config.enable_short_selling:
                    order_id = await self.sell(symbol, self.position_size, price=current_price)
                    if order_id:
                        self.log_info(f"平多开空 - {symbol} @ {current_price:.4f}")
        
        except Exception as e:
            self.log_error(f"生成卖出信号异常: {e}")
    
    def _log_signal_details(self, symbol: str, signal_type: str, price: float):
        """记录信号详情"""
        try:
            short_ma = self.short_ma_data[symbol][-1] if self.short_ma_data[symbol] else 0
            long_ma = self.long_ma_data[symbol][-1] if self.long_ma_data[symbol] else 0
            
            self.log_info(f"信号详情 - {signal_type} {symbol}:")
            self.log_info(f"  当前价格: {price:.4f}")
            self.log_info(f"  短期MA({self.short_window}): {short_ma:.4f}")
            self.log_info(f"  长期MA({self.long_window}): {long_ma:.4f}")
            self.log_info(f"  MA差值: {(short_ma - long_ma):.4f}")
        
        except Exception as e:
            self.log_error(f"记录信号详情异常: {e}")
    
    def _log_performance_summary(self):
        """输出性能总结"""
        try:
            stats = self.performance_stats
            
            self.log_info("=== 移动平均策略性能总结 ===")
            self.log_info(f"策略名称: {self.strategy_name}")
            self.log_info(f"运行时长: {self._start_time} - {datetime.now()}")
            self.log_info(f"交易品种: {', '.join(self.config.symbols)}")
            self.log_info(f"参数配置: MA({self.short_window}, {self.long_window})")
            
            if stats:
                self.log_info(f"总交易次数: {stats.get('total_trades', 0)}")
                self.log_info(f"盈利交易: {stats.get('winning_trades', 0)}")
                self.log_info(f"亏损交易: {stats.get('losing_trades', 0)}")
                self.log_info(f"胜率: {stats.get('win_rate', 0):.2%}")
                self.log_info(f"总盈亏: {stats.get('total_pnl', 0):.4f}")
                self.log_info(f"收益率: {stats.get('total_return', 0):.2%}")
            
            # 输出每个品种的持仓状态
            positions = self.get_all_positions()
            if positions:
                self.log_info("最终持仓:")
                for symbol, position in positions.items():
                    self.log_info(f"  {symbol}: {position.side.value} {position.quantity} @ {position.average_price}")
            else:
                self.log_info("无持仓")
            
            self.log_info("============================")
        
        except Exception as e:
            self.log_error(f"输出性能总结异常: {e}")
    
    async def on_order_update(self, order):
        """订单状态更新回调"""
        self.log_info(f"订单更新: {order.symbol} {order.side.value} {order.status}")
    
    async def on_trade_update(self, trade):
        """成交更新回调"""
        self.log_info(f"成交确认: {trade.symbol} {trade.side.value} {trade.quantity}@{trade.price}")
    
    async def on_position_update(self, position):
        """持仓更新回调"""
        self.log_info(f"持仓更新: {position.symbol} {position.side.value} {position.quantity}")
    
    def get_strategy_info(self) -> Dict[str, any]:
        """获取策略信息"""
        return {
            'strategy_type': 'Simple Moving Average',
            'parameters': {
                'short_window': self.short_window,
                'long_window': self.long_window,
                'position_size': self.position_size
            },
            'indicators': {
                'short_ma_values': {symbol: list(ma_data)[-5:] if ma_data else [] 
                                  for symbol, ma_data in self.short_ma_data.items()},
                'long_ma_values': {symbol: list(ma_data)[-5:] if ma_data else [] 
                                 for symbol, ma_data in self.long_ma_data.items()}
            },
            'last_signals': self.last_signals.copy()
        }


def create_simple_ma_strategy(strategy_id: str, 
                             symbols: List[str], 
                             short_window: int = 5,
                             long_window: int = 20,
                             position_size: int = 100,
                             initial_capital: float = 100000) -> SimpleMAStrategy:
    """
    创建简单移动平均策略实例
    
    Args:
        strategy_id: 策略ID
        symbols: 交易品种列表
        short_window: 短期移动平均窗口
        long_window: 长期移动平均窗口
        position_size: 每次交易的数量
        initial_capital: 初始资金
        
    Returns:
        SimpleMAStrategy: 策略实例
    """
    config = StrategyConfig(
        strategy_id=strategy_id,
        strategy_name=f"简单移动平均策略_{strategy_id}",
        strategy_type=StrategyType.MOMENTUM,
        symbols=symbols,
        initial_capital=initial_capital,
        parameters={
            'short_window': short_window,
            'long_window': long_window,
            'position_size': position_size
        }
    )
    
    return SimpleMAStrategy(config)


# 使用示例
if __name__ == "__main__":
    import asyncio
    
    async def example_usage():
        """示例用法"""
        
        # 创建策略
        strategy = create_simple_ma_strategy(
            strategy_id="ma_demo_001",
            symbols=["BTCUSDT", "ETHUSDT"],
            short_window=5,
            long_window=20,
            position_size=100,
            initial_capital=100000
        )
        
        # 启动策略
        await strategy.start()
        
        # 模拟市场数据
        from decimal import Decimal
        import random
        
        base_price = 50000
        for i in range(100):
            # 生成模拟价格数据
            price_change = random.uniform(-0.02, 0.02)  # ±2%的随机变动
            base_price *= (1 + price_change)
            
            market_data = MarketData(
                symbol="BTCUSDT",
                timestamp=datetime.now(),
                open=base_price * 0.999,
                high=base_price * 1.001,
                low=base_price * 0.998,
                close=base_price,
                volume=1000
            )
            
            # 推送数据到策略
            await strategy.on_tick(market_data)
            
            # 每10个数据点输出一次状态
            if i % 10 == 0:
                info = strategy.get_strategy_info()
                print(f"步骤 {i}: 价格 {base_price:.2f}, 信号: {info['last_signals']}")
        
        # 停止策略
        await strategy.stop()
    
    # 运行示例
    asyncio.run(example_usage())
