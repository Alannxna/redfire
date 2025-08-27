# 🚀 RedFire Chart Engine - 专业量化图表引擎

## 📊 项目概述

RedFire Chart Engine 是基于vnpy-core强大的桌面图表组件，专为现代Web应用设计的专业量化交易图表引擎。

### 🎯 核心特性

- ✅ **vnpy图表算法移植**: 基于vnpy-core成熟的图表渲染和技术指标算法
- ✅ **高性能Web渲染**: Canvas/WebGL渲染，支持10万+K线丝滑显示
- ✅ **实时数据流**: WebSocket实时推送，毫秒级数据更新
- ✅ **专业技术指标**: 20+种技术指标，包括MA、MACD、RSI、BOLL、KDJ等
- ✅ **多图表管理**: 支持100+图表并发，智能资源管理
- ✅ **FastAPI集成**: 完整的RESTful API接口

### 🏗️ 架构设计

```
RedFire Chart Engine
├── 核心引擎 (ChartEngine)
│   ├── 数据管理器 (ChartDataManager)
│   ├── Web渲染器 (WebChartRenderer)  
│   ├── 指标计算器 (IndicatorCalculator)
│   └── 性能监控器 (PerformanceMonitor)
├── API接口 (ChartEngineAPI)
├── WebSocket处理器 (ChartWebSocketHandler)
└── 前端组件 (Chart Components)
```

## 🚀 快速开始

### 1. 安装依赖

```bash
cd backend/core/chart-engine
pip install -r requirements.txt
```

### 2. 基础使用

```python
from src.core.chart_engine import ChartEngine
from src.models.chart_models import ChartType, Interval

# 创建图表引擎
engine = ChartEngine()
await engine.start()

# 创建图表
chart = await engine.create_chart(
    chart_id="BTCUSDT_1m",
    symbol="BTCUSDT", 
    chart_type=ChartType.CANDLESTICK,
    interval=Interval.MINUTE_1
)

# 订阅图表
subscription = await engine.subscribe_chart("BTCUSDT_1m", "user_123")

# 获取渲染数据
render_data = await engine.get_chart_render_data("BTCUSDT_1m")
```

### 3. API接口使用

```python
from fastapi import FastAPI
from src.api.chart_api import ChartEngineAPI

app = FastAPI()
chart_engine = ChartEngine()
chart_api = ChartEngineAPI(chart_engine)

# 注册API路由
app.include_router(chart_api.get_router())
```

## 📚 核心组件详解

### 1. ChartEngine - 核心引擎

```python
class ChartEngine:
    """图表引擎核心类"""
    
    async def create_chart(self, chart_id, symbol, chart_type, interval, config)
    async def delete_chart(self, chart_id)
    async def subscribe_chart(self, chart_id, subscriber_id)
    async def update_chart_data(self, chart_id, bar_data)
    async def get_chart_render_data(self, chart_id)
```

**功能特性:**
- 🔄 多图表并发管理
- 📊 实时数据更新
- 👥 订阅者管理
- ⚡ 高性能缓存

### 2. ChartDataManager - 数据管理器

```python
class ChartDataManager:
    """图表数据管理器"""
    
    async def create_chart_data(self, chart_id, symbol, interval)
    async def add_bar_data(self, chart_id, bar)
    async def get_chart_data(self, chart_id, limit, start_time, end_time)
    async def get_price_range(self, chart_id, count)
```

**功能特性:**
- 💾 高性能内存缓存
- 🔍 智能数据检索
- 📈 价格范围计算
- 🧹 自动缓存清理

### 3. WebChartRenderer - Web渲染器

```python
class WebChartRenderer:
    """Web图表渲染器"""
    
    async def create_chart_renderer(self, chart_id, chart_type, config)
    async def prepare_render_data(self, chart_id, bars, indicators, config)
```

**功能特性:**
- 🎨 多种图表类型 (K线、分时、面积图)
- 🎯 精确的坐标计算
- 🌈 专业配色方案
- 📱 响应式设计

### 4. IndicatorCalculator - 指标计算器

```python
class IndicatorCalculator:
    """技术指标计算器"""
    
    async def calculate_indicators(self, chart_id, bars, indicator_configs)
    async def get_indicators(self, chart_id)
```

**支持指标:**
- 📊 **趋势指标**: MA、EMA、MACD
- 📈 **动量指标**: RSI、KDJ、CCI
- 📉 **波动指标**: BOLL、ATR
- 📋 **成交量指标**: OBV、VOLUME

## 🔧 配置说明

### 图表配置 (ChartConfig)

```python
config = ChartConfig(
    title="BTCUSDT 1分钟K线",
    show_volume=True,           # 显示成交量
    show_crosshair=True,        # 显示十字光标
    max_bars=1000,              # 最大K线数量
    decimal_places=2,           # 小数位数
    auto_scale=True,            # 自动缩放
    up_color="#26a69a",         # 上涨颜色
    down_color="#ef5350",       # 下跌颜色
    indicators=[                # 技术指标
        IndicatorConfig(
            type=IndicatorType.MA,
            name="MA20",
            parameters={"period": 20}
        )
    ]
)
```

### 引擎配置

```python
engine_config = {
    "max_charts": 100,              # 最大图表数量
    "max_bars_per_chart": 10000,    # 单图表最大K线数
    "cache_size": 1000,             # 缓存大小
    "cache_ttl": 300,               # 缓存TTL(秒)
    "render_fps": 60,               # 渲染帧率
    "data_sources": {               # 数据源配置
        "mock_data": True
    }
}
```

## 🔌 API接口

### RESTful API

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/chart/status` | 获取引擎状态 |
| POST | `/api/chart/charts` | 创建图表 |
| GET | `/api/chart/charts` | 获取图表列表 |
| GET | `/api/chart/charts/{id}` | 获取图表信息 |
| GET | `/api/chart/charts/{id}/data` | 获取图表数据 |
| POST | `/api/chart/charts/{id}/subscribe` | 订阅图表 |
| POST | `/api/chart/charts/{id}/indicators` | 添加技术指标 |
| DELETE | `/api/chart/charts/{id}` | 删除图表 |

### WebSocket接口

```javascript
// 连接WebSocket
const ws = new WebSocket('ws://localhost:8000/api/chart/ws');

// 订阅图表
ws.send(JSON.stringify({
    action: 'subscribe',
    chart_id: 'BTCUSDT_1m'
}));

// 接收实时数据
ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    // 更新图表
    updateChart(data);
};
```

## 📊 性能指标

### 性能目标
- **渲染性能**: 60FPS丝滑渲染
- **数据容量**: 单图表支持10万+K线
- **并发能力**: 支持100+用户同时看图
- **响应时间**: API响应 < 100ms
- **内存使用**: 单图表 < 50MB

### 性能监控

```python
# 获取性能指标
status = engine.get_engine_status()
print(status["performance"])

# 输出示例:
{
    "uptime": 3600.5,
    "counters": {
        "render_requests_BTCUSDT_1m": 1234,
        "indicator_calculations_BTCUSDT_1m": 567
    },
    "metrics": {
        "active_charts": {"count": 10, "avg": 8.5, "max": 15},
        "memory_usage": {"latest": 512.3}
    },
    "timers": {
        "render_prepare_BTCUSDT_1m": {
            "count": 1000, "avg": 0.025, "p99": 0.08
        }
    }
}
```

## 🧪 测试

### 单元测试

```bash
cd backend/core/chart-engine
python -m pytest tests/ -v
```

### 性能测试

```bash
# 压力测试
python tests/performance/stress_test.py

# 内存泄漏测试  
python tests/performance/memory_test.py
```

## 🔗 集成示例

### 与RedFire主系统集成

```python
# backend/main.py
from core.chart_engine.src.core.chart_engine import ChartEngine
from core.chart_engine.src.api.chart_api import ChartEngineAPI

class RedFireApplication:
    def __init__(self):
        # 初始化图表引擎
        self.chart_engine = ChartEngine()
        self.chart_api = ChartEngineAPI(self.chart_engine)
        
    async def startup(self):
        # 启动图表引擎
        await self.chart_engine.start()
        
        # 注册API路由
        self.app.include_router(self.chart_api.get_router())
```

### 与策略引擎集成

```python
# 策略回测结果展示
async def show_backtest_result(strategy_id: str):
    # 获取回测数据
    backtest_data = await get_backtest_data(strategy_id)
    
    # 创建图表
    chart_id = f"backtest_{strategy_id}"
    await chart_engine.create_chart(
        chart_id=chart_id,
        symbol=backtest_data.symbol,
        chart_type=ChartType.CANDLESTICK,
        interval=backtest_data.interval
    )
    
    # 添加K线数据
    for bar in backtest_data.bars:
        await chart_engine.update_chart_data(chart_id, bar)
    
    # 添加交易信号指标
    await chart_engine.add_indicator(chart_id, "trade_signals", trade_points)
```

## 🛠️ 开发指南

### 添加新的技术指标

```python
# 1. 在TechnicalIndicators类中添加计算方法
@staticmethod
def new_indicator(prices: np.ndarray, period: int) -> np.ndarray:
    # 指标计算逻辑
    pass

# 2. 在IndicatorCalculationEngine中添加处理
def _calculate_new_indicator(self, prices, params):
    period = params.get('period', 14)
    values = TechnicalIndicators.new_indicator(prices, period)
    return {"new_indicator": values.tolist()}

# 3. 在IndicatorType枚举中添加类型
class IndicatorType(str, Enum):
    NEW_INDICATOR = "new_indicator"
```

### 添加新的图表类型

```python
# 1. 在ChartType枚举中添加类型
class ChartType(str, Enum):
    NEW_CHART = "new_chart"

# 2. 在ChartRenderer中添加渲染逻辑
def _prepare_new_chart_data(self, bars):
    # 新图表类型的渲染数据准备
    pass
```

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

*RedFire Chart Engine - 让量化交易图表更专业、更强大！* 🚀