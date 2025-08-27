"""
Trading Enums
============

交易系统核心枚举定义，包含交易方向、状态、类型等关键概念。
"""

from enum import Enum, auto
from typing import Set


class Direction(Enum):
    """交易方向"""
    LONG = "LONG"           # 做多
    SHORT = "SHORT"         # 做空
    NET = "NET"             # 净持仓


class Offset(Enum):
    """开平标志"""
    OPEN = "OPEN"           # 开仓
    CLOSE = "CLOSE"         # 平仓
    CLOSETODAY = "CLOSETODAY"  # 平今
    CLOSEYESTERDAY = "CLOSEYESTERDAY"  # 平昨


class OrderStatus(Enum):
    """订单状态"""
    SUBMITTING = "SUBMITTING"      # 提交中
    SUBMITTED = "SUBMITTED"        # 已提交
    PARTTRADED = "PARTTRADED"      # 部分成交
    ALLTRADED = "ALLTRADED"        # 全部成交
    CANCELLED = "CANCELLED"        # 已撤销
    REJECTED = "REJECTED"          # 已拒绝
    EXPIRED = "EXPIRED"            # 已过期
    UNKNOWN = "UNKNOWN"            # 未知状态


class TradeStatus(Enum):
    """成交状态"""
    PENDING = "PENDING"            # 待处理
    CONFIRMED = "CONFIRMED"        # 已确认
    CANCELLED = "CANCELLED"        # 已取消
    REJECTED = "REJECTED"          # 已拒绝


class PositionStatus(Enum):
    """持仓状态"""
    ACTIVE = "ACTIVE"              # 活跃
    CLOSED = "CLOSED"              # 已平仓
    EXPIRED = "EXPIRED"            # 已过期
    DELIVERED = "DELIVERED"        # 已交割


class Product(Enum):
    """产品类型"""
    EQUITY = "EQUITY"              # 股票
    FUTURES = "FUTURES"            # 期货
    OPTION = "OPTION"              # 期权
    FOREX = "FOREX"                # 外汇
    SPOT = "SPOT"                  # 现货
    ETF = "ETF"                    # 交易所交易基金
    BOND = "BOND"                  # 债券
    FUND = "FUND"                  # 基金
    WARRANT = "WARRANT"            # 权证
    INDEX = "INDEX"                # 指数


class Exchange(Enum):
    """交易所"""
    # 中国股票交易所
    SSE = "SSE"                    # 上海证券交易所
    SZSE = "SZSE"                  # 深圳证券交易所
    BSE = "BSE"                    # 北京证券交易所
    
    # 中国期货交易所
    CFFEX = "CFFEX"                # 中国金融期货交易所
    SHFE = "SHFE"                  # 上海期货交易所
    DCE = "DCE"                    # 大连商品交易所
    CZCE = "CZCE"                  # 郑州商品交易所
    INE = "INE"                    # 上海国际能源交易中心
    GFEX = "GFEX"                  # 广州期货交易所
    
    # 其他中国交易所
    SGE = "SGE"                    # 上海黄金交易所
    WXE = "WXE"                    # 上海票据交易所
    CFETS = "CFETS"                # 中国外汇交易中心
    
    # 国际交易所
    NYSE = "NYSE"                  # 纽约证券交易所
    NASDAQ = "NASDAQ"              # 纳斯达克证券交易所
    CME = "CME"                    # 芝加哥商品交易所
    CBOT = "CBOT"                  # 芝加哥期货交易所
    NYMEX = "NYMEX"                # 纽约商品交易所
    COMEX = "COMEX"                # 纽约商品交易所
    ICE = "ICE"                    # 洲际交易所
    EUREX = "EUREX"                # 欧洲期货交易所
    LSE = "LSE"                    # 伦敦证券交易所
    TSE = "TSE"                    # 东京证券交易所
    HKEX = "HKEX"                  # 香港交易所
    SGX = "SGX"                    # 新加坡交易所


class OrderType(Enum):
    """订单类型"""
    LIMIT = "LIMIT"                # 限价单
    MARKET = "MARKET"              # 市价单
    STOP = "STOP"                  # 止损单
    STOP_LIMIT = "STOP_LIMIT"      # 止损限价单
    FAK = "FAK"                    # 立即成交剩余撤销
    FOK = "FOK"                    # 立即全部成交否则撤销
    IOC = "IOC"                    # 立即成交剩余撤销
    GTC = "GTC"                    # 撤销前有效
    GTD = "GTD"                    # 指定日期前有效


class PriceType(Enum):
    """价格类型"""
    LIMIT = "LIMIT"                # 限价
    MARKET = "MARKET"              # 市价
    BEST = "BEST"                  # 最优价
    STOP = "STOP"                  # 止损价


# 订单类型与价格类型的兼容性映射
ORDER_PRICE_TYPE_COMPATIBILITY: dict[OrderType, Set[PriceType]] = {
    OrderType.LIMIT: {PriceType.LIMIT},
    OrderType.MARKET: {PriceType.MARKET, PriceType.BEST},
    OrderType.STOP: {PriceType.STOP, PriceType.MARKET},
    OrderType.STOP_LIMIT: {PriceType.LIMIT, PriceType.STOP},
    OrderType.FAK: {PriceType.LIMIT, PriceType.MARKET},
    OrderType.FOK: {PriceType.LIMIT, PriceType.MARKET},
    OrderType.IOC: {PriceType.LIMIT, PriceType.MARKET},
    OrderType.GTC: {PriceType.LIMIT},
    OrderType.GTD: {PriceType.LIMIT},
}

# 交易所产品映射
EXCHANGE_PRODUCT_MAPPING: dict[Exchange, Set[Product]] = {
    # 中国股票交易所
    Exchange.SSE: {Product.EQUITY, Product.ETF, Product.BOND, Product.FUND},
    Exchange.SZSE: {Product.EQUITY, Product.ETF, Product.BOND, Product.FUND},
    Exchange.BSE: {Product.EQUITY},
    
    # 中国期货交易所
    Exchange.CFFEX: {Product.FUTURES, Product.OPTION},
    Exchange.SHFE: {Product.FUTURES, Product.OPTION},
    Exchange.DCE: {Product.FUTURES, Product.OPTION},
    Exchange.CZCE: {Product.FUTURES, Product.OPTION},
    Exchange.INE: {Product.FUTURES},
    Exchange.GFEX: {Product.FUTURES},
    
    # 其他中国交易所
    Exchange.SGE: {Product.SPOT},
    Exchange.WXE: {Product.SPOT},
    Exchange.CFETS: {Product.FOREX},
    
    # 国际交易所
    Exchange.NYSE: {Product.EQUITY, Product.ETF, Product.BOND},
    Exchange.NASDAQ: {Product.EQUITY, Product.ETF},
    Exchange.CME: {Product.FUTURES, Product.OPTION},
    Exchange.CBOT: {Product.FUTURES, Product.OPTION},
    Exchange.NYMEX: {Product.FUTURES, Product.OPTION},
    Exchange.COMEX: {Product.FUTURES, Product.OPTION},
    Exchange.ICE: {Product.FUTURES, Product.OPTION},
    Exchange.EUREX: {Product.FUTURES, Product.OPTION},
    Exchange.LSE: {Product.EQUITY, Product.ETF, Product.BOND},
    Exchange.TSE: {Product.EQUITY, Product.ETF},
    Exchange.HKEX: {Product.EQUITY, Product.ETF, Product.WARRANT},
    Exchange.SGX: {Product.FUTURES, Product.EQUITY},
}
