"""
用户相关命令定义
实现用户业务操作的命令模式

优化特性:
- 增强类型安全性
- 统一验证逻辑
- 提供完整的文档字符串
- 支持自定义验证规则
"""

# 标准库导入
from __future__ import annotations
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, ClassVar, Dict, Any, Pattern

# 核心层导入
from ...core.common.enums.user_roles import UserRole

# 领域层导入
from ...domain.shared.value_objects.email import Email

# 应用层内部导入
from .base_command import BaseCommand


@dataclass
class CreateUserCommand(BaseCommand):
    """
    创建用户命令
    
    用于创建新用户账户，包含完整的用户信息验证和业务规则检查。
    
    Attributes:
        username: 用户名，必须符合用户名规范
        email: 邮箱地址，必须为有效邮箱格式
        password: 密码，必须符合密码强度要求
        full_name: 用户全名，可选字段
        role: 用户角色，默认为交易员角色
    
    Raises:
        ValueError: 当必填字段为空或格式不正确时
    """
    
    # 验证规则
    USERNAME_PATTERN: ClassVar[Pattern[str]] = re.compile(r'^[a-zA-Z0-9_]{3,30}$')
    PASSWORD_MIN_LENGTH: ClassVar[int] = 8
    
    # 必需字段
    username: str = None
    email: str = None
    password: str = None
    # 可选字段
    full_name: Optional[str] = None
    role: UserRole = UserRole.TRADER
    
    def __post_init__(self) -> None:
        """初始化后验证"""
        super().__post_init__()
        self._validate_required_fields()
        self._validate_username()
        self._validate_email()
        self._validate_password()
        self._validate_full_name()
    
    def _validate_required_fields(self) -> None:
        """验证必填字段"""
        if not self.username:
            raise ValueError("用户名不能为空")
        if not self.email:
            raise ValueError("邮箱不能为空")
        if not self.password:
            raise ValueError("密码不能为空")
    
    def _validate_username(self) -> None:
        """验证用户名格式"""
        if not self.USERNAME_PATTERN.match(self.username):
            raise ValueError("用户名必须为3-30位字母、数字或下划线")
    
    def _validate_email(self) -> None:
        """验证邮箱格式"""
        try:
            Email(self.email)  # 使用值对象验证
        except Exception:
            raise ValueError("邮箱格式不正确")
    
    def _validate_password(self) -> None:
        """验证密码强度"""
        if len(self.password) < self.PASSWORD_MIN_LENGTH:
            raise ValueError(f"密码长度不能少于{self.PASSWORD_MIN_LENGTH}位")
        
        # 检查密码复杂度
        has_upper = any(c.isupper() for c in self.password)
        has_lower = any(c.islower() for c in self.password)
        has_digit = any(c.isdigit() for c in self.password)
        
        if not (has_upper and has_lower and has_digit):
            raise ValueError("密码必须包含大写字母、小写字母和数字")
    
    def _validate_full_name(self) -> None:
        """验证全名"""
        if self.full_name and len(self.full_name.strip()) > 100:
            raise ValueError("用户全名长度不能超过100个字符")


@dataclass
class UpdateUserProfileCommand(BaseCommand):
    """更新用户资料命令"""
    user_id: str = None
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    
    def __post_init__(self):
        super().__post_init__()
        if not self.user_id:
            raise ValueError("用户ID不能为空")


@dataclass
class ChangeUserPasswordCommand(BaseCommand):
    """
    修改用户密码命令
    
    用于安全地更改用户密码，包含旧密码验证和新密码强度检查。
    支持管理员重置密码功能。
    
    Attributes:
        user_id: 用户ID，必填
        current_password: 当前密码，用于身份验证（管理员重置时可为空）
        new_password: 新密码，必须符合密码强度要求
        is_admin_reset: 是否为管理员重置密码，默认False
    
    Raises:
        ValueError: 当字段验证失败时
    """
    
    user_id: str = None
    current_password: Optional[str] = None
    new_password: str = None
    is_admin_reset: bool = False
    
    def __post_init__(self) -> None:
        """初始化后验证"""
        super().__post_init__()
        self._validate_required_fields()
        self._validate_password_change()
    
    def _validate_required_fields(self) -> None:
        """验证必填字段"""
        if not self.user_id:
            raise ValueError("用户ID不能为空")
        if not self.is_admin_reset and not self.current_password:
            raise ValueError("当前密码不能为空")
        if not self.new_password:
            raise ValueError("新密码不能为空")
    
    def _validate_password_change(self) -> None:
        """验证密码更改规则"""
        # 如果不是管理员重置，检查新旧密码不能相同
        if not self.is_admin_reset and self.current_password == self.new_password:
            raise ValueError("新密码不能与当前密码相同")
        
        # 验证新密码强度（复用CreateUserCommand的逻辑）
        if len(self.new_password) < CreateUserCommand.PASSWORD_MIN_LENGTH:
            raise ValueError(f"新密码长度不能少于{CreateUserCommand.PASSWORD_MIN_LENGTH}位")
        
        has_upper = any(c.isupper() for c in self.new_password)
        has_lower = any(c.islower() for c in self.new_password)
        has_digit = any(c.isdigit() for c in self.new_password)
        
        if not (has_upper and has_lower and has_digit):
            raise ValueError("新密码必须包含大写字母、小写字母和数字")


@dataclass
class ChangeUserRoleCommand(BaseCommand):
    """修改用户角色命令"""
    user_id: str = None
    new_role: UserRole = None
    operator_id: str = None  # 操作者ID
    
    def __post_init__(self):
        super().__post_init__()
        if not self.user_id:
            raise ValueError("用户ID不能为空")
        if not self.new_role:
            raise ValueError("新角色不能为空")
        if not self.operator_id:
            raise ValueError("操作者ID不能为空")


@dataclass
class ActivateUserCommand(BaseCommand):
    """激活用户命令"""
    user_id: str = None
    operator_id: str = None
    
    def __post_init__(self):
        super().__post_init__()
        if not self.user_id:
            raise ValueError("用户ID不能为空")
        if not self.operator_id:
            raise ValueError("操作者ID不能为空")


@dataclass
class DeactivateUserCommand(BaseCommand):
    """
    停用用户命令
    
    用于临时停用用户账户，保留数据但禁止登录和操作。
    
    Attributes:
        user_id: 用户ID，必填
        operator_id: 操作者ID，必填
        reason: 停用原因，必填（用于审计和通知）
        duration_days: 停用天数，可选（默认永久停用）
        notify_user: 是否通知用户，默认True
    
    Raises:
        ValueError: 当字段验证失败时
    """
    
    user_id: str = None
    operator_id: str = None
    reason: str = None
    duration_days: Optional[int] = None
    notify_user: bool = True
    
    def __post_init__(self) -> None:
        """初始化后验证"""
        super().__post_init__()
        self._validate_required_fields()
        self._validate_optional_fields()
    
    def _validate_required_fields(self) -> None:
        """验证必填字段"""
        if not self.user_id:
            raise ValueError("用户ID不能为空")
        if not self.operator_id:
            raise ValueError("操作者ID不能为空")
        if not self.reason:
            raise ValueError("停用原因不能为空")
    
    def _validate_optional_fields(self) -> None:
        """验证可选字段"""
        self.reason = self.reason.strip()
        if len(self.reason) > 200:
            raise ValueError("停用原因长度不能超过200个字符")
        
        if self.duration_days is not None:
            if self.duration_days <= 0 or self.duration_days > 365:
                raise ValueError("停用天数必须在1-365天之间")


@dataclass
class DeleteUserCommand(BaseCommand):
    """
    删除用户命令
    
    用于安全地删除用户账户，包含必要的安全检查和确认步骤。
    
    Attributes:
        user_id: 用户ID，必填
        operator_id: 操作者ID，必填
        confirmation_token: 确认令牌，必填（防止误删除）
        reason: 删除原因，必填（用于审计）
        hard_delete: 是否硬删除，默认False（管理员特权）
        backup_data: 是否备份数据，默认True
    
    Raises:
        ValueError: 当字段验证失败时
    """
    
    user_id: str = None
    operator_id: str = None
    confirmation_token: str = None
    reason: str = None
    hard_delete: bool = False
    backup_data: bool = True
    
    def __post_init__(self) -> None:
        """初始化后验证"""
        super().__post_init__()
        self._validate_required_fields()
        self._validate_optional_fields()
    
    def _validate_required_fields(self) -> None:
        """验证必填字段"""
        if not self.user_id:
            raise ValueError("用户ID不能为空")
        if not self.operator_id:
            raise ValueError("操作者ID不能为空")
        if not self.confirmation_token:
            raise ValueError("确认令牌不能为空")
        if not self.reason:
            raise ValueError("删除原因不能为空")
    
    def _validate_optional_fields(self) -> None:
        """验证可选字段"""
        self.reason = self.reason.strip()
        if len(self.reason) > 200:
            raise ValueError("删除原因长度不能超过200个字符")


@dataclass
class LoginUserCommand(BaseCommand):
    """
    用户登录命令
    
    支持使用用户名或邮箱进行登录，包含安全验证和会话管理选项。
    
    Attributes:
        username_or_email: 用户名或邮箱地址
        password: 用户密码
        remember_me: 是否记住登录状态
        client_ip: 客户端IP地址（可选，用于安全审计）
        user_agent: 用户代理字符串（可选，用于安全审计）
    
    Raises:
        ValueError: 当必填字段为空时
    """
    
    username_or_email: str = None
    password: str = None
    remember_me: bool = False
    client_ip: Optional[str] = None
    user_agent: Optional[str] = None
    
    def __post_init__(self) -> None:
        """初始化后验证"""
        super().__post_init__()
        self._validate_required_fields()
        self._validate_login_identifier()
    
    def _validate_required_fields(self) -> None:
        """验证必填字段"""
        if not self.username_or_email:
            raise ValueError("用户名或邮箱不能为空")
        if not self.password:
            raise ValueError("密码不能为空")
    
    def _validate_login_identifier(self) -> None:
        """验证登录标识符"""
        # 清理输入
        self.username_or_email = self.username_or_email.strip().lower()
        
        # 基本格式检查
        if len(self.username_or_email) < 3:
            raise ValueError("用户名或邮箱长度至少为3个字符")
    
    def is_email_login(self) -> bool:
        """判断是否使用邮箱登录"""
        return '@' in self.username_or_email


@dataclass
class LogoutUserCommand(BaseCommand):
    """用户登出命令"""
    user_id: str = None
    session_id: Optional[str] = None
    
    def __post_init__(self):
        super().__post_init__()
        if not self.user_id:
            raise ValueError("用户ID不能为空")


@dataclass
class RefreshTokenCommand(BaseCommand):
    """刷新令牌命令"""
    refresh_token: str = None
    
    def __post_init__(self):
        super().__post_init__()
        if not self.refresh_token:
            raise ValueError("刷新令牌不能为空")


@dataclass
class ResetPasswordCommand(BaseCommand):
    """重置密码命令"""
    email: str = None
    
    def __post_init__(self):
        super().__post_init__()
        if not self.email:
            raise ValueError("邮箱不能为空")


@dataclass
class ConfirmPasswordResetCommand(BaseCommand):
    """确认密码重置命令"""
    token: str = None
    new_password: str = None
    
    def __post_init__(self):
        super().__post_init__()
        if not self.token:
            raise ValueError("令牌不能为空")
        if not self.new_password:
            raise ValueError("新密码不能为空")


@dataclass
class VerifyEmailCommand(BaseCommand):
    """验证邮箱命令"""
    user_id: str = None
    verification_code: str = None
    
    def __post_init__(self):
        super().__post_init__()
        if not self.user_id:
            raise ValueError("用户ID不能为空")
        if not self.verification_code:
            raise ValueError("验证码不能为空")


@dataclass
class ResendVerificationEmailCommand(BaseCommand):
    """重发验证邮件命令"""
    user_id: str = None
    
    def __post_init__(self):
        super().__post_init__()
        if not self.user_id:
            raise ValueError("用户ID不能为空")


# 验证工具函数
class CommandValidationUtils:
    """
    命令验证工具类
    
    提供通用的验证方法，避免在各个命令类中重复代码。
    """
    
    @staticmethod
    def validate_password_strength(password: str, min_length: int = 8) -> None:
        """验证密码强度"""
        if len(password) < min_length:
            raise ValueError(f"密码长度不能少于{min_length}位")
        
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        
        if not (has_upper and has_lower and has_digit):
            raise ValueError("密码必须包含大写字母、小写字母和数字")
    
    @staticmethod
    def validate_email_format(email: str) -> None:
        """验证邮箱格式"""
        try:
            Email(email)  # 使用值对象验证
        except Exception:
            raise ValueError("邮箱格式不正确")
    
    @staticmethod
    def validate_username_format(username: str) -> None:
        """验证用户名格式"""
        if not CreateUserCommand.USERNAME_PATTERN.match(username):
            raise ValueError("用户名必须为3-30位字母、数字或下划线")
    
    @staticmethod
    def sanitize_string_input(value: Optional[str], max_length: int = None) -> Optional[str]:
        """清理字符串输入"""
        if value is None:
            return None
        
        cleaned = value.strip()
        if not cleaned:
            return None
        
        if max_length and len(cleaned) > max_length:
            raise ValueError(f"输入长度不能超过{max_length}个字符")
        
        return cleaned
    
    @staticmethod
    def validate_url_format(url: str) -> bool:
        """验证URL格式"""
        url_pattern = re.compile(
            r'^https?://(?:[-\w.])+(?::[0-9]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:[\w.])*)?)?$'
        )
        return bool(url_pattern.match(url))
    
    @staticmethod
    def validate_phone_format(phone: str) -> bool:
        """验证手机号码格式"""
        # 简单的手机号验证，支持中国大陆手机号
        phone_pattern = re.compile(r'^1[3-9]\d{9}$')
        return bool(phone_pattern.match(phone))


# 导出所有命令
__all__ = [
    'CreateUserCommand',
    'UpdateUserProfileCommand', 
    'ChangeUserPasswordCommand',
    'DeleteUserCommand',
    'DeactivateUserCommand',
    'ActivateUserCommand',
    'ChangeUserRoleCommand',
    'LoginUserCommand',
    'LogoutUserCommand',
    'RefreshTokenCommand',
    'ResetPasswordCommand',
    'ConfirmPasswordResetCommand',
    'VerifyEmailCommand',
    'ResendVerificationEmailCommand',
    'CommandValidationUtils'
]
