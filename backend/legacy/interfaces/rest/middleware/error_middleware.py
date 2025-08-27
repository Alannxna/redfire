"""
错误处理中间件
==============

提供全局错误处理和异常捕获功能
"""

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import logging
from typing import Union
import traceback

from ..models.common import ErrorResponse, ValidationErrorResponse
from ....core.base.exceptions import DomainException


class ErrorHandlingMiddleware:
    """错误处理中间件"""
    
    def __init__(self):
        self._logger = logging.getLogger(self.__class__.__name__)
    
    async def handle_errors(self, request: Request, call_next):
        """错误处理"""
        try:
            response = await call_next(request)
            return response
            
        except HTTPException as e:
            # FastAPI HTTP异常
            return JSONResponse(
                status_code=e.status_code,
                content=ErrorResponse(
                    message=e.detail,
                    error_code="HTTP_EXCEPTION"
                ).dict()
            )
            
        except RequestValidationError as e:
            # Pydantic验证错误
            self._logger.warning(f"请求验证失败: {e}")
            
            errors = []
            for error in e.errors():
                errors.append({
                    "field": " -> ".join(str(loc) for loc in error["loc"]),
                    "message": error["msg"],
                    "type": error["type"]
                })
            
            return JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                content=ValidationErrorResponse(
                    message="请求参数验证失败",
                    errors=errors
                ).dict()
            )
            
        except DomainException as e:
            # 领域异常
            self._logger.warning(f"领域异常: {e}")
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=ErrorResponse(
                    message=str(e),
                    error_code="DOMAIN_EXCEPTION"
                ).dict()
            )
            
        except ValueError as e:
            # 值错误
            self._logger.warning(f"参数错误: {e}")
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=ErrorResponse(
                    message=str(e),
                    error_code="VALUE_ERROR"
                ).dict()
            )
            
        except Exception as e:
            # 未知异常
            self._logger.error(f"未处理的异常: {e}")
            self._logger.error(f"异常堆栈: {traceback.format_exc()}")
            
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=ErrorResponse(
                    message="服务器内部错误",
                    error_code="INTERNAL_ERROR",
                    error_detail=str(e) if self._is_debug_mode() else None
                ).dict()
            )
    
    def _is_debug_mode(self) -> bool:
        """检查是否为调试模式"""
        # 这里可以从配置中读取
        return True  # 暂时返回True用于开发