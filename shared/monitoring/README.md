# RedFire统一监控系统

基于现有85%完善基础构建的企业级监控解决方案。

## 🌟 核心特性

### 已有基础 (85%完成)
- ✅ **647行企业级配置** - `config/backend/monitor_config.py`
- ✅ **专业交易监控** - `DomesticGatewayMonitor` (251行完整实现)
- ✅ **Docker容器化** - `backend/gateway/docker-compose.yml`
- ✅ **运维指南** - `docs/operations/monitoringGuide.md`

### 新增完善 (15%补充)
- 🆕 **Prometheus指标导出** - 统一指标收集和导出
- 🆕 **Grafana仪表板** - 系统总览和VnPy交易监控
- 🆕 **ELK日志系统** - 结构化日志收集和分析
- 🆕 **健康检查API** - 6个核心服务健康监控
- 🆕 **告警通知系统** - 基于配置的多渠道通知
- 🆕 **统一监控服务** - 集成所有监控组件
- 🆕 **RESTful API** - 完整的监控管理接口

## 🏗️ 系统架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Prometheus    │    │     Grafana     │    │   ELK Stack     │
│   指标收集      │    │   可视化展示    │    │   日志分析      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
┌─────────────────────────────────┼─────────────────────────────────┐
│                    UnifiedMonitor                                │
│                     统一监控服务                                │
├─────────────────────────────────┼─────────────────────────────────┤
│  PrometheusExporter  │  HealthChecker  │  AlertManager         │
│    指标导出          │    健康检查     │   告警管理            │
└─────────────────────────────────┼─────────────────────────────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         │                       │                       │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  VnPy核心服务   │    │  用户交易服务   │    │  策略数据服务   │
│    :8006        │    │    :8001        │    │    :8002        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 快速开始

### 1. 一键启动监控系统

```bash
# 进入监控目录
cd backend/gateway

# 执行启动脚本 (Windows)
.\monitoring\start-monitoring.sh

# 或使用Docker Compose
docker-compose up -d
```

### 2. 访问监控界面

- **Grafana仪表板**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090
- **Kibana日志**: http://localhost:5601
- **Elasticsearch**: http://localhost:9200

### 3. 监控API接口

```python
from shared.monitoring import monitoring_router, unified_monitor
from fastapi import FastAPI

app = FastAPI()

# 集成监控API
app.include_router(monitoring_router)

# 启动统一监控
@app.on_event("startup")
async def startup():
    await unified_monitor.start_monitoring()

@app.on_event("shutdown")
async def shutdown():
    await unified_monitor.stop_monitoring()
```

## 📊 监控指标

### 系统指标
- CPU使用率、内存使用率、磁盘使用率
- 网络流量、系统负载
- 服务健康状态、响应时间

### 应用指标  
- HTTP请求数、响应时间、错误率
- 活跃连接数、请求队列长度
- 数据库连接池状态

### 业务指标 (VnPy)
- 网关连接状态、交易延迟
- 订单频率、交易量
- 策略盈亏、持仓价值
- DomesticGateway专业监控

## 🚨 告警配置

基于 `config/backend/monitor_config.py` 的8个核心告警规则：

```python
ALERT_RULES_CONFIG = [
    AlertRuleConfig(
        rule_id="cpu_high",
        name="CPU使用率过高", 
        condition="value > 85",
        level=MonitorLevel.ERROR
    ),
    # ... 其他7个规则
]
```

### 通知渠道
- ✉️ **邮件通知** - SMTP配置
- 🔗 **Webhook通知** - HTTP回调
- 📱 **短信通知** - SMS网关
- 📝 **日志记录** - 结构化日志

## 🔧 API接口

### 健康检查
```bash
# 基础健康检查
curl http://localhost:8000/monitoring/health

# 详细健康状态
curl http://localhost:8000/monitoring/health/detailed

# 单个服务健康检查
curl http://localhost:8000/monitoring/health/vnpy_core
```

### 监控指标
```bash
# Prometheus指标
curl http://localhost:8000/monitoring/metrics

# 监控摘要
curl http://localhost:8000/monitoring/metrics/summary

# 完整监控数据
curl http://localhost:8000/monitoring/metrics/full
```

### 告警管理
```bash
# 获取告警列表
curl http://localhost:8000/monitoring/alerts

# 确认告警
curl -X POST "http://localhost:8000/monitoring/alerts/cpu_high/acknowledge?acknowledged_by=admin"

# 静默告警
curl -X POST "http://localhost:8000/monitoring/alerts/cpu_high/silence?duration_minutes=60"
```

### DomesticGateway专用
```bash
# 性能指标
curl http://localhost:8000/monitoring/domestic-gateway/performance

# 统计信息
curl http://localhost:8000/monitoring/domestic-gateway/statistics
```

## 📈 Grafana仪表板

### 系统总览仪表板
- CPU、内存、网络、磁盘使用率
- 服务状态表格
- 系统负载趋势

### VnPy交易监控仪表板
- 网关连接状态
- 交易延迟分布 (95th/50th percentile)
- 订单频率和交易量
- 策略盈亏和持仓价值

## 🗂️ 日志系统

### ELK Stack配置
- **Elasticsearch**: 日志存储和索引
- **Logstash**: 日志解析和处理
- **Kibana**: 日志查询和可视化

### 日志格式
```json
{
  "timestamp": "2024-12-01T10:30:00Z",
  "level": "INFO",
  "service": "vnpy_core", 
  "message": "订单执行成功",
  "request_id": "req_123456",
  "gateway": "ctptest",
  "symbol": "rb2501"
}
```

### 日志索引
- `redfire-logs-*`: 应用日志
- `redfire-errors-*`: 错误日志
- `redfire-trading-*`: VnPy交易日志
- `redfire-metrics-*`: 性能指标日志

## 🔧 配置管理

### 监控配置 (monitor_config.py)
```python
# 服务配置
MONITORED_SERVICES_DETAILED = {
    "vnpy_core": {
        "name": "🔥 VnPy核心服务",
        "port": 8006,
        "priority": "critical",
        "health_check": {
            "endpoint": "/health",
            "timeout": 5,
            "interval": 30
        }
    }
}

# 告警规则
ALERT_RULES_CONFIG = [...]

# 通知渠道  
NOTIFICATION_CHANNELS_CONFIG = [...]
```

### Docker配置 (docker-compose.yml)
- Prometheus + Grafana + ELK Stack
- 数据持久化卷配置
- 网络和依赖关系

## 🛠️ 开发指南

### 添加自定义指标
```python
from shared.monitoring import prometheus_exporter

# 添加业务指标
prometheus_exporter.business_metrics['custom_metric'].set(value)
```

### 集成DomesticGatewayMonitor
```python
from shared.monitoring import unified_monitor

# 监控器会自动集成DomesticGatewayMonitor
# 无需额外配置
```

### 自定义告警规则
```python
from config.backend.monitor_config import ALERT_RULES_CONFIG
from shared.monitoring.alert_system import AlertRuleConfig, MonitorLevel

# 添加新规则
new_rule = AlertRuleConfig(
    rule_id="custom_alert",
    name="自定义告警",
    metric_name="custom_metric", 
    condition="value > 100",
    level=MonitorLevel.WARNING
)
```

## 📋 运维指南

### 服务管理
```bash
# 查看服务状态
docker-compose ps

# 查看服务日志
docker-compose logs -f grafana
docker-compose logs -f prometheus
docker-compose logs -f elasticsearch

# 重启服务
docker-compose restart grafana
```

### 数据备份
```bash
# 备份Grafana配置
docker cp redfire-grafana:/var/lib/grafana ./backup/grafana

# 备份Prometheus数据
docker cp redfire-prometheus:/prometheus ./backup/prometheus

# 备份Elasticsearch数据
docker cp redfire-elasticsearch:/usr/share/elasticsearch/data ./backup/elasticsearch
```

### 性能调优
- **Prometheus**: 调整抓取间隔和保留时间
- **Grafana**: 优化查询和缓存设置
- **Elasticsearch**: 配置JVM堆大小和索引策略

## 🔍 故障排除

### 常见问题

1. **Grafana无法连接Prometheus**
   - 检查Docker网络配置
   - 验证Prometheus服务状态

2. **Elasticsearch启动失败**
   - 检查内存设置 (`ES_JAVA_OPTS`)
   - 确保端口未被占用

3. **告警不发送**
   - 检查SMTP配置
   - 验证Webhook URL可达性

### 调试命令
```bash
# 检查网络连通性
docker-compose exec grafana ping prometheus
docker-compose exec logstash ping elasticsearch

# 查看配置文件
docker-compose exec prometheus cat /etc/prometheus/prometheus.yml
docker-compose exec grafana cat /etc/grafana/grafana.ini
```

## 📚 相关文档

- [监控配置文档](../../config/backend/monitor_config.py)
- [运维指南](../../docs/operations/monitoringGuide.md)  
- [DomesticGateway监控](../../backend/core/tradingEngine/monitoring/)
- [Docker部署配置](../../backend/gateway/docker-compose.yml)

## 🤝 贡献指南

1. Fork项目仓库
2. 创建功能分支
3. 提交代码变更
4. 创建Pull Request

## 📄 许可证

MIT License - 详见 [LICENSE](../../LICENSE) 文件

---

**RedFire监控系统 v2.0** - 基于85%已有基础的企业级监控解决方案 🚀
