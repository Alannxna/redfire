#!/usr/bin/env python3
"""
完整后端数据库模型
映射现有MySQL数据库中的所有表结构
"""

from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Text, Boolean, 
    ForeignKey, Index, UniqueConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional
import uuid

Base = declarative_base()

# ==================== 用户相关表 ====================

class A2User(Base):
    """A2用户表 - 映射现有a2_user表"""
    __tablename__ = 'a2_user'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=True)
    status = Column(String(20), nullable=True)
    email_verified = Column(Boolean, nullable=True, default=False)
    created_at = Column(DateTime, nullable=True, default=func.now())
    updated_at = Column(DateTime, nullable=True, default=func.now(), onupdate=func.now())

class WebUser(Base):
    """Web用户表 - 映射现有web_users表"""
    __tablename__ = 'web_users'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(50), unique=True, nullable=False)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    phone = Column(String(20), nullable=True)
    full_name = Column(String(100), nullable=True)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, nullable=True, default=True)
    is_verified = Column(Boolean, nullable=True, default=False)
    role = Column(String(20), nullable=True, default='user')
    permissions = Column(Text, nullable=True)
    max_positions = Column(Integer, nullable=True)
    max_order_value = Column(Float, nullable=True)
    daily_loss_limit = Column(Float, nullable=True)
    created_at = Column(DateTime, nullable=True, default=func.now())
    updated_at = Column(DateTime, nullable=True, default=func.now(), onupdate=func.now())
    last_login = Column(DateTime, nullable=True)
    
    # 关系
    sessions = relationship("WebUserSession", back_populates="user")
    trading_accounts = relationship("WebTradingAccount", back_populates="user")
    orders = relationship("WebOrder", back_populates="user")
    strategies = relationship("WebStrategy", back_populates="user")
    notifications = relationship("WebNotification", back_populates="user")

class WebUserSession(Base):
    """用户会话表 - 映射现有web_user_sessions表"""
    __tablename__ = 'web_user_sessions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(100), unique=True, nullable=False)
    user_id = Column(String(50), ForeignKey('web_users.user_id'), nullable=False)
    is_active = Column(Boolean, nullable=True, default=True)
    user_agent = Column(String(500), nullable=True)
    ip_address = Column(String(45), nullable=True)
    created_at = Column(DateTime, nullable=True, default=func.now())
    updated_at = Column(DateTime, nullable=True, default=func.now(), onupdate=func.now())
    expires_at = Column(DateTime, nullable=False)
    
    # 关系
    user = relationship("WebUser", back_populates="sessions")

# ==================== 交易相关表 ====================

class WebTradingAccount(Base):
    """交易账户表 - 映射现有web_trading_accounts表"""
    __tablename__ = 'web_trading_accounts'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(String(50), unique=True, nullable=False)
    user_id = Column(String(50), ForeignKey('web_users.user_id'), nullable=False)
    account_name = Column(String(100), nullable=False)
    account_type = Column(String(20), nullable=True)
    gateway = Column(String(50), nullable=True)
    initial_capital = Column(Float, nullable=True)
    available_cash = Column(Float, nullable=True)
    frozen_cash = Column(Float, nullable=True)
    total_value = Column(Float, nullable=True)
    position_value = Column(Float, nullable=True)
    is_active = Column(Boolean, nullable=True, default=True)
    is_connected = Column(Boolean, nullable=True, default=False)
    created_at = Column(DateTime, nullable=True, default=func.now())
    updated_at = Column(DateTime, nullable=True, default=func.now(), onupdate=func.now())
    
    # 关系
    user = relationship("WebUser", back_populates="trading_accounts")
    orders = relationship("WebOrder", back_populates="account")
    positions = relationship("WebPosition", back_populates="account")
    balances = relationship("WebAccountBalance", back_populates="account")

class WebOrder(Base):
    """订单表 - 映射现有web_orders表"""
    __tablename__ = 'web_orders'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(String(50), unique=True, nullable=False)
    user_id = Column(String(50), ForeignKey('web_users.user_id'), nullable=False)
    account_id = Column(String(50), ForeignKey('web_trading_accounts.account_id'), nullable=False)
    strategy_id = Column(String(50), ForeignKey('web_strategies.strategy_id'), nullable=True)
    vt_symbol = Column(String(50), nullable=False, index=True)
    exchange = Column(String(20), nullable=False)
    direction = Column(String(10), nullable=False)
    offset = Column(String(10), nullable=True)
    order_type = Column(String(20), nullable=True)
    volume = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    status = Column(String(20), nullable=True, index=True)
    traded_volume = Column(Integer, nullable=True)
    created_at = Column(DateTime, nullable=True, default=func.now())
    updated_at = Column(DateTime, nullable=True, default=func.now(), onupdate=func.now())
    
    # 关系
    user = relationship("WebUser", back_populates="orders")
    account = relationship("WebTradingAccount", back_populates="orders")
    strategy = relationship("WebStrategy", back_populates="orders")
    trades = relationship("WebTrade", back_populates="order")

class WebTrade(Base):
    """成交表 - 映射现有web_trades表"""
    __tablename__ = 'web_trades'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    trade_id = Column(String(50), unique=True, nullable=False)
    order_id = Column(String(50), ForeignKey('web_orders.order_id'), nullable=False)
    vt_symbol = Column(String(50), nullable=False, index=True)
    exchange = Column(String(20), nullable=False)
    direction = Column(String(10), nullable=False)
    offset = Column(String(10), nullable=False)
    volume = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    commission = Column(Float, nullable=True)
    slippage = Column(Float, nullable=True)
    trade_time = Column(DateTime, nullable=True, index=True)
    
    # 关系
    order = relationship("WebOrder", back_populates="trades")

class WebPosition(Base):
    """持仓表 - 映射现有web_positions表"""
    __tablename__ = 'web_positions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(String(50), ForeignKey('web_trading_accounts.account_id'), nullable=False)
    vt_symbol = Column(String(50), nullable=False, index=True)
    exchange = Column(String(20), nullable=False)
    direction = Column(String(10), nullable=False)
    volume = Column(Integer, nullable=True)
    frozen_volume = Column(Integer, nullable=True)
    avg_price = Column(Float, nullable=True)
    last_price = Column(Float, nullable=True)
    unrealized_pnl = Column(Float, nullable=True)
    realized_pnl = Column(Float, nullable=True)
    updated_at = Column(DateTime, nullable=True, default=func.now(), onupdate=func.now())
    
    # 关系
    account = relationship("WebTradingAccount", back_populates="positions")

class WebAccountBalance(Base):
    """账户余额表 - 映射现有web_account_balances表"""
    __tablename__ = 'web_account_balances'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(String(50), ForeignKey('web_trading_accounts.account_id'), nullable=False)
    timestamp = Column(DateTime, nullable=True, default=func.now())
    available_cash = Column(Float, nullable=False)
    frozen_cash = Column(Float, nullable=False)
    total_value = Column(Float, nullable=False)
    position_value = Column(Float, nullable=False)
    change_type = Column(String(20), nullable=False)
    change_amount = Column(Float, nullable=False)
    description = Column(String(200), nullable=True)
    
    # 关系
    account = relationship("WebTradingAccount", back_populates="balances")

# ==================== 策略相关表 ====================

class WebStrategy(Base):
    """策略表 - 映射现有web_strategies表"""
    __tablename__ = 'web_strategies'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    strategy_id = Column(String(50), unique=True, nullable=False)
    user_id = Column(String(50), ForeignKey('web_users.user_id'), nullable=False)
    strategy_name = Column(String(100), nullable=False)
    class_name = Column(String(100), nullable=False)
    vt_symbol = Column(String(50), nullable=False, index=True)
    exchange = Column(String(20), nullable=False)
    parameters = Column(Text, nullable=True)
    variables = Column(Text, nullable=True)
    status = Column(String(20), nullable=True)
    auto_start = Column(Boolean, nullable=True, default=False)
    total_trades = Column(Integer, nullable=True)
    winning_trades = Column(Integer, nullable=True)
    total_pnl = Column(Float, nullable=True)
    max_drawdown = Column(Float, nullable=True)
    created_at = Column(DateTime, nullable=True, default=func.now())
    updated_at = Column(DateTime, nullable=True, default=func.now(), onupdate=func.now())
    started_at = Column(DateTime, nullable=True)
    stopped_at = Column(DateTime, nullable=True)
    
    # 关系
    user = relationship("WebUser", back_populates="strategies")
    orders = relationship("WebOrder", back_populates="strategy")
    logs = relationship("WebStrategyLog", back_populates="strategy")
    parameters_rel = relationship("WebStrategyParameter", back_populates="strategy")

class WebStrategyLog(Base):
    """策略日志表 - 映射现有web_strategy_logs表"""
    __tablename__ = 'web_strategy_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    strategy_id = Column(String(50), ForeignKey('web_strategies.strategy_id'), nullable=False)
    timestamp = Column(DateTime, nullable=True, default=func.now())
    level = Column(String(10), nullable=False)
    message = Column(Text, nullable=False)
    position = Column(Integer, nullable=True)
    pnl = Column(Float, nullable=True)
    
    # 关系
    strategy = relationship("WebStrategy", back_populates="logs")

class WebStrategyParameter(Base):
    """策略参数表 - 映射现有web_strategy_parameters表"""
    __tablename__ = 'web_strategy_parameters'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    strategy_id = Column(Integer, ForeignKey('web_strategies.id'), nullable=False)
    parameter_name = Column(String(100), nullable=False)
    parameter_value = Column(Text, nullable=False)
    parameter_type = Column(String(20), nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=True, default=func.now())
    updated_at = Column(DateTime, nullable=True, default=func.now(), onupdate=func.now())
    
    # 关系
    strategy = relationship("WebStrategy", back_populates="parameters_rel")

# ==================== 通知和日志表 ====================

class WebNotification(Base):
    """通知表 - 映射现有web_notifications表"""
    __tablename__ = 'web_notifications'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(50), ForeignKey('web_users.user_id'), nullable=True)
    type = Column(String(20), nullable=False)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    level = Column(String(10), nullable=True)
    is_read = Column(Boolean, nullable=True, default=False)
    is_sent = Column(Boolean, nullable=True, default=False)
    created_at = Column(DateTime, nullable=True, default=func.now())
    read_at = Column(DateTime, nullable=True)
    
    # 关系
    user = relationship("WebUser", back_populates="notifications")

class WebSystemLog(Base):
    """系统日志表 - 映射现有web_system_logs表"""
    __tablename__ = 'web_system_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=True, default=func.now(), index=True)
    level = Column(String(10), nullable=False)
    service = Column(String(50), nullable=False, index=True)
    module = Column(String(100), nullable=True)
    message = Column(Text, nullable=False)
    user_id = Column(String(50), nullable=True)
    request_id = Column(String(100), nullable=True)
    ip_address = Column(String(45), nullable=True)

# ==================== VnPy数据表 ====================

class DbBarData(Base):
    """K线数据表 - 映射现有dbbardata表"""
    __tablename__ = 'dbbardata'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(255), nullable=False, index=True)
    exchange = Column(String(255), nullable=False)
    datetime = Column(DateTime, nullable=False)
    interval = Column(String(255), nullable=False)
    volume = Column(Float, nullable=False)
    turnover = Column(Float, nullable=False)
    open_interest = Column(Float, nullable=False)
    open_price = Column(Float, nullable=False)
    high_price = Column(Float, nullable=False)
    low_price = Column(Float, nullable=False)
    close_price = Column(Float, nullable=False)

class DbBarOverview(Base):
    """K线概览表 - 映射现有dbbaroverview表"""
    __tablename__ = 'dbbaroverview'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(255), nullable=False, index=True)
    exchange = Column(String(255), nullable=False)
    interval = Column(String(255), nullable=False)
    count = Column(Integer, nullable=False)
    start = Column(DateTime, nullable=False)
    end = Column(DateTime, nullable=False)

class DbTickData(Base):
    """Tick数据表 - 映射现有dbtickdata表"""
    __tablename__ = 'dbtickdata'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(255), nullable=False, index=True)
    exchange = Column(String(255), nullable=False)
    datetime = Column(DateTime(3), nullable=False)  # 支持毫秒
    name = Column(String(255), nullable=False)
    volume = Column(Float, nullable=False)
    turnover = Column(Float, nullable=False)
    open_interest = Column(Float, nullable=False)
    last_price = Column(Float, nullable=False)
    last_volume = Column(Float, nullable=False)
    limit_up = Column(Float, nullable=False)
    limit_down = Column(Float, nullable=False)
    open_price = Column(Float, nullable=False)
    high_price = Column(Float, nullable=False)
    low_price = Column(Float, nullable=False)
    pre_close = Column(Float, nullable=False)
    bid_price_1 = Column(Float, nullable=False)
    bid_price_2 = Column(Float, nullable=True)
    bid_price_3 = Column(Float, nullable=True)
    bid_price_4 = Column(Float, nullable=True)
    bid_price_5 = Column(Float, nullable=True)
    ask_price_1 = Column(Float, nullable=False)
    ask_price_2 = Column(Float, nullable=True)
    ask_price_3 = Column(Float, nullable=True)
    ask_price_4 = Column(Float, nullable=True)
    ask_price_5 = Column(Float, nullable=True)
    bid_volume_1 = Column(Float, nullable=False)
    bid_volume_2 = Column(Float, nullable=True)
    bid_volume_3 = Column(Float, nullable=True)
    bid_volume_4 = Column(Float, nullable=True)
    bid_volume_5 = Column(Float, nullable=True)
    ask_volume_1 = Column(Float, nullable=False)
    ask_volume_2 = Column(Float, nullable=True)
    ask_volume_3 = Column(Float, nullable=True)
    ask_volume_4 = Column(Float, nullable=True)
    ask_volume_5 = Column(Float, nullable=True)
    localtime = Column(DateTime(3), nullable=True)

class DbTickOverview(Base):
    """Tick概览表 - 映射现有dbtickoverview表"""
    __tablename__ = 'dbtickoverview'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(255), nullable=False, index=True)
    exchange = Column(String(255), nullable=False)
    count = Column(Integer, nullable=False)
    start = Column(DateTime, nullable=False)
    end = Column(DateTime, nullable=False)

# ==================== 创建索引 ====================

# 为性能优化添加必要的复合索引
Index('ix_web_orders_user_status', WebOrder.user_id, WebOrder.status)
Index('ix_web_orders_account_symbol', WebOrder.account_id, WebOrder.vt_symbol)
Index('ix_web_trades_symbol_time', WebTrade.vt_symbol, WebTrade.trade_time)
Index('ix_web_positions_account_symbol', WebPosition.account_id, WebPosition.vt_symbol)
Index('ix_web_strategies_user_status', WebStrategy.user_id, WebStrategy.status)
Index('ix_dbbardata_symbol_datetime', DbBarData.symbol, DbBarData.datetime)
Index('ix_dbtickdata_symbol_datetime', DbTickData.symbol, DbTickData.datetime)

# 导出所有模型
__all__ = [
    'Base',
    'A2User', 'WebUser', 'WebUserSession',
    'WebTradingAccount', 'WebOrder', 'WebTrade', 'WebPosition', 'WebAccountBalance',
    'WebStrategy', 'WebStrategyLog', 'WebStrategyParameter',
    'WebNotification', 'WebSystemLog',
    'DbBarData', 'DbBarOverview', 'DbTickData', 'DbTickOverview'
]
