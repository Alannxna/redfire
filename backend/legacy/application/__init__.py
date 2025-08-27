"""
应用层 - CQRS架构实现
提供命令查询责任分离的应用服务接口和统一初始化系统
"""

from .commands.command_bus import CommandBus
from .queries.query_bus import QueryBus
from .services.base_application_service import BaseApplicationService

# 用户相关
from .commands.user_commands import *
from .queries.user_queries import *
from .handlers.user_command_handlers import *
from .handlers.user_query_handlers import *
from .services.user_application_service import UserApplicationService

# 新的初始化系统
from .application_initializer import (
    ApplicationInitializer,
    ApplicationInitializationOptions,
    ApplicationInitializationResult,
    initialize_application_layer
)

# CQRS配置管理
from .cqrs import (
    CQRSConfigurationManager,
    initialize_cqrs,
    get_cqrs_manager
)

# 依赖注入助手
from .di import (
    DependencyInjectionHelper,
    create_di_helper,
    get_di_helper
)

__all__ = [
    # CQRS基础设施
    "CommandBus",
    "QueryBus",
    "BaseApplicationService",
    
    # 用户模块
    "UserApplicationService",
    
    # 命令
    "CreateUserCommand",
    "UpdateUserProfileCommand", 
    "ChangeUserPasswordCommand",
    "ChangeUserRoleCommand",
    "ActivateUserCommand",
    "DeactivateUserCommand",
    "DeleteUserCommand",
    "LoginUserCommand",
    "LogoutUserCommand",
    
    # 查询
    "GetUserByIdQuery",
    "GetUserByUsernameQuery", 
    "GetUserByEmailQuery",
    "GetUsersQuery",
    "SearchUsersQuery",
    "GetUserProfileQuery",
    "ValidateUserCredentialsQuery",
    "CheckUsernameAvailabilityQuery",
    "CheckEmailAvailabilityQuery",
    
    # 处理器
    "CreateUserCommandHandler",
    "UpdateUserProfileCommandHandler",
    "ChangeUserPasswordCommandHandler", 
    "ChangeUserRoleCommandHandler",
    "ActivateUserCommandHandler",
    "DeactivateUserCommandHandler",
    "LoginUserCommandHandler",
    
    "GetUserByIdQueryHandler",
    "GetUserByUsernameQueryHandler",
    "GetUserByEmailQueryHandler", 
    "GetUsersQueryHandler",
    "SearchUsersQueryHandler",
    "GetUserProfileQueryHandler",
    "ValidateUserCredentialsQueryHandler",
    "CheckUsernameAvailabilityQueryHandler",
    "CheckEmailAvailabilityQueryHandler",
    
    # 新的初始化系统
    "ApplicationInitializer",
    "ApplicationInitializationOptions",
    "ApplicationInitializationResult",
    "initialize_application_layer",
    
    # CQRS配置管理
    "CQRSConfigurationManager",
    "initialize_cqrs",
    "get_cqrs_manager",
    
    # 依赖注入助手
    "DependencyInjectionHelper",
    "create_di_helper",
    "get_di_helper",
]