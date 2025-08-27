"""
认证应用服务
==========

提供用户认证相关的应用层服务
"""

import logging
import uuid
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta

from ...core.config.unified_config import UnifiedConfig
from ...core.common.exceptions import DomainException, ApplicationException
from ...interfaces.rest.middleware.auth_middleware import JWTHelper
from ...domain.user.entities.user import User
from ...domain.user.services.user_domain_service import UserDomainService
from ...domain.user.repositories.user_repository import IUserRepository


class AuthenticationResult:
    """认证结果"""
    
    def __init__(self, success: bool, user: Optional[User] = None, 
                 access_token: Optional[str] = None, refresh_token: Optional[str] = None,
                 error_message: Optional[str] = None, error_code: Optional[str] = None):
        self.success = success
        self.user = user
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.error_message = error_message
        self.error_code = error_code


class AuthService:
    """认证服务"""
    
    def __init__(self, config: UnifiedConfig, user_repository: IUserRepository, 
                 user_domain_service: UserDomainService):
        self.config = config
        self.user_repository = user_repository
        self.user_domain_service = user_domain_service
        self.jwt_helper = JWTHelper(config)
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 失败尝试跟踪（生产环境应使用Redis）
        self._failed_attempts: Dict[str, list] = {}
        self._lockout_duration = timedelta(minutes=30)
        self._max_attempts = 5
    
    async def authenticate(self, username_or_email: str, password: str, 
                          client_ip: Optional[str] = None) -> AuthenticationResult:
        """
        用户认证
        
        Args:
            username_or_email: 用户名或邮箱
            password: 密码
            client_ip: 客户端IP
            
        Returns:
            认证结果
        """
        try:
            # 检查账户是否被锁定
            if self._is_account_locked(username_or_email, client_ip):
                return AuthenticationResult(
                    success=False,
                    error_message="账户暂时被锁定，请稍后再试",
                    error_code="ACCOUNT_LOCKED"
                )
            
            # 验证用户凭据
            user = await self.user_domain_service.authenticate_user(username_or_email, password)
            
            if user is None:
                self._record_failed_attempt(username_or_email, client_ip)
                return AuthenticationResult(
                    success=False,
                    error_message="用户名/邮箱或密码错误",
                    error_code="INVALID_CREDENTIALS"
                )
            
            # 检查用户状态
            if not user.is_active:
                return AuthenticationResult(
                    success=False,
                    error_message="账户已被禁用",
                    error_code="ACCOUNT_DISABLED"
                )
            
            # 生成JWT令牌
            user_data = {
                "user_id": str(user.user_id.value),
                "username": user.username.value,
                "email": user.email.value,
                "role": user.role.value
            }
            
            access_token = self.jwt_helper.create_access_token(user_data)
            refresh_token = self.jwt_helper.create_refresh_token(user_data)
            
            # 更新最后登录时间
            await self._update_last_login(user)
            
            # 清除失败尝试记录
            self._clear_failed_attempts(username_or_email, client_ip)
            
            self.logger.info(f"用户 {user.username.value} 登录成功，IP: {client_ip}")
            
            return AuthenticationResult(
                success=True,
                user=user,
                access_token=access_token,
                refresh_token=refresh_token
            )
            
        except DomainException as e:
            self.logger.warning(f"认证失败: {str(e)}")
            return AuthenticationResult(
                success=False,
                error_message=str(e),
                error_code="DOMAIN_ERROR"
            )
        except Exception as e:
            self.logger.error(f"认证服务异常: {str(e)}")
            return AuthenticationResult(
                success=False,
                error_message="认证服务暂时不可用",
                error_code="SERVICE_ERROR"
            )
    
    async def refresh_token(self, refresh_token: str) -> AuthenticationResult:
        """
        刷新访问令牌
        
        Args:
            refresh_token: 刷新令牌
            
        Returns:
            新的认证结果
        """
        try:
            # 验证刷新令牌
            payload = self.jwt_helper.verify_token(refresh_token, "refresh")
            if not payload:
                return AuthenticationResult(
                    success=False,
                    error_message="刷新令牌无效或已过期",
                    error_code="INVALID_REFRESH_TOKEN"
                )
            
            # 根据user_id获取用户
            user_id = payload.get("user_id")
            from ...domain.user.value_objects.user_id import UserId
            user = await self.user_repository.find_by_id(UserId(user_id))
            
            if not user or not user.is_active:
                return AuthenticationResult(
                    success=False,
                    error_message="用户不存在或已被禁用",
                    error_code="USER_NOT_FOUND"
                )
            
            # 生成新的访问令牌
            user_data = {
                "user_id": str(user.user_id.value),
                "username": user.username.value,
                "email": user.email.value,
                "role": user.role.value
            }
            
            access_token = self.jwt_helper.create_access_token(user_data)
            
            return AuthenticationResult(
                success=True,
                user=user,
                access_token=access_token,
                refresh_token=refresh_token  # 保持原有刷新令牌
            )
            
        except Exception as e:
            self.logger.error(f"刷新令牌失败: {str(e)}")
            return AuthenticationResult(
                success=False,
                error_message="令牌刷新失败",
                error_code="REFRESH_ERROR"
            )
    
    def validate_token(self, access_token: str) -> Optional[Dict[str, Any]]:
        """
        验证访问令牌
        
        Args:
            access_token: 访问令牌
            
        Returns:
            令牌载荷或None
        """
        return self.jwt_helper.verify_token(access_token, "access")
    
    async def logout(self, access_token: str) -> bool:
        """
        用户登出（将令牌加入黑名单）
        
        Args:
            access_token: 访问令牌
            
        Returns:
            是否成功
        """
        try:
            # 解码令牌获取信息
            payload = self.jwt_helper.decode_token_without_verification(access_token)
            if payload:
                username = payload.get("username")
                self.logger.info(f"用户 {username} 登出")
                
                # TODO: 在生产环境中，应该将令牌添加到Redis黑名单
                # 目前只记录日志
                return True
            return False
        except Exception as e:
            self.logger.error(f"登出失败: {str(e)}")
            return False
    
    def _is_account_locked(self, identifier: str, client_ip: Optional[str]) -> bool:
        """检查账户是否被锁定"""
        key = f"{identifier}:{client_ip or 'unknown'}"
        attempts = self._failed_attempts.get(key, [])
        
        if len(attempts) < self._max_attempts:
            return False
        
        # 检查最后一次失败时间
        last_attempt = attempts[-1]
        if datetime.now() - last_attempt < self._lockout_duration:
            return True
        
        # 锁定时间已过，清除记录
        self._failed_attempts.pop(key, None)
        return False
    
    def _record_failed_attempt(self, identifier: str, client_ip: Optional[str]):
        """记录失败尝试"""
        key = f"{identifier}:{client_ip or 'unknown'}"
        attempts = self._failed_attempts.get(key, [])
        attempts.append(datetime.now())
        
        # 只保留最近的尝试记录
        if len(attempts) > self._max_attempts:
            attempts = attempts[-self._max_attempts:]
        
        self._failed_attempts[key] = attempts
    
    def _clear_failed_attempts(self, identifier: str, client_ip: Optional[str]):
        """清除失败尝试记录"""
        key = f"{identifier}:{client_ip or 'unknown'}"
        self._failed_attempts.pop(key, None)
    
    async def _update_last_login(self, user: User):
        """更新用户最后登录时间"""
        try:
            # 这里应该调用用户仓储更新最后登录时间
            # 暂时跳过，因为User实体可能需要添加相应方法
            pass
        except Exception as e:
            self.logger.warning(f"更新最后登录时间失败: {str(e)}")
