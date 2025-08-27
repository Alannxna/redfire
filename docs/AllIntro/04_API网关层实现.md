# 🔌 TODO-04: API网关层实现

## 🎯 任务概述

**任务ID**: micro_02  
**优先级**: 高  
**预估工期**: 4-5天  
**负责模块**: 微服务架构

### 问题描述
实现基于FastAPI的统一API网关，集成认证、限流、负载均衡等核心功能，为5个微服务提供统一的访问入口。

## 🔍 现状分析

### 当前API架构问题

#### 1. 分散的API入口
```python
# backend/main.py - 简单FastAPI应用
app = FastAPI(title="RedFire API")
app.include_router(auth_router)

# backend/legacy/interfaces/rest/app.py - VnPy Web API  
class VnPyWebAPI:
    def get_app(self) -> FastAPI:
        # 另一套API架构
        
# 问题: 
# - 没有统一的API网关
# - 服务直接暴露给客户端
# - 缺乏统一的认证和授权
```

#### 2. 认证机制不统一
```python
# backend/api/auth_routes.py - 基础认证
def get_current_user(credentials: HTTPAuthorizationCredentials):
    token = credentials.credentials
    payload = verify_token(token)
    
# backend/legacy/interfaces/rest/middleware/auth_middleware.py - 复杂认证
class AuthMiddleware:
    def __init__(self, config: Optional[UnifiedConfig] = None):
        self.jwt_helper = JWTHelper(config)
        
# 问题:
# - 多套认证逻辑
# - JWT处理不一致
# - 权限控制分散
```

#### 3. 缺乏统一的中间件
- 没有统一的请求日志记录
- 缺乏API限流保护
- 错误处理不标准化
- 监控指标收集不完整

### 微服务通信问题

#### 1. 服务发现机制缺失
```python
# 当前硬编码的服务调用
VNPY_CORE_URL = "http://localhost:8006"
USER_TRADING_URL = "http://localhost:8001"

# 问题:
# - 服务地址硬编码
# - 无法动态发现服务
# - 负载均衡缺失
```

#### 2. 跨服务认证复杂
- 微服务间需要重复认证
- 缺乏统一的服务间认证
- Token传递机制不完善

## 🎨 设计方案

### 1. API网关核心架构

```python
# gateway/core/gateway.py
class RedFireAPIGateway:
    """RedFire API网关核心类"""
    
    def __init__(self, config: GatewayConfig):
        self.config = config
        self.app = FastAPI(
            title="RedFire API Gateway",
            version="1.0.0",
            docs_url="/gateway/docs"
        )
        
        # 核心组件
        self.service_registry = ServiceRegistry(config.service_registry)
        self.auth_manager = AuthManager(config.auth)
        self.rate_limiter = RateLimiter(config.rate_limit)
        self.load_balancer = LoadBalancer(config.load_balance)
        
        # 初始化网关
        self._setup_middleware()
        self._setup_routes()
        self._setup_error_handlers()
    
    def _setup_middleware(self):
        """设置中间件"""
        # 1. CORS中间件
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=self.config.cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"]
        )
        
        # 2. 请求日志中间件
        self.app.add_middleware(RequestLoggingMiddleware)
        
        # 3. 认证中间件
        self.app.add_middleware(
            GatewayAuthMiddleware,
            auth_manager=self.auth_manager
        )
        
        # 4. 限流中间件
        self.app.add_middleware(
            RateLimitingMiddleware,
            rate_limiter=self.rate_limiter
        )
        
        # 5. 监控中间件
        self.app.add_middleware(MetricsMiddleware)
    
    def _setup_routes(self):
        """设置路由"""
        # 认证相关路由
        self.app.include_router(
            self._create_auth_router(),
            prefix="/api/v1/auth",
            tags=["认证"]
        )
        
        # 代理路由
        self.app.include_router(
            self._create_proxy_router(),
            prefix="/api/v1"
        )
        
        # 网关管理路由
        self.app.include_router(
            self._create_gateway_router(),
            prefix="/gateway"
        )
```

### 2. 服务发现与注册

```python
# gateway/core/service_registry.py
class ServiceRegistry:
    """服务注册与发现"""
    
    def __init__(self, config: ServiceRegistryConfig):
        self.config = config
        self.services: Dict[str, List[ServiceInstance]] = {}
        self.health_checker = HealthChecker()
        
    async def register_service(self, service: ServiceInstance):
        """注册服务实例"""
        service_name = service.name
        
        if service_name not in self.services:
            self.services[service_name] = []
        
        self.services[service_name].append(service)
        
        # 启动健康检查
        await self.health_checker.start_monitoring(service)
        
        logger.info(f"服务注册成功: {service_name}@{service.host}:{service.port}")
    
    async def discover_service(self, service_name: str) -> Optional[ServiceInstance]:
        """发现可用服务实例"""
        if service_name not in self.services:
            return None
        
        # 获取健康的服务实例
        healthy_instances = [
            instance for instance in self.services[service_name]
            if instance.status == ServiceStatus.HEALTHY
        ]
        
        if not healthy_instances:
            logger.warning(f"没有可用的服务实例: {service_name}")
            return None
        
        # 负载均衡选择实例
        return self.load_balancer.select_instance(healthy_instances)
    
    async def get_service_endpoints(self) -> Dict[str, List[str]]:
        """获取所有服务端点"""
        endpoints = {}
        for service_name, instances in self.services.items():
            endpoints[service_name] = [
                f"http://{instance.host}:{instance.port}"
                for instance in instances
                if instance.status == ServiceStatus.HEALTHY
            ]
        return endpoints

# gateway/core/service_instance.py
@dataclass
class ServiceInstance:
    """服务实例"""
    name: str
    host: str
    port: int
    version: str
    status: ServiceStatus = ServiceStatus.UNKNOWN
    metadata: Dict[str, Any] = field(default_factory=dict)
    last_heartbeat: Optional[datetime] = None
    
    @property
    def url(self) -> str:
        return f"http://{self.host}:{self.port}"
    
    @property
    def health_check_url(self) -> str:
        return f"{self.url}/health"
```

### 3. 统一认证管理

```python
# gateway/auth/auth_manager.py
class AuthManager:
    """统一认证管理器"""
    
    def __init__(self, config: AuthConfig):
        self.config = config
        self.jwt_handler = JWTHandler(config.jwt)
        self.user_service = UserServiceClient(config.user_service_url)
        
    async def authenticate_request(self, request: Request) -> Optional[UserContext]:
        """认证请求"""
        # 1. 检查是否为公开路径
        if self._is_public_path(request.url.path):
            return None
        
        # 2. 提取认证信息
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            raise AuthenticationError("缺少认证令牌")
        
        # 3. 验证JWT令牌
        try:
            token = auth_header.split(" ")[1]  # Bearer <token>
            payload = self.jwt_handler.decode_token(token)
        except Exception as e:
            raise AuthenticationError(f"令牌验证失败: {e}")
        
        # 4. 获取用户信息
        user_id = payload.get("user_id")
        user_info = await self.user_service.get_user_info(user_id)
        
        if not user_info:
            raise AuthenticationError("用户不存在")
        
        return UserContext(
            user_id=user_id,
            username=user_info["username"],
            roles=user_info["roles"],
            permissions=user_info["permissions"]
        )
    
    async def authorize_request(self, user_context: UserContext, 
                              required_permission: str) -> bool:
        """授权检查"""
        if not user_context:
            return False
        
        return required_permission in user_context.permissions
    
    def _is_public_path(self, path: str) -> bool:
        """检查是否为公开路径"""
        public_paths = [
            "/api/v1/auth/login",
            "/api/v1/auth/register", 
            "/api/v1/auth/refresh",
            "/health",
            "/docs",
            "/gateway/docs"
        ]
        return any(path.startswith(public_path) for public_path in public_paths)
```

### 4. API代理与路由

```python
# gateway/proxy/api_proxy.py
class APIProxy:
    """API代理器"""
    
    def __init__(self, service_registry: ServiceRegistry):
        self.service_registry = service_registry
        self.http_client = httpx.AsyncClient(timeout=30.0)
        
    async def proxy_request(self, request: Request, service_name: str) -> Response:
        """代理请求到目标服务"""
        
        # 1. 发现目标服务
        service_instance = await self.service_registry.discover_service(service_name)
        if not service_instance:
            raise ServiceUnavailableError(f"服务不可用: {service_name}")
        
        # 2. 构建目标URL
        target_url = f"{service_instance.url}{request.url.path}"
        if request.url.query:
            target_url += f"?{request.url.query}"
        
        # 3. 转发请求
        try:
            # 复制请求头
            headers = dict(request.headers)
            headers.pop("host", None)  # 移除host头
            
            # 添加服务间认证头
            headers["X-Gateway-Service"] = "api-gateway"
            headers["X-Request-ID"] = str(uuid.uuid4())
            
            # 发送请求
            response = await self.http_client.request(
                method=request.method,
                url=target_url,
                headers=headers,
                content=await request.body(),
                params=request.query_params
            )
            
            # 返回响应
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=dict(response.headers)
            )
            
        except httpx.RequestError as e:
            logger.error(f"代理请求失败: {e}")
            raise ServiceUnavailableError("服务请求失败")

# gateway/routes/proxy_routes.py
def create_proxy_router(api_proxy: APIProxy) -> APIRouter:
    """创建代理路由"""
    router = APIRouter()
    
    # 用户交易服务路由
    @router.api_route("/trading/{path:path}", 
                     methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
    async def proxy_to_trading(request: Request, path: str):
        return await api_proxy.proxy_request(request, "user_trading")
    
    # VnPy核心服务路由
    @router.api_route("/vnpy/{path:path}",
                     methods=["GET", "POST", "PUT", "DELETE", "PATCH"]) 
    async def proxy_to_vnpy(request: Request, path: str):
        return await api_proxy.proxy_request(request, "vnpy_core")
    
    # 策略数据服务路由
    @router.api_route("/strategy/{path:path}",
                     methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
    async def proxy_to_strategy(request: Request, path: str):
        return await api_proxy.proxy_request(request, "strategy_data")
    
    # 网关适配服务路由
    @router.api_route("/gateway-adapter/{path:path}",
                     methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
    async def proxy_to_gateway_adapter(request: Request, path: str):
        return await api_proxy.proxy_request(request, "gateway")
    
    # 监控服务路由
    @router.api_route("/monitor/{path:path}",
                     methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
    async def proxy_to_monitor(request: Request, path: str):
        return await api_proxy.proxy_request(request, "monitor")
    
    return router
```

### 5. 限流与负载均衡

```python
# gateway/middleware/rate_limiting.py
class RateLimitingMiddleware:
    """限流中间件"""
    
    def __init__(self, rate_limiter: RateLimiter):
        self.rate_limiter = rate_limiter
    
    async def __call__(self, request: Request, call_next):
        """限流检查"""
        
        # 获取客户端标识
        client_id = self._get_client_id(request)
        
        # 检查限流
        if not await self.rate_limiter.allow_request(client_id, request.url.path):
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "message": "请求过于频繁，请稍后重试"
                }
            )
        
        return await call_next(request)
    
    def _get_client_id(self, request: Request) -> str:
        """获取客户端标识"""
        # 优先使用API Key
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return f"api_key:{api_key}"
        
        # 使用用户ID
        user_id = getattr(request.state, "user_id", None)
        if user_id:
            return f"user:{user_id}"
        
        # 使用IP地址
        client_ip = request.client.host
        return f"ip:{client_ip}"

# gateway/core/load_balancer.py
class LoadBalancer:
    """负载均衡器"""
    
    def __init__(self, strategy: str = "round_robin"):
        self.strategy = strategy
        self.round_robin_counters = {}
    
    def select_instance(self, instances: List[ServiceInstance]) -> ServiceInstance:
        """选择服务实例"""
        if not instances:
            raise ValueError("没有可用的服务实例")
        
        if len(instances) == 1:
            return instances[0]
        
        if self.strategy == "round_robin":
            return self._round_robin_select(instances)
        elif self.strategy == "random":
            return random.choice(instances)
        elif self.strategy == "least_connections":
            return self._least_connections_select(instances)
        else:
            return instances[0]
    
    def _round_robin_select(self, instances: List[ServiceInstance]) -> ServiceInstance:
        """轮询选择"""
        service_name = instances[0].name
        
        if service_name not in self.round_robin_counters:
            self.round_robin_counters[service_name] = 0
        
        counter = self.round_robin_counters[service_name]
        selected = instances[counter % len(instances)]
        
        self.round_robin_counters[service_name] = (counter + 1) % len(instances)
        
        return selected
```

## 🔧 实施步骤

### 阶段1: 网关基础架构 (2天)

1. **创建网关项目结构**
   ```bash
   mkdir -p gateway/{core,auth,proxy,middleware,routes}
   mkdir -p gateway/config
   ```

2. **实现核心网关类**
   - RedFireAPIGateway主类
   - 基础中间件集成
   - 配置管理

### 阶段2: 服务发现实现 (1天)

1. **服务注册机制**
   - ServiceRegistry实现
   - 健康检查机制
   - 服务实例管理

2. **服务发现API**
   ```python
   # 服务自动注册
   @app.on_event("startup")
   async def register_service():
       await service_registry.register_service(ServiceInstance(
           name="user_trading",
           host="user-trading",
           port=8001
       ))
   ```

### 阶段3: 认证统一化 (1天)

1. **JWT认证集成**
   - 统一JWT处理
   - 用户信息获取
   - 权限验证

2. **认证中间件**
   - 请求认证拦截
   - 用户上下文传递
   - 错误处理

### 阶段4: 代理与路由 (1天)

1. **API代理实现**
   - 请求转发机制
   - 响应处理
   - 错误处理

2. **动态路由配置**
   - 路由规则定义
   - 服务映射
   - 版本控制

## 📊 验收标准

### 功能验收
- [ ] 统一API入口工作正常
- [ ] 服务发现和注册功能
- [ ] 认证和授权机制
- [ ] 请求代理和负载均衡

### 性能指标
- [ ] API响应时间增加 < 50ms
- [ ] 支持并发请求 > 1000
- [ ] 错误率 < 0.1%
- [ ] 限流机制有效

### 安全标准
- [ ] JWT认证安全
- [ ] API限流保护
- [ ] 请求日志完整
- [ ] 错误信息不泄露敏感数据

## 🚨 风险评估

### 高风险
- **单点故障**: 网关故障影响所有服务
- **性能瓶颈**: 可能成为系统瓶颈

### 中风险
- **配置复杂**: 路由配置管理复杂
- **调试困难**: 请求链路复杂化

### 缓解措施
1. **高可用部署**: 多实例部署
2. **性能优化**: 异步处理和连接池
3. **监控完善**: 全链路监控

## 📈 预期收益

### 短期收益
- API访问统一化
- 认证机制标准化
- 安全性显著提升

### 长期收益
- 支持API版本管理
- 便于服务治理
- 微服务架构完善

## 📝 相关文档

- [API网关设计模式](../architecture/api-gateway-patterns.md)
- [微服务认证指南](../security/microservices-auth.md)
- [负载均衡策略](../architecture/load-balancing.md)

---

**更新时间**: 2024-01-15  
**文档版本**: v1.0  
**负责人**: RedFire架构团队
