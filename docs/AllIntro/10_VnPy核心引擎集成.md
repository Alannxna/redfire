# 🚀 TODO-10: VnPy核心引擎集成

## 🎯 任务概述

**任务ID**: vnpy_01  
**优先级**: 高  
**预估工期**: 6-7天  
**负责模块**: VnPy集成

### 问题描述
完善VnPy核心引擎与RedFire系统的深度集成，包括交易引擎、策略引擎、事件引擎、风险引擎的统一管理和微服务化改造。

## 🔍 现状分析

### 当前VnPy集成状况

#### 1. 基础交易引擎架构存在
```python
# backend/core/tradingEngine/mainEngine.py
class MainTradingEngine:
    def __init__(self, event_engine: Optional[EventTradingEngine] = None):
        self.eventTradingEngine = event_engine or EventTradingEngine()
        self.engineManager = EngineManager()
        self.pluginManager = PluginManager()
        
# backend/core/tradingEngine/eventEngine.py  
class EventTradingEngine:
    def __init__(self):
        self.eventQueue = Queue()
        self.eventHandlers: Dict[str, List[Callable]] = {}
        
# 问题:
# - 与VnPy官方引擎API不完全兼容
# - 缺乏完整的VnPy功能模块集成
# - 事件引擎局限于本地处理
```

#### 2. VnPy配置和示例
```python
# backend/core/vnpy-engine/examples/client_server/run_client.py
from vnpy.event import EventEngine
from vnpy.trader.engine import MainEngine
from vnpy.trader.ui import MainWindow, create_qapp

from vnpy_rpcservice import RpcGateway
from vnpy_ctastrategy import CtaStrategyApp
from vnpy_datamanager import DataManagerApp

def main():
    event_engine = EventEngine()
    main_engine = MainEngine(event_engine)
    
    # 添加功能模块
    main_engine.add_app(CtaStrategyApp)
    main_engine.add_app(DataManagerApp)
    
# 问题:
# - 只是基础的VnPy使用示例
# - 没有与RedFire微服务架构集成
# - 缺乏API接口封装
```

#### 3. 配置管理分散
```python
# backend/core/vnpy-engine/config/backend/config.env
VNPY_DATA_DIR=./vnpy_data
VNPY_LOG_DIR=./vnpy_logs
VNPY_CONFIG_DIR=./vnpy_config

# config/vt_setting.json
# VnPy默认配置文件

# 问题:
# - VnPy配置与RedFire配置分离
# - 缺乏统一的配置管理
# - 环境配置不完整
```

### 架构集成问题

#### 1. 服务化程度不足
```
当前架构:
VnPy Engine → 本地引擎
            → 本地事件处理
            → 本地数据管理

需要的架构:
VnPy Core Service (8006) → 微服务化
                      → 跨服务事件
                      → 分布式数据管理
```

#### 2. API接口缺失
- 没有RESTful API包装VnPy功能
- 缺乏WebSocket实时数据推送
- 无法与其他微服务协同工作

#### 3. 数据持久化不完整
- VnPy数据没有与RedFire数据库集成
- 缺乏统一的数据模型
- 历史数据管理分离

## 🎨 设计方案

### 1. VnPy微服务化架构

```python
# services/vnpy-core/main.py
class VnPyCoreService:
    """VnPy核心服务"""
    
    def __init__(self, config: VnPyCoreConfig):
        self.config = config
        self.app = FastAPI(title="VnPy Core Service", version="1.0.0")
        
        # VnPy核心组件
        self.event_engine = EventEngine()
        self.main_engine = MainEngine(self.event_engine)
        self.strategy_engine = None
        self.risk_engine = None
        
        # RedFire集成组件
        self.db_manager = DatabaseManager(config.database)
        self.message_bus = MessageBus(config.message_bus)
        self.service_registry = ServiceRegistry(config.service_registry)
        
        # 初始化服务
        self._setup_vnpy_apps()
        self._setup_api_routes()
        self._setup_event_handlers()
        
    def _setup_vnpy_apps(self):
        """设置VnPy应用模块"""
        # CTA策略引擎
        self.main_engine.add_app(CtaStrategyApp)
        self.strategy_engine = self.main_engine.get_app("CtaStrategy")
        
        # 数据管理器
        self.main_engine.add_app(DataManagerApp)
        self.data_manager = self.main_engine.get_app("DataManager")
        
        # 风险管理器  
        self.main_engine.add_app(RiskManagerApp)
        self.risk_engine = self.main_engine.get_app("RiskManager")
        
        # 算法交易
        self.main_engine.add_app(AlgoTradingApp)
        self.algo_engine = self.main_engine.get_app("AlgoTrading")
        
        # 图表分析
        self.main_engine.add_app(ChartWizardApp)
        self.chart_engine = self.main_engine.get_app("ChartWizard")
        
    def _setup_api_routes(self):
        """设置API路由"""
        # 交易相关API
        self.app.include_router(
            create_trading_router(self.main_engine),
            prefix="/api/v1/trading",
            tags=["交易"]
        )
        
        # 策略相关API
        self.app.include_router(
            create_strategy_router(self.strategy_engine),
            prefix="/api/v1/strategies", 
            tags=["策略"]
        )
        
        # 数据相关API
        self.app.include_router(
            create_data_router(self.data_manager),
            prefix="/api/v1/data",
            tags=["数据"]
        )
        
        # 风险相关API
        self.app.include_router(
            create_risk_router(self.risk_engine),
            prefix="/api/v1/risk",
            tags=["风险"]
        )
        
        # WebSocket端点
        self.app.websocket("/ws")(self.websocket_endpoint)
    
    async def websocket_endpoint(self, websocket: WebSocket):
        """WebSocket端点"""
        await self.message_bus.handle_websocket_connection(websocket)
        
    def _setup_event_handlers(self):
        """设置事件处理器"""
        # 订单事件处理
        self.event_engine.register(EVENT_ORDER, self._on_order_event)
        
        # 成交事件处理
        self.event_engine.register(EVENT_TRADE, self._on_trade_event)
        
        # 持仓事件处理
        self.event_engine.register(EVENT_POSITION, self._on_position_event)
        
        # 账户事件处理
        self.event_engine.register(EVENT_ACCOUNT, self._on_account_event)
        
        # Tick数据事件处理
        self.event_engine.register(EVENT_TICK, self._on_tick_event)
    
    async def _on_order_event(self, event: Event):
        """订单事件处理"""
        order_data = event.data
        
        # 持久化到数据库
        await self.db_manager.store_order_event(order_data)
        
        # 发布到消息总线
        await self.message_bus.publish("order.updated", {
            "order_id": order_data.orderid,
            "symbol": order_data.symbol,
            "status": order_data.status.value,
            "traded": order_data.traded,
            "timestamp": datetime.now().isoformat()
        })
        
    async def _on_trade_event(self, event: Event):
        """成交事件处理"""
        trade_data = event.data
        
        # 持久化到数据库
        await self.db_manager.store_trade_event(trade_data)
        
        # 发布到消息总线
        await self.message_bus.publish("trade.executed", {
            "trade_id": trade_data.tradeid,
            "order_id": trade_data.orderid,
            "symbol": trade_data.symbol,
            "price": trade_data.price,
            "volume": trade_data.volume,
            "timestamp": datetime.now().isoformat()
        })
        
    async def _on_tick_event(self, event: Event):
        """Tick数据事件处理"""
        tick_data = event.data
        
        # 存储到时序数据库
        await self.db_manager.store_tick_data(tick_data)
        
        # 实时推送到WebSocket客户端
        await self.message_bus.publish(f"tick.{tick_data.symbol}", {
            "symbol": tick_data.symbol,
            "last_price": tick_data.last_price,
            "volume": tick_data.volume,
            "timestamp": tick_data.datetime.isoformat()
        })
```

### 2. API接口封装

```python
# services/vnpy-core/routers/trading_router.py
def create_trading_router(main_engine: MainEngine) -> APIRouter:
    """创建交易API路由"""
    router = APIRouter()
    
    @router.get("/gateways")
    async def get_gateways():
        """获取交易接口列表"""
        gateways = main_engine.get_all_gateway_names()
        return {"gateways": gateways}
    
    @router.post("/gateways/{gateway_name}/connect")
    async def connect_gateway(gateway_name: str, setting: dict):
        """连接交易接口"""
        result = main_engine.connect(setting, gateway_name)
        return {"success": result, "gateway": gateway_name}
    
    @router.post("/orders")
    async def submit_order(order_request: OrderRequest):
        """提交订单"""
        req = OrderRequest(
            symbol=order_request.symbol,
            exchange=Exchange(order_request.exchange),
            direction=Direction(order_request.direction),
            type=OrderType(order_request.type),
            volume=order_request.volume,
            price=order_request.price,
            reference=order_request.reference
        )
        
        order_id = main_engine.send_order(req, order_request.gateway_name)
        return {"order_id": order_id, "success": bool(order_id)}
    
    @router.delete("/orders/{order_id}")
    async def cancel_order(order_id: str, gateway_name: str):
        """撤销订单"""
        req = CancelRequest(orderid=order_id, symbol="", exchange=Exchange.SSE)
        result = main_engine.cancel_order(req, gateway_name)
        return {"success": result}
    
    @router.get("/orders")
    async def get_orders():
        """获取订单列表"""
        orders = main_engine.get_all_orders()
        return {
            "orders": [
                {
                    "orderid": order.orderid,
                    "symbol": order.symbol,
                    "exchange": order.exchange.value,
                    "direction": order.direction.value,
                    "type": order.type.value,
                    "volume": order.volume,
                    "traded": order.traded,
                    "status": order.status.value,
                    "datetime": order.datetime.isoformat()
                }
                for order in orders
            ]
        }
    
    @router.get("/positions")
    async def get_positions():
        """获取持仓列表"""
        positions = main_engine.get_all_positions()
        return {
            "positions": [
                {
                    "symbol": pos.symbol,
                    "exchange": pos.exchange.value,
                    "direction": pos.direction.value,
                    "volume": pos.volume,
                    "frozen": pos.frozen,
                    "price": pos.price,
                    "pnl": pos.pnl
                }
                for pos in positions
            ]
        }
    
    @router.get("/accounts")
    async def get_accounts():
        """获取账户信息"""
        accounts = main_engine.get_all_accounts()
        return {
            "accounts": [
                {
                    "accountid": acc.accountid,
                    "balance": acc.balance,
                    "frozen": acc.frozen,
                    "available": acc.available
                }
                for acc in accounts
            ]
        }
    
    return router

# services/vnpy-core/routers/strategy_router.py
def create_strategy_router(strategy_engine) -> APIRouter:
    """创建策略API路由"""
    router = APIRouter()
    
    @router.get("/")
    async def get_strategies():
        """获取策略列表"""
        strategies = strategy_engine.get_all_strategy_names()
        return {"strategies": strategies}
    
    @router.post("/{strategy_name}/start")
    async def start_strategy(strategy_name: str):
        """启动策略"""
        result = strategy_engine.start_strategy(strategy_name)
        return {"success": result, "strategy": strategy_name}
    
    @router.post("/{strategy_name}/stop")
    async def stop_strategy(strategy_name: str):
        """停止策略"""
        result = strategy_engine.stop_strategy(strategy_name)
        return {"success": result, "strategy": strategy_name}
    
    @router.get("/{strategy_name}/parameters")
    async def get_strategy_parameters(strategy_name: str):
        """获取策略参数"""
        parameters = strategy_engine.get_strategy_parameters(strategy_name)
        return {"parameters": parameters}
    
    @router.put("/{strategy_name}/parameters")
    async def update_strategy_parameters(strategy_name: str, parameters: dict):
        """更新策略参数"""
        result = strategy_engine.edit_strategy(strategy_name, parameters)
        return {"success": result}
    
    @router.post("/")
    async def add_strategy(strategy_config: StrategyConfig):
        """添加策略"""
        result = strategy_engine.add_strategy(
            strategy_config.class_name,
            strategy_config.strategy_name,
            strategy_config.vt_symbol,
            strategy_config.setting
        )
        return {"success": result}
    
    @router.delete("/{strategy_name}")
    async def remove_strategy(strategy_name: str):
        """删除策略"""
        result = strategy_engine.remove_strategy(strategy_name)
        return {"success": result}
    
    return router
```

### 3. 数据集成和持久化

```python
# services/vnpy-core/data/vnpy_data_adapter.py
class VnPyDataAdapter:
    """VnPy数据适配器"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        
    async def store_order_event(self, order_data):
        """存储订单事件"""
        order_dict = {
            "order_id": order_data.orderid,
            "symbol": order_data.symbol,
            "exchange": order_data.exchange.value,
            "direction": order_data.direction.value,
            "order_type": order_data.type.value,
            "volume": float(order_data.volume),
            "traded": float(order_data.traded),
            "price": float(order_data.price) if order_data.price else None,
            "status": order_data.status.value,
            "datetime": order_data.datetime,
            "gateway_name": order_data.gateway_name,
            "reference": order_data.reference
        }
        
        # 存储到MySQL
        async with self.db_manager.mysql.begin() as conn:
            await conn.execute(
                insert(orders_table).values(**order_dict)
                .on_duplicate_key_update(**order_dict)
            )
        
        # 缓存最新状态到Redis
        await self.db_manager.redis.setex(
            f"order:{order_data.orderid}",
            3600,
            json.dumps(order_dict, default=str)
        )
    
    async def store_trade_event(self, trade_data):
        """存储成交事件"""
        trade_dict = {
            "trade_id": trade_data.tradeid,
            "order_id": trade_data.orderid,
            "symbol": trade_data.symbol,
            "exchange": trade_data.exchange.value,
            "direction": trade_data.direction.value,
            "volume": float(trade_data.volume),
            "price": float(trade_data.price),
            "datetime": trade_data.datetime,
            "gateway_name": trade_data.gateway_name
        }
        
        # 存储到MySQL
        async with self.db_manager.mysql.begin() as conn:
            await conn.execute(
                insert(trades_table).values(**trade_dict)
            )
    
    async def store_tick_data(self, tick_data):
        """存储Tick数据到时序数据库"""
        write_api = self.db_manager.influxdb.write_api()
        
        point = Point("tick_data") \
            .tag("symbol", tick_data.symbol) \
            .tag("exchange", tick_data.exchange.value) \
            .field("last_price", float(tick_data.last_price)) \
            .field("volume", float(tick_data.volume)) \
            .field("open_interest", float(tick_data.open_interest or 0)) \
            .field("bid_price_1", float(tick_data.bid_price_1 or 0)) \
            .field("ask_price_1", float(tick_data.ask_price_1 or 0)) \
            .field("bid_volume_1", float(tick_data.bid_volume_1 or 0)) \
            .field("ask_volume_1", float(tick_data.ask_volume_1 or 0)) \
            .time(tick_data.datetime)
        
        await write_api.write(
            bucket=self.config.influxdb_bucket,
            record=point
        )
    
    async def get_historical_data(self, symbol: str, exchange: str, 
                                 start: datetime, end: datetime, interval: str):
        """获取历史数据"""
        query_api = self.db_manager.influxdb.query_api()
        
        query = f'''
        from(bucket: "{self.config.influxdb_bucket}")
          |> range(start: {start.isoformat()}, stop: {end.isoformat()})
          |> filter(fn: (r) => r["_measurement"] == "tick_data")
          |> filter(fn: (r) => r["symbol"] == "{symbol}")
          |> filter(fn: (r) => r["exchange"] == "{exchange}")
          |> aggregateWindow(every: {interval}, fn: last)
          |> sort(columns: ["_time"])
        '''
        
        tables = await query_api.query(query)
        return self._parse_historical_data(tables)

# services/vnpy-core/strategies/strategy_manager.py
class RedFireStrategyManager:
    """RedFire策略管理器"""
    
    def __init__(self, strategy_engine, db_manager: DatabaseManager):
        self.strategy_engine = strategy_engine
        self.db_manager = db_manager
        
    async def load_strategies_from_db(self):
        """从数据库加载策略配置"""
        async with self.db_manager.mysql.begin() as conn:
            result = await conn.execute(
                select(strategies_table).where(strategies_table.c.is_active == True)
            )
            
            for row in result:
                await self._load_strategy(row)
    
    async def _load_strategy(self, strategy_row):
        """加载单个策略"""
        try:
            # 解析策略配置
            setting = json.loads(strategy_row.setting)
            
            # 添加到VnPy引擎
            self.strategy_engine.add_strategy(
                strategy_row.class_name,
                strategy_row.strategy_name,
                strategy_row.vt_symbol,
                setting
            )
            
            # 如果配置为自动启动
            if strategy_row.auto_start:
                self.strategy_engine.start_strategy(strategy_row.strategy_name)
                
        except Exception as e:
            logger.error(f"加载策略失败 {strategy_row.strategy_name}: {e}")
    
    async def save_strategy_to_db(self, strategy_name: str, config: dict):
        """保存策略配置到数据库"""
        strategy_dict = {
            "strategy_name": strategy_name,
            "class_name": config["class_name"],
            "vt_symbol": config["vt_symbol"], 
            "setting": json.dumps(config["setting"]),
            "is_active": True,
            "auto_start": config.get("auto_start", False)
        }
        
        async with self.db_manager.mysql.begin() as conn:
            await conn.execute(
                insert(strategies_table).values(**strategy_dict)
                .on_duplicate_key_update(**strategy_dict)
            )
```

### 4. 配置集成

```python
# services/vnpy-core/config/vnpy_config.py
class VnPyCoreConfig(BaseConfig):
    """VnPy核心服务配置"""
    
    # 服务基础配置
    service_name: str = "vnpy_core"
    service_port: int = 8006
    
    # VnPy数据目录
    vnpy_data_dir: str = Field(default="./vnpy_data")
    vnpy_config_dir: str = Field(default="./vnpy_config")
    vnpy_log_dir: str = Field(default="./vnpy_logs")
    
    # 数据库配置
    database: DatabaseConfig
    
    # 消息总线配置
    message_bus: MessageBusConfig
    
    # 交易接口配置
    gateways: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    
    # 策略配置
    strategies: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    
    # 风险管理配置
    risk_management: Dict[str, Any] = Field(default_factory=dict)
    
    def get_vnpy_setting(self) -> dict:
        """获取VnPy配置字典"""
        return {
            "data_folder": self.vnpy_data_dir,
            "log_folder": self.vnpy_log_dir,
            "gateways": self.gateways,
            "risk_management": self.risk_management
        }
    
    def save_vnpy_setting(self):
        """保存VnPy配置文件"""
        setting_file = Path(self.vnpy_config_dir) / "vt_setting.json"
        setting_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(setting_file, "w", encoding="utf-8") as f:
            json.dump(self.get_vnpy_setting(), f, indent=2, ensure_ascii=False)
```

## 🔧 实施步骤

### 阶段1: 基础架构搭建 (2天)

1. **创建VnPy微服务**
   ```bash
   mkdir -p services/vnpy-core/{routers,data,strategies,config}
   ```

2. **基础服务框架**
   - VnPyCoreService主类
   - API路由框架
   - 配置管理集成

### 阶段2: API接口实现 (2天)

1. **交易API封装**
   - 订单管理接口
   - 持仓查询接口
   - 账户信息接口

2. **策略API封装**
   - 策略生命周期管理
   - 参数配置接口
   - 性能监控接口

### 阶段3: 数据集成 (2天)

1. **数据持久化**
   - 交易数据存储
   - 历史数据查询
   - 实时数据推送

2. **事件处理**
   - VnPy事件到RedFire事件的转换
   - 跨服务事件分发
   - 事件持久化

### 阶段4: 高级功能集成 (1天)

1. **风险管理集成**
2. **监控和告警**
3. **性能优化**

## 📊 验收标准

### 功能验收
- [ ] VnPy引擎正常启动
- [ ] 交易API接口工作正常
- [ ] 策略引擎集成完成
- [ ] 数据持久化正常

### 性能指标
- [ ] API响应时间 < 100ms
- [ ] 事件处理延迟 < 50ms
- [ ] 策略运行稳定
- [ ] 内存使用合理

### 兼容性标准
- [ ] VnPy官方模块正常工作
- [ ] 现有策略无需修改
- [ ] 配置向后兼容
- [ ] 数据格式标准化

## 🚨 风险评估

### 高风险
- **VnPy版本兼容**: 不同VnPy版本API变化
- **策略迁移**: 现有策略可能需要修改

### 中风险
- **性能影响**: 微服务化可能影响性能
- **数据一致性**: 分布式数据一致性问题

### 缓解措施
1. **版本锁定**: 固定VnPy版本
2. **渐进迁移**: 逐步迁移现有策略
3. **性能测试**: 全面性能基准测试

## 📈 预期收益

### 短期收益
- VnPy功能微服务化
- API接口标准化
- 数据持久化完善

### 长期收益
- 支持分布式策略执行
- 完善的历史数据分析
- 高可用交易系统

## 📝 相关文档

- [VnPy官方文档](https://www.vnpy.com/docs/)
- [交易策略开发指南](../development/strategy-development.md)
- [风险管理配置](../operations/risk-management.md)

---

**更新时间**: 2024-01-15  
**文档版本**: v1.0  
**负责人**: RedFire架构团队
