"""
核心异常定义

定义系统中的基础异常类型
"""

from typing import Optional, Any, Dict


class BaseException(Exception):
    """基础异常类"""
    
    def __init__(self, message: str, code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}


class DomainException(BaseException):
    """领域异常"""
    
    def __init__(self, message: str, code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code, details)


class ApplicationException(BaseException):
    """应用异常"""
    
    def __init__(self, message: str, code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code, details)


class InfrastructureException(BaseException):
    """基础设施异常"""
    
    def __init__(self, message: str, code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code, details)


class ValidationException(DomainException):
    """验证异常"""
    pass


class NotFoundError(DomainException):
    """未找到异常"""
    pass


class ConflictError(DomainException):
    """冲突异常"""
    pass


class UnauthorizedError(ApplicationException):
    """未授权异常"""
    pass


class ForbiddenError(ApplicationException):
    """禁止访问异常"""
    pass
