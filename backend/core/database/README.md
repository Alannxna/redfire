# RedFire 统一数据库管理系统

## 🎯 概述

RedFire统一数据库管理系统为量化交易平台提供完整的数据库解决方案，支持多种数据库类型，具备企业级的性能、可靠性和扩展性。

## ✨ 核心特性

### 🔧 多数据库支持
- **MySQL**: 主要业务数据存储，支持读写分离
- **Redis**: 高性能缓存和会话存储
- **InfluxDB**: 时序数据存储（K线、Tick数据等）
- **MongoDB**: 日志和文档存储
- **PostgreSQL**: 备选关系型数据库

### ⚡ 性能优化
- **连接池管理**: 智能连接池配置和监控
- **UTF8MB4字符集**: 完整Unicode支持
- **读写分离**: 自动读写请求路由和负载均衡
- **缓存策略**: 多级缓存和智能失效机制
- **批量操作**: 高效的批量数据处理

### 🛡️ 可靠性保障
- **健康检查**: 自动连接健康监控
- **故障转移**: 自动故障检测和恢复
- **连接重试**: 智能重试和熔断机制
- **事务管理**: 完整的事务支持和回滚

## 🏗️ 架构设计

```
RedFire数据库架构
├── 统一数据库管理器 (UnifiedDatabaseManager)
│   ├── MySQL连接池 (主业务数据)
│   ├── Redis连接池 (缓存)
│   ├── InfluxDB客户端 (时序数据)
│   └── MongoDB客户端 (日志)
│
├── 读写分离管理器 (ReadWriteSplitManager)
│   ├── 主节点 (写操作)
│   ├── 从节点 (读操作)
│   └── 负载均衡器
│
├── 缓存策略管理器 (RedisCacheManager)
│   ├── 多级缓存
│   ├── 失效策略
│   └── 缓存装饰器
│
└── 专用数据管理器
    ├── 交易数据管理器 (TradingDataManager)
    └── 日志管理器 (LogManager)
```

## 🚀 快速开始

### 1. 环境配置

复制并配置数据库环境变量：

```bash
cp backend/core/database/.env.database .env
```

编辑 `.env` 文件，配置您的数据库连接信息：

```env
# 主数据库配置 (基于您的配置)
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=root
DB_NAME=vnpy

# Redis缓存配置
REDIS_HOST=localhost
REDIS_PORT=6379
```

### 2. 数据库初始化

```python
from backend.core.database import initialize_databases

# 初始化所有数据库
success = initialize_databases()
if success:
    print("✅ 数据库初始化成功")
else:
    print("❌ 数据库初始化失败")
```

### 3. 基本使用

```python
from backend.core.database import (
    get_db_session,
    get_cache_manager,
    get_trading_data_manager
)

# MySQL数据库操作
with get_db_session() as session:
    result = session.execute("SELECT * FROM users")
    users = result.fetchall()

# Redis缓存操作
cache = get_cache_manager()
cache.set("user_data", "user_123", {"name": "张三"})
user_data = cache.get("user_data", "user_123")

# 时序数据操作
trading_manager = get_trading_data_manager()
trading_manager.write_kline_data(
    symbol="AAPL",
    timeframe="1m",
    timestamp=datetime.now(),
    open_price=150.00,
    high_price=151.00,
    low_price=149.50,
    close_price=150.75,
    volume=100000
)
```

## 📚 详细使用指南

### MySQL数据库操作

#### 基本CRUD操作

```python
from backend.core.database import get_db_session
from sqlalchemy import text

# 查询操作
with get_db_session() as session:
    # 查询用户
    result = session.execute(text("SELECT * FROM users WHERE id = :id"), {"id": 1})
    user = result.fetchone()
    
    # 统计查询
    result = session.execute(text("SELECT COUNT(*) FROM trading_orders"))
    count = result.scalar()

# 插入操作
with get_db_session() as session:
    session.execute(text("""
        INSERT INTO users (username, email, password_hash) 
        VALUES (:username, :email, :password)
    """), {
        "username": "newuser",
        "email": "newuser@example.com", 
        "password": "hashed_password"
    })
    # 自动提交
```

#### 读写分离

```python
from backend.core.database import get_read_session, get_write_session

# 读操作 - 使用从库
with get_read_session() as session:
    result = session.execute(text("SELECT * FROM users"))
    users = result.fetchall()

# 写操作 - 使用主库
with get_write_session() as session:
    session.execute(text("UPDATE users SET last_login = NOW() WHERE id = :id"), {"id": 1})
```

#### 异步操作

```python
from backend.core.database import get_async_db_session
import asyncio

async def async_database_operations():
    async with get_async_db_session() as session:
        result = await session.execute(text("SELECT * FROM users"))
        users = result.fetchall()
        return users

# 运行异步操作
users = asyncio.run(async_database_operations())
```

### Redis缓存操作

#### 基本缓存操作

```python
from backend.core.database import get_cache_manager

# 获取缓存管理器
cache = get_cache_manager("user_data")  # 使用预定义配置

# 设置缓存
cache.set("user_profile", "user_123", {
    "name": "张三",
    "email": "zhangsan@example.com",
    "preferences": {"theme": "dark"}
}, ttl=3600)  # 1小时过期

# 获取缓存
user_profile = cache.get("user_profile", "user_123")

# 删除缓存
cache.delete("user_profile", "user_123")

# 检查缓存是否存在
exists = cache.exists("user_profile", "user_123")
```

#### 缓存装饰器

```python
from backend.core.database import cache

@cache("api_data", ttl=300)  # 5分钟缓存
def get_market_data(symbol: str):
    """获取市场数据 - 自动缓存结果"""
    # 模拟API调用
    return {
        "symbol": symbol,
        "price": 150.25,
        "timestamp": datetime.now().isoformat()
    }

# 第一次调用会执行函数并缓存结果
data1 = get_market_data("AAPL")

# 第二次调用直接从缓存获取
data2 = get_market_data("AAPL")  # 从缓存获取
```

#### 缓存统计和监控

```python
# 获取缓存统计
stats = cache.get_stats()
print(f"命中率: {stats['hit_rate']}")
print(f"总请求: {stats['total_requests']}")

# 清空命名空间缓存
cache.clear_namespace("user_profile")
```

### InfluxDB时序数据操作

#### 交易数据存储

```python
from backend.core.database import get_trading_data_manager
from datetime import datetime

trading_manager = get_trading_data_manager()

# 写入K线数据
success = trading_manager.write_kline_data(
    symbol="AAPL",
    timeframe="1m",
    timestamp=datetime.now(),
    open_price=150.00,
    high_price=151.00,
    low_price=149.50,
    close_price=150.75,
    volume=100000
)

# 写入Tick数据
success = trading_manager.write_tick_data(
    symbol="AAPL",
    timestamp=datetime.now(),
    last_price=150.75,
    volume=1000,
    bid_price=150.70,
    ask_price=150.80,
    bid_volume=500,
    ask_volume=600
)

# 查询历史K线数据
kline_data = trading_manager.get_kline_data(
    symbol="AAPL",
    timeframe="1m",
    start_time=datetime.now() - timedelta(hours=1),
    end_time=datetime.now()
)

# 获取最新价格
latest_price = trading_manager.get_latest_price("AAPL")
```

#### 自定义时序数据

```python
from backend.core.database import get_influx_manager, TimeSeriesPoint

influx_manager = get_influx_manager()

# 创建自定义数据点
point = TimeSeriesPoint(
    measurement="portfolio_value",
    fields={
        "total_value": 100000.0,
        "cash": 20000.0,
        "positions": 80000.0
    },
    tags={
        "user_id": "user_123",
        "account_type": "live"
    },
    timestamp=datetime.now()
)

# 写入数据点
success = influx_manager.write_point(point)
```

### MongoDB日志操作

#### 结构化日志

```python
from backend.core.database import get_log_manager, LogEntry, LogLevel, LogCategory
import asyncio

async def logging_operations():
    log_manager = get_log_manager()
    
    # 创建日志条目
    log_entry = LogEntry(
        level=LogLevel.INFO,
        category=LogCategory.TRADING,
        message="用户下单操作",
        source="trading_service",
        user_id="user_123",
        data={
            "symbol": "AAPL",
            "quantity": 100,
            "price": 150.00,
            "order_type": "LIMIT"
        },
        tags=["trading", "order", "user_action"]
    )
    
    # 写入日志
    log_id = await log_manager.write_log(log_entry)
    print(f"日志ID: {log_id}")

# 运行异步日志操作
asyncio.run(logging_operations())
```

#### 审计日志

```python
async def audit_logging():
    log_manager = get_log_manager()
    
    # 写入审计日志
    audit_id = await log_manager.write_audit_log(
        user_id="user_123",
        action="CREATE_ORDER",
        resource="trading_orders",
        details={
            "order_id": "order_456",
            "symbol": "AAPL",
            "side": "BUY",
            "quantity": 100
        },
        ip_address="192.168.1.100",
        user_agent="Mozilla/5.0..."
    )
```

#### 日志查询和分析

```python
async def log_analysis():
    log_manager = get_log_manager()
    
    # 查询特定类型的日志
    logs = await log_manager.query_logs(
        category=LogCategory.TRADING,
        level=LogLevel.ERROR,
        start_time=datetime.now() - timedelta(days=1),
        user_id="user_123",
        limit=100
    )
    
    # 获取日志统计
    stats = await log_manager.get_log_statistics(
        start_time=datetime.now() - timedelta(days=7),
        end_time=datetime.now()
    )
    
    print(f"总日志数: {stats['total']}")
    print(f"错误日志数: {stats['by_level'].get('ERROR', 0)}")
```

## 🔧 配置说明

### 数据库连接配置

```env
# MySQL主数据库
DB_HOST=localhost          # 数据库主机
DB_PORT=3306              # 数据库端口
DB_USER=root              # 数据库用户名
DB_PASSWORD=root          # 数据库密码
DB_NAME=vnpy              # 数据库名称

# 连接池优化
DB_POOL_SIZE=15           # 连接池大小
DB_MAX_OVERFLOW=30        # 最大溢出连接数
DB_POOL_TIMEOUT=20        # 连接超时时间(秒)
DB_POOL_RECYCLE=1800      # 连接回收时间(秒)
```

### Redis缓存配置

```env
# Redis连接
REDIS_HOST=localhost      # Redis主机
REDIS_PORT=6379          # Redis端口
REDIS_DB=0               # Redis数据库编号
REDIS_PASSWORD=          # Redis密码(可选)

# 缓存策略
REDIS_DEFAULT_TTL=3600   # 默认过期时间(秒)
REDIS_MAX_CONNECTIONS=20 # 最大连接数
```

### 读写分离配置

```env
# 主数据库(写操作)
DB_MASTER_HOST=localhost
DB_MASTER_PORT=3306
DB_MASTER_USER=root
DB_MASTER_PASSWORD=root

# 从数据库(读操作) - 可选
DB_SLAVE_HOST=slave-host
DB_SLAVE_PORT=3306
DB_SLAVE_USER=readonly
DB_SLAVE_PASSWORD=readonly
```

## 📊 监控和诊断

### 数据库状态监控

```python
from backend.core.database import get_database_manager, get_database_status

# 获取所有数据库统计
db_manager = get_database_manager()
stats = db_manager.get_all_stats()

# 测试所有数据库连接
health_status = db_manager.test_all_connections()

# 获取详细状态信息
status = get_database_status()
print(f"数据库初始化状态: {status}")
```

### 读写分离监控

```python
from backend.core.database import get_rw_split_manager

rw_manager = get_rw_split_manager()
rw_stats = rw_manager.get_all_stats()

print(f"读请求数: {rw_stats['read_queries']}")
print(f"写请求数: {rw_stats['write_queries']}")
print(f"故障转移次数: {rw_stats['failovers']}")
```

### 缓存性能监控

```python
from backend.core.database import get_cache_manager

cache = get_cache_manager()
cache_stats = cache.get_stats()

print(f"缓存命中率: {cache_stats['hit_rate']}")
print(f"缓存错误数: {cache_stats['errors']}")
```

## 🛠️ 最佳实践

### 1. 连接管理

```python
# ✅ 推荐：使用上下文管理器
with get_db_session() as session:
    # 数据库操作
    result = session.execute("SELECT ...")
    # 自动提交和关闭连接

# ❌ 不推荐：手动管理连接
session = get_db_session_direct()
try:
    result = session.execute("SELECT ...")
    session.commit()
finally:
    session.close()  # 容易忘记
```

### 2. 缓存策略

```python
# ✅ 推荐：使用装饰器缓存
@cache("expensive_operation", ttl=3600)
def expensive_calculation(params):
    # 耗时计算
    return result

# ✅ 推荐：合理设置TTL
cache.set("user_session", user_id, session_data, ttl=1800)  # 30分钟
cache.set("market_data", symbol, data, ttl=60)  # 1分钟

# ❌ 不推荐：无限期缓存
cache.set("permanent_data", key, data)  # 可能导致内存泄漏
```

### 3. 错误处理

```python
# ✅ 推荐：完整的错误处理
try:
    with get_write_session() as session:
        session.execute("INSERT INTO ...")
except SQLAlchemyError as e:
    logger.error(f"数据库操作失败: {e}")
    # 记录错误日志
    await log_manager.write_log(LogEntry(
        level=LogLevel.ERROR,
        category=LogCategory.DATABASE,
        message="数据库写入失败",
        exception=str(e)
    ))
    raise
```

### 4. 批量操作

```python
# ✅ 推荐：批量写入时序数据
points = []
for record in large_dataset:
    point = TimeSeriesPoint(...)
    points.append(point)

# 批量写入
influx_manager.write_points(points)

# ❌ 不推荐：逐条写入
for record in large_dataset:
    point = TimeSeriesPoint(...)
    influx_manager.write_point(point)  # 效率低
```

## 🔍 故障排除

### 常见问题

1. **MySQL连接失败**
   ```
   错误: Can't connect to MySQL server
   解决: 检查DB_HOST、DB_PORT、DB_USER、DB_PASSWORD配置
   ```

2. **Redis连接超时**
   ```
   错误: Redis connection timeout
   解决: 检查REDIS_HOST、REDIS_PORT配置，确认Redis服务运行
   ```

3. **InfluxDB写入失败**
   ```
   错误: InfluxDB write failed
   解决: 检查INFLUX_TOKEN、INFLUX_ORG、INFLUX_BUCKET配置
   ```

4. **连接池耗尽**
   ```
   错误: QueuePool limit exceeded
   解决: 增加DB_POOL_SIZE和DB_MAX_OVERFLOW值
   ```

### 调试模式

```python
# 启用SQL日志
import os
os.environ['DB_ECHO'] = 'true'

# 启用Redis调试
os.environ['REDIS_DEBUG'] = 'true'

# 查看详细错误信息
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📈 性能优化建议

### 1. 连接池调优

```env
# 高并发环境
DB_POOL_SIZE=25
DB_MAX_OVERFLOW=50
DB_POOL_TIMEOUT=10

# 低延迟环境
DB_POOL_RECYCLE=900  # 15分钟回收
DB_POOL_TIMEOUT=5    # 快速失败
```

### 2. 缓存优化

```python
# 分层缓存策略
@cache("hot_data", ttl=60)      # 热数据1分钟
@cache("warm_data", ttl=600)    # 温数据10分钟
@cache("cold_data", ttl=3600)   # 冷数据1小时
```

### 3. 读写分离优化

```python
# 读密集型应用
# 配置多个从节点
DB_SLAVE_HOST_1=slave1
DB_SLAVE_HOST_2=slave2
DB_SLAVE_HOST_3=slave3
```

## 🤝 贡献指南

欢迎提交Issue和Pull Request来改进RedFire数据库管理系统。

### 开发环境设置

```bash
# 1. 克隆项目
git clone <repository>

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置数据库
cp backend/core/database/.env.database .env

# 4. 运行测试
python -m pytest backend/core/database/tests/

# 5. 运行示例
python backend/core/database/usage_examples.py
```

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件。

---

**RedFire数据库管理系统** - 为量化交易平台提供企业级数据库解决方案 🚀
