"""
Order Management Service
========================

订单管理服务，负责订单的创建、验证、提交、撤销等核心业务逻辑。
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from decimal import Decimal

from ..entities.order_entity import Order
from ..entities.contract_entity import Contract
from ..entities.account_entity import Account
from ..enums import Direction, Offset, OrderType, OrderStatus, PriceType
from ..constants import (
    MIN_VOLUME, MAX_VOLUME, MIN_PRICE, MAX_PRICE,
    DEFAULT_COMMISSION_RATE, DEFAULT_SLIPPAGE
)

logger = logging.getLogger(__name__)


class OrderManagementService:
    """订单管理服务"""
    
    def __init__(self):
        self._orders: Dict[str, Order] = {}
        self._contracts: Dict[str, Contract] = {}
        self._accounts: Dict[str, Account] = {}
        
        # 统计信息
        self._statistics = {
            "total_orders": 0,
            "active_orders": 0,
            "cancelled_orders": 0,
            "rejected_orders": 0,
            "total_volume": 0,
            "total_amount": Decimal("0")
        }
    
    # ==================== 订单创建 ====================
    
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
        user_id: str = "",
        account_id: str = ""
    ) -> Order:
        """创建订单"""
        try:
            # 验证合约
            contract = await self._get_contract(symbol, exchange)
            if not contract:
                raise ValueError(f"合约不存在: {symbol}.{exchange}")
            
            # 验证账户
            if account_id:
                account = await self._get_account(account_id)
                if not account:
                    raise ValueError(f"账户不存在: {account_id}")
                
                if not account.is_active or not account.is_trading:
                    raise ValueError(f"账户不可交易: {account_id}")
            
            # 创建订单
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
            
            # 合约特定验证
            if not await self._validate_order_with_contract(order, contract):
                raise ValueError("订单合约验证失败")
            
            # 账户资金验证
            if account_id and not await self._validate_order_funds(order, account):
                raise ValueError("订单资金验证失败")
            
            # 保存订单
            self._orders[order.order_id] = order
            self._update_statistics(order, "create")
            
            logger.info(f"创建订单成功: {order.order_id}, {symbol}, {direction.value}, {volume}")
            return order
            
        except Exception as e:
            logger.error(f"创建订单失败: {e}")
            raise
    
    async def _validate_order_with_contract(self, order: Order, contract: Contract) -> bool:
        """验证订单与合约的兼容性"""
        try:
            # 验证价格
            if order.price and not contract.validate_price(order.price):
                logger.warning(f"价格验证失败: {order.price}, tick: {contract.price_tick}")
                return False
            
            # 验证数量
            if not contract.validate_volume(order.volume):
                logger.warning(f"数量验证失败: {order.volume}, size: {contract.size}")
                return False
            
            # 验证订单类型与合约的兼容性
            if not self._validate_order_type_compatibility(order, contract):
                logger.warning(f"订单类型不兼容: {order.order_type.value}")
                return False
            
            # 验证交易时间
            if not contract.is_trading_time():
                logger.warning(f"非交易时间: {contract.symbol}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"合约验证失败: {e}")
            return False
    
    def _validate_order_type_compatibility(self, order: Order, contract: Contract) -> bool:
        """验证订单类型与合约的兼容性"""
        # 期货合约支持更多订单类型
        if contract.is_futures:
            return order.order_type in [
                OrderType.LIMIT, OrderType.MARKET, OrderType.STOP,
                OrderType.STOP_LIMIT, OrderType.FAK, OrderType.FOK
            ]
        
        # 股票合约只支持基本订单类型
        if contract.is_equity:
            return order.order_type in [OrderType.LIMIT, OrderType.MARKET]
        
        # 期权合约支持限价和市价
        if contract.is_option:
            return order.order_type in [OrderType.LIMIT, OrderType.MARKET]
        
        return False
    
    async def _validate_order_funds(self, order: Order, account: Account) -> bool:
        """验证订单资金"""
        try:
            # 计算所需资金
            required_amount = self._calculate_required_amount(order)
            
            # 检查可用资金
            if not account.can_trade(required_amount):
                logger.warning(f"资金不足: 需要{required_amount}, 可用{account.available}")
                return False
            
            # 检查持仓限额（如果是开仓）
            if order.offset == Offset.OPEN:
                if not await self._check_position_limit(order, account):
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"资金验证失败: {e}")
            return False
    
    def _calculate_required_amount(self, order: Order) -> Decimal:
        """计算订单所需资金"""
        if order.price is None:
            # 市价单使用预估价格
            estimated_price = Decimal("100")  # 这里应该从市场数据获取
            amount = order.volume * estimated_price
        else:
            amount = order.volume * order.price
        
        # 添加手续费和滑点
        commission = amount * DEFAULT_COMMISSION_RATE
        slippage = amount * DEFAULT_SLIPPAGE
        
        return amount + commission + slippage
    
    async def _check_position_limit(self, order: Order, account: Account) -> bool:
        """检查持仓限额"""
        # 这里应该实现具体的持仓限额检查逻辑
        # 暂时返回True
        return True
    
    # ==================== 订单操作 ====================
    
    async def submit_order(self, order_id: str) -> bool:
        """提交订单"""
        if order_id not in self._orders:
            raise ValueError(f"订单不存在: {order_id}")
        
        order = self._orders[order_id]
        
        # 检查订单状态
        if order.status != OrderStatus.SUBMITTING:
            logger.warning(f"订单状态不正确: {order_id}, {order.status.value}")
            return False
        
        # 提交订单
        if order.submit():
            self._update_statistics(order, "submit")
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
        
        # 检查订单状态
        if order.status not in [OrderStatus.SUBMITTED, OrderStatus.PARTTRADED]:
            logger.warning(f"订单状态不允许撤销: {order_id}, {order.status.value}")
            return False
        
        # 撤销订单
        if order.cancel():
            self._update_statistics(order, "cancel")
            logger.info(f"订单撤销成功: {order_id}")
            return True
        else:
            logger.warning(f"订单撤销失败: {order_id}")
            return False
    
    async def reject_order(self, order_id: str, reason: str = "") -> bool:
        """拒绝订单"""
        if order_id not in self._orders:
            raise ValueError(f"订单不存在: {order_id}")
        
        order = self._orders[order_id]
        
        # 拒绝订单
        if order.reject(reason):
            self._update_statistics(order, "reject")
            logger.info(f"订单拒绝成功: {order_id}, 原因: {reason}")
            return True
        else:
            logger.warning(f"订单拒绝失败: {order_id}")
            return False
    
    # ==================== 订单查询 ====================
    
    async def get_order(self, order_id: str) -> Optional[Order]:
        """获取订单"""
        return self._orders.get(order_id)
    
    async def get_orders_by_user(self, user_id: str) -> List[Order]:
        """获取用户的订单"""
        return [order for order in self._orders.values() if order.user_id == user_id]
    
    async def get_orders_by_symbol(self, symbol: str) -> List[Order]:
        """获取指定品种的订单"""
        return [order for order in self._orders.values() if order.symbol == symbol]
    
    async def get_active_orders(self, user_id: str = "") -> List[Order]:
        """获取活跃订单"""
        if user_id:
            return [order for order in self._orders.values() 
                   if order.user_id == user_id and order.is_active()]
        else:
            return [order for order in self._orders.values() if order.is_active()]
    
    async def get_orders_by_status(self, status: OrderStatus) -> List[Order]:
        """根据状态获取订单"""
        return [order for order in self._orders.values() if order.status == status]
    
    # ==================== 订单更新 ====================
    
    async def update_order_status(self, order_id: str, status: OrderStatus, remark: str = "") -> bool:
        """更新订单状态"""
        if order_id not in self._orders:
            return False
        
        order = self._orders[order_id]
        old_status = order.status
        
        # 更新状态
        if status == OrderStatus.REJECTED:
            order.reject(remark)
        elif status == OrderStatus.CANCELLED:
            order.cancel()
        elif status == OrderStatus.EXPIRED:
            order.status = status
            order.remark = remark
            order.update_time = datetime.now()
        
        # 更新统计
        if old_status != order.status:
            self._update_statistics(order, "status_change")
        
        return True
    
    async def update_order_trade(self, order_id: str, trade_volume: int, trade_price: Decimal) -> bool:
        """更新订单成交"""
        if order_id not in self._orders:
            return False
        
        order = self._orders[order_id]
        
        # 更新成交信息
        if order.update_trade(trade_volume, trade_price):
            self._update_statistics(order, "trade")
            logger.info(f"订单成交更新: {order_id}, 数量: {trade_volume}, 价格: {trade_price}")
            return True
        
        return False
    
    # ==================== 合约和账户管理 ====================
    
    async def add_contract(self, contract: Contract) -> None:
        """添加合约"""
        contract_key = f"{contract.symbol}.{contract.exchange.value}"
        self._contracts[contract_key] = contract
        logger.info(f"添加合约: {contract_key}")
    
    async def add_account(self, account: Account) -> None:
        """添加账户"""
        self._accounts[account.account_id] = account
        logger.info(f"添加账户: {account.account_id}")
    
    async def _get_contract(self, symbol: str, exchange: str) -> Optional[Contract]:
        """获取合约"""
        contract_key = f"{symbol}.{exchange}"
        return self._contracts.get(contract_key)
    
    async def _get_account(self, account_id: str) -> Optional[Account]:
        """获取账户"""
        return self._accounts.get(account_id)
    
    # ==================== 统计信息 ====================
    
    def _update_statistics(self, order: Order, action: str) -> None:
        """更新统计信息"""
        if action == "create":
            self._statistics["total_orders"] += 1
            self._statistics["total_volume"] += order.volume
            if order.price:
                self._statistics["total_amount"] += order.get_total_amount()
        
        elif action == "submit":
            self._statistics["active_orders"] += 1
        
        elif action == "cancel":
            self._statistics["cancelled_orders"] += 1
            self._statistics["active_orders"] -= 1
        
        elif action == "reject":
            self._statistics["rejected_orders"] += 1
        
        elif action == "trade":
            # 成交后更新统计
            pass
        
        elif action == "status_change":
            # 状态变更后更新统计
            if order.status == OrderStatus.ALLTRADED:
                self._statistics["active_orders"] -= 1
    
    async def get_order_statistics(self) -> Dict[str, Any]:
        """获取订单统计信息"""
        return {
            **self._statistics,
            "total_amount": float(self._statistics["total_amount"]),
            "average_order_size": (
                self._statistics["total_volume"] / self._statistics["total_orders"]
                if self._statistics["total_orders"] > 0 else 0
            ),
            "order_success_rate": (
                (self._statistics["total_orders"] - self._statistics["rejected_orders"]) / self._statistics["total_orders"]
                if self._statistics["total_orders"] > 0 else 0
            )
        }
    
    async def reset_daily_statistics(self) -> None:
        """重置每日统计信息"""
        self._statistics["active_orders"] = 0
        logger.info("每日订单统计已重置")
