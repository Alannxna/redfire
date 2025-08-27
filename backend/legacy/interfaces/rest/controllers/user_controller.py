"""
用户控制器
==========

处理用户相关的HTTP请求
"""

from fastapi import APIRouter, HTTPException, status, Request, Query
from typing import Optional
import logging

from ..models.common import APIResponse, PaginatedResponse
from ..models.user_models import *
from ....application.services.user_application_service import UserApplicationService
from ....application.commands.command_bus import command_bus
from ....application.queries.query_bus import query_bus
from ....application.handlers.user_command_handlers import *
from ....application.handlers.user_query_handlers import *


class UserController:
    """用户控制器"""
    
    def __init__(self):
        self.router = APIRouter()
        self._logger = logging.getLogger(self.__class__.__name__)
        
        # 注册处理器
        self._register_handlers()
        
        # 创建用户应用服务
        self._user_service = UserApplicationService(command_bus, query_bus)
        
        # 设置路由
        self._setup_routes()
    
    def _register_handlers(self):
        """注册命令和查询处理器"""
        # 注册命令处理器
        command_bus.register_handler(CreateUserCommand, CreateUserCommandHandler())
        command_bus.register_handler(UpdateUserProfileCommand, UpdateUserProfileCommandHandler())
        command_bus.register_handler(ChangeUserPasswordCommand, ChangeUserPasswordCommandHandler())
        command_bus.register_handler(ChangeUserRoleCommand, ChangeUserRoleCommandHandler())
        command_bus.register_handler(ActivateUserCommand, ActivateUserCommandHandler())
        command_bus.register_handler(DeactivateUserCommand, DeactivateUserCommandHandler())
        command_bus.register_handler(LoginUserCommand, LoginUserCommandHandler())
        command_bus.register_handler(LogoutUserCommand, LogoutUserCommandHandler())
        command_bus.register_handler(RefreshTokenCommand, RefreshTokenCommandHandler())
        
        # 注册查询处理器
        query_bus.register_handler(GetUserByIdQuery, GetUserByIdQueryHandler())
        query_bus.register_handler(GetUserByUsernameQuery, GetUserByUsernameQueryHandler())
        query_bus.register_handler(GetUserByEmailQuery, GetUserByEmailQueryHandler())
        query_bus.register_handler(GetUsersQuery, GetUsersQueryHandler())
        query_bus.register_handler(SearchUsersQuery, SearchUsersQueryHandler())
        query_bus.register_handler(GetUserProfileQuery, GetUserProfileQueryHandler())
        query_bus.register_handler(ValidateUserCredentialsQuery, ValidateUserCredentialsQueryHandler())
        query_bus.register_handler(CheckUsernameAvailabilityQuery, CheckUsernameAvailabilityQueryHandler())
        query_bus.register_handler(CheckEmailAvailabilityQuery, CheckEmailAvailabilityQueryHandler())
    
    def _setup_routes(self):
        """设置路由"""
        
        @self.router.post("/register", response_model=APIResponse, summary="用户注册")
        async def register_user(user_data: CreateUserRequest):
            """注册新用户"""
            try:
                result = await self._user_service.create_user(user_data.dict())
                
                if result["success"]:
                    return APIResponse(
                        success=True,
                        message=result["message"],
                        data=result["data"]
                    )
                else:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=result["error"]
                    )
                    
            except Exception as e:
                self._logger.error(f"用户注册失败: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="用户注册失败"
                )
        
        @self.router.post("/login", response_model=APIResponse, summary="用户登录")
        async def login_user(login_data: LoginRequest):
            """用户登录"""
            try:
                result = await self._user_service.login_user(
                    login_data.username_or_email, 
                    login_data.password
                )
                
                if result["success"]:
                    return APIResponse(
                        success=True,
                        message=result["message"],
                        data=result["data"]
                    )
                else:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail=result["error"]
                    )
                    
            except Exception as e:
                self._logger.error(f"用户登录失败: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="用户登录失败"
                )
        
        @self.router.post("/logout", response_model=APIResponse, summary="用户登出")
        async def logout_user(request: Request):
            """用户登出"""
            try:
                # 从请求状态中获取当前用户信息
                current_user = getattr(request.state, 'user', None)
                if not current_user:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="用户未登录"
                    )
                
                result = await self._user_service.logout_user(current_user["user_id"])
                
                if result["success"]:
                    return APIResponse(
                        success=True,
                        message=result["message"],
                        data=result["data"]
                    )
                else:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=result["error"]
                    )
                    
            except Exception as e:
                self._logger.error(f"用户登出失败: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="用户登出失败"
                )
        
        @self.router.get("/me", response_model=APIResponse, summary="获取当前用户信息")
        async def get_current_user(request: Request):
            """获取当前登录用户的信息"""
            try:
                # 从请求状态中获取当前用户信息
                current_user = getattr(request.state, 'user', None)
                if not current_user:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="用户未登录"
                    )
                
                # 获取详细的用户信息
                result = await self._user_service.get_user_by_id(current_user["user_id"])
                
                if result["success"]:
                    return APIResponse(
                        success=True,
                        message="获取用户信息成功",
                        data=result["data"]
                    )
                else:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=result["error"]
                    )
                    
            except Exception as e:
                self._logger.error(f"获取当前用户信息失败: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="获取用户信息失败"
                )
        
        @self.router.post("/refresh-token", response_model=APIResponse, summary="刷新访问令牌")
        async def refresh_token(refresh_token_data: RefreshTokenRequest):
            """刷新访问令牌"""
            try:
                result = await self._user_service.refresh_token(refresh_token_data.refresh_token)
                
                if result["success"]:
                    return APIResponse(
                        success=True,
                        message=result["message"],
                        data=result["data"]
                    )
                else:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail=result["error"]
                    )
                    
            except Exception as e:
                self._logger.error(f"刷新令牌失败: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="刷新令牌失败"
                )
        
        @self.router.get("/{user_id}", response_model=APIResponse, summary="根据ID获取用户")
        async def get_user_by_id(user_id: str, request: Request):
            """根据ID获取用户信息"""
            try:
                result = await self._user_service.get_user_by_id(user_id)
                
                if result["success"]:
                    return APIResponse(
                        success=True,
                        message=result["message"],
                        data=result["data"]
                    )
                else:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=result["error"]
                    )
                    
            except Exception as e:
                self._logger.error(f"获取用户失败: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="获取用户失败"
                )
        
        @self.router.get("/", response_model=PaginatedResponse, summary="获取用户列表")
        async def get_users(
            request: Request,
            page: int = Query(1, ge=1, description="页码"),
            page_size: int = Query(20, ge=1, le=100, description="页面大小"),
            search: Optional[str] = Query(None, description="搜索关键词")
        ):
            """获取用户列表"""
            try:
                if search:
                    result = await self._user_service.search_users(search, page, page_size)
                else:
                    result = await self._user_service.get_users(page, page_size)
                
                if result["success"]:
                    data = result["data"]
                    return PaginatedResponse(
                        success=True,
                        message=result["message"],
                        data=data.get("items", []),
                        pagination={
                            "page": data.get("page", page),
                            "page_size": data.get("page_size", page_size),
                            "total_count": data.get("total_count", 0),
                            "total_pages": data.get("total_pages", 0)
                        }
                    )
                else:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=result["error"]
                    )
                    
            except Exception as e:
                self._logger.error(f"获取用户列表失败: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="获取用户列表失败"
                )
        
        @self.router.put("/{user_id}/profile", response_model=APIResponse, summary="更新用户资料")
        async def update_user_profile(
            user_id: str, 
            profile_data: UpdateUserProfileRequest,
            request: Request
        ):
            """更新用户资料"""
            try:
                # 验证权限（用户只能修改自己的资料）
                current_user = getattr(request.state, 'user', None)
                if current_user and current_user["user_id"] != user_id:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="无权限修改其他用户资料"
                    )
                
                result = await self._user_service.update_user_profile(
                    user_id, 
                    profile_data.dict(exclude_unset=True)
                )
                
                if result["success"]:
                    return APIResponse(
                        success=True,
                        message=result["message"],
                        data=result["data"]
                    )
                else:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=result["error"]
                    )
                    
            except Exception as e:
                self._logger.error(f"更新用户资料失败: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="更新用户资料失败"
                )
        
        @self.router.post("/{user_id}/change-password", response_model=APIResponse, summary="修改用户密码")
        async def change_user_password(
            user_id: str,
            password_data: ChangePasswordRequest,
            request: Request
        ):
            """修改用户密码"""
            try:
                # 验证权限（用户只能修改自己的密码）
                current_user = getattr(request.state, 'user', None)
                if current_user and current_user["user_id"] != user_id:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="无权限修改其他用户密码"
                    )
                
                result = await self._user_service.change_user_password(
                    user_id,
                    password_data.old_password,
                    password_data.new_password
                )
                
                if result["success"]:
                    return APIResponse(
                        success=True,
                        message=result["message"],
                        data=result["data"]
                    )
                else:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=result["error"]
                    )
                    
            except Exception as e:
                self._logger.error(f"修改用户密码失败: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="修改用户密码失败"
                )
        
        @self.router.get("/check-username/{username}", response_model=APIResponse, summary="检查用户名可用性")
        async def check_username_availability(username: str):
            """检查用户名是否可用"""
            try:
                result = await self._user_service.check_username_availability(username)
                
                if result["success"]:
                    return APIResponse(
                        success=True,
                        message=result["message"],
                        data=result["data"]
                    )
                else:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=result["error"]
                    )
                    
            except Exception as e:
                self._logger.error(f"检查用户名可用性失败: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="检查用户名可用性失败"
                )
        
        @self.router.get("/check-email/{email}", response_model=APIResponse, summary="检查邮箱可用性")
        async def check_email_availability(email: str):
            """检查邮箱是否可用"""
            try:
                result = await self._user_service.check_email_availability(email)
                
                if result["success"]:
                    return APIResponse(
                        success=True,
                        message=result["message"],
                        data=result["data"]
                    )
                else:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=result["error"]
                    )
                    
            except Exception as e:
                self._logger.error(f"检查邮箱可用性失败: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="检查邮箱可用性失败"
                )
        
        # 新增的CRUD操作
        
        @self.router.put("/{user_id}", response_model=APIResponse, summary="更新用户信息")
        async def update_user(
            user_id: str,
            user_data: AdminUpdateUserRequest,
            request: Request
        ):
            """更新用户信息（管理员操作）"""
            try:
                # 验证管理员权限
                current_user = getattr(request.state, 'user', None)
                if not current_user or current_user.get("role") not in ["admin", "super_admin"]:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="需要管理员权限"
                    )
                
                result = await self._user_service.update_user(
                    user_id,
                    user_data.dict(exclude_unset=True)
                )
                
                if result["success"]:
                    return APIResponse(
                        success=True,
                        message=result["message"],
                        data=result["data"]
                    )
                else:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=result["error"]
                    )
                    
            except Exception as e:
                self._logger.error(f"更新用户信息失败: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="更新用户信息失败"
                )
        
        @self.router.delete("/{user_id}", response_model=APIResponse, summary="删除用户")
        async def delete_user(user_id: str, request: Request):
            """删除用户（软删除）"""
            try:
                # 验证管理员权限
                current_user = getattr(request.state, 'user', None)
                if not current_user or current_user.get("role") not in ["admin", "super_admin"]:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="需要管理员权限"
                    )
                
                result = await self._user_service.delete_user(user_id)
                
                if result["success"]:
                    return APIResponse(
                        success=True,
                        message=result["message"],
                        data=result["data"]
                    )
                else:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=result["error"]
                    )
                    
            except Exception as e:
                self._logger.error(f"删除用户失败: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="删除用户失败"
                )
        
        @self.router.post("/{user_id}/activate", response_model=APIResponse, summary="激活用户")
        async def activate_user(user_id: str, request: Request):
            """激活用户"""
            try:
                # 验证管理员权限
                current_user = getattr(request.state, 'user', None)
                if not current_user or current_user.get("role") not in ["admin", "super_admin"]:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="需要管理员权限"
                    )
                
                result = await self._user_service.activate_user(user_id)
                
                if result["success"]:
                    return APIResponse(
                        success=True,
                        message=result["message"],
                        data=result["data"]
                    )
                else:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=result["error"]
                    )
                    
            except Exception as e:
                self._logger.error(f"激活用户失败: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="激活用户失败"
                )
        
        @self.router.post("/{user_id}/deactivate", response_model=APIResponse, summary="停用用户")
        async def deactivate_user(user_id: str, request: Request):
            """停用用户"""
            try:
                # 验证管理员权限
                current_user = getattr(request.state, 'user', None)
                if not current_user or current_user.get("role") not in ["admin", "super_admin"]:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="需要管理员权限"
                    )
                
                result = await self._user_service.deactivate_user(user_id)
                
                if result["success"]:
                    return APIResponse(
                        success=True,
                        message=result["message"],
                        data=result["data"]
                    )
                else:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=result["error"]
                    )
                    
            except Exception as e:
                self._logger.error(f"停用用户失败: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="停用用户失败"
                )
        
        @self.router.post("/{user_id}/change-role", response_model=APIResponse, summary="修改用户角色")
        async def change_user_role(
            user_id: str,
            role_data: ChangeRoleRequest,
            request: Request
        ):
            """修改用户角色"""
            try:
                # 验证超级管理员权限
                current_user = getattr(request.state, 'user', None)
                if not current_user or current_user.get("role") != "super_admin":
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="需要超级管理员权限"
                    )
                
                result = await self._user_service.change_user_role(
                    user_id,
                    role_data.new_role
                )
                
                if result["success"]:
                    return APIResponse(
                        success=True,
                        message=result["message"],
                        data=result["data"]
                    )
                else:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=result["error"]
                    )
                    
            except Exception as e:
                self._logger.error(f"修改用户角色失败: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="修改用户角色失败"
                )
        
        # 用户统计和管理功能
        
        @self.router.get("/stats/overview", response_model=APIResponse, summary="用户统计概览")
        async def get_user_statistics(request: Request):
            """获取用户统计信息"""
            try:
                # 验证管理员权限
                current_user = getattr(request.state, 'user', None)
                if not current_user or current_user.get("role") not in ["admin", "super_admin"]:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="需要管理员权限"
                    )
                
                result = await self._user_service.get_user_statistics()
                
                if result["success"]:
                    return APIResponse(
                        success=True,
                        message=result["message"],
                        data=result["data"]
                    )
                else:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=result["error"]
                    )
                    
            except Exception as e:
                self._logger.error(f"获取用户统计信息失败: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="获取用户统计信息失败"
                )
        
        @self.router.get("/search/advanced", response_model=PaginatedResponse, summary="高级用户搜索")
        async def advanced_user_search(
            request: Request,
            page: int = Query(1, ge=1, description="页码"),
            page_size: int = Query(20, ge=1, le=100, description="页面大小"),
            search: Optional[str] = Query(None, description="搜索关键词"),
            role: Optional[str] = Query(None, description="用户角色"),
            status: Optional[str] = Query(None, description="用户状态"),
            sort_by: str = Query("created_at", description="排序字段"),
            sort_order: str = Query("desc", description="排序方向")
        ):
            """高级用户搜索"""
            try:
                # 验证管理员权限
                current_user = getattr(request.state, 'user', None)
                if not current_user or current_user.get("role") not in ["admin", "super_admin"]:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="需要管理员权限"
                    )
                
                result = await self._user_service.advanced_user_search(
                    page=page,
                    page_size=page_size,
                    search=search,
                    role=role,
                    status=status,
                    sort_by=sort_by,
                    sort_order=sort_order
                )
                
                if result["success"]:
                    data = result["data"]
                    return PaginatedResponse(
                        success=True,
                        message=result["message"],
                        data=data.get("items", []),
                        pagination={
                            "page": data.get("page", page),
                            "page_size": data.get("page_size", page_size),
                            "total_count": data.get("total_count", 0),
                            "total_pages": data.get("total_pages", 0)
                        }
                    )
                else:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=result["error"]
                    )
                    
            except Exception as e:
                self._logger.error(f"高级用户搜索失败: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="高级用户搜索失败"
                )
        
        @self.router.get("/export/csv", response_model=APIResponse, summary="导出用户数据")
        async def export_users_csv(
            request: Request,
            role: Optional[str] = Query(None, description="用户角色"),
            status: Optional[str] = Query(None, description="用户状态"),
            created_after: Optional[str] = Query(None, description="创建日期之后"),
            created_before: Optional[str] = Query(None, description="创建日期之前")
        ):
            """导出用户数据为CSV"""
            try:
                # 验证管理员权限
                current_user = getattr(request.state, 'user', None)
                if not current_user or current_user.get("role") not in ["admin", "super_admin"]:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="需要管理员权限"
                    )
                
                result = await self._user_service.export_users_csv(
                    role=role,
                    status=status,
                    created_after=created_after,
                    created_before=created_before
                )
                
                if result["success"]:
                    return APIResponse(
                        success=True,
                        message=result["message"],
                        data=result["data"]
                    )
                else:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=result["error"]
                    )
                    
            except Exception as e:
                self._logger.error(f"导出用户数据失败: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="导出用户数据失败"
                )
        
        @self.router.post("/batch/delete", response_model=APIResponse, summary="批量删除用户")
        async def batch_delete_users(
            user_ids: BatchDeleteRequest,
            request: Request
        ):
            """批量删除用户"""
            try:
                # 验证超级管理员权限
                current_user = getattr(request.state, 'user', None)
                if not current_user or current_user.get("role") != "super_admin":
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="需要超级管理员权限"
                    )
                
                result = await self._user_service.batch_delete_users(user_ids.user_ids)
                
                if result["success"]:
                    return APIResponse(
                        success=True,
                        message=result["message"],
                        data=result["data"]
                    )
                else:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=result["error"]
                    )
                    
            except Exception as e:
                self._logger.error(f"批量删除用户失败: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="批量删除用户失败"
                )
        
        @self.router.post("/batch/update-role", response_model=APIResponse, summary="批量更新用户角色")
        async def batch_update_user_roles(
            batch_data: BatchUpdateRoleRequest,
            request: Request
        ):
            """批量更新用户角色"""
            try:
                # 验证超级管理员权限
                current_user = getattr(request.state, 'user', None)
                if not current_user or current_user.get("role") != "super_admin":
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="需要超级管理员权限"
                    )
                
                result = await self._user_service.batch_update_user_roles(
                    batch_data.user_ids,
                    batch_data.new_role
                )
                
                if result["success"]:
                    return APIResponse(
                        success=True,
                        message=result["message"],
                        data=result["data"]
                    )
                else:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=result["error"]
                    )
                    
            except Exception as e:
                self._logger.error(f"批量更新用户角色失败: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="批量更新用户角色失败"
                )
        
        # 用户个人资料相关
        
        @self.router.get("/{user_id}/profile", response_model=APIResponse, summary="获取用户详细资料")
        async def get_user_profile(user_id: str, request: Request):
            """获取用户详细资料"""
            try:
                # 验证权限（用户可以查看自己的资料，管理员可以查看任何用户资料）
                current_user = getattr(request.state, 'user', None)
                if not current_user:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="需要登录"
                    )
                
                if (current_user["user_id"] != user_id and 
                    current_user.get("role") not in ["admin", "super_admin"]):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="无权限查看此用户资料"
                    )
                
                result = await self._user_service.get_user_profile(user_id)
                
                if result["success"]:
                    return APIResponse(
                        success=True,
                        message=result["message"],
                        data=result["data"]
                    )
                else:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=result["error"]
                    )
                    
            except Exception as e:
                self._logger.error(f"获取用户详细资料失败: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="获取用户详细资料失败"
                )
        
        @self.router.post("/{user_id}/reset-password", response_model=APIResponse, summary="重置用户密码")
        async def reset_user_password(
            user_id: str,
            reset_data: AdminResetPasswordRequest,
            request: Request
        ):
            """重置用户密码（管理员操作）"""
            try:
                # 验证管理员权限
                current_user = getattr(request.state, 'user', None)
                if not current_user or current_user.get("role") not in ["admin", "super_admin"]:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="需要管理员权限"
                    )
                
                result = await self._user_service.reset_user_password(
                    user_id,
                    reset_data.new_password,
                    reset_data.notify_user
                )
                
                if result["success"]:
                    return APIResponse(
                        success=True,
                        message=result["message"],
                        data=result["data"]
                    )
                else:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=result["error"]
                    )
                    
            except Exception as e:
                self._logger.error(f"重置用户密码失败: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="重置用户密码失败"
                )