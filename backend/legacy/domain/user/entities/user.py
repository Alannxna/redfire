"""
用户实体

用户领域的核心实体，包含用户的基本信息和行为
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from enum import Enum

from ...shared.value_objects.email import Email
from ...shared.value_objects.phone import Phone
from ..value_objects.user_id import UserId
from ..value_objects.username import Username
from ...shared.events.domain_event import DomainEvent
from ....core.base.entity_base import BaseEntity
from ....core.common.enums.user_roles import UserRole, UserStatus


@dataclass
class UserCreatedEvent(DomainEvent):
    """用户创建事件"""
    event_type: str = "user_created"
    user_id: str = ""
    username: str = ""
    email: str = ""


@dataclass
class UserUpdatedEvent(DomainEvent):
    """用户更新事件"""
    event_type: str = "user_updated"
    user_id: str = ""
    changed_fields: Dict[str, Any] = None


@dataclass
class UserStatusChangedEvent(DomainEvent):
    """用户状态变更事件"""
    event_type: str = "user_status_changed"
    user_id: str = ""
    old_status: str = ""
    new_status: str = ""
    reason: Optional[str] = None


class User(BaseEntity):
    """用户实体
    
    用户领域的聚合根，管理用户的基本信息、状态和行为
    """
    
    def __init__(self, user_id: UserId, username: Username, email: Email,
                 hashed_password: str, 
                 full_name: Optional[str] = None,
                 role: UserRole = UserRole.TRADER,
                 status: UserStatus = UserStatus.ACTIVE,
                 phone: Optional[Phone] = None,
                 avatar_url: Optional[str] = None,
                 created_at: Optional[datetime] = None,
                 updated_at: Optional[datetime] = None,
                 last_login_at: Optional[datetime] = None):
        
        super().__init__(user_id.value)
        
        # 值对象
        self._user_id = user_id
        self._username = username
        self._email = email
        self._phone = phone
        
        # 基本属性
        self._hashed_password = hashed_password
        self._role = role
        self._status = status
        self._full_name = full_name
        self._avatar_url = avatar_url
        
        # 时间戳
        self._created_at = created_at or datetime.now()
        self._updated_at = updated_at or datetime.now()
        self._last_login_at = last_login_at
        
        # 业务属性
        self._login_attempts = 0
        self._max_login_attempts = 5
        self._account_locked_until: Optional[datetime] = None
        
        # 权限相关
        self._permissions: List[str] = []
        self._settings: Dict[str, Any] = {}
    
    @property
    def user_id(self) -> UserId:
        """用户ID"""
        return self._user_id
    
    @property
    def username(self) -> Username:
        """用户名"""
        return self._username
    
    @property
    def email(self) -> Email:
        """邮箱"""
        return self._email
    
    @property
    def phone(self) -> Optional[Phone]:
        """手机号"""
        return self._phone
    
    @property
    def hashed_password(self) -> str:
        """哈希密码"""
        return self._hashed_password
    
    @property
    def role(self) -> UserRole:
        """用户角色"""
        return self._role
    
    @property
    def status(self) -> UserStatus:
        """用户状态"""
        return self._status
    
    @property
    def full_name(self) -> Optional[str]:
        """全名"""
        return self._full_name
    
    @property
    def avatar_url(self) -> Optional[str]:
        """头像URL"""
        return self._avatar_url
    
    @property
    def created_at(self) -> datetime:
        """创建时间"""
        return self._created_at
    
    @property
    def updated_at(self) -> datetime:
        """更新时间"""
        return self._updated_at
    
    @property
    def last_login_at(self) -> Optional[datetime]:
        """最后登录时间"""
        return self._last_login_at
    
    @property
    def login_attempts(self) -> int:
        """登录尝试次数"""
        return self._login_attempts
    
    @property
    def is_account_locked(self) -> bool:
        """账户是否被锁定"""
        if self._account_locked_until is None:
            return False
        return datetime.now() < self._account_locked_until
    
    @property
    def is_active(self) -> bool:
        """用户是否活跃"""
        return self._status == UserStatus.ACTIVE and not self.is_account_locked
    
    @property
    def permissions(self) -> List[str]:
        """用户权限列表"""
        return self._permissions.copy()
    
    @property
    def settings(self) -> Dict[str, Any]:
        """用户设置"""
        return self._settings.copy()
    
    @classmethod
    def create(cls, username: str, email: str, hashed_password: str,
               role: UserRole = UserRole.TRADER, full_name: Optional[str] = None,
               phone: Optional[str] = None) -> 'User':
        """创建新用户
        
        Args:
            username: 用户名
            email: 邮箱地址
            hashed_password: 哈希后的密码
            role: 用户角色
            full_name: 全名
            phone: 手机号
            
        Returns:
            新创建的用户实体
        """
        # 创建值对象
        user_id = UserId.generate()
        username_vo = Username(username)
        email_vo = Email(email)
        phone_vo = Phone(phone) if phone else None
        
        # 创建用户实体
        user = cls(
            user_id=user_id,
            username=username_vo,
            email=email_vo,
            hashed_password=hashed_password,
            role=role,
            phone=phone_vo,
            full_name=full_name
        )
        
        # 添加领域事件
        user.add_domain_event(UserCreatedEvent(
            user_id=user_id.value,
            username=username,
            email=email,
            occurred_at=datetime.now()
        ))
        
        return user
    
    def update_profile(self, full_name: Optional[str] = None,
                      phone: Optional[str] = None,
                      avatar_url: Optional[str] = None) -> None:
        """更新用户资料
        
        Args:
            full_name: 全名
            phone: 手机号
            avatar_url: 头像URL
        """
        changed_fields = {}
        
        if full_name is not None and full_name != self._full_name:
            changed_fields['full_name'] = {'old': self._full_name, 'new': full_name}
            self._full_name = full_name
        
        if phone is not None:
            phone_vo = Phone(phone)
            if phone_vo != self._phone:
                changed_fields['phone'] = {
                    'old': self._phone.value if self._phone else None,
                    'new': phone
                }
                self._phone = phone_vo
        
        if avatar_url is not None and avatar_url != self._avatar_url:
            changed_fields['avatar_url'] = {'old': self._avatar_url, 'new': avatar_url}
            self._avatar_url = avatar_url
        
        if changed_fields:
            self._updated_at = datetime.now()
            self.mark_as_modified()
            
            # 添加领域事件
            self.add_domain_event(UserUpdatedEvent(
                user_id=self._user_id.value,
                changed_fields=changed_fields,
                occurred_at=datetime.now()
            ))
    
    def change_email(self, new_email: str) -> None:
        """更改邮箱地址
        
        Args:
            new_email: 新邮箱地址
        """
        new_email_vo = Email(new_email)
        if new_email_vo != self._email:
            old_email = self._email.value
            self._email = new_email_vo
            self._updated_at = datetime.now()
            self.mark_as_modified()
            
            # 添加领域事件
            self.add_domain_event(UserUpdatedEvent(
                user_id=self._user_id.value,
                changed_fields={'email': {'old': old_email, 'new': new_email}},
                occurred_at=datetime.now()
            ))
    
    def change_password(self, new_hashed_password: str) -> None:
        """更改密码
        
        Args:
            new_hashed_password: 新的哈希密码
        """
        self._hashed_password = new_hashed_password
        self._updated_at = datetime.now()
        self.mark_as_modified()
        
        # 重置登录尝试次数
        self._login_attempts = 0
        self._account_locked_until = None
        
        # 添加领域事件
        self.add_domain_event(UserUpdatedEvent(
            user_id=self._user_id.value,
            changed_fields={'password': {'changed': True}},
            occurred_at=datetime.now()
        ))
    
    def change_role(self, new_role: UserRole) -> None:
        """更改用户角色
        
        Args:
            new_role: 新角色
        """
        if new_role != self._role:
            old_role = self._role
            self._role = new_role
            self._updated_at = datetime.now()
            self.mark_as_modified()
            
            # 添加领域事件
            self.add_domain_event(UserUpdatedEvent(
                user_id=self._user_id.value,
                changed_fields={'role': {'old': old_role.value, 'new': new_role.value}},
                occurred_at=datetime.now()
            ))
    
    def change_status(self, new_status: UserStatus, reason: Optional[str] = None) -> None:
        """更改用户状态
        
        Args:
            new_status: 新状态
            reason: 状态变更原因
        """
        if new_status != self._status:
            old_status = self._status
            self._status = new_status
            self._updated_at = datetime.now()
            self.mark_as_modified()
            
            # 添加领域事件
            self.add_domain_event(UserStatusChangedEvent(
                user_id=self._user_id.value,
                old_status=old_status.value,
                new_status=new_status.value,
                reason=reason,
                occurred_at=datetime.now()
            ))
    
    def activate(self) -> None:
        """激活用户"""
        self.change_status(UserStatus.ACTIVE, "用户激活")
    
    def deactivate(self, reason: Optional[str] = None) -> None:
        """停用用户"""
        self.change_status(UserStatus.INACTIVE, reason or "用户停用")
    
    def suspend(self, reason: Optional[str] = None) -> None:
        """暂停用户"""
        self.change_status(UserStatus.SUSPENDED, reason or "用户暂停")
    
    def soft_delete(self, reason: Optional[str] = None) -> None:
        """软删除用户"""
        self.change_status(UserStatus.DELETED, reason or "用户删除")
    
    def record_successful_login(self) -> None:
        """记录成功登录"""
        self._last_login_at = datetime.now()
        self._login_attempts = 0
        self._account_locked_until = None
        self.mark_as_modified()
    
    def record_failed_login(self) -> None:
        """记录失败登录"""
        self._login_attempts += 1
        
        # 如果超过最大尝试次数，锁定账户
        if self._login_attempts >= self._max_login_attempts:
            # 锁定账户30分钟
            from datetime import timedelta
            self._account_locked_until = datetime.now() + timedelta(minutes=30)
        
        self.mark_as_modified()
    
    def unlock_account(self) -> None:
        """解锁账户"""
        self._login_attempts = 0
        self._account_locked_until = None
        self.mark_as_modified()
    
    def has_permission(self, permission: str) -> bool:
        """检查用户是否有指定权限
        
        Args:
            permission: 权限名称
            
        Returns:
            是否有权限
        """
        # 管理员拥有所有权限
        if self._role == UserRole.ADMIN:
            return True
        
        return permission in self._permissions
    
    def grant_permission(self, permission: str) -> None:
        """授予权限
        
        Args:
            permission: 权限名称
        """
        if permission not in self._permissions:
            self._permissions.append(permission)
            self.mark_as_modified()
    
    def revoke_permission(self, permission: str) -> None:
        """撤销权限
        
        Args:
            permission: 权限名称
        """
        if permission in self._permissions:
            self._permissions.remove(permission)
            self.mark_as_modified()
    
    def update_setting(self, key: str, value: Any) -> None:
        """更新用户设置
        
        Args:
            key: 设置键
            value: 设置值
        """
        self._settings[key] = value
        self.mark_as_modified()
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """获取用户设置
        
        Args:
            key: 设置键
            default: 默认值
            
        Returns:
            设置值
        """
        return self._settings.get(key, default)
    
    def remove_setting(self, key: str) -> None:
        """删除用户设置
        
        Args:
            key: 设置键
        """
        if key in self._settings:
            del self._settings[key]
            self.mark_as_modified()
    
    def __eq__(self, other) -> bool:
        """相等性比较"""
        if not isinstance(other, User):
            return False
        return self._user_id == other._user_id
    
    def __hash__(self) -> int:
        """哈希值"""
        return hash(self._user_id)
    
    def __str__(self) -> str:
        """字符串表示"""
        return f"User(id={self._user_id.value}, username={self._username.value}, email={self._email.value})"
    
    def validate(self) -> bool:
        """验证用户实体的业务规则"""
        try:
            # 验证值对象
            if not self._user_id.validate():
                return False
            if not self._username.validate():
                return False
            if not self._email.validate():
                return False
            if self._phone and not self._phone.validate():
                return False
            
            # 验证基本属性
            if not self._hashed_password:
                return False
            
            # 验证角色
            if not isinstance(self._role, UserRole):
                return False
            
            # 验证状态
            if not isinstance(self._status, UserStatus):
                return False
            
            return True
        except Exception:
            return False
    
    def check_invariants(self) -> bool:
        """检查用户聚合不变式"""
        try:
            # 基本验证
            if not self.validate():
                return False
            
            # 业务不变式检查
            # 1. 激活用户必须有有效的邮箱
            if self.is_active and not self._email.validate():
                return False
            
            # 2. 管理员用户不能被删除
            if self._role == UserRole.ADMIN and self._status == UserStatus.DELETED:
                return False
            
            # 3. 用户名和邮箱必须唯一（这里只做基本检查，实际唯一性由仓储层保证）
            if not self._username.value or not self._email.value:
                return False
            
            return True
        except Exception:
            return False
