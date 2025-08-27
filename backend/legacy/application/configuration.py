"""
应用层配置（兼容版本）
===================

为了保持向后兼容性而保留的传统配置模块
推荐使用新的 ApplicationInitializer 进行应用初始化
"""

# 标准库导入
from typing import Dict, Type, Any
import logging

# 核心层导入
from ..core.infrastructure.dependency_container import DependencyContainer as IServiceContainer

# 应用层内部导入
from .commands.command_bus import ICommandBus, CommandBus, CommandHandler
from .queries.query_bus import IQueryBus, QueryBus, QueryHandler

# 新的初始化系统
from .application_initializer import (
    ApplicationInitializer, 
    ApplicationInitializationOptions,
    initialize_application_layer
)


logger = logging.getLogger(__name__)


class ApplicationConfiguration:
    """应用层配置类"""
    
    @staticmethod
    def configure_services(container: IServiceContainer) -> None:
        """配置应用层服务"""
        logger.info("配置应用层服务...")
        
        # 注册CQRS基础设施
        ApplicationConfiguration._register_cqrs_infrastructure(container)
        
        # 注册用户模块
        ApplicationConfiguration._register_user_module(container)
        
        # 注册应用服务
        ApplicationConfiguration._register_application_services(container)
        
        logger.info("应用层服务配置完成")
    
    @staticmethod
    def _register_cqrs_infrastructure(container: IServiceContainer) -> None:
        """注册CQRS基础设施"""
        # 注册命令总线
        container.register_singleton(ICommandBus, CommandBus)
        container.register_singleton(CommandBus, CommandBus)
        
        # 注册查询总线
        container.register_singleton(IQueryBus, QueryBus)
        container.register_singleton(QueryBus, QueryBus)
    
    @staticmethod
    def _register_user_module(container: IServiceContainer) -> None:
        """注册用户模块处理器"""
        
        # 注册命令处理器
        container.register_transient(
            CreateUserCommandHandler,
            CreateUserCommandHandler
        )
        container.register_transient(
            UpdateUserProfileCommandHandler,
            UpdateUserProfileCommandHandler
        )
        container.register_transient(
            ChangeUserPasswordCommandHandler,
            ChangeUserPasswordCommandHandler
        )
        container.register_transient(
            ChangeUserRoleCommandHandler,
            ChangeUserRoleCommandHandler
        )
        container.register_transient(
            ActivateUserCommandHandler,
            ActivateUserCommandHandler
        )
        container.register_transient(
            DeactivateUserCommandHandler,
            DeactivateUserCommandHandler
        )
        container.register_transient(
            LoginUserCommandHandler,
            LoginUserCommandHandler
        )
        
        # 注册查询处理器
        container.register_transient(
            GetUserByIdQueryHandler,
            GetUserByIdQueryHandler
        )
        container.register_transient(
            GetUserByUsernameQueryHandler,
            GetUserByUsernameQueryHandler
        )
        container.register_transient(
            GetUserByEmailQueryHandler,
            GetUserByEmailQueryHandler
        )
        container.register_transient(
            GetUsersQueryHandler,
            GetUsersQueryHandler
        )
        container.register_transient(
            SearchUsersQueryHandler,
            SearchUsersQueryHandler
        )
        container.register_transient(
            GetUserProfileQueryHandler,
            GetUserProfileQueryHandler
        )
        container.register_transient(
            ValidateUserCredentialsQueryHandler,
            ValidateUserCredentialsQueryHandler
        )
        container.register_transient(
            CheckUsernameAvailabilityQueryHandler,
            CheckUsernameAvailabilityQueryHandler
        )
        container.register_transient(
            CheckEmailAvailabilityQueryHandler,
            CheckEmailAvailabilityQueryHandler
        )
    
    @staticmethod
    def _register_application_services(container: IServiceContainer) -> None:
        """注册应用服务"""
        container.register_scoped(UserApplicationService, UserApplicationService)
    
    @staticmethod
    async def configure_handlers(container: IServiceContainer) -> None:
        """配置处理器映射"""
        logger.info("配置CQRS处理器映射...")
        
        # 获取总线
        command_bus = container.resolve(CommandBus)
        query_bus = container.resolve(QueryBus)
        
        # 配置命令处理器映射
        await ApplicationConfiguration._configure_command_handlers(container, command_bus)
        
        # 配置查询处理器映射
        await ApplicationConfiguration._configure_query_handlers(container, query_bus)
        
        logger.info("CQRS处理器映射配置完成")
    
    @staticmethod
    async def _configure_command_handlers(
        container: IServiceContainer,
        command_bus: CommandBus
    ) -> None:
        """配置命令处理器映射"""
        
        # 用户命令处理器映射
        command_handlers = {
            CreateUserCommand: CreateUserCommandHandler,
            UpdateUserProfileCommand: UpdateUserProfileCommandHandler,
            ChangeUserPasswordCommand: ChangeUserPasswordCommandHandler,
            ChangeUserRoleCommand: ChangeUserRoleCommandHandler,
            ActivateUserCommand: ActivateUserCommandHandler,
            DeactivateUserCommand: DeactivateUserCommandHandler,
            LoginUserCommand: LoginUserCommandHandler,
        }
        
        # 注册处理器
        for command_type, handler_type in command_handlers.items():
            handler = container.resolve(handler_type)
            await command_bus.register_handler(command_type, handler)
            logger.debug(f"注册命令处理器: {command_type.__name__} -> {handler_type.__name__}")
    
    @staticmethod
    async def _configure_query_handlers(
        container: IServiceContainer,
        query_bus: QueryBus
    ) -> None:
        """配置查询处理器映射"""
        
        # 用户查询处理器映射
        query_handlers = {
            GetUserByIdQuery: GetUserByIdQueryHandler,
            GetUserByUsernameQuery: GetUserByUsernameQueryHandler,
            GetUserByEmailQuery: GetUserByEmailQueryHandler,
            GetUsersQuery: GetUsersQueryHandler,
            SearchUsersQuery: SearchUsersQueryHandler,
            GetUserProfileQuery: GetUserProfileQueryHandler,
            ValidateUserCredentialsQuery: ValidateUserCredentialsQueryHandler,
            CheckUsernameAvailabilityQuery: CheckUsernameAvailabilityQueryHandler,
            CheckEmailAvailabilityQuery: CheckEmailAvailabilityQueryHandler,
        }
        
        # 注册处理器
        for query_type, handler_type in query_handlers.items():
            handler = container.resolve(handler_type)
            await query_bus.register_handler(query_type, handler)
            logger.debug(f"注册查询处理器: {query_type.__name__} -> {handler_type.__name__}")


async def configure_application_layer(container: IServiceContainer) -> None:
    """配置应用层（兼容版本）
    
    此函数保留用于向后兼容性，推荐使用新的 initialize_application_layer
    """
    logger.warning("使用了兼容版本的 configure_application_layer，推荐使用 initialize_application_layer")
    
    # 使用新的初始化系统
    options = ApplicationInitializationOptions(
        enable_cqrs_auto_discovery=True,
        enable_dependency_validation=True
    )
    
    result = await initialize_application_layer(container, options)
    
    if not result.success:
        error_msg = f"应用层配置失败: {', '.join(result.errors)}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    
    logger.info("应用层配置完成（通过新系统）")
