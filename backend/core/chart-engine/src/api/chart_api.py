"""
图表引擎FastAPI接口 - 与RedFire主系统集成

提供RESTful API接口供前端调用
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Depends, Query, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field
import json

from ..core.chart_engine import ChartEngine, ChartEngineStatus
from ..models.chart_models import (
    ChartType, Interval, ChartConfig, IndicatorConfig, IndicatorType
)

logger = logging.getLogger(__name__)


# Pydantic模型定义
class CreateChartRequest(BaseModel):
    """创建图表请求"""
    symbol: str = Field(..., description="交易品种")
    chart_type: ChartType = Field(ChartType.CANDLESTICK, description="图表类型")
    interval: Interval = Field(Interval.MINUTE_1, description="时间周期")
    config: Optional[Dict[str, Any]] = Field(None, description="图表配置")


class ChartConfigRequest(BaseModel):
    """图表配置请求"""
    title: str = Field("", description="图表标题")
    show_volume: bool = Field(True, description="显示成交量")
    show_crosshair: bool = Field(True, description="显示十字光标")
    show_toolbar: bool = Field(True, description="显示工具栏")
    max_bars: int = Field(1000, description="最大K线数量")
    decimal_places: int = Field(2, description="小数位数")
    auto_scale: bool = Field(True, description="自动缩放")
    show_grid: bool = Field(True, description="显示网格")
    indicators: List[Dict[str, Any]] = Field([], description="技术指标配置")
    main_chart_height: int = Field(400, description="主图高度")
    sub_chart_height: int = Field(100, description="副图高度")
    up_color: str = Field("#26a69a", description="上涨颜色")
    down_color: str = Field("#ef5350", description="下跌颜色")
    background_color: str = Field("#1e1e1e", description="背景颜色")
    grid_color: str = Field("#333333", description="网格颜色")
    text_color: str = Field("#ffffff", description="文字颜色")
    auto_update: bool = Field(True, description="自动更新")
    update_interval: int = Field(1000, description="更新间隔(毫秒)")


class AddIndicatorRequest(BaseModel):
    """添加技术指标请求"""
    type: IndicatorType = Field(..., description="指标类型")
    name: str = Field(..., description="指标名称")
    parameters: Dict[str, Any] = Field({}, description="指标参数")
    color: str = Field("#3498db", description="指标颜色")
    line_width: int = Field(2, description="线条宽度")
    visible: bool = Field(True, description="是否可见")


class ChartResponse(BaseModel):
    """图表响应"""
    chart_id: str
    symbol: str
    chart_type: str
    interval: str
    created_at: str
    is_active: bool
    bar_count: int
    subscribers_count: int


class ChartDataResponse(BaseModel):
    """图表数据响应"""
    chart_id: str
    data: Dict[str, Any]
    timestamp: str


class EngineStatusResponse(BaseModel):
    """引擎状态响应"""
    status: str
    charts_count: int
    subscribers_count: int
    performance: Dict[str, Any]


class ChartEngineAPI:
    """
    图表引擎API类
    
    提供完整的图表API接口，集成到RedFire主系统
    """
    
    def __init__(self, chart_engine: ChartEngine):
        self.chart_engine = chart_engine
        self.router = APIRouter(prefix="/api/chart", tags=["图表引擎"])
        self._setup_routes()
        
        logger.info("图表引擎API初始化完成")
    
    def _setup_routes(self) -> None:
        """设置API路由"""
        
        @self.router.get("/status", response_model=EngineStatusResponse)
        async def get_engine_status():
            """获取引擎状态"""
            try:
                status = self.chart_engine.get_engine_status()
                return EngineStatusResponse(
                    status=status["status"],
                    charts_count=status["charts_count"],
                    subscribers_count=status["subscribers_count"],
                    performance=status["performance"]
                )
            except Exception as e:
                logger.error(f"获取引擎状态失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.router.post("/charts", response_model=Dict[str, Any])
        async def create_chart(request: CreateChartRequest):
            """创建图表"""
            try:
                # 生成图表ID
                chart_id = f"{request.symbol}_{request.interval.value}_{datetime.now().timestamp()}"
                
                # 解析配置
                config = None
                if request.config:
                    config = ChartConfig(**request.config)
                
                # 创建图表
                chart = await self.chart_engine.create_chart(
                    chart_id=chart_id,
                    symbol=request.symbol,
                    chart_type=request.chart_type,
                    interval=request.interval,
                    config=config
                )
                
                return {
                    "success": True,
                    "chart_id": chart_id,
                    "message": "图表创建成功",
                    "chart": {
                        "chart_id": chart.chart_id,
                        "symbol": chart.symbol,
                        "chart_type": chart.chart_type.value,
                        "interval": chart.interval.value,
                        "created_at": chart.created_at.isoformat(),
                        "is_active": chart.is_active
                    }
                }
            except Exception as e:
                logger.error(f"创建图表失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.router.delete("/charts/{chart_id}")
        async def delete_chart(chart_id: str):
            """删除图表"""
            try:
                await self.chart_engine.delete_chart(chart_id)
                return {"success": True, "message": "图表删除成功"}
            except Exception as e:
                logger.error(f"删除图表失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.router.get("/charts", response_model=List[ChartResponse])
        async def list_charts():
            """获取图表列表"""
            try:
                charts = []
                for chart_id in self.chart_engine.charts:
                    chart_info = self.chart_engine.get_chart_info(chart_id)
                    if chart_info:
                        charts.append(ChartResponse(
                            chart_id=chart_info["chart_id"],
                            symbol=chart_info["symbol"],
                            chart_type=chart_info["chart_type"],
                            interval=chart_info["interval"],
                            created_at=chart_info["created_at"],
                            is_active=chart_info["is_active"],
                            bar_count=chart_info["bar_count"],
                            subscribers_count=chart_info["subscribers_count"]
                        ))
                return charts
            except Exception as e:
                logger.error(f"获取图表列表失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.router.get("/charts/{chart_id}", response_model=ChartResponse)
        async def get_chart_info(chart_id: str):
            """获取图表信息"""
            try:
                chart_info = self.chart_engine.get_chart_info(chart_id)
                if not chart_info:
                    raise HTTPException(status_code=404, detail="图表不存在")
                
                return ChartResponse(
                    chart_id=chart_info["chart_id"],
                    symbol=chart_info["symbol"],
                    chart_type=chart_info["chart_type"],
                    interval=chart_info["interval"],
                    created_at=chart_info["created_at"],
                    is_active=chart_info["is_active"],
                    bar_count=chart_info["bar_count"],
                    subscribers_count=chart_info["subscribers_count"]
                )
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"获取图表信息失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.router.get("/charts/{chart_id}/data", response_model=ChartDataResponse)
        async def get_chart_data(
            chart_id: str,
            limit: Optional[int] = Query(None, description="数据数量限制"),
            start_time: Optional[str] = Query(None, description="开始时间"),
            end_time: Optional[str] = Query(None, description="结束时间")
        ):
            """获取图表数据"""
            try:
                # 解析时间参数
                start_dt = None
                end_dt = None
                if start_time:
                    start_dt = datetime.fromisoformat(start_time)
                if end_time:
                    end_dt = datetime.fromisoformat(end_time)
                
                # 获取渲染数据
                render_data = await self.chart_engine.get_chart_render_data(chart_id)
                
                return ChartDataResponse(
                    chart_id=chart_id,
                    data=render_data,
                    timestamp=datetime.now().isoformat()
                )
            except Exception as e:
                logger.error(f"获取图表数据失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.router.post("/charts/{chart_id}/subscribe")
        async def subscribe_chart(chart_id: str, subscriber_id: str):
            """订阅图表"""
            try:
                subscription_info = await self.chart_engine.subscribe_chart(chart_id, subscriber_id)
                return {
                    "success": True,
                    "message": "订阅成功",
                    "subscription": subscription_info.to_dict()
                }
            except Exception as e:
                logger.error(f"订阅图表失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.router.post("/charts/{chart_id}/unsubscribe")
        async def unsubscribe_chart(chart_id: str, subscriber_id: str):
            """取消订阅图表"""
            try:
                await self.chart_engine.unsubscribe_chart(chart_id, subscriber_id)
                return {"success": True, "message": "取消订阅成功"}
            except Exception as e:
                logger.error(f"取消订阅图表失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.router.post("/charts/{chart_id}/indicators")
        async def add_indicator(chart_id: str, request: AddIndicatorRequest):
            """添加技术指标"""
            try:
                if chart_id not in self.chart_engine.charts:
                    raise HTTPException(status_code=404, detail="图表不存在")
                
                chart = self.chart_engine.charts[chart_id]
                
                # 创建指标配置
                indicator_config = IndicatorConfig(
                    type=request.type,
                    name=request.name,
                    parameters=request.parameters,
                    color=request.color,
                    line_width=request.line_width,
                    visible=request.visible
                )
                
                # 添加到图表配置
                chart.config.add_indicator(indicator_config)
                
                return {
                    "success": True,
                    "message": "技术指标添加成功",
                    "indicator": {
                        "type": request.type.value,
                        "name": request.name,
                        "parameters": request.parameters
                    }
                }
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"添加技术指标失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.router.delete("/charts/{chart_id}/indicators/{indicator_name}")
        async def remove_indicator(chart_id: str, indicator_name: str):
            """移除技术指标"""
            try:
                if chart_id not in self.chart_engine.charts:
                    raise HTTPException(status_code=404, detail="图表不存在")
                
                chart = self.chart_engine.charts[chart_id]
                chart.config.remove_indicator(indicator_name)
                
                return {"success": True, "message": "技术指标移除成功"}
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"移除技术指标失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))
    
    def get_router(self) -> APIRouter:
        """获取API路由器"""
        return self.router
