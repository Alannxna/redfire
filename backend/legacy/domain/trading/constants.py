"""
Trading Constants
================

交易系统核心常量定义，包含精度、范围、时间、费用等关键配置。
"""

from decimal import Decimal
from typing import Dict, Set

# ==================== 精度常量 ====================
PRICE_PRECISION = 4         # 价格精度（小数位数）
VOLUME_PRECISION = 0        # 数量精度（小数位数）
AMOUNT_PRECISION = 2        # 金额精度（小数位数）

# ==================== 数量范围 ====================
MIN_VOLUME = 1              # 最小交易数量
MAX_VOLUME = 999999999      # 最大交易数量

# ==================== 价格范围 ====================
MIN_PRICE = Decimal("0.0001")          # 最小价格
MAX_PRICE = Decimal("999999.9999")     # 最大价格

# ==================== 时间常量 ====================
TRADING_DAY_START = "09:00:00"      # 交易日开始时间
TRADING_DAY_END = "15:00:00"        # 交易日结束时间
NIGHT_TRADING_START = "21:00:00"    # 夜盘开始时间
NIGHT_TRADING_END = "02:30:00"      # 夜盘结束时间

# ==================== 订单ID相关 ====================
ORDER_ID_PREFIX = "ORDER_"          # 订单ID前缀
TRADE_ID_PREFIX = "TRADE_"          # 成交ID前缀
POSITION_ID_PREFIX = "POS_"         # 持仓ID前缀

# ==================== 费用相关 ====================
DEFAULT_COMMISSION_RATE = Decimal("0.0003")    # 默认手续费率
DEFAULT_SLIPPAGE = Decimal("0.0001")           # 默认滑点

# ==================== 风控相关 ====================
DEFAULT_MAX_POSITION_RATIO = Decimal("0.95")   # 默认最大持仓比例
DEFAULT_STOP_LOSS_RATIO = Decimal("0.05")      # 默认止损比例
DEFAULT_TAKE_PROFIT_RATIO = Decimal("0.10")    # 默认止盈比例

# ==================== 数据相关 ====================
MAX_TICK_CACHE_SIZE = 10000         # 最大Tick缓存数量
MAX_ORDER_CACHE_SIZE = 1000         # 最大订单缓存数量
MAX_TRADE_CACHE_SIZE = 1000         # 最大成交缓存数量

# ==================== 网关相关 ====================
GATEWAY_CONNECTION_TIMEOUT = 30     # 网关连接超时时间（秒）
GATEWAY_HEARTBEAT_INTERVAL = 30     # 网关心跳间隔（秒）
GATEWAY_RECONNECT_INTERVAL = 5      # 网关重连间隔（秒）
MAX_RECONNECT_ATTEMPTS = 10         # 最大重连次数

# ==================== 风控限额 ====================
MAX_DAILY_LOSS_RATIO = Decimal("0.10")         # 最大日亏损比例
MAX_SINGLE_ORDER_RATIO = Decimal("0.20")       # 最大单笔订单比例
MAX_POSITION_CONCENTRATION = Decimal("0.30")   # 最大持仓集中度

# ==================== 交易规则 ====================
MIN_ORDER_INTERVAL = 0.1             # 最小下单间隔（秒）
MAX_ORDERS_PER_SECOND = 10          # 每秒最大订单数
MAX_ACTIVE_ORDERS = 100             # 最大活跃订单数

# ==================== 结算相关 ====================
SETTLEMENT_TIME = "15:30:00"        # 结算时间
CLEARING_TIME = "16:00:00"          # 清算时间
FUND_TRANSFER_TIME = "16:30:00"     # 资金划转时间

# ==================== 市场状态 ====================
MARKET_OPEN_STATUS = "OPEN"         # 市场开放状态
MARKET_CLOSED_STATUS = "CLOSED"     # 市场关闭状态
MARKET_PAUSE_STATUS = "PAUSE"       # 市场暂停状态
MARKET_BREAK_STATUS = "BREAK"       # 市场休息状态

# ==================== 错误码 ====================
ERROR_CODES = {
    "INSUFFICIENT_BALANCE": "E001",      # 余额不足
    "INSUFFICIENT_POSITION": "E002",     # 持仓不足
    "INVALID_ORDER_TYPE": "E003",        # 无效订单类型
    "INVALID_PRICE": "E004",             # 无效价格
    "INVALID_VOLUME": "E005",            # 无效数量
    "MARKET_CLOSED": "E006",             # 市场关闭
    "ORDER_REJECTED": "E007",            # 订单被拒绝
    "GATEWAY_ERROR": "E008",             # 网关错误
    "RISK_LIMIT_EXCEEDED": "E009",      # 风险限额超限
    "SYSTEM_ERROR": "E999",              # 系统错误
}

# ==================== 通知类型 ====================
NOTIFICATION_TYPES = {
    "ORDER_STATUS": "ORDER_STATUS",           # 订单状态变更
    "TRADE_CONFIRM": "TRADE_CONFIRM",        # 成交确认
    "POSITION_UPDATE": "POSITION_UPDATE",    # 持仓更新
    "RISK_ALERT": "RISK_ALERT",              # 风险告警
    "SYSTEM_ALERT": "SYSTEM_ALERT",          # 系统告警
    "MARKET_ALERT": "MARKET_ALERT",          # 市场告警
}

# ==================== 日志级别 ====================
LOG_LEVELS = {
    "DEBUG": "DEBUG",                         # 调试级别
    "INFO": "INFO",                           # 信息级别
    "WARNING": "WARNING",                     # 警告级别
    "ERROR": "ERROR",                         # 错误级别
    "CRITICAL": "CRITICAL",                   # 严重级别
}

# ==================== 缓存配置 ====================
CACHE_CONFIG = {
    "DEFAULT_TTL": 300,                       # 默认缓存时间（秒）
    "MAX_SIZE": 10000,                        # 最大缓存条目数
    "CLEANUP_INTERVAL": 60,                   # 清理间隔（秒）
    "EVICTION_POLICY": "LRU",                 # 淘汰策略
}

# ==================== 性能配置 ====================
PERFORMANCE_CONFIG = {
    "MAX_CONCURRENT_ORDERS": 100,             # 最大并发订单数
    "ORDER_PROCESSING_TIMEOUT": 5.0,          # 订单处理超时（秒）
    "DATA_UPDATE_INTERVAL": 0.1,              # 数据更新间隔（秒）
    "HEARTBEAT_INTERVAL": 30,                 # 心跳间隔（秒）
}
