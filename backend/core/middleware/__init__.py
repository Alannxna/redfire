"""
中间件管理模块
=============

统一管理所有中间件
"""

import logging
from fastapi import FastAPI

from .auth_middleware import AuthMiddleware
from .logging_middleware import LoggingMiddleware
from .error_middleware import ErrorHandlingMiddleware
from ..config import AppConfig

logger = logging.getLogger(__name__)


def setup_middleware(app: FastAPI, config: AppConfig):
    """设置所有中间件"""
    
    # 错误处理中间件（最外层）
    error_middleware = ErrorHandlingMiddleware(config)
    app.middleware("http")(error_middleware.handle_errors)
    
    # 日志中间件
    logging_middleware = LoggingMiddleware(config)
    app.middleware("http")(logging_middleware.log_requests)
    
    # 认证中间件（仅对需要认证的路径）
    # 注意：认证中间件通常通过依赖注入实现，而不是全局中间件
    # 这里预留接口
    
    logger.info("中间件设置完成")


__all__ = [
    'setup_middleware',
    'AuthMiddleware',
    'LoggingMiddleware', 
    'ErrorHandlingMiddleware'
]
