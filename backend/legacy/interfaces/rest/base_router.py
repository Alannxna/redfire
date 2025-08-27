"""
基础路由器

提供REST API路由的基础功能和通用方法
"""

from abc import ABC
from typing import Optional, Dict, Any, Callable
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from ...application.services.base_application_service import BaseApplicationService
from ...core.base.exceptions import DomainException


class BaseRouter(ABC):
    """基础路由器类
    
    提供REST API的通用功能：
    1. 统一的响应格式
    2. 异常处理
    3. 权限验证
    4. 请求日志
    """
    
    def __init__(self, prefix: str, tags: list, 
                 application_service: Optional[BaseApplicationService] = None):
        self.router = APIRouter(prefix=prefix, tags=tags)
        self.application_service = application_service
        self.logger = logging.getLogger(self.__class__.__name__)
        self.security = HTTPBearer(auto_error=False)
        
        # 设置异常处理器
        self._setup_exception_handlers()
    
    def _setup_exception_handlers(self) -> None:
        """设置异常处理器"""
        
        @self.router.exception_handler(DomainException)  
        async def domain_exception_handler(request: Request, exc: DomainException):
            self.logger.warning(f"领域异常: {str(exc)}")
            raise HTTPException(status_code=400, detail=str(exc))
        
        @self.router.exception_handler(ValueError)
        async def value_error_handler(request: Request, exc: ValueError):
            self.logger.warning(f"参数错误: {str(exc)}")
            raise HTTPException(status_code=400, detail=f"参数错误: {str(exc)}")
        
        @self.router.exception_handler(Exception)
        async def general_exception_handler(request: Request, exc: Exception):
            self.logger.error(f"未处理异常: {str(exc)}", exc_info=True)
            raise HTTPException(status_code=500, detail="系统内部错误")
    
    async def get_current_user(self, 
                             credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
                             ) -> Optional[Dict[str, Any]]:
        """获取当前用户信息
        
        Args:
            credentials: JWT凭证
            
        Returns:
            用户信息字典，如果未认证则返回None
        """
        if not credentials:
            return None
        
        try:
            # 这里需要实现JWT token验证逻辑
            # 可以调用认证服务或直接验证JWT
            token = credentials.credentials
            
            # 模拟解析JWT获取用户信息
            # 实际实现需要验证签名、过期时间等
            user_info = self._decode_jwt_token(token)
            
            return user_info
            
        except Exception as e:
            self.logger.warning(f"用户认证失败: {str(e)}")
            return None
    
    def _decode_jwt_token(self, token: str) -> Dict[str, Any]:
        """解码JWT token
        
        Args:
            token: JWT token字符串
            
        Returns:
            用户信息
            
        Raises:
            Exception: token无效
        """
        # 这里需要实现实际的JWT解码逻辑
        # 使用PyJWT库或其他JWT库
        # 验证签名、过期时间、颁发者等
        
        # 暂时返回模拟数据
        return {
            'user_id': 'mock_user_id',
            'username': 'mock_user',
            'roles': ['user']
        }
    
    def require_auth(self) -> Callable:
        """需要认证的依赖项
        
        Returns:
            FastAPI依赖项函数
        """
        async def auth_dependency(user: Optional[Dict[str, Any]] = Depends(self.get_current_user)):
            if not user:
                raise HTTPException(status_code=401, detail="需要认证")
            return user
        
        return auth_dependency
    
    def require_roles(self, required_roles: list) -> Callable:
        """需要特定角色的依赖项
        
        Args:
            required_roles: 所需角色列表
            
        Returns:
            FastAPI依赖项函数
        """
        async def role_dependency(user: Dict[str, Any] = Depends(self.require_auth())):
            user_roles = user.get('roles', [])
            if not any(role in user_roles for role in required_roles):
                raise HTTPException(status_code=403, detail="权限不足")
            return user
        
        return role_dependency
    
    def log_request(self, request: Request, user: Optional[Dict[str, Any]] = None) -> None:
        """记录请求日志
        
        Args:
            request: FastAPI请求对象
            user: 用户信息
        """
        user_id = user.get('user_id') if user else 'anonymous'
        self.logger.info(
            f"API请求: {request.method} {request.url.path} "
            f"用户: {user_id} "
            f"时间: {datetime.utcnow().isoformat()}"
        )
    
    def create_success_response(self, data: Any = None, 
                              message: str = "操作成功") -> Dict[str, Any]:
        """创建成功响应
        
        Args:
            data: 响应数据
            message: 响应消息
            
        Returns:
            响应字典
        """
        return {
            "success": True,
            "data": data,
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def create_error_response(self, message: str, 
                            status_code: int = 400) -> HTTPException:
        """创建错误响应
        
        Args:
            message: 错误消息
            status_code: HTTP状态码
            
        Returns:
            HTTP异常
        """
        return HTTPException(status_code=status_code, detail=message)
    
    def validate_pagination_params(self, page: int = 1, page_size: int = 20) -> Dict[str, int]:
        """验证分页参数
        
        Args:
            page: 页码
            page_size: 每页大小
            
        Returns:
            验证后的分页参数
        """
        if page < 1:
            page = 1
        if page_size < 1 or page_size > 1000:
            page_size = 20
        
        return {'page': page, 'page_size': page_size}
