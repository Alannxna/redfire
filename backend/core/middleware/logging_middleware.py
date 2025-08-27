"""
日志中间件
==========

记录HTTP请求和响应信息
"""

import time
import logging
from typing import Callable
from fastapi import Request, Response

from ..config import AppConfig

logger = logging.getLogger(__name__)


class LoggingMiddleware:
    """日志中间件"""
    
    def __init__(self, config: AppConfig):
        self.config = config
        self.access_logger = logging.getLogger("access")
        
    async def log_requests(self, request: Request, call_next: Callable) -> Response:
        """记录请求日志"""
        start_time = time.time()
        
        # 记录请求开始
        if self.config.debug:
            logger.debug(
                f"Request started: {request.method} {request.url} "
                f"from {request.client.host if request.client else 'unknown'}"
            )
        
        try:
            # 处理请求
            response = await call_next(request)
            
            # 计算处理时间
            process_time = time.time() - start_time
            
            # 记录访问日志
            self.access_logger.info(
                f"{request.client.host if request.client else 'unknown'} - "
                f'"{request.method} {request.url}" '
                f"{response.status_code} - {process_time:.3f}s"
            )
            
            # 添加处理时间头
            response.headers["X-Process-Time"] = str(process_time)
            
            return response
            
        except Exception as e:
            # 记录错误
            process_time = time.time() - start_time
            logger.error(
                f"Request failed: {request.method} {request.url} - "
                f"Error: {str(e)} - Time: {process_time:.3f}s"
            )
            raise
