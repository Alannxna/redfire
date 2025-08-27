"""
命令总线实现
============

提供命令的分发和处理功能
"""

# 标准库导入
import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, Type, Any, Optional

# 核心层导入
from ...core.base.exceptions import DomainException

# 领域层导入
from ...domain.shared.events.domain_event import DomainEvent


class Command(ABC):
    """命令基类"""
    
    def __init__(self):
        self.command_id: str = ""
        self.timestamp: str = ""
        self.user_id: Optional[str] = None
        self.correlation_id: Optional[str] = None


class CommandHandler(ABC):
    """命令处理器基类"""
    
    @abstractmethod
    async def handle(self, command: Command) -> Any:
        """处理命令"""
        pass


class CommandResult:
    """命令执行结果"""
    
    def __init__(self, success: bool = True, data: Any = None, 
                 error: Optional[str] = None, events: Optional[list] = None):
        self.success = success
        self.data = data
        self.error = error
        self.events = events or []


class ICommandBus(ABC):
    """命令总线接口"""
    
    @abstractmethod
    async def dispatch(self, command: Command) -> CommandResult:
        """分发命令"""
        pass
    
    @abstractmethod
    def register_handler(self, command_type: Type[Command], handler: CommandHandler) -> None:
        """注册命令处理器"""
        pass


class CommandBus(ICommandBus):
    """命令总线"""
    
    def __init__(self):
        self._handlers: Dict[Type[Command], CommandHandler] = {}
        self._logger = logging.getLogger(__name__)
    
    def register_handler(self, command_type: Type[Command], handler: CommandHandler):
        """注册命令处理器"""
        self._handlers[command_type] = handler
        self._logger.debug(f"注册命令处理器: {command_type.__name__} -> {handler.__class__.__name__}")
    
    async def dispatch(self, command: Command) -> CommandResult:
        """分发命令"""
        command_type = type(command)
        
        if command_type not in self._handlers:
            error_msg = f"未找到命令处理器: {command_type.__name__}"
            self._logger.error(error_msg)
            return CommandResult(success=False, error=error_msg)
        
        handler = self._handlers[command_type]
        
        try:
            self._logger.info(f"执行命令: {command_type.__name__}")
            result = await handler.handle(command)
            
            return CommandResult(success=True, data=result)
            
        except DomainException as e:
            self._logger.warning(f"命令执行失败 - 领域异常: {e}")
            return CommandResult(success=False, error=str(e))
            
        except Exception as e:
            self._logger.error(f"命令执行失败 - 系统异常: {e}")
            return CommandResult(success=False, error=f"系统错误: {str(e)}")
    
    def get_registered_handlers(self) -> Dict[str, str]:
        """获取已注册的处理器列表"""
        return {
            cmd_type.__name__: handler.__class__.__name__ 
            for cmd_type, handler in self._handlers.items()
        }


# 全局命令总线实例
command_bus = CommandBus()