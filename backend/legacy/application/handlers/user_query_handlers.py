"""
用户查询处理器
============

处理用户相关的查询
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from ..queries.user_queries import *
from ..queries.base_query import QueryResult
from ..handlers.base_query_handler import BaseQueryHandler
from ...domain.user.repositories.user_repository import IUserRepository as UserRepository
from ...domain.user.value_objects.user_id import UserId
from ...domain.shared.value_objects.email import Email
from ...domain.user.value_objects.username import Username
from ...core.base.exceptions import ValidationException


class GetUserByIdQueryHandler(BaseQueryHandler[GetUserByIdQuery]):
    """根据ID获取用户查询处理器"""
    
    def __init__(self, user_repository: UserRepository):
        super().__init__()
        self._user_repository = user_repository
        self._logger = logging.getLogger(self.__class__.__name__)
    
    async def handle(self, query: GetUserByIdQuery) -> QueryResult:
        """处理根据ID获取用户查询"""
        try:
            # 验证用户ID
            if not query.user_id:
                return QueryResult(
                    success=False,
                    error="用户ID不能为空"
                )
            
            # 查找用户
            user = await self._user_repository.find_by_id(UserId(query.user_id))
            
            if not user:
                return QueryResult(
                    success=False,
                    error="用户不存在"
                )
            
            # 返回用户信息
            user_data = {
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
            
            return QueryResult(
                success=True,
                data=user_data,
                message="用户查询成功"
            )
            
        except ValidationException as e:
            self._logger.error(f"用户查询验证失败: {e}")
            return QueryResult(
                success=False,
                error=str(e)
            )
        except Exception as e:
            self._logger.error(f"用户查询失败: {e}")
            return QueryResult(
                success=False,
                error="用户查询失败"
            )


class GetUserByUsernameQueryHandler(BaseQueryHandler[GetUserByUsernameQuery]):
    """根据用户名获取用户查询处理器"""
    
    def __init__(self, user_repository: UserRepository):
        super().__init__()
        self._user_repository = user_repository
        self._logger = logging.getLogger(self.__class__.__name__)
    
    async def handle(self, query: GetUserByUsernameQuery) -> QueryResult:
        """处理根据用户名获取用户查询"""
        try:
            # 验证用户名
            if not query.username:
                return QueryResult(
                    success=False,
                    error="用户名不能为空"
                )
            
            # 查找用户
            user = await self._user_repository.find_by_username(query.username)
            
            if not user:
                return QueryResult(
                    success=False,
                    error="用户不存在"
                )
            
            # 返回用户信息
            user_data = {
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
            
            return QueryResult(
                success=True,
                data=user_data,
                message="用户查询成功"
            )
            
        except ValidationException as e:
            self._logger.error(f"用户查询验证失败: {e}")
            return QueryResult(
                success=False,
                error=str(e)
            )
        except Exception as e:
            self._logger.error(f"用户查询失败: {e}")
            return QueryResult(
                success=False,
                error="用户查询失败"
            )


class GetUserByEmailQueryHandler(BaseQueryHandler[GetUserByEmailQuery]):
    """根据邮箱获取用户查询处理器"""
    
    def __init__(self, user_repository: UserRepository):
        super().__init__()
        self._user_repository = user_repository
        self._logger = logging.getLogger(self.__class__.__name__)
    
    async def handle(self, query: GetUserByEmailQuery) -> QueryResult:
        """处理根据邮箱获取用户查询"""
        try:
            # 验证邮箱
            if not query.email:
                return QueryResult(
                    success=False,
                    error="邮箱不能为空"
                )
            
            # 查找用户
            user = await self._user_repository.find_by_email(query.email)
            
            if not user:
                return QueryResult(
                    success=False,
                    error="用户不存在"
                )
            
            # 返回用户信息
            user_data = {
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
            
            return QueryResult(
                success=True,
                data=user_data,
                message="用户查询成功"
            )
            
        except ValidationException as e:
            self._logger.error(f"用户查询验证失败: {e}")
            return QueryResult(
                success=False,
                error=str(e)
            )
        except Exception as e:
            self._logger.error(f"用户查询失败: {e}")
            return QueryResult(
                success=False,
                error="用户查询失败"
            )


class GetUsersQueryHandler(BaseQueryHandler[GetUsersQuery]):
    """获取用户列表查询处理器"""
    
    def __init__(self, user_repository: UserRepository):
        super().__init__()
        self._user_repository = user_repository
        self._logger = logging.getLogger(self.__class__.__name__)
    
    async def handle(self, query: GetUsersQuery) -> QueryResult:
        """处理获取用户列表查询"""
        try:
            # 验证分页参数
            if query.page < 1:
                query.page = 1
            if query.page_size < 1 or query.page_size > 100:
                query.page_size = 20
            
            # 获取用户列表
            users, total_count = await self._user_repository.find_all(
                page=query.page,
                page_size=query.page_size
            )
            
            # 计算总页数
            total_pages = (total_count + query.page_size - 1) // query.page_size
            
            # 转换用户数据
            users_data = []
            for user in users:
                user_data = {
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
                users_data.append(user_data)
            
            # 返回分页数据
            result_data = {
                "items": users_data,
                "page": query.page,
                "page_size": query.page_size,
                "total_count": total_count,
                "total_pages": total_pages
            }
            
            return QueryResult(
                success=True,
                data=result_data,
                message="用户列表查询成功"
            )
            
        except Exception as e:
            self._logger.error(f"用户列表查询失败: {e}")
            return QueryResult(
                success=False,
                error="用户列表查询失败"
            )


class SearchUsersQueryHandler(BaseQueryHandler[SearchUsersQuery]):
    """搜索用户查询处理器"""
    
    def __init__(self, user_repository: UserRepository):
        super().__init__()
        self._user_repository = user_repository
        self._logger = logging.getLogger(self.__class__.__name__)
    
    async def handle(self, query: SearchUsersQuery) -> QueryResult:
        """处理搜索用户查询"""
        try:
            # 验证搜索参数
            if not query.search_term or len(query.search_term.strip()) < 2:
                return QueryResult(
                    success=False,
                    error="搜索关键词至少需要2个字符"
                )
            
            # 验证分页参数
            if query.page < 1:
                query.page = 1
            if query.page_size < 1 or query.page_size > 100:
                query.page_size = 20
            
            # 搜索用户
            users, total_count = await self._user_repository.search(
                search_term=query.search_term.strip(),
                page=query.page,
                page_size=query.page_size
            )
            
            # 计算总页数
            total_pages = (total_count + query.page_size - 1) // query.page_size
            
            # 转换用户数据
            users_data = []
            for user in users:
                user_data = {
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
                users_data.append(user_data)
            
            # 返回分页数据
            result_data = {
                "items": users_data,
                "page": query.page,
                "page_size": query.page_size,
                "total_count": total_count,
                "total_pages": total_pages,
                "search_term": query.search_term
            }
            
            return QueryResult(
                success=True,
                data=result_data,
                message="用户搜索成功"
            )
            
        except Exception as e:
            self._logger.error(f"用户搜索失败: {e}")
            return QueryResult(
                success=False,
                error="用户搜索失败"
            )


class GetUserProfileQueryHandler(BaseQueryHandler[GetUserProfileQuery]):
    """获取用户详细资料查询处理器"""
    
    def __init__(self, user_repository: UserRepository):
        super().__init__()
        self._user_repository = user_repository
        self._logger = logging.getLogger(self.__class__.__name__)
    
    async def handle(self, query: GetUserProfileQuery) -> QueryResult:
        """处理获取用户详细资料查询"""
        try:
            # 验证用户ID
            if not query.user_id:
                return QueryResult(
                    success=False,
                    error="用户ID不能为空"
                )
            
            # 查找用户
            user = await self._user_repository.find_by_id(UserId(query.user_id))
            
            if not user:
                return QueryResult(
                    success=False,
                    error="用户不存在"
                )
            
            # 返回详细用户信息
            user_data = {
                "id": user.id.value,
                "username": user.username.value,
                "email": user.email.value,
                "phone": user.phone.value if user.phone else None,
                "role": user.role.value,
                "status": user.status.value,
                "created_at": user.created_at.isoformat(),
                "updated_at": user.updated_at.isoformat(),
                "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
                "profile": {
                    "avatar_url": getattr(user, 'avatar_url', None),
                    "bio": getattr(user, 'bio', None),
                    "timezone": getattr(user, 'timezone', None),
                    "language": getattr(user, 'language', None),
                    "preferences": getattr(user, 'preferences', {})
                }
            }
            
            return QueryResult(
                success=True,
                data=user_data,
                message="用户详细资料查询成功"
            )
            
        except ValidationException as e:
            self._logger.error(f"用户详细资料查询验证失败: {e}")
            return QueryResult(
                success=False,
                error=str(e)
            )
        except Exception as e:
            self._logger.error(f"用户详细资料查询失败: {e}")
            return QueryResult(
                success=False,
                error="用户详细资料查询失败"
            )


class ValidateUserCredentialsQueryHandler(BaseQueryHandler[ValidateUserCredentialsQuery]):
    """验证用户凭据查询处理器"""
    
    def __init__(self, user_repository: UserRepository):
        super().__init__()
        self._user_repository = user_repository
        self._logger = logging.getLogger(self.__class__.__name__)
    
    async def handle(self, query: ValidateUserCredentialsQuery) -> QueryResult:
        """处理验证用户凭据查询"""
        try:
            # 验证输入参数
            if not query.username or not query.password:
                return QueryResult(
                    success=False,
                    error="用户名和密码不能为空"
                )
            
            # 查找用户
            user = None
            if '@' in query.username:
                # 邮箱登录
                user = await self._user_repository.find_by_email(query.username)
            else:
                # 用户名登录
                user = await self._user_repository.find_by_username(query.username)
            
            if not user:
                return QueryResult(
                    success=False,
                    error="用户名或密码错误"
                )
            
            # 检查用户状态
            if user.status.value != "active":
                return QueryResult(
                    success=False,
                    error="用户账户已被停用"
                )
            
            # 返回验证结果（不包含密码信息）
            validation_data = {
                "is_valid": True,
                "user_id": user.id.value,
                "username": user.username.value,
                "email": user.email.value,
                "role": user.role.value,
                "status": user.status.value
            }
            
            return QueryResult(
                success=True,
                data=validation_data,
                message="用户凭据验证成功"
            )
            
        except Exception as e:
            self._logger.error(f"用户凭据验证失败: {e}")
            return QueryResult(
                success=False,
                error="用户凭据验证失败"
            )


class CheckUsernameAvailabilityQueryHandler(BaseQueryHandler[CheckUsernameAvailabilityQuery]):
    """检查用户名可用性查询处理器"""
    
    def __init__(self, user_repository: UserRepository):
        super().__init__()
        self._user_repository = user_repository
        self._logger = logging.getLogger(self.__class__.__name__)
    
    async def handle(self, query: CheckUsernameAvailabilityQuery) -> QueryResult:
        """处理检查用户名可用性查询"""
        try:
            # 验证用户名
            if not query.username:
                return QueryResult(
                    success=False,
                    error="用户名不能为空"
                )
            
            # 检查用户名是否已存在
            existing_user = await self._user_repository.find_by_username(query.username)
            
            # 返回检查结果
            availability_data = {
                "field_name": "username",
                "field_value": query.username,
                "is_available": existing_user is None,
                "checked_at": datetime.now().isoformat()
            }
            
            return QueryResult(
                success=True,
                data=availability_data,
                message="用户名可用性检查完成"
            )
            
        except Exception as e:
            self._logger.error(f"用户名可用性检查失败: {e}")
            return QueryResult(
                success=False,
                error="用户名可用性检查失败"
            )


class CheckEmailAvailabilityQueryHandler(BaseQueryHandler[CheckEmailAvailabilityQuery]):
    """检查邮箱可用性查询处理器"""
    
    def __init__(self, user_repository: UserRepository):
        super().__init__()
        self._user_repository = user_repository
        self._logger = logging.getLogger(self.__class__.__name__)
    
    async def handle(self, query: CheckEmailAvailabilityQuery) -> QueryResult:
        """处理检查邮箱可用性查询"""
        try:
            # 验证邮箱
            if not query.email:
                return QueryResult(
                    success=False,
                    error="邮箱不能为空"
                )
            
            # 检查邮箱是否已存在
            existing_user = await self._user_repository.find_by_email(query.email)
            
            # 返回检查结果
            availability_data = {
                "field_name": "email",
                "field_value": query.email,
                "is_available": existing_user is None,
                "checked_at": datetime.now().isoformat()
            }
            
            return QueryResult(
                success=True,
                data=availability_data,
                message="邮箱可用性检查完成"
            )
            
        except Exception as e:
            self._logger.error(f"邮箱可用性检查失败: {e}")
            return QueryResult(
                success=False,
                error="邮箱可用性检查失败"
            )