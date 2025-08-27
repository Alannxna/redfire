"""
基础异常定义
============

定义系统的基础异常类
"""

from typing import Any, Dict, Optional


class VnPyWebException(Exception):
    """VnPy Web系统基础异常类"""
    
    def __init__(
        self, 
        message: str, 
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "error_type": self.__class__.__name__,
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details
        }


class ValidationError(VnPyWebException):
    """数据验证异常"""
    
    def __init__(self, field: str, value: Any, message: str):
        super().__init__(f"验证失败: {field} = {value}, {message}")
        self.field = field
        self.value = value
        self.details = {"field": field, "value": str(value)}


class ConfigurationError(VnPyWebException):
    """配置错误异常"""
    
    def __init__(self, config_key: str, message: str):
        super().__init__(f"配置错误: {config_key}, {message}")
        self.config_key = config_key
        self.details = {"config_key": config_key}


class AuthenticationError(VnPyWebException):
    """认证失败异常"""
    
    def __init__(self, message: str = "认证失败", username: Optional[str] = None):
        super().__init__(message)
        if username:
            self.details = {"username": username}


class AuthorizationError(VnPyWebException):
    """授权失败异常"""
    
    def __init__(
        self, 
        message: str = "权限不足", 
        required_permission: Optional[str] = None,
        user_permissions: Optional[list] = None
    ):
        super().__init__(message)
        self.details = {
            "required_permission": required_permission,
            "user_permissions": user_permissions or []
        }


class ServiceUnavailableError(VnPyWebException):
    """服务不可用异常"""
    
    def __init__(self, service_name: str, message: str = "服务暂时不可用"):
        super().__init__(f"{service_name}: {message}")
        self.service_name = service_name
        self.details = {"service_name": service_name}


class RateLimitError(VnPyWebException):
    """频率限制异常"""
    
    def __init__(self, limit: int, window: int, message: str = "请求频率过高"):
        super().__init__(f"{message}，限制: {limit}次/{window}秒")
        self.limit = limit
        self.window = window
        self.details = {"limit": limit, "window": window}
