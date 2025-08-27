# RedFire 后端项目结构规范

## 📁 目录结构总览

```
backend/
├── 📂 core/                       # 核心引擎模块
│   ├── alpha-engine/              # Alpha算法引擎
│   ├── chart-engine/              # 图表引擎  
│   ├── tradingEngine/             # 交易引擎
│   └── vnpy-engine/               # VnPy集成引擎
├── 📂 legacy/                     # 主要业务代码 (Clean Architecture)
│   ├── application/               # 应用层
│   ├── core/                      # 核心基础设施
│   ├── domain/                    # 领域层
│   ├── infrastructure/            # 基础设施层
│   ├── interfaces/                # 接口层
│   ├── persistence/               # 持久化层
│   └── main.py                    # 主应用入口
├── 📂 infrastructure/             # 基础设施组件
├── 📂 shared/                     # 共享组件
├── 📂 tests/                      # 测试代码
├── 📂 tools/                      # 工具脚本
├── 📂 data/                       # 数据目录
├── 📂 logs/                       # 日志目录
├── 📂 uploads/                    # 上传文件
├── 📂 vnpy_config/                # VnPy配置
├── 📂 vnpy_data/                  # VnPy数据
├── 📄 requirements.txt            # Python依赖
├── 📄 pyproject.toml             # 项目配置
└── 📄 Dockerfile                 # Docker配置
```

## 🏗️ Clean Architecture 分层架构

### 1. 领域层 (Domain Layer) - `legacy/domain/`

领域层是系统的核心，包含业务规则和领域逻辑。

```
domain/
├── user/                          # 用户域
│   ├── entities/                  # 实体
│   │   └── user.py               # 用户实体
│   ├── value_objects/            # 值对象
│   │   ├── user_id.py           # 用户ID
│   │   ├── username.py          # 用户名
│   │   └── email.py             # 邮箱
│   ├── services/                 # 领域服务
│   │   └── user_domain_service.py
│   └── repositories/             # 仓储接口
│       └── user_repository.py
├── trading/                       # 交易域
│   ├── entities/                  # 交易实体
│   │   ├── order_entity.py       # 订单
│   │   ├── trade_entity.py       # 成交
│   │   ├── position_entity.py    # 持仓
│   │   ├── account_entity.py     # 账户
│   │   └── contract_entity.py    # 合约
│   ├── enums.py                  # 交易枚举
│   ├── constants.py              # 交易常量
│   └── services/                 # 交易服务
├── strategy/                      # 策略域
│   ├── entities/
│   ├── services/
│   └── repositories/
├── monitoring/                    # 监控域
│   ├── entities/
│   ├── services/
│   └── events/
├── data/                         # 数据域
│   └── services/
└── shared/                       # 共享组件
    ├── events/                   # 领域事件
    │   └── domain_event.py
    └── value_objects/            # 共享值对象
```

### 2. 应用层 (Application Layer) - `legacy/application/`

应用层协调领域对象执行用例，不包含业务规则。

```
application/
├── services/                      # 应用服务
│   ├── user_application_service.py
│   ├── trading_application_service.py
│   └── strategy_application_service.py
├── commands/                      # 命令 (CQRS)
│   ├── base_command.py
│   ├── command_bus.py
│   └── user_commands.py
├── queries/                       # 查询 (CQRS)
│   ├── base_query.py
│   ├── query_bus.py
│   └── user_queries.py
├── handlers/                      # 处理器
│   ├── command_handlers.py
│   └── query_handlers.py
├── workflows/                     # 工作流
├── dtos/                         # 数据传输对象
└── configuration.py              # 应用配置
```

### 3. 基础设施层 (Infrastructure Layer) - `legacy/infrastructure/`

基础设施层提供技术实现，支持其他层的运行。

```
infrastructure/
├── repositories/                  # 仓储实现
│   ├── user_repository_impl.py
│   └── trading_repository_impl.py
├── data/                         # 数据访问
│   ├── database.py
│   └── migrations/
├── messaging/                    # 消息队列
│   └── kafka_service.py
├── cache/                        # 缓存
│   └── multi_level_cache.py
├── monitoring/                   # 监控
│   ├── metrics.py
│   └── health_checks.py
├── vnpy/                        # VnPy集成
│   └── vnpy_integration_manager.py
└── di/                          # 依赖注入
    └── container.py
```

### 4. 接口层 (Interface Layer) - `legacy/interfaces/`

接口层处理外部交互，如REST API、WebSocket等。

```
interfaces/
├── rest/                         # REST API
│   ├── controllers/              # 控制器
│   │   ├── user_controller.py
│   │   ├── trading_controller.py
│   │   ├── dashboard_controller.py
│   │   └── strategy_engine_controller.py
│   ├── middleware/               # 中间件
│   │   ├── auth_middleware.py
│   │   └── error_middleware.py
│   ├── models/                   # API模型
│   │   ├── common.py
│   │   ├── user_models.py
│   │   └── trading_models.py
│   └── app.py                   # FastAPI应用
└── websocket/                   # WebSocket
    ├── handlers/
    └── events.py
```

### 5. 持久化层 (Persistence Layer) - `legacy/persistence/`

持久化层处理数据的存储和检索。

```
persistence/
├── models/                       # ORM模型
│   ├── base.py
│   ├── user_model.py
│   └── trading_model.py
└── repositories/                 # 仓储实现
    ├── user_repository.py
    └── trading_repository.py
```

## 🎯 核心引擎模块 - `core/`

### 1. 交易引擎 (`core/tradingEngine/`)

```
tradingEngine/
├── mainEngine.py                 # 主交易引擎
├── eventEngine.py                # 事件引擎
├── baseEngine.py                 # 基础引擎
├── engineManager.py              # 引擎管理器
├── apps/                         # 交易应用
│   ├── dataManager.py           # 数据管理
│   ├── riskManager.py           # 风险管理
│   └── strategyManager.py       # 策略管理
├── engines/                      # 具体引擎
│   ├── ctpEngine.py            # CTP接口
│   ├── ibEngine.py             # IB接口
│   └── okexEngine.py           # OKEx接口
└── gateways/                    # 网关接口
    ├── baseGateway.py
    └── simGateway.py
```

### 2. 图表引擎 (`core/chart-engine/`)

```
chart-engine/
├── src/                         # 源代码
│   ├── data_processors/         # 数据处理器
│   ├── renderers/              # 渲染器
│   └── utils/                  # 工具类
├── templates/                  # 图表模板
└── tests/                      # 测试
```

### 3. Alpha引擎 (`core/alpha-engine/`)

```
alpha-engine/
├── src/                        # 源代码
│   ├── research/              # 研究模块
│   ├── data/                  # 数据模块
│   └── utils/                 # 工具模块
├── research_templates/        # 研究模板
└── notebooks/                # Jupyter笔记本
```

### 4. VnPy引擎 (`core/vnpy-engine/`)

```
vnpy-engine/
├── config/                    # 配置文件
│   ├── backend/              # 后端配置
│   ├── vnpy/                 # VnPy配置
│   └── config.env           # 环境配置
├── src/                      # 源代码
│   ├── trader/              # 交易模块
│   ├── data/                # 数据模块
│   └── utils/               # 工具模块
├── examples/                 # 示例代码
└── tests/                   # 测试
```

## 🔧 基础设施组件 - `infrastructure/`

```
infrastructure/
├── cache/                       # 缓存服务
│   ├── config/
│   └── src/
│       ├── redis/
│       ├── memcached/
│       └── strategies/
├── database/                    # 数据库服务
│   ├── config/
│   ├── scripts/
│   └── src/
├── message-queue/              # 消息队列
│   ├── config/
│   └── src/
├── security/                   # 安全服务
│   ├── config/
│   └── src/
└── storage/                    # 存储服务
    ├── config/
    └── src/
```

## 📚 共享组件 - `shared/`

```
shared/
├── common/                     # 通用组件
│   ├── src/
│   └── tests/
├── middleware/                 # 中间件
│   ├── src/
│   └── tests/
├── models/                     # 共享模型
│   ├── src/
│   ├── migrations/
│   └── tests/
└── utils/                      # 工具类
    ├── src/
    └── tests/
```

## 🧪 测试结构 - `tests/`

```
tests/
├── unit/                       # 单元测试
│   ├── application/
│   └── domain/
├── integration/                # 集成测试
│   └── test_complete_integration.py
├── performance/                # 性能测试
│   └── test_performance.py
└── vnpy_integration/          # VnPy集成测试
    └── test_vnpy_integration.py
```

## 🚀 应用启动流程

### 主入口文件: `legacy/main.py`

```python
# 1. 配置加载
config_manager = ConfigManager()
config = await config_manager.load_from_environment()

# 2. 依赖注入容器初始化
container = DependencyContainer()

# 3. 服务注册
await register_services(container)

# 4. FastAPI应用创建
app = VnPyWebAPI()

# 5. 应用启动
uvicorn.run(app.get_app(), host="0.0.0.0", port=8000)
```

## 📋 开发规范

### 1. 命名规范

- **文件名**: 小写字母 + 下划线 (snake_case)
- **类名**: 大驼峰命名 (PascalCase)
- **方法名**: 小驼峰命名 (camelCase)
- **常量**: 全大写 + 下划线

### 2. 目录规范

- 每个模块都应有 `__init__.py` 文件
- 测试文件以 `test_` 前缀命名
- 配置文件统一放在 `config/` 目录

### 3. 导入规范

```python
# 标准库导入
import os
import sys

# 第三方库导入
from fastapi import FastAPI
from sqlalchemy import create_engine

# 本地导入
from .domain.user.entities import User
from ..application.services import UserApplicationService
```

### 4. 文档规范

- 每个模块都应有详细的文档字符串
- 公共API都应有类型注解
- 重要的业务逻辑应有注释说明

## 🔄 持续改进

这个项目结构是一个活文档，会根据项目发展不断更新和完善。

---

**文档版本**: v1.0
**更新时间**: 2025-08-26
**维护者**: RedFire 开发团队
