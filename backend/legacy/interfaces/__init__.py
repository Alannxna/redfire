"""
接口层 - API和外部接口实现
提供REST API、WebSocket等外部接口
"""

from .rest.app import vnpy_api, app, VnPyWebAPI
from .rest.controllers.user_controller import UserController
from .rest.middleware.auth_middleware import AuthMiddleware, JWTHelper
from .rest.middleware.error_middleware import ErrorHandlingMiddleware

# REST API模型
from .rest.models.common import APIResponse, PaginatedResponse, HealthCheckResponse
from .rest.models.user_models import (
    CreateUserRequest, UpdateUserProfileRequest, ChangePasswordRequest,
    LoginRequest, UserResponse, UsersListResponse, UserProfileResponse
)

__all__ = [
    # 应用程序
    "VnPyWebAPI",
    "app",
    
    # 控制器
    "UserController",
    
    # 中间件
    "AuthMiddleware",
    "JWTHelper", 
    "ErrorHandlingMiddleware",
    
    # 通用模型
    "APIResponse",
    "PaginatedResponse",
    "HealthCheckResponse",
    
    # 用户模型
    "CreateUserRequest",
    "UpdateUserProfileRequest",
    "ChangePasswordRequest",
    "LoginRequest",
    "UserResponse", 
    "UsersListResponse",
    "UserProfileResponse",
]