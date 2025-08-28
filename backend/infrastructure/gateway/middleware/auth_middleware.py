"""
网关认证中间件
=============

处理API网关的统一认证和授权
"""

import logging
import jwt
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from fastapi import HTTPException, status, Request
import redis.asyncio as redis

from ..config.gateway_config import AuthConfig

logger = logging.getLogger(__name__)


@dataclass
class UserContext:
    """用户上下文"""
    user_id: str
    username: str
    roles: List[str]
    permissions: List[str]
    
    def has_permission(self, permission: str) -> bool:
        """检查权限"""
        return permission in self.permissions
    
    def has_role(self, role: str) -> bool:
        """检查角色"""
        return role in self.roles


class GatewayAuthMiddleware:
    """网关认证中间件"""
    
    def __init__(self, config: AuthConfig):
        self.config = config
        self.redis_client: Optional[redis.Redis] = None
        
        # 权限缓存
        self._permission_cache: Dict[str, List[str]] = {}
        
    async def initialize(self):
        """初始化中间件"""
        if self.config.cache_enabled:
            self.redis_client = redis.from_url(
                self.config.redis_url,
                decode_responses=True
            )
    
    async def authenticate_request(self, request: Request) -> Optional[UserContext]:
        """认证请求"""
        path = request.url.path
        
        # 检查是否为公开路径
        if self._is_public_path(path):
            return None
        
        # 提取认证令牌
        token = self._extract_token(request)
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="缺少认证令牌",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # 验证令牌
        try:
            payload = self._verify_token(token)
            user_context = await self._build_user_context(payload)
            
            # 检查路径权限
            required_permission = self._get_required_permission(path, request.method)
            if required_permission and not user_context.has_permission(required_permission):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="权限不足"
                )
            
            return user_context
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="令牌已过期",
                headers={"WWW-Authenticate": "Bearer"}
            )
        except jwt.InvalidTokenError as e:
            logger.warning(f"无效令牌: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的认证令牌",
                headers={"WWW-Authenticate": "Bearer"}
            )
        except Exception as e:
            logger.error(f"认证失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="认证服务异常"
            )
    
    def _is_public_path(self, path: str) -> bool:
        """检查是否为公开路径"""
        for public_path in self.config.public_paths:
            if path.startswith(public_path):
                return True
        return False
    
    def _extract_token(self, request: Request) -> Optional[str]:
        """提取认证令牌"""
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return None
        
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return None
        
        return parts[1]
    
    def _verify_token(self, token: str) -> Dict[str, Any]:
        """验证JWT令牌"""
        try:
            payload = jwt.decode(
                token,
                self.config.jwt_secret,
                algorithms=[self.config.jwt_algorithm]
            )
            return payload
        except Exception as e:
            logger.debug(f"令牌验证失败: {e}")
            raise
    
    async def _build_user_context(self, payload: Dict[str, Any]) -> UserContext:
        """构建用户上下文"""
        user_id = payload.get("sub")
        username = payload.get("username", "")
        
        if not user_id:
            raise ValueError("令牌中缺少用户ID")
        
        # 从缓存或数据库获取用户权限
        roles = await self._get_user_roles(user_id)
        permissions = await self._get_user_permissions(user_id)
        
        return UserContext(
            user_id=user_id,
            username=username,
            roles=roles,
            permissions=permissions
        )
    
    async def _get_user_roles(self, user_id: str) -> List[str]:
        """获取用户角色"""
        # 先从缓存查找
        cache_key = f"user:roles:{user_id}"
        
        if self.redis_client:
            try:
                cached_roles = await self.redis_client.lrange(cache_key, 0, -1)
                if cached_roles:
                    return cached_roles
            except Exception:
                pass
        
        # 从数据库查询（这里使用模拟数据）
        roles = self._mock_get_user_roles(user_id)
        
        # 写入缓存
        if self.redis_client and roles:
            try:
                await self.redis_client.delete(cache_key)
                await self.redis_client.lpush(cache_key, *roles)
                await self.redis_client.expire(cache_key, 300)  # 5分钟过期
            except Exception:
                pass
        
        return roles
    
    async def _get_user_permissions(self, user_id: str) -> List[str]:
        """获取用户权限"""
        # 先从缓存查找
        cache_key = f"user:permissions:{user_id}"
        
        if self.redis_client:
            try:
                cached_permissions = await self.redis_client.lrange(cache_key, 0, -1)
                if cached_permissions:
                    return cached_permissions
            except Exception:
                pass
        
        # 从数据库查询
        permissions = self._mock_get_user_permissions(user_id)
        
        # 写入缓存
        if self.redis_client and permissions:
            try:
                await self.redis_client.delete(cache_key)
                await self.redis_client.lpush(cache_key, *permissions)
                await self.redis_client.expire(cache_key, 300)
            except Exception:
                pass
        
        return permissions
    
    def _get_required_permission(self, path: str, method: str) -> Optional[str]:
        """获取路径所需权限"""
        # 权限映射规则
        permission_rules = {
            "/api/v1/users": {
                "GET": "user:read",
                "POST": "user:create",
                "PUT": "user:update",
                "DELETE": "user:delete"
            },
            "/api/v1/strategies": {
                "GET": "strategy:read",
                "POST": "strategy:create",
                "PUT": "strategy:update",
                "DELETE": "strategy:delete"
            },
            "/api/v1/data": {
                "GET": "data:read",
                "POST": "data:write"
            },
            "/api/v1/vnpy": {
                "GET": "trading:read",
                "POST": "trading:execute"
            }
        }
        
        for prefix, methods in permission_rules.items():
            if path.startswith(prefix):
                return methods.get(method.upper())
        
        return None
    
    def _mock_get_user_roles(self, user_id: str) -> List[str]:
        """模拟获取用户角色"""
        # 在实际应用中，这里应该查询数据库
        role_map = {
            "admin": ["admin", "trader", "viewer"],
            "trader": ["trader", "viewer"],
            "viewer": ["viewer"]
        }
        
        # 简单的用户角色映射
        if user_id.startswith("admin"):
            return role_map["admin"]
        elif user_id.startswith("trader"):
            return role_map["trader"]
        else:
            return role_map["viewer"]
    
    def _mock_get_user_permissions(self, user_id: str) -> List[str]:
        """模拟获取用户权限"""
        permission_map = {
            "admin": [
                "user:read", "user:create", "user:update", "user:delete",
                "strategy:read", "strategy:create", "strategy:update", "strategy:delete",
                "data:read", "data:write",
                "trading:read", "trading:execute"
            ],
            "trader": [
                "user:read",
                "strategy:read", "strategy:create", "strategy:update",
                "data:read", "data:write",
                "trading:read", "trading:execute"
            ],
            "viewer": [
                "user:read",
                "strategy:read",
                "data:read",
                "trading:read"
            ]
        }
        
        roles = self._mock_get_user_roles(user_id)
        permissions = set()
        
        for role in roles:
            if role in permission_map:
                permissions.update(permission_map[role])
        
        return list(permissions)
    
    async def close(self):
        """关闭中间件"""
        if self.redis_client:
            await self.redis_client.close()
