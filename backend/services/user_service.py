#!/usr/bin/env python3
"""
用户服务层
处理用户相关的业务逻辑
"""

from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from models.database_models import WebUser
from schemas.auth_schemas import UserRegisterRequest, UserResponse
from auth.security import get_password_hash, verify_password, create_access_token, generate_user_id


class UserService:
    """用户服务类"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_user_by_username(self, username: str) -> Optional[WebUser]:
        """根据用户名获取用户"""
        return self.db.query(WebUser).filter(
            (WebUser.username == username) | (WebUser.email == username)
        ).first()
    
    def get_user_by_email(self, email: str) -> Optional[WebUser]:
        """根据邮箱获取用户"""
        return self.db.query(WebUser).filter(WebUser.email == email).first()
    
    def get_user_by_id(self, user_id: str) -> Optional[WebUser]:
        """根据用户ID获取用户"""
        return self.db.query(WebUser).filter(WebUser.user_id == user_id).first()
    
    def create_user(self, user_data: UserRegisterRequest) -> tuple[bool, str, Optional[WebUser]]:
        """创建新用户"""
        try:
            # 检查用户名是否已存在
            if self.get_user_by_username(user_data.username):
                return False, "用户名已存在", None
            
            # 检查邮箱是否已存在
            if self.get_user_by_email(user_data.email):
                return False, "邮箱已存在", None
            
            # 创建新用户
            hashed_password = get_password_hash(user_data.password)
            new_user = WebUser(
                user_id=generate_user_id(),
                username=user_data.username,
                email=user_data.email,
                password_hash=hashed_password,
                full_name=user_data.full_name,
                phone=user_data.phone,
                created_at=datetime.utcnow()
            )
            
            self.db.add(new_user)
            self.db.commit()
            self.db.refresh(new_user)
            
            return True, "用户创建成功", new_user
            
        except IntegrityError:
            self.db.rollback()
            return False, "用户信息冲突", None
        except Exception as e:
            self.db.rollback()
            return False, f"创建用户失败: {str(e)}", None
    
    def authenticate_user(self, username: str, password: str) -> tuple[bool, str, Optional[WebUser]]:
        """用户认证"""
        user = self.get_user_by_username(username)
        if not user:
            return False, "用户不存在", None
        
        if not user.is_active:
            return False, "用户已被禁用", None
        
        if not verify_password(password, user.password_hash):
            return False, "密码错误", None
        
        # 更新最后登录时间
        user.last_login = datetime.utcnow()
        self.db.commit()
        
        return True, "登录成功", user
    
    def create_access_token_for_user(self, user: WebUser) -> str:
        """为用户创建访问令牌"""
        token_data = {
            "sub": user.user_id,
            "username": user.username,
            "role": user.role
        }
        return create_access_token(token_data)
    
    def update_user_profile(self, user_id: str, **kwargs) -> tuple[bool, str, Optional[WebUser]]:
        """更新用户资料"""
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                return False, "用户不存在", None
            
            # 更新允许的字段
            allowed_fields = ['full_name', 'phone', 'is_verified']
            for field, value in kwargs.items():
                if field in allowed_fields and hasattr(user, field):
                    setattr(user, field, value)
            
            user.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(user)
            
            return True, "用户资料更新成功", user
            
        except Exception as e:
            self.db.rollback()
            return False, f"更新失败: {str(e)}", None
    
    def deactivate_user(self, user_id: str) -> tuple[bool, str]:
        """停用用户"""
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                return False, "用户不存在"
            
            user.is_active = False
            user.updated_at = datetime.utcnow()
            self.db.commit()
            
            return True, "用户已停用"
            
        except Exception as e:
            self.db.rollback()
            return False, f"停用失败: {str(e)}"