"""
用户命令处理器
============

处理用户相关的命令
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
from ...interfaces.rest.middleware.auth_middleware import JWTHelper
import uuid

from ..commands.user_commands import *
from ..commands.base_command import CommandResult
from ..handlers.base_command_handler import BaseCommandHandler
from ...domain.user.services.user_domain_service import UserDomainService
from ...domain.user.repositories.user_repository import IUserRepository as UserRepository
from ...domain.user.entities.user import User
from ...domain.user.value_objects.user_id import UserId
from ...domain.shared.value_objects.email import Email

from ...domain.shared.value_objects.phone import Phone
from ...domain.user.value_objects.username import Username
from ...core.common.enums.user_roles import UserRole, UserStatus
from ...core.base.exceptions import DomainException, ValidationException



class CreateUserCommandHandler(BaseCommandHandler[CreateUserCommand]):
    """创建用户命令处理器"""
    
    def __init__(self, user_repository: UserRepository, user_domain_service: UserDomainService):
        super().__init__()
        self._user_repository = user_repository
        self._user_domain_service = user_domain_service
        self._logger = logging.getLogger(self.__class__.__name__)
    
    async def handle(self, command: CreateUserCommand) -> CommandResult:
        """处理创建用户命令"""
        try:
            # 验证输入
            if not command.username or not command.email or not command.password:
                return CommandResult(
                    success=False,
                    error="用户名、邮箱和密码不能为空"
                )
            
            # 检查用户名是否已存在
            existing_user = await self._user_repository.find_by_username(command.username)
            if existing_user:
                return CommandResult(
                    success=False,
                    error="用户名已存在"
                )
            
            # 检查邮箱是否已存在
            existing_email = await self._user_repository.find_by_email(command.email)
            if existing_email:
                return CommandResult(
                    success=False,
                    error="邮箱已存在"
                )
            
            # 创建用户ID
            user_id = UserId(str(uuid.uuid4()))
            
            # 创建值对象
            username = Username(command.username)
            email = Email(command.email)
            phone = Phone(command.phone) if command.phone else None
            role = UserRole(command.role) if command.role else UserRole.USER
            
            # 加密密码
            hashed_password = self._user_domain_service._hash_password(command.password)
            
            # 创建用户实体
            user = User(
                id=user_id,
                username=username,
                email=email,
                password_hash=hashed_password,
                phone=phone,
                role=role,
                status=UserStatus.ACTIVE,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            # 保存用户
            await self._user_repository.save(user)
            
            # 返回用户信息（不包含密码）
            user_data = {
                "id": user.id.value,
                "username": user.username.value,
                "email": user.email.value,
                "phone": user.phone.value if user.phone else None,
                "role": user.role.value,
                "status": user.status.value,
                "created_at": user.created_at.isoformat(),
                "updated_at": user.updated_at.isoformat()
            }
            
            self._logger.info(f"用户创建成功: {user.username.value}")
            
            return CommandResult(
                success=True,
                data=user_data,
                message="用户创建成功"
            )
            
        except ValidationException as e:
            self._logger.error(f"用户创建验证失败: {e}")
            return CommandResult(
                success=False,
                error=str(e)
            )
        except Exception as e:
            self._logger.error(f"用户创建失败: {e}")
            return CommandResult(
                success=False,
                error="用户创建失败"
            )


class UpdateUserProfileCommandHandler(BaseCommandHandler[UpdateUserProfileCommand]):
    """更新用户资料命令处理器"""
    
    def __init__(self, user_repository: UserRepository):
        super().__init__()
        self._user_repository = user_repository
        self._logger = logging.getLogger(self.__class__.__name__)
    
    async def handle(self, command: UpdateUserProfileCommand) -> CommandResult:
        """处理更新用户资料命令"""
        try:
            # 获取用户
            user = await self._user_repository.find_by_id(UserId(command.user_id))
            if not user:
                return CommandResult(
                    success=False,
                    error="用户不存在"
                )
            
            # 更新字段
            updated = False
            
            if command.email:
                # 检查邮箱是否已被其他用户使用
                existing_user = await self._user_repository.find_by_email(command.email)
                if existing_user and existing_user.id.value != command.user_id:
                    return CommandResult(
                        success=False,
                        error="邮箱已被其他用户使用"
                    )
                user.email = Email(command.email)
                updated = True
            
            if command.phone:
                user.phone = Phone(command.phone)
                updated = True
            
            if updated:
                user.updated_at = datetime.now()
                await self._user_repository.save(user)
            
            # 返回更新后的用户信息
            user_data = {
                "id": user.id.value,
                "username": user.username.value,
                "email": user.email.value,
                "phone": user.phone.value if user.phone else None,
                "role": user.role.value,
                "status": user.status.value,
                "created_at": user.created_at.isoformat(),
                "updated_at": user.updated_at.isoformat()
            }
            
            self._logger.info(f"用户资料更新成功: {user.username.value}")
            
            return CommandResult(
                success=True,
                data=user_data,
                message="用户资料更新成功"
            )
            
        except ValidationException as e:
            self._logger.error(f"用户资料更新验证失败: {e}")
            return CommandResult(
                success=False,
                error=str(e)
            )
        except Exception as e:
            self._logger.error(f"用户资料更新失败: {e}")
            return CommandResult(
                success=False,
                error="用户资料更新失败"
            )


class ChangeUserPasswordCommandHandler(BaseCommandHandler[ChangeUserPasswordCommand]):
    """修改用户密码命令处理器"""
    
    def __init__(self, user_repository: UserRepository, user_domain_service: UserDomainService):
        super().__init__()
        self._user_repository = user_repository
        self._user_domain_service = user_domain_service
        self._logger = logging.getLogger(self.__class__.__name__)
    
    async def handle(self, command: ChangeUserPasswordCommand) -> CommandResult:
        """处理修改用户密码命令"""
        try:
            # 获取用户
            user = await self._user_repository.find_by_id(UserId(command.user_id))
            if not user:
                return CommandResult(
                    success=False,
                    error="用户不存在"
                )
            
            # 如果不是管理员重置，需要验证旧密码
            if not command.is_admin_reset:
                if not command.old_password:
                    return CommandResult(
                        success=False,
                        error="原密码不能为空"
                    )
                
                # 验证旧密码
                if not self._user_domain_service._verify_password(command.old_password, user.password_hash):
                    return CommandResult(
                        success=False,
                        error="原密码错误"
                    )
            
            # 验证新密码
            if not command.new_password:
                return CommandResult(
                    success=False,
                    error="新密码不能为空"
                )
            
            # 加密新密码
            new_password_hash = self._user_domain_service._hash_password(command.new_password)
            
            # 更新密码
            user.password_hash = new_password_hash
            user.updated_at = datetime.now()
            
            # 保存用户
            await self._user_repository.save(user)
            
            self._logger.info(f"用户密码修改成功: {user.username.value}")
            
            return CommandResult(
                success=True,
                data={"user_id": user.id.value},
                message="密码修改成功"
            )
            
        except ValidationException as e:
            self._logger.error(f"密码修改验证失败: {e}")
            return CommandResult(
                success=False,
                error=str(e)
            )
        except Exception as e:
            self._logger.error(f"密码修改失败: {e}")
            return CommandResult(
                success=False,
                error="密码修改失败"
            )


class ChangeUserRoleCommandHandler(BaseCommandHandler[ChangeUserRoleCommand]):
    """修改用户角色命令处理器"""
    
    def __init__(self, user_repository: UserRepository):
        super().__init__()
        self._user_repository = user_repository
        self._logger = logging.getLogger(self.__class__.__name__)
    
    async def handle(self, command: ChangeUserRoleCommand) -> CommandResult:
        """处理修改用户角色命令"""
        try:
            # 获取用户
            user = await self._user_repository.find_by_id(UserId(command.user_id))
            if not user:
                return CommandResult(
                    success=False,
                    error="用户不存在"
                )
            
            # 验证新角色
            try:
                new_role = UserRole(command.new_role)
            except ValueError:
                return CommandResult(
                    success=False,
                    error="无效的用户角色"
                )
            
            # 更新角色
            user.role = new_role
            user.updated_at = datetime.now()
            
            # 保存用户
            await self._user_repository.save(user)
            
            # 返回更新后的用户信息
            user_data = {
                "id": user.id.value,
                "username": user.username.value,
                "email": user.email.value,
                "phone": user.phone.value if user.phone else None,
                "role": user.role.value,
                "status": user.status.value,
                "created_at": user.created_at.isoformat(),
                "updated_at": user.updated_at.isoformat()
            }
            
            self._logger.info(f"用户角色修改成功: {user.username.value} -> {new_role.value}")
            
            return CommandResult(
                success=True,
                data=user_data,
                message="用户角色修改成功"
            )
            
        except ValidationException as e:
            self._logger.error(f"用户角色修改验证失败: {e}")
            return CommandResult(
                success=False,
                error=str(e)
            )
        except Exception as e:
            self._logger.error(f"用户角色修改失败: {e}")
            return CommandResult(
                success=False,
                error="用户角色修改失败"
            )


class ActivateUserCommandHandler(BaseCommandHandler[ActivateUserCommand]):
    """激活用户命令处理器"""
    
    def __init__(self, user_repository: UserRepository):
        super().__init__()
        self._user_repository = user_repository
        self._logger = logging.getLogger(self.__class__.__name__)
    
    async def handle(self, command: ActivateUserCommand) -> CommandResult:
        """处理激活用户命令"""
        try:
            # 获取用户
            user = await self._user_repository.find_by_id(UserId(command.user_id))
            if not user:
                return CommandResult(
                    success=False,
                    error="用户不存在"
                )
            
            # 检查用户是否已经是激活状态
            if user.status == UserStatus.ACTIVE:
                return CommandResult(
                    success=False,
                    error="用户已经是激活状态"
                )
            
            # 激活用户
            user.status = UserStatus.ACTIVE
            user.updated_at = datetime.now()
            
            # 保存用户
            await self._user_repository.save(user)
            
            # 返回更新后的用户信息
            user_data = {
                "id": user.id.value,
                "username": user.username.value,
                "email": user.email.value,
                "phone": user.phone.value if user.phone else None,
                "role": user.role.value,
                "status": user.status.value,
                "created_at": user.created_at.isoformat(),
                "updated_at": user.updated_at.isoformat()
            }
            
            self._logger.info(f"用户激活成功: {user.username.value}")
            
            return CommandResult(
                success=True,
                data=user_data,
                message="用户激活成功"
            )
            
        except Exception as e:
            self._logger.error(f"用户激活失败: {e}")
            return CommandResult(
                success=False,
                error="用户激活失败"
            )


class DeactivateUserCommandHandler(BaseCommandHandler[DeactivateUserCommand]):
    """停用用户命令处理器"""
    
    def __init__(self, user_repository: UserRepository):
        super().__init__()
        self._user_repository = user_repository
        self._logger = logging.getLogger(self.__class__.__name__)
    
    async def handle(self, command: DeactivateUserCommand) -> CommandResult:
        """处理停用用户命令"""
        try:
            # 获取用户
            user = await self._user_repository.find_by_id(UserId(command.user_id))
            if not user:
                return CommandResult(
                    success=False,
                    error="用户不存在"
                )
            
            # 检查用户是否已经是停用状态
            if user.status == UserStatus.INACTIVE:
                return CommandResult(
                    success=False,
                    error="用户已经是停用状态"
                )
            
            # 停用用户
            user.status = UserStatus.INACTIVE
            user.updated_at = datetime.now()
            
            # 保存用户
            await self._user_repository.save(user)
            
            # 返回更新后的用户信息
            user_data = {
                "id": user.id.value,
                "username": user.username.value,
                "email": user.email.value,
                "phone": user.phone.value if user.phone else None,
                "role": user.role.value,
                "status": user.status.value,
                "created_at": user.created_at.isoformat(),
                "updated_at": user.updated_at.isoformat()
            }
            
            self._logger.info(f"用户停用成功: {user.username.value}")
            
            return CommandResult(
                success=True,
                data=user_data,
                message="用户停用成功"
            )
            
        except Exception as e:
            self._logger.error(f"用户停用失败: {e}")
            return CommandResult(
                success=False,
                error="用户停用失败"
            )


class LoginUserCommandHandler(BaseCommandHandler[LoginUserCommand]):
    """用户登录命令处理器"""
    
    def __init__(self, user_repository: UserRepository, user_domain_service: UserDomainService):
        super().__init__()
        self._user_repository = user_repository
        self._user_domain_service = user_domain_service
        self._jwt_helper = JWTHelper()
        self._logger = logging.getLogger(self.__class__.__name__)
    
    async def handle(self, command: LoginUserCommand) -> CommandResult:
        """处理用户登录命令"""
        try:
            # 查找用户（支持用户名或邮箱登录）
            user = None
            if '@' in command.username_or_email:
                # 邮箱登录
                user = await self._user_repository.find_by_email(command.username_or_email)
            else:
                # 用户名登录
                user = await self._user_repository.find_by_username(command.username_or_email)
            
            if not user:
                return CommandResult(
                    success=False,
                    error="用户名或密码错误"
                )
            
            # 检查用户状态
            if user.status != UserStatus.ACTIVE:
                return CommandResult(
                    success=False,
                    error="用户账户已被停用"
                )
            
            # 验证密码
            if not self._user_domain_service._verify_password(command.password, user.password_hash):
                return CommandResult(
                    success=False,
                    error="用户名或密码错误"
                )
            
            # 准备用户数据用于生成JWT token
            user_data = {
                "user_id": user.id.value,
                "username": user.username.value,
                "email": user.email.value,
                "role": user.role.value
            }
            
            # 生成JWT访问令牌
            access_token = self._jwt_helper.create_access_token(user_data)
            
            # 生成JWT刷新令牌
            refresh_token = self._jwt_helper.create_refresh_token(user_data)
            
            # 更新最后登录时间
            user.last_login_at = datetime.now()
            user.updated_at = datetime.now()
            await self._user_repository.save(user)
            
            # 返回登录信息
            login_data = {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "Bearer",
                "expires_in": 3600,  # 1小时（与JWT配置对应）
                "user": {
                    "id": user.id.value,
                    "username": user.username.value,
                    "email": user.email.value,
                    "phone": user.phone.value if user.phone else None,
                    "role": user.role.value,
                    "status": user.status.value,
                    "created_at": user.created_at.isoformat(),
                    "updated_at": user.updated_at.isoformat(),
                    "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None
                }
            }
            
            self._logger.info(f"用户登录成功: {user.username.value}")
            
            return CommandResult(
                success=True,
                data=login_data,
                message="登录成功"
            )
            
        except Exception as e:
            self._logger.error(f"用户登录失败: {e}")
            return CommandResult(
                success=False,
                error="登录失败"
            )


class LogoutUserCommandHandler(BaseCommandHandler[LogoutUserCommand]):
    """用户登出命令处理器"""
    
    def __init__(self, user_repository: UserRepository):
        super().__init__()
        self._user_repository = user_repository
        self._jwt_helper = JWTHelper()
        self._logger = logging.getLogger(self.__class__.__name__)
    
    async def handle(self, command: LogoutUserCommand) -> CommandResult:
        """处理用户登出命令"""
        try:
            # 查找用户
            user = await self._user_repository.find_by_id(command.user_id)
            if not user:
                return CommandResult(
                    success=False,
                    error="用户不存在"
                )
            
            # TODO: 实现令牌黑名单机制
            # 这里可以将用户的令牌添加到黑名单中，使其立即失效
            # 目前JWT是无状态的，所以我们暂时记录登出时间
            
            # 更新用户的最后活动时间
            user.updated_at = datetime.now()
            await self._user_repository.save(user)
            
            self._logger.info(f"用户登出成功: {user.username.value}")
            
            return CommandResult(
                success=True,
                data={"user_id": command.user_id},
                message="登出成功"
            )
            
        except Exception as e:
            self._logger.error(f"用户登出失败: {e}")
            return CommandResult(
                success=False,
                error="登出失败"
            )


class RefreshTokenCommandHandler(BaseCommandHandler[RefreshTokenCommand]):
    """刷新令牌命令处理器"""
    
    def __init__(self, user_repository: UserRepository):
        super().__init__()
        self._user_repository = user_repository
        self._jwt_helper = JWTHelper()
        self._logger = logging.getLogger(self.__class__.__name__)
    
    async def handle(self, command: RefreshTokenCommand) -> CommandResult:
        """处理刷新令牌命令"""
        try:
            # 验证刷新令牌
            payload = self._jwt_helper.verify_token(command.refresh_token, "refresh")
            if not payload:
                return CommandResult(
                    success=False,
                    error="刷新令牌无效或已过期"
                )
            
            # 查找用户
            user_id = payload.get("user_id")
            user = await self._user_repository.find_by_id(user_id)
            if not user:
                return CommandResult(
                    success=False,
                    error="用户不存在"
                )
            
            # 检查用户状态
            if user.status != UserStatus.ACTIVE:
                return CommandResult(
                    success=False,
                    error="用户账户已被停用"
                )
            
            # 准备用户数据用于生成新的JWT token
            user_data = {
                "user_id": user.id.value,
                "username": user.username.value,
                "email": user.email.value,
                "role": user.role.value
            }
            
            # 生成新的访问令牌
            new_access_token = self._jwt_helper.create_access_token(user_data)
            
            # 生成新的刷新令牌
            new_refresh_token = self._jwt_helper.create_refresh_token(user_data)
            
            # 返回新的令牌信息
            token_data = {
                "access_token": new_access_token,
                "refresh_token": new_refresh_token,
                "token_type": "Bearer",
                "expires_in": 3600,  # 1小时（与JWT配置对应）
            }
            
            self._logger.info(f"令牌刷新成功: {user.username.value}")
            
            return CommandResult(
                success=True,
                data=token_data,
                message="令牌刷新成功"
            )
            
        except Exception as e:
            self._logger.error(f"刷新令牌失败: {e}")
            return CommandResult(
                success=False,
                error="刷新令牌失败"
            )