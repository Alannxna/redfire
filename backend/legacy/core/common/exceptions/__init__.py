"""
统一异常定义模块
================

提供分层的异常定义，确保错误处理的一致性
"""

from .base_exceptions import (
    VnPyWebException,
    ValidationError,
    ConfigurationError,
    AuthenticationError,
    AuthorizationError
)

from .domain_exceptions import (
    DomainException,
    UserNotFoundError,
    InvalidUserError,
    TradingPermissionError,
    OrderValidationError,
    StrategyError,
    InsufficientFundsError
)

from .application_exceptions import (
    ApplicationException,
    CommandValidationError,
    QueryValidationError,
    CommandHandlerNotFoundError,
    QueryHandlerNotFoundError,
    ServiceUnavailableError,
    BusinessRuleViolationError,
    ConcurrencyConflictError,
    ResourceNotFoundError,
    DuplicateResourceError,
    PermissionDeniedError
)

# 添加别名以兼容旧代码
NotFoundException = ResourceNotFoundError
ValidationException = ValidationError

from .infrastructure_exceptions import (
    InfrastructureException,
    DatabaseConnectionError,
    CacheError,
    ExternalServiceError,
    NetworkError,
    TimeoutError
)

__all__ = [
    # 基础异常
    'VnPyWebException',
    'ValidationError',
    'ConfigurationError',
    'AuthenticationError',
    'AuthorizationError',
    
    # 应用层异常
    'ApplicationException',
    'CommandValidationError',
    'QueryValidationError',
    'CommandHandlerNotFoundError',
    'QueryHandlerNotFoundError',
    'ServiceUnavailableError',
    'BusinessRuleViolationError',
    'ConcurrencyConflictError',
    'ResourceNotFoundError',
    'DuplicateResourceError',
    'PermissionDeniedError',
    
    # 领域异常
    'DomainException',
    'UserNotFoundError',
    'InvalidUserError',
    'TradingPermissionError',
    'OrderValidationError',
    'StrategyError',
    'InsufficientFundsError',
    
    # 基础设施异常
    'InfrastructureException',
    'DatabaseConnectionError',
    'CacheError',
    'ExternalServiceError',
    'NetworkError',
    'TimeoutError',
    
    # 别名
    'NotFoundException',
    'ValidationException'
]
