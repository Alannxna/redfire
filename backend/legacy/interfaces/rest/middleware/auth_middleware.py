"""
认证中间件
==========

提供JWT认证和权限验证功能
"""

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
import jwt
import logging
import secrets
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from ..models.common import ErrorResponse
from ....core.config.unified_config import UnifiedConfig


class JWTHelper:
    """JWT辅助类"""
    
    def __init__(self, config: Optional[UnifiedConfig] = None):
        self.config = config or UnifiedConfig()
        self.secret_key = self._get_secure_secret_key()
        self.algorithm = self.config.jwt_algorithm
        self.access_token_expire_minutes = self.config.jwt_access_token_expire_minutes
        self._logger = logging.getLogger(self.__class__.__name__)
    
    def _get_secure_secret_key(self) -> str:
        """获取安全的JWT密钥"""
        # 优先使用环境变量或配置文件中的密钥
        secret_key = self.config.jwt_secret_key
        
        # 如果是默认密钥且在生产环境，生成一个强密钥
        if secret_key == "jwt-secret-key" and self.config.environment.environment.value == "production":
            self._logger.warning("使用默认JWT密钥在生产环境，建议配置强密钥")
            # 生成临时强密钥
            secret_key = secrets.token_urlsafe(32)
        
        return secret_key
    
    def create_access_token(self, user_data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """创建访问令牌"""
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        payload = {
            "sub": str(user_data.get("user_id")),  # subject - 标准JWT字段
            "user_id": user_data.get("user_id"),
            "username": user_data.get("username"),
            "role": user_data.get("role", "trader"),
            "email": user_data.get("email"),
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        }
        
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        return token
    
    def create_refresh_token(self, user_data: Dict[str, Any]) -> str:
        """创建刷新令牌（有效期7天）"""
        expire = datetime.utcnow() + timedelta(days=7)
        
        payload = {
            "sub": str(user_data.get("user_id")),
            "user_id": user_data.get("user_id"),
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh"
        }
        
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        return token
    
    def verify_token(self, token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
        """验证JWT令牌"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # 验证令牌类型
            if payload.get("type") != token_type:
                self._logger.warning(f"令牌类型不匹配，期望: {token_type}, 实际: {payload.get('type')}")
                return None
                
            return payload
        except jwt.ExpiredSignatureError:
            self._logger.warning("JWT令牌已过期")
            return None
        except jwt.InvalidTokenError as e:
            self._logger.warning(f"无效的JWT令牌: {str(e)}")
            return None
        except Exception as e:
            self._logger.error(f"JWT令牌验证失败: {str(e)}")
            return None
    
    def decode_token_without_verification(self, token: str) -> Optional[Dict[str, Any]]:
        """解码令牌但不验证（用于获取过期令牌信息）"""
        try:
            return jwt.decode(token, options={"verify_signature": False})
        except Exception:
            return None


class AuthMiddleware:
    """认证中间件"""
    
    def __init__(self, config: Optional[UnifiedConfig] = None):
        self._logger = logging.getLogger(self.__class__.__name__)
        self.jwt_helper = JWTHelper(config)
        self.config = config or UnifiedConfig()
        
        # 不需要认证的路径
        self.public_paths = {
            "/",
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/api/v1/users/login",
            "/api/v1/users/register",
            "/api/v1/users/check-username",
            "/api/v1/users/check-email",
            "/api/v1/users/refresh-token",
            "/api/v1/users/forgot-password",
            "/api/v1/users/reset-password"
        }
    
    async def authenticate(self, request: Request, call_next):
        """认证处理"""
        path = request.url.path
        
        # 检查是否是公开路径
        if path in self.public_paths or path.startswith("/static/") or path.startswith("/ws/"):
            return await call_next(request)
        
        # 获取Authorization头
        auth_header = request.headers.get("Authorization")
        
        if not auth_header:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content=ErrorResponse(
                    message="缺少认证令牌",
                    error_code="MISSING_TOKEN",
                    details="请在Authorization头中提供Bearer令牌"
                ).dict()
            )
        
        # 验证Bearer令牌格式
        try:
            scheme, token = auth_header.split()
            if scheme.lower() != "bearer":
                raise ValueError("无效的认证方案")
        except ValueError:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content=ErrorResponse(
                    message="无效的认证令牌格式",
                    error_code="INVALID_TOKEN_FORMAT",
                    details="格式应为: Bearer <token>"
                ).dict()
            )
        
        # 验证JWT令牌
        payload = self.jwt_helper.verify_token(token, "access")
        if not payload:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content=ErrorResponse(
                    message="认证令牌无效或已过期",
                    error_code="INVALID_TOKEN",
                    details="请重新登录获取新的访问令牌"
                ).dict()
            )
        
        # 将用户信息添加到请求状态
        request.state.user = {
            "user_id": payload.get("user_id"),
            "username": payload.get("username"),
            "role": payload.get("role"),
            "email": payload.get("email"),
            "token_exp": payload.get("exp")
        }
        
        # 记录用户访问日志
        self._logger.debug(f"用户 {payload.get('username')} 访问路径: {path}")
        
        return await call_next(request)
    
    def get_user_permissions(self, role: str) -> list[str]:
        """根据角色获取权限列表"""
        permissions_map = {
            "admin": [
                "user:read", "user:write", "user:delete",
                "trading:read", "trading:write", "trading:execute",
                "strategy:read", "strategy:write", "strategy:execute",
                "data:read", "data:write",
                "system:read", "system:write", "system:admin"
            ],
            "trader": [
                "user:read", "user:write",
                "trading:read", "trading:write", "trading:execute",
                "strategy:read", "strategy:write", "strategy:execute",
                "data:read"
            ],
            "viewer": [
                "user:read",
                "trading:read",
                "strategy:read",
                "data:read"
            ]
        }
        return permissions_map.get(role.lower(), [])