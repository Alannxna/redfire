# RedFire 量化策略模块

企业级量化策略开发框架，提供完整的策略开发、回测、风险管理和绩效分析功能。

## 🎯 核心特性

### 🚀 统一策略开发框架
- **标准化策略基类**: 规范化的策略接口和生命周期管理
- **多种策略类型**: 支持CTA、套利、做市、配对交易等多种策略类型  
- **灵活配置系统**: 丰富的策略配置选项和参数管理
- **事件驱动架构**: 高效的异步事件处理机制

### ⚡ 高性能策略执行引擎
- **多策略并发**: 支持数百个策略同时运行
- **智能资源管理**: 自动负载均衡和资源分配
- **实时数据处理**: 毫秒级数据分发和处理
- **订单管理系统**: 完整的订单生命周期管理

### 📊 专业回测引擎
- **多种回测模式**: Tick级、K线级、事件驱动回测
- **真实交易成本**: 精确的滑点和手续费模拟
- **风险控制模拟**: 回测期间的风险管理验证
- **详细回测报告**: 全面的回测结果分析

### 🛡️ 智能风险管理
- **实时风险监控**: 多维度风险指标实时计算
- **多层风险控制**: 全局、策略、品种级别风险限制
- **智能风险处置**: 自动化风险事件处理
- **压力测试**: 多种市场情景的压力测试

### 📈 全面绩效分析
- **实时绩效监控**: 30+ 专业绩效指标
- **基准比较分析**: 与市场基准的详细对比
- **风险调整收益**: Sharpe、Sortino、Calmar等比率
- **交易行为分析**: 深度的交易模式分析

## 🏗️ 系统架构

```
backend/strategy/
├── core/                          # 核心模块
│   ├── strategy_base.py          # 策略基类和数据结构
│   ├── strategy_engine.py        # 策略执行引擎
│   ├── backtest_engine.py        # 回测引擎
│   ├── risk_manager.py           # 风险管理
│   └── performance_analyzer.py   # 绩效分析
├── integration/                   # 集成模块
│   ├── strategy_integration.py   # 一键集成
│   └── __init__.py
├── examples/                      # 示例策略
│   ├── simple_ma_strategy.py     # 移动平均策略
│   ├── pairs_trading.py          # 配对交易策略
│   └── mean_reversion.py         # 均值回归策略
└── README.md                      # 使用文档
```

## 🚀 快速开始

### 1. 基础安装

```bash
# 安装依赖
pip install pandas numpy scipy fastapi uvicorn

# 确保RedFire项目结构正确
cd backend/strategy
```

### 2. 创建第一个策略

```python
from backend.strategy import BaseStrategy, StrategyConfig, StrategyType, MarketData

class MyStrategy(BaseStrategy):
    """我的第一个量化策略"""
    
    async def on_start(self):
        """策略启动时调用"""
        self.log_info("策略启动")
        self.ma_window = 20
        self.price_history = []
    
    async def on_stop(self):
        """策略停止时调用"""
        self.log_info("策略停止")
    
    async def on_tick(self, data: MarketData):
        """处理实时行情数据"""
        # 添加价格到历史
        self.price_history.append(data.close)
        
        # 保持窗口大小
        if len(self.price_history) > self.ma_window:
            self.price_history.pop(0)
        
        # 计算移动平均
        if len(self.price_history) == self.ma_window:
            ma = sum(self.price_history) / self.ma_window
            current_price = data.close
            
            # 简单的交易逻辑
            position = self.get_position(data.symbol)
            
            if current_price > ma * 1.02 and not position:
                # 价格突破移动平均线2%，买入
                await self.buy(data.symbol, 100)
                self.log_info(f"买入信号: {data.symbol} @ {current_price}")
                
            elif current_price < ma * 0.98 and position:
                # 价格跌破移动平均线2%，卖出
                await self.sell(data.symbol, position.quantity)
                self.log_info(f"卖出信号: {data.symbol} @ {current_price}")
    
    async def on_bar(self, data: MarketData):
        """处理K线数据"""
        await self.on_tick(data)  # 复用tick逻辑

# 创建策略配置
config = StrategyConfig(
    strategy_id="my_strategy_001",
    strategy_name="我的移动平均策略",
    strategy_type=StrategyType.MOMENTUM,
    symbols=["BTCUSDT", "ETHUSDT"],
    initial_capital=100000,
    max_position_size=0.1
)

# 创建策略实例
strategy = MyStrategy(config)
```

### 3. 系统集成

```python
from fastapi import FastAPI
from backend.strategy import setup_strategy_system

# 创建FastAPI应用
app = FastAPI(title="量化交易系统")

# 一键集成策略系统
strategy_system = setup_strategy_system(app)

# 添加策略
await strategy_system.add_strategy(strategy)

# 启动系统
await strategy_system.start()

# 启动策略
await strategy_system.start_strategy("my_strategy_001")

# 推送市场数据
market_data = MarketData(
    symbol="BTCUSDT",
    timestamp=datetime.now(),
    open=50000,
    high=50100,
    low=49900,
    close=50050,
    volume=1000
)

await strategy_system.feed_market_data(market_data)
```

### 4. 运行服务器

```bash
# 启动服务
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# 访问API文档
# http://localhost:8000/docs
```

## 📊 API接口使用

### 系统管理

```bash
# 获取系统状态
GET /api/strategy/system/status

# 启动/停止系统
POST /api/strategy/system/start
POST /api/strategy/system/stop

# 健康检查
GET /api/strategy/health
```

### 策略管理

```bash
# 获取策略列表
GET /api/strategy/list

# 启动/停止策略
POST /api/strategy/{strategy_id}/start
POST /api/strategy/{strategy_id}/stop

# 删除策略
DELETE /api/strategy/{strategy_id}
```

### 绩效分析

```bash
# 获取策略绩效
GET /api/strategy/{strategy_id}/performance

# 获取权益曲线
GET /api/strategy/{strategy_id}/equity-curve

# 生成绩效报告
GET /api/strategy/{strategy_id}/report

# 策略比较
POST /api/strategy/compare
{
  "strategy_ids": ["strategy_1", "strategy_2"]
}
```

### 风险管理

```bash
# 获取风险状态
GET /api/strategy/risk/status

# 获取风险事件
GET /api/strategy/risk/events?active_only=true

# 风险报告
GET /api/strategy/risk/report
```

### 数据推送

```bash
# 推送市场数据
POST /api/strategy/data/feed
{
  "symbol": "BTCUSDT",
  "timestamp": "2024-01-15T10:30:00",
  "open": 50000,
  "high": 50100,
  "low": 49900,
  "close": 50050,
  "volume": 1000
}
```

## 🎯 进阶功能

### 回测系统

```python
from backend.strategy.core import BacktestEngine, BacktestConfig

# 配置回测
backtest_config = BacktestConfig(
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 12, 31),
    initial_capital=100000,
    commission_rate=0.0002,
    slippage_rate=0.0001
)

# 设置数据提供器
def data_provider(symbol: str, start_date: datetime, end_date: datetime):
    # 返回历史数据DataFrame
    # 包含: open, high, low, close, volume列
    pass

# 运行回测
result = await strategy_system.run_backtest(strategy, backtest_config)
print(f"总收益率: {result['result']['total_return']:.2%}")
print(f"年化收益: {result['result']['annual_return']:.2%}")
print(f"夏普比率: {result['result']['sharpe_ratio']:.2f}")
```

### 策略组合管理

```python
# 创建策略组合
await strategy_system.manager.create_strategy_group(
    group_name="momentum_group",
    strategy_ids=["strategy_1", "strategy_2", "strategy_3"],
    capital_allocation=0.6,  # 分配60%资金
    config={"risk_level": "medium"}
)

# 启动组合
await strategy_system.manager.start_strategy_group("momentum_group")

# 获取组合绩效
performance = await strategy_system.manager.update_group_performance("momentum_group")
```

### 风险控制配置

```python
from backend.strategy.core import RiskConfig

risk_config = RiskConfig(
    max_total_exposure=1.0,      # 最大总敞口
    max_single_position=0.1,     # 单个头寸最大比例
    max_daily_loss=0.02,         # 单日最大亏损
    max_drawdown=0.05,           # 最大回撤
    max_leverage=3.0,            # 最大杠杆
    var_confidence_level=0.95    # VaR置信度
)

# 应用风险配置
strategy_system = StrategySystem(risk_config=risk_config)
```

### 绩效分析配置

```python
from backend.strategy.core import PerformanceConfig, PerformanceFrequency

performance_config = PerformanceConfig(
    frequency=PerformanceFrequency.DAILY,
    benchmark_symbol="SPY",
    risk_free_rate=0.03,
    enable_benchmark_comparison=True,
    update_interval=300
)

# 应用绩效配置
strategy_system = StrategySystem(performance_config=performance_config)
```

## 🛡️ 风险指标说明

### 基础风险指标
- **最大回撤 (Max Drawdown)**: 从峰值到谷值的最大跌幅
- **波动率 (Volatility)**: 收益率的标准差（年化）
- **VaR (Value at Risk)**: 给定置信度下的最大可能损失
- **CVaR (Conditional VaR)**: 超过VaR的平均损失

### 风险调整收益
- **夏普比率 (Sharpe Ratio)**: 超额收益与波动率的比值
- **索提诺比率 (Sortino Ratio)**: 超额收益与下行波动率的比值
- **卡尔马比率 (Calmar Ratio)**: 年化收益与最大回撤的比值
- **信息比率 (Information Ratio)**: 相对基准的超额收益与跟踪误差的比值

## 📈 绩效指标说明

### 收益指标
- **总收益率 (Total Return)**: 整个期间的累计收益率
- **年化收益率 (Annual Return)**: 按年计算的收益率
- **累计收益率 (Cumulative Return)**: (1+日收益率)的累积乘积

### 交易指标
- **总交易次数 (Total Trades)**: 完成的交易笔数
- **胜率 (Win Rate)**: 盈利交易占总交易的比例
- **盈亏比 (Profit Factor)**: 总盈利与总亏损的比值
- **期望值 (Expectancy)**: 每笔交易的期望盈亏

### 稳定性指标
- **稳定性 (Stability)**: 收益曲线的线性度（R²）
- **偏度 (Skewness)**: 收益分布的不对称程度
- **峰度 (Kurtosis)**: 收益分布的尖峭程度

## 🔧 自定义扩展

### 自定义技术指标

```python
class CustomIndicator:
    """自定义技术指标"""
    
    def __init__(self, period: int = 20):
        self.period = period
        self.data = []
    
    def update(self, value: float) -> float:
        self.data.append(value)
        if len(self.data) > self.period:
            self.data.pop(0)
        
        return sum(self.data) / len(self.data)

# 在策略中使用
class MyAdvancedStrategy(BaseStrategy):
    
    async def on_start(self):
        self.custom_ma = CustomIndicator(period=20)
        self.custom_momentum = CustomIndicator(period=10)
    
    async def on_tick(self, data: MarketData):
        ma_value = self.custom_ma.update(data.close)
        momentum = self.custom_momentum.update(data.close - data.open)
        
        # 使用自定义指标的交易逻辑
        pass
```

### 自定义风险控制

```python
from backend.strategy.core import RiskManager, RiskEvent, RiskLevel

class CustomRiskManager(RiskManager):
    """自定义风险管理器"""
    
    async def custom_risk_check(self, strategy_id: str) -> bool:
        """自定义风险检查"""
        # 实现自定义风险逻辑
        strategy = self._strategies.get(strategy_id)
        if not strategy:
            return False
        
        # 例如：检查持仓集中度
        positions = strategy.get_all_positions()
        if len(positions) > 0:
            largest_position = max(positions.values(), 
                                 key=lambda p: float(p.market_value))
            concentration = float(largest_position.market_value) / float(strategy.account_balance)
            
            if concentration > 0.3:  # 30%集中度限制
                await self._handle_custom_risk_event(strategy_id, "持仓过度集中")
                return False
        
        return True
    
    async def _handle_custom_risk_event(self, strategy_id: str, message: str):
        """处理自定义风险事件"""
        # 创建风险事件并处理
        pass
```

## 🚨 常见问题解决

### 1. 策略启动失败
```python
# 检查策略状态
status = strategy_system.get_system_status()
print(f"系统状态: {status}")

# 检查日志
import logging
logging.basicConfig(level=logging.INFO)
```

### 2. 数据推送问题
```python
# 验证数据格式
market_data = MarketData(
    symbol="BTCUSDT",
    timestamp=datetime.now(),
    open=50000.0,    # 确保是float类型
    high=50100.0,
    low=49900.0,
    close=50050.0,
    volume=1000.0
)

# 检查数据推送状态
await strategy_system.feed_market_data(market_data)
```

### 3. 绩效计算异常
```python
# 确保有足够的历史数据
equity_curve = strategy_system.performance_analyzer.get_equity_curve(strategy_id)
if equity_curve is None or len(equity_curve) < 10:
    print("历史数据不足，无法计算绩效指标")
```

### 4. 内存使用过高
```python
# 配置数据保留策略
from backend.strategy.core import EngineConfig

engine_config = EngineConfig(
    max_bars_in_memory=5000,  # 限制内存中的数据量
    data_queue_size=1000,     # 限制数据队列大小
    order_queue_size=500      # 限制订单队列大小
)
```

## 📚 示例策略

项目提供了多个示例策略供参考：

1. **移动平均策略** (`examples/simple_ma_strategy.py`)
   - 基于移动平均线的趋势跟随策略
   - 适合初学者学习基础概念

2. **配对交易策略** (`examples/pairs_trading.py`)
   - 基于统计套利的配对交易
   - 展示多品种策略开发

3. **均值回归策略** (`examples/mean_reversion.py`)
   - 基于价格均值回归的策略
   - 演示震荡市场的交易逻辑

## 🔗 相关文档

- [FastAPI官方文档](https://fastapi.tiangolo.com/)
- [Pandas官方文档](https://pandas.pydata.org/)
- [NumPy官方文档](https://numpy.org/)
- [量化投资理论](https://en.wikipedia.org/wiki/Quantitative_analysis_(finance))

## 🤝 贡献指南

欢迎贡献代码和改进建议！

1. Fork 项目
2. 创建特性分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 📞 支持

如有问题或建议，请：
- 提交 Issue
- 发送邮件至 support@redfire.com
- 访问在线文档

---

**RedFire量化策略模块** - 让量化交易更简单、更专业、更可靠！
