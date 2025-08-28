"""
错误处理中间件
==============

统一处理应用中的异常和错误
"""

import logging
import traceback
from typing import Callable
from fastapi import Request, Response
from fastapi.responses import JSONResponse

from ..config import AppConfig

logger = logging.getLogger(__name__)


class ErrorHandlingMiddleware:
    """错误处理中间件"""
    
    def __init__(self, config: AppConfig):
        self.config = config
        
    async def handle_errors(self, request: Request, call_next: Callable) -> Response:
        """处理请求中的错误"""
        try:
            response = await call_next(request)
            return response
            
        except Exception as e:
            # 记录错误详情
            error_id = self._log_error(request, e)
            
            # 根据环境返回不同详细程度的错误信息
            if self.config.is_production():
                # 生产环境：返回通用错误信息
                return JSONResponse(
                    status_code=500,
                    content={
                        "success": False,
                        "message": "内部服务器错误",
                        "error_id": error_id,
                        "detail": "请联系系统管理员"
                    }
                )
            else:
                # 开发环境：返回详细错误信息
                return JSONResponse(
                    status_code=500,
                    content={
                        "success": False,
                        "message": "内部服务器错误",
                        "error_id": error_id,
                        "detail": str(e),
                        "traceback": traceback.format_exc() if self.config.debug else None
                    }
                )
    
    def _log_error(self, request: Request, error: Exception) -> str:
        """记录错误信息并返回错误ID"""
        import uuid
        error_id = str(uuid.uuid4())[:8]
        
        logger.error(
            f"Error ID {error_id}: {type(error).__name__}: {str(error)} "
            f"- Path: {request.method} {request.url} "
            f"- Client: {request.client.host if request.client else 'unknown'}"
        )
        
        if self.config.debug:
            logger.error(f"Traceback for Error ID {error_id}:\n{traceback.format_exc()}")
        
        return error_id
