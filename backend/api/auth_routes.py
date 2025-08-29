#!/usr/bin/env python3
"""
认证相关的API路由
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from database import get_db
from services.user_service import UserService
from schemas.auth_schemas import (
    UserRegisterRequest, 
    UserLoginRequest, 
    LoginResponse, 
    RegisterResponse,
    TokenResponse,
    UserResponse,
    ErrorResponse
)
from auth.security import verify_token

# 创建路由器
router = APIRouter(prefix="/api/auth", tags=["认证"])
security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """获取当前用户"""
    token = credentials.credentials
    payload = verify_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_service = UserService(db)
    user = user_service.get_user_by_id(payload.get("sub"))
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserRegisterRequest,
    db: Session = Depends(get_db)
):
    """用户注册"""
    user_service = UserService(db)
    success, message, user = user_service.create_user(user_data)
    
    if not success:
        return RegisterResponse(
            success=False,
            message=message
        )
    
    return RegisterResponse(
        success=True,
        message=message,
        data=UserResponse.from_orm(user)
    )


@router.post("/login", response_model=LoginResponse)
async def login_user(
    login_data: UserLoginRequest,
    db: Session = Depends(get_db)
):
    """用户登录"""
    user_service = UserService(db)
    success, message, user = user_service.authenticate_user(
        login_data.username, 
        login_data.password
    )
    
    if not success:
        return LoginResponse(
            success=False,
            message=message
        )
    
    # 生成访问令牌
    access_token = user_service.create_access_token_for_user(user)
    
    return LoginResponse(
        success=True,
        message=message,
        data=TokenResponse(
            access_token=access_token,
            user=UserResponse.from_orm(user)
        )
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user = Depends(get_current_user)
):
    """获取当前用户信息"""
    return UserResponse.from_orm(current_user)


@router.post("/logout")
async def logout_user():
    """用户登出"""
    # 在实际应用中，这里可能需要将token加入黑名单
    return {"success": True, "message": "登出成功"}


@router.get("/verify-token")
async def verify_user_token(
    current_user = Depends(get_current_user)
):
    """验证令牌有效性"""
    return {
        "success": True, 
        "message": "令牌有效",
        "user": UserResponse.from_orm(current_user)
    }
