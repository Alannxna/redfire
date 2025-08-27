"""
日志格式化器

提供多种日志输出格式
"""

import json
import logging
import traceback
from datetime import datetime
from typing import Dict, Any, Optional


class StructuredFormatter(logging.Formatter):
    """结构化日志格式化器
    
    提供易读的结构化日志输出
    """
    
    # ANSI颜色代码
    COLORS = {
        'DEBUG': '\033[36m',      # 青色
        'INFO': '\033[32m',       # 绿色
        'WARNING': '\033[33m',    # 黄色
        'ERROR': '\033[31m',      # 红色
        'CRITICAL': '\033[35m',   # 紫色
        'RESET': '\033[0m'        # 重置
    }
    
    def __init__(self, include_service_name: bool = True, use_colors: bool = True,
                 extra_fields: Optional[Dict[str, Any]] = None):
        super().__init__()
        self.include_service_name = include_service_name
        self.use_colors = use_colors
        self.extra_fields = extra_fields or {}
    
    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录"""
        # 基础信息
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        level = record.levelname
        logger_name = record.name
        message = record.getMessage()
        
        # 应用颜色
        if self.use_colors:
            level_colored = f"{self.COLORS.get(level, '')}{level:<8}{self.COLORS['RESET']}"
            logger_colored = f"\033[34m{logger_name}\033[0m"  # 蓝色
        else:
            level_colored = f"{level:<8}"
            logger_colored = logger_name
        
        # 构建基础格式
        if self.include_service_name:
            parts = [
                f"[{timestamp}]",
                f"{level_colored}",
                f"{logger_colored}:",
                message
            ]
        else:
            parts = [
                f"[{timestamp}]",
                f"{level_colored}",
                message
            ]
        
        base_message = " ".join(parts)
        
        # 添加异常信息
        if record.exc_info:
            exc_text = self.formatException(record.exc_info)
            base_message += f"\n{exc_text}"
        
        # 添加额外字段
        extra_info = []
        for key, value in self.extra_fields.items():
            extra_info.append(f"{key}={value}")
        
        # 添加记录中的额外字段
        for key, value in record.__dict__.items():
            if key not in ('name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                          'filename', 'module', 'lineno', 'funcName', 'created', 'msecs',
                          'relativeCreated', 'thread', 'threadName', 'processName',
                          'process', 'getMessage', 'exc_info', 'exc_text', 'stack_info'):
                extra_info.append(f"{key}={value}")
        
        if extra_info:
            base_message += f" [{', '.join(extra_info)}]"
        
        return base_message


class JSONFormatter(logging.Formatter):
    """JSON格式化器
    
    输出JSON格式的日志，便于日志分析系统处理
    """
    
    def __init__(self, include_service_name: bool = True, 
                 extra_fields: Optional[Dict[str, Any]] = None):
        super().__init__()
        self.include_service_name = include_service_name
        self.extra_fields = extra_fields or {}
    
    def format(self, record: logging.LogRecord) -> str:
        """格式化为JSON格式"""
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "thread": record.thread,
            "thread_name": record.threadName,
            "process": record.process,
            "process_name": record.processName
        }
        
        # 添加日志记录器名称
        if self.include_service_name:
            log_entry["logger"] = record.name
        
        # 添加额外字段
        log_entry.update(self.extra_fields)
        
        # 添加记录中的自定义字段
        for key, value in record.__dict__.items():
            if key not in ('name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                          'filename', 'module', 'lineno', 'funcName', 'created', 'msecs',
                          'relativeCreated', 'thread', 'threadName', 'processName',
                          'process', 'getMessage', 'exc_info', 'exc_text', 'stack_info'):
                # 确保值是JSON可序列化的
                try:
                    json.dumps(value)
                    log_entry[key] = value
                except (TypeError, ValueError):
                    log_entry[key] = str(value)
        
        # 添加异常信息
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": self.formatException(record.exc_info)
            }
        
        # 添加堆栈信息
        if record.stack_info:
            log_entry["stack_info"] = record.stack_info
        
        return json.dumps(log_entry, ensure_ascii=False, default=str)


class CompactFormatter(logging.Formatter):
    """紧凑格式化器
    
    提供紧凑的单行日志格式，适用于开发调试
    """
    
    def __init__(self, include_timestamp: bool = True):
        super().__init__()
        self.include_timestamp = include_timestamp
    
    def format(self, record: logging.LogRecord) -> str:
        """格式化为紧凑格式"""
        parts = []
        
        if self.include_timestamp:
            timestamp = datetime.fromtimestamp(record.created).strftime('%H:%M:%S')
            parts.append(f"[{timestamp}]")
        
        parts.extend([
            f"{record.levelname[0]}",  # 只显示级别首字母
            f"{record.name}:",
            record.getMessage()
        ])
        
        message = " ".join(parts)
        
        # 添加异常信息（简化）
        if record.exc_info and record.exc_info[1]:
            message += f" | {record.exc_info[0].__name__}: {record.exc_info[1]}"
        
        return message


class RequestFormatter(logging.Formatter):
    """请求日志格式化器
    
    专门用于HTTP请求日志
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """格式化请求日志"""
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')
        
        # 提取请求相关信息
        method = getattr(record, 'method', 'UNKNOWN')
        path = getattr(record, 'path', 'UNKNOWN')
        status_code = getattr(record, 'status_code', 'UNKNOWN')
        response_time = getattr(record, 'response_time', 'UNKNOWN')
        user_agent = getattr(record, 'user_agent', 'UNKNOWN')
        remote_addr = getattr(record, 'remote_addr', 'UNKNOWN')
        
        # 根据状态码设置颜色
        if isinstance(status_code, int):
            if status_code < 400:
                status_color = '\033[32m'  # 绿色
            elif status_code < 500:
                status_color = '\033[33m'  # 黄色
            else:
                status_color = '\033[31m'  # 红色
        else:
            status_color = ''
        
        message = (
            f"[{timestamp}] {remote_addr} - "
            f"{method} {path} - "
            f"{status_color}{status_code}\033[0m - "
            f"{response_time}ms"
        )
        
        # 添加User-Agent（如果不是默认值）
        if user_agent != 'UNKNOWN' and len(user_agent) < 100:
            message += f" - {user_agent}"
        
        return message
