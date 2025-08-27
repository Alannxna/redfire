"""
交易应用服务
============

负责协调交易领域服务和基础设施，处理交易相关的应用层业务逻辑
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from ...core.base import BaseApplicationService
from ...domain.trading.services.trading_domain_service import get_trading_domain_service, TradingDomainService


class TradingApplicationService(BaseApplicationService):
    """
    交易应用服务
    
    协调交易相关的业务流程：
    - 订单生命周期管理
    - 持仓计算和查询
    - 账户信息管理
    - 风险控制集成
    """
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.trading_domain_service: TradingDomainService = get_trading_domain_service()
        
        # 模拟数据存储（生产环境应该使用真实的仓储）
        self._orders_storage: Dict[str, Dict[str, Any]] = {}
        self._positions_storage: Dict[str, Dict[str, Any]] = {}
        self._accounts_storage: Dict[str, Dict[str, Any]] = {}
        
        # 初始化默认数据
        self._initialize_default_data()
    
    def _initialize_default_data(self):
        """初始化默认数据"""
        # 创建默认账户
        default_account = {
            "account_id": "default",
            "account_type": "cash",
            "balance": Decimal("100000.00"),
            "available_balance": Decimal("100000.00"),
            "frozen_balance": Decimal("0.00"),
            "margin_used": Decimal("0.00"),
            "margin_available": Decimal("100000.00"),
            "total_pnl": Decimal("0.00"),
            "daily_pnl": Decimal("0.00"),
            "total_commission": Decimal("0.00"),
            "currency": "CNY",
            "risk_level": "low",
            "trading_status": "active",
            "created_at": datetime.now(timezone.utc)
        }
        
        self._accounts_storage["default"] = default_account
        self.logger.info("默认账户数据初始化完成")
    
    async def submit_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        提交订单
        
        Args:
            order_data: 订单数据
            
        Returns:
            订单提交结果
        """
        try:
            # 生成订单ID
            order_id = str(uuid4())
            now = datetime.now(timezone.utc)
            
            # 执行预交易风险检查
            await self._pre_trade_risk_check(order_data)
            
            # 构建完整订单对象
            order = {
                "order_id": order_id,
                "user_id": order_data["user_id"],
                "account_id": order_data["account_id"],
                "symbol": order_data["symbol"],
                "exchange": order_data["exchange"],
                "direction": order_data["direction"],
                "order_type": order_data["order_type"],
                "quantity": order_data["quantity"],
                "price": order_data["price"],
                "time_in_force": order_data.get("time_in_force", "GTC"),
                "strategy_id": order_data.get("strategy_id"),
                "stop_price": order_data.get("stop_price"),
                "take_profit_price": order_data.get("take_profit_price"),
                "notes": order_data.get("notes"),
                
                # 状态信息
                "status": "submitted",
                "filled_quantity": Decimal("0"),
                "remaining_quantity": order_data["quantity"],
                "average_price": None,
                
                # 时间戳
                "created_at": now,
                "submitted_at": now,
                "filled_at": None,
                "cancelled_at": None,
                
                # 费用信息
                "commission": Decimal("0"),
                "fee": Decimal("0"),
                "tax": Decimal("0"),
                
                # 错误信息
                "error_code": None,
                "error_message": None,
                
                # 元数据
                "metadata": order_data.get("metadata", {})
            }
            
            # 保存订单
            self._orders_storage[order_id] = order
            
            # 冻结资金（如果是买单）
            if order["direction"] == "buy" and order["price"]:
                freeze_amount = order["quantity"] * order["price"]
                await self._freeze_balance(order["account_id"], freeze_amount)
            
            # 记录到领域服务统计
            self.trading_domain_service._trade_statistics["total_orders"] += 1
            
            self.logger.info(f"订单提交成功: {order_id}, 标的: {order['symbol']}, 数量: {order['quantity']}")
            
            return order
            
        except Exception as e:
            self.logger.error(f"订单提交失败: {e}", exc_info=True)
            raise
    
    async def get_orders(self, query_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        获取订单列表
        
        Args:
            query_params: 查询参数
            
        Returns:
            订单列表和总数
        """
        try:
            user_id = query_params["user_id"]
            status_filter = query_params.get("status")
            symbol_filter = query_params.get("symbol")
            exchange_filter = query_params.get("exchange")
            limit = query_params.get("limit", 50)
            offset = query_params.get("offset", 0)
            
            # 过滤订单
            filtered_orders = []
            for order in self._orders_storage.values():
                # 用户过滤
                if order["user_id"] != user_id:
                    continue
                
                # 状态过滤
                if status_filter and order["status"] != status_filter:
                    continue
                
                # 标的过滤
                if symbol_filter and order["symbol"] != symbol_filter:
                    continue
                
                # 交易所过滤
                if exchange_filter and order["exchange"] != exchange_filter:
                    continue
                
                filtered_orders.append(order)
            
            # 排序（按创建时间倒序）
            filtered_orders.sort(key=lambda x: x["created_at"], reverse=True)
            
            # 分页
            total_count = len(filtered_orders)
            paginated_orders = filtered_orders[offset:offset + limit]
            
            self.logger.info(f"查询到 {total_count} 条订单，返回 {len(paginated_orders)} 条")
            
            return {
                "orders": paginated_orders,
                "total_count": total_count,
                "limit": limit,
                "offset": offset
            }
            
        except Exception as e:
            self.logger.error(f"获取订单列表失败: {e}", exc_info=True)
            raise
    
    async def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """
        取消订单
        
        Args:
            order_id: 订单ID
            
        Returns:
            取消结果
        """
        try:
            # 检查订单是否存在
            if order_id not in self._orders_storage:
                raise ValueError(f"订单不存在: {order_id}")
            
            order = self._orders_storage[order_id]
            
            # 检查订单状态
            if order["status"] not in ["pending", "submitted", "partial_filled"]:
                raise ValueError(f"订单状态为 {order['status']}，无法取消")
            
            # 更新订单状态
            cancelled_at = datetime.now(timezone.utc)
            order["status"] = "cancelled"
            order["cancelled_at"] = cancelled_at
            
            # 释放冻结资金
            if order["direction"] == "buy" and order["remaining_quantity"] > 0 and order["price"]:
                unfreeze_amount = order["remaining_quantity"] * order["price"]
                await self._unfreeze_balance(order["account_id"], unfreeze_amount)
            
            # 更新统计
            self.trading_domain_service._trade_statistics["cancelled_orders"] += 1
            
            self.logger.info(f"订单取消成功: {order_id}")
            
            return {
                "order_id": order_id,
                "cancelled_at": cancelled_at,
                "remaining_quantity": order["remaining_quantity"]
            }
            
        except Exception as e:
            self.logger.error(f"订单取消失败: {e}", exc_info=True)
            raise
    
    async def get_order_by_id(self, order_id: str) -> Optional[Dict[str, Any]]:
        """根据ID获取订单"""
        return self._orders_storage.get(order_id)
    
    async def get_positions(self, query_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        获取持仓信息
        
        Args:
            query_params: 查询参数
            
        Returns:
            持仓列表
        """
        try:
            user_id = query_params["user_id"]
            account_id = query_params["account_id"]
            symbol_filter = query_params.get("symbol")
            exchange_filter = query_params.get("exchange")
            
            # 构建持仓key
            position_key = f"{user_id}_{account_id}"
            
            # 过滤持仓
            filtered_positions = []
            for position_id, position in self._positions_storage.items():
                # 检查是否属于当前用户账户
                if not position_id.startswith(position_key):
                    continue
                
                # 标的过滤
                if symbol_filter and position["symbol"] != symbol_filter:
                    continue
                
                # 交易所过滤
                if exchange_filter and position["exchange"] != exchange_filter:
                    continue
                
                # 只返回有持仓的记录
                if position["long_quantity"] > 0 or position["short_quantity"] > 0:
                    filtered_positions.append(position)
            
            self.logger.info(f"查询到 {len(filtered_positions)} 个持仓")
            
            return {
                "positions": filtered_positions
            }
            
        except Exception as e:
            self.logger.error(f"获取持仓信息失败: {e}", exc_info=True)
            raise
    
    async def get_account_info(self, user_id: str, account_id: str) -> Dict[str, Any]:
        """
        获取账户信息
        
        Args:
            user_id: 用户ID
            account_id: 账户ID
            
        Returns:
            账户信息
        """
        try:
            # 获取账户基础信息
            if account_id not in self._accounts_storage:
                # 创建新账户
                await self._create_account(user_id, account_id)
            
            account = self._accounts_storage[account_id].copy()
            
            # 计算实时盈亏和统计
            await self._update_account_pnl(account_id)
            
            self.logger.info(f"获取账户信息成功: {account_id}")
            
            return account
            
        except Exception as e:
            self.logger.error(f"获取账户信息失败: {e}", exc_info=True)
            raise
    
    async def _pre_trade_risk_check(self, order_data: Dict[str, Any]):
        """预交易风险检查"""
        # 检查交易是否启用
        if not self.trading_domain_service.is_trading_enabled():
            raise ValueError("交易功能已关闭")
        
        # 检查账户状态
        account_id = order_data["account_id"]
        if account_id in self._accounts_storage:
            account = self._accounts_storage[account_id]
            if account["trading_status"] != "active":
                raise ValueError(f"账户交易状态异常: {account['trading_status']}")
        
        # 检查资金充足性（买单）
        if order_data["direction"] == "buy" and order_data["price"]:
            required_amount = order_data["quantity"] * order_data["price"]
            account = self._accounts_storage.get(account_id, {})
            available_balance = account.get("available_balance", Decimal("0"))
            
            if required_amount > available_balance:
                raise ValueError(f"资金不足，需要 {required_amount}，可用 {available_balance}")
        
        # 检查订单数量限制
        risk_limits = self.trading_domain_service.get_risk_limits()
        active_orders_count = self.trading_domain_service.get_active_orders_count()
        
        if active_orders_count >= risk_limits.get("max_open_orders", 500):
            raise ValueError("活跃订单数量已达上限")
    
    async def _freeze_balance(self, account_id: str, amount: Decimal):
        """冻结账户余额"""
        if account_id in self._accounts_storage:
            account = self._accounts_storage[account_id]
            if account["available_balance"] >= amount:
                account["available_balance"] -= amount
                account["frozen_balance"] += amount
                self.logger.debug(f"冻结余额: {amount}, 账户: {account_id}")
            else:
                raise ValueError("可用余额不足")
    
    async def _unfreeze_balance(self, account_id: str, amount: Decimal):
        """解冻账户余额"""
        if account_id in self._accounts_storage:
            account = self._accounts_storage[account_id]
            if account["frozen_balance"] >= amount:
                account["frozen_balance"] -= amount
                account["available_balance"] += amount
                self.logger.debug(f"解冻余额: {amount}, 账户: {account_id}")
    
    async def _create_account(self, user_id: str, account_id: str):
        """创建新账户"""
        account = {
            "account_id": account_id,
            "user_id": user_id,
            "account_type": "cash",
            "balance": Decimal("100000.00"),
            "available_balance": Decimal("100000.00"),
            "frozen_balance": Decimal("0.00"),
            "margin_used": Decimal("0.00"),
            "margin_available": Decimal("100000.00"),
            "total_pnl": Decimal("0.00"),
            "daily_pnl": Decimal("0.00"),
            "total_commission": Decimal("0.00"),
            "currency": "CNY",
            "risk_level": "low",
            "trading_status": "active",
            "created_at": datetime.now(timezone.utc)
        }
        
        self._accounts_storage[account_id] = account
        self.logger.info(f"创建新账户: {account_id}")
    
    async def _update_account_pnl(self, account_id: str):
        """更新账户盈亏"""
        # 这里应该根据持仓和当前价格计算实时盈亏
        # 暂时使用模拟数据
        pass
    
    def get_trading_statistics(self) -> Dict[str, Any]:
        """获取交易统计信息"""
        return self.trading_domain_service.get_trading_statistics()


# 全局服务实例
_trading_app_service: Optional[TradingApplicationService] = None


def get_trading_application_service() -> TradingApplicationService:
    """获取交易应用服务实例"""
    global _trading_app_service
    if _trading_app_service is None:
        _trading_app_service = TradingApplicationService()
    return _trading_app_service
