#!/usr/bin/env python3
"""
数据传输对象（DTOs）模块
"""

from .auth_schemas import (
    UserRegisterRequest,
    UserLoginRequest,
    UserResponse,
    TokenResponse,
    LoginResponse,
    RegisterResponse,
    ErrorResponse
)

__all__ = [
    "UserRegisterRequest",
    "UserLoginRequest", 
    "UserResponse",
    "TokenResponse",
    "LoginResponse",
    "RegisterResponse",
    "ErrorResponse"
]
