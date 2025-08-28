#!/usr/bin/env python3
"""
API基础路由和工具
提供通用的响应格式、错误处理和工具函数
"""

from datetime import datetime, timezone
from typing import Any, Dict, Optional, Union
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel


class APIResponse(BaseModel):
    """标准API响应格式"""
    success: bool
    message: str
    data: Optional[Any] = None
    error_code: Optional[str] = None
    timestamp: str = datetime.now(timezone.utc).isoformat()


class ErrorResponse(BaseModel):
    """错误响应格式"""
    success: bool = False
    message: str
    error_code: str
    timestamp: str = datetime.now(timezone.utc).isoformat()


def create_success_response(
    message: str = "操作成功",
    data: Any = None,
    status_code: int = status.HTTP_200_OK
) -> JSONResponse:
    """创建成功响应"""
    response = APIResponse(
        success=True,
        message=message,
        data=data
    )
    return JSONResponse(
        content=response.dict(),
        status_code=status_code
    )


def create_error_response(
    message: str,
    error_code: str = "UNKNOWN_ERROR",
    status_code: int = status.HTTP_400_BAD_REQUEST
) -> JSONResponse:
    """创建错误响应"""
    response = ErrorResponse(
        message=message,
        error_code=error_code
    )
    return JSONResponse(
        content=response.dict(),
        status_code=status_code
    )


def handle_api_exception(exc: Exception) -> JSONResponse:
    """处理API异常"""
    if isinstance(exc, HTTPException):
        return create_error_response(
            message=str(exc.detail),
            error_code=f"HTTP_{exc.status_code}",
            status_code=exc.status_code
        )
    
    return create_error_response(
        message="内部服务器错误",
        error_code="INTERNAL_ERROR",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
    )


# 创建基础路由器
base_router = APIRouter(tags=["基础"])


@base_router.get("/health")
async def health_check():
    """健康检查接口"""
    return create_success_response(
        message="服务运行正常",
        data={
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "version": "1.0.0"
        }
    )


@base_router.get("/")
async def root():
    """根路径接口"""
    return create_success_response(
        message="欢迎使用 RedFire API",
        data={
            "service": "RedFire Trading System",
            "version": "1.0.0",
            "docs": "/docs",
            "health": "/health"
        }
    )
