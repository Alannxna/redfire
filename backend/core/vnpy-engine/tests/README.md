# VnPy Web 项目测试计划

## 概述

本测试计划针对VnPy Web项目的整体架构、功能、接口和配置进行全面测试，确保系统的稳定性、可靠性和性能。

## 项目架构分析

### 技术栈
- **后端**: FastAPI + SQLAlchemy + PostgreSQL
- **前端**: Vue.js + Vite
- **架构**: Clean Architecture (DDD)
- **通信**: REST API + WebSocket
- **部署**: Docker + Docker Compose

### 核心模块
1. **领域层 (Domain)**
   - 用户管理 (User)
   - 策略管理 (Strategy) 
   - 交易管理 (Trading)
   - 共享组件 (Shared)

2. **应用层 (Application)**
   - 命令处理 (Commands)
   - 查询处理 (Queries)
   - 应用服务 (Services)
   - 工作流 (Workflows)

3. **基础设施层 (Infrastructure)**
   - 数据库访问
   - 缓存管理
   - 日志系统
   - 监控服务

4. **接口层 (Interfaces)**
   - REST API
   - WebSocket
   - 中间件

## 测试策略

### 测试金字塔
```
    E2E Tests (10%)
   ├─────────────────┤
  Integration Tests (20%)
 ├─────────────────────┤
Unit Tests (70%)
```

### 测试类型分布
- **单元测试**: 70% - 快速反馈，覆盖业务逻辑
- **集成测试**: 20% - 验证模块间协作
- **端到端测试**: 10% - 验证用户场景

## 测试环境配置

### 测试数据库
- 使用独立的测试数据库
- 每个测试用例前后清理数据
- 支持事务回滚

### 模拟服务
- 外部API模拟
- 消息队列模拟
- 文件系统模拟

## 详细测试计划

## 1. 单元测试 (Unit Tests)

### 1.1 领域层测试

#### 用户实体测试 (`test_user_entity.py`)
- ✅ 用户创建和验证
- ✅ 密码哈希和验证
- ✅ 用户状态管理
- ✅ 权限验证
- ✅ 账户锁定逻辑
- ✅ 领域事件触发

#### 值对象测试
- ✅ 用户ID验证 (`test_user_id.py`)
- ✅ 用户名验证 (`test_username.py`) 
- ✅ 邮箱验证 (`test_email.py`)
- ✅ 手机号验证 (`test_phone.py`)

#### 领域服务测试 (`test_domain_services.py`)
- ✅ 用户域服务
- ✅ 策略域服务
- ✅ 交易域服务

### 1.2 应用层测试

#### 命令处理器测试 (`test_command_handlers.py`)
- ✅ 创建用户命令
- ✅ 更新用户命令
- ✅ 删除用户命令
- ✅ 修改密码命令

#### 查询处理器测试 (`test_query_handlers.py`)
- ✅ 用户查询
- ✅ 用户列表查询
- ✅ 分页查询

#### 应用服务测试 (`test_application_services.py`)
- ✅ 用户应用服务
- ✅ 策略应用服务
- ✅ 交易应用服务

### 1.3 基础设施层测试

#### 仓储实现测试 (`test_repositories.py`)
- ✅ 用户仓储
- ✅ 策略仓储
- ✅ 交易仓储
- ✅ 数据库连接和事务

#### 缓存服务测试 (`test_cache_service.py`)
- ✅ Redis连接
- ✅ 缓存CRUD操作
- ✅ 缓存过期策略

#### 日志服务测试 (`test_logging.py`)
- ✅ 日志格式化
- ✅ 日志级别控制
- ✅ 日志文件轮转

## 2. 集成测试 (Integration Tests)

### 2.1 数据库集成测试 (`test_database_integration.py`)
- ✅ 数据库连接池
- ✅ 事务管理
- ✅ 数据一致性
- ✅ 并发访问

### 2.2 API集成测试 (`test_api_integration.py`)
- ✅ 用户管理API
- ✅ 认证和授权
- ✅ 错误处理
- ✅ 中间件链

### 2.3 消息队列集成测试 (`test_messaging_integration.py`)
- ✅ 消息发送和接收
- ✅ 消息持久化
- ✅ 死信队列处理

### 2.4 缓存集成测试 (`test_cache_integration.py`)
- ✅ Redis集群
- ✅ 缓存同步
- ✅ 缓存失效策略

## 3. API接口测试 (API Tests)

### 3.1 REST API测试 (`test_rest_api.py`)

#### 用户管理接口
- ✅ `POST /api/v1/users` - 创建用户
- ✅ `GET /api/v1/users/{id}` - 获取用户信息
- ✅ `PUT /api/v1/users/{id}` - 更新用户信息
- ✅ `DELETE /api/v1/users/{id}` - 删除用户
- ✅ `GET /api/v1/users` - 用户列表（分页）
- ✅ `POST /api/v1/users/login` - 用户登录
- ✅ `POST /api/v1/users/logout` - 用户登出

#### 系统接口
- ✅ `GET /health` - 健康检查
- ✅ `GET /` - 根路径信息

#### 认证测试
- ✅ JWT token生成和验证
- ✅ 权限控制
- ✅ Token过期处理

### 3.2 WebSocket测试 (`test_websocket.py`)
- ✅ 连接建立和断开
- ✅ 消息推送
- ✅ 心跳检测
- ✅ 重连机制

## 4. 端到端测试 (E2E Tests)

### 4.1 用户流程测试 (`test_user_flow.py`)
- ✅ 用户注册流程
- ✅ 用户登录流程  
- ✅ 用户信息管理
- ✅ 密码修改流程

### 4.2 业务流程测试 (`test_business_flow.py`)
- ✅ 策略创建和管理
- ✅ 交易执行流程
- ✅ 数据同步流程

## 5. 性能测试 (Performance Tests)

### 5.1 负载测试 (`test_load.py`)
- ✅ API并发访问
- ✅ 数据库连接池压力
- ✅ 内存使用监控

### 5.2 压力测试 (`test_stress.py`)
- ✅ 极限负载测试
- ✅ 系统恢复能力
- ✅ 资源泄漏检测

## 6. 安全测试 (Security Tests)

### 6.1 认证安全测试 (`test_auth_security.py`)
- ✅ SQL注入防护
- ✅ XSS防护
- ✅ CSRF防护
- ✅ 密码安全策略

### 6.2 API安全测试 (`test_api_security.py`)
- ✅ 权限绕过测试
- ✅ 参数篡改测试
- ✅ 频率限制测试

## 7. 配置测试 (Configuration Tests)

### 7.1 环境配置测试 (`test_config.py`)
- ✅ 开发环境配置
- ✅ 测试环境配置
- ✅ 生产环境配置
- ✅ 配置热更新

### 7.2 Docker配置测试 (`test_docker.py`)
- ✅ 容器启动和停止
- ✅ 服务间通信
- ✅ 数据卷挂载
- ✅ 环境变量传递

## 测试数据管理

### 测试数据策略
- **固定数据**: 基础测试数据
- **随机数据**: 边界条件测试
- **真实数据**: 性能和集成测试

### 数据清理策略
- 测试前准备干净数据
- 测试后清理临时数据
- 使用事务回滚机制

## 测试执行策略

### 本地开发测试
```bash
# 运行所有测试
pytest

# 运行单元测试
pytest tests/unit/

# 运行集成测试
pytest tests/integration/

# 生成覆盖率报告
pytest --cov=src --cov-report=html
```

### CI/CD集成
- 代码提交时自动运行单元测试
- Pull Request时运行完整测试套件
- 部署前运行端到端测试

## 测试覆盖率目标

| 测试类型 | 覆盖率目标 | 当前覆盖率 |
|---------|-----------|-----------|
| 单元测试 | ≥ 80% | 待测量 |
| 集成测试 | ≥ 60% | 待测量 |
| API测试 | ≥ 90% | 待测量 |
| 整体覆盖率 | ≥ 75% | 待测量 |

## 测试工具和框架

### Python测试框架
- **pytest**: 主要测试框架
- **pytest-asyncio**: 异步测试支持
- **pytest-cov**: 覆盖率测试
- **httpx**: HTTP客户端测试
- **websockets**: WebSocket测试

### 模拟和存根
- **pytest-mock**: Mock对象
- **responses**: HTTP响应模拟
- **fakeredis**: Redis模拟

### 数据库测试
- **pytest-postgresql**: PostgreSQL测试数据库
- **alembic**: 数据库迁移测试

## 测试报告

### 报告格式
- HTML覆盖率报告
- JUnit XML格式
- JSON测试结果

### 报告内容
- 测试通过率
- 代码覆盖率
- 性能指标
- 错误详情

## 持续改进

### 测试质量监控
- 定期审查测试用例
- 监控测试执行时间
- 分析测试失败原因

### 测试维护
- 及时更新测试用例
- 重构重复测试代码
- 优化测试执行效率

---

## 快速开始

1. **安装测试依赖**
```bash
pip install -r requirements-test.txt
```

2. **配置测试环境**
```bash
cp config/test.env.template config/test.env
```

3. **运行测试**
```bash
pytest tests/ -v
```

4. **查看覆盖率**
```bash
pytest --cov=src --cov-report=html
open htmlcov/index.html
```

---

*最后更新: 2024-01-XX*
*版本: 1.0.0*