#!/usr/bin/env python3
"""
认证相关的数据传输对象（DTOs）
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class UserRegisterRequest(BaseModel):
    """用户注册请求"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: EmailStr = Field(..., description="邮箱地址")
    password: str = Field(..., min_length=6, max_length=100, description="密码")
    full_name: Optional[str] = Field(None, max_length=100, description="全名")
    phone: Optional[str] = Field(None, max_length=20, description="手机号")


class UserLoginRequest(BaseModel):
    """用户登录请求"""
    username: str = Field(..., description="用户名或邮箱")
    password: str = Field(..., description="密码")


class UserResponse(BaseModel):
    """用户响应"""
    id: int
    user_id: str
    username: str
    email: str
    full_name: Optional[str] = None
    phone: Optional[str] = None
    role: str = "user"
    is_active: bool = True
    is_verified: bool = False
    created_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """令牌响应"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 1800  # 30分钟
    user: UserResponse


class LoginResponse(BaseModel):
    """登录响应"""
    success: bool
    message: str
    data: Optional[TokenResponse] = None


class RegisterResponse(BaseModel):
    """注册响应"""
    success: bool
    message: str
    data: Optional[UserResponse] = None


class ErrorResponse(BaseModel):
    """错误响应"""
    success: bool = False
    message: str
    details: Optional[str] = None
