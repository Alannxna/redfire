"""
策略引擎控制器
提供策略引擎管理、策略管理、网关管理等核心API接口
"""

import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from src.application.services.strategy.strategy_application_service import StrategyApplicationService
from src.domain.strategy.entities.strategy_entity import (
    StrategyStatus, StrategyType, StrategyConfiguration, StrategyInstance
)
from src.interfaces.rest.middleware.auth_middleware import get_current_user
from src.interfaces.rest.models.user import User

logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter(prefix="/api/strategy-engine", tags=["策略引擎"])

# ==================== 请求/响应模型 ====================

class EngineStatusResponse(BaseModel):
    """引擎状态响应"""
    engine_id: str
    status: str
    uptime: str
    strategy_count: int
    gateway_count: int
    last_heartbeat: str
    version: str
    is_healthy: bool

class StrategyCreateRequest(BaseModel):
    """策略创建请求"""
    strategy_name: str = Field(..., description="策略名称")
    strategy_type: StrategyType = Field(..., description="策略类型")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="策略参数")
    risk_limits: Dict[str, Any] = Field(default_factory=dict, description="风险限制")
    description: Optional[str] = Field(None, description="策略描述")

class StrategyResponse(BaseModel):
    """策略响应"""
    strategy_id: str
    strategy_name: str
    strategy_type: StrategyType
    status: StrategyStatus
    parameters: Dict[str, Any]
    risk_limits: Dict[str, Any]
    performance: Dict[str, Any]
    created_at: str
    updated_at: str

class GatewayResponse(BaseModel):
    """网关响应"""
    gateway_id: str
    gateway_name: str
    gateway_type: str
    status: str
    connection_info: Dict[str, Any]
    last_connection: str
    is_connected: bool

class ContractInfoResponse(BaseModel):
    """合约信息响应"""
    symbol: str
    exchange: str
    contract_type: str
    size: float
    price_tick: float
    min_volume: float
    trading_hours: str
    last_price: float
    bid_price: float
    ask_price: float
    volume: int
    open_interest: int

class MarketDataRequest(BaseModel):
    """市场数据请求"""
    symbols: List[str] = Field(..., description="交易品种列表")
    data_type: str = Field(default="tick", description="数据类型: tick, bar, depth")
    interval: Optional[str] = Field(None, description="K线间隔(仅用于bar数据)")

class MarketDataResponse(BaseModel):
    """市场数据响应"""
    symbol: str
    data_type: str
    timestamp: str
    data: Dict[str, Any]

# ==================== 依赖注入 ====================

async def get_strategy_service() -> StrategyApplicationService:
    """获取策略应用服务依赖"""
    # 这里应该从依赖注入容器获取
    # 暂时返回None，后续集成
    return None

# ==================== 引擎管理API ====================

@router.post("/engine/start", response_model=Dict[str, Any])
async def start_engine(
    current_user: User = Depends(get_current_user),
    strategy_service: StrategyApplicationService = Depends(get_strategy_service)
):
    """
    启动策略引擎
    
    启动VnPy策略引擎，初始化所有必要的服务和连接
    """
    try:
        if not strategy_service:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="策略服务不可用"
            )
        
        # 启动引擎
        result = await strategy_service.start_engine()
        
        logger.info(f"用户 {current_user.username} 启动了策略引擎")
        
        return {
            "success": True,
            "message": "策略引擎启动成功",
            "engine_id": result.get("engine_id"),
            "start_time": result.get("start_time")
        }
        
    except Exception as e:
        logger.error(f"启动策略引擎失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"启动策略引擎失败: {str(e)}"
        )

@router.post("/engine/stop", response_model=Dict[str, Any])
async def stop_engine(
    current_user: User = Depends(get_current_user),
    strategy_service: StrategyApplicationService = Depends(get_strategy_service)
):
    """
    停止策略引擎
    
    安全停止VnPy策略引擎，保存所有状态并关闭连接
    """
    try:
        if not strategy_service:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="策略服务不可用"
            )
        
        # 停止引擎
        result = await strategy_service.stop_engine()
        
        logger.info(f"用户 {current_user.username} 停止了策略引擎")
        
        return {
            "success": True,
            "message": "策略引擎停止成功",
            "stop_time": result.get("stop_time"),
            "final_status": result.get("final_status")
        }
        
    except Exception as e:
        logger.error(f"停止策略引擎失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"停止策略引擎失败: {str(e)}"
        )

@router.get("/engine/status", response_model=EngineStatusResponse)
async def get_engine_status(
    current_user: User = Depends(get_current_user),
    strategy_service: StrategyApplicationService = Depends(get_strategy_service)
):
    """
    获取引擎状态
    
    获取策略引擎的详细状态信息，包括运行状态、策略数量、网关状态等
    """
    try:
        if not strategy_service:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="策略服务不可用"
            )
        
        # 获取引擎状态
        status_info = await strategy_service.get_engine_status()
        
        return EngineStatusResponse(**status_info)
        
    except Exception as e:
        logger.error(f"获取引擎状态失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取引擎状态失败: {str(e)}"
        )

# ==================== 策略管理API ====================

@router.post("/strategy/create", response_model=StrategyResponse)
async def create_strategy(
    request: StrategyCreateRequest,
    current_user: User = Depends(get_current_user),
    strategy_service: StrategyApplicationService = Depends(get_strategy_service)
):
    """
    创建策略
    
    创建新的交易策略，包括配置参数和风险限制设置
    """
    try:
        if not strategy_service:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="策略服务不可用"
            )
        
        # 创建策略
        strategy = await strategy_service.create_strategy(
            strategy_name=request.strategy_name,
            strategy_type=request.strategy_type,
            parameters=request.parameters,
            risk_limits=request.risk_limits,
            description=request.description,
            user_id=current_user.id
        )
        
        logger.info(f"用户 {current_user.username} 创建了策略: {request.strategy_name}")
        
        return StrategyResponse(
            strategy_id=strategy.strategy_id,
            strategy_name=strategy.strategy_name,
            strategy_type=strategy.strategy_type,
            status=strategy.status,
            parameters=strategy.parameters,
            risk_limits=strategy.risk_limits,
            performance=strategy.performance.to_dict() if strategy.performance else {},
            created_at=strategy.created_at.isoformat(),
            updated_at=strategy.updated_at.isoformat()
        )
        
    except Exception as e:
        logger.error(f"创建策略失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建策略失败: {str(e)}"
        )

@router.get("/strategy/list", response_model=List[StrategyResponse])
async def get_strategy_list(
    current_user: User = Depends(get_current_user),
    strategy_service: StrategyApplicationService = Depends(get_strategy_service)
):
    """
    获取策略列表
    
    获取当前用户的所有策略列表
    """
    try:
        if not strategy_service:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="策略服务不可用"
            )
        
        # 获取策略列表
        strategies = await strategy_service.get_user_strategies(user_id=current_user.id)
        
        return [
            StrategyResponse(
                strategy_id=strategy.strategy_id,
                strategy_name=strategy.strategy_name,
                strategy_type=strategy.strategy_type,
                status=strategy.status,
                parameters=strategy.parameters,
                risk_limits=strategy.risk_limits,
                performance=strategy.performance.to_dict() if strategy.performance else {},
                created_at=strategy.created_at.isoformat(),
                updated_at=strategy.updated_at.isoformat()
            )
            for strategy in strategies
        ]
        
    except Exception as e:
        logger.error(f"获取策略列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取策略列表失败: {str(e)}"
        )

@router.get("/strategy/{strategy_id}", response_model=StrategyResponse)
async def get_strategy_detail(
    strategy_id: str,
    current_user: User = Depends(get_current_user),
    strategy_service: StrategyApplicationService = Depends(get_strategy_service)
):
    """
    获取策略详情
    
    获取指定策略的详细信息
    """
    try:
        if not strategy_service:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="策略服务不可用"
            )
        
        # 获取策略详情
        strategy = await strategy_service.get_strategy(strategy_id=strategy_id, user_id=current_user.id)
        
        if not strategy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="策略不存在"
            )
        
        return StrategyResponse(
            strategy_id=strategy.strategy_id,
            strategy_name=strategy.strategy_name,
            strategy_type=strategy.strategy_type,
            status=strategy.status,
            parameters=strategy.parameters,
            risk_limits=strategy.risk_limits,
            performance=strategy.performance.to_dict() if strategy.performance else {},
            created_at=strategy.created_at.isoformat(),
            updated_at=strategy.updated_at.isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取策略详情失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取策略详情失败: {str(e)}"
        )

@router.post("/strategy/{strategy_id}/start", response_model=Dict[str, Any])
async def start_strategy(
    strategy_id: str,
    current_user: User = Depends(get_current_user),
    strategy_service: StrategyApplicationService = Depends(get_strategy_service)
):
    """
    启动策略
    
    启动指定的交易策略
    """
    try:
        if not strategy_service:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="策略服务不可用"
            )
        
        # 启动策略
        result = await strategy_service.start_strategy(strategy_id=strategy_id, user_id=current_user.id)
        
        logger.info(f"用户 {current_user.username} 启动了策略: {strategy_id}")
        
        return {
            "success": True,
            "message": "策略启动成功",
            "strategy_id": strategy_id,
            "start_time": result.get("start_time")
        }
        
    except Exception as e:
        logger.error(f"启动策略失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"启动策略失败: {str(e)}"
        )

@router.post("/strategy/{strategy_id}/stop", response_model=Dict[str, Any])
async def stop_strategy(
    strategy_id: str,
    current_user: User = Depends(get_current_user),
    strategy_service: StrategyApplicationService = Depends(get_strategy_service)
):
    """
    停止策略
    
    停止指定的交易策略
    """
    try:
        if not strategy_service:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="策略服务不可用"
            )
        
        # 停止策略
        result = await strategy_service.stop_strategy(strategy_id=strategy_id, user_id=current_user.id)
        
        logger.info(f"用户 {current_user.username} 停止了策略: {strategy_id}")
        
        return {
            "success": True,
            "message": "策略停止成功",
            "strategy_id": strategy_id,
            "stop_time": result.get("stop_time")
        }
        
    except Exception as e:
        logger.error(f"停止策略失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"停止策略失败: {str(e)}"
        )

# ==================== 网关管理API ====================

@router.get("/gateway/list", response_model=List[GatewayResponse])
async def get_gateway_list(
    current_user: User = Depends(get_current_user),
    strategy_service: StrategyApplicationService = Depends(get_strategy_service)
):
    """
    获取网关列表
    
    获取所有可用的交易网关信息
    """
    try:
        if not strategy_service:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="策略服务不可用"
            )
        
        # 获取网关列表
        gateways = await strategy_service.get_gateway_list()
        
        return [
            GatewayResponse(
                gateway_id=gateway.gateway_id,
                gateway_name=gateway.gateway_name,
                gateway_type=gateway.gateway_type,
                status=gateway.status,
                connection_info=gateway.connection_info,
                last_connection=gateway.last_connection.isoformat() if gateway.last_connection else "",
                is_connected=gateway.is_connected
            )
            for gateway in gateways
        ]
        
    except Exception as e:
        logger.error(f"获取网关列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取网关列表失败: {str(e)}"
        )

@router.post("/gateway/{gateway_id}/connect", response_model=Dict[str, Any])
async def connect_gateway(
    gateway_id: str,
    current_user: User = Depends(get_current_user),
    strategy_service: StrategyApplicationService = Depends(get_strategy_service)
):
    """
    连接网关
    
    连接到指定的交易网关
    """
    try:
        if not strategy_service:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="策略服务不可用"
            )
        
        # 连接网关
        result = await strategy_service.connect_gateway(gateway_id=gateway_id)
        
        logger.info(f"用户 {current_user.username} 连接了网关: {gateway_id}")
        
        return {
            "success": True,
            "message": "网关连接成功",
            "gateway_id": gateway_id,
            "connection_time": result.get("connection_time")
        }
        
    except Exception as e:
        logger.error(f"连接网关失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"连接网关失败: {str(e)}"
        )

@router.post("/gateway/{gateway_id}/disconnect", response_model=Dict[str, Any])
async def disconnect_gateway(
    gateway_id: str,
    current_user: User = Depends(get_current_user),
    strategy_service: StrategyApplicationService = Depends(get_strategy_service)
):
    """
    断开网关
    
    断开指定的交易网关连接
    """
    try:
        if not strategy_service:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="策略服务不可用"
            )
        
        # 断开网关
        result = await strategy_service.disconnect_gateway(gateway_id=gateway_id)
        
        logger.info(f"用户 {current_user.username} 断开了网关: {gateway_id}")
        
        return {
            "success": True,
            "message": "网关断开成功",
            "gateway_id": gateway_id,
            "disconnect_time": result.get("disconnect_time")
        }
        
    except Exception as e:
        logger.error(f"断开网关失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"断开网关失败: {str(e)}"
        )

@router.get("/gateway/{gateway_id}/contracts", response_model=List[ContractInfoResponse])
async def get_contract_info(
    gateway_id: str,
    current_user: User = Depends(get_current_user),
    strategy_service: StrategyApplicationService = Depends(get_strategy_service)
):
    """
    获取合约信息
    
    获取指定网关的合约信息列表
    """
    try:
        if not strategy_service:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="策略服务不可用"
            )
        
        # 获取合约信息
        contracts = await strategy_service.get_contract_info(gateway_id=gateway_id)
        
        return [
            ContractInfoResponse(
                symbol=contract.symbol,
                exchange=contract.exchange,
                contract_type=contract.contract_type,
                size=contract.size,
                price_tick=contract.price_tick,
                min_volume=contract.min_volume,
                trading_hours=contract.trading_hours,
                last_price=contract.last_price,
                bid_price=contract.bid_price,
                ask_price=contract.ask_price,
                volume=contract.volume,
                open_interest=contract.open_interest
            )
            for contract in contracts
        ]
        
    except Exception as e:
        logger.error(f"获取合约信息失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取合约信息失败: {str(e)}"
        )

# ==================== 实时数据API ====================

@router.post("/market-data/subscribe", response_model=Dict[str, Any])
async def subscribe_market_data(
    request: MarketDataRequest,
    current_user: User = Depends(get_current_user),
    strategy_service: StrategyApplicationService = Depends(get_strategy_service)
):
    """
    订阅市场数据
    
    订阅指定品种的实时市场数据
    """
    try:
        if not strategy_service:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="策略服务不可用"
            )
        
        # 订阅市场数据
        result = await strategy_service.subscribe_market_data(
            symbols=request.symbols,
            data_type=request.data_type,
            interval=request.interval,
            user_id=current_user.id
        )
        
        logger.info(f"用户 {current_user.username} 订阅了市场数据: {request.symbols}")
        
        return {
            "success": True,
            "message": "市场数据订阅成功",
            "subscription_id": result.get("subscription_id"),
            "symbols": request.symbols,
            "data_type": request.data_type
        }
        
    except Exception as e:
        logger.error(f"订阅市场数据失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"订阅市场数据失败: {str(e)}"
        )

@router.get("/market-data/realtime", response_model=List[MarketDataResponse])
async def get_realtime_data(
    symbols: str,
    current_user: User = Depends(get_current_user),
    strategy_service: StrategyApplicationService = Depends(get_strategy_service)
):
    """
    获取实时数据
    
    获取指定品种的实时市场数据
    """
    try:
        if not strategy_service:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="策略服务不可用"
            )
        
        # 解析品种列表
        symbol_list = [s.strip() for s in symbols.split(",") if s.strip()]
        
        # 获取实时数据
        data_list = await strategy_service.get_realtime_data(
            symbols=symbol_list,
            user_id=current_user.id
        )
        
        return [
            MarketDataResponse(
                symbol=data.symbol,
                data_type=data.data_type,
                timestamp=data.timestamp.isoformat(),
                data=data.data
            )
            for data in data_list
        ]
        
    except Exception as e:
        logger.error(f"获取实时数据失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取实时数据失败: {str(e)}"
        )

# ==================== 策略监控API ====================

@router.get("/strategy/{strategy_id}/performance", response_model=Dict[str, Any])
async def get_strategy_performance(
    strategy_id: str,
    current_user: User = Depends(get_current_user),
    strategy_service: StrategyApplicationService = Depends(get_strategy_service)
):
    """
    获取策略绩效
    
    获取指定策略的实时绩效数据
    """
    try:
        if not strategy_service:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="策略服务不可用"
            )
        
        # 获取策略绩效
        performance = await strategy_service.get_strategy_performance(
            strategy_id=strategy_id,
            user_id=current_user.id
        )
        
        return performance
        
    except Exception as e:
        logger.error(f"获取策略绩效失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取策略绩效失败: {str(e)}"
        )

@router.get("/strategy/{strategy_id}/positions", response_model=List[Dict[str, Any]])
async def get_strategy_positions(
    strategy_id: str,
    current_user: User = Depends(get_current_user),
    strategy_service: StrategyApplicationService = Depends(get_strategy_service)
):
    """
    获取策略持仓
    
    获取指定策略的实时持仓数据
    """
    try:
        if not strategy_service:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="策略服务不可用"
            )
        
        # 获取策略持仓
        positions = await strategy_service.get_strategy_positions(
            strategy_id=strategy_id,
            user_id=current_user.id
        )
        
        return positions
        
    except Exception as e:
        logger.error(f"获取策略持仓失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取策略持仓失败: {str(e)}"
        )
