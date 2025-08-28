"""
增强认证中间件
==============

企业级认证授权系统，整合了JWT认证、RBAC权限控制、会话管理、安全响应头等功能
根据TODO-14要求实现的完整认证授权解决方案
"""

import logging
import secrets
import asyncio
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any, Set, Union
from dataclasses import dataclass, field
from enum import Enum
import hashlib

import jwt
import redis.asyncio as redis
from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from passlib.context import CryptContext
import ipaddress


# 日志配置
logger = logging.getLogger(__name__)

# 密码哈希上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class TokenType(str, Enum):
    """令牌类型枚举"""
    ACCESS = "access"
    REFRESH = "refresh"
    RESET_PASSWORD = "reset_password"
    EMAIL_VERIFICATION = "email_verification"


class UserRole(str, Enum):
    """用户角色枚举"""
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    TRADER = "trader"
    ANALYST = "analyst"
    VIEWER = "viewer"
    GUEST = "guest"


class Permission(str, Enum):
    """权限枚举"""
    # 用户管理
    USER_READ = "user:read"
    USER_CREATE = "user:create"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"
    
    # 交易管理
    TRADING_READ = "trading:read"
    TRADING_EXECUTE = "trading:execute"
    TRADING_MANAGE = "trading:manage"
    
    # 策略管理
    STRATEGY_READ = "strategy:read"
    STRATEGY_CREATE = "strategy:create"
    STRATEGY_UPDATE = "strategy:update"
    STRATEGY_DELETE = "strategy:delete"
    STRATEGY_EXECUTE = "strategy:execute"
    
    # 数据管理
    DATA_READ = "data:read"
    DATA_WRITE = "data:write"
    DATA_EXPORT = "data:export"
    
    # 系统管理
    SYSTEM_READ = "system:read"
    SYSTEM_CONFIG = "system:config"
    SYSTEM_ADMIN = "system:admin"
    
    # 监控管理
    MONITOR_READ = "monitor:read"
    MONITOR_MANAGE = "monitor:manage"


@dataclass
class SecurityConfig:
    """安全配置"""
    # JWT配置
    jwt_secret_key: str = "jwt-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    
    # 安全配置
    max_login_attempts: int = 5
    lockout_duration_minutes: int = 15
    password_min_length: int = 8
    require_strong_password: bool = True
    
    # 会话配置
    max_concurrent_sessions: int = 3
    session_timeout_minutes: int = 60
    
    # Redis配置
    redis_url: str = "redis://localhost:6379/0"
    cache_enabled: bool = True
    cache_ttl_seconds: int = 300
    
    # IP限制
    enable_ip_whitelist: bool = False
    ip_whitelist: List[str] = field(default_factory=list)
    
    # 安全响应头
    enable_security_headers: bool = True
    cors_enabled: bool = True
    cors_origins: List[str] = field(default_factory=lambda: ["*"])


@dataclass
class UserContext:
    """用户上下文"""
    user_id: str
    username: str
    email: str
    roles: List[UserRole]
    permissions: Set[Permission]
    session_id: str
    login_time: datetime
    last_activity: datetime
    ip_address: str
    user_agent: str
    
    def has_permission(self, permission: Union[Permission, str]) -> bool:
        """检查权限"""
        if isinstance(permission, str):
            try:
                permission = Permission(permission)
            except ValueError:
                return False
        return permission in self.permissions
    
    def has_role(self, role: Union[UserRole, str]) -> bool:
        """检查角色"""
        if isinstance(role, str):
            try:
                role = UserRole(role)
            except ValueError:
                return False
        return role in self.roles
    
    def has_any_role(self, roles: List[Union[UserRole, str]]) -> bool:
        """检查是否拥有任一角色"""
        return any(self.has_role(role) for role in roles)


class SessionManager:
    """会话管理器"""
    
    def __init__(self, redis_client: Optional[redis.Redis], config: SecurityConfig):
        self.redis_client = redis_client
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.SessionManager")
    
    async def create_session(self, user_context: UserContext) -> str:
        """创建会话"""
        session_id = self._generate_session_id()
        
        if self.redis_client:
            # 检查并清理过期会话
            await self._cleanup_user_sessions(user_context.user_id)
            
            # 限制并发会话数
            await self._enforce_session_limit(user_context.user_id)
            
            # 存储会话信息
            session_key = f"session:{session_id}"
            session_data = {
                "user_id": user_context.user_id,
                "username": user_context.username,
                "email": user_context.email,
                "roles": [role.value for role in user_context.roles],
                "login_time": user_context.login_time.isoformat(),
                "last_activity": user_context.last_activity.isoformat(),
                "ip_address": user_context.ip_address,
                "user_agent": user_context.user_agent
            }
            
            await self.redis_client.hset(session_key, mapping=session_data)
            await self.redis_client.expire(session_key, self.config.session_timeout_minutes * 60)
            
            # 添加到用户会话列表
            user_sessions_key = f"user_sessions:{user_context.user_id}"
            await self.redis_client.sadd(user_sessions_key, session_id)
            await self.redis_client.expire(user_sessions_key, self.config.session_timeout_minutes * 60)
        
        return session_id
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话"""
        if not self.redis_client:
            return None
        
        session_key = f"session:{session_id}"
        session_data = await self.redis_client.hgetall(session_key)
        
        if not session_data:
            return None
        
        # 更新最后活动时间
        await self.update_last_activity(session_id)
        
        return session_data
    
    async def update_last_activity(self, session_id: str):
        """更新最后活动时间"""
        if not self.redis_client:
            return
        
        session_key = f"session:{session_id}"
        await self.redis_client.hset(session_key, "last_activity", datetime.now(timezone.utc).isoformat())
        await self.redis_client.expire(session_key, self.config.session_timeout_minutes * 60)
    
    async def revoke_session(self, session_id: str):
        """撤销会话"""
        if not self.redis_client:
            return
        
        # 获取会话信息
        session_data = await self.get_session(session_id)
        if session_data:
            user_id = session_data.get("user_id")
            if user_id:
                # 从用户会话列表中移除
                user_sessions_key = f"user_sessions:{user_id}"
                await self.redis_client.srem(user_sessions_key, session_id)
        
        # 删除会话
        session_key = f"session:{session_id}"
        await self.redis_client.delete(session_key)
    
    async def revoke_all_user_sessions(self, user_id: str):
        """撤销用户所有会话"""
        if not self.redis_client:
            return
        
        user_sessions_key = f"user_sessions:{user_id}"
        session_ids = await self.redis_client.smembers(user_sessions_key)
        
        for session_id in session_ids:
            await self.revoke_session(session_id)
        
        await self.redis_client.delete(user_sessions_key)
    
    async def _cleanup_user_sessions(self, user_id: str):
        """清理用户过期会话"""
        if not self.redis_client:
            return
        
        user_sessions_key = f"user_sessions:{user_id}"
        session_ids = await self.redis_client.smembers(user_sessions_key)
        
        for session_id in session_ids:
            session_key = f"session:{session_id}"
            exists = await self.redis_client.exists(session_key)
            if not exists:
                await self.redis_client.srem(user_sessions_key, session_id)
    
    async def _enforce_session_limit(self, user_id: str):
        """强制执行会话限制"""
        if not self.redis_client:
            return
        
        user_sessions_key = f"user_sessions:{user_id}"
        session_count = await self.redis_client.scard(user_sessions_key)
        
        if session_count >= self.config.max_concurrent_sessions:
            # 获取最旧的会话并删除
            session_ids = await self.redis_client.smembers(user_sessions_key)
            oldest_sessions = []
            
            for session_id in session_ids:
                session_data = await self.get_session(session_id)
                if session_data:
                    login_time = datetime.fromisoformat(session_data.get("login_time", ""))
                    oldest_sessions.append((session_id, login_time))
            
            # 按登录时间排序，删除最旧的会话
            oldest_sessions.sort(key=lambda x: x[1])
            sessions_to_remove = len(oldest_sessions) - self.config.max_concurrent_sessions + 1
            
            for i in range(sessions_to_remove):
                await self.revoke_session(oldest_sessions[i][0])
    
    def _generate_session_id(self) -> str:
        """生成会话ID"""
        return secrets.token_urlsafe(32)


class RBACManager:
    """基于角色的访问控制管理器"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.RBACManager")
        self._role_permissions = self._initialize_role_permissions()
    
    def _initialize_role_permissions(self) -> Dict[UserRole, Set[Permission]]:
        """初始化角色权限映射"""
        return {
            UserRole.SUPER_ADMIN: set(Permission),  # 超级管理员拥有所有权限
            
            UserRole.ADMIN: {
                Permission.USER_READ, Permission.USER_CREATE, Permission.USER_UPDATE, Permission.USER_DELETE,
                Permission.TRADING_READ, Permission.TRADING_EXECUTE, Permission.TRADING_MANAGE,
                Permission.STRATEGY_READ, Permission.STRATEGY_CREATE, Permission.STRATEGY_UPDATE, 
                Permission.STRATEGY_DELETE, Permission.STRATEGY_EXECUTE,
                Permission.DATA_READ, Permission.DATA_WRITE, Permission.DATA_EXPORT,
                Permission.SYSTEM_READ, Permission.SYSTEM_CONFIG,
                Permission.MONITOR_READ, Permission.MONITOR_MANAGE
            },
            
            UserRole.TRADER: {
                Permission.USER_READ,
                Permission.TRADING_READ, Permission.TRADING_EXECUTE,
                Permission.STRATEGY_READ, Permission.STRATEGY_CREATE, Permission.STRATEGY_UPDATE, 
                Permission.STRATEGY_EXECUTE,
                Permission.DATA_READ, Permission.DATA_WRITE,
                Permission.MONITOR_READ
            },
            
            UserRole.ANALYST: {
                Permission.USER_READ,
                Permission.TRADING_READ,
                Permission.STRATEGY_READ, Permission.STRATEGY_CREATE, Permission.STRATEGY_UPDATE,
                Permission.DATA_READ, Permission.DATA_WRITE, Permission.DATA_EXPORT,
                Permission.MONITOR_READ
            },
            
            UserRole.VIEWER: {
                Permission.USER_READ,
                Permission.TRADING_READ,
                Permission.STRATEGY_READ,
                Permission.DATA_READ,
                Permission.MONITOR_READ
            },
            
            UserRole.GUEST: {
                Permission.TRADING_READ,
                Permission.STRATEGY_READ,
                Permission.DATA_READ
            }
        }
    
    def get_role_permissions(self, roles: List[UserRole]) -> Set[Permission]:
        """获取角色权限集合"""
        permissions = set()
        for role in roles:
            permissions.update(self._role_permissions.get(role, set()))
        return permissions
    
    def check_permission(self, user_roles: List[UserRole], required_permission: Permission) -> bool:
        """检查权限"""
        user_permissions = self.get_role_permissions(user_roles)
        return required_permission in user_permissions


class JWTManager:
    """JWT令牌管理器"""
    
    def __init__(self, config: SecurityConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.JWTManager")
        self._ensure_secure_key()
    
    def _ensure_secure_key(self):
        """确保JWT密钥安全"""
        if self.config.jwt_secret_key == "jwt-secret-key-change-in-production":
            self.logger.warning("使用默认JWT密钥，建议在生产环境中更改")
            # 生成临时强密钥
            self.config.jwt_secret_key = secrets.token_urlsafe(32)
    
    def create_token(self, 
                    user_data: Dict[str, Any], 
                    token_type: TokenType,
                    expires_delta: Optional[timedelta] = None) -> str:
        """创建JWT令牌"""
        now = datetime.now(timezone.utc)
        
        if expires_delta:
            expire = now + expires_delta
        elif token_type == TokenType.ACCESS:
            expire = now + timedelta(minutes=self.config.access_token_expire_minutes)
        elif token_type == TokenType.REFRESH:
            expire = now + timedelta(days=self.config.refresh_token_expire_days)
        else:
            expire = now + timedelta(hours=1)  # 默认1小时
        
        payload = {
            "sub": str(user_data.get("user_id")),
            "user_id": user_data.get("user_id"),
            "username": user_data.get("username"),
            "email": user_data.get("email"),
            "roles": user_data.get("roles", []),
            "session_id": user_data.get("session_id"),
            "type": token_type.value,
            "iat": now,
            "exp": expire,
            "iss": "redfire-auth",  # 发行者
            "aud": "redfire-client",  # 受众
            "jti": secrets.token_urlsafe(16)  # JWT ID
        }
        
        token = jwt.encode(payload, self.config.jwt_secret_key, algorithm=self.config.jwt_algorithm)
        return token
    
    def verify_token(self, token: str, expected_type: TokenType) -> Optional[Dict[str, Any]]:
        """验证JWT令牌"""
        try:
            payload = jwt.decode(
                token,
                self.config.jwt_secret_key,
                algorithms=[self.config.jwt_algorithm],
                audience="redfire-client",
                issuer="redfire-auth"
            )
            
            # 验证令牌类型
            if payload.get("type") != expected_type.value:
                self.logger.warning(f"令牌类型不匹配，期望: {expected_type.value}, 实际: {payload.get('type')}")
                return None
            
            return payload
            
        except jwt.ExpiredSignatureError:
            self.logger.debug("JWT令牌已过期")
            return None
        except jwt.InvalidTokenError as e:
            self.logger.debug(f"无效的JWT令牌: {str(e)}")
            return None
        except Exception as e:
            self.logger.error(f"JWT令牌验证失败: {str(e)}")
            return None
    
    def decode_token_without_verification(self, token: str) -> Optional[Dict[str, Any]]:
        """解码令牌但不验证（用于获取过期令牌信息）"""
        try:
            return jwt.decode(token, options={"verify_signature": False})
        except Exception:
            return None


class SecurityManager:
    """安全管理器"""
    
    def __init__(self, redis_client: Optional[redis.Redis], config: SecurityConfig):
        self.redis_client = redis_client
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.SecurityManager")
    
    async def check_login_attempts(self, identifier: str) -> bool:
        """检查登录尝试次数"""
        if not self.redis_client:
            return True
        
        key = f"login_attempts:{identifier}"
        attempts = await self.redis_client.get(key)
        
        if attempts and int(attempts) >= self.config.max_login_attempts:
            self.logger.warning(f"登录尝试次数过多: {identifier}")
            return False
        
        return True
    
    async def record_login_attempt(self, identifier: str, success: bool):
        """记录登录尝试"""
        if not self.redis_client:
            return
        
        key = f"login_attempts:{identifier}"
        
        if success:
            # 登录成功，清除尝试记录
            await self.redis_client.delete(key)
        else:
            # 登录失败，增加尝试次数
            current = await self.redis_client.get(key)
            attempts = int(current) + 1 if current else 1
            
            await self.redis_client.set(key, attempts)
            await self.redis_client.expire(key, self.config.lockout_duration_minutes * 60)
    
    def validate_password_strength(self, password: str) -> tuple[bool, List[str]]:
        """验证密码强度"""
        errors = []
        
        if len(password) < self.config.password_min_length:
            errors.append(f"密码长度至少{self.config.password_min_length}位")
        
        if self.config.require_strong_password:
            if not any(c.isupper() for c in password):
                errors.append("密码必须包含大写字母")
            
            if not any(c.islower() for c in password):
                errors.append("密码必须包含小写字母")
            
            if not any(c.isdigit() for c in password):
                errors.append("密码必须包含数字")
            
            if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
                errors.append("密码必须包含特殊字符")
        
        return len(errors) == 0, errors
    
    def check_ip_whitelist(self, ip_address: str) -> bool:
        """检查IP白名单"""
        if not self.config.enable_ip_whitelist:
            return True
        
        try:
            client_ip = ipaddress.ip_address(ip_address)
            for allowed_ip in self.config.ip_whitelist:
                if "/" in allowed_ip:
                    # CIDR网段
                    if client_ip in ipaddress.ip_network(allowed_ip, strict=False):
                        return True
                else:
                    # 单个IP
                    if client_ip == ipaddress.ip_address(allowed_ip):
                        return True
            return False
        except Exception as e:
            self.logger.error(f"IP检查失败: {e}")
            return False
    
    def hash_password(self, password: str) -> str:
        """哈希密码"""
        return pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """验证密码"""
        return pwd_context.verify(plain_password, hashed_password)


class EnhancedAuthMiddleware(BaseHTTPMiddleware):
    """增强认证中间件"""
    
    def __init__(self, app, config: Optional[SecurityConfig] = None):
        super().__init__(app)
        self.config = config or SecurityConfig()
        self.logger = logging.getLogger(f"{__name__}.EnhancedAuthMiddleware")
        
        # 初始化组件
        self.redis_client: Optional[redis.Redis] = None
        self.jwt_manager = JWTManager(self.config)
        self.rbac_manager = RBACManager()
        self.session_manager = None
        self.security_manager = None
        
        # 公开路径配置
        self.public_paths = {
            "/", "/health", "/docs", "/redoc", "/openapi.json",
            "/api/v1/auth/login", "/api/v1/auth/register", 
            "/api/v1/auth/refresh", "/api/v1/auth/forgot-password",
            "/api/v1/auth/reset-password", "/api/v1/auth/verify-email",
            "/static", "/ws", "/favicon.ico"
        }
        
        # 权限路径映射
        self.path_permissions = {
            "/api/v1/users": {
                "GET": Permission.USER_READ,
                "POST": Permission.USER_CREATE,
                "PUT": Permission.USER_UPDATE,
                "DELETE": Permission.USER_DELETE
            },
            "/api/v1/strategies": {
                "GET": Permission.STRATEGY_READ,
                "POST": Permission.STRATEGY_CREATE,
                "PUT": Permission.STRATEGY_UPDATE,
                "DELETE": Permission.STRATEGY_DELETE
            },
            "/api/v1/trading": {
                "GET": Permission.TRADING_READ,
                "POST": Permission.TRADING_EXECUTE
            },
            "/api/v1/data": {
                "GET": Permission.DATA_READ,
                "POST": Permission.DATA_WRITE
            },
            "/api/v1/admin": {
                "GET": Permission.SYSTEM_READ,
                "POST": Permission.SYSTEM_CONFIG,
                "PUT": Permission.SYSTEM_CONFIG,
                "DELETE": Permission.SYSTEM_ADMIN
            }
        }
    
    async def initialize(self):
        """异步初始化"""
        if self.config.cache_enabled:
            try:
                self.redis_client = redis.from_url(
                    self.config.redis_url,
                    decode_responses=True,
                    retry_on_timeout=True,
                    health_check_interval=30
                )
                await self.redis_client.ping()
                self.logger.info("Redis连接成功")
            except Exception as e:
                self.logger.warning(f"Redis连接失败: {e}")
                self.redis_client = None
        
        self.session_manager = SessionManager(self.redis_client, self.config)
        self.security_manager = SecurityManager(self.redis_client, self.config)
    
    async def dispatch(self, request: Request, call_next):
        """请求分发处理"""
        # 确保初始化完成
        if self.session_manager is None:
            await self.initialize()
        
        try:
            # 添加安全响应头
            response = await self._process_request(request, call_next)
            
            if self.config.enable_security_headers:
                self._add_security_headers(response)
            
            return response
            
        except HTTPException as e:
            return self._create_error_response(e.status_code, e.detail)
        except Exception as e:
            self.logger.error(f"认证中间件处理失败: {e}")
            return self._create_error_response(500, "认证服务异常")
    
    async def _process_request(self, request: Request, call_next):
        """处理请求"""
        path = request.url.path
        method = request.method
        
        # 检查是否为公开路径
        if self._is_public_path(path):
            return await call_next(request)
        
        # IP白名单检查
        client_ip = self._get_client_ip(request)
        if not self.security_manager.check_ip_whitelist(client_ip):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="IP地址不在白名单中"
            )
        
        # 提取和验证令牌
        token = self._extract_token(request)
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="缺少认证令牌",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # 验证JWT令牌
        payload = self.jwt_manager.verify_token(token, TokenType.ACCESS)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效或过期的认证令牌",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # 验证会话
        session_id = payload.get("session_id")
        if session_id:
            session_data = await self.session_manager.get_session(session_id)
            if not session_data:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="会话已过期，请重新登录"
                )
        
        # 构建用户上下文
        user_context = await self._build_user_context(payload, request)
        
        # 权限检查
        required_permission = self._get_required_permission(path, method)
        if required_permission:
            if not user_context.has_permission(required_permission):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"权限不足，需要权限: {required_permission.value}"
                )
        
        # 将用户上下文添加到请求状态
        request.state.user = user_context
        
        # 记录访问日志
        self.logger.info(f"用户 {user_context.username} 访问 {method} {path}")
        
        return await call_next(request)
    
    def _is_public_path(self, path: str) -> bool:
        """检查是否为公开路径"""
        return any(path.startswith(public_path) for public_path in self.public_paths)
    
    def _extract_token(self, request: Request) -> Optional[str]:
        """提取认证令牌"""
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return None
        
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return None
        
        return parts[1]
    
    async def _build_user_context(self, payload: Dict[str, Any], request: Request) -> UserContext:
        """构建用户上下文"""
        user_id = payload.get("user_id")
        username = payload.get("username", "")
        email = payload.get("email", "")
        role_names = payload.get("roles", [])
        session_id = payload.get("session_id", "")
        
        # 转换角色
        roles = []
        for role_name in role_names:
            try:
                roles.append(UserRole(role_name))
            except ValueError:
                self.logger.warning(f"未知角色: {role_name}")
        
        # 获取权限
        permissions = self.rbac_manager.get_role_permissions(roles)
        
        # 构建用户上下文
        return UserContext(
            user_id=user_id,
            username=username,
            email=email,
            roles=roles,
            permissions=permissions,
            session_id=session_id,
            login_time=datetime.fromisoformat(payload.get("iat", datetime.now(timezone.utc).isoformat())),
            last_activity=datetime.now(timezone.utc),
            ip_address=self._get_client_ip(request),
            user_agent=request.headers.get("User-Agent", "")
        )
    
    def _get_required_permission(self, path: str, method: str) -> Optional[Permission]:
        """获取路径所需权限"""
        for prefix, methods in self.path_permissions.items():
            if path.startswith(prefix):
                permission_str = methods.get(method.upper())
                if permission_str:
                    return permission_str
        return None
    
    def _get_client_ip(self, request: Request) -> str:
        """获取客户端IP"""
        # 检查代理头
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"
    
    def _add_security_headers(self, response):
        """添加安全响应头"""
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        
        if self.config.cors_enabled:
            origin = response.headers.get("Origin")
            if origin in self.config.cors_origins or "*" in self.config.cors_origins:
                response.headers["Access-Control-Allow-Origin"] = origin or "*"
                response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
                response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
                response.headers["Access-Control-Allow-Credentials"] = "true"
    
    def _create_error_response(self, status_code: int, detail: str) -> JSONResponse:
        """创建错误响应"""
        return JSONResponse(
            status_code=status_code,
            content={
                "error": True,
                "message": detail,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "status_code": status_code
            }
        )
    
    async def close(self):
        """关闭中间件"""
        if self.redis_client:
            await self.redis_client.close()


# FastAPI依赖注入函数
security = HTTPBearer()


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> UserContext:
    """获取当前用户（FastAPI依赖注入）"""
    if hasattr(request.state, 'user'):
        return request.state.user
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="用户未认证"
    )


async def require_permission(permission: Permission):
    """权限检查装饰器"""
    def permission_checker(user: UserContext = Depends(get_current_user)):
        if not user.has_permission(permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"权限不足，需要权限: {permission.value}"
            )
        return user
    
    return permission_checker


async def require_role(role: UserRole):
    """角色检查装饰器"""
    def role_checker(user: UserContext = Depends(get_current_user)):
        if not user.has_role(role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"角色权限不足，需要角色: {role.value}"
            )
        return user
    
    return role_checker


# 便捷函数
def create_auth_middleware(config: Optional[SecurityConfig] = None) -> EnhancedAuthMiddleware:
    """创建认证中间件实例"""
    return EnhancedAuthMiddleware(None, config)


def get_security_config() -> SecurityConfig:
    """获取安全配置"""
    return SecurityConfig()
