# Config 模块介绍

## 🎯 概述

`config` 是 RedFire 量化交易平台的配置管理模块，负责管理整个系统的配置信息，包括环境配置、网关配置、安全配置、部署配置等。该模块采用分层配置管理，支持多环境部署和动态配置更新。

## 📁 目录结构

```
config/
├── config.env                 # 🔧 主环境配置文件
├── config.env.template        # 📝 环境配置模板
├── vt_setting.json            # ⚙️ VnPy交易设置
├── domestic_gateways_example.yaml  # 🚪 国内网关配置示例
├── secrets/                   # 🔐 密钥管理
├── templates/                 # 📋 配置模板
├── environments/              # 🌍 环境配置
├── frontend/                  # 🎨 前端配置
├── nginx/                     # 🌐 Nginx配置
└── backend/                   # 🔧 后端配置
```

## 🔧 核心配置文件

### 1. **主环境配置** (`config.env`)

**作用**: 系统核心环境变量配置

**主要配置项**:
```bash
# 数据库配置
DATABASE_URL=postgresql://user:pass@localhost/redfire
REDIS_URL=redis://localhost:6379

# 应用配置
APP_ENV=production
DEBUG=false
SECRET_KEY=your-secret-key

# 服务配置
API_HOST=0.0.0.0
API_PORT=8000
FRONTEND_URL=http://localhost:3000

# 交易配置
TRADING_ENABLED=true
RISK_LIMIT=1000000
MAX_ORDERS_PER_MINUTE=100

# 日志配置
LOG_LEVEL=INFO
LOG_FILE_PATH=logs/app.log

# 监控配置
MONITORING_ENABLED=true
METRICS_PORT=9090
```

### 2. **VnPy交易设置** (`vt_setting.json`)

**作用**: VnPy交易引擎配置

**配置内容**:
```json
{
  "database.name": "sqlite",
  "database.database": "database.db",
  "database.host": "localhost",
  "database.port": 3306,
  "database.username": "vnpy",
  "database.password": "vnpy",
  "database.authentication_source": "admin",
  "log.level": "INFO",
  "log.file": "logs/vt.log"
}
```

### 3. **国内网关配置** (`domestic_gateways_example.yaml`)

**作用**: 国内交易所网关配置示例

**配置结构**:
```yaml
# 华鑫奇点
huaxin:
  gateway_name: "HuaxinGateway"
  gateway_display_name: "华鑫奇点"
  gateway_type: "STOCK"
  gateway_color: "FF0000"
  gateway_sort: 1
  gateway_setting: {
    "用户名": "",
    "密码": "",
    "交易服务器": "",
    "行情服务器": "",
    "产品名称": "",
    "授权编码": ""
  }

# 中泰XTP
zhongtai:
  gateway_name: "ZhongtaiGateway"
  gateway_display_name: "中泰XTP"
  gateway_type: "STOCK"
  gateway_color: "FF0000"
  gateway_sort: 2
  gateway_setting: {
    "账号": "",
    "密码": "",
    "客户端ID": "",
    "行情服务器": "",
    "交易服务器": ""
  }
```

## 🗂️ 子目录详解

### 1. **密钥管理** (`secrets/`)

**作用**: 敏感信息和安全密钥管理

**内容**:
- API密钥
- 数据库密码
- 加密密钥
- 证书文件
- 私钥文件

**安全特性**:
- 加密存储
- 访问控制
- 密钥轮换
- 审计日志

### 2. **配置模板** (`templates/`)

**作用**: 各种配置文件的模板

**模板类型**:
- 应用配置模板
- 数据库配置模板
- 服务配置模板
- 部署配置模板

**使用方式**:
```bash
# 复制模板并自定义
cp templates/app.config.template app.config
# 编辑配置文件
vim app.config
```

### 3. **环境配置** (`environments/`)

**作用**: 不同环境的配置管理

**环境类型**:
- `development/` - 开发环境
- `testing/` - 测试环境
- `staging/` - 预发布环境
- `production/` - 生产环境

**配置差异**:
```yaml
# 开发环境
development:
  debug: true
  log_level: DEBUG
  database_url: "sqlite:///dev.db"

# 生产环境
production:
  debug: false
  log_level: WARNING
  database_url: "postgresql://prod:pass@prod-db/redfire"
```

### 4. **前端配置** (`frontend/`)

**作用**: 前端应用配置

**配置内容**:
- API端点配置
- 环境变量
- 构建配置
- 部署配置

**示例**:
```javascript
// frontend/config.js
export const config = {
  apiBaseUrl: process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000',
  wsUrl: process.env.REACT_APP_WS_URL || 'ws://localhost:8000/ws',
  environment: process.env.NODE_ENV || 'development'
};
```

### 5. **Nginx配置** (`nginx/`)

**作用**: Web服务器配置

**配置文件**:
- `nginx.conf` - 主配置文件
- `ssl.conf` - SSL证书配置
- `proxy.conf` - 代理配置
- `gzip.conf` - 压缩配置

**功能特性**:
- 负载均衡
- 反向代理
- SSL终止
- 静态文件服务
- 缓存配置

### 6. **后端配置** (`backend/`)

**作用**: 后端服务专用配置

**配置内容**:
- 服务配置
- 数据库配置
- 缓存配置
- 消息队列配置
- 监控配置

## 🔄 配置管理策略

### **分层配置**

1. **默认配置** (最低优先级)
   - 系统默认值
   - 基础配置项

2. **环境配置** (中等优先级)
   - 环境特定配置
   - 部署环境差异

3. **用户配置** (最高优先级)
   - 用户自定义配置
   - 运行时配置

### **配置验证**

```python
from pydantic import BaseSettings, validator

class AppConfig(BaseSettings):
    database_url: str
    redis_url: str
    secret_key: str
    
    @validator('database_url')
    def validate_database_url(cls, v):
        if not v.startswith(('postgresql://', 'mysql://', 'sqlite://')):
            raise ValueError('Invalid database URL format')
        return v
    
    class Config:
        env_file = ".env"
```

### **动态配置**

```python
class ConfigManager:
    def __init__(self):
        self._config = {}
        self._watchers = []
    
    async def update_config(self, key: str, value: Any):
        """动态更新配置"""
        self._config[key] = value
        await self._notify_watchers(key, value)
    
    async def get_config(self, key: str, default: Any = None):
        """获取配置值"""
        return self._config.get(key, default)
```

## 🛡️ 安全配置

### **密钥管理**

```bash
# 使用环境变量
export SECRET_KEY="your-secret-key"
export DATABASE_PASSWORD="your-db-password"

# 使用密钥文件
echo "your-secret-key" > config/secrets/secret_key.txt
chmod 600 config/secrets/secret_key.txt
```

### **访问控制**

```yaml
# 配置访问权限
permissions:
  config_read:
    roles: ["admin", "developer"]
  config_write:
    roles: ["admin"]
  secrets_access:
    roles: ["admin"]
```

### **配置加密**

```python
from cryptography.fernet import Fernet

class EncryptedConfig:
    def __init__(self, key: bytes):
        self.cipher = Fernet(key)
    
    def encrypt_value(self, value: str) -> str:
        return self.cipher.encrypt(value.encode()).decode()
    
    def decrypt_value(self, encrypted_value: str) -> str:
        return self.cipher.decrypt(encrypted_value.encode()).decode()
```

## 🔧 配置工具

### **配置验证工具**

```python
def validate_config():
    """验证配置完整性"""
    required_configs = [
        'DATABASE_URL',
        'SECRET_KEY',
        'REDIS_URL'
    ]
    
    missing_configs = []
    for config in required_configs:
        if not os.getenv(config):
            missing_configs.append(config)
    
    if missing_configs:
        raise ValueError(f"Missing required configs: {missing_configs}")
```

### **配置生成工具**

```python
def generate_config_template():
    """生成配置模板"""
    template = {
        "database": {
            "url": "postgresql://user:pass@localhost/db",
            "pool_size": 10,
            "max_overflow": 20
        },
        "redis": {
            "url": "redis://localhost:6379",
            "pool_size": 10
        },
        "app": {
            "debug": False,
            "secret_key": "your-secret-key",
            "host": "0.0.0.0",
            "port": 8000
        }
    }
    
    with open('config.template.yaml', 'w') as f:
        yaml.dump(template, f, default_flow_style=False)
```

## 📊 配置监控

### **配置变更监控**

```python
class ConfigMonitor:
    def __init__(self, config_file: str):
        self.config_file = config_file
        self.last_modified = os.path.getmtime(config_file)
    
    def check_changes(self) -> bool:
        """检查配置是否变更"""
        current_modified = os.path.getmtime(self.config_file)
        if current_modified > self.last_modified:
            self.last_modified = current_modified
            return True
        return False
    
    async def watch_config(self):
        """监控配置变更"""
        while True:
            if self.check_changes():
                await self.reload_config()
            await asyncio.sleep(5)
```

### **配置健康检查**

```python
async def check_config_health():
    """检查配置健康状态"""
    health_status = {
        "database": await check_database_config(),
        "redis": await check_redis_config(),
        "api": await check_api_config(),
        "security": await check_security_config()
    }
    
    return health_status
```

## 🚀 部署配置

### **Docker配置**

```dockerfile
# Dockerfile
FROM python:3.9-slim

# 复制配置文件
COPY config/ /app/config/
COPY config.env /app/

# 设置环境变量
ENV CONFIG_PATH=/app/config

# 启动应用
CMD ["python", "main.py"]
```

### **Kubernetes配置**

```yaml
# configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: redfire-config
data:
  config.yaml: |
    database:
      url: "postgresql://user:pass@db-service/redfire"
    redis:
      url: "redis://redis-service:6379"
    app:
      debug: false
      secret_key: "your-secret-key"
```

## 📚 最佳实践

### **1. 配置分离**
- 敏感信息使用环境变量
- 配置文件版本控制
- 不同环境使用不同配置

### **2. 配置验证**
- 启动时验证配置完整性
- 运行时检查配置有效性
- 配置变更时进行测试

### **3. 配置备份**
- 定期备份配置文件
- 配置变更记录
- 回滚机制

### **4. 配置文档**
- 配置项说明文档
- 配置示例
- 故障排除指南

---

**总结**: Config模块是RedFire平台的配置管理中心，采用分层配置管理策略，支持多环境部署和动态配置更新。通过完善的配置验证、安全管理和监控机制，确保系统配置的可靠性和安全性。
