# 🔧 RedFire外部配置管理服务

## 📋 概述

RedFire配置管理服务是一个基于外部微服务架构的配置管理系统，完全舍弃了复杂的DDD架构，采用简单直接的三层架构设计。

### ✨ 核心特性

- **🎯 简单架构**: 舍弃DDD复杂性，采用 API → Service → Repository 三层架构
- **📄 多源配置**: 支持文件、环境变量、字典等多种配置源
- **🔄 热重载**: 实时监听配置文件变更，自动重新加载
- **🛡️ 类型安全**: 基于Pydantic的类型安全配置模型
- **⚡ 高性能**: FastAPI + 异步I/O，支持高并发
- **🔍 配置验证**: 自动配置验证和错误提示
- **💾 智能缓存**: 多级缓存提升配置访问性能
- **📊 REST API**: 完整的RESTful API支持CRUD操作
- **🔔 事件通知**: 配置变更实时通知机制

### 🏗️ 架构设计

```
┌─────────────────────────────────────────┐
│            外部微服务架构                │
├─────────────────────────────────────────┤
│  🌐 REST API 层                        │
│  ├── 配置CRUD接口                       │
│  ├── 健康检查接口                       │
│  └── 配置验证接口                       │
├─────────────────────────────────────────┤
│  🔧 服务层 (Core)                      │
│  ├── 配置管理器                         │
│  ├── 文件监听器                         │
│  ├── 缓存管理器                         │
│  └── 事件通知器                         │
├─────────────────────────────────────────┤
│  📦 模型层 (Models)                     │
│  ├── Pydantic配置模型                   │
│  ├── 配置验证器                         │
│  └── 类型定义                           │
└─────────────────────────────────────────┘
```

## 🚀 快速开始

### 1. 安装依赖

```bash
cd backend/config_service
pip install -r requirements.txt
```

### 2. 配置环境

复制并编辑配置文件：

```bash
cp config/development.yaml config/production.yaml
# 编辑 config/production.yaml 设置生产环境配置
```

### 3. 启动服务

#### 方式一：使用启动脚本（推荐）

```bash
# 使用默认配置启动
python start_service.py

# 使用指定配置文件启动
python start_service.py --config config/production.yaml

# 启用热重载（开发环境）
python start_service.py --reload

# 自定义主机和端口
python start_service.py --host 127.0.0.1 --port 8080
```

#### 方式二：使用CLI命令

```bash
# 运行服务
python -m backend.config_service.main run

# 使用指定配置
python -m backend.config_service.main run --config-file config/production.yaml

# 验证配置文件
python -m backend.config_service.main validate --config-file config/development.yaml

# 生成配置模板
python -m backend.config_service.main template --output my_config.yaml

# 查看配置信息
python -m backend.config_service.main info

# 健康检查
python -m backend.config_service.main health
```

#### 方式三：程序调用

```python
import asyncio
from backend.config_service import quick_start

# 快速启动
asyncio.run(quick_start("config/development.yaml"))
```

### 4. 访问服务

- **服务地址**: http://localhost:8001
- **API文档**: http://localhost:8001/docs
- **ReDoc文档**: http://localhost:8001/redoc
- **健康检查**: http://localhost:8001/health

## 📖 使用指南

### 配置模型

配置服务支持多种配置类型：

```python
from backend.config_service import (
    AppConfig, DatabaseConfig, RedisConfig, 
    VnPyConfig, SecurityConfig, MonitoringConfig
)

# 主配置
config = AppConfig(
    app_name="My App",
    environment="production",
    database=DatabaseConfig(
        engine="postgresql",
        host="localhost",
        port=5432,
        database="mydb"
    ),
    redis=RedisConfig(
        host="localhost",
        port=6379
    )
)
```

### 配置文件格式

支持YAML和JSON格式：

```yaml
# config.yaml
app_name: "RedFire Config Service"
environment: "development"
debug: true

database:
  engine: "postgresql"
  host: "localhost"
  port: 5432
  database: "redfire"
  username: "user"
  password: "pass"

redis:
  host: "localhost"
  port: 6379
  db: 0

security:
  secret_key: "your-secret-key"
  algorithm: "HS256"
```

### 环境变量

支持通过环境变量配置：

```bash
# 应用配置
export APP_NAME="My Service"
export APP_ENVIRONMENT="production"
export APP_DEBUG=false

# 数据库配置（使用双下划线表示嵌套）
export DB__HOST="prod-db.example.com"
export DB__PORT=5432
export DB__DATABASE="myapp"
export DB__USERNAME="dbuser"
export DB__PASSWORD="dbpass"

# Redis配置
export REDIS__HOST="redis.example.com"
export REDIS__PORT=6379
```

### 编程方式使用

#### 初始化配置

```python
from backend.config_service import initialize_config, get_config

# 从文件初始化
config = await initialize_config("config.yaml")

# 从环境变量初始化
config = await initialize_config()

# 从字典初始化
config_dict = {"app_name": "Test", "debug": True}
config = await initialize_config(config_dict=config_dict)
```

#### 获取配置

```python
from backend.config_service import (
    get_config, get_database_config, get_redis_config
)

# 获取完整配置
config = get_config()
print(f"App: {config.app_name} v{config.app_version}")

# 获取特定配置
db_config = get_database_config()
redis_config = get_redis_config()

# 获取嵌套配置
from backend.config_service.core.config_manager import config_manager
db_host = config_manager.get_nested_config("database.host")
```

#### 配置热重载

```python
from backend.config_service import reload_config

# 手动重新加载配置
success = await reload_config()

# 注册配置变更回调
def on_config_change(new_config):
    print(f"配置已更新: {new_config.app_name}")

config_manager.add_change_callback(on_config_change)
```

## 🔌 API接口

### 认证

所有API接口需要Bearer Token认证：

```bash
curl -H "Authorization: Bearer your-token" http://localhost:8001/config
```

### 主要接口

#### 获取配置

```bash
# 获取完整配置
GET /config

# 获取特定路径配置
GET /config?key_path=database.host

# 包含敏感信息
GET /config?include_sensitive=true
```

#### 更新配置

```bash
# 更新配置
PUT /config
{
    "updates": {
        "debug": true,
        "database": {
            "pool_size": 50
        }
    }
}

# 试运行模式
PUT /config
{
    "updates": {...},
    "dry_run": true
}
```

#### 重新加载配置

```bash
POST /config/reload
```

#### 获取特定配置

```bash
GET /config/database    # 数据库配置
GET /config/redis       # Redis配置
GET /config/vnpy        # VnPy配置
GET /config/security    # 安全配置
```

#### 健康检查

```bash
GET /health
```

#### 配置信息

```bash
GET /config/info
```

### 响应格式

```json
{
    "success": true,
    "message": "配置获取成功",
    "data": {
        "app_name": "RedFire Config Service",
        "environment": "development"
    },
    "timestamp": "2024-01-01T00:00:00"
}
```

## 🛠️ 开发指南

### 项目结构

```
backend/config_service/
├── __init__.py              # 包初始化
├── main.py                  # 服务启动入口
├── start_service.py         # 快速启动脚本
├── requirements.txt         # 依赖列表
├── README.md               # 文档
├── models/                 # 配置模型
│   ├── __init__.py
│   └── config_models.py    # Pydantic模型
├── core/                   # 核心服务
│   ├── __init__.py
│   └── config_manager.py   # 配置管理器
├── api/                    # API接口
│   ├── __init__.py
│   └── config_api.py       # REST API
└── config/                 # 配置文件
    └── development.yaml    # 开发环境配置
```

### 添加新配置类型

1. 在 `config_models.py` 中定义新的配置模型：

```python
class MyServiceConfig(BaseSettings):
    """我的服务配置"""
    host: str = Field("localhost", description="服务主机")
    port: int = Field(8080, description="服务端口")
    
    class Config:
        env_prefix = "MY_SERVICE_"
```

2. 在主配置中添加新配置：

```python
class AppConfig(BaseSettings):
    # ... 其他配置
    my_service: MyServiceConfig = Field(default_factory=MyServiceConfig)
```

3. 在配置管理器中添加便捷方法：

```python
def get_my_service_config():
    """获取我的服务配置"""
    return config_manager.get_config().my_service
```

### 自定义验证器

```python
from pydantic import validator

class MyConfig(BaseSettings):
    port: int
    
    @validator('port')
    def validate_port(cls, v):
        if not 1 <= v <= 65535:
            raise ValueError('端口必须在1-65535之间')
        return v
```

### 配置变更监听

```python
def on_config_change(new_config: AppConfig):
    # 处理配置变更
    print(f"配置已更新: {new_config.app_name}")
    
    # 重新初始化服务组件
    reinitialize_services(new_config)

config_manager.add_change_callback(on_config_change)
```

## 🧪 测试

### 运行测试

```bash
# 安装测试依赖
pip install pytest pytest-asyncio pytest-cov

# 运行所有测试
pytest

# 运行覆盖率测试
pytest --cov=backend.config_service

# 运行特定测试
pytest tests/test_config_models.py
```

### 测试示例

```python
import pytest
from backend.config_service import initialize_config, get_config

@pytest.mark.asyncio
async def test_config_loading():
    """测试配置加载"""
    config = await initialize_config("tests/fixtures/test_config.yaml")
    assert config.app_name == "Test App"
    assert config.environment == "testing"

@pytest.mark.asyncio
async def test_config_validation():
    """测试配置验证"""
    invalid_config = {"database": {"port": 70000}}  # 无效端口
    
    with pytest.raises(ValueError):
        await initialize_config(config_dict=invalid_config)
```

## 🔧 部署

### Docker部署

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY backend/config_service/ ./
RUN pip install -r requirements.txt

EXPOSE 8001
CMD ["python", "main.py", "run"]
```

### 环境变量配置

```bash
# .env
APP_NAME=RedFire Config Service
APP_ENVIRONMENT=production
APP_DEBUG=false
APP_HOST=0.0.0.0
APP_PORT=8001

DB__ENGINE=postgresql
DB__HOST=postgres.example.com
DB__PORT=5432
DB__DATABASE=redfire
DB__USERNAME=dbuser
DB__PASSWORD=dbpass

SECURITY__SECRET_KEY=your-production-secret-key
```

### 健康检查

```bash
# Docker健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8001/health || exit 1
```

## 📊 监控

### Prometheus指标

配置服务自动暴露Prometheus指标：

- `config_requests_total`: 配置请求总数
- `config_reload_total`: 配置重载次数
- `config_validation_errors_total`: 配置验证错误数
- `config_cache_hits_total`: 配置缓存命中数

### 日志记录

```python
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 查看配置服务日志
logger = logging.getLogger('backend.config_service')
```

## ❓ 常见问题

### Q: 如何处理敏感配置信息？

A: 使用 `SecretStr` 类型和环境变量：

```python
from pydantic import SecretStr

class SecurityConfig(BaseSettings):
    secret_key: SecretStr = Field(..., env="SECRET_KEY")
    
    def get_secret_value(self):
        return self.secret_key.get_secret_value()
```

### Q: 配置热重载不工作？

A: 检查以下项目：
1. 文件监听是否启用：`enable_file_watching=True`
2. 配置文件路径是否正确
3. 文件权限是否正确
4. 是否有文件锁定

### Q: 如何自定义配置验证？

A: 使用Pydantic验证器：

```python
@validator('database_url')
def validate_database_url(cls, v):
    if not v.startswith(('postgresql://', 'mysql://')):
        raise ValueError('不支持的数据库URL格式')
    return v
```

### Q: 如何处理配置升级？

A: 实现配置迁移函数：

```python
def migrate_config_v1_to_v2(old_config: dict) -> dict:
    """配置版本升级"""
    new_config = old_config.copy()
    # 执行升级逻辑
    return new_config
```

## 📚 更多资源

- [Pydantic文档](https://docs.pydantic.dev/)
- [FastAPI文档](https://fastapi.tiangolo.com/)
- [配置最佳实践](https://12factor.net/config)

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📄 许可证

MIT License
