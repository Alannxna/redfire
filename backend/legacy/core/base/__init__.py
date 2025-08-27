"""
统一服务基类模块
================

提供统一的服务架构基类，所有服务必须继承这些基类
"""

from .service_base import BaseService, ServiceConfig
from .domain_service import BaseDomainService, DomainServiceConfig
from .application_service import BaseApplicationService, ApplicationServiceConfig, WorkflowDefinition, WorkflowStep
from .infrastructure_service import BaseInfrastructureService, InfrastructureServiceConfig
from .repository_base import BaseRepository
from .entity_base import BaseEntity
from .value_object_base import BaseValueObject
from .exceptions import (
    BaseException,
    DomainException,
    ApplicationException,
    InfrastructureException,
    ValidationException,
    NotFoundError,
    ConflictError,
    UnauthorizedError,
    ForbiddenError
)

__all__ = [
    # 基础服务类
    'BaseService',
    'ServiceConfig',
    
    # 领域服务类
    'BaseDomainService',
    'DomainServiceConfig',
    
    # 应用服务类
    'BaseApplicationService',
    'ApplicationServiceConfig',
    'WorkflowDefinition',
    'WorkflowStep',
    
    # 基础设施服务类
    'BaseInfrastructureService',
    'InfrastructureServiceConfig',
    
    # 领域驱动设计基类
    'BaseRepository',
    'BaseEntity',
    'BaseValueObject',
    
    # 异常类
    'BaseException',
    'DomainException',
    'ApplicationException',
    'InfrastructureException',
    'ValidationException',
    'NotFoundError',
    'ConflictError',
    'UnauthorizedError',
    'ForbiddenError'
]
