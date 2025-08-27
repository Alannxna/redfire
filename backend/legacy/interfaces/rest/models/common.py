"""
通用API模型
===========

定义通用的API请求和响应模型
"""

from typing import Any, Optional, List, Dict
from pydantic import BaseModel, Field
from datetime import datetime


class APIResponse(BaseModel):
    """通用API响应模型"""
    
    success: bool = Field(..., description="操作是否成功")
    message: str = Field(..., description="响应消息")
    data: Optional[Any] = Field(None, description="响应数据")
    error: Optional[str] = Field(None, description="错误信息")
    timestamp: datetime = Field(default_factory=datetime.now, description="响应时间")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class PaginatedResponse(BaseModel):
    """分页响应模型"""
    
    success: bool = Field(..., description="操作是否成功")
    message: str = Field(..., description="响应消息")
    data: List[Any] = Field(..., description="数据列表")
    pagination: Dict[str, Any] = Field(..., description="分页信息")
    error: Optional[str] = Field(None, description="错误信息")
    timestamp: datetime = Field(default_factory=datetime.now, description="响应时间")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class HealthCheckResponse(BaseModel):
    """健康检查响应模型"""
    
    status: str = Field(..., description="服务状态")
    message: str = Field(..., description="状态消息")
    version: str = Field(..., description="版本号")
    timestamp: datetime = Field(default_factory=datetime.now, description="检查时间")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ValidationErrorResponse(BaseModel):
    """验证错误响应模型"""
    
    success: bool = Field(default=False, description="操作是否成功")
    message: str = Field(..., description="错误消息")
    errors: List[Dict[str, Any]] = Field(..., description="详细错误信息")
    timestamp: datetime = Field(default_factory=datetime.now, description="错误时间")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ErrorResponse(BaseModel):
    """通用错误响应模型"""
    
    success: bool = Field(default=False, description="操作是否成功")
    message: str = Field(..., description="错误消息")
    error_code: Optional[str] = Field(None, description="错误代码")
    error_detail: Optional[str] = Field(None, description="错误详情")
    timestamp: datetime = Field(default_factory=datetime.now, description="错误时间")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }