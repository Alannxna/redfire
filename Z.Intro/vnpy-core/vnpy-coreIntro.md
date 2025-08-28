# VnPy-Core 模块介绍

## 🎯 概述

`vnpy-core` 是 RedFire 量化交易平台的 VnPy 核心引擎模块，提供完整的 VnPy 交易引擎集成，支持策略开发、回测分析、实盘交易等功能。该模块是 RedFire 平台与 VnPy 生态系统的桥梁，确保与现有 VnPy 策略的兼容性。

## 📁 目录结构

```
vnpy-core/
├── trader/                    # 💹 交易引擎
├── rpc/                       # 🔗 RPC服务
├── event/                     # 📡 事件系统
├── chart/                     # 📊 图表组件
├── app/                       # 🎯 应用框架
├── alpha/                     # 🧠 Alpha策略
├── requirements.txt           # 📦 依赖包列表
├── Dockerfile                 # 🐳 Docker配置
├── __init__.py                # 🐍 模块初始化
├── run.py                     # 🚀 启动脚本
└── tushare_config.json        # ⚙️ Tushare配置
```

## 💹 交易引擎 (`trader/`)

### **作用**: VnPy交易引擎核心组件

### **主要功能**:
- 订单管理
- 持仓管理
- 风险控制
- 交易执行

### **核心组件**:
```python
# trader/engine.py
from vnpy.trader.engine import MainEngine
from vnpy.trader.object import TickData, OrderData, TradeData

class RedFireEngine(MainEngine):
    """RedFire交易引擎"""
    
    def __init__(self, event_engine=None):
        super().__init__(event_engine)
        self.init_components()
    
    def init_components(self):
        """初始化组件"""
        # 添加交易接口
        self.add_gateway(HuaxinGateway)
        self.add_gateway(ZhongtaiGateway)
        
        # 添加应用模块
        self.add_app(DataRecorderApp)
        self.add_app(RiskManagerApp)
        self.add_app(StrategyManagerApp)
    
    def connect(self, gateway_name: str, setting: dict):
        """连接交易接口"""
        gateway = self.get_gateway(gateway_name)
        if gateway:
            gateway.connect(setting)
    
    def subscribe(self, req: SubscribeRequest, gateway_name: str):
        """订阅行情"""
        gateway = self.get_gateway(gateway_name)
        if gateway:
            gateway.subscribe(req)
    
    def send_order(self, req: OrderRequest, gateway_name: str):
        """发送订单"""
        gateway = self.get_gateway(gateway_name)
        if gateway:
            return gateway.send_order(req)
        return ""
    
    def cancel_order(self, req: CancelRequest, gateway_name: str):
        """撤销订单"""
        gateway = self.get_gateway(gateway_name)
        if gateway:
            gateway.cancel_order(req)
```

## 🔗 RPC服务 (`rpc/`)

### **作用**: 提供远程过程调用服务

### **主要功能**:
- 远程API调用
- 服务注册发现
- 负载均衡
- 故障转移

### **服务实现**:
```python
# rpc/server.py
import asyncio
from vnpy.rpc import RpcServer
from vnpy.trader.object import TickData, OrderData

class RedFireRpcServer(RpcServer):
    """RedFire RPC服务器"""
    
    def __init__(self, engine):
        super().__init__()
        self.engine = engine
        self.register_functions()
    
    def register_functions(self):
        """注册RPC函数"""
        self.register(self.get_tick)
        self.register(self.get_order)
        self.register(self.send_order)
        self.register(self.cancel_order)
        self.register(self.get_account)
        self.register(self.get_position)
    
    def get_tick(self, symbol: str) -> dict:
        """获取行情数据"""
        tick = self.engine.get_tick(symbol)
        if tick:
            return {
                "symbol": tick.symbol,
                "exchange": tick.exchange.value,
                "datetime": tick.datetime.isoformat(),
                "name": tick.name,
                "volume": tick.volume,
                "turnover": tick.turnover,
                "open_interest": tick.open_interest,
                "last_price": tick.last_price,
                "last_volume": tick.last_volume,
                "limit_up": tick.limit_up,
                "limit_down": tick.limit_down,
                "open_price": tick.open_price,
                "high_price": tick.high_price,
                "low_price": tick.low_price,
                "pre_close": tick.pre_close,
                "bid_price_1": tick.bid_price_1,
                "bid_price_2": tick.bid_price_2,
                "bid_price_3": tick.bid_price_3,
                "bid_price_4": tick.bid_price_4,
                "bid_price_5": tick.bid_price_5,
                "ask_price_1": tick.ask_price_1,
                "ask_price_2": tick.ask_price_2,
                "ask_price_3": tick.ask_price_3,
                "ask_price_4": tick.ask_price_4,
                "ask_price_5": tick.ask_price_5,
                "bid_volume_1": tick.bid_volume_1,
                "bid_volume_2": tick.bid_volume_2,
                "bid_volume_3": tick.bid_volume_3,
                "bid_volume_4": tick.bid_volume_4,
                "bid_volume_5": tick.bid_volume_5,
                "ask_volume_1": tick.ask_volume_1,
                "ask_volume_2": tick.ask_volume_2,
                "ask_volume_3": tick.ask_volume_3,
                "ask_volume_4": tick.ask_volume_4,
                "ask_volume_5": tick.ask_volume_5,
                "localtime": tick.localtime.isoformat()
            }
        return {}
    
    def send_order(self, symbol: str, exchange: str, direction: str, 
                   type: str, volume: float, price: float = 0.0) -> str:
        """发送订单"""
        from vnpy.trader.object import OrderRequest
        
        req = OrderRequest(
            symbol=symbol,
            exchange=Exchange(exchange),
            direction=Direction(direction),
            type=OrderType(type),
            volume=volume,
            price=price
        )
        
        return self.engine.send_order(req, "huaxin")
    
    def cancel_order(self, order_id: str, symbol: str, exchange: str):
        """撤销订单"""
        from vnpy.trader.object import CancelRequest
        
        req = CancelRequest(
            order_id=order_id,
            symbol=symbol,
            exchange=Exchange(exchange)
        )
        
        self.engine.cancel_order(req, "huaxin")
```

## 📡 事件系统 (`event/`)

### **作用**: 事件驱动架构核心

### **主要功能**:
- 事件发布订阅
- 异步事件处理
- 事件过滤
- 事件队列管理

### **事件类型**:
```python
# event/event_engine.py
from vnpy.event import EventEngine
from vnpy.trader.event import EVENT_TICK, EVENT_ORDER, EVENT_TRADE

class RedFireEventEngine(EventEngine):
    """RedFire事件引擎"""
    
    def __init__(self):
        super().__init__()
        self.init_handlers()
    
    def init_handlers(self):
        """初始化事件处理器"""
        self.register(EVENT_TICK, self.process_tick_event)
        self.register(EVENT_ORDER, self.process_order_event)
        self.register(EVENT_TRADE, self.process_trade_event)
    
    def process_tick_event(self, event):
        """处理行情事件"""
        tick = event.data
        # 处理行情数据
        self.broadcast_tick(tick)
    
    def process_order_event(self, event):
        """处理订单事件"""
        order = event.data
        # 处理订单状态变化
        self.broadcast_order(order)
    
    def process_trade_event(self, event):
        """处理成交事件"""
        trade = event.data
        # 处理成交信息
        self.broadcast_trade(trade)
    
    def broadcast_tick(self, tick):
        """广播行情数据"""
        # 发送到WebSocket
        # 保存到数据库
        # 触发策略计算
        pass
    
    def broadcast_order(self, order):
        """广播订单状态"""
        # 更新订单状态
        # 发送通知
        pass
    
    def broadcast_trade(self, trade):
        """广播成交信息"""
        # 更新持仓
        # 计算盈亏
        # 发送通知
        pass
```

## 📊 图表组件 (`chart/`)

### **作用**: 数据可视化组件

### **主要功能**:
- K线图表
- 技术指标
- 交易信号
- 回测结果展示

### **图表实现**:
```python
# chart/chart_widget.py
from vnpy.chart import ChartWidget
from vnpy.chart.item import CandleItem, VolumeItem

class RedFireChartWidget(ChartWidget):
    """RedFire图表组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_chart()
    
    def init_chart(self):
        """初始化图表"""
        # 添加K线图
        self.candle_plot = self.add_plot("candle", 0.7)
        self.candle_item = CandleItem()
        self.candle_plot.addItem(self.candle_item)
        
        # 添加成交量图
        self.volume_plot = self.add_plot("volume", 0.3)
        self.volume_item = VolumeItem()
        self.volume_plot.addItem(self.volume_item)
        
        # 添加技术指标
        self.add_indicators()
    
    def add_indicators(self):
        """添加技术指标"""
        # 移动平均线
        self.ma_plot = self.add_plot("ma", 0.7)
        self.ma5_item = self.add_line("MA5", "red")
        self.ma10_item = self.add_line("MA10", "blue")
        self.ma20_item = self.add_line("MA20", "green")
        
        # MACD指标
        self.macd_plot = self.add_plot("macd", 0.3)
        self.macd_item = self.add_bar("MACD", "blue")
        self.signal_item = self.add_line("Signal", "red")
        self.histogram_item = self.add_bar("Histogram", "gray")
    
    def update_data(self, data):
        """更新图表数据"""
        # 更新K线数据
        self.candle_item.update_data(data)
        
        # 更新成交量数据
        self.volume_item.update_data(data)
        
        # 更新技术指标
        self.update_indicators(data)
    
    def update_indicators(self, data):
        """更新技术指标"""
        # 计算移动平均线
        ma5 = self.calculate_ma(data, 5)
        ma10 = self.calculate_ma(data, 10)
        ma20 = self.calculate_ma(data, 20)
        
        # 更新MA线
        self.ma5_item.update_data(ma5)
        self.ma10_item.update_data(ma10)
        self.ma20_item.update_data(ma20)
        
        # 计算MACD
        macd, signal, histogram = self.calculate_macd(data)
        
        # 更新MACD
        self.macd_item.update_data(macd)
        self.signal_item.update_data(signal)
        self.histogram_item.update_data(histogram)
    
    def calculate_ma(self, data, period):
        """计算移动平均线"""
        import pandas as pd
        df = pd.DataFrame(data)
        return df['close'].rolling(period).mean().values
    
    def calculate_macd(self, data):
        """计算MACD指标"""
        import pandas as pd
        import numpy as np
        
        df = pd.DataFrame(data)
        close = df['close']
        
        # 计算EMA
        ema12 = close.ewm(span=12).mean()
        ema26 = close.ewm(span=26).mean()
        
        # 计算MACD线
        macd = ema12 - ema26
        
        # 计算信号线
        signal = macd.ewm(span=9).mean()
        
        # 计算柱状图
        histogram = macd - signal
        
        return macd.values, signal.values, histogram.values
```

## 🎯 应用框架 (`app/`)

### **作用**: VnPy应用模块框架

### **主要功能**:
- 策略管理
- 数据记录
- 风险管理
- 回测分析

### **应用模块**:
```python
# app/strategy_manager.py
from vnpy.app import BaseApp
from vnpy.trader.object import TickData, OrderData, TradeData

class StrategyManagerApp(BaseApp):
    """策略管理应用"""
    
    app_name = "StrategyManager"
    app_module = __module__
    app_author = "RedFire"
    
    def __init__(self, main_engine, event_engine):
        super().__init__(main_engine, event_engine)
        self.strategies = {}
        self.init_ui()
    
    def init_ui(self):
        """初始化界面"""
        self.widget = StrategyManagerWidget(self)
        self.main_engine.put_widget(self.widget, self.app_name, self.widget)
    
    def add_strategy(self, strategy_name: str, strategy_class: type, setting: dict):
        """添加策略"""
        strategy = strategy_class(self.main_engine, self.event_engine, setting)
        self.strategies[strategy_name] = strategy
        strategy.init()
    
    def remove_strategy(self, strategy_name: str):
        """移除策略"""
        if strategy_name in self.strategies:
            strategy = self.strategies[strategy_name]
            strategy.stop()
            del self.strategies[strategy_name]
    
    def start_strategy(self, strategy_name: str):
        """启动策略"""
        if strategy_name in self.strategies:
            strategy = self.strategies[strategy_name]
            strategy.start()
    
    def stop_strategy(self, strategy_name: str):
        """停止策略"""
        if strategy_name in self.strategies:
            strategy = self.strategies[strategy_name]
            strategy.stop()
    
    def get_strategy_status(self, strategy_name: str) -> dict:
        """获取策略状态"""
        if strategy_name in self.strategies:
            strategy = self.strategies[strategy_name]
            return {
                "name": strategy_name,
                "status": strategy.trading,
                "pos": strategy.pos,
                "net_pnl": strategy.net_pnl,
                "total_pnl": strategy.total_pnl
            }
        return {}
```

## 🧠 Alpha策略 (`alpha/`)

### **作用**: Alpha策略开发框架

### **主要功能**:
- 因子计算
- 信号生成
- 组合优化
- 风险控制

### **策略框架**:
```python
# alpha/alpha_strategy.py
from vnpy.app.cta_strategy import CtaTemplate
from vnpy.trader.object import TickData, BarData, TradeData, OrderData
from vnpy.trader.constant import Direction, Offset, Exchange

class AlphaStrategy(CtaTemplate):
    """Alpha策略基类"""
    
    author = "RedFire"
    
    # 策略参数
    fast_window = 10
    slow_window = 20
    risk_ratio = 0.02
    
    # 策略变量
    fast_ma0 = 0.0
    fast_ma1 = 0.0
    slow_ma0 = 0.0
    slow_ma1 = 0.0
    
    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)
        
        self.bg_fast = ArrayManager(self.fast_window)
        self.bg_slow = ArrayManager(self.slow_window)
    
    def on_init(self):
        """策略初始化"""
        self.write_log("策略初始化")
        self.load_bar(10)
    
    def on_start(self):
        """策略启动"""
        self.write_log("策略启动")
    
    def on_stop(self):
        """策略停止"""
        self.write_log("策略停止")
    
    def on_tick(self, tick: TickData):
        """Tick数据更新"""
        self.bg_fast.update_tick(tick)
        self.bg_slow.update_tick(tick)
        
        if not self.bg_fast.inited or not self.bg_slow.inited:
            return
        
        self.fast_ma0 = self.bg_fast.sma()
        self.fast_ma1 = self.bg_fast.sma(1)
        self.slow_ma0 = self.bg_slow.sma()
        self.slow_ma1 = self.bg_slow.sma(1)
        
        cross_over = (self.fast_ma0 > self.slow_ma0 and
                     self.fast_ma1 <= self.slow_ma1)
        cross_below = (self.fast_ma0 < self.slow_ma0 and
                      self.fast_ma1 >= self.slow_ma1)
        
        if cross_over:
            if not self.pos:
                self.buy(tick.last_price, 1)
        elif cross_below:
            if self.pos > 0:
                self.sell(tick.last_price, abs(self.pos))
    
    def on_bar(self, bar: BarData):
        """K线数据更新"""
        self.bg_fast.update_bar(bar)
        self.bg_slow.update_bar(bar)
        
        if not self.bg_fast.inited or not self.bg_slow.inited:
            return
        
        self.fast_ma0 = self.bg_fast.sma()
        self.fast_ma1 = self.bg_fast.sma(1)
        self.slow_ma0 = self.bg_slow.sma()
        self.slow_ma1 = self.bg_slow.sma(1)
        
        cross_over = (self.fast_ma0 > self.slow_ma0 and
                     self.fast_ma1 <= self.slow_ma1)
        cross_below = (self.fast_ma0 < self.slow_ma0 and
                      self.fast_ma1 >= self.slow_ma1)
        
        if cross_over:
            if not self.pos:
                self.buy(bar.close_price, 1)
        elif cross_below:
            if self.pos > 0:
                self.sell(bar.close_price, abs(self.pos))
    
    def on_order(self, order: OrderData):
        """订单更新"""
        pass
    
    def on_trade(self, trade: TradeData):
        """成交更新"""
        self.put_event()
```

## 🚀 启动脚本 (`run.py`)

### **作用**: VnPy引擎启动入口

### **启动流程**:
```python
# run.py
import sys
import os
from PyQt5.QtWidgets import QApplication
from vnpy.event import EventEngine
from vnpy.trader.engine import MainEngine
from vnpy.trader.ui import MainWindow, create_qapp

from trader.engine import RedFireEngine
from rpc.server import RedFireRpcServer
from app.strategy_manager import StrategyManagerApp

def main():
    """主函数"""
    # 创建Qt应用
    qapp = create_qapp()
    
    # 创建事件引擎
    event_engine = EventEngine()
    
    # 创建主引擎
    main_engine = RedFireEngine(event_engine)
    
    # 添加应用模块
    main_engine.add_app(StrategyManagerApp)
    
    # 创建主窗口
    main_window = MainWindow(main_engine, event_engine)
    main_window.showMaximized()
    
    # 创建RPC服务器
    rpc_server = RedFireRpcServer(main_engine)
    rpc_server.start()
    
    # 运行应用
    qapp.exec_()

if __name__ == "__main__":
    main()
```

## 📦 依赖管理

### **requirements.txt**
```
vnpy-trader>=3.0.0
vnpy-ib>=3.0.0
vnpy-ctp>=3.0.0
vnpy-ctastrategy>=3.0.0
vnpy-sqlite>=3.0.0
vnpy-chart>=3.0.0
PyQt5>=5.15.0
pandas>=1.3.0
numpy>=1.21.0
```

## 🐳 Docker配置

### **Dockerfile**
```dockerfile
FROM python:3.9-slim

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    qt5-default \
    libqt5gui5 \
    libqt5core5a \
    libqt5dbus5 \
    && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 暴露端口
EXPOSE 2014

# 启动命令
CMD ["python", "run.py"]
```

## ⚙️ 配置管理

### **tushare_config.json**
```json
{
    "token": "your_tushare_token",
    "database": {
        "host": "localhost",
        "port": 3306,
        "database": "vnpy",
        "username": "vnpy",
        "password": "vnpy"
    },
    "gateway": {
        "huaxin": {
            "username": "your_username",
            "password": "your_password",
            "server": "your_server",
            "port": 12345
        },
        "zhongtai": {
            "username": "your_username",
            "password": "your_password",
            "server": "your_server",
            "port": 12345
        }
    }
}
```

## 🔧 集成接口

### **1. 与RedFire平台集成**

```python
# integration/redfire_integration.py
from vnpy.trader.engine import MainEngine
from redfire.gateway import RedFireGateway

class VnPyRedFireIntegration:
    """VnPy与RedFire集成"""
    
    def __init__(self, main_engine: MainEngine):
        self.main_engine = main_engine
        self.redfire_gateway = None
    
    def setup_redfire_gateway(self, config: dict):
        """设置RedFire网关"""
        self.redfire_gateway = RedFireGateway(self.main_engine, "redfire")
        self.main_engine.add_gateway(self.redfire_gateway)
        
        # 连接RedFire网关
        self.redfire_gateway.connect(config)
    
    def sync_data(self):
        """同步数据"""
        # 同步行情数据
        self.sync_market_data()
        
        # 同步交易数据
        self.sync_trade_data()
        
        # 同步持仓数据
        self.sync_position_data()
    
    def sync_market_data(self):
        """同步行情数据"""
        # 从RedFire获取行情数据
        # 转换为VnPy格式
        # 发送到VnPy引擎
        pass
    
    def sync_trade_data(self):
        """同步交易数据"""
        # 从RedFire获取交易数据
        # 转换为VnPy格式
        # 发送到VnPy引擎
        pass
    
    def sync_position_data(self):
        """同步持仓数据"""
        # 从RedFire获取持仓数据
        # 转换为VnPy格式
        # 发送到VnPy引擎
        pass
```

### **2. 策略迁移工具**

```python
# tools/strategy_migrator.py
import ast
import astor

class StrategyMigrator:
    """策略迁移工具"""
    
    def __init__(self):
        self.migration_rules = self.load_migration_rules()
    
    def migrate_strategy(self, source_file: str, target_file: str):
        """迁移策略文件"""
        # 读取源文件
        with open(source_file, 'r', encoding='utf-8') as f:
            source_code = f.read()
        
        # 解析AST
        tree = ast.parse(source_code)
        
        # 应用迁移规则
        migrated_tree = self.apply_migration_rules(tree)
        
        # 生成目标代码
        target_code = astor.to_source(migrated_tree)
        
        # 写入目标文件
        with open(target_file, 'w', encoding='utf-8') as f:
            f.write(target_code)
    
    def load_migration_rules(self):
        """加载迁移规则"""
        return {
            "imports": {
                "vnpy.app.cta_strategy": "redfire.strategy",
                "vnpy.trader.object": "redfire.models"
            },
            "classes": {
                "CtaTemplate": "BaseStrategy"
            },
            "methods": {
                "on_tick": "on_market_data",
                "on_bar": "on_bar_data"
            }
        }
    
    def apply_migration_rules(self, tree):
        """应用迁移规则"""
        # 实现AST转换逻辑
        return tree
```

---

**总结**: VnPy-Core模块提供了完整的VnPy交易引擎集成，包括交易引擎、RPC服务、事件系统、图表组件、应用框架和Alpha策略等核心功能。通过标准化的接口和工具，确保与现有VnPy生态系统的兼容性，为策略开发和实盘交易提供强大支持。
