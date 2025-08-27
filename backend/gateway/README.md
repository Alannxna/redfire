# 🚀 RedFire API网关

RedFire量化交易平台的统一API网关，提供微服务架构的统一入口点。

## ✨ 主要特性

### 🔐 统一认证授权
- JWT令牌验证
- 基于角色的权限控制
- 用户上下文传递
- 公开路径配置

### 🚦 智能限流保护
- 多种限流算法支持
- Redis/内存存储选择
- 路径特定限制
- 突发流量处理

### ⚖️ 负载均衡
- 轮询、加权轮询算法
- 最少连接算法
- 健康检查集成
- 熔断器保护

### 🔍 服务发现
- Redis服务注册中心
- 自动健康检查
- 服务元数据管理
- 动态路由更新

### 📊 监控指标
- 请求性能统计
- 服务健康状态
- 错误率监控
- 自定义指标收集

### 🌐 WebSocket支持
- 实时消息传递
- 主题订阅机制
- 跨服务消息路由
- 连接管理

## 🏗️ 架构设计

```
┌─────────────────────────────────────────────────┐
│                API Gateway                       │
├─────────────────────────────────────────────────┤
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ │
│  │    Auth     │ │Rate Limiter │ │Load Balancer│ │
│  │ Middleware  │ │ Middleware  │ │ Middleware  │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ │
├─────────────────────────────────────────────────┤
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ │
│  │   Service   │ │   Metrics   │ │  WebSocket  │ │
│  │  Registry   │ │  Collector  │ │Message Bus  │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ │
└─────────────────────────────────────────────────┘
                       │
          ┌────────────┼────────────┐
          │            │            │
    ┌─────────┐  ┌─────────┐  ┌─────────┐
    │ User    │  │Strategy │  │ VnPy    │
    │Service  │  │Service  │  │Service  │
    │ :8001   │  │ :8002   │  │ :8006   │
    └─────────┘  └─────────┘  └─────────┘
```

## 🚀 快速开始

### 环境要求
- Python 3.11+
- Redis 6.0+
- Docker (可选)

### 本地开发

1. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

2. **配置环境变量**
   ```bash
   cp .env.example .env
   # 编辑 .env 文件，修改相应配置
   ```

3. **启动Redis**
   ```bash
   docker run -d -p 6379:6379 redis:7-alpine
   ```

4. **启动网关**
   ```bash
   python -m gateway.main
   ```

5. **验证运行**
   ```bash
   curl http://localhost:8000/health
   ```

### Docker部署

1. **使用Docker Compose**
   ```bash
   docker-compose up -d
   ```

2. **查看状态**
   ```bash
   docker-compose ps
   ```

3. **查看日志**
   ```bash
   docker-compose logs gateway
   ```

## 📖 API文档

启动网关后，访问以下URL查看API文档：

- **OpenAPI文档**: http://localhost:8000/docs
- **ReDoc文档**: http://localhost:8000/redoc
- **健康检查**: http://localhost:8000/health
- **监控指标**: http://localhost:8000/metrics

## 🔧 配置说明

### 基础配置
```python
GATEWAY_HOST=0.0.0.0          # 监听地址
GATEWAY_PORT=8000             # 监听端口
GATEWAY_DEBUG=false           # 调试模式
```

### 认证配置
```python
JWT_SECRET=your-secret        # JWT密钥
JWT_ALGORITHM=HS256           # JWT算法
JWT_EXPIRATION=3600           # 令牌过期时间(秒)
```

### 限流配置
```python
RATE_LIMIT_ENABLED=true       # 启用限流
RATE_LIMIT_DEFAULT=100        # 默认限制(每分钟)
RATE_LIMIT_WINDOW=60          # 时间窗口(秒)
```

### 服务配置
```python
USER_SERVICE_URL=http://localhost:8001
STRATEGY_SERVICE_URL=http://localhost:8002
VNPY_SERVICE_URL=http://localhost:8006
```

## 🔌 服务集成

### 注册微服务
```python
from gateway.discovery.service_registry import ServiceRegistry, ServiceInfo

# 注册服务
service = ServiceInfo(
    name="user_service",
    host="localhost",
    port=8001,
    health_check_url="/health"
)

await registry.register_service(service)
```

### 服务间通信
```python
from shared.communication import ServiceClient

# 创建客户端
client = ServiceClient(
    service_name="user_service",
    base_url="http://localhost:8001"
)

# 调用服务
response = await client.get("/api/v1/users")
print(response.data)
```

### 事件发布订阅
```python
from shared.communication import EventBus, DomainEvent

# 创建事件总线
event_bus = EventBus("redis://localhost:6379", "gateway_service")

# 发布事件
await event_bus.publish_domain_event(
    event_type="user.registered",
    aggregate_id="user_123",
    aggregate_type="User",
    payload={"username": "new_user"}
)

# 注册事件处理器
async def handle_user_event(event: DomainEvent):
    print(f"处理用户事件: {event.event_type}")

event_bus.register_handler("user.registered", handle_user_event)
```

## 📊 监控和运维

### 健康检查
```bash
curl http://localhost:8000/health
```

### 获取指标
```bash
curl http://localhost:8000/metrics
```

### 服务状态
```bash
curl http://localhost:8000/admin/services
```

### 限流状态
```bash
curl http://localhost:8000/admin/rate-limits
```

## 🧪 测试

### 运行测试
```bash
pytest tests/ -v
```

### 集成测试
```bash
pytest tests/test_gateway_integration.py -v
```

### 性能测试
```bash
python tests/performance_test.py
```

## 🔒 安全考虑

### JWT安全
- 使用强密钥
- 定期轮换密钥
- 设置合理的过期时间

### 限流保护
- 配置合理的限流阈值
- 监控异常流量模式
- 实施IP白名单

### 网络安全
- 使用HTTPS
- 配置CORS策略
- 实施请求验证

## 📈 性能优化

### 连接池优化
- 配置合理的连接数
- 启用连接复用
- 监控连接状态

### 缓存策略
- Redis缓存配置
- 权限信息缓存
- 响应结果缓存

### 监控指标
- 响应时间监控
- 吞吐量统计
- 错误率跟踪

## 🐛 故障排除

### 常见问题

1. **Redis连接失败**
   ```bash
   # 检查Redis状态
   redis-cli ping
   
   # 检查网络连接
   telnet localhost 6379
   ```

2. **服务发现失败**
   ```bash
   # 检查服务注册
   curl http://localhost:8000/admin/services
   
   # 查看服务日志
   docker-compose logs user-service
   ```

3. **认证失败**
   ```bash
   # 验证JWT密钥配置
   echo $JWT_SECRET
   
   # 检查令牌格式
   curl -H "Authorization: Bearer YOUR_TOKEN" \
        http://localhost:8000/api/v1/users
   ```

### 日志分析
```bash
# 查看网关日志
tail -f logs/gateway.log

# 查看错误日志
grep ERROR logs/gateway.log

# 查看性能日志
grep "SLOW REQUEST" logs/gateway.log
```

## 🤝 贡献指南

1. Fork 项目
2. 创建特性分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 📄 许可证

MIT License

## 📞 支持

- 文档: [RedFire文档](https://docs.redfire.com)
- 问题反馈: [GitHub Issues](https://github.com/redfire/gateway/issues)
- 讨论: [GitHub Discussions](https://github.com/redfire/gateway/discussions)
