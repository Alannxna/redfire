"""
基础应用服务
============

提供应用服务的基础功能和通用接口
"""

# 标准库导入
import logging
from abc import ABC, abstractmethod
from typing import Any, Optional, Dict

# 核心层导入
from ...core.base.exceptions import DomainException

# 应用层内部导入
from ..commands.command_bus import CommandBus, Command, CommandResult
from ..queries.query_bus import QueryBus, Query, QueryResult


class BaseApplicationService(ABC):
    """基础应用服务"""
    
    def __init__(self, command_bus: CommandBus, query_bus: QueryBus):
        self._command_bus = command_bus
        self._query_bus = query_bus
        self._logger = logging.getLogger(self.__class__.__name__)
    
    async def execute_command(self, command: Command) -> CommandResult:
        """执行命令"""
        try:
            self._logger.info(f"执行命令: {command.__class__.__name__}")
            return await self._command_bus.dispatch(command)
        except Exception as e:
            self._logger.error(f"命令执行失败: {e}")
            return CommandResult(success=False, error=str(e))
    
    async def execute_query(self, query: Query) -> QueryResult:
        """执行查询"""
        try:
            self._logger.info(f"执行查询: {query.__class__.__name__}")
            return await self._query_bus.dispatch(query)
        except Exception as e:
            self._logger.error(f"查询执行失败: {e}")
            return QueryResult(success=False, error=str(e))
    
    def _validate_input(self, data: Dict[str, Any], required_fields: list) -> None:
        """验证输入数据"""
        missing_fields = []
        for field in required_fields:
            if field not in data or data[field] is None:
                missing_fields.append(field)
        
        if missing_fields:
            raise DomainException(f"缺少必需字段: {', '.join(missing_fields)}")
    
    def _sanitize_input(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """清理输入数据"""
        sanitized = {}
        for key, value in data.items():
            if isinstance(value, str):
                sanitized[key] = value.strip()
            else:
                sanitized[key] = value
        return sanitized
    
    @abstractmethod
    def get_service_info(self) -> Dict[str, Any]:
        """获取服务信息"""
        pass