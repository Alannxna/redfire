"""
基础命令处理器
============

所有命令处理器的基类
"""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Any
from ..commands.base_command import CommandResult

# 定义命令类型变量
C = TypeVar('C')


class BaseCommandHandler(Generic[C], ABC):
    """基础命令处理器抽象基类"""
    
    def __init__(self):
        """初始化命令处理器"""
        pass
    
    @abstractmethod
    async def handle(self, command: C) -> CommandResult:
        """
        处理命令的抽象方法
        
        Args:
            command: 命令对象
            
        Returns:
            CommandResult: 命令执行结果
        """
        pass
    
    def validate_command(self, command: C) -> bool:
        """
        验证命令对象
        
        Args:
            command: 命令对象
            
        Returns:
            bool: 验证是否通过
        """
        return command is not None
    
    def pre_process(self, command: C) -> C:
        """
        命令预处理
        
        Args:
            command: 命令对象
            
        Returns:
            C: 处理后的命令对象
        """
        return command
    
    def post_process(self, result: CommandResult) -> CommandResult:
        """
        结果后处理
        
        Args:
            result: 命令执行结果
            
        Returns:
            CommandResult: 处理后的结果
        """
        return result
    
    async def execute(self, command: C) -> CommandResult:
        """
        执行命令的完整流程
        
        Args:
            command: 命令对象
            
        Returns:
            CommandResult: 命令执行结果
        """
        try:
            # 验证命令
            if not self.validate_command(command):
                return CommandResult(
                    success=False,
                    error="命令对象无效"
                )
            
            # 预处理
            processed_command = self.pre_process(command)
            
            # 执行命令
            result = await self.handle(processed_command)
            
            # 后处理
            final_result = self.post_process(result)
            
            return final_result
            
        except Exception as e:
            return CommandResult(
                success=False,
                error=f"命令执行失败: {str(e)}"
            )
