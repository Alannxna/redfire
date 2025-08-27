"""
命令总线和基础设施
================

提供命令处理的基础设施和接口定义
"""

from .base_command import BaseCommand, BaseCommandHandler, CommandResult
from .command_bus import CommandBus, ICommandBus, CommandHandler

# 为了保持兼容性，创建一些别名
Command = BaseCommand
Result = CommandResult

__all__ = [
    'BaseCommand',
    'BaseCommandHandler', 
    'CommandResult',
    'CommandBus',
    'ICommandBus',
    'CommandHandler',
    'Command',
    'Result'
]
