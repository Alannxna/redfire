"""
认证系统集成模块
================

提供FastAPI应用的认证中间件集成和使用示例
"""

import asyncio
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel

from .enhanced_auth_middleware import (
    EnhancedAuthMiddleware, SecurityConfig, UserContext, JWTManager,
    SessionManager, TokenType, UserRole, Permission,
    get_current_user, require_permission, require_role
)
from .auth_config import AuthConfig, get_auth_config


# 数据模型
class LoginRequest(BaseModel):
    """登录请求模型"""
    username: str
    password: str
    remember_me: bool = False


class LoginResponse(BaseModel):
    """登录响应模型"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user_info: Dict[str, Any]


class RefreshTokenRequest(BaseModel):
    """刷新令牌请求模型"""
    refresh_token: str


class UserRegistrationRequest(BaseModel):
    """用户注册请求模型"""
    username: str
    email: str
    password: str
    confirm_password: str
    role: str = "trader"


class PasswordChangeRequest(BaseModel):
    """密码修改请求模型"""
    current_password: str
    new_password: str
    confirm_password: str


# 认证服务类
class AuthService:
    """认证服务"""
    
    def __init__(self, config: Optional[SecurityConfig] = None):
        self.config = config or SecurityConfig()
        self.jwt_manager = JWTManager(self.config)
        self.session_manager = None
        self.logger = logging.getLogger(f"{__name__}.AuthService")
        
        # 模拟用户数据库
        self._users_db = {
            "admin": {
                "user_id": "admin_001",
                "username": "admin",
                "email": "admin@redfire.com",
                "password_hash": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewKyNnm7CKtF/XKi",  # "admin123"
                "roles": ["super_admin"],
                "is_active": True,
                "created_at": "2024-01-01T00:00:00Z"
            },
            "trader001": {
                "user_id": "trader_001",
                "username": "trader001", 
                "email": "trader001@redfire.com",
                "password_hash": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewKyNnm7CKtF/XKi",  # "trader123"
                "roles": ["trader"],
                "is_active": True,
                "created_at": "2024-01-01T00:00:00Z"
            },
            "analyst001": {
                "user_id": "analyst_001",
                "username": "analyst001",
                "email": "analyst001@redfire.com", 
                "password_hash": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewKyNnm7CKtF/XKi",  # "analyst123"
                "roles": ["analyst"],
                "is_active": True,
                "created_at": "2024-01-01T00:00:00Z"
            }
        }
    
    async def initialize(self, redis_client=None):
        """初始化服务"""
        self.session_manager = SessionManager(redis_client, self.config)
    
    async def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """认证用户"""
        user = self._users_db.get(username)
        if not user:
            return None
        
        if not user.get("is_active", False):
            return None
        
        # 这里应该验证密码哈希，暂时简化处理
        if password in ["admin123", "trader123", "analyst123"]:
            return user
        
        return None
    
    async def login(self, username: str, password: str, request_info: Dict[str, Any]) -> LoginResponse:
        """用户登录"""
        # 认证用户
        user = await self.authenticate_user(username, password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误"
            )
        
        # 创建会话
        now = datetime.utcnow()
        user_context = UserContext(
            user_id=user["user_id"],
            username=user["username"],
            email=user["email"],
            roles=[UserRole(role) for role in user["roles"]],
            permissions=set(),  # 权限将由RBAC管理器计算
            session_id="",
            login_time=now,
            last_activity=now,
            ip_address=request_info.get("ip_address", ""),
            user_agent=request_info.get("user_agent", "")
        )
        
        session_id = await self.session_manager.create_session(user_context)
        
        # 创建JWT令牌
        token_data = {
            "user_id": user["user_id"],
            "username": user["username"],
            "email": user["email"],
            "roles": user["roles"],
            "session_id": session_id
        }
        
        access_token = self.jwt_manager.create_token(token_data, TokenType.ACCESS)
        refresh_token = self.jwt_manager.create_token(token_data, TokenType.REFRESH)
        
        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=self.config.access_token_expire_minutes * 60,
            user_info={
                "user_id": user["user_id"],
                "username": user["username"],
                "email": user["email"],
                "roles": user["roles"]
            }
        )
    
    async def refresh_token(self, refresh_token: str) -> LoginResponse:
        """刷新访问令牌"""
        # 验证刷新令牌
        payload = self.jwt_manager.verify_token(refresh_token, TokenType.REFRESH)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的刷新令牌"
            )
        
        # 获取用户信息
        username = payload.get("username")
        user = self._users_db.get(username)
        if not user or not user.get("is_active"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户不存在或已禁用"
            )
        
        # 创建新的访问令牌
        token_data = {
            "user_id": user["user_id"],
            "username": user["username"],
            "email": user["email"],
            "roles": user["roles"],
            "session_id": payload.get("session_id")
        }
        
        access_token = self.jwt_manager.create_token(token_data, TokenType.ACCESS)
        
        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,  # 保持原刷新令牌
            expires_in=self.config.access_token_expire_minutes * 60,
            user_info={
                "user_id": user["user_id"],
                "username": user["username"],
                "email": user["email"],
                "roles": user["roles"]
            }
        )
    
    async def logout(self, user_context: UserContext):
        """用户登出"""
        if self.session_manager and user_context.session_id:
            await self.session_manager.revoke_session(user_context.session_id)
    
    async def logout_all_sessions(self, user_id: str):
        """登出用户所有会话"""
        if self.session_manager:
            await self.session_manager.revoke_all_user_sessions(user_id)


# FastAPI应用集成函数
def setup_auth_middleware(app: FastAPI, config: Optional[SecurityConfig] = None) -> EnhancedAuthMiddleware:
    """设置认证中间件"""
    middleware = EnhancedAuthMiddleware(app, config)
    app.add_middleware(EnhancedAuthMiddleware, config=config)
    return middleware


def create_auth_routes(auth_service: AuthService) -> FastAPI:
    """创建认证相关路由"""
    from fastapi import APIRouter
    
    router = APIRouter(prefix="/api/v1/auth", tags=["认证"])
    
    @router.post("/login", response_model=LoginResponse)
    async def login(
        login_data: LoginRequest,
        request: Any = None  # 实际使用时应该是 Request 类型
    ):
        """用户登录"""
        request_info = {
            "ip_address": "127.0.0.1",  # 实际应从request获取
            "user_agent": "Test Client"
        }
        
        return await auth_service.login(
            login_data.username,
            login_data.password,
            request_info
        )
    
    @router.post("/refresh", response_model=LoginResponse)
    async def refresh_token(refresh_data: RefreshTokenRequest):
        """刷新访问令牌"""
        return await auth_service.refresh_token(refresh_data.refresh_token)
    
    @router.post("/logout")
    async def logout(user: UserContext = Depends(get_current_user)):
        """用户登出"""
        await auth_service.logout(user)
        return {"message": "登出成功"}
    
    @router.post("/logout-all")
    async def logout_all(user: UserContext = Depends(get_current_user)):
        """登出所有会话"""
        await auth_service.logout_all_sessions(user.user_id)
        return {"message": "已登出所有会话"}
    
    @router.get("/me")
    async def get_current_user_info(user: UserContext = Depends(get_current_user)):
        """获取当前用户信息"""
        return {
            "user_id": user.user_id,
            "username": user.username,
            "email": user.email,
            "roles": [role.value for role in user.roles],
            "permissions": [perm.value for perm in user.permissions],
            "login_time": user.login_time.isoformat(),
            "last_activity": user.last_activity.isoformat()
        }
    
    return router


# 权限检查装饰器示例
def create_protected_routes() -> FastAPI:
    """创建受保护的路由示例"""
    from fastapi import APIRouter
    
    router = APIRouter(prefix="/api/v1", tags=["受保护的资源"])
    
    @router.get("/users")
    async def list_users(user: UserContext = Depends(require_permission(Permission.USER_READ))):
        """获取用户列表（需要用户读取权限）"""
        return {"users": ["user1", "user2"], "requested_by": user.username}
    
    @router.post("/users")
    async def create_user(
        user_data: dict,
        user: UserContext = Depends(require_permission(Permission.USER_CREATE))
    ):
        """创建用户（需要用户创建权限）"""
        return {"message": "用户创建成功", "created_by": user.username}
    
    @router.get("/admin/system-info")
    async def get_system_info(user: UserContext = Depends(require_role(UserRole.ADMIN))):
        """获取系统信息（需要管理员角色）"""
        return {"system": "RedFire", "version": "1.0.0", "admin": user.username}
    
    @router.post("/trading/execute")
    async def execute_trade(
        trade_data: dict,
        user: UserContext = Depends(require_permission(Permission.TRADING_EXECUTE))
    ):
        """执行交易（需要交易执行权限）"""
        return {"message": "交易执行成功", "trader": user.username}
    
    return router


# 完整的FastAPI应用示例
def create_demo_app() -> FastAPI:
    """创建演示应用"""
    app = FastAPI(title="RedFire认证系统演示", version="1.0.0")
    
    # 配置认证
    auth_config = get_auth_config()
    security_config = SecurityConfig(
        jwt_secret_key=auth_config.jwt_secret_key,
        access_token_expire_minutes=auth_config.access_token_expire_minutes,
        redis_url=auth_config.redis_url,
        cache_enabled=auth_config.cache_enabled
    )
    
    # 创建认证服务
    auth_service = AuthService(security_config)
    
    # 设置中间件
    setup_auth_middleware(app, security_config)
    
    # 添加路由
    auth_router = create_auth_routes(auth_service)
    protected_router = create_protected_routes()
    
    app.include_router(auth_router)
    app.include_router(protected_router)
    
    @app.on_event("startup")
    async def startup_event():
        """应用启动事件"""
        await auth_service.initialize()
        logging.info("认证系统初始化完成")
    
    @app.get("/")
    async def root():
        """根路径"""
        return {"message": "RedFire认证系统演示", "status": "运行中"}
    
    @app.get("/health")
    async def health_check():
        """健康检查"""
        return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}
    
    return app


# 使用示例
if __name__ == "__main__":
    import uvicorn
    
    # 创建演示应用
    demo_app = create_demo_app()
    
    # 运行应用
    uvicorn.run(
        demo_app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
