"""
用户相关查询定义
实现用户数据查询的查询模式
"""

# 标准库导入
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict, Any

# 核心层导入
from ...core.common.enums.user_roles import UserRole, UserStatus

# 应用层内部导入
from .base_query import BaseQuery, PaginatedQuery


@dataclass
class GetUserByIdQuery(BaseQuery):
    """根据ID获取用户"""
    user_id: str = None


@dataclass
class GetUserByUsernameQuery(BaseQuery):
    """根据用户名获取用户"""
    username: str = None


@dataclass
class GetUserByEmailQuery(BaseQuery):
    """根据邮箱获取用户"""
    email: str = None


@dataclass
class GetUsersQuery(PaginatedQuery):
    """获取用户列表"""
    role: Optional[UserRole] = None
    status: Optional[UserStatus] = None
    search: Optional[str] = None  # 搜索用户名、邮箱、全名
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    last_login_after: Optional[datetime] = None
    last_login_before: Optional[datetime] = None
    sort_by: str = "created_at"
    sort_order: str = "desc"


@dataclass
class SearchUsersQuery(BaseQuery):
    """搜索用户"""
    keyword: str = None
    limit: int = 10
    include_inactive: bool = False


@dataclass
class GetUserPermissionsQuery(BaseQuery):
    """获取用户权限"""
    user_id: str = None


@dataclass
class GetUserSessionsQuery(BaseQuery):
    """获取用户会话"""
    user_id: str = None
    active_only: bool = True


@dataclass
class GetUserActivityLogQuery(PaginatedQuery):
    """获取用户活动日志"""
    user_id: str = None
    action: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


@dataclass
class ValidateUserCredentialsQuery(BaseQuery):
    """验证用户凭据"""
    username_or_email: str = None
    password: str = None


@dataclass
class CheckUsernameAvailabilityQuery(BaseQuery):
    """检查用户名可用性"""
    username: str = None


@dataclass
class CheckEmailAvailabilityQuery(BaseQuery):
    """检查邮箱可用性"""
    email: str = None


@dataclass
class GetUserStatisticsQuery(BaseQuery):
    """获取用户统计信息"""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    group_by: str = "day"  # day, week, month


@dataclass
class GetOnlineUsersQuery(BaseQuery):
    """获取在线用户"""
    last_active_minutes: int = 30


@dataclass
class GetRecentlyRegisteredUsersQuery(BaseQuery):
    """获取最近注册的用户"""
    days: int = 7
    limit: int = 20


@dataclass
class GetUserProfileQuery(BaseQuery):
    """获取用户资料"""
    user_id: str = None
    include_sensitive: bool = False  # 是否包含敏感信息


@dataclass
class GetUserPreferencesQuery(BaseQuery):
    """获取用户偏好设置"""
    user_id: str = None


@dataclass
class GetUserRolesQuery(BaseQuery):
    """获取用户角色列表"""
    include_permissions: bool = False
