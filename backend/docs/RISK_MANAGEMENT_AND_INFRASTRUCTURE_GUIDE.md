# 风险管理和基础设施完善指南

## 📋 概述

本文档详细介绍RedFire交易系统中完善的风险管理模块和基础设施组件，包括VaR计算、压力测试、实时监控、多级缓存系统和Kafka消息队列。

## 🔥 风险管理模块

### 1. VaR计算引擎

支持三种VaR计算方法：

#### 1.1 历史模拟VaR
```python
from src.domain.trading.services.enhanced_risk_service import EnhancedRiskService

risk_service = EnhancedRiskService()

# 计算历史模拟VaR
var_result = await risk_service.calculate_historical_var(
    positions=positions,
    confidence_level=0.95,
    time_horizon=1,
    lookback_days=252
)

print(f"VaR(95%): {var_result.var_value}")
print(f"期望损失: {var_result.expected_shortfall}")
```

#### 1.2 参数VaR
```python
# 计算参数VaR（假设正态分布）
var_result = await risk_service.calculate_parametric_var(
    positions=positions,
    confidence_level=0.95,
    time_horizon=1
)
```

#### 1.3 蒙特卡洛VaR
```python
# 计算蒙特卡洛VaR
var_result = await risk_service.calculate_monte_carlo_var(
    positions=positions,
    confidence_level=0.95,
    time_horizon=1,
    simulations=10000
)
```

### 2. 压力测试系统

#### 2.1 创建压力测试情景
```python
from src.domain.trading.services.enhanced_risk_service import StressTestScenario

# 创建市场暴跌情景
crash_scenario = StressTestScenario(
    scenario_id="MARKET_CRASH_2024",
    name="2024年市场暴跌",
    description="股票市场下跌25%的极端情景",
    market_shocks={
        "AAPL": Decimal("-0.25"),
        "MSFT": Decimal("-0.20"),
        "GOOGL": Decimal("-0.30")
    }
)

await risk_service.add_stress_scenario(crash_scenario)
```

#### 2.2 运行压力测试
```python
# 运行压力测试
stress_result = await risk_service.run_stress_test(
    scenario_id="MARKET_CRASH_2024",
    positions=positions,
    market_data=current_market_data
)

print(f"压力测试盈亏: {stress_result.portfolio_pnl}")
print(f"最大单品种损失: {min(stress_result.position_impacts.values())}")
```

#### 2.3 历史情景回测
```python
from datetime import datetime, timedelta

# 创建历史情景
start_date = datetime(2020, 3, 1)  # 2020年3月疫情暴跌
end_date = datetime(2020, 4, 1)

historical_scenario = await risk_service.create_historical_scenario(
    scenario_id="COVID_CRASH_2020",
    name="新冠疫情暴跌",
    description="2020年3月疫情引发的市场暴跌",
    start_date=start_date,
    end_date=end_date
)

# 运行历史回测
backtest_result = await risk_service.run_historical_backtest(
    scenario_id="COVID_CRASH_2020",
    positions=positions,
    initial_portfolio_value=Decimal("1000000")
)

print(f"回测总盈亏: {backtest_result.total_pnl}")
print(f"最大回撤: {backtest_result.max_drawdown}")
print(f"夏普比率: {backtest_result.sharpe_ratio}")
```

### 3. 实时风险监控

#### 3.1 添加监控规则
```python
from src.domain.trading.services.enhanced_risk_service import MonitoringRule, MonitoringFrequency
from src.domain.trading.services.advanced_risk_service import RiskLevel

# 创建自定义监控规则
custom_rule = MonitoringRule(
    rule_id="CUSTOM_VAR_LIMIT",
    name="自定义VaR限额",
    description="VaR不得超过总资产的3%",
    metric_name="var_95_ratio",
    threshold=Decimal("0.03"),
    comparison=">",
    severity=RiskLevel.CRITICAL,
    frequency=MonitoringFrequency.REAL_TIME
)

await risk_service.add_monitoring_rule(custom_rule)
```

#### 3.2 运行综合监控
```python
# 运行实时风险监控
alerts = await risk_service.run_comprehensive_monitoring(
    positions=positions,
    accounts=accounts,
    market_data=market_data
)

for alert in alerts:
    print(f"风险告警: {alert.message}")
    print(f"严重程度: {alert.severity.value}")
    print(f"详细信息: {alert.details}")
```

#### 3.3 获取风险指标
```python
# 计算综合风险指标
risk_metrics = await risk_service.calculate_comprehensive_risk_metrics(
    positions=positions,
    accounts=accounts,
    market_data=market_data
)

print(f"VaR(95%): {risk_metrics.var_95}")
print(f"VaR(99%): {risk_metrics.var_99}")
print(f"最大回撤: {risk_metrics.max_drawdown}")
print(f"投资组合Beta: {risk_metrics.beta}")
print(f"集中度风险: {risk_metrics.concentration_risk}")
print(f"流动性风险: {risk_metrics.liquidity_risk}")
```

### 4. 自动风险控制

#### 4.1 订单预检查
```python
from src.domain.trading.entities.order_entity import Order

# 新订单风险检查
new_order = Order(
    symbol="AAPL",
    direction=Direction.LONG,
    volume=Decimal("1000"),
    price=Decimal("150.00")
)

allow_order, control_actions = await risk_service.auto_risk_control(
    order=new_order,
    positions=positions,
    accounts=accounts,
    market_data=market_data
)

if not allow_order:
    print("订单被风险控制系统拒绝:")
    for action in control_actions:
        print(f"- {action}")
else:
    print("订单通过风险检查，可以执行")
```

## 🏗️ 基础设施模块

### 1. 多级缓存系统

#### 1.1 基本使用
```python
from src.infrastructure.cache.multi_level_cache import get_cache

# 获取全局缓存实例
cache = await get_cache()

# 设置缓存
await cache.set("user:123", {"name": "张三", "balance": 100000})

# 获取缓存
user_data = await cache.get("user:123")
print(user_data)  # {'name': '张三', 'balance': 100000}

# 删除缓存
await cache.delete("user:123")
```

#### 1.2 配置缓存层级
```python
from src.infrastructure.cache.multi_level_cache import MultiLevelCache, CacheLevel

# 自定义缓存配置
l1_config = {
    "max_size": 1000,
    "max_memory": 100 * 1024 * 1024,  # 100MB
    "eviction_policy": "LRU"
}

l2_config = {
    "redis_url": "redis://localhost:6379",
    "db": 1,
    "key_prefix": "trading:",
    "default_ttl": 3600
}

l3_config = {
    "cache_dir": "/var/cache/redfire",
    "max_files": 10000,
    "default_ttl": 86400
}

cache = MultiLevelCache(
    l1_config=l1_config,
    l2_config=l2_config,
    l3_config=l3_config
)

await cache.initialize()
```

#### 1.3 缓存装饰器
```python
from src.infrastructure.cache.multi_level_cache import cache_decorator

@cache_decorator(ttl=3600)
async def get_market_data(symbol: str) -> dict:
    # 模拟从外部API获取市场数据
    return {
        "symbol": symbol,
        "price": 150.00,
        "timestamp": datetime.now().isoformat()
    }

# 第一次调用会从API获取数据并缓存
data1 = await get_market_data("AAPL")

# 第二次调用直接从缓存返回
data2 = await get_market_data("AAPL")  # 从缓存获取
```

#### 1.4 缓存预热
```python
# 定义数据加载器
async def load_user_data(user_id: str) -> dict:
    # 从数据库加载用户数据
    return {"user_id": user_id, "name": f"User_{user_id}"}

# 预热缓存
user_ids = ["1001", "1002", "1003", "1004", "1005"]
await cache.warmup(user_ids, load_user_data)
```

#### 1.5 获取缓存统计
```python
# 获取缓存统计信息
stats = await cache.get_stats()

print(f"总命中率: {stats['total_stats']['hit_rate']:.2%}")
print(f"L1缓存命中率: {stats['l1_stats']['hit_rate']:.2%}")
print(f"L2缓存命中率: {stats['l2_stats']['hit_rate']:.2%}")
print(f"L3缓存命中率: {stats['l3_stats']['hit_rate']:.2%}")
```

### 2. Kafka消息队列系统

#### 2.1 基本消息发送
```python
from src.infrastructure.messaging.kafka_service import get_message_service, Message, MessageType

# 获取消息服务
message_service = await get_message_service()

# 创建消息
trade_message = Message(
    key="TRADE_001",
    value={
        "order_id": "ORDER_123",
        "symbol": "AAPL",
        "quantity": 100,
        "price": 150.00,
        "timestamp": datetime.now().isoformat()
    },
    headers={"source": "trading_engine"},
    message_type=MessageType.TRADE_ORDER
)

# 发送消息
success = await message_service.send_message("trade_orders", trade_message)
if success:
    print("交易订单消息发送成功")
```

#### 2.2 批量发送消息
```python
# 批量发送市场数据
market_messages = []
for symbol in ["AAPL", "MSFT", "GOOGL"]:
    message = {
        "key": symbol,
        "value": {
            "symbol": symbol,
            "price": 150.00,
            "volume": 1000,
            "timestamp": datetime.now().isoformat()
        }
    }
    market_messages.append(message)

success_count, failed_count = await message_service.send_batch(
    "market_data", 
    market_messages
)

print(f"批量发送: 成功 {success_count}, 失败 {failed_count}")
```

#### 2.3 消息消费
```python
from src.infrastructure.messaging.kafka_service import message_handler

@message_handler("trade_orders", "risk_monitor_group")
async def handle_trade_order(message: Message):
    """处理交易订单消息"""
    order_data = message.value
    print(f"收到交易订单: {order_data['order_id']}")
    
    # 执行风险检查
    if order_data['quantity'] > 1000:
        print("大额订单，需要额外审批")
    
    # 更新订单状态
    print(f"订单 {order_data['order_id']} 处理完成")

@message_handler("risk_alerts", "alert_processor_group")
async def handle_risk_alert(message: Message):
    """处理风险告警消息"""
    alert_data = message.value
    print(f"收到风险告警: {alert_data['severity']} - {alert_data['message']}")
    
    # 根据严重程度处理
    if alert_data['severity'] == 'CRITICAL':
        print("发送紧急通知给风险管理员")
    
    # 记录告警日志
    print(f"告警已记录: {alert_data['alert_id']}")
```

#### 2.4 创建主题
```python
from src.infrastructure.messaging.kafka_service import TopicConfig, CompressionType

# 创建自定义主题
custom_topic = TopicConfig(
    name="portfolio_updates",
    num_partitions=6,
    replication_factor=1,
    retention_ms=604800000,  # 7天
    compression_type=CompressionType.LZ4
)

success = await message_service.topic_manager.create_topic(custom_topic)
if success:
    print("自定义主题创建成功")
```

#### 2.5 获取消息统计
```python
# 获取消息服务统计
stats = await message_service.get_stats()

print(f"服务运行状态: {stats['is_running']}")
print(f"生产者发送消息数: {stats['producer_stats']['messages_sent']}")
print(f"可用主题: {stats['topics']}")

# 消费者统计
for group_id, consumer_stats in stats['consumer_stats'].items():
    print(f"消费者组 {group_id}: 消费 {consumer_stats['messages_consumed']} 条消息")
```

## 🔧 集成示例

### 1. 完整的风险监控工作流
```python
async def risk_monitoring_workflow():
    """完整的风险监控工作流"""
    
    # 1. 初始化服务
    risk_service = EnhancedRiskService()
    cache = await get_cache()
    message_service = await get_message_service()
    
    # 2. 获取当前持仓和市场数据
    positions = await get_current_positions()
    accounts = await get_current_accounts()
    market_data = await get_market_data()
    
    # 3. 计算风险指标
    risk_metrics = await risk_service.calculate_comprehensive_risk_metrics(
        positions, accounts, market_data
    )
    
    # 4. 缓存风险指标
    await cache.set(
        "latest_risk_metrics", 
        risk_metrics.to_dict(), 
        ttl=300  # 5分钟缓存
    )
    
    # 5. 运行监控检查
    alerts = await risk_service.run_comprehensive_monitoring(
        positions, accounts, market_data
    )
    
    # 6. 发送风险告警
    for alert in alerts:
        alert_message = Message(
            key=alert.alert_id,
            value=alert.to_dict(),
            message_type=MessageType.RISK_ALERT
        )
        
        await message_service.send_message("risk_alerts", alert_message)
    
    # 7. 运行压力测试（定期）
    if should_run_stress_test():
        for scenario_id in ["MARKET_CRASH", "RATE_RISE", "EM_CRISIS"]:
            stress_result = await risk_service.run_stress_test(
                scenario_id, positions, market_data
            )
            
            # 发送压力测试结果
            stress_message = Message(
                key=f"stress_test_{scenario_id}",
                value=stress_result.to_dict(),
                message_type=MessageType.SYSTEM_EVENT
            )
            
            await message_service.send_message("system_events", stress_message)
    
    print(f"风险监控完成: {len(alerts)} 个告警, 风险指标已更新")
```

### 2. 交易订单风险检查
```python
async def process_trading_order(order_data: dict):
    """处理交易订单的风险检查"""
    
    # 1. 从缓存获取当前风险状态
    cache = await get_cache()
    current_risk = await cache.get("latest_risk_metrics")
    
    if current_risk and current_risk["var_95_ratio"] > 0.05:
        print("当前VaR超限，暂停新订单")
        return False
    
    # 2. 创建订单对象
    order = Order(**order_data)
    
    # 3. 获取当前状态
    positions = await get_current_positions()
    accounts = await get_current_accounts()
    market_data = await get_market_data()
    
    # 4. 风险控制检查
    risk_service = EnhancedRiskService()
    allow_order, control_actions = await risk_service.auto_risk_control(
        order, positions, accounts, market_data
    )
    
    # 5. 发送决策消息
    message_service = await get_message_service()
    decision_message = Message(
        key=order.order_id,
        value={
            "order_id": order.order_id,
            "allow_order": allow_order,
            "control_actions": control_actions,
            "timestamp": datetime.now().isoformat()
        },
        message_type=MessageType.SYSTEM_EVENT
    )
    
    await message_service.send_message("order_decisions", decision_message)
    
    return allow_order
```

### 3. 缓存优化的数据访问
```python
from src.infrastructure.cache.multi_level_cache import cache_decorator

@cache_decorator(ttl=1800)  # 30分钟缓存
async def get_portfolio_analytics(user_id: str) -> dict:
    """获取投资组合分析数据"""
    
    # 从数据库获取持仓
    positions = await db.get_user_positions(user_id)
    
    # 计算分析指标
    risk_service = EnhancedRiskService()
    
    # VaR计算
    var_result = await risk_service.calculate_historical_var(positions)
    
    # 组合统计
    total_value = sum(pos.market_value for pos in positions)
    largest_position = max(positions, key=lambda p: p.market_value)
    
    return {
        "user_id": user_id,
        "total_value": float(total_value),
        "var_95": float(var_result.var_value),
        "largest_position": {
            "symbol": largest_position.symbol,
            "value": float(largest_position.market_value),
            "ratio": float(largest_position.market_value / total_value)
        },
        "calculated_at": datetime.now().isoformat()
    }

# 使用缓存的分析数据
user_analytics = await get_portfolio_analytics("user_123")
print(f"用户投资组合价值: {user_analytics['total_value']}")
```

## 📊 监控和诊断

### 1. 系统健康检查
```python
async def system_health_check():
    """系统健康检查"""
    
    health_status = {
        "timestamp": datetime.now().isoformat(),
        "services": {}
    }
    
    # 检查缓存系统
    try:
        cache = await get_cache()
        cache_stats = await cache.get_stats()
        health_status["services"]["cache"] = {
            "status": "healthy",
            "hit_rate": cache_stats["total_stats"]["hit_rate"],
            "enabled_levels": cache_stats["enabled_levels"]
        }
    except Exception as e:
        health_status["services"]["cache"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    # 检查消息队列
    try:
        message_service = await get_message_service()
        msg_stats = await message_service.get_stats()
        health_status["services"]["messaging"] = {
            "status": "healthy",
            "is_running": msg_stats["is_running"],
            "topics": len(msg_stats["topics"])
        }
    except Exception as e:
        health_status["services"]["messaging"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    # 检查风险管理
    try:
        risk_service = EnhancedRiskService()
        risk_summary = await risk_service.get_enhanced_risk_summary()
        health_status["services"]["risk_management"] = {
            "status": "healthy",
            "monitoring_enabled": risk_summary["monitoring_enabled"],
            "active_rules": risk_summary["active_monitoring_rules"]
        }
    except Exception as e:
        health_status["services"]["risk_management"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    return health_status
```

### 2. 性能指标监控
```python
async def collect_performance_metrics():
    """收集性能指标"""
    
    metrics = {
        "timestamp": datetime.now().isoformat(),
        "cache_metrics": {},
        "messaging_metrics": {},
        "risk_metrics": {}
    }
    
    # 缓存指标
    cache = await get_cache()
    cache_stats = await cache.get_stats()
    
    metrics["cache_metrics"] = {
        "l1_hit_rate": cache_stats["l1_stats"]["hit_rate"],
        "l2_hit_rate": cache_stats["l2_stats"]["hit_rate"],
        "l3_hit_rate": cache_stats["l3_stats"]["hit_rate"],
        "total_hit_rate": cache_stats["total_stats"]["hit_rate"],
        "l1_size_mb": cache_stats["l1_stats"]["size"] / (1024 * 1024),
        "l3_size_mb": cache_stats["l3_stats"]["size"] / (1024 * 1024)
    }
    
    # 消息队列指标
    message_service = await get_message_service()
    msg_stats = await message_service.get_stats()
    
    metrics["messaging_metrics"] = {
        "messages_sent": msg_stats["producer_stats"]["messages_sent"],
        "messages_failed": msg_stats["producer_stats"]["messages_failed"],
        "bytes_sent_mb": msg_stats["producer_stats"]["bytes_sent"] / (1024 * 1024),
        "active_topics": len(msg_stats["topics"])
    }
    
    # 风险管理指标
    risk_service = EnhancedRiskService()
    risk_summary = await risk_service.get_enhanced_risk_summary()
    
    if risk_summary.get("latest_risk_metrics"):
        latest_metrics = risk_summary["latest_risk_metrics"]
        metrics["risk_metrics"] = {
            "var_95": latest_metrics["var_95"],
            "max_drawdown": latest_metrics["max_drawdown"],
            "concentration_risk": latest_metrics["concentration_risk"],
            "liquidity_risk": latest_metrics["liquidity_risk"]
        }
    
    return metrics
```

## 🚀 部署和配置

### 1. 环境配置
```bash
# Redis配置
REDIS_URL=redis://localhost:6379
REDIS_DB=0
REDIS_KEY_PREFIX=redfire:

# Kafka配置
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_CLIENT_ID_PREFIX=redfire
KAFKA_COMPRESSION_TYPE=gzip

# 缓存配置
CACHE_L1_MAX_SIZE=1000
CACHE_L1_MAX_MEMORY_MB=100
CACHE_L2_TTL_SECONDS=3600
CACHE_L3_DIR=/var/cache/redfire
CACHE_L3_MAX_FILES=10000

# 风险管理配置
RISK_VAR_CONFIDENCE_LEVEL=0.95
RISK_MAX_VAR_RATIO=0.05
RISK_MAX_POSITION_RATIO=0.20
RISK_MONITORING_FREQUENCY=60
```

### 2. 服务启动脚本
```python
async def start_risk_infrastructure():
    """启动风险管理和基础设施服务"""
    
    print("启动RedFire风险管理和基础设施服务...")
    
    # 1. 初始化缓存系统
    print("初始化多级缓存系统...")
    cache = await get_cache()
    print("✓ 缓存系统启动成功")
    
    # 2. 启动消息队列
    print("启动Kafka消息队列...")
    message_service = await get_message_service()
    print("✓ 消息队列启动成功")
    
    # 3. 初始化风险管理
    print("初始化风险管理服务...")
    risk_service = EnhancedRiskService()
    await risk_service.create_default_scenarios()
    print("✓ 风险管理服务启动成功")
    
    # 4. 运行健康检查
    print("运行系统健康检查...")
    health = await system_health_check()
    
    unhealthy_services = [
        name for name, status in health["services"].items() 
        if status["status"] == "unhealthy"
    ]
    
    if unhealthy_services:
        print(f"⚠ 警告: 以下服务状态异常: {unhealthy_services}")
    else:
        print("✓ 所有服务健康检查通过")
    
    print("RedFire风险管理和基础设施服务启动完成!")
    return {
        "cache": cache,
        "messaging": message_service,
        "risk_management": risk_service
    }

# 启动服务
if __name__ == "__main__":
    import asyncio
    services = asyncio.run(start_risk_infrastructure())
```

## 📝 总结

本指南展示了RedFire交易系统中完善的风险管理和基础设施模块：

### 风险管理特性
- ✅ **三种VaR计算方法**: 历史模拟、参数、蒙特卡洛
- ✅ **压力测试系统**: 市场情景分析和历史回测
- ✅ **实时监控**: 自定义规则和全面风险指标
- ✅ **自动控制**: 订单预检查和风险限额控制

### 基础设施特性
- ✅ **多级缓存**: L1内存、L2 Redis、L3持久化
- ✅ **消息队列**: Kafka生产者/消费者和主题管理
- ✅ **高性能**: 异步处理和并发优化
- ✅ **可扩展**: 模块化设计和配置化管理

### 生产就绪
- ✅ **错误处理**: 完整的异常处理和降级策略
- ✅ **监控告警**: 健康检查和性能指标
- ✅ **测试覆盖**: 完整的单元测试和集成测试
- ✅ **文档完整**: 详细的使用指南和示例代码

这套完整的风险管理和基础设施系统为RedFire交易平台提供了企业级的可靠性、性能和安全性保障。
