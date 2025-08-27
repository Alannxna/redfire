"""
引擎工具 - EngineUtils

提供交易引擎的通用工具函数，包括：
1. 性能分析 - 性能指标计算和分析
2. 配置管理 - 配置验证和转换
3. 数据转换 - 数据格式转换和验证
4. 时间处理 - 时间相关工具函数
5. 日志工具 - 日志格式化和分析

作者: RedFire团队
创建时间: 2024年9月2日
"""

import time
import json
import hashlib
import logging
from typing import Dict, List, Optional, Any, Union, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import traceback


class LogLevel(Enum):
    """日志级别枚举"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class PerformanceMetrics:
    """性能指标数据类"""
    operation_name: str
    start_time: float
    end_time: float
    duration: float
    success: bool
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class PerformanceAnalyzer:
    """性能分析器"""
    
    def __init__(self):
        self.metrics: List[PerformanceMetrics] = []
        self.operation_stats: Dict[str, Dict[str, Any]] = {}
    
    def start_operation(self, operation_name: str) -> float:
        """
        开始操作计时
        
        参数:
            operation_name: 操作名称
            
        返回:
            开始时间戳
        """
        return time.time()
    
    def end_operation(self, operation_name: str, start_time: float, 
                     success: bool = True, error_message: Optional[str] = None,
                     metadata: Optional[Dict[str, Any]] = None) -> PerformanceMetrics:
        """
        结束操作计时
        
        参数:
            operation_name: 操作名称
            start_time: 开始时间
            success: 是否成功
            error_message: 错误信息
            metadata: 元数据
            
        返回:
            性能指标对象
        """
        end_time = time.time()
        duration = end_time - start_time
        
        metrics = PerformanceMetrics(
            operation_name=operation_name,
            start_time=start_time,
            end_time=end_time,
            duration=duration,
            success=success,
            error_message=error_message,
            metadata=metadata or {}
        )
        
        self.metrics.append(metrics)
        self._update_operation_stats(operation_name, metrics)
        
        return metrics
    
    def _update_operation_stats(self, operation_name: str, metrics: PerformanceMetrics):
        """更新操作统计信息"""
        if operation_name not in self.operation_stats:
            self.operation_stats[operation_name] = {
                "total_count": 0,
                "success_count": 0,
                "error_count": 0,
                "total_duration": 0.0,
                "min_duration": float('inf'),
                "max_duration": 0.0,
                "avg_duration": 0.0
            }
        
        stats = self.operation_stats[operation_name]
        stats["total_count"] += 1
        stats["total_duration"] += metrics.duration
        
        if metrics.success:
            stats["success_count"] += 1
        else:
            stats["error_count"] += 1
        
        if metrics.duration < stats["min_duration"]:
            stats["min_duration"] = metrics.duration
        
        if metrics.duration > stats["max_duration"]:
            stats["max_duration"] = metrics.duration
        
        stats["avg_duration"] = stats["total_duration"] / stats["total_count"]
    
    def get_operation_stats(self, operation_name: Optional[str] = None) -> Dict[str, Any]:
        """
        获取操作统计信息
        
        参数:
            operation_name: 操作名称，如果为None则返回所有操作的统计
            
        返回:
            统计信息字典
        """
        if operation_name:
            return self.operation_stats.get(operation_name, {})
        else:
            return self.operation_stats
    
    def get_performance_report(self) -> Dict[str, Any]:
        """获取性能报告"""
        return {
            "total_operations": len(self.metrics),
            "operation_stats": self.operation_stats,
            "recent_metrics": [asdict(m) for m in self.metrics[-10:]]  # 最近10个指标
        }


class ConfigValidator:
    """配置验证器"""
    
    @staticmethod
    def validate_required_fields(config: Dict[str, Any], required_fields: List[str]) -> Tuple[bool, List[str]]:
        """
        验证必需字段
        
        参数:
            config: 配置字典
            required_fields: 必需字段列表
            
        返回:
            (是否有效, 错误字段列表)
        """
        missing_fields = []
        for field in required_fields:
            if field not in config or config[field] is None:
                missing_fields.append(field)
        
        return len(missing_fields) == 0, missing_fields
    
    @staticmethod
    def validate_field_types(config: Dict[str, Any], field_types: Dict[str, type]) -> Tuple[bool, List[str]]:
        """
        验证字段类型
        
        参数:
            config: 配置字典
            field_types: 字段类型映射
            
        返回:
            (是否有效, 错误字段列表)
        """
        type_errors = []
        for field, expected_type in field_types.items():
            if field in config and not isinstance(config[field], expected_type):
                type_errors.append(f"{field}: 期望类型 {expected_type.__name__}, 实际类型 {type(config[field]).__name__}")
        
        return len(type_errors) == 0, type_errors
    
    @staticmethod
    def validate_field_ranges(config: Dict[str, Any], field_ranges: Dict[str, Tuple[Union[int, float], Union[int, float]]]) -> Tuple[bool, List[str]]:
        """
        验证字段范围
        
        参数:
            config: 配置字典
            field_ranges: 字段范围映射 (min, max)
            
        返回:
            (是否有效, 错误字段列表)
        """
        range_errors = []
        for field, (min_val, max_val) in field_ranges.items():
            if field in config:
                value = config[field]
                if not (min_val <= value <= max_val):
                    range_errors.append(f"{field}: 值 {value} 超出范围 [{min_val}, {max_val}]")
        
        return len(range_errors) == 0, range_errors


class DataConverter:
    """数据转换器"""
    
    @staticmethod
    def dict_to_json(data: Dict[str, Any], indent: int = 2) -> str:
        """字典转JSON字符串"""
        try:
            return json.dumps(data, indent=indent, ensure_ascii=False, default=str)
        except Exception as e:
            return f"转换失败: {e}"
    
    @staticmethod
    def json_to_dict(json_str: str) -> Optional[Dict[str, Any]]:
        """JSON字符串转字典"""
        try:
            return json.loads(json_str)
        except Exception as e:
            return None
    
    @staticmethod
    def safe_float(value: Any, default: float = 0.0) -> float:
        """安全转换为浮点数"""
        try:
            return float(value)
        except (ValueError, TypeError):
            return default
    
    @staticmethod
    def safe_int(value: Any, default: int = 0) -> int:
        """安全转换为整数"""
        try:
            return int(value)
        except (ValueError, TypeError):
            return default
    
    @staticmethod
    def safe_bool(value: Any, default: bool = False) -> bool:
        """安全转换为布尔值"""
        if isinstance(value, bool):
            return value
        elif isinstance(value, str):
            return value.lower() in ('true', '1', 'yes', 'on')
        elif isinstance(value, (int, float)):
            return value != 0
        else:
            return default


class TimeUtils:
    """时间工具类"""
    
    @staticmethod
    def get_current_timestamp() -> float:
        """获取当前时间戳"""
        return time.time()
    
    @staticmethod
    def get_current_datetime() -> datetime:
        """获取当前日期时间"""
        return datetime.now()
    
    @staticmethod
    def format_datetime(dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
        """格式化日期时间"""
        return dt.strftime(format_str)
    
    @staticmethod
    def parse_datetime(date_str: str, format_str: str = "%Y-%m-%d %H:%M:%S") -> Optional[datetime]:
        """解析日期时间字符串"""
        try:
            return datetime.strptime(date_str, format_str)
        except ValueError:
            return None
    
    @staticmethod
    def get_time_difference(start_time: Union[float, datetime], 
                          end_time: Union[float, datetime]) -> float:
        """计算时间差（秒）"""
        if isinstance(start_time, datetime):
            start_time = start_time.timestamp()
        if isinstance(end_time, datetime):
            end_time = end_time.timestamp()
        
        return end_time - start_time
    
    @staticmethod
    def is_market_open(current_time: Optional[datetime] = None) -> bool:
        """
        判断是否为交易时间
        
        参数:
            current_time: 当前时间，如果为None则使用系统时间
            
        返回:
            是否为交易时间
        """
        if current_time is None:
            current_time = datetime.now()
        
        # 简单的交易时间判断（9:00-15:00）
        hour = current_time.hour
        return 9 <= hour < 15


class LogUtils:
    """日志工具类"""
    
    @staticmethod
    def setup_logger(name: str, level: LogLevel = LogLevel.INFO, 
                    log_file: Optional[str] = None) -> logging.Logger:
        """
        设置日志记录器
        
        参数:
            name: 日志记录器名称
            level: 日志级别
            log_file: 日志文件路径
            
        返回:
            配置好的日志记录器
        """
        logger = logging.getLogger(name)
        logger.setLevel(getattr(logging, level.value))
        
        # 清除现有的处理器
        logger.handlers.clear()
        
        # 创建控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, level.value))
        
        # 创建格式化器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # 如果指定了日志文件，创建文件处理器
        if log_file:
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(getattr(logging, level.value))
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        
        return logger
    
    @staticmethod
    def log_performance(logger: logging.Logger, metrics: PerformanceMetrics):
        """记录性能指标"""
        if metrics.success:
            logger.info(f"操作 {metrics.operation_name} 完成，耗时: {metrics.duration:.3f}秒")
        else:
            logger.error(f"操作 {metrics.operation_name} 失败，耗时: {metrics.duration:.3f}秒，错误: {metrics.error_message}")
    
    @staticmethod
    def log_config(logger: logging.Logger, config: Dict[str, Any], config_name: str = "配置"):
        """记录配置信息"""
        logger.info(f"{config_name}: {DataConverter.dict_to_json(config)}")


class EngineUtils:
    """
    引擎工具类
    
    提供交易引擎的通用工具函数
    """
    
    def __init__(self):
        self.performance_analyzer = PerformanceAnalyzer()
        self.config_validator = ConfigValidator()
        self.data_converter = DataConverter()
        self.time_utils = TimeUtils()
        self.log_utils = LogUtils()
    
    def measure_performance(self, operation_name: str):
        """
        性能测量装饰器
        
        参数:
            operation_name: 操作名称
        """
        def decorator(func):
            def wrapper(*args, **kwargs):
                start_time = self.performance_analyzer.start_operation(operation_name)
                try:
                    result = func(*args, **kwargs)
                    self.performance_analyzer.end_operation(
                        operation_name, start_time, success=True
                    )
                    return result
                except Exception as e:
                    self.performance_analyzer.end_operation(
                        operation_name, start_time, success=False, 
                        error_message=str(e)
                    )
                    raise
            return wrapper
        return decorator
    
    def validate_config(self, config: Dict[str, Any], required_fields: List[str],
                       field_types: Optional[Dict[str, type]] = None,
                       field_ranges: Optional[Dict[str, Tuple[Union[int, float], Union[int, float]]]] = None) -> Tuple[bool, List[str]]:
        """
        验证配置
        
        参数:
            config: 配置字典
            required_fields: 必需字段列表
            field_types: 字段类型映射
            field_ranges: 字段范围映射
            
        返回:
            (是否有效, 错误列表)
        """
        errors = []
        
        # 验证必需字段
        is_valid, missing_fields = self.config_validator.validate_required_fields(config, required_fields)
        if not is_valid:
            errors.extend([f"缺少必需字段: {field}" for field in missing_fields])
        
        # 验证字段类型
        if field_types:
            is_valid, type_errors = self.config_validator.validate_field_types(config, field_types)
            if not is_valid:
                errors.extend(type_errors)
        
        # 验证字段范围
        if field_ranges:
            is_valid, range_errors = self.config_validator.validate_field_ranges(config, field_ranges)
            if not is_valid:
                errors.extend(range_errors)
        
        return len(errors) == 0, errors
    
    def get_performance_report(self) -> Dict[str, Any]:
        """获取性能报告"""
        return self.performance_analyzer.get_performance_report()
    
    def create_hash(self, data: str) -> str:
        """创建数据哈希值"""
        return hashlib.md5(data.encode('utf-8')).hexdigest()
    
    def format_duration(self, seconds: float) -> str:
        """格式化持续时间"""
        if seconds < 60:
            return f"{seconds:.3f}秒"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.2f}分钟"
        else:
            hours = seconds / 3600
            return f"{hours:.2f}小时"
    
    def safe_execute(self, func: callable, *args, default_value: Any = None, **kwargs) -> Any:
        """
        安全执行函数
        
        参数:
            func: 要执行的函数
            *args: 位置参数
            default_value: 默认返回值
            **kwargs: 关键字参数
            
        返回:
            函数执行结果或默认值
        """
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(f"函数执行异常: {e}")
            return default_value
