"""
基础设施异常定义
================

定义基础设施层的技术异常
"""

from typing import Any, Dict, Optional
from .base_exceptions import VnPyWebException


class InfrastructureException(VnPyWebException):
    """基础设施层基础异常"""
    pass


# 数据库异常
class DatabaseError(InfrastructureException):
    """数据库基础异常"""
    
    def __init__(self, operation: str, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(f"数据库操作失败: {operation}, {message}")
        self.operation = operation
        self.details = details or {"operation": operation}


class DatabaseConnectionError(DatabaseError):
    """数据库连接异常"""
    
    def __init__(self, host: str, database: str, reason: str):
        super().__init__(
            "连接",
            f"无法连接到数据库 {database}@{host}，原因: {reason}",
            {"host": host, "database": database, "reason": reason}
        )


class DatabaseTimeoutError(DatabaseError):
    """数据库超时异常"""
    
    def __init__(self, operation: str, timeout: int):
        super().__init__(
            operation,
            f"操作超时，超时时间: {timeout}秒",
            {"timeout": timeout}
        )


class DatabaseTransactionError(DatabaseError):
    """数据库事务异常"""
    
    def __init__(self, operation: str, reason: str):
        super().__init__(
            f"事务{operation}",
            reason,
            {"transaction_operation": operation}
        )


# 缓存异常
class CacheError(InfrastructureException):
    """缓存异常基类"""
    
    def __init__(self, operation: str, key: str, message: str):
        super().__init__(f"缓存操作失败: {operation} key={key}, {message}")
        self.operation = operation
        self.key = key
        self.details = {"operation": operation, "key": key}


class CacheConnectionError(CacheError):
    """缓存连接异常"""
    
    def __init__(self, host: str, port: int, reason: str):
        super().__init__(
            "连接",
            f"{host}:{port}",
            f"无法连接到缓存服务器，原因: {reason}"
        )
        self.details.update({"host": host, "port": port, "reason": reason})


class CacheTimeoutError(CacheError):
    """缓存超时异常"""
    
    def __init__(self, operation: str, key: str, timeout: int):
        super().__init__(operation, key, f"操作超时，超时时间: {timeout}秒")
        self.details.update({"timeout": timeout})


# 网络异常
class NetworkError(InfrastructureException):
    """网络异常基类"""
    
    def __init__(self, url: str, operation: str, message: str):
        super().__init__(f"网络请求失败: {operation} {url}, {message}")
        self.url = url
        self.operation = operation
        self.details = {"url": url, "operation": operation}


class ExternalServiceError(NetworkError):
    """外部服务异常"""
    
    def __init__(self, service_name: str, url: str, status_code: int, response: str):
        super().__init__(
            url,
            f"{service_name}服务调用",
            f"状态码: {status_code}, 响应: {response}"
        )
        self.service_name = service_name
        self.status_code = status_code
        self.response = response
        self.details.update({
            "service_name": service_name,
            "status_code": status_code,
            "response": response
        })


class TimeoutError(NetworkError):
    """超时异常"""
    
    def __init__(self, url: str, timeout: int, operation: str = "请求"):
        super().__init__(url, operation, f"请求超时，超时时间: {timeout}秒")
        self.timeout = timeout
        self.details.update({"timeout": timeout})


class ConnectionError(NetworkError):
    """连接异常"""
    
    def __init__(self, url: str, reason: str):
        super().__init__(url, "连接", f"连接失败，原因: {reason}")
        self.reason = reason
        self.details.update({"reason": reason})


# 消息队列异常
class MessagingError(InfrastructureException):
    """消息队列异常基类"""
    
    def __init__(self, operation: str, topic: str, message: str):
        super().__init__(f"消息操作失败: {operation} topic={topic}, {message}")
        self.operation = operation
        self.topic = topic
        self.details = {"operation": operation, "topic": topic}


class MessagePublishError(MessagingError):
    """消息发布异常"""
    
    def __init__(self, topic: str, reason: str):
        super().__init__("发布", topic, reason)


class MessageConsumeError(MessagingError):
    """消息消费异常"""
    
    def __init__(self, topic: str, reason: str):
        super().__init__("消费", topic, reason)


# 文件系统异常
class FileSystemError(InfrastructureException):
    """文件系统异常基类"""
    
    def __init__(self, operation: str, path: str, message: str):
        super().__init__(f"文件操作失败: {operation} {path}, {message}")
        self.operation = operation
        self.path = path
        self.details = {"operation": operation, "path": path}


class FileNotFoundError(FileSystemError):
    """文件未找到异常"""
    
    def __init__(self, path: str):
        super().__init__("读取", path, "文件不存在")


class FilePermissionError(FileSystemError):
    """文件权限异常"""
    
    def __init__(self, operation: str, path: str):
        super().__init__(operation, path, "权限不足")


class DiskSpaceError(FileSystemError):
    """磁盘空间不足异常"""
    
    def __init__(self, path: str, required: int, available: int):
        super().__init__(
            "写入",
            path,
            f"磁盘空间不足，需要: {required}字节, 可用: {available}字节"
        )
        self.required = required
        self.available = available
        self.details.update({
            "required": required,
            "available": available
        })


# 配置异常
class ConfigurationError(InfrastructureException):
    """配置异常"""
    
    def __init__(self, config_key: str, reason: str, config_file: Optional[str] = None):
        super().__init__(f"配置错误: {config_key}, {reason}")
        self.config_key = config_key
        self.config_file = config_file
        self.reason = reason
        self.details = {
            "config_key": config_key,
            "config_file": config_file,
            "reason": reason
        }


class MissingConfigurationError(ConfigurationError):
    """缺少配置异常"""
    
    def __init__(self, config_key: str, config_file: Optional[str] = None):
        super().__init__(config_key, "配置项缺失", config_file)


class InvalidConfigurationError(ConfigurationError):
    """无效配置异常"""
    
    def __init__(self, config_key: str, value: Any, expected_type: str, config_file: Optional[str] = None):
        super().__init__(
            config_key,
            f"配置值无效，值: {value}, 期望类型: {expected_type}",
            config_file
        )
        self.value = value
        self.expected_type = expected_type
        self.details.update({
            "value": str(value),
            "expected_type": expected_type
        })
