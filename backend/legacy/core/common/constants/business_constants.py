"""
业务常量定义
============

定义业务逻辑相关的常量
"""

# 交易相关
MIN_ORDER_AMOUNT = 0.01
MAX_ORDER_AMOUNT = 1000000.0
DEFAULT_LEVERAGE = 1.0
MAX_LEVERAGE = 100.0

# 风险管理
RISK_WARNING_THRESHOLD = 0.8  # 80%
STOP_LOSS_THRESHOLD = 0.9     # 90%
MAX_DAILY_LOSS_RATIO = 0.05   # 5%
MAX_POSITION_RATIO = 0.3      # 30%

# 手续费相关
DEFAULT_COMMISSION_RATE = 0.0003  # 0.03%
MIN_COMMISSION = 5.0
MAX_COMMISSION_RATE = 0.01        # 1%

# 保证金相关
DEFAULT_MARGIN_RATIO = 0.1   # 10%
MIN_MARGIN_RATIO = 0.05      # 5%
MAX_MARGIN_RATIO = 1.0       # 100%

# 策略相关
MAX_STRATEGY_COUNT = 100
MAX_STRATEGY_NAME_LENGTH = 50
DEFAULT_STRATEGY_PARAMETERS = {
    "fast_period": 10,
    "slow_period": 20,
    "signal_period": 9
}

# 回测相关
MIN_BACKTEST_PERIOD_DAYS = 1
MAX_BACKTEST_PERIOD_DAYS = 3650  # 10年
DEFAULT_BACKTEST_PERIOD_DAYS = 365  # 1年
DEFAULT_INITIAL_CAPITAL = 1000000.0  # 100万

# 数据相关
MAX_HISTORY_BARS = 10000
DEFAULT_HISTORY_BARS = 1000
TICK_DATA_RETENTION_DAYS = 30
BAR_DATA_RETENTION_DAYS = 3650  # 10年

# 市场时间（小时）
MARKET_OPEN_TIME = 9.0    # 9:00
MARKET_CLOSE_TIME = 15.0  # 15:00
NIGHT_SESSION_START = 21.0  # 21:00
NIGHT_SESSION_END = 2.5     # 2:30

# 交易时段
TRADING_SESSIONS = {
    "morning": {"start": "09:00", "end": "11:30"},
    "afternoon": {"start": "13:30", "end": "15:00"},
    "night": {"start": "21:00", "end": "02:30"}
}

# 合约相关
CONTRACT_SIZE_MULTIPLIER = 10
TICK_SIZE = 0.01
MIN_PRICE_CHANGE = 0.01

# 账户相关
MIN_ACCOUNT_BALANCE = 1000.0
INITIAL_DEMO_BALANCE = 100000.0  # 10万
VIP_THRESHOLD = 1000000.0        # 100万

# 用户等级
USER_LEVELS = {
    "bronze": {"min_balance": 0, "max_leverage": 10},
    "silver": {"min_balance": 50000, "max_leverage": 20},
    "gold": {"min_balance": 200000, "max_leverage": 50},
    "platinum": {"min_balance": 1000000, "max_leverage": 100}
}

# 风控参数
RISK_CONTROL_PARAMS = {
    "max_single_order_ratio": 0.1,      # 单笔订单最大比例
    "max_daily_trades": 1000,            # 日最大交易次数
    "max_open_orders": 100,              # 最大挂单数
    "force_close_ratio": 0.95,           # 强制平仓比例
    "warning_ratio": 0.8                 # 预警比例
}

# 技术指标参数
INDICATOR_PARAMS = {
    "sma": {"period": 20},
    "ema": {"period": 12},
    "macd": {"fast": 12, "slow": 26, "signal": 9},
    "rsi": {"period": 14},
    "bollinger": {"period": 20, "std": 2.0},
    "atr": {"period": 14}
}

# 数据源相关
SUPPORTED_EXCHANGES = [
    "SHFE", "CFFEX", "DCE", "CZCE", "INE",
    "SSE", "SZSE", "SGE"
]

SUPPORTED_PRODUCTS = [
    "futures", "stocks", "options", "forex", "crypto"
]

# 通知相关
MAX_NOTIFICATION_COUNT = 1000
NOTIFICATION_RETENTION_DAYS = 30
ALERT_TYPES = [
    "price_alert", "position_alert", "risk_alert",
    "system_alert", "strategy_alert"
]

# 报告相关
REPORT_TYPES = [
    "daily_report", "weekly_report", "monthly_report",
    "performance_report", "risk_report"
]

MAX_REPORT_HISTORY_MONTHS = 24  # 2年

# 数据导出相关
EXPORT_FORMATS = ["csv", "xlsx", "json"]
MAX_EXPORT_RECORDS = 100000
EXPORT_FILE_RETENTION_DAYS = 7

# API相关
API_RATE_LIMITS = {
    "market_data": 1000,    # 每分钟
    "trading": 100,         # 每分钟
    "account": 60,          # 每分钟
    "strategy": 30          # 每分钟
}
