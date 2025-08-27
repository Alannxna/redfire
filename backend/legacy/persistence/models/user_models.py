"""
用户持久化模型
SQLAlchemy ORM模型定义
"""

from sqlalchemy import Column, String, Boolean, DateTime, Enum, Text, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from datetime import datetime

from .base import BaseModel
from ...core.common.enums.user_roles import UserRole, UserStatus


class UserModel(BaseModel):
    """用户数据模型"""
    
    __tablename__ = "users"
    
    # 基本信息
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    
    # 个人信息
    full_name = Column(String(100), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    
    # 角色和状态
    role = Column(Enum(UserRole), nullable=False, default=UserRole.TRADER, index=True)
    status = Column(Enum(UserStatus), nullable=False, default=UserStatus.ACTIVE, index=True)
    
    # 验证信息
    email_verified = Column(Boolean, nullable=False, default=False)
    email_verification_token = Column(String(255), nullable=True)
    email_verification_expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # 密码重置
    password_reset_token = Column(String(255), nullable=True)
    password_reset_expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # 时间戳
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    
    # 额外信息
    preferences = Column(Text, nullable=True)  # JSON格式的用户偏好
    user_metadata = Column(Text, nullable=True)     # JSON格式的额外元数据
    
    # 索引
    __table_args__ = (
        Index('idx_users_email_verified', 'email_verified'),
        Index('idx_users_created_at', 'created_at'),
        Index('idx_users_last_login_at', 'last_login_at'),
        Index('idx_users_deleted_at', 'deleted_at'),
        Index('idx_users_role_status', 'role', 'status'),
    )
    
    def __repr__(self):
        return f"<UserModel(id={self.id}, username='{self.username}', email='{self.email}')>"


class UserSessionModel(BaseModel):
    """用户会话数据模型"""
    
    __tablename__ = "user_sessions"
    
    # 主键
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    session_id = Column(String(255), unique=True, nullable=False, index=True)
    
    # 关联用户
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # 会话信息
    access_token = Column(Text, nullable=False)
    refresh_token = Column(Text, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    
    # 客户端信息
    ip_address = Column(String(45), nullable=True)  # 支持IPv6
    user_agent = Column(Text, nullable=True)
    device_info = Column(Text, nullable=True)  # JSON格式
    
    # 状态
    is_active = Column(Boolean, nullable=False, default=True)
    last_activity_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # 索引
    __table_args__ = (
        Index('idx_user_sessions_user_id', 'user_id'),
        Index('idx_user_sessions_expires_at', 'expires_at'),
        Index('idx_user_sessions_is_active', 'is_active'),
        Index('idx_user_sessions_last_activity', 'last_activity_at'),
    )
    
    def __repr__(self):
        return f"<UserSessionModel(id={self.id}, user_id={self.user_id}, session_id='{self.session_id}')>"


class UserActivityLogModel(BaseModel):
    """用户活动日志数据模型"""
    
    __tablename__ = "user_activity_logs"
    
    # 主键
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # 关联用户
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # 活动信息
    action = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    details = Column(Text, nullable=True)  # JSON格式的详细信息
    
    # 上下文信息
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    session_id = Column(String(255), nullable=True)
    
    # 结果
    success = Column(Boolean, nullable=False, default=True)
    error_message = Column(Text, nullable=True)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # 索引
    __table_args__ = (
        Index('idx_user_activity_logs_user_id', 'user_id'),
        Index('idx_user_activity_logs_action', 'action'),
        Index('idx_user_activity_logs_created_at', 'created_at'),
        Index('idx_user_activity_logs_success', 'success'),
        Index('idx_user_activity_logs_user_action', 'user_id', 'action'),
    )
    
    def __repr__(self):
        return f"<UserActivityLogModel(id={self.id}, user_id={self.user_id}, action='{self.action}')>"


class UserPermissionModel(BaseModel):
    """用户权限数据模型"""
    
    __tablename__ = "user_permissions"
    
    # 主键
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # 关联用户
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # 权限信息
    permission = Column(String(100), nullable=False, index=True)
    resource = Column(String(100), nullable=True, index=True)
    action = Column(String(50), nullable=True, index=True)
    
    # 权限范围
    scope = Column(String(100), nullable=True)  # 权限范围（如：组织、项目等）
    constraints = Column(Text, nullable=True)   # JSON格式的权限约束
    
    # 权限状态
    is_active = Column(Boolean, nullable=False, default=True)
    granted_by = Column(UUID(as_uuid=True), nullable=True)  # 授权者
    granted_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)  # 权限过期时间
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # 索引
    __table_args__ = (
        Index('idx_user_permissions_user_id', 'user_id'),
        Index('idx_user_permissions_permission', 'permission'),
        Index('idx_user_permissions_resource_action', 'resource', 'action'),
        Index('idx_user_permissions_is_active', 'is_active'),
        Index('idx_user_permissions_expires_at', 'expires_at'),
        Index('idx_user_permissions_user_permission', 'user_id', 'permission'),
    )
    
    def __repr__(self):
        return f"<UserPermissionModel(id={self.id}, user_id={self.user_id}, permission='{self.permission}')>"
