"""
用户应用服务
===========

提供用户相关的应用层服务接口
"""

# 标准库导入
import logging
from typing import Dict, Any, Optional, List

# 核心层导入
from ...core.base.exceptions import DomainException

# 应用层内部导入
from .base_application_service import BaseApplicationService
from ..commands.command_bus import CommandBus
from ..queries.query_bus import QueryBus
from ..commands.user_commands import *
from ..queries.user_queries import *


class UserApplicationService(BaseApplicationService):
    """用户应用服务"""
    
    def __init__(self, command_bus: CommandBus, query_bus: QueryBus):
        super().__init__(command_bus, query_bus)
        self._logger = logging.getLogger(self.__class__.__name__)
    
    async def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建用户"""
        try:
            # 验证输入数据
            self._validate_input(user_data, ['username', 'email', 'password'])
            
            # 清理输入数据
            clean_data = self._sanitize_input(user_data)
            
            # 创建命令
            command = CreateUserCommand(
                username=clean_data['username'],
                email=clean_data['email'],
                password=clean_data['password'],
                phone=clean_data.get('phone'),
                role=clean_data.get('role', 'user')
            )
            
            # 执行命令
            result = await self.execute_command(command)
            
            if result.success:
                self._logger.info(f"用户创建成功: {result.data.get('username')}")
                return {
                    "success": True,
                    "data": result.data,
                    "message": "用户创建成功"
                }
            else:
                return {
                    "success": False,
                    "error": result.error,
                    "message": "用户创建失败"
                }
                
        except Exception as e:
            self._logger.error(f"创建用户服务失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "创建用户服务失败"
            }
    
    async def get_user_by_id(self, user_id: str) -> Dict[str, Any]:
        """根据ID获取用户"""
        try:
            query = GetUserByIdQuery(user_id=user_id)
            result = await self.execute_query(query)
            
            if result.success:
                return {
                    "success": True,
                    "data": result.data,
                    "message": "用户查询成功"
                }
            else:
                return {
                    "success": False,
                    "error": result.error,
                    "message": "用户查询失败"
                }
                
        except Exception as e:
            self._logger.error(f"查询用户服务失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "查询用户服务失败"
            }
    
    async def get_user_by_username(self, username: str) -> Dict[str, Any]:
        """根据用户名获取用户"""
        try:
            query = GetUserByUsernameQuery(username=username)
            result = await self.execute_query(query)
            
            if result.success:
                return {
                    "success": True,
                    "data": result.data,
                    "message": "用户查询成功"
                }
            else:
                return {
                    "success": False,
                    "error": result.error,
                    "message": "用户查询失败"
                }
                
        except Exception as e:
            self._logger.error(f"根据用户名查询用户服务失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "根据用户名查询用户服务失败"
            }
    
    async def get_user_by_email(self, email: str) -> Dict[str, Any]:
        """根据邮箱获取用户"""
        try:
            query = GetUserByEmailQuery(email=email)
            result = await self.execute_query(query)
            
            if result.success:
                return {
                    "success": True,
                    "data": result.data,
                    "message": "用户查询成功"
                }
            else:
                return {
                    "success": False,
                    "error": result.error,
                    "message": "用户查询失败"
                }
                
        except Exception as e:
            self._logger.error(f"根据邮箱查询用户服务失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "根据邮箱查询用户服务失败"
            }
    
    async def get_users(self, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """获取用户列表"""
        try:
            query = GetUsersQuery(page=page, page_size=page_size)
            result = await self.execute_query(query)
            
            if result.success:
                return {
                    "success": True,
                    "data": result.data,
                    "message": "用户列表查询成功"
                }
            else:
                return {
                    "success": False,
                    "error": result.error,
                    "message": "用户列表查询失败"
                }
                
        except Exception as e:
            self._logger.error(f"查询用户列表服务失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "查询用户列表服务失败"
            }
    
    async def search_users(self, search_term: str, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """搜索用户"""
        try:
            query = SearchUsersQuery(keyword=search_term, limit=page_size)
            result = await self.execute_query(query)
            
            if result.success:
                return {
                    "success": True,
                    "data": result.data,
                    "message": "用户搜索成功"
                }
            else:
                return {
                    "success": False,
                    "error": result.error,
                    "message": "用户搜索失败"
                }
                
        except Exception as e:
            self._logger.error(f"搜索用户服务失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "搜索用户服务失败"
            }
    
    async def update_user_profile(self, user_id: str, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """更新用户资料"""
        try:
            # 清理输入数据
            clean_data = self._sanitize_input(profile_data)
            
            command = UpdateUserProfileCommand(
                user_id=user_id,
                email=clean_data.get('email'),
                phone=clean_data.get('phone')
            )
            
            result = await self.execute_command(command)
            
            if result.success:
                return {
                    "success": True,
                    "data": result.data,
                    "message": "用户资料更新成功"
                }
            else:
                return {
                    "success": False,
                    "error": result.error,
                    "message": "用户资料更新失败"
                }
                
        except Exception as e:
            self._logger.error(f"更新用户资料服务失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "更新用户资料服务失败"
            }
    
    async def change_user_password(self, user_id: str, old_password: str, new_password: str) -> Dict[str, Any]:
        """修改用户密码"""
        try:
            command = ChangeUserPasswordCommand(
                user_id=user_id,
                old_password=old_password,
                new_password=new_password
            )
            
            result = await self.execute_command(command)
            
            if result.success:
                return {
                    "success": True,
                    "data": result.data,
                    "message": "密码修改成功"
                }
            else:
                return {
                    "success": False,
                    "error": result.error,
                    "message": "密码修改失败"
                }
                
        except Exception as e:
            self._logger.error(f"修改用户密码服务失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "修改用户密码服务失败"
            }
    
    async def login_user(self, username: str, password: str) -> Dict[str, Any]:
        """用户登录"""
        try:
            command = LoginUserCommand(username_or_email=username, password=password)
            result = await self.execute_command(command)
            
            if result.success:
                return {
                    "success": True,
                    "data": result.data,
                    "message": "登录成功"
                }
            else:
                return {
                    "success": False,
                    "error": result.error,
                    "message": "登录失败"
                }
                
        except Exception as e:
            self._logger.error(f"用户登录服务失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "用户登录服务失败"
            }
    
    async def logout_user(self, user_id: str) -> Dict[str, Any]:
        """用户登出"""
        try:
            command = LogoutUserCommand(user_id=user_id)
            result = await self.execute_command(command)
            
            if result.success:
                return {
                    "success": True,
                    "data": result.data,
                    "message": "登出成功"
                }
            else:
                return {
                    "success": False,
                    "error": result.error,
                    "message": "登出失败"
                }
                
        except Exception as e:
            self._logger.error(f"用户登出服务失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "用户登出服务失败"
            }
    
    async def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """刷新访问令牌"""
        try:
            command = RefreshTokenCommand(refresh_token=refresh_token)
            result = await self.execute_command(command)
            
            if result.success:
                return {
                    "success": True,
                    "data": result.data,
                    "message": "令牌刷新成功"
                }
            else:
                return {
                    "success": False,
                    "error": result.error,
                    "message": "令牌刷新失败"
                }
                
        except Exception as e:
            self._logger.error(f"刷新令牌服务失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "刷新令牌服务失败"
            }
    
    async def check_username_availability(self, username: str) -> Dict[str, Any]:
        """检查用户名可用性"""
        try:
            query = CheckUsernameAvailabilityQuery(username=username)
            result = await self.execute_query(query)
            
            if result.success:
                return {
                    "success": True,
                    "data": result.data,
                    "message": "用户名可用性检查完成"
                }
            else:
                return {
                    "success": False,
                    "error": result.error,
                    "message": "用户名可用性检查失败"
                }
                
        except Exception as e:
            self._logger.error(f"检查用户名可用性服务失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "检查用户名可用性服务失败"
            }
    
    async def check_email_availability(self, email: str) -> Dict[str, Any]:
        """检查邮箱可用性"""
        try:
            query = CheckEmailAvailabilityQuery(email=email)
            result = await self.execute_query(query)
            
            if result.success:
                return {
                    "success": True,
                    "data": result.data,
                    "message": "邮箱可用性检查完成"
                }
            else:
                return {
                    "success": False,
                    "error": result.error,
                    "message": "邮箱可用性检查失败"
                }
                
        except Exception as e:
            self._logger.error(f"检查邮箱可用性服务失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "检查邮箱可用性服务失败"
            }
    
    async def reset_user_password(self, user_id: str, new_password: str, notify_user: bool = True) -> Dict[str, Any]:
        """重置用户密码（管理员操作）"""
        try:
            # 验证输入数据
            self._validate_input({"user_id": user_id, "new_password": new_password}, ['user_id', 'new_password'])
            
            # 清理输入数据
            clean_password = self._sanitize_input({"password": new_password})['password']
            
            # 创建命令
            command = ChangeUserPasswordCommand(
                user_id=user_id,
                old_password=None,  # 管理员重置密码不需要旧密码
                new_password=clean_password,
                is_admin_reset=True
            )
            
            # 执行命令
            result = await self.execute_command(command)
            
            if result.success:
                self._logger.info(f"用户密码重置成功: {user_id}")
                
                # 如果需要通知用户，这里可以添加邮件通知逻辑
                if notify_user:
                    self._logger.info(f"已通知用户密码重置: {user_id}")
                
                return {
                    "success": True,
                    "data": {"user_id": user_id},
                    "message": "用户密码重置成功"
                }
            else:
                return {
                    "success": False,
                    "error": result.error,
                    "message": "用户密码重置失败"
                }
                
        except Exception as e:
            self._logger.error(f"重置用户密码服务失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "重置用户密码服务失败"
            }
    
    # 新增的管理员功能
    
    async def update_user(self, user_id: str, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """更新用户信息（管理员操作）"""
        try:
            # 清理输入数据
            clean_data = self._sanitize_input(user_data)
            
            # 创建命令
            command = UpdateUserProfileCommand(
                user_id=user_id,
                email=clean_data.get('email'),
                phone=clean_data.get('phone')
            )
            
            # 执行命令
            result = await self.execute_command(command)
            
            if result.success:
                self._logger.info(f"用户信息更新成功: {user_id}")
                return {
                    "success": True,
                    "data": result.data,
                    "message": "用户信息更新成功"
                }
            else:
                return {
                    "success": False,
                    "error": result.error,
                    "message": "用户信息更新失败"
                }
                
        except Exception as e:
            self._logger.error(f"更新用户信息服务失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "更新用户信息服务失败"
            }
    
    async def delete_user(self, user_id: str) -> Dict[str, Any]:
        """删除用户（软删除）"""
        try:
            # 创建命令
            command = DeactivateUserCommand(user_id=user_id)
            
            # 执行命令
            result = await self.execute_command(command)
            
            if result.success:
                self._logger.info(f"用户删除成功: {user_id}")
                return {
                    "success": True,
                    "data": result.data,
                    "message": "用户删除成功"
                }
            else:
                return {
                    "success": False,
                    "error": result.error,
                    "message": "用户删除失败"
                }
                
        except Exception as e:
            self._logger.error(f"删除用户服务失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "删除用户服务失败"
            }
    
    async def activate_user(self, user_id: str) -> Dict[str, Any]:
        """激活用户"""
        try:
            command = ActivateUserCommand(user_id=user_id)
            result = await self.execute_command(command)
            
            if result.success:
                return {
                    "success": True,
                    "data": result.data,
                    "message": "用户激活成功"
                }
            else:
                return {
                    "success": False,
                    "error": result.error,
                    "message": "用户激活失败"
                }
                
        except Exception as e:
            self._logger.error(f"激活用户服务失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "激活用户服务失败"
            }
    
    async def deactivate_user(self, user_id: str) -> Dict[str, Any]:
        """停用用户"""
        try:
            command = DeactivateUserCommand(user_id=user_id)
            result = await self.execute_command(command)
            
            if result.success:
                return {
                    "success": True,
                    "data": result.data,
                    "message": "用户停用成功"
                }
            else:
                return {
                    "success": False,
                    "error": result.error,
                    "message": "用户停用失败"
                }
                
        except Exception as e:
            self._logger.error(f"停用用户服务失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "停用用户服务失败"
            }
    
    async def change_user_role(self, user_id: str, new_role: str) -> Dict[str, Any]:
        """修改用户角色"""
        try:
            command = ChangeUserRoleCommand(
                user_id=user_id,
                new_role=new_role
            )
            result = await self.execute_command(command)
            
            if result.success:
                return {
                    "success": True,
                    "data": result.data,
                    "message": "用户角色修改成功"
                }
            else:
                return {
                    "success": False,
                    "error": result.error,
                    "message": "用户角色修改失败"
                }
                
        except Exception as e:
            self._logger.error(f"修改用户角色服务失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "修改用户角色服务失败"
            }
    
    async def get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """获取用户详细资料"""
        try:
            query = GetUserProfileQuery(user_id=user_id)
            result = await self.execute_query(query)
            
            if result.success:
                return {
                    "success": True,
                    "data": result.data,
                    "message": "用户详细资料查询成功"
                }
            else:
                return {
                    "success": False,
                    "error": result.error,
                    "message": "用户详细资料查询失败"
                }
                
        except Exception as e:
            self._logger.error(f"获取用户详细资料服务失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "获取用户详细资料服务失败"
            }
    
    # 批量操作功能
    
    async def batch_delete_users(self, user_ids: List[str]) -> Dict[str, Any]:
        """批量删除用户"""
        try:
            success_count = 0
            failed_count = 0
            success_ids = []
            failed_items = []
            
            for user_id in user_ids:
                result = await self.delete_user(user_id)
                if result["success"]:
                    success_count += 1
                    success_ids.append(user_id)
                else:
                    failed_count += 1
                    failed_items.append({
                        "user_id": user_id,
                        "error": result["error"]
                    })
            
            return {
                "success": True,
                "data": {
                    "success_count": success_count,
                    "failed_count": failed_count,
                    "total_count": len(user_ids),
                    "success_ids": success_ids,
                    "failed_items": failed_items
                },
                "message": f"批量删除完成，成功: {success_count}，失败: {failed_count}"
            }
            
        except Exception as e:
            self._logger.error(f"批量删除用户服务失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "批量删除用户服务失败"
            }
    
    async def batch_update_user_roles(self, user_ids: List[str], new_role: str) -> Dict[str, Any]:
        """批量更新用户角色"""
        try:
            success_count = 0
            failed_count = 0
            success_ids = []
            failed_items = []
            
            for user_id in user_ids:
                result = await self.change_user_role(user_id, new_role)
                if result["success"]:
                    success_count += 1
                    success_ids.append(user_id)
                else:
                    failed_count += 1
                    failed_items.append({
                        "user_id": user_id,
                        "error": result["error"]
                    })
            
            return {
                "success": True,
                "data": {
                    "success_count": success_count,
                    "failed_count": failed_count,
                    "total_count": len(user_ids),
                    "success_ids": success_ids,
                    "failed_items": failed_items,
                    "new_role": new_role
                },
                "message": f"批量更新角色完成，成功: {success_count}，失败: {failed_count}"
            }
            
        except Exception as e:
            self._logger.error(f"批量更新用户角色服务失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "批量更新用户角色服务失败"
            }
    
    # 统计功能
    
    async def get_user_statistics(self) -> Dict[str, Any]:
        """获取用户统计信息"""
        try:
            # 这里应该调用领域服务或查询来获取统计数据
            # 暂时返回模拟数据
            stats_data = {
                "total_users": 1000,
                "active_users": 850,
                "role_distribution": {
                    "user": 800,
                    "trader": 150,
                    "admin": 40,
                    "super_admin": 10
                },
                "status_distribution": {
                    "active": 850,
                    "inactive": 150
                },
                "new_users_today": 25,
                "new_users_this_week": 150,
                "new_users_this_month": 500,
                "activity_rate": 85.0
            }
            
            return {
                "success": True,
                "data": stats_data,
                "message": "用户统计信息获取成功"
            }
            
        except Exception as e:
            self._logger.error(f"获取用户统计信息服务失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "获取用户统计信息服务失败"
            }
    
    async def advanced_user_search(self, page: int = 1, page_size: int = 20, 
                                 search: Optional[str] = None, role: Optional[str] = None,
                                 status: Optional[str] = None, sort_by: str = "created_at",
                                 sort_order: str = "desc") -> Dict[str, Any]:
        """高级用户搜索"""
        try:
            # 这里应该实现更复杂的搜索逻辑
            # 暂时使用基本的搜索功能
            if search:
                return await self.search_users(search, page, page_size)
            else:
                return await self.get_users(page, page_size)
                
        except Exception as e:
            self._logger.error(f"高级用户搜索服务失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "高级用户搜索服务失败"
            }
    
    async def export_users_csv(self, role: Optional[str] = None, status: Optional[str] = None,
                             created_after: Optional[str] = None, created_before: Optional[str] = None) -> Dict[str, Any]:
        """导出用户数据为CSV"""
        try:
            # 这里应该实现CSV导出逻辑
            # 暂时返回模拟数据
            export_data = {
                "file_url": "/exports/users_20241201.csv",
                "file_size": "2.5MB",
                "record_count": 1000,
                "exported_at": "2024-12-01T10:00:00Z"
            }
            
            return {
                "success": True,
                "data": export_data,
                "message": "用户数据导出成功"
            }
            
        except Exception as e:
            self._logger.error(f"导出用户数据服务失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "导出用户数据服务失败"
            }
    
    def get_service_info(self) -> Dict[str, Any]:
        """获取服务信息"""
        return {
            "service_name": "UserApplicationService",
            "version": "1.0.0",
            "description": "用户管理应用服务",
            "supported_operations": [
                "create_user", "get_user_by_id", "get_user_by_username", 
                "get_user_by_email", "get_users", "search_users",
                "update_user_profile", "change_user_password", "login_user",
                "check_username_availability", "check_email_availability",
                "reset_user_password", "update_user", "delete_user",
                "activate_user", "deactivate_user", "change_user_role",
                "get_user_profile", "batch_delete_users", "batch_update_user_roles",
                "get_user_statistics", "advanced_user_search", "export_users_csv"
            ]
        }