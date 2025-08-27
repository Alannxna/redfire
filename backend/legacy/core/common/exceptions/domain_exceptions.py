"""
领域异常定义
============

定义领域层的业务异常
"""

from typing import Any, Dict, Optional
from .base_exceptions import VnPyWebException


class DomainException(VnPyWebException):
    """领域层基础异常"""
    pass


# 用户域异常
class UserNotFoundError(DomainException):
    """用户未找到异常"""
    
    def __init__(self, user_id: str):
        super().__init__(f"用户未找到: {user_id}")
        self.user_id = user_id
        self.details = {"user_id": user_id}


class InvalidUserError(DomainException):
    """无效用户异常"""
    
    def __init__(self, user_id: str, reason: str):
        super().__init__(f"无效用户: {user_id}, 原因: {reason}")
        self.user_id = user_id
        self.reason = reason
        self.details = {"user_id": user_id, "reason": reason}


class UserAlreadyExistsError(DomainException):
    """用户已存在异常"""
    
    def __init__(self, username: str):
        super().__init__(f"用户已存在: {username}")
        self.username = username
        self.details = {"username": username}


class InvalidPasswordError(DomainException):
    """无效密码异常"""
    
    def __init__(self, message: str = "密码不符合安全要求"):
        super().__init__(message)


# 交易域异常
class TradingPermissionError(DomainException):
    """交易权限异常"""
    
    def __init__(self, user_id: str, operation: str, current_permission: str):
        super().__init__(f"用户 {user_id} 无权限执行 {operation}，当前权限: {current_permission}")
        self.user_id = user_id
        self.operation = operation
        self.current_permission = current_permission
        self.details = {
            "user_id": user_id,
            "operation": operation,
            "current_permission": current_permission
        }


class OrderValidationError(DomainException):
    """订单验证异常"""
    
    def __init__(self, order_id: str, field: str, reason: str):
        super().__init__(f"订单验证失败: {order_id}, 字段: {field}, 原因: {reason}")
        self.order_id = order_id
        self.field = field
        self.reason = reason
        self.details = {
            "order_id": order_id,
            "field": field,
            "reason": reason
        }


class InsufficientFundsError(DomainException):
    """资金不足异常"""
    
    def __init__(self, account_id: str, required: float, available: float):
        super().__init__(f"账户 {account_id} 资金不足，需要: {required}, 可用: {available}")
        self.account_id = account_id
        self.required = required
        self.available = available
        self.details = {
            "account_id": account_id,
            "required": required,
            "available": available
        }


class InvalidSymbolError(DomainException):
    """无效交易品种异常"""
    
    def __init__(self, symbol: str):
        super().__init__(f"无效的交易品种: {symbol}")
        self.symbol = symbol
        self.details = {"symbol": symbol}


# 策略域异常
class StrategyError(DomainException):
    """策略异常基类"""
    
    def __init__(self, strategy_name: str, message: str):
        super().__init__(f"策略 {strategy_name}: {message}")
        self.strategy_name = strategy_name
        self.details = {"strategy_name": strategy_name}


class StrategyNotFoundError(StrategyError):
    """策略未找到异常"""
    
    def __init__(self, strategy_name: str):
        super().__init__(strategy_name, "策略未找到")


class StrategyConfigError(StrategyError):
    """策略配置错误异常"""
    
    def __init__(self, strategy_name: str, config_field: str, reason: str):
        super().__init__(strategy_name, f"配置错误: {config_field}, {reason}")
        self.config_field = config_field
        self.reason = reason
        self.details.update({
            "config_field": config_field,
            "reason": reason
        })


class StrategyRuntimeError(StrategyError):
    """策略运行时异常"""
    
    def __init__(self, strategy_name: str, operation: str, error: str):
        super().__init__(strategy_name, f"运行时错误: {operation}, {error}")
        self.operation = operation
        self.error = error
        self.details.update({
            "operation": operation,
            "error": error
        })


# 市场数据域异常
class MarketDataError(DomainException):
    """市场数据异常"""
    
    def __init__(self, symbol: str, message: str):
        super().__init__(f"市场数据错误: {symbol}, {message}")
        self.symbol = symbol
        self.details = {"symbol": symbol}


class DataNotAvailableError(MarketDataError):
    """数据不可用异常"""
    
    def __init__(self, symbol: str, data_type: str, time_range: str):
        super().__init__(symbol, f"数据不可用: {data_type}, 时间范围: {time_range}")
        self.data_type = data_type
        self.time_range = time_range
        self.details.update({
            "data_type": data_type,
            "time_range": time_range
        })


# 风险管理异常
class RiskManagementError(DomainException):
    """风险管理异常"""
    
    def __init__(self, rule_name: str, message: str, risk_data: Optional[Dict[str, Any]] = None):
        super().__init__(f"风险规则触发: {rule_name}, {message}")
        self.rule_name = rule_name
        self.risk_data = risk_data or {}
        self.details = {
            "rule_name": rule_name,
            "risk_data": self.risk_data
        }


class PositionLimitExceededError(RiskManagementError):
    """持仓限制超出异常"""
    
    def __init__(self, symbol: str, current_position: float, limit: float):
        super().__init__(
            "持仓限制",
            f"品种 {symbol} 持仓超限，当前: {current_position}, 限制: {limit}",
            {"symbol": symbol, "current_position": current_position, "limit": limit}
        )


class DailyLossLimitExceededError(RiskManagementError):
    """日亏损限制超出异常"""
    
    def __init__(self, current_loss: float, limit: float):
        super().__init__(
            "日亏损限制",
            f"当日亏损超限，当前亏损: {current_loss}, 限制: {limit}",
            {"current_loss": current_loss, "limit": limit}
        )
