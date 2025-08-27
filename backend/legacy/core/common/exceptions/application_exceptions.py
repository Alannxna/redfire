"""
应用层异常定义
==============

定义应用服务层的异常类型
"""

from .base_exceptions import VnPyWebException


class ApplicationException(VnPyWebException):
    """应用层异常基类"""
    
    def __init__(self, message: str, error_code: str = "APP_ERROR", details: dict = None):
        super().__init__(message, error_code, details)


class CommandValidationError(ApplicationException):
    """命令验证错误"""
    
    def __init__(self, message: str = "命令验证失败", details: dict = None):
        super().__init__(message, "COMMAND_VALIDATION_ERROR", details)


class QueryValidationError(ApplicationException):
    """查询验证错误"""
    
    def __init__(self, message: str = "查询验证失败", details: dict = None):
        super().__init__(message, "QUERY_VALIDATION_ERROR", details)


class CommandHandlerNotFoundError(ApplicationException):
    """命令处理器未找到错误"""
    
    def __init__(self, command_type: str):
        message = f"未找到命令 {command_type} 的处理器"
        super().__init__(message, "COMMAND_HANDLER_NOT_FOUND", {"command_type": command_type})


class QueryHandlerNotFoundError(ApplicationException):
    """查询处理器未找到错误"""
    
    def __init__(self, query_type: str):
        message = f"未找到查询 {query_type} 的处理器"
        super().__init__(message, "QUERY_HANDLER_NOT_FOUND", {"query_type": query_type})


class ServiceUnavailableError(ApplicationException):
    """服务不可用错误"""
    
    def __init__(self, service_name: str, message: str = None):
        message = message or f"服务 {service_name} 不可用"
        super().__init__(message, "SERVICE_UNAVAILABLE", {"service_name": service_name})


class BusinessRuleViolationError(ApplicationException):
    """业务规则违反错误"""
    
    def __init__(self, rule_name: str, message: str = None):
        message = message or f"违反业务规则: {rule_name}"
        super().__init__(message, "BUSINESS_RULE_VIOLATION", {"rule_name": rule_name})


class ConcurrencyConflictError(ApplicationException):
    """并发冲突错误"""
    
    def __init__(self, resource_id: str, resource_type: str = "resource"):
        message = f"{resource_type} {resource_id} 存在并发冲突"
        super().__init__(message, "CONCURRENCY_CONFLICT", {
            "resource_id": resource_id,
            "resource_type": resource_type
        })


class ResourceNotFoundError(ApplicationException):
    """资源未找到错误"""
    
    def __init__(self, resource_id: str, resource_type: str = "resource"):
        message = f"{resource_type} {resource_id} 未找到"
        super().__init__(message, "RESOURCE_NOT_FOUND", {
            "resource_id": resource_id,
            "resource_type": resource_type
        })


class DuplicateResourceError(ApplicationException):
    """重复资源错误"""
    
    def __init__(self, resource_id: str, resource_type: str = "resource"):
        message = f"{resource_type} {resource_id} 已存在"
        super().__init__(message, "DUPLICATE_RESOURCE", {
            "resource_id": resource_id,
            "resource_type": resource_type
        })


class PermissionDeniedError(ApplicationException):
    """权限拒绝错误"""
    
    def __init__(self, operation: str, resource: str = None):
        message = f"无权限执行操作: {operation}"
        if resource:
            message += f" on {resource}"
        super().__init__(message, "PERMISSION_DENIED", {
            "operation": operation,
            "resource": resource
        })
