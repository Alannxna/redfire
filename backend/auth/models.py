"""
认证系统数据模型
================

用户、角色、权限的数据库模型定义
"""

from datetime import datetime, timezone
from typing import List, Optional, Set
from sqlalchemy import Column, String, DateTime, Boolean, Text, ForeignKey, Table, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, Session
from sqlalchemy.dialects.postgresql import UUID
import uuid

from .enhanced_auth_middleware import UserRole, Permission


Base = declarative_base()

# 多对多关系表
user_roles = Table(
    'user_roles',
    Base.metadata,
    Column('user_id', String(36), ForeignKey('users.id'), primary_key=True),
    Column('role_id', String(36), ForeignKey('roles.id'), primary_key=True)
)

role_permissions = Table(
    'role_permissions',
    Base.metadata,
    Column('role_id', String(36), ForeignKey('roles.id'), primary_key=True),
    Column('permission_id', String(36), ForeignKey('permissions.id'), primary_key=True)
)


class User(Base):
    """用户模型"""
    __tablename__ = 'users'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    
    # 用户信息
    first_name = Column(String(50))
    last_name = Column(String(50))
    phone = Column(String(20))
    
    # 状态信息
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    is_locked = Column(Boolean, default=False, nullable=False)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    last_login = Column(DateTime(timezone=True))
    password_changed_at = Column(DateTime(timezone=True))
    
    # 安全信息
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime(timezone=True))
    
    # 关系
    roles = relationship("Role", secondary=user_roles, back_populates="users")
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, username={self.username})>"
    
    def get_permissions(self) -> Set[str]:
        """获取用户所有权限"""
        permissions = set()
        for role in self.roles:
            for permission in role.permissions:
                permissions.add(permission.name)
        return permissions
    
    def has_permission(self, permission_name: str) -> bool:
        """检查用户是否有指定权限"""
        return permission_name in self.get_permissions()
    
    def has_role(self, role_name: str) -> bool:
        """检查用户是否有指定角色"""
        return any(role.name == role_name for role in self.roles)
    
    def is_locked_out(self) -> bool:
        """检查用户是否被锁定"""
        if not self.is_locked:
            return False
        
        if self.locked_until and datetime.now(timezone.utc) < self.locked_until:
            return True
        
        return False


class Role(Base):
    """角色模型"""
    __tablename__ = 'roles'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(50), unique=True, nullable=False, index=True)
    display_name = Column(String(100), nullable=False)
    description = Column(Text)
    
    # 状态
    is_active = Column(Boolean, default=True, nullable=False)
    is_system = Column(Boolean, default=False, nullable=False)  # 系统角色不可删除
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # 关系
    users = relationship("User", secondary=user_roles, back_populates="roles")
    permissions = relationship("RolePermission", secondary=role_permissions, back_populates="roles")
    
    def __repr__(self):
        return f"<Role(id={self.id}, name={self.name})>"


class RolePermission(Base):
    """权限模型"""
    __tablename__ = 'permissions'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), unique=True, nullable=False, index=True)
    display_name = Column(String(100), nullable=False)
    description = Column(Text)
    category = Column(String(50))  # 权限分类，如 user, trading, strategy等
    
    # 状态
    is_active = Column(Boolean, default=True, nullable=False)
    is_system = Column(Boolean, default=False, nullable=False)  # 系统权限不可删除
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # 关系
    roles = relationship("Role", secondary=role_permissions, back_populates="permissions")
    
    def __repr__(self):
        return f"<Permission(id={self.id}, name={self.name})>"


class UserSession(Base):
    """用户会话模型"""
    __tablename__ = 'user_sessions'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey('users.id'), nullable=False)
    session_id = Column(String(255), unique=True, nullable=False, index=True)
    
    # 会话信息
    ip_address = Column(String(45))  # IPv6最长45位
    user_agent = Column(Text)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    last_activity = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    
    # 状态
    is_active = Column(Boolean, default=True, nullable=False)
    
    # 关系
    user = relationship("User", back_populates="sessions")
    
    def __repr__(self):
        return f"<UserSession(id={self.id}, user_id={self.user_id})>"
    
    def is_expired(self) -> bool:
        """检查会话是否过期"""
        return datetime.now(timezone.utc) > self.expires_at


class AuditLog(Base):
    """审计日志模型"""
    __tablename__ = 'audit_logs'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey('users.id'), nullable=True)  # 可能是匿名操作
    
    # 操作信息
    action = Column(String(100), nullable=False)  # login, logout, create_user, etc.
    resource = Column(String(100))  # 操作的资源类型
    resource_id = Column(String(36))  # 操作的资源ID
    
    # 请求信息
    ip_address = Column(String(45))
    user_agent = Column(Text)
    request_method = Column(String(10))
    request_path = Column(String(255))
    
    # 结果信息
    success = Column(Boolean, nullable=False)
    error_message = Column(Text)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    
    # 关系
    user = relationship("User", back_populates="audit_logs")
    
    def __repr__(self):
        return f"<AuditLog(id={self.id}, action={self.action})>"


class PasswordResetToken(Base):
    """密码重置令牌模型"""
    __tablename__ = 'password_reset_tokens'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey('users.id'), nullable=False)
    token = Column(String(255), unique=True, nullable=False, index=True)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used_at = Column(DateTime(timezone=True))
    
    # 状态
    is_used = Column(Boolean, default=False, nullable=False)
    
    def __repr__(self):
        return f"<PasswordResetToken(id={self.id}, user_id={self.user_id})>"
    
    def is_expired(self) -> bool:
        """检查令牌是否过期"""
        return datetime.now(timezone.utc) > self.expires_at


# 数据库操作类
class UserRepository:
    """用户仓储类"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, user_id: str) -> Optional[User]:
        """根据ID获取用户"""
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_by_username(self, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        return self.db.query(User).filter(User.username == username).first()
    
    def get_by_email(self, email: str) -> Optional[User]:
        """根据邮箱获取用户"""
        return self.db.query(User).filter(User.email == email).first()
    
    def create(self, user_data: dict) -> User:
        """创建用户"""
        user = User(**user_data)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def update(self, user_id: str, user_data: dict) -> Optional[User]:
        """更新用户"""
        user = self.get_by_id(user_id)
        if user:
            for key, value in user_data.items():
                setattr(user, key, value)
            user.updated_at = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(user)
        return user
    
    def delete(self, user_id: str) -> bool:
        """删除用户"""
        user = self.get_by_id(user_id)
        if user:
            self.db.delete(user)
            self.db.commit()
            return True
        return False
    
    def list_all(self, skip: int = 0, limit: int = 100) -> List[User]:
        """获取用户列表"""
        return self.db.query(User).offset(skip).limit(limit).all()


class RoleRepository:
    """角色仓储类"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, role_id: str) -> Optional[Role]:
        """根据ID获取角色"""
        return self.db.query(Role).filter(Role.id == role_id).first()
    
    def get_by_name(self, name: str) -> Optional[Role]:
        """根据名称获取角色"""
        return self.db.query(Role).filter(Role.name == name).first()
    
    def create(self, role_data: dict) -> Role:
        """创建角色"""
        role = Role(**role_data)
        self.db.add(role)
        self.db.commit()
        self.db.refresh(role)
        return role
    
    def list_all(self) -> List[Role]:
        """获取所有角色"""
        return self.db.query(Role).filter(Role.is_active == True).all()


class SessionRepository:
    """会话仓储类"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, session_data: dict) -> UserSession:
        """创建会话"""
        session = UserSession(**session_data)
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session
    
    def get_by_session_id(self, session_id: str) -> Optional[UserSession]:
        """根据会话ID获取会话"""
        return self.db.query(UserSession).filter(
            UserSession.session_id == session_id,
            UserSession.is_active == True
        ).first()
    
    def update_last_activity(self, session_id: str):
        """更新最后活动时间"""
        session = self.get_by_session_id(session_id)
        if session:
            session.last_activity = datetime.now(timezone.utc)
            self.db.commit()
    
    def revoke_session(self, session_id: str):
        """撤销会话"""
        session = self.get_by_session_id(session_id)
        if session:
            session.is_active = False
            self.db.commit()
    
    def revoke_user_sessions(self, user_id: str):
        """撤销用户所有会话"""
        self.db.query(UserSession).filter(
            UserSession.user_id == user_id,
            UserSession.is_active == True
        ).update({"is_active": False})
        self.db.commit()
    
    def cleanup_expired_sessions(self):
        """清理过期会话"""
        now = datetime.now(timezone.utc)
        self.db.query(UserSession).filter(
            UserSession.expires_at < now
        ).update({"is_active": False})
        self.db.commit()


def init_default_data(db: Session):
    """初始化默认数据"""
    # 创建默认权限
    default_permissions = [
        {"name": "user:read", "display_name": "查看用户", "category": "user"},
        {"name": "user:create", "display_name": "创建用户", "category": "user"},
        {"name": "user:update", "display_name": "更新用户", "category": "user"},
        {"name": "user:delete", "display_name": "删除用户", "category": "user"},
        
        {"name": "trading:read", "display_name": "查看交易", "category": "trading"},
        {"name": "trading:execute", "display_name": "执行交易", "category": "trading"},
        {"name": "trading:manage", "display_name": "管理交易", "category": "trading"},
        
        {"name": "strategy:read", "display_name": "查看策略", "category": "strategy"},
        {"name": "strategy:create", "display_name": "创建策略", "category": "strategy"},
        {"name": "strategy:update", "display_name": "更新策略", "category": "strategy"},
        {"name": "strategy:delete", "display_name": "删除策略", "category": "strategy"},
        {"name": "strategy:execute", "display_name": "执行策略", "category": "strategy"},
        
        {"name": "data:read", "display_name": "查看数据", "category": "data"},
        {"name": "data:write", "display_name": "写入数据", "category": "data"},
        {"name": "data:export", "display_name": "导出数据", "category": "data"},
        
        {"name": "system:read", "display_name": "查看系统", "category": "system"},
        {"name": "system:config", "display_name": "系统配置", "category": "system"},
        {"name": "system:admin", "display_name": "系统管理", "category": "system"},
        
        {"name": "monitor:read", "display_name": "查看监控", "category": "monitor"},
        {"name": "monitor:manage", "display_name": "管理监控", "category": "monitor"},
    ]
    
    for perm_data in default_permissions:
        existing = db.query(RolePermission).filter(RolePermission.name == perm_data["name"]).first()
        if not existing:
            permission = RolePermission(**perm_data, is_system=True)
            db.add(permission)
    
    # 创建默认角色
    default_roles = [
        {
            "name": "super_admin",
            "display_name": "超级管理员",
            "description": "拥有所有权限的超级管理员",
            "is_system": True
        },
        {
            "name": "admin",
            "display_name": "管理员", 
            "description": "系统管理员",
            "is_system": True
        },
        {
            "name": "trader",
            "display_name": "交易员",
            "description": "可以执行交易和管理策略",
            "is_system": True
        },
        {
            "name": "analyst",
            "display_name": "分析师",
            "description": "可以分析数据和创建策略",
            "is_system": True
        },
        {
            "name": "viewer",
            "display_name": "查看者",
            "description": "只能查看数据",
            "is_system": True
        }
    ]
    
    for role_data in default_roles:
        existing = db.query(Role).filter(Role.name == role_data["name"]).first()
        if not existing:
            role = Role(**role_data)
            db.add(role)
    
    db.commit()
    
    # 分配权限给角色
    role_permission_mapping = {
        "super_admin": [perm["name"] for perm in default_permissions],
        "admin": [
            "user:read", "user:create", "user:update", "user:delete",
            "trading:read", "trading:execute", "trading:manage",
            "strategy:read", "strategy:create", "strategy:update", "strategy:delete", "strategy:execute",
            "data:read", "data:write", "data:export",
            "system:read", "system:config",
            "monitor:read", "monitor:manage"
        ],
        "trader": [
            "user:read",
            "trading:read", "trading:execute",
            "strategy:read", "strategy:create", "strategy:update", "strategy:execute",
            "data:read", "data:write",
            "monitor:read"
        ],
        "analyst": [
            "user:read",
            "trading:read",
            "strategy:read", "strategy:create", "strategy:update",
            "data:read", "data:write", "data:export",
            "monitor:read"
        ],
        "viewer": [
            "user:read",
            "trading:read",
            "strategy:read",
            "data:read",
            "monitor:read"
        ]
    }
    
    for role_name, permission_names in role_permission_mapping.items():
        role = db.query(Role).filter(Role.name == role_name).first()
        if role:
            for perm_name in permission_names:
                permission = db.query(RolePermission).filter(RolePermission.name == perm_name).first()
                if permission and permission not in role.permissions:
                    role.permissions.append(permission)
    
    db.commit()
