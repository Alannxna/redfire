"""
Trading Domain Service
======================

交易领域服务，负责协调订单管理、持仓管理和风险管理等核心业务逻辑。
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from decimal import Decimal

from ..entities.order_entity import Order
from ..entities.trade_entity import Trade
from ..entities.position_entity import Position
from ..enums import Direction, Offset, OrderStatus, OrderType
from ..constants import (
    DEFAULT_COMMISSION_RATE, DEFAULT_SLIPPAGE,
    DEFAULT_MAX_POSITION_RATIO, DEFAULT_STOP_LOSS_RATIO
)

logger = logging.getLogger(__name__)


class TradingDomainService:
    """交易领域服务"""
    
    def __init__(self):
        self._orders: Dict[str, Order] = {}
        self._trades: Dict[str, Trade] = {}
        self._positions: Dict[str, Position] = {}
        
        # 统计信息
        self._statistics = {
            "total_orders": 0,
            "total_trades": 0,
            "total_positions": 0,
            "daily_pnl": Decimal("0"),
            "total_commission": Decimal("0"),
            "total_slippage": Decimal("0")
        }
    
    # ==================== 订单管理 ====================
    
    async def create_order(
        self,
        symbol: str,
        exchange: str,
        direction: Direction,
        offset: Offset,
        volume: int,
        order_type: OrderType = OrderType.LIMIT,
        price: Optional[Decimal] = None,
        stop_price: Optional[Decimal] = None,
        strategy_name: str = "",
        user_id: str = ""
    ) -> Order:
        """创建订单"""
        try:
            # 创建订单实体
            order = Order(
                symbol=symbol,
                exchange=exchange,
                direction=direction,
                offset=offset,
                volume=volume,
                order_type=order_type,
                price=price,
                stop_price=stop_price,
                strategy_name=strategy_name,
                user_id=user_id
            )
            
            # 验证订单
            if not order.is_valid():
                errors = order.get_validation_errors()
                raise ValueError(f"订单验证失败: {', '.join(errors)}")
            
            # 风险检查
            if not await self._check_order_risk(order):
                raise ValueError("订单风险检查未通过")
            
            # 保存订单
            self._orders[order.order_id] = order
            self._statistics["total_orders"] += 1
            
            logger.info(f"创建订单成功: {order.order_id}, {symbol}, {direction.value}, {volume}")
            return order
            
        except Exception as e:
            logger.error(f"创建订单失败: {e}")
            raise
    
    async def submit_order(self, order_id: str) -> bool:
        """提交订单"""
        if order_id not in self._orders:
            raise ValueError(f"订单不存在: {order_id}")
        
        order = self._orders[order_id]
        if order.submit():
            logger.info(f"订单提交成功: {order_id}")
            return True
        else:
            logger.warning(f"订单提交失败: {order_id}")
            return False
    
    async def cancel_order(self, order_id: str) -> bool:
        """撤销订单"""
        if order_id not in self._orders:
            raise ValueError(f"订单不存在: {order_id}")
        
        order = self._orders[order_id]
        if order.cancel():
            logger.info(f"订单撤销成功: {order_id}")
            return True
        else:
            logger.warning(f"订单撤销失败: {order_id}")
            return False
    
    async def get_order(self, order_id: str) -> Optional[Order]:
        """获取订单"""
        return self._orders.get(order_id)
    
    async def get_active_orders(self, symbol: str = "") -> List[Order]:
        """获取活跃订单"""
        if symbol:
            return [order for order in self._orders.values() 
                   if order.symbol == symbol and order.is_active()]
        else:
            return [order for order in self._orders.values() if order.is_active()]
    
    # ==================== 成交管理 ====================
    
    async def process_trade(
        self,
        order_id: str,
        volume: int,
        price: Decimal,
        trade_time: Optional[datetime] = None
    ) -> Trade:
        """处理成交"""
        if order_id not in self._orders:
            raise ValueError(f"订单不存在: {order_id}")
        
        order = self._orders[order_id]
        
        # 创建成交记录
        trade = Trade(
            order_id=order_id,
            symbol=order.symbol,
            exchange=order.exchange,
            product=order.product,
            direction=order.direction,
            offset=order.offset,
            volume=volume,
            price=price,
            trade_time=trade_time or datetime.now(),
            gateway_name=order.gateway_name,
            strategy_name=order.strategy_name,
            user_id=order.user_id
        )
        
        # 计算费用
        trade.commission = self._calculate_commission(volume, price)
        trade.slippage = self._calculate_slippage(volume, price)
        
        # 更新订单状态
        if order.update_trade(volume, price):
            # 保存成交记录
            self._trades[trade.trade_id] = trade
            self._statistics["total_trades"] += 1
            
            # 更新统计信息
            self._statistics["total_commission"] += trade.commission
            self._statistics["total_slippage"] += trade.slippage
            
            # 更新持仓
            await self._update_position(trade)
            
            logger.info(f"成交处理成功: {trade.trade_id}, 数量: {volume}, 价格: {price}")
            return trade
        else:
            raise ValueError("订单成交更新失败")
    
    def _calculate_commission(self, volume: int, price: Decimal) -> Decimal:
        """计算手续费"""
        amount = volume * price
        return amount * DEFAULT_COMMISSION_RATE
    
    def _calculate_slippage(self, volume: int, price: Decimal) -> Decimal:
        """计算滑点"""
        amount = volume * price
        return amount * DEFAULT_SLIPPAGE
    
    # ==================== 持仓管理 ====================
    
    async def _update_position(self, trade: Trade) -> None:
        """更新持仓"""
        position_key = f"{trade.symbol}_{trade.exchange}_{trade.user_id}"
        
        if position_key not in self._positions:
            # 创建新持仓
            position = Position(
                symbol=trade.symbol,
                exchange=trade.exchange,
                user_id=trade.user_id
            )
            self._positions[position_key] = position
            self._statistics["total_positions"] += 1
        
        position = self._positions[position_key]
        
        # 更新持仓数量
        if trade.offset == Offset.OPEN:
            if trade.direction == Direction.LONG:
                position.long_volume += trade.volume
                position.long_avg_price = self._calculate_avg_price(
                    position.long_volume, position.long_avg_price, trade.volume, trade.price
                )
            else:  # SHORT
                position.short_volume += trade.volume
                position.short_avg_price = self._calculate_avg_price(
                    position.short_volume, position.short_avg_price, trade.volume, trade.price
                )
        else:  # CLOSE
            if trade.direction == Direction.LONG:
                position.short_volume = max(0, position.short_volume - trade.volume)
            else:  # SHORT
                position.long_volume = max(0, position.long_volume - trade.volume)
        
        # 更新持仓状态
        position.update_time = datetime.now()
        position.calculate_pnl()
    
    def _calculate_avg_price(
        self, 
        current_volume: int, 
        current_price: Decimal, 
        new_volume: int, 
        new_price: Decimal
    ) -> Decimal:
        """计算平均价格"""
        if current_volume == 0:
            return new_price
        
        total_amount = current_volume * current_price + new_volume * new_price
        total_volume = current_volume + new_volume
        
        return total_amount / total_volume
    
    async def get_position(self, symbol: str, exchange: str, user_id: str) -> Optional[Position]:
        """获取持仓"""
        position_key = f"{symbol}_{exchange}_{user_id}"
        return self._positions.get(position_key)
    
    async def get_all_positions(self, user_id: str = "") -> List[Position]:
        """获取所有持仓"""
        if user_id:
            return [pos for pos in self._positions.values() if pos.user_id == user_id]
        else:
            return list(self._positions.values())
    
    # ==================== 风险管理 ====================
    
    async def _check_order_risk(self, order: Order) -> bool:
        """检查订单风险"""
        try:
            # 检查持仓限额
            if not await self._check_position_limit(order):
                return False
            
            # 检查资金限额
            if not await self._check_balance_limit(order):
                return False
            
            # 检查风险限额
            if not await self._check_risk_limit(order):
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"风险检查失败: {e}")
            return False
    
    async def _check_position_limit(self, order: Order) -> bool:
        """检查持仓限额"""
        # 获取当前持仓
        position = await self.get_position(order.symbol, order.exchange, order.user_id)
        
        if position is None:
            return True
        
        # 计算新持仓数量
        if order.offset == Offset.OPEN:
            if order.direction == Direction.LONG:
                new_volume = position.long_volume + order.volume
            else:
                new_volume = position.short_volume + order.volume
        else:
            # 平仓不需要检查持仓限额
            return True
        
        # 检查是否超过最大持仓比例
        # 这里需要获取账户总资产来计算比例
        # 暂时使用固定限额
        max_volume = 1000000  # 假设最大持仓100万
        
        if new_volume > max_volume:
            logger.warning(f"持仓超过限额: {order.symbol}, 新持仓: {new_volume}, 限额: {max_volume}")
            return False
        
        return True
    
    async def _check_balance_limit(self, order: Order) -> bool:
        """检查资金限额"""
        # 这里需要检查账户余额
        # 暂时返回True
        return True
    
    async def _check_risk_limit(self, order: Order) -> bool:
        """检查风险限额"""
        # 这里需要检查各种风险限额
        # 暂时返回True
        return True
    
    # ==================== 统计信息 ====================
    
    async def get_trading_statistics(self) -> Dict[str, Any]:
        """获取交易统计信息"""
        # 计算当日盈亏
        daily_pnl = sum(pos.daily_pnl for pos in self._positions.values())
        self._statistics["daily_pnl"] = daily_pnl
        
        return {
            **self._statistics,
            "active_orders": len([o for o in self._orders.values() if o.is_active()]),
            "total_positions": len(self._positions),
            "daily_pnl": float(daily_pnl),
            "total_commission": float(self._statistics["total_commission"]),
            "total_slippage": float(self._statistics["total_slippage"])
        }
    
    async def reset_daily_statistics(self) -> None:
        """重置每日统计信息"""
        self._statistics["daily_pnl"] = Decimal("0")
        
        # 重置持仓的每日盈亏
        for position in self._positions.values():
            position.reset_daily_pnl()
        
        logger.info("每日统计信息已重置")
