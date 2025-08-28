# 配置加载器迁移指南

## 🚀 概述

本文档指导如何从现有的配置管理器迁移到新的**共享配置加载器 (SharedConfigLoader)**，该加载器符合外部微服务架构标准。

## 🎯 迁移目标

### ✅ 已解决的问题
- **命名冲突**: `UnifiedConfigLoader` → `SharedConfigLoader`
- **标准化路径**: 统一使用 `config/{service}/{environment}/{name}.yaml`
- **环境变量**: 统一前缀 `REDFIRE_{SERVICE}_{CONFIG}_`
- **外部服务**: 集成配置微服务API

### 📊 迁移前后对比

| 方面 | 迁移前 | 迁移后 |
|------|--------|--------|
| **类名** | `UnifiedConfigLoader` | `SharedConfigLoader` |
| **配置路径** | 多种不统一路径 | `config/{service}/{env}/{name}.yaml` |
| **环境变量** | `APP_*`, `CONFIG_*` | `REDFIRE_{SERVICE}_{CONFIG}_*` |
| **服务URL** | `CONFIG_SERVICE_URL` | `REDFIRE_CONFIG_SERVICE_URL` |
| **API路径** | `/config/{name}` | `/config/{service}/{name}` |

## 📋 迁移步骤

### Step 1: 更新导入语句

**迁移前:**
```python
from backend.shared.config import UnifiedConfigLoader
```

**迁移后:**
```python
from backend.shared.config import SharedConfigLoader
```

### Step 2: 更新实例化代码

**迁移前:**
```python
loader = UnifiedConfigLoader()
```

**迁移后:**
```python
loader = SharedConfigLoader()
# 或使用全局实例
loader = get_config_loader()
```

### Step 3: 更新配置文件路径

**迁移前:**
```
config/app.yaml
backend/config/database.yaml
backend/config_service/config/vnpy.yaml
```

**迁移后:**
```
config/user/development/config.yaml
config/trading/development/vnpy.yaml  
config/shared/development/database.yaml
```

**目录结构:**
```
config/
├── user/
│   ├── development/
│   │   ├── config.yaml
│   │   └── database.yaml
│   └── production/
│       ├── config.yaml
│       └── database.yaml
├── trading/
│   ├── development/
│   │   ├── config.yaml
│   │   ├── vnpy.yaml
│   │   └── risk.yaml
│   └── production/
│       ├── config.yaml
│       ├── vnpy.yaml
│       └── risk.yaml
└── shared/
    ├── development/
    │   ├── database.yaml
    │   ├── redis.yaml
    │   └── logging.yaml
    └── production/
        ├── database.yaml
        ├── redis.yaml
        └── logging.yaml
```

### Step 4: 更新环境变量

**迁移前:**
```bash
export APP_DEBUG=true
export CONFIG_SERVICE_URL=http://localhost:8001
export VNPY_DATA_PATH=/data/vnpy
```

**迁移后:**
```bash
export REDFIRE_ENVIRONMENT=development
export REDFIRE_CONFIG_SERVICE_URL=http://localhost:8001
export REDFIRE_USER_DEBUG=true
export REDFIRE_TRADING_VNPY_DATA_PATH=/data/vnpy
export REDFIRE_SHARED_DB_HOST=localhost
```

### Step 5: 更新配置加载调用

**迁移前:**
```python
# 基本加载
config = await loader.load_config('app')

# 带参数加载
config = await loader.load_config('database', 
                                 sources=[ConfigSource.FILE, ConfigSource.ENV])
```

**迁移后:**
```python
# 指定服务加载
config = await loader.load_config('config', service='user')

# 加载特定服务配置
app_config = await loader.load_config('config', service='trading')
vnpy_config = await loader.load_config('vnpy', service='trading')

# 验证配置标准
validation = loader.validate_config('config', config.data, service='user')
```

### Step 6: 使用配置模板生成

**新功能:**
```python
# 生成标准配置模板
template = loader.generate_config_template('trading', 'development')

# 输出标准配置模板到文件
import yaml
config_path = 'config/trading/development/config.yaml'
with open(config_path, 'w') as f:
    yaml.dump(template, f, default_flow_style=False)
```

## 🔧 服务特定迁移

### 用户服务 (User Service)

**配置文件:** `config/user/development/config.yaml`
```yaml
app:
  name: user_service
  version: 1.0.0
  environment: development
  port: 8010

config_service:
  url: ${REDFIRE_CONFIG_SERVICE_URL:http://localhost:8001}
  token: ${REDFIRE_CONFIG_SERVICE_TOKEN}
  enabled: true

database:
  host: ${REDFIRE_USER_DB_HOST:localhost}
  port: ${REDFIRE_USER_DB_PORT:5432}
  name: ${REDFIRE_USER_DB_NAME:user_db}
```

**环境变量:**
```bash
REDFIRE_USER_DB_HOST=localhost
REDFIRE_USER_DB_PORT=5432
REDFIRE_USER_DB_NAME=user_db
REDFIRE_USER_DEBUG=true
```

**代码调用:**
```python
# 加载用户服务配置
config = await loader.load_config('config', service='user')
db_config = config['database']
```

### 交易服务 (Trading Service)

**配置文件:** `config/trading/development/config.yaml`
```yaml
app:
  name: trading_service
  version: 1.0.0
  environment: development
  port: 8020

vnpy:
  config_path: config/vnpy/development/config.yaml
  data_path: ${REDFIRE_TRADING_VNPY_DATA_PATH:/data/vnpy}
  log_path: logs/vnpy

risk:
  max_position: ${REDFIRE_TRADING_RISK_MAX_POSITION:1000000}
  max_daily_loss: ${REDFIRE_TRADING_RISK_MAX_LOSS:50000}
```

**代码调用:**
```python
# 加载交易服务配置
trading_config = await loader.load_config('config', service='trading')
vnpy_config = await loader.load_config('vnpy', service='trading')
risk_config = await loader.load_config('risk', service='trading')
```

### 策略服务 (Strategy Service)

**配置文件:** `config/strategy/development/config.yaml`
```yaml
app:
  name: strategy_service
  version: 1.0.0
  environment: development
  port: 8030

strategy:
  strategy_path: ${REDFIRE_STRATEGY_PATH:strategies}
  backtest_data_path: ${REDFIRE_STRATEGY_BACKTEST_PATH:data/backtest}
  live_trading: ${REDFIRE_STRATEGY_LIVE_TRADING:false}
```

## 🔄 渐进式迁移策略

### Phase 1: 并行运行 (1周)
1. 保持现有配置管理器不变
2. 新代码使用SharedConfigLoader
3. 建立配置文件的新目录结构
4. 设置新的环境变量

### Phase 2: 兼容适配 (2周)
1. 使用LegacyConfigAdapter提供向后兼容
2. 逐步迁移核心配置到新格式
3. 更新环境变量和配置路径
4. 测试新旧系统兼容性

### Phase 3: 完全切换 (2周)
1. 所有新功能使用SharedConfigLoader
2. Legacy系统通过适配器调用
3. 验证所有配置符合新标准
4. 移除冗余的配置文件

### Phase 4: 清理优化 (1周)
1. 移除不再使用的配置管理器
2. 清理重复的配置文件
3. 优化配置加载性能
4. 完善监控和告警

## 🧪 测试验证

### 单元测试迁移

**迁移前:**
```python
def test_unified_loader():
    loader = UnifiedConfigLoader()
    # 测试代码...
```

**迁移后:**
```python
def test_shared_loader():
    loader = SharedConfigLoader()
    # 测试代码...
    
def test_config_validation():
    loader = SharedConfigLoader()
    config_data = {"app": {"name": "test_service"}}
    validation = loader.validate_config('config', config_data, service='test')
    assert validation['compliant'] == True
```

### 集成测试

```python
@pytest.mark.asyncio
async def test_service_config_loading():
    """测试服务配置加载"""
    loader = get_config_loader()
    
    async with loader:
        # 测试用户服务配置
        user_config = await loader.load_config('config', service='user')
        assert user_config['app']['name'] == 'user_service'
        
        # 测试交易服务配置
        trading_config = await loader.load_config('config', service='trading')
        assert 'vnpy' in trading_config
        
        # 测试配置验证
        validation = loader.validate_config('config', user_config, service='user')
        assert validation['compliant'] == True
```

## 🚨 常见问题和解决方案

### Q1: 配置文件找不到
**问题**: `ConfigLoadResult(success=False, error="配置文件不存在")`

**解决**: 
1. 检查配置文件路径是否符合新标准
2. 确认环境变量 `REDFIRE_ENVIRONMENT` 设置正确
3. 使用配置模板生成器创建标准配置

```python
# 生成配置模板
loader = SharedConfigLoader()
template = loader.generate_config_template('user', 'development')
```

### Q2: 环境变量不生效
**问题**: 环境变量值没有被正确读取

**解决**:
1. 检查环境变量前缀是否正确: `REDFIRE_{SERVICE}_{CONFIG}_`
2. 确认环境变量在配置文件中正确引用: `${REDFIRE_USER_DB_HOST:localhost}`

### Q3: 配置服务连接失败
**问题**: `ConfigLoadResult(success=False, error="配置服务连接失败")`

**解决**:
1. 检查 `REDFIRE_CONFIG_SERVICE_URL` 环境变量
2. 确认配置服务正在运行
3. 验证认证令牌 `REDFIRE_CONFIG_SERVICE_TOKEN`

### Q4: 类型导入错误
**问题**: `ImportError: cannot import name 'UnifiedConfigLoader'`

**解决**:
```python
# 错误的导入
from backend.shared.config import UnifiedConfigLoader

# 正确的导入  
from backend.shared.config import SharedConfigLoader
```

## 📚 参考资源

### 相关文档
- [外部微服务架构设计文档](../../../ZZZ/5外部微服务架构设计文档.md)
- [配置管理使用指南](../README.md)
- [配置加载器代码审查报告](../../../ZReView/配置加载器代码审查报告.md)

### 配置标准
- [外部服务配置标准](external_service_standards.py)
- [配置模板生成器](config_loader.py#generate_config_template)
- [配置验证工具](config_loader.py#validate_config)

### 示例代码
- [集成示例](integration_examples.py)
- [单元测试](test_config_loader.py)

---

**迁移支持**: 如遇到问题，请参考配置加载器文档或联系开发团队。
