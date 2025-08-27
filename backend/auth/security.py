#!/usr/bin/env python3
"""
认证和安全相关工具
包含密码哈希、JWT token生成和验证等功能
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Union
import uuid

from jose import JWTError, jwt
from passlib.context import CryptContext
from passlib.hash import bcrypt

# 密码哈希上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT设置
SECRET_KEY = "your-secret-key-change-in-production"  # 生产环境中应该从环境变量读取
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """生成密码哈希"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """创建访问令牌"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """验证令牌并返回payload"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def generate_session_id() -> str:
    """生成会话ID"""
    return str(uuid.uuid4())


def generate_user_id() -> str:
    """生成用户ID"""
    return str(uuid.uuid4())
