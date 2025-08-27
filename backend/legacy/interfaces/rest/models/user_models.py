"""
用户API模型
===========

定义用户相关的API请求和响应模型
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, EmailStr, validator
from datetime import datetime


class CreateUserRequest(BaseModel):
    """创建用户请求模型"""
    
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: EmailStr = Field(..., description="邮箱地址")
    password: str = Field(..., min_length=6, max_length=128, description="密码")
    phone: Optional[str] = Field(None, description="手机号码")
    role: Optional[str] = Field("user", description="用户角色")
    
    @validator('username')
    def validate_username(cls, v):
        if not v.isalnum() and '_' not in v:
            raise ValueError('用户名只能包含字母、数字和下划线')
        return v
    
    @validator('phone')
    def validate_phone(cls, v):
        if v and not v.startswith('+'):
            raise ValueError('手机号码必须包含国家代码，如+86')
        return v


class UpdateUserProfileRequest(BaseModel):
    """更新用户资料请求模型"""
    
    email: Optional[EmailStr] = Field(None, description="邮箱地址")
    phone: Optional[str] = Field(None, description="手机号码")
    
    @validator('phone')
    def validate_phone(cls, v):
        if v and not v.startswith('+'):
            raise ValueError('手机号码必须包含国家代码，如+86')
        return v


class ChangePasswordRequest(BaseModel):
    """修改密码请求模型"""
    
    old_password: str = Field(..., description="原密码")
    new_password: str = Field(..., min_length=6, max_length=128, description="新密码")
    confirm_password: str = Field(..., description="确认新密码")
    
    @validator('confirm_password')
    def passwords_match(cls, v, values, **kwargs):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('新密码和确认密码不匹配')
        return v


class LoginRequest(BaseModel):
    """登录请求模型"""
    
    username_or_email: str = Field(..., description="用户名或邮箱")
    password: str = Field(..., description="密码")
    remember_me: bool = Field(False, description="记住我")
    client_info: Optional[dict] = Field(None, description="客户端信息")


class RefreshTokenRequest(BaseModel):
    """刷新令牌请求模型"""
    
    refresh_token: str = Field(..., description="刷新令牌")


class UserResponse(BaseModel):
    """用户响应模型"""
    
    id: str = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    email: str = Field(..., description="邮箱地址")
    phone: Optional[str] = Field(None, description="手机号码")
    role: str = Field(..., description="用户角色")
    is_active: bool = Field(..., description="是否激活")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class UserProfileResponse(BaseModel):
    """用户详细资料响应模型"""
    
    id: str = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    email: str = Field(..., description="邮箱地址")
    phone: Optional[str] = Field(None, description="手机号码")
    role: str = Field(..., description="用户角色")
    is_active: bool = Field(..., description="是否激活")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    last_login: Optional[datetime] = Field(None, description="最后登录时间")
    profile: Optional[dict] = Field(None, description="扩展资料")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class UsersListResponse(BaseModel):
    """用户列表响应模型"""
    
    users: List[UserResponse] = Field(..., description="用户列表")
    total_count: int = Field(..., description="总数量")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="页面大小")
    total_pages: int = Field(..., description="总页数")


class LoginResponse(BaseModel):
    """登录响应模型"""
    
    access_token: str = Field(..., description="访问令牌")
    refresh_token: str = Field(..., description="刷新令牌")
    token_type: str = Field(default="Bearer", description="令牌类型")
    expires_in: int = Field(..., description="访问令牌有效期(秒)")
    user: UserResponse = Field(..., description="用户信息")
    login_time: datetime = Field(default_factory=lambda: datetime.now(), description="登录时间")
    permissions: List[str] = Field(default=[], description="用户权限")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class RefreshTokenRequest(BaseModel):
    """刷新令牌请求模型"""
    
    refresh_token: str = Field(..., description="刷新令牌")


class RefreshTokenResponse(BaseModel):
    """刷新令牌响应模型"""
    
    access_token: str = Field(..., description="新的访问令牌")
    refresh_token: str = Field(..., description="新的刷新令牌")
    token_type: str = Field(default="Bearer", description="令牌类型")
    expires_in: int = Field(..., description="访问令牌有效期(秒)")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class LogoutRequest(BaseModel):
    """登出请求模型"""
    
    refresh_token: Optional[str] = Field(None, description="刷新令牌")
    logout_all_devices: bool = Field(False, description="是否登出所有设备")


class LogoutResponse(BaseModel):
    """登出响应模型"""
    
    message: str = Field(default="成功登出", description="响应消息")
    logout_time: datetime = Field(default_factory=lambda: datetime.now(), description="登出时间")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class TokenValidationRequest(BaseModel):
    """令牌验证请求模型"""
    
    token: str = Field(..., description="待验证的令牌")
    token_type: str = Field(default="access", description="令牌类型")


class TokenValidationResponse(BaseModel):
    """令牌验证响应模型"""
    
    is_valid: bool = Field(..., description="令牌是否有效")
    user_id: Optional[str] = Field(None, description="用户ID")
    username: Optional[str] = Field(None, description="用户名")
    expires_at: Optional[datetime] = Field(None, description="过期时间")
    scopes: List[str] = Field(default=[], description="令牌权限范围")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class AvailabilityCheckResponse(BaseModel):
    """可用性检查响应模型"""
    
    field_name: str = Field(..., description="字段名称")
    field_value: str = Field(..., description="字段值")
    is_available: bool = Field(..., description="是否可用")
    checked_at: datetime = Field(..., description="检查时间")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# 新增的扩展模型

class UpdateUserRequest(BaseModel):
    """更新用户请求模型"""
    
    username: Optional[str] = Field(None, description="用户名")
    email: Optional[str] = Field(None, description="邮箱")
    first_name: Optional[str] = Field(None, description="名")
    last_name: Optional[str] = Field(None, description="姓")
    phone: Optional[str] = Field(None, description="手机号")
    avatar_url: Optional[str] = Field(None, description="头像URL")
    bio: Optional[str] = Field(None, description="个人简介")
    timezone: Optional[str] = Field(None, description="时区")
    language: Optional[str] = Field(None, description="语言偏好")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ChangePasswordRequest(BaseModel):
    """修改密码请求模型"""
    
    current_password: str = Field(..., description="当前密码")
    new_password: str = Field(..., description="新密码")
    confirm_password: str = Field(..., description="确认新密码")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ResetPasswordRequest(BaseModel):
    """重置密码请求模型"""
    
    email: str = Field(..., description="邮箱地址")
    reset_token: Optional[str] = Field(None, description="重置令牌")
    new_password: Optional[str] = Field(None, description="新密码")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class UserSessionInfo(BaseModel):
    """用户会话信息模型"""
    
    session_id: str = Field(..., description="会话ID")
    user_id: str = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    ip_address: str = Field(..., description="IP地址")
    user_agent: str = Field(..., description="用户代理")
    login_time: datetime = Field(..., description="登录时间")
    last_activity: datetime = Field(..., description="最后活动时间")
    is_active: bool = Field(..., description="是否活跃")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class UserSessionsResponse(BaseModel):
    """用户会话列表响应模型"""
    
    sessions: List[UserSessionInfo] = Field(..., description="会话列表")
    total_count: int = Field(..., description="总会话数")
    active_count: int = Field(..., description="活跃会话数")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class UserActivityLog(BaseModel):
    """用户活动日志模型"""
    
    log_id: str = Field(..., description="日志ID")
    user_id: str = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    activity_type: str = Field(..., description="活动类型")
    activity_description: str = Field(..., description="活动描述")
    ip_address: str = Field(..., description="IP地址")
    user_agent: str = Field(..., description="用户代理")
    timestamp: datetime = Field(..., description="时间戳")
    metadata: Dict[str, Any] = Field(default={}, description="元数据")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class UserActivityResponse(BaseModel):
    """用户活动响应模型"""
    
    activities: List[UserActivityLog] = Field(..., description="活动列表")
    total_count: int = Field(..., description="总活动数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="页面大小")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class UserPreferences(BaseModel):
    """用户偏好设置模型"""
    
    theme: str = Field(default="light", description="主题")
    language: str = Field(default="zh-CN", description="语言")
    timezone: str = Field(default="Asia/Shanghai", description="时区")
    date_format: str = Field(default="YYYY-MM-DD", description="日期格式")
    time_format: str = Field(default="24h", description="时间格式")
    currency: str = Field(default="CNY", description="货币")
    notifications: Dict[str, bool] = Field(default={}, description="通知设置")
    trading_preferences: Dict[str, Any] = Field(default={}, description="交易偏好")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class UpdatePreferencesRequest(BaseModel):
    """更新偏好设置请求模型"""
    
    theme: Optional[str] = Field(None, description="主题")
    language: Optional[str] = Field(None, description="语言")
    timezone: Optional[str] = Field(None, description="时区")
    date_format: Optional[str] = Field(None, description="日期格式")
    time_format: Optional[str] = Field(None, description="时间格式")
    currency: Optional[str] = Field(None, description="货币")
    notifications: Optional[Dict[str, bool]] = Field(None, description="通知设置")
    trading_preferences: Optional[Dict[str, Any]] = Field(None, description="交易偏好")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class UserStatistics(BaseModel):
    """用户统计信息模型"""
    
    total_login_count: int = Field(..., description="总登录次数")
    last_login_date: Optional[datetime] = Field(None, description="最后登录日期")
    total_trading_days: int = Field(..., description="总交易天数")
    total_orders: int = Field(..., description="总订单数")
    successful_orders: int = Field(..., description="成功订单数")
    total_volume: float = Field(..., description="总交易量")
    total_pnl: float = Field(..., description="总盈亏")
    win_rate: float = Field(..., description="胜率")
    average_holding_time: float = Field(..., description="平均持仓时间")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class UserDashboardData(BaseModel):
    """用户仪表板数据模型"""
    
    user_info: UserResponse = Field(..., description="用户信息")
    statistics: UserStatistics = Field(..., description="统计信息")
    recent_activities: List[UserActivityLog] = Field(..., description="最近活动")
    active_sessions: int = Field(..., description="活跃会话数")
    system_notifications: List[Dict[str, Any]] = Field(default=[], description="系统通知")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class AdminUpdateUserRequest(BaseModel):
    """更新用户信息请求模型（管理员用）"""
    
    username: Optional[str] = Field(None, min_length=3, max_length=50, description="用户名")
    email: Optional[EmailStr] = Field(None, description="邮箱地址")
    full_name: Optional[str] = Field(None, max_length=100, description="全名")
    phone: Optional[str] = Field(None, description="手机号码")
    role: Optional[str] = Field(None, description="用户角色")
    status: Optional[str] = Field(None, description="用户状态")
    avatar_url: Optional[str] = Field(None, description="头像URL")
    
    @validator('username')
    def validate_username(cls, v):
        if v and (not v.isalnum() and '_' not in v):
            raise ValueError('用户名只能包含字母、数字和下划线')
        return v
    
    @validator('phone')
    def validate_phone(cls, v):
        if v and not v.startswith('+'):
            raise ValueError('手机号码必须包含国家代码，如+86')
        return v


class ChangeRoleRequest(BaseModel):
    """修改用户角色请求模型"""
    
    new_role: str = Field(..., description="新角色")
    reason: Optional[str] = Field(None, description="修改原因")
    
    @validator('new_role')
    def validate_role(cls, v):
        valid_roles = ['user', 'trader', 'admin', 'super_admin']
        if v not in valid_roles:
            raise ValueError(f'角色必须是以下之一: {", ".join(valid_roles)}')
        return v


class AdminResetPasswordRequest(BaseModel):
    """管理员重置密码请求模型"""
    
    new_password: str = Field(..., min_length=6, max_length=128, description="新密码")
    notify_user: bool = Field(True, description="是否通知用户")


class BatchDeleteRequest(BaseModel):
    """批量删除用户请求模型"""
    
    user_ids: List[str] = Field(..., min_items=1, max_items=100, description="用户ID列表")
    reason: Optional[str] = Field(None, description="删除原因")


class BatchUpdateRoleRequest(BaseModel):
    """批量更新角色请求模型"""
    
    user_ids: List[str] = Field(..., min_items=1, max_items=100, description="用户ID列表")
    new_role: str = Field(..., description="新角色")
    reason: Optional[str] = Field(None, description="更新原因")
    
    @validator('new_role')
    def validate_role(cls, v):
        valid_roles = ['user', 'trader', 'admin', 'super_admin']
        if v not in valid_roles:
            raise ValueError(f'角色必须是以下之一: {", ".join(valid_roles)}')
        return v


class UserStatisticsResponse(BaseModel):
    """用户统计信息响应模型"""
    
    total_users: int = Field(..., description="总用户数")
    active_users: int = Field(..., description="活跃用户数")
    role_distribution: dict = Field(..., description="角色分布")
    status_distribution: dict = Field(..., description="状态分布")
    new_users_today: int = Field(..., description="今日新用户")
    new_users_this_week: int = Field(..., description="本周新用户")
    new_users_this_month: int = Field(..., description="本月新用户")
    activity_rate: float = Field(..., description="活跃率(%)")
    growth_trends: Optional[dict] = Field(None, description="增长趋势")


class AdvancedSearchRequest(BaseModel):
    """高级搜索请求模型"""
    
    search: Optional[str] = Field(None, description="搜索关键词")
    role: Optional[str] = Field(None, description="用户角色")
    status: Optional[str] = Field(None, description="用户状态")
    created_after: Optional[datetime] = Field(None, description="创建时间之后")
    created_before: Optional[datetime] = Field(None, description="创建时间之前")
    last_login_after: Optional[datetime] = Field(None, description="最后登录之后")
    last_login_before: Optional[datetime] = Field(None, description="最后登录之前")
    sort_by: str = Field("created_at", description="排序字段")
    sort_order: str = Field("desc", description="排序方向")
    
    @validator('sort_order')
    def validate_sort_order(cls, v):
        if v.lower() not in ['asc', 'desc']:
            raise ValueError('排序方向必须是 asc 或 desc')
        return v.lower()


class ExportUsersRequest(BaseModel):
    """导出用户数据请求模型"""
    
    format: str = Field("csv", description="导出格式")
    role: Optional[str] = Field(None, description="用户角色")
    status: Optional[str] = Field(None, description="用户状态")
    created_after: Optional[datetime] = Field(None, description="创建时间之后")
    created_before: Optional[datetime] = Field(None, description="创建时间之前")
    include_fields: List[str] = Field(
        default=["id", "username", "email", "role", "status", "created_at"],
        description="包含的字段"
    )
    
    @validator('format')
    def validate_format(cls, v):
        if v.lower() not in ['csv', 'excel', 'json']:
            raise ValueError('导出格式必须是 csv, excel 或 json')
        return v.lower()


class UserDetailedResponse(BaseModel):
    """用户详细信息响应模型"""
    
    id: str = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    email: str = Field(..., description="邮箱地址")
    full_name: Optional[str] = Field(None, description="全名")
    phone: Optional[str] = Field(None, description="手机号码")
    avatar_url: Optional[str] = Field(None, description="头像URL")
    role: str = Field(..., description="用户角色")
    status: str = Field(..., description="用户状态")
    email_verified: bool = Field(..., description="邮箱是否验证")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    last_login_at: Optional[datetime] = Field(None, description="最后登录时间")
    login_count: Optional[int] = Field(None, description="登录次数")
    preferences: Optional[dict] = Field(None, description="用户偏好")
    metadata: Optional[dict] = Field(None, description="额外元数据")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class BulkOperationResponse(BaseModel):
    """批量操作响应模型"""
    
    success_count: int = Field(..., description="成功数量")
    failed_count: int = Field(..., description="失败数量")
    total_count: int = Field(..., description="总数量")
    success_ids: List[str] = Field(..., description="成功的用户ID列表")
    failed_items: List[dict] = Field(..., description="失败的项目列表")
    operation_id: Optional[str] = Field(None, description="操作ID")
    
    
class UserActivityLog(BaseModel):
    """用户活动日志模型"""
    
    user_id: str = Field(..., description="用户ID")
    action: str = Field(..., description="操作类型")
    timestamp: datetime = Field(..., description="时间戳")
    ip_address: Optional[str] = Field(None, description="IP地址")
    user_agent: Optional[str] = Field(None, description="用户代理")
    details: Optional[dict] = Field(None, description="详细信息")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class UserPreferencesRequest(BaseModel):
    """用户偏好设置请求模型"""
    
    theme: Optional[str] = Field(None, description="主题")
    language: Optional[str] = Field(None, description="语言")
    timezone: Optional[str] = Field(None, description="时区")
    notifications: Optional[dict] = Field(None, description="通知设置")
    dashboard_layout: Optional[dict] = Field(None, description="仪表板布局")
    trading_preferences: Optional[dict] = Field(None, description="交易偏好")


class UserSecuritySettings(BaseModel):
    """用户安全设置模型"""
    
    two_factor_enabled: bool = Field(False, description="是否启用双因子认证")
    login_notifications: bool = Field(True, description="登录通知")
    session_timeout: int = Field(3600, description="会话超时时间(秒)")
    allowed_ip_ranges: List[str] = Field(default=[], description="允许的IP范围")
    password_expiry_days: Optional[int] = Field(None, description="密码过期天数")


class UserPermissionsResponse(BaseModel):
    """用户权限响应模型"""
    
    user_id: str = Field(..., description="用户ID")
    role: str = Field(..., description="用户角色")
    permissions: List[str] = Field(..., description="权限列表")
    resource_permissions: dict = Field(..., description="资源权限")
    effective_permissions: List[str] = Field(..., description="有效权限")
    
    
class CreateUserBatchRequest(BaseModel):
    """批量创建用户请求模型"""
    
    users: List[CreateUserRequest] = Field(..., min_items=1, max_items=50, description="用户列表")
    send_welcome_email: bool = Field(True, description="发送欢迎邮件")
    default_role: str = Field("user", description="默认角色")
    
    @validator('default_role')
    def validate_role(cls, v):
        valid_roles = ['user', 'trader', 'admin']
        if v not in valid_roles:
            raise ValueError(f'默认角色必须是以下之一: {", ".join(valid_roles)}')
        return v