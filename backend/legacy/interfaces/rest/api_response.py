"""
API响应格式

统一的API响应格式定义
"""

from typing import Any, Optional, Dict
from datetime import datetime
from pydantic import BaseModel
from fastapi import HTTPException
from fastapi.responses import JSONResponse


class APIResponse(BaseModel):
    """API响应基类"""
    success: bool = True
    message: str = "操作成功"
    data: Any = None
    timestamp: str = None
    
    def __init__(self, **data):
        if 'timestamp' not in data:
            data['timestamp'] = datetime.utcnow().isoformat()
        super().__init__(**data)
    
    @classmethod
    def success(cls, data: Any = None, message: str = "操作成功") -> 'APIResponse':
        """创建成功响应"""
        return cls(success=True, data=data, message=message)
    
    @classmethod
    def error(cls, message: str = "操作失败", data: Any = None) -> 'APIResponse':
        """创建错误响应"""
        return cls(success=False, message=message, data=data)


class PaginatedResponse(APIResponse):
    """分页响应"""
    pagination: Dict[str, Any] = None
    
    @classmethod
    def create(cls, data: list, total_count: int, page: int, page_size: int,
              message: str = "查询成功") -> 'PaginatedResponse':
        """创建分页响应"""
        total_pages = (total_count + page_size - 1) // page_size
        
        pagination = {
            'total_count': total_count,
            'total_pages': total_pages,
            'current_page': page,
            'page_size': page_size,
            'has_next': page < total_pages,
            'has_previous': page > 1
        }
        
        return cls(
            success=True,
            data=data,
            message=message,
            pagination=pagination
        )


class APIError(HTTPException):
    """API错误响应"""
    
    def __init__(self, message: str, status_code: int = 400, 
                 details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        self.timestamp = datetime.utcnow().isoformat()
        
        detail = {
            'success': False,
            'message': message,
            'details': self.details,
            'timestamp': self.timestamp
        }
        
        super().__init__(status_code=status_code, detail=detail)
    
    @classmethod
    def bad_request(cls, message: str = "请求参数错误", 
                   details: Optional[Dict[str, Any]] = None) -> 'APIError':
        """400 错误请求"""
        return cls(message=message, status_code=400, details=details)
    
    @classmethod
    def unauthorized(cls, message: str = "未授权访问") -> 'APIError':
        """401 未授权"""
        return cls(message=message, status_code=401)
    
    @classmethod
    def forbidden(cls, message: str = "禁止访问") -> 'APIError':
        """403 禁止访问"""
        return cls(message=message, status_code=403)
    
    @classmethod
    def not_found(cls, message: str = "资源未找到") -> 'APIError':
        """404 未找到"""
        return cls(message=message, status_code=404)
    
    @classmethod
    def conflict(cls, message: str = "资源冲突") -> 'APIError':
        """409 冲突"""
        return cls(message=message, status_code=409)
    
    @classmethod
    def unprocessable_entity(cls, message: str = "无法处理的实体", 
                           details: Optional[Dict[str, Any]] = None) -> 'APIError':
        """422 无法处理的实体"""
        return cls(message=message, status_code=422, details=details)
    
    @classmethod
    def internal_server_error(cls, message: str = "服务器内部错误") -> 'APIError':
        """500 服务器内部错误"""
        return cls(message=message, status_code=500)


def create_error_response(status_code: int, message: str, 
                         details: Optional[Dict[str, Any]] = None) -> JSONResponse:
    """创建错误响应的便捷函数"""
    content = {
        'success': False,
        'message': message,
        'details': details or {},
        'timestamp': datetime.utcnow().isoformat()
    }
    
    return JSONResponse(
        status_code=status_code,
        content=content
    )


def create_success_response(data: Any = None, message: str = "操作成功") -> JSONResponse:
    """创建成功响应的便捷函数"""
    content = {
        'success': True,
        'message': message,
        'data': data,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    return JSONResponse(
        status_code=200,
        content=content
    )
