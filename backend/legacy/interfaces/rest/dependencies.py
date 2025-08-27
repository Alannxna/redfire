"""
REST API依赖注入模块
==================

提供FastAPI的依赖注入功能，包括用户认证、权限验证等
"""

import logging
from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from pydantic import BaseModel

from ...core.common.exceptions.application_exceptions import PermissionDeniedError, ResourceNotFoundError
from ...domain.user.entities.user import User
from ...domain.user.services.user_domain_service import UserDomainService
from ...core.infrastructure.dependency_container import DependencyContainer

logger = logging.getLogger(__name__)

# JWT配置
SECRET_KEY = "your-secret-key-here"  # 应该从配置文件读取
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# HTTP Bearer认证
security = HTTPBearer()


class TokenData(BaseModel):
    """JWT令牌数据"""
    user_id: Optional[str] = None
    username: Optional[str] = None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """
    获取当前认证用户
    
    Args:
        credentials: HTTP Bearer令牌
        
    Returns:
        User: 当前用户实体
        
    Raises:
        HTTPException: 认证失败
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # 解析JWT令牌
        payload = jwt.decode(
            credentials.credentials, 
            SECRET_KEY, 
            algorithms=[ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
            
        token_data = TokenData(user_id=user_id)
        
    except JWTError:
        raise credentials_exception
    
    # 获取用户服务
    try:
        container = DependencyContainer()
        user_service = container.resolve(UserDomainService)
        
        # 查询用户
        user = await user_service.get_user_by_id(token_data.user_id)
        if user is None:
            raise credentials_exception
            
        return user
        
    except Exception as e:
        logger.error(f"获取用户失败: {e}")
        raise credentials_exception


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[User]:
    """
    获取可选的当前用户（用于可选认证的端点）
    
    Args:
        credentials: 可选的HTTP Bearer令牌
        
    Returns:
        Optional[User]: 当前用户实体或None
    """
    if not credentials:
        return None
        
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """
    要求管理员权限
    
    Args:
        current_user: 当前用户
        
    Returns:
        User: 管理员用户
        
    Raises:
        HTTPException: 权限不足
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator access required"
        )
    return current_user


def require_trader(current_user: User = Depends(get_current_user)) -> User:
    """
    要求交易员权限
    
    Args:
        current_user: 当前用户
        
    Returns:
        User: 交易员用户
        
    Raises:
        HTTPException: 权限不足
    """
    if not (current_user.is_trader or current_user.is_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Trader access required"
        )
    return current_user


def require_analyst(current_user: User = Depends(get_current_user)) -> User:
    """
    要求分析师权限
    
    Args:
        current_user: 当前用户
        
    Returns:
        User: 分析师用户
        
    Raises:
        HTTPException: 权限不足
    """
    if not (current_user.is_analyst or current_user.is_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Analyst access required"
        )
    return current_user


async def get_service_container() -> DependencyContainer:
    """
    获取服务容器
    
    Returns:
        DependencyContainer: 依赖注入容器
    """
    return DependencyContainer()


def create_access_token(data: Dict[str, Any]) -> str:
    """
    创建JWT访问令牌
    
    Args:
        data: 要编码的数据
        
    Returns:
        str: JWT令牌
    """
    from datetime import datetime, timedelta
    
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """
    验证JWT令牌
    
    Args:
        token: JWT令牌
        
    Returns:
        Optional[Dict[str, Any]]: 解码后的数据或None
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None
