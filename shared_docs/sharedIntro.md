# Shared 模块介绍

## 🎯 概述

`shared` 是 RedFire 量化交易平台的共享资源模块，提供跨模块使用的公共组件、工具函数、类型定义和配置。该模块确保代码复用、一致性维护和模块间的解耦。

## 📁 目录结构

```
shared/
└── monitoring/               # 📊 监控组件
```

## 📊 监控组件 (`monitoring/`)

### **作用**: 提供统一的监控和可观测性功能

### **主要功能**:
- 性能监控
- 健康检查
- 指标收集
- 告警管理

### **组件特性**:
- 跨模块复用
- 统一监控接口
- 可配置的监控策略
- 实时数据收集

## 🔧 共享功能

### **1. 通用工具函数**

```python
# shared/utils/
class CommonUtils:
    @staticmethod
    def format_currency(amount, currency="CNY"):
        """格式化货币"""
        return f"{amount:,.2f} {currency}"
    
    @staticmethod
    def format_percentage(value, decimals=2):
        """格式化百分比"""
        return f"{value:.{decimals}%}"
    
    @staticmethod
    def validate_email(email):
        """验证邮箱格式"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def generate_uuid():
        """生成UUID"""
        import uuid
        return str(uuid.uuid4())
```

### **2. 类型定义**

```python
# shared/types/
from typing import TypedDict, Optional, List, Dict, Any
from datetime import datetime

class User(TypedDict):
    id: str
    username: str
    email: str
    created_at: datetime
    updated_at: datetime

class Order(TypedDict):
    id: str
    symbol: str
    direction: str
    quantity: int
    price: Optional[float]
    status: str
    created_at: datetime

class Position(TypedDict):
    symbol: str
    quantity: int
    average_price: float
    current_price: float
    unrealized_pnl: float
    realized_pnl: float

class MarketData(TypedDict):
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    amount: float
```

### **3. 常量定义**

```python
# shared/constants/
class TradingConstants:
    # 订单类型
    ORDER_TYPE_MARKET = "MARKET"
    ORDER_TYPE_LIMIT = "LIMIT"
    ORDER_TYPE_STOP = "STOP"
    
    # 订单方向
    DIRECTION_BUY = "BUY"
    DIRECTION_SELL = "SELL"
    
    # 订单状态
    STATUS_PENDING = "PENDING"
    STATUS_PARTIAL = "PARTIAL"
    STATUS_FILLED = "FILLED"
    STATUS_CANCELLED = "CANCELLED"
    STATUS_REJECTED = "REJECTED"
    
    # 交易时间
    MARKET_OPEN = "09:30:00"
    MARKET_CLOSE = "15:00:00"
    
    # 风险限制
    MAX_ORDER_SIZE = 1000000
    MAX_POSITION_SIZE = 5000000
    MIN_ORDER_SIZE = 100

class SystemConstants:
    # 系统配置
    DEFAULT_PAGE_SIZE = 20
    MAX_PAGE_SIZE = 1000
    
    # 缓存配置
    CACHE_TTL = 300  # 5分钟
    CACHE_MAX_SIZE = 10000
    
    # 日志配置
    LOG_LEVEL = "INFO"
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
```

### **4. 配置管理**

```python
# shared/config/
import os
from typing import Dict, Any

class SharedConfig:
    def __init__(self):
        self.config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """加载配置"""
        return {
            "database": {
                "url": os.getenv("DATABASE_URL", "sqlite:///redfire.db"),
                "pool_size": int(os.getenv("DB_POOL_SIZE", "10")),
                "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "20"))
            },
            "redis": {
                "url": os.getenv("REDIS_URL", "redis://localhost:6379"),
                "pool_size": int(os.getenv("REDIS_POOL_SIZE", "10"))
            },
            "api": {
                "host": os.getenv("API_HOST", "0.0.0.0"),
                "port": int(os.getenv("API_PORT", "8000")),
                "debug": os.getenv("DEBUG", "false").lower() == "true"
            },
            "security": {
                "secret_key": os.getenv("SECRET_KEY", "your-secret-key"),
                "jwt_expire_hours": int(os.getenv("JWT_EXPIRE_HOURS", "24"))
            }
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any):
        """设置配置值"""
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
```

### **5. 错误处理**

```python
# shared/exceptions/
class RedFireException(Exception):
    """RedFire基础异常类"""
    
    def __init__(self, message: str, error_code: str = None, details: Dict = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)

class ValidationError(RedFireException):
    """验证错误"""
    pass

class AuthenticationError(RedFireException):
    """认证错误"""
    pass

class AuthorizationError(RedFireException):
    """授权错误"""
    pass

class DatabaseError(RedFireException):
    """数据库错误"""
    pass

class TradingError(RedFireException):
    """交易错误"""
    pass

class ConfigurationError(RedFireException):
    """配置错误"""
    pass
```

### **6. 响应格式**

```python
# shared/responses/
from typing import Any, Dict, Optional
from datetime import datetime

class ResponseFormatter:
    @staticmethod
    def success(data: Any = None, message: str = "操作成功") -> Dict[str, Any]:
        """成功响应格式"""
        return {
            "success": True,
            "message": message,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
    
    @staticmethod
    def error(message: str, error_code: str = None, details: Dict = None) -> Dict[str, Any]:
        """错误响应格式"""
        return {
            "success": False,
            "message": message,
            "error_code": error_code,
            "details": details or {},
            "timestamp": datetime.now().isoformat()
        }
    
    @staticmethod
    def paginated(data: list, total: int, page: int, page_size: int) -> Dict[str, Any]:
        """分页响应格式"""
        return {
            "success": True,
            "data": data,
            "pagination": {
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size
            },
            "timestamp": datetime.now().isoformat()
        }
```

### **7. 缓存管理**

```python
# shared/cache/
import asyncio
from typing import Any, Optional
import json

class CacheManager:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.default_ttl = 300  # 5分钟
    
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        try:
            value = await self.redis.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            print(f"Cache get error: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """设置缓存值"""
        try:
            ttl = ttl or self.default_ttl
            serialized_value = json.dumps(value)
            await self.redis.setex(key, ttl, serialized_value)
            return True
        except Exception as e:
            print(f"Cache set error: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """删除缓存值"""
        try:
            await self.redis.delete(key)
            return True
        except Exception as e:
            print(f"Cache delete error: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """检查缓存是否存在"""
        try:
            return await self.redis.exists(key) > 0
        except Exception as e:
            print(f"Cache exists error: {e}")
            return False
    
    async def clear_pattern(self, pattern: str) -> int:
        """清除匹配模式的缓存"""
        try:
            keys = await self.redis.keys(pattern)
            if keys:
                return await self.redis.delete(*keys)
            return 0
        except Exception as e:
            print(f"Cache clear pattern error: {e}")
            return 0
```

### **8. 日志管理**

```python
# shared/logging/
import logging
import json
from datetime import datetime
from typing import Dict, Any

class SharedLogger:
    def __init__(self, name: str, level: str = "INFO"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper()))
        self.setup_handlers()
    
    def setup_handlers(self):
        """设置日志处理器"""
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(self.get_formatter())
        self.logger.addHandler(console_handler)
        
        # 文件处理器
        file_handler = logging.FileHandler(f"logs/shared_{datetime.now().strftime('%Y%m%d')}.log")
        file_handler.setFormatter(self.get_formatter())
        self.logger.addHandler(file_handler)
    
    def get_formatter(self):
        """获取日志格式器"""
        return logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def info(self, message: str, extra: Dict[str, Any] = None):
        """信息日志"""
        self._log(logging.INFO, message, extra)
    
    def warning(self, message: str, extra: Dict[str, Any] = None):
        """警告日志"""
        self._log(logging.WARNING, message, extra)
    
    def error(self, message: str, extra: Dict[str, Any] = None):
        """错误日志"""
        self._log(logging.ERROR, message, extra)
    
    def debug(self, message: str, extra: Dict[str, Any] = None):
        """调试日志"""
        self._log(logging.DEBUG, message, extra)
    
    def _log(self, level: int, message: str, extra: Dict[str, Any] = None):
        """内部日志方法"""
        if extra:
            log_data = {
                "message": message,
                "extra": extra,
                "timestamp": datetime.now().isoformat()
            }
            self.logger.log(level, json.dumps(log_data))
        else:
            self.logger.log(level, message)
```

## 🔄 模块集成

### **1. 导入方式**

```python
# 在其他模块中使用共享组件
from shared.utils import CommonUtils
from shared.types import User, Order, Position
from shared.constants import TradingConstants
from shared.config import SharedConfig
from shared.exceptions import RedFireException
from shared.responses import ResponseFormatter
from shared.cache import CacheManager
from shared.logging import SharedLogger

# 使用示例
config = SharedConfig()
cache = CacheManager(config.get('redis.client'))
logger = SharedLogger('my_module')

# 使用工具函数
formatted_amount = CommonUtils.format_currency(1000000)
user_id = CommonUtils.generate_uuid()

# 使用类型定义
user: User = {
    "id": user_id,
    "username": "test_user",
    "email": "test@example.com",
    "created_at": datetime.now(),
    "updated_at": datetime.now()
}

# 使用响应格式
response = ResponseFormatter.success(data=user, message="用户创建成功")
```

### **2. 版本管理**

```python
# shared/version.py
__version__ = "1.0.0"

class VersionInfo:
    def __init__(self):
        self.version = __version__
        self.build_date = "2024-01-01"
        self.commit_hash = "abc123"
    
    def to_dict(self):
        return {
            "version": self.version,
            "build_date": self.build_date,
            "commit_hash": self.commit_hash
        }
```

## 📊 监控集成

### **1. 性能监控**

```python
# shared/monitoring/performance.py
import time
import functools
from typing import Callable, Any

class PerformanceMonitor:
    def __init__(self, logger):
        self.logger = logger
    
    def monitor(self, func_name: str = None):
        """性能监控装饰器"""
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs) -> Any:
                start_time = time.time()
                try:
                    result = await func(*args, **kwargs)
                    execution_time = time.time() - start_time
                    self.logger.info(
                        f"Function {func_name or func.__name__} executed successfully",
                        {"execution_time": execution_time}
                    )
                    return result
                except Exception as e:
                    execution_time = time.time() - start_time
                    self.logger.error(
                        f"Function {func_name or func.__name__} failed",
                        {"execution_time": execution_time, "error": str(e)}
                    )
                    raise
            
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs) -> Any:
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    execution_time = time.time() - start_time
                    self.logger.info(
                        f"Function {func_name or func.__name__} executed successfully",
                        {"execution_time": execution_time}
                    )
                    return result
                except Exception as e:
                    execution_time = time.time() - start_time
                    self.logger.error(
                        f"Function {func_name or func.__name__} failed",
                        {"execution_time": execution_time, "error": str(e)}
                    )
                    raise
            
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper
        
        return decorator
```

### **2. 健康检查**

```python
# shared/monitoring/health.py
from typing import Dict, Any
import asyncio

class HealthChecker:
    def __init__(self, config, cache, logger):
        self.config = config
        self.cache = cache
        self.logger = logger
    
    async def check_database(self) -> Dict[str, Any]:
        """检查数据库健康状态"""
        try:
            # 执行简单查询
            start_time = time.time()
            # await self.db.execute("SELECT 1")
            execution_time = time.time() - start_time
            
            return {
                "status": "healthy",
                "response_time": execution_time,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def check_redis(self) -> Dict[str, Any]:
        """检查Redis健康状态"""
        try:
            start_time = time.time()
            await self.cache.set("health_check", "ok", 10)
            await self.cache.get("health_check")
            execution_time = time.time() - start_time
            
            return {
                "status": "healthy",
                "response_time": execution_time,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def check_all(self) -> Dict[str, Any]:
        """检查所有组件健康状态"""
        checks = {
            "database": await self.check_database(),
            "redis": await self.check_redis(),
            "timestamp": datetime.now().isoformat()
        }
        
        # 确定整体状态
        all_healthy = all(check["status"] == "healthy" for check in checks.values() if isinstance(check, dict))
        checks["overall_status"] = "healthy" if all_healthy else "unhealthy"
        
        return checks
```

---

**总结**: Shared模块提供了跨模块使用的公共组件和工具，包括工具函数、类型定义、常量、配置管理、错误处理、响应格式、缓存管理和日志管理等。通过统一的接口和标准化的实现，确保代码复用、一致性维护和模块间的解耦，提高开发效率和代码质量。
