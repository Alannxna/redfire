# 高级交易引擎模块

## 📋 概述

高级交易引擎模块是基于vnpy-core的MainEngine实现，提供了增强的交易引擎功能，包括多连接管理、负载均衡、故障转移、性能监控和资源管理等高级特性。

## 🚀 主要功能

### 1. 高级主引擎 (AdvancedMainEngine)
- **多连接管理**: 支持多个网关连接，智能管理连接状态
- **负载均衡**: 多种负载均衡策略，自动优化负载分配
- **故障转移**: 自动故障检测和恢复，提高系统可用性
- **性能监控**: 实时性能指标监控，自动性能优化
- **资源管理**: 智能资源分配和回收

### 2. 多连接引擎 (MultiConnectionEngine)
- **多网关连接**: 同时连接多个交易网关
- **连接池管理**: 动态管理连接数量，优化资源使用
- **智能路由**: 根据策略自动选择最优网关
- **健康监控**: 实时监控网关健康状态
- **自动重连**: 故障自动恢复机制

### 3. 负载均衡引擎 (LoadBalancingEngine)
- **多种算法**: 轮询、加权、最少连接、响应时间等
- **动态调整**: 根据性能指标自动调整负载分配策略
- **性能优化**: 自动优化负载分配，提升系统性能
- **健康检查**: 实时监控网关健康状态
- **统计报告**: 详细的负载均衡统计信息

### 4. 连接管理器 (ConnectionManager)
- **连接池管理**: 创建、销毁、复用连接
- **故障转移**: 自动故障检测和恢复
- **健康监控**: 连接状态监控和告警
- **负载均衡**: 智能连接分配

### 5. 资源管理器 (ResourceManager)
- **内存管理**: 内存分配、监控、优化
- **CPU管理**: CPU使用率监控、负载均衡
- **线程管理**: 线程池管理、任务调度
- **缓存管理**: 缓存策略、内存清理
- **性能优化**: 资源使用优化建议

### 6. 引擎工具 (EngineUtils)
- **性能分析**: 性能指标计算和分析
- **配置管理**: 配置验证和转换
- **数据转换**: 数据格式转换和验证
- **时间处理**: 时间相关工具函数
- **日志工具**: 日志格式化和分析

## 🏗️ 架构设计

```
AdvancedMainEngine
├── ConnectionManager (连接管理)
│   ├── ConnectionPool (连接池)
│   ├── HealthMonitor (健康监控)
│   └── FailoverManager (故障转移)
├── LoadBalancingEngine (负载均衡)
│   ├── AlgorithmSelector (算法选择器)
│   ├── PerformanceAnalyzer (性能分析器)
│   └── AutoAdjuster (自动调整器)
├── ResourceManager (资源管理)
│   ├── MemoryManager (内存管理)
│   ├── ThreadManager (线程管理)
│   └── PerformanceOptimizer (性能优化器)
└── EngineUtils (工具类)
    ├── PerformanceAnalyzer (性能分析)
    ├── ConfigValidator (配置验证)
    ├── DataConverter (数据转换)
    ├── TimeUtils (时间工具)
    └── LogUtils (日志工具)
```

## 📖 使用方法

### 1. 基本使用

```python
from backend.core.tradingEngine.advanced import AdvancedMainEngine, ConnectionManager

# 创建高级主引擎
advanced_engine = AdvancedMainEngine(main_engine, event_engine)

# 添加网关
gateway = advanced_engine.add_gateway_with_monitoring(
    gateway_class=MyGateway,
    gateway_name="my_gateway",
    weight=1.0,
    max_connections=10
)

# 获取最优网关
optimal_gateway = advanced_engine.get_optimal_gateway()

# 更新连接状态
advanced_engine.update_connection_status(
    gateway_name="my_gateway",
    status=ConnectionStatus.CONNECTED
)
```

### 2. 连接管理

```python
from backend.core.tradingEngine.advanced.managers import ConnectionManager, ConnectionConfig, ConnectionType

# 创建连接管理器
connection_manager = ConnectionManager(main_engine, event_engine)

# 创建连接池
config = ConnectionConfig(
    gateway_name="my_gateway",
    connection_type=ConnectionType.TRADING,
    max_connections=10,
    min_connections=2
)

connection_pool = connection_manager.create_connection_pool(config)

# 获取连接
connection = connection_manager.get_optimal_connection(
    gateway_name="my_gateway",
    connection_type=ConnectionType.TRADING,
    strategy="health_based"
)
```

### 3. 负载均衡

```python
from backend.core.tradingEngine.advanced.engines import LoadBalancingEngine, LoadBalanceAlgorithm

# 创建负载均衡引擎
load_balance_engine = LoadBalancingEngine(main_engine, event_engine)

# 注册网关
load_balance_engine.register_gateway(
    gateway_name="gateway1",
    max_connections=100,
    weight=2.0,
    priority=1
)

# 获取最优网关
optimal_gateway = load_balance_engine.get_optimal_gateway(
    algorithm=LoadBalanceAlgorithm.WEIGHTED_LEAST_CONNECTIONS
)

# 更新网关指标
load_balance_engine.update_gateway_metrics(
    gateway_name="gateway1",
    response_time=150.0,
    success=True,
    connection_count=25
)
```

### 4. 资源管理

```python
from backend.core.tradingEngine.advanced.managers import ResourceManager

# 创建资源管理器
resource_manager = ResourceManager(main_engine, event_engine)

# 注册线程
import threading
thread = threading.Thread(target=worker_function)
resource_manager.register_thread(thread, pool_name="worker_pool")

# 获取资源统计
stats = resource_manager.get_resource_stats()
print(f"内存使用率: {stats['memory']['usage_percent']}%")
print(f"线程数量: {stats['thread']['active_threads']}")
```

### 5. 工具函数

```python
from backend.core.tradingEngine.advanced.utils import EngineUtils

# 创建工具类实例
utils = EngineUtils()

# 性能测量装饰器
@utils.measure_performance("database_query")
def query_database():
    # 数据库查询逻辑
    pass

# 配置验证
config = {"host": "localhost", "port": 8080}
is_valid, errors = utils.validate_config(
    config=config,
    required_fields=["host", "port"],
    field_types={"port": int},
    field_ranges={"port": (1, 65535)}
)

if not is_valid:
    print(f"配置验证失败: {errors}")

# 获取性能报告
performance_report = utils.get_performance_report()
print(f"总操作数: {performance_report['total_operations']}")
```

## ⚙️ 配置选项

### 高级主引擎配置

```python
# 连接管理配置
connection_config = {
    "max_connections": 100,
    "min_connections": 10,
    "connection_timeout": 30.0,
    "heartbeat_interval": 10.0,
    "retry_interval": 5.0,
    "max_retries": 3
}

# 负载均衡配置
load_balance_config = {
    "algorithm": "weighted_least_connections",
    "auto_adjust_enabled": True,
    "adjustment_interval": 30.0
}

# 故障转移配置
failover_config = {
    "enabled": True,
    "auto_reconnect": True,
    "failover_threshold": 3
}
```

### 性能阈值配置

```python
# 性能监控阈值
performance_thresholds = {
    "max_response_time": 1000.0,    # 最大响应时间（毫秒）
    "max_error_rate": 0.1,          # 最大错误率
    "max_connection_usage": 0.8,    # 最大连接使用率
    "memory_warning_threshold": 75.0,  # 内存警告阈值
    "memory_critical_threshold": 90.0  # 内存严重阈值
}
```

## 📊 监控和统计

### 1. 连接状态监控

```python
# 获取连接统计
connection_stats = advanced_engine.get_connection_stats()

for gateway_name, stats in connection_stats.items():
    print(f"网关 {gateway_name}:")
    print(f"  状态: {stats['status']}")
    print(f"  连接时间: {stats['connect_time']}")
    print(f"  响应时间: {stats['response_time']}")
    print(f"  错误次数: {stats['error_count']}")
```

### 2. 负载均衡统计

```python
# 获取负载均衡统计
load_balance_stats = load_balance_engine.get_load_balance_stats()

print(f"当前算法: {load_balance_stats['algorithm']}")
print(f"自动调整: {load_balance_stats['auto_adjust_enabled']}")

for gateway_name, gateway_stats in load_balance_stats['gateway_loads'].items():
    print(f"网关 {gateway_name}:")
    print(f"  连接使用率: {gateway_stats['connection_usage']:.2%}")
    print(f"  平均响应时间: {gateway_stats['avg_response_time']:.2f}ms")
    print(f"  错误率: {gateway_stats['error_rate']:.2%}")
    print(f"  负载评分: {gateway_stats['load_score']:.4f}")
```

### 3. 资源使用统计

```python
# 获取资源统计
resource_stats = resource_manager.get_resource_stats()

print(f"内存使用率: {resource_stats['memory']['usage_percent']:.1f}%")
print(f"CPU使用率: {resource_stats['cpu']['usage_percent']:.1f}%")
print(f"活跃线程数: {resource_stats['thread']['active_threads']}")
```

## 🧪 测试

运行测试文件验证模块功能：

```bash
cd backend/core/tradingEngine/advanced
python test_advanced_engines.py
```

## 📝 注意事项

1. **依赖管理**: 确保安装了所需的依赖包（如psutil）
2. **线程安全**: 所有操作都是线程安全的
3. **资源清理**: 使用完毕后记得调用close()方法清理资源
4. **性能监控**: 建议在生产环境中启用性能监控
5. **配置验证**: 使用配置验证功能确保配置正确性

## 🔧 故障排除

### 常见问题

1. **导入错误**: 检查模块路径和依赖关系
2. **连接失败**: 检查网关配置和网络连接
3. **性能下降**: 检查资源使用情况和负载均衡配置
4. **内存泄漏**: 检查是否正确调用了close()方法

### 调试技巧

1. 启用详细日志记录
2. 使用性能监控工具
3. 检查系统资源使用情况
4. 验证配置参数正确性

## 📚 相关文档

- [vnpy-core文档](https://www.vnpy.com/docs/)
- [交易引擎架构设计](./ARCHITECTURE.md)
- [API参考文档](./API_REFERENCE.md)
- [性能调优指南](./PERFORMANCE_TUNING.md)

## 🤝 贡献

欢迎提交Issue和Pull Request来改进这个模块。

## �� 许可证

本项目采用MIT许可证。
