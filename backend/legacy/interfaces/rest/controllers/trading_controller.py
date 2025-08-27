"""
交易控制器
===========

负责处理交易相关的REST API请求
"""

import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from ..models.common import APIResponse
from ..dependencies import get_current_user
from ....core.common.enums.trading_enums import ExchangeType
from ....domain.trading.services.trading_domain_service import get_trading_domain_service
from ....application.services.trading_application_service import get_trading_application_service

logger = logging.getLogger(__name__)


# 请求模型
class SubmitOrderRequest(BaseModel):
    """提交订单请求"""
    symbol: str = Field(..., description="交易标的代码")
    exchange: str = Field(..., description="交易所代码")
    direction: str = Field(..., description="交易方向：buy/sell")
    order_type: str = Field(..., description="订单类型：limit/market/stop")
    quantity: float = Field(..., gt=0, description="交易数量")
    price: Optional[float] = Field(None, description="价格（限价单必填）")
    time_in_force: str = Field("GTC", description="有效期类型")
    strategy_id: Optional[str] = Field(None, description="策略ID")
    stop_price: Optional[float] = Field(None, description="止损价格")
    take_profit_price: Optional[float] = Field(None, description="止盈价格")
    notes: Optional[str] = Field(None, description="备注")


class OrderFilterParams(BaseModel):
    """订单过滤参数"""
    status: Optional[str] = Field(None, description="订单状态")
    symbol: Optional[str] = Field(None, description="交易标的")
    exchange: Optional[str] = Field(None, description="交易所")
    start_date: Optional[datetime] = Field(None, description="开始时间")
    end_date: Optional[datetime] = Field(None, description="结束时间")
    limit: int = Field(50, le=200, description="返回数量限制")
    offset: int = Field(0, ge=0, description="偏移量")


# 响应模型
class OrderResponse(BaseModel):
    """订单响应"""
    order_id: str
    user_id: str
    account_id: str
    symbol: str
    exchange: str
    direction: str
    order_type: str
    quantity: float
    price: Optional[float]
    status: str
    filled_quantity: float
    remaining_quantity: float
    average_price: Optional[float]
    created_at: datetime
    submitted_at: Optional[datetime]
    commission: float
    fee: float
    error_message: Optional[str] = None


class PositionResponse(BaseModel):
    """持仓响应"""
    user_id: str
    account_id: str
    symbol: str
    exchange: str
    long_quantity: float
    short_quantity: float
    net_quantity: float
    long_cost: float
    short_cost: float
    current_price: Optional[float]
    unrealized_pnl: float
    realized_pnl: float
    total_pnl: float
    market_value: float
    last_update_time: Optional[datetime]


class AccountInfoResponse(BaseModel):
    """账户信息响应"""
    account_id: str
    account_type: str
    balance: float
    available_balance: float
    frozen_balance: float
    margin_used: float
    margin_available: float
    total_pnl: float
    daily_pnl: float
    total_commission: float
    currency: str
    risk_level: str
    trading_status: str


class TradingController:
    """
    交易控制器
    
    提供交易相关的REST API接口：
    - 订单提交和管理
    - 持仓查询
    - 账户信息
    - 交易历史
    """
    
    def __init__(self):
        self.router = APIRouter(prefix="/api/v1/trading", tags=["交易管理"])
        self.trading_service = get_trading_domain_service()
        self.trading_app_service = get_trading_application_service()
        self._setup_routes()
    
    def _setup_routes(self):
        """设置路由"""
        
        @self.router.post("/orders", response_model=APIResponse[OrderResponse])
        async def submit_order(
            request: SubmitOrderRequest,
            current_user: Dict[str, Any] = Depends(get_current_user)
        ):
            """
            提交订单
            
            提交新的交易订单，支持限价单、市价单等多种类型
            """
            try:
                # 验证用户权限
                if not self._check_trading_permission(current_user):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="用户没有交易权限"
                    )
                
                # 验证交易所
                if not self._validate_exchange(request.exchange):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"不支持的交易所: {request.exchange}"
                    )
                
                # 验证订单参数
                self._validate_order_params(request)
                
                # 风险检查
                await self._perform_risk_check(current_user, request)
                
                # 创建订单数据
                order_data = {
                    "user_id": current_user["user_id"],
                    "account_id": current_user.get("account_id", "default"),
                    "symbol": request.symbol,
                    "exchange": request.exchange,
                    "direction": request.direction,
                    "order_type": request.order_type,
                    "quantity": Decimal(str(request.quantity)),
                    "price": Decimal(str(request.price)) if request.price else None,
                    "time_in_force": request.time_in_force,
                    "strategy_id": request.strategy_id,
                    "stop_price": Decimal(str(request.stop_price)) if request.stop_price else None,
                    "take_profit_price": Decimal(str(request.take_profit_price)) if request.take_profit_price else None,
                    "notes": request.notes
                }
                
                # 提交订单到交易服务
                order_result = await self.trading_app_service.submit_order(order_data)
                
                # 构造响应
                order_response = OrderResponse(
                    order_id=order_result["order_id"],
                    user_id=order_result["user_id"],
                    account_id=order_result["account_id"],
                    symbol=order_result["symbol"],
                    exchange=order_result["exchange"],
                    direction=order_result["direction"],
                    order_type=order_result["order_type"],
                    quantity=float(order_result["quantity"]),
                    price=float(order_result["price"]) if order_result["price"] else None,
                    status=order_result["status"],
                    filled_quantity=float(order_result["filled_quantity"]),
                    remaining_quantity=float(order_result["remaining_quantity"]),
                    average_price=float(order_result["average_price"]) if order_result["average_price"] else None,
                    created_at=order_result["created_at"],
                    submitted_at=order_result.get("submitted_at"),
                    commission=float(order_result.get("commission", 0)),
                    fee=float(order_result.get("fee", 0))
                )
                
                logger.info(f"订单提交成功: {order_result['order_id']}")
                return APIResponse(
                    success=True,
                    message="订单提交成功",
                    data=order_response
                )
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"订单提交失败: {e}", exc_info=True)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"订单提交失败: {str(e)}"
                )
        
        @self.router.get("/orders", response_model=APIResponse[List[OrderResponse]])
        async def get_orders(
            status: Optional[str] = Query(None, description="订单状态过滤"),
            symbol: Optional[str] = Query(None, description="交易标的过滤"),
            exchange: Optional[str] = Query(None, description="交易所过滤"),
            limit: int = Query(50, le=200, description="返回数量限制"),
            offset: int = Query(0, ge=0, description="偏移量"),
            current_user: Dict[str, Any] = Depends(get_current_user)
        ):
            """
            获取订单列表
            
            根据条件查询用户的订单列表
            """
            try:
                # 构造查询参数
                query_params = {
                    "user_id": current_user["user_id"],
                    "status": status,
                    "symbol": symbol,
                    "exchange": exchange,
                    "limit": limit,
                    "offset": offset
                }
                
                # 查询订单
                orders_result = await self.trading_app_service.get_orders(query_params)
                
                # 构造响应
                orders_response = []
                for order in orders_result["orders"]:
                    order_response = OrderResponse(
                        order_id=order["order_id"],
                        user_id=order["user_id"],
                        account_id=order["account_id"],
                        symbol=order["symbol"],
                        exchange=order["exchange"],
                        direction=order["direction"],
                        order_type=order["order_type"],
                        quantity=float(order["quantity"]),
                        price=float(order["price"]) if order["price"] else None,
                        status=order["status"],
                        filled_quantity=float(order["filled_quantity"]),
                        remaining_quantity=float(order["remaining_quantity"]),
                        average_price=float(order["average_price"]) if order["average_price"] else None,
                        created_at=order["created_at"],
                        submitted_at=order.get("submitted_at"),
                        commission=float(order.get("commission", 0)),
                        fee=float(order.get("fee", 0)),
                        error_message=order.get("error_message")
                    )
                    orders_response.append(order_response)
                
                return APIResponse(
                    success=True,
                    message=f"获取到 {len(orders_response)} 条订单记录",
                    data=orders_response
                )
                
            except Exception as e:
                logger.error(f"获取订单列表失败: {e}", exc_info=True)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"获取订单列表失败: {str(e)}"
                )
        
        @self.router.delete("/orders/{order_id}", response_model=APIResponse[Dict[str, Any]])
        async def cancel_order(
            order_id: str,
            current_user: Dict[str, Any] = Depends(get_current_user)
        ):
            """
            取消订单
            
            取消指定的订单
            """
            try:
                # 验证订单所有权
                order_info = await self.trading_app_service.get_order_by_id(order_id)
                if not order_info:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="订单不存在"
                    )
                
                if order_info["user_id"] != current_user["user_id"]:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="无权取消此订单"
                    )
                
                # 检查订单状态
                if order_info["status"] not in ["pending", "submitted", "partial_filled"]:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"订单状态为 {order_info['status']}，无法取消"
                    )
                
                # 取消订单
                cancel_result = await self.trading_app_service.cancel_order(order_id)
                
                logger.info(f"订单取消成功: {order_id}")
                return APIResponse(
                    success=True,
                    message="订单取消成功",
                    data={
                        "order_id": order_id,
                        "cancelled_at": cancel_result["cancelled_at"],
                        "remaining_quantity": cancel_result["remaining_quantity"]
                    }
                )
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"订单取消失败: {e}", exc_info=True)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"订单取消失败: {str(e)}"
                )
        
        @self.router.get("/positions", response_model=APIResponse[List[PositionResponse]])
        async def get_positions(
            symbol: Optional[str] = Query(None, description="交易标的过滤"),
            exchange: Optional[str] = Query(None, description="交易所过滤"),
            current_user: Dict[str, Any] = Depends(get_current_user)
        ):
            """
            获取持仓信息
            
            查询用户的持仓信息
            """
            try:
                # 构造查询参数
                query_params = {
                    "user_id": current_user["user_id"],
                    "account_id": current_user.get("account_id", "default"),
                    "symbol": symbol,
                    "exchange": exchange
                }
                
                # 查询持仓
                positions_result = await self.trading_app_service.get_positions(query_params)
                
                # 构造响应
                positions_response = []
                for position in positions_result["positions"]:
                    position_response = PositionResponse(
                        user_id=position["user_id"],
                        account_id=position["account_id"],
                        symbol=position["symbol"],
                        exchange=position["exchange"],
                        long_quantity=float(position["long_quantity"]),
                        short_quantity=float(position["short_quantity"]),
                        net_quantity=float(position["net_quantity"]),
                        long_cost=float(position["long_cost"]),
                        short_cost=float(position["short_cost"]),
                        current_price=float(position["current_price"]) if position["current_price"] else None,
                        unrealized_pnl=float(position["unrealized_pnl"]),
                        realized_pnl=float(position["realized_pnl"]),
                        total_pnl=float(position["total_pnl"]),
                        market_value=float(position["market_value"]),
                        last_update_time=position.get("last_update_time")
                    )
                    positions_response.append(position_response)
                
                return APIResponse(
                    success=True,
                    message=f"获取到 {len(positions_response)} 个持仓",
                    data=positions_response
                )
                
            except Exception as e:
                logger.error(f"获取持仓信息失败: {e}", exc_info=True)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"获取持仓信息失败: {str(e)}"
                )
        
        @self.router.get("/account", response_model=APIResponse[AccountInfoResponse])
        async def get_account_info(
            current_user: Dict[str, Any] = Depends(get_current_user)
        ):
            """
            获取账户信息
            
            查询用户的账户信息
            """
            try:
                # 查询账户信息
                account_result = await self.trading_app_service.get_account_info(
                    current_user["user_id"],
                    current_user.get("account_id", "default")
                )
                
                # 构造响应
                account_response = AccountInfoResponse(
                    account_id=account_result["account_id"],
                    account_type=account_result["account_type"],
                    balance=float(account_result["balance"]),
                    available_balance=float(account_result["available_balance"]),
                    frozen_balance=float(account_result["frozen_balance"]),
                    margin_used=float(account_result["margin_used"]),
                    margin_available=float(account_result["margin_available"]),
                    total_pnl=float(account_result["total_pnl"]),
                    daily_pnl=float(account_result["daily_pnl"]),
                    total_commission=float(account_result["total_commission"]),
                    currency=account_result["currency"],
                    risk_level=account_result["risk_level"],
                    trading_status=account_result["trading_status"]
                )
                
                return APIResponse(
                    success=True,
                    message="账户信息获取成功",
                    data=account_response
                )
                
            except Exception as e:
                logger.error(f"获取账户信息失败: {e}", exc_info=True)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"获取账户信息失败: {str(e)}"
                )
    
    def _check_trading_permission(self, user: Dict[str, Any]) -> bool:
        """检查用户是否有交易权限"""
        user_role = user.get("role", "guest")
        return user_role in ["admin", "trader"]
    
    def _validate_exchange(self, exchange: str) -> bool:
        """验证交易所是否支持"""
        try:
            ExchangeType(exchange.upper())
            return True
        except ValueError:
            return False
    
    def _validate_order_params(self, request: SubmitOrderRequest):
        """验证订单参数"""
        # 验证交易方向
        if request.direction not in ["buy", "sell"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="交易方向必须是 buy 或 sell"
            )
        
        # 验证订单类型
        if request.order_type not in ["limit", "market", "stop", "stop_limit"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不支持的订单类型"
            )
        
        # 限价单必须有价格
        if request.order_type in ["limit", "stop_limit"] and request.price is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="限价单必须指定价格"
            )
        
        # 止损单必须有止损价格
        if request.order_type in ["stop", "stop_limit"] and request.stop_price is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="止损单必须指定止损价格"
            )
    
    async def _perform_risk_check(self, user: Dict[str, Any], request: SubmitOrderRequest):
        """执行风险检查"""
        # 这里可以添加各种风险检查逻辑
        # 例如：资金检查、持仓限制、交易频率限制等
        
        # 基础资金检查（示例）
        if request.order_type in ["limit", "market"] and request.price and request.quantity:
            estimated_value = request.price * request.quantity
            # 这里应该查询实际账户余额进行检查
            # 暂时使用模拟检查
            if estimated_value > 1000000:  # 100万限制示例
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="订单金额超过风险限制"
                )
    

