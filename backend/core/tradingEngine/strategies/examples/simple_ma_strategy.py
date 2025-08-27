"""
简单移动平均策略示例

演示如何使用独立策略引擎创建交易策略。
"""

import asyncio
from typing import Any, Dict, List
from collections import deque
from ..strategyEngine import BaseStrategy, StrategyConfig


class SimpleMAStrategy(BaseStrategy):
    """
    简单移动平均策略
    
    基于短期和长期移动平均线的交叉信号进行交易。
    """
    
    def __init__(self, strategy_id: str, config: StrategyConfig):
        super().__init__(strategy_id, config)
        
        # 策略参数
        self.short_window = self.config.config_data.get('short_window', 5)
        self.long_window = self.config.config_data.get('long_window', 20)
        self.symbol = self.config.config_data.get('symbol', 'BTCUSDT')
        
        # 数据存储
        self.price_data: deque = deque(maxlen=self.long_window)
        self.short_ma_data: deque = deque(maxlen=100)
        self.long_ma_data: deque = deque(maxlen=100)
        
        # 交易状态
        self.position = 0  # 0: 空仓, 1: 多仓, -1: 空仓
        self.last_price = 0.0
        self.entry_price = 0.0
        self.total_trades = 0
        self.winning_trades = 0
        
        # 信号状态
        self.last_signal = None
        
        self.log_info(f"策略初始化完成 - 短期窗口: {self.short_window}, 长期窗口: {self.long_window}")
    
    async def on_start(self):
        """策略启动"""
        self.log_info(f"移动平均策略启动 - 交易品种: {self.symbol}")
        
        # 重置统计数据
        self.performance_stats = {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'win_rate': 0.0,
            'total_pnl': 0.0,
            'max_drawdown': 0.0,
            'sharpe_ratio': 0.0
        }
    
    async def on_stop(self):
        """策略停止"""
        self.log_info("移动平均策略停止")
        
        # 平仓所有持仓
        if self.position != 0:
            await self._close_position("策略停止")
        
        # 输出最终统计
        self._log_performance_summary()
    
    async def on_tick(self, tick_data: Any):
        """处理tick数据"""
        try:
            # 提取价格数据
            if isinstance(tick_data, dict):
                price = float(tick_data.get('price', 0))
                symbol = tick_data.get('symbol', '')
            else:
                # 假设tick_data有price和symbol属性
                price = float(getattr(tick_data, 'price', 0))
                symbol = getattr(tick_data, 'symbol', '')
            
            # 只处理指定品种
            if symbol != self.symbol:
                return
            
            if price <= 0:
                return
            
            self.last_price = price
            
            # 添加价格数据
            self.price_data.append(price)
            
            # 计算移动平均线
            if len(self.price_data) >= self.long_window:
                await self._calculate_indicators()
                await self._check_signals()
        
        except Exception as e:
            self.log_error(f"处理tick数据异常: {e}")
    
    async def on_bar(self, bar_data: Any):
        """处理K线数据"""
        try:
            # 提取K线数据
            if isinstance(bar_data, dict):
                close_price = float(bar_data.get('close', 0))
                symbol = bar_data.get('symbol', '')
            else:
                close_price = float(getattr(bar_data, 'close', 0))
                symbol = getattr(bar_data, 'symbol', '')
            
            # 只处理指定品种
            if symbol != self.symbol:
                return
            
            if close_price <= 0:
                return
            
            # 使用收盘价更新指标
            self.last_price = close_price
            self.price_data.append(close_price)
            
            if len(self.price_data) >= self.long_window:
                await self._calculate_indicators()
                await self._check_signals()
        
        except Exception as e:
            self.log_error(f"处理K线数据异常: {e}")
    
    async def on_order(self, order_data: Any):
        """处理订单状态更新"""
        try:
            if isinstance(order_data, dict):
                order_id = order_data.get('order_id', '')
                status = order_data.get('status', '')
                self.log_info(f"订单状态更新: {order_id} - {status}")
            
        except Exception as e:
            self.log_error(f"处理订单状态异常: {e}")
    
    async def on_trade(self, trade_data: Any):
        """处理成交数据"""
        try:
            if isinstance(trade_data, dict):
                trade_id = trade_data.get('trade_id', '')
                price = float(trade_data.get('price', 0))
                quantity = float(trade_data.get('quantity', 0))
                side = trade_data.get('side', '')
                
                self.log_info(f"成交确认: {trade_id} - {side} {quantity}@{price}")
                
                # 更新持仓和统计
                await self._update_position_stats(price, quantity, side)
        
        except Exception as e:
            self.log_error(f"处理成交数据异常: {e}")
    
    async def _calculate_indicators(self):
        """计算技术指标"""
        try:
            price_list = list(self.price_data)
            
            # 计算短期移动平均
            if len(price_list) >= self.short_window:
                short_ma = sum(price_list[-self.short_window:]) / self.short_window
                self.short_ma_data.append(short_ma)
            
            # 计算长期移动平均
            if len(price_list) >= self.long_window:
                long_ma = sum(price_list[-self.long_window:]) / self.long_window
                self.long_ma_data.append(long_ma)
        
        except Exception as e:
            self.log_error(f"计算指标异常: {e}")
    
    async def _check_signals(self):
        """检查交易信号"""
        try:
            if len(self.short_ma_data) < 2 or len(self.long_ma_data) < 2:
                return
            
            short_ma_current = self.short_ma_data[-1]
            short_ma_previous = self.short_ma_data[-2]
            long_ma_current = self.long_ma_data[-1]
            long_ma_previous = self.long_ma_data[-2]
            
            # 金叉信号 - 短期均线上穿长期均线
            if (short_ma_previous <= long_ma_previous and 
                short_ma_current > long_ma_current and 
                self.last_signal != 'buy'):
                
                await self._generate_buy_signal()
                self.last_signal = 'buy'
            
            # 死叉信号 - 短期均线下穿长期均线
            elif (short_ma_previous >= long_ma_previous and 
                  short_ma_current < long_ma_current and 
                  self.last_signal != 'sell'):
                
                await self._generate_sell_signal()
                self.last_signal = 'sell'
        
        except Exception as e:
            self.log_error(f"检查信号异常: {e}")
    
    async def _generate_buy_signal(self):
        """生成买入信号"""
        try:
            if self.position <= 0:  # 空仓或空头
                await self._open_long_position()
        except Exception as e:
            self.log_error(f"生成买入信号异常: {e}")
    
    async def _generate_sell_signal(self):
        """生成卖出信号"""
        try:
            if self.position >= 0:  # 多仓或空仓
                await self._open_short_position()
        except Exception as e:
            self.log_error(f"生成卖出信号异常: {e}")
    
    async def _open_long_position(self):
        """开多仓"""
        try:
            # 如果有空头持仓，先平仓
            if self.position < 0:
                await self._close_position("平空开多")
            
            # 开多仓
            self.position = 1
            self.entry_price = self.last_price
            self.total_trades += 1
            
            self.log_info(f"开多仓 - 价格: {self.last_price:.4f}")
            
            # 这里应该发送实际的交易指令
            # await self._send_order('buy', quantity)
        
        except Exception as e:
            self.log_error(f"开多仓异常: {e}")
    
    async def _open_short_position(self):
        """开空仓"""
        try:
            # 如果有多头持仓，先平仓
            if self.position > 0:
                await self._close_position("平多开空")
            
            # 开空仓
            self.position = -1
            self.entry_price = self.last_price
            self.total_trades += 1
            
            self.log_info(f"开空仓 - 价格: {self.last_price:.4f}")
            
            # 这里应该发送实际的交易指令
            # await self._send_order('sell', quantity)
        
        except Exception as e:
            self.log_error(f"开空仓异常: {e}")
    
    async def _close_position(self, reason: str):
        """平仓"""
        try:
            if self.position == 0:
                return
            
            # 计算盈亏
            if self.position > 0:  # 多仓
                pnl = self.last_price - self.entry_price
            else:  # 空仓
                pnl = self.entry_price - self.last_price
            
            # 更新统计
            if pnl > 0:
                self.winning_trades += 1
            
            self.log_info(f"平仓 - 原因: {reason}, 盈亏: {pnl:.4f}")
            
            # 重置持仓
            self.position = 0
            self.entry_price = 0.0
            
            # 更新性能统计
            self.performance_stats['total_pnl'] += pnl
            self._update_performance_stats()
        
        except Exception as e:
            self.log_error(f"平仓异常: {e}")
    
    async def _update_position_stats(self, price: float, quantity: float, side: str):
        """更新持仓统计"""
        # 这里可以根据实际成交更新持仓信息
        pass
    
    def _update_performance_stats(self):
        """更新性能统计"""
        try:
            total_trades = self.total_trades
            if total_trades > 0:
                self.performance_stats.update({
                    'total_trades': total_trades,
                    'winning_trades': self.winning_trades,
                    'losing_trades': total_trades - self.winning_trades,
                    'win_rate': (self.winning_trades / total_trades) * 100
                })
        
        except Exception as e:
            self.log_error(f"更新性能统计异常: {e}")
    
    def _log_performance_summary(self):
        """输出性能总结"""
        try:
            stats = self.performance_stats
            self.log_info("=== 策略性能总结 ===")
            self.log_info(f"总交易次数: {stats.get('total_trades', 0)}")
            self.log_info(f"盈利交易: {stats.get('winning_trades', 0)}")
            self.log_info(f"亏损交易: {stats.get('losing_trades', 0)}")
            self.log_info(f"胜率: {stats.get('win_rate', 0):.2f}%")
            self.log_info(f"总盈亏: {stats.get('total_pnl', 0):.4f}")
            self.log_info("==================")
        
        except Exception as e:
            self.log_error(f"输出性能总结异常: {e}")
