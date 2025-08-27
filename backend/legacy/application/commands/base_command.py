"""
基础命令和命令处理器

实现命令模式的基础抽象类
"""

# 标准库导入
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import TypeVar, Generic, Any, Dict, Optional

# 核心层导入
from ...core.base.exceptions import DomainException as ApplicationException


@dataclass
class BaseCommand(ABC):
    """命令基类
    
    所有命令都应继承此类
    命令是不可变对象，包含执行操作所需的所有数据
    """
    command_id: Optional[str] = None
    user_id: Optional[str] = None
    timestamp: Optional[datetime] = None
    
    def __post_init__(self):
        if self.command_id is None:
            self.command_id = str(uuid.uuid4())
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'command_id': self.command_id,
            'user_id': self.user_id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'command_type': self.__class__.__name__
        }


TCommand = TypeVar('TCommand', bound=BaseCommand)
TResult = TypeVar('TResult')


class BaseCommandHandler(Generic[TCommand, TResult], ABC):
    """命令处理器基类
    
    负责处理特定类型的命令
    实现命令验证、执行和结果返回
    """
    
    @abstractmethod
    async def handle(self, command: TCommand) -> TResult:
        """处理命令
        
        Args:
            command: 要处理的命令
            
        Returns:
            命令执行结果
            
        Raises:
            ApplicationException: 命令处理失败
        """
        pass
    
    async def validate(self, command: TCommand) -> None:
        """验证命令
        
        Args:
            command: 要验证的命令
            
        Raises:
            ApplicationException: 验证失败
        """
        if not command.command_id:
            raise ApplicationException("命令ID不能为空")
    
    def get_command_type(self) -> type:
        """获取处理的命令类型"""
        return self.__orig_bases__[0].__args__[0]


class CommandResult:
    """命令执行结果"""
    
    def __init__(self, success: bool = True, data: Any = None, 
                 message: str = "", errors: Optional[Dict[str, str]] = None):
        self.success = success
        self.data = data
        self.message = message
        self.errors = errors or {}
        self.timestamp = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'success': self.success,
            'data': self.data,
            'message': self.message,
            'errors': self.errors,
            'timestamp': self.timestamp.isoformat()
        }
    
    @classmethod
    def success_result(cls, data: Any = None, message: str = "操作成功") -> 'CommandResult':
        """创建成功结果"""
        return cls(success=True, data=data, message=message)
    
    @classmethod
    def failure_result(cls, message: str = "操作失败", 
                      errors: Optional[Dict[str, str]] = None) -> 'CommandResult':
        """创建失败结果"""
        return cls(success=False, message=message, errors=errors)
