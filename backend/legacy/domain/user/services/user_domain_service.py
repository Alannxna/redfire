"""
用户领域服务

用户领域的核心业务逻辑实现，包含用户注册、认证、权限管理等
"""

import hashlib
import secrets
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from ....core.base.domain_service import BaseDomainService, DomainServiceConfig
from ....core.common.exceptions import DomainException
from ....core.common.enums.user_roles import UserRole
from ..entities.user import User, UserStatus
from ..value_objects.user_id import UserId
from ..value_objects.username import Username
from ...shared.value_objects.email import Email
from ...shared.value_objects.phone import Phone
from ..repositories.user_repository import IUserRepository


class UserDomainServiceConfig(DomainServiceConfig):
    """用户领域服务配置"""
    
    def __init__(self):
        super().__init__(
            service_name="user_domain_service",
            domain_name="user",
            description="用户领域服务 - 负责用户注册、认证、权限管理等核心业务逻辑",
            version="1.0.0"
        )


class UserDomainService(BaseDomainService):
    """用户领域服务
    
    负责用户相关的核心业务逻辑：
    - 用户注册和验证
    - 密码管理和安全
    - 用户认证和授权
    - 账户状态管理
    - 权限检查
    """
    
    def __init__(self, config: UserDomainServiceConfig, user_repository: IUserRepository):
        super().__init__(config)
        self.user_repository = user_repository
        
        # 密码策略配置
        self.min_password_length = 8
        self.require_special_chars = True
        self.require_uppercase = True
        self.require_lowercase = True
        self.require_numbers = True
        
        # 账户锁定策略
        self.max_failed_attempts = 5
        self.lockout_duration_minutes = 30
    
    async def create_user(self, username: str, email: str, password: str,
                         role: UserRole = UserRole.TRADER,
                         full_name: Optional[str] = None,
                         phone: Optional[str] = None) -> User:
        """创建新用户
        
        Args:
            username: 用户名
            email: 邮箱地址
            password: 明文密码
            role: 用户角色
            full_name: 全名
            phone: 手机号
            
        Returns:
            创建的用户实体
            
        Raises:
            DomainException: 当用户名或邮箱已存在时
        """
        # 验证用户名和邮箱唯一性
        await self._ensure_username_unique(username)
        await self._ensure_email_unique(email)
        
        # 验证密码强度
        self._validate_password_strength(password)
        
        # 哈希密码
        hashed_password = self._hash_password(password)
        
        # 创建用户实体
        user = User.create(
            username=username,
            email=email,
            hashed_password=hashed_password,
            role=role,
            full_name=full_name,
            phone=phone
        )
        
        self.logger.info(f"创建新用户: {username} ({email})")
        return user
    
    async def authenticate_user(self, username_or_email: str, password: str) -> Optional[User]:
        """用户认证
        
        Args:
            username_or_email: 用户名或邮箱
            password: 明文密码
            
        Returns:
            认证成功的用户实体，失败返回None
        """
        # 查找用户
        user = await self._find_user_by_login_identifier(username_or_email)
        if not user:
            self.logger.warning(f"用户不存在: {username_or_email}")
            return None
        
        # 检查账户状态
        if not user.is_active:
            self.logger.warning(f"用户账户不活跃: {username_or_email}")
            return None
        
        # 检查账户是否被锁定
        if user.is_account_locked:
            self.logger.warning(f"用户账户被锁定: {username_or_email}")
            return None
        
        # 验证密码
        if self._verify_password(password, user.hashed_password):
            # 认证成功
            user.record_successful_login()
            self.logger.info(f"用户认证成功: {username_or_email}")
            return user
        else:
            # 认证失败
            user.record_failed_login()
            self.logger.warning(f"用户认证失败: {username_or_email}")
            return None
    
    async def change_user_password(self, user_id: UserId, current_password: str, new_password: str) -> bool:
        """修改用户密码
        
        Args:
            user_id: 用户ID
            current_password: 当前密码
            new_password: 新密码
            
        Returns:
            是否修改成功
            
        Raises:
            DomainException: 当前密码错误或新密码不符合要求时
        """
        user = await self.user_repository.find_by_id(user_id)
        if not user:
            raise DomainException(f"用户不存在: {user_id.value}")
        
        # 验证当前密码
        if not self._verify_password(current_password, user.hashed_password):
            raise DomainException("当前密码错误")
        
        # 验证新密码强度
        self._validate_password_strength(new_password)
        
        # 确保新密码与当前密码不同
        if self._verify_password(new_password, user.hashed_password):
            raise DomainException("新密码不能与当前密码相同")
        
        # 更新密码
        hashed_new_password = self._hash_password(new_password)
        user.change_password(hashed_new_password)
        
        self.logger.info(f"用户密码修改成功: {user.username.value}")
        return True
    
    async def reset_user_password(self, user_id: UserId, new_password: str) -> str:
        """重置用户密码（管理员操作）
        
        Args:
            user_id: 用户ID
            new_password: 新密码（可选，不提供则生成随机密码）
            
        Returns:
            新密码（明文）
            
        Raises:
            DomainException: 用户不存在时
        """
        user = await self.user_repository.find_by_id(user_id)
        if not user:
            raise DomainException(f"用户不存在: {user_id.value}")
        
        # 如果没有提供新密码，生成随机密码
        if not new_password:
            new_password = self._generate_random_password()
        else:
            self._validate_password_strength(new_password)
        
        # 更新密码
        hashed_new_password = self._hash_password(new_password)
        user.change_password(hashed_new_password)
        
        self.logger.info(f"管理员重置用户密码: {user.username.value}")
        return new_password
    
    async def change_user_role(self, user_id: UserId, new_role: UserRole, operator_role: UserRole) -> bool:
        """修改用户角色
        
        Args:
            user_id: 用户ID
            new_role: 新角色
            operator_role: 操作者角色
            
        Returns:
            是否修改成功
            
        Raises:
            DomainException: 权限不足或用户不存在时
        """
        # 权限检查：只有管理员可以修改角色
        if operator_role != UserRole.ADMIN:
            raise DomainException("权限不足：只有管理员可以修改用户角色")
        
        user = await self.user_repository.find_by_id(user_id)
        if not user:
            raise DomainException(f"用户不存在: {user_id.value}")
        
        user.change_role(new_role)
        self.logger.info(f"用户角色修改: {user.username.value} -> {new_role.value}")
        return True
    
    async def suspend_user(self, user_id: UserId, reason: str, operator_role: UserRole) -> bool:
        """暂停用户
        
        Args:
            user_id: 用户ID
            reason: 暂停原因
            operator_role: 操作者角色
            
        Returns:
            是否暂停成功
            
        Raises:
            DomainException: 权限不足或用户不存在时
        """
        # 权限检查
        if operator_role not in [UserRole.ADMIN, UserRole.MODERATOR]:
            raise DomainException("权限不足：只有管理员或版主可以暂停用户")
        
        user = await self.user_repository.find_by_id(user_id)
        if not user:
            raise DomainException(f"用户不存在: {user_id.value}")
        
        user.suspend(reason)
        self.logger.info(f"用户暂停: {user.username.value}, 原因: {reason}")
        return True
    
    async def activate_user(self, user_id: UserId, operator_role: UserRole) -> bool:
        """激活用户
        
        Args:
            user_id: 用户ID
            operator_role: 操作者角色
            
        Returns:
            是否激活成功
            
        Raises:
            DomainException: 权限不足或用户不存在时
        """
        # 权限检查
        if operator_role not in [UserRole.ADMIN, UserRole.MODERATOR]:
            raise DomainException("权限不足：只有管理员或版主可以激活用户")
        
        user = await self.user_repository.find_by_id(user_id)
        if not user:
            raise DomainException(f"用户不存在: {user_id.value}")
        
        user.activate()
        self.logger.info(f"用户激活: {user.username.value}")
        return True
            
    def check_permission(self, user: User, permission: str) -> bool:
        """检查用户权限
        
        Args:
            user: 用户实体
            permission: 权限名称
            
        Returns:
            是否有权限
        """
        # 检查用户状态
        if not user.is_active:
            return False
    
        # 检查角色权限
        return user.has_permission(permission)
    
    def _validate_password_strength(self, password: str) -> None:
        """验证密码强度
        
        Args:
            password: 明文密码
            
        Raises:
            DomainException: 密码不符合要求时
        """
        if len(password) < self.min_password_length:
            raise DomainException(f"密码长度不能少于{self.min_password_length}个字符")
        
        if self.require_uppercase and not any(c.isupper() for c in password):
            raise DomainException("密码必须包含至少一个大写字母")
        
        if self.require_lowercase and not any(c.islower() for c in password):
            raise DomainException("密码必须包含至少一个小写字母")
        
        if self.require_numbers and not any(c.isdigit() for c in password):
            raise DomainException("密码必须包含至少一个数字")
        
        if self.require_special_chars and not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            raise DomainException("密码必须包含至少一个特殊字符")
    
    def _hash_password(self, password: str) -> str:
        """哈希密码
        
        Args:
            password: 明文密码
            
        Returns:
            哈希后的密码
        """
        salt = secrets.token_hex(16)
        hashed = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
        return f"{salt}:{hashed.hex()}"
    
    def _verify_password(self, password: str, hashed_password: str) -> bool:
        """验证密码
        
        Args:
            password: 明文密码
            hashed_password: 哈希密码
            
        Returns:
            是否匹配
        """
        try:
            salt, hash_hex = hashed_password.split(':')
            hashed = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
            return hashed.hex() == hash_hex
        except ValueError:
            return False
    
    def _generate_random_password(self, length: int = 12) -> str:
        """生成随机密码
        
        Args:
            length: 密码长度
            
        Returns:
            随机密码
        """
        import string
        characters = string.ascii_letters + string.digits + "!@#$%^&*"
        return ''.join(secrets.choice(characters) for _ in range(length))
    
    async def _find_user_by_login_identifier(self, identifier: str) -> Optional[User]:
        """根据登录标识符查找用户
        
        Args:
            identifier: 用户名或邮箱
            
        Returns:
            用户实体或None
        """
        # 尝试作为邮箱查找
        if '@' in identifier:
            try:
                email = Email(identifier)
                return await self.user_repository.find_by_email(email)
            except DomainException:
                pass
        
        # 尝试作为用户名查找
        try:
            username = Username(identifier)
            return await self.user_repository.find_by_username(username)
        except DomainException:
            pass
        
        return None
    
    async def _ensure_username_unique(self, username: str) -> None:
        """确保用户名唯一
        
        Args:
            username: 用户名
            
        Raises:
            DomainException: 用户名已存在时
        """
        username_vo = Username(username)
        if await self.user_repository.username_exists(username_vo):
            raise DomainException(f"用户名已存在: {username}")
    
    async def _ensure_email_unique(self, email: str) -> None:
        """确保邮箱唯一
        
        Args:
            email: 邮箱地址
            
        Raises:
            DomainException: 邮箱已存在时
        """
        email_vo = Email(email)
        if await self.user_repository.email_exists(email_vo):
            raise DomainException(f"邮箱已存在: {email}")


# 服务实例获取函数
_service_instance: Optional[UserDomainService] = None

def get_user_domain_service(user_repository: IUserRepository) -> UserDomainService:
    """获取用户领域服务实例"""
    global _service_instance
    if _service_instance is None:
        config = UserDomainServiceConfig()
        _service_instance = UserDomainService(config, user_repository)
    return _service_instance
