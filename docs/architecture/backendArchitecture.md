# ⚙️ RedFire后端架构设计

## 📋 概述

RedFire后端采用DDD（领域驱动设计）架构，基于Python FastAPI框架构建，支持异步处理、事件驱动和微服务架构。

## 🏗️ 架构层次

### 1. 接口层 (Interface Layer)
- **REST API**: FastAPI实现的RESTful接口
- **WebSocket**: 实时数据推送服务
- **GraphQL**: 灵活的数据查询接口
- **gRPC**: 高性能的内部服务通信

### 2. 应用层 (Application Layer)
- **交易应用**: 交易逻辑和业务流程
- **数据应用**: 数据管理和处理
- **策略应用**: 量化策略执行
- **风险应用**: 风险监控和控制

### 3. 领域层 (Domain Layer)
- **交易领域**: 订单、持仓、成交等核心业务
- **策略领域**: 策略定义、回测、执行
- **风险领域**: 风险计算、限额控制
- **数据领域**: 市场数据、历史数据

### 4. 基础设施层 (Infrastructure Layer)
- **数据访问**: 数据库操作和缓存
- **消息队列**: 异步任务处理
- **外部接口**: 第三方服务集成
- **监控日志**: 系统监控和日志记录

## 🔧 核心组件

### 主交易引擎 (Main Trading Engine)
```python
class MainTradingEngine:
    """主交易引擎 - 系统核心控制器"""
    
    def __init__(self):
        self.event_engine = EventEngine()
        self.engine_manager = EngineManager()
        self.plugin_manager = PluginManager()
        self.risk_manager = RiskManager()
    
    async def start(self):
        """启动交易引擎"""
        await self.event_engine.start()
        await self.engine_manager.start()
        await self.plugin_manager.load_plugins()
    
    async def stop(self):
        """停止交易引擎"""
        await self.event_engine.stop()
        await self.engine_manager.stop()
```

### 事件引擎 (Event Engine)
```python
class EventEngine:
    """事件引擎 - 事件驱动架构核心"""
    
    def __init__(self):
        self._queue = asyncio.Queue()
        self._active = False
        self._handlers = defaultdict(list)
        self._thread = None
    
    async def start(self):
        """启动事件引擎"""
        self._active = True
        self._thread = asyncio.create_task(self._run())
    
    async def _run(self):
        """事件循环"""
        while self._active:
            try:
                event = await self._queue.get()
                await self._process(event)
            except Exception as e:
                logger.error(f"事件处理错误: {e}")
```

### 引擎管理器 (Engine Manager)
```python
class EngineManager:
    """引擎管理器 - 管理各种交易引擎"""
    
    def __init__(self):
        self.engines = {}
        self.engine_configs = {}
    
    async def add_engine(self, engine_name: str, engine_class: type):
        """添加交易引擎"""
        engine = engine_class()
        await engine.init()
        self.engines[engine_name] = engine
    
    async def remove_engine(self, engine_name: str):
        """移除交易引擎"""
        if engine_name in self.engines:
            await self.engines[engine_name].close()
            del self.engines[engine_name]
```

## 🔌 插件系统

### 插件接口
```python
class PluginInterface(ABC):
    """插件接口基类"""
    
    @abstractmethod
    async def init(self):
        """初始化插件"""
        pass
    
    @abstractmethod
    async def start(self):
        """启动插件"""
        pass
    
    @abstractmethod
    async def stop(self):
        """停止插件"""
        pass
    
    @abstractmethod
    async def close(self):
        """关闭插件"""
        pass
```

### 插件管理器
```python
class PluginManager:
    """插件管理器 - 管理所有插件"""
    
    def __init__(self):
        self.plugins = {}
        self.plugin_configs = {}
    
    async def load_plugin(self, plugin_path: str):
        """加载插件"""
        try:
            module = importlib.import_module(plugin_path)
            plugin_class = getattr(module, 'Plugin')
            plugin = plugin_class()
            await plugin.init()
            self.plugins[plugin.__class__.__name__] = plugin
        except Exception as e:
            logger.error(f"插件加载失败: {e}")
    
    async def start_plugin(self, plugin_name: str):
        """启动插件"""
        if plugin_name in self.plugins:
            await self.plugins[plugin_name].start()
```

## 🗄️ 数据访问层

### 数据库连接池
```python
class DatabaseManager:
    """数据库管理器 - 管理数据库连接"""
    
    def __init__(self):
        self.postgres_pool = None
        self.redis_pool = None
        self.influx_client = None
        self.mongo_client = None
    
    async def init_postgres(self, config: dict):
        """初始化PostgreSQL连接池"""
        self.postgres_pool = await asyncpg.create_pool(
            host=config['host'],
            port=config['port'],
            user=config['user'],
            password=config['password'],
            database=config['database'],
            min_size=config.get('min_size', 5),
            max_size=config.get('max_size', 20)
        )
    
    async def init_redis(self, config: dict):
        """初始化Redis连接池"""
        self.redis_pool = aioredis.from_url(
            f"redis://{config['host']}:{config['port']}",
            password=config.get('password'),
            db=config.get('db', 0),
            max_connections=config.get('max_connections', 20)
        )
```

### 仓储模式
```python
class BaseRepository(ABC):
    """仓储基类"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    @abstractmethod
    async def create(self, entity):
        """创建实体"""
        pass
    
    @abstractmethod
    async def read(self, entity_id):
        """读取实体"""
        pass
    
    @abstractmethod
    async def update(self, entity):
        """更新实体"""
        pass
    
    @abstractmethod
    async def delete(self, entity_id):
        """删除实体"""
        pass

class OrderRepository(BaseRepository):
    """订单仓储"""
    
    async def create(self, order: Order):
        """创建订单"""
        query = """
            INSERT INTO orders (symbol, direction, volume, price, order_type, status)
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING id
        """
        result = await self.db.postgres_pool.fetchval(
            query, order.symbol, order.direction, order.volume,
            order.price, order.order_type, order.status
        )
        order.id = result
        return order
```

## 📡 消息队列

### 任务队列
```python
class TaskQueue:
    """任务队列 - 异步任务处理"""
    
    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self.celery_app = None
    
    def init_celery(self):
        """初始化Celery"""
        self.celery_app = Celery(
            'redfire',
            broker=self.redis_url,
            backend=self.redis_url
        )
        
        # 配置任务路由
        self.celery_app.conf.task_routes = {
            'redfire.tasks.data.*': {'queue': 'data'},
            'redfire.tasks.trading.*': {'queue': 'trading'},
            'redfire.tasks.risk.*': {'queue': 'risk'},
        }
    
    def submit_task(self, task_name: str, *args, **kwargs):
        """提交任务"""
        return self.celery_app.send_task(task_name, args=args, kwargs=kwargs)
```

## 🔐 安全机制

### 认证授权
```python
class SecurityManager:
    """安全管理器"""
    
    def __init__(self):
        self.jwt_secret = os.getenv('JWT_SECRET')
        self.jwt_algorithm = 'HS256'
        self.jwt_expire_minutes = 30
    
    def create_access_token(self, data: dict):
        """创建访问令牌"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=self.jwt_expire_minutes)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.jwt_secret, algorithm=self.jwt_algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str):
        """验证令牌"""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
            return payload
        except JWTError:
            return None
```

## 📊 监控日志

### 日志配置
```python
class LogManager:
    """日志管理器"""
    
    def __init__(self):
        self.logger = logging.getLogger('redfire')
        self.setup_logging()
    
    def setup_logging(self):
        """配置日志"""
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # 文件处理器
        file_handler = logging.FileHandler('logs/redfire.log')
        file_handler.setLevel(logging.DEBUG)
        
        # 格式化器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)
        
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)
        self.logger.setLevel(logging.DEBUG)
```

### 性能监控
```python
class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self):
        self.metrics = {}
        self.start_time = time.time()
    
    def record_metric(self, name: str, value: float):
        """记录指标"""
        if name not in self.metrics:
            self.metrics[name] = []
        self.metrics[name].append({
            'timestamp': time.time(),
            'value': value
        })
    
    def get_average(self, name: str, window: int = 100):
        """获取平均值"""
        if name not in self.metrics:
            return 0
        values = self.metrics[name][-window:]
        return sum(v['value'] for v in values) / len(values)
```

## 🚀 部署配置

### Docker配置
```dockerfile
# Dockerfile
FROM python:3.9-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .
RUN pip install -r requirements.txt

# 复制应用代码
COPY . .

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 环境配置
```python
# config.py
class Settings(BaseSettings):
    """应用配置"""
    
    # 数据库配置
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "redfire"
    POSTGRES_PASSWORD: str = "password"
    POSTGRES_DATABASE: str = "redfire"
    
    # Redis配置
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""
    REDIS_DB: int = 0
    
    # JWT配置
    JWT_SECRET: str = "your-secret-key"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 30
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/redfire.log"
    
    class Config:
        env_file = ".env"
```

## 📈 性能优化

### 异步处理
- 使用asyncio实现异步I/O
- 数据库连接池管理
- 异步任务队列

### 缓存策略
- Redis缓存热点数据
- 数据库查询结果缓存
- 策略计算结果缓存

### 数据库优化
- 索引优化
- 查询语句优化
- 分表分库策略

---

*RedFire后端架构设计 - 构建高性能、可扩展的交易系统后端* 🔥
