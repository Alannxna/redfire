# 🚀 国内券商接口快速开始指南

## 📖 概述

RedFire交易系统现已完全支持国内三大主流券商接口：
- **vnpy_ctptest**: CTP测试/仿真交易系统
- **vnpy_xtp**: 中泰证券XTP极速交易接口  
- **vnpy_oes**: 宽睿OES高性能交易系统

本指南将帮助您快速上手并开始交易。

## ⚡ 快速安装

### 1. 安装依赖
```bash
# 安装VnPy和相关网关
pip install vnpy
pip install vnpy_ctptest
pip install vnpy_xtp    # 生产环境
pip install vnpy_oes    # 生产环境

# 安装其他依赖
pip install pyyaml
pip install pytest
```

### 2. 克隆RedFire项目
```bash
git clone <your-redfire-repo>
cd redfire
```

## 🔧 配置设置

### 1. 复制配置模板
```bash
cp config/domestic_gateways_example.yaml config/domestic_gateways_dev.yaml
```

### 2. 编辑配置文件
编辑 `config/domestic_gateways_dev.yaml`：

```yaml
# 开发环境只启用CTP测试
enabled_gateways:
  - ctptest

# CTP测试配置（SimNow仿真）
ctptest_config:
  enabled: true
  userid: "your_simnow_userid"     # 替换为您的SimNow账号
  password: "your_simnow_password" # 替换为您的SimNow密码
  brokerid: "9999"
  td_address: "tcp://180.168.146.187:10101"
  md_address: "tcp://180.168.146.187:10111"
  environment: "simnow"

# 其他网关暂时禁用
xtp_config:
  enabled: false
oes_config:
  enabled: false

# 开发环境配置
enable_auto_reconnect: true
reconnect_interval: 5
enable_monitoring: true
```

## 🎯 快速测试

### 1. 运行测试用例
```bash
# 运行基础测试
python -m pytest tests/test_domestic_gateways.py -v

# 运行特定测试
python -m pytest tests/test_domestic_gateways.py::TestDomesticGatewaysAdapter::test_adapter_initialization -v
```

### 2. 运行示例程序
```bash
# 运行完整演示
python examples/domestic_gateways_usage_example.py
```

## 💻 基础使用代码

### 最简使用示例
```python
import asyncio
from backend.core.tradingEngine.adapters.domestic_gateways_adapter import DomesticGatewaysAdapter
from backend.core.tradingEngine.config.domestic_gateways_config import load_domestic_config

async def simple_trading_example():
    # 1. 创建适配器
    adapter = DomesticGatewaysAdapter()
    
    # 2. 加载配置
    config = load_domestic_config("development")
    
    # 3. 初始化
    await adapter.initialize(config)
    
    # 4. 连接网关
    results = await adapter.connect_all_gateways()
    print(f"连接结果: {results}")
    
    # 5. 提交测试订单
    order_data = {
        'symbol': '000001',
        'price': 10.0,
        'volume': 100,
        'direction': 'BUY'
    }
    
    order_id = await adapter.submit_order(order_data)
    print(f"订单ID: {order_id}")
    
    # 6. 清理
    await adapter.disconnect_all_gateways()

# 运行示例
asyncio.run(simple_trading_example())
```

## 📊 监控和告警

### 启用监控
```python
from backend.core.tradingEngine.monitoring.domestic_gateway_monitor import get_gateway_monitor

# 获取监控实例
monitor = get_gateway_monitor()

# 启动监控
await monitor.start_monitoring()

# 添加自定义告警回调
def my_alert_handler(alert):
    print(f"收到告警: {alert.message}")

monitor.add_alert_callback(my_alert_handler)

# 记录性能数据
monitor.record_latency("CTPTEST", 50.0)
monitor.record_order_result("CTPTEST", True)

# 获取统计信息
stats = monitor.get_gateway_statistics("CTPTEST")
print(f"网关统计: {stats}")
```

## 🔍 故障排除

### 常见问题

#### 1. CTPTest连接失败
```
❌ 错误: CTPTest配置缺少必要字段
```
**解决方案**: 检查配置文件中是否包含所有必要字段：
- userid, password, brokerid
- td_address, md_address

#### 2. SimNow认证失败
```
❌ 错误: Authentication failed
```
**解决方案**: 
- 确认SimNow账号密码正确
- 检查网络连接
- 尝试重新申请SimNow账号

#### 3. 导入错误
```
❌ 错误: No module named 'vnpy_ctptest'
```
**解决方案**: 安装对应的网关模块
```bash
pip install vnpy_ctptest
```

### 调试模式

启用详细日志：
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📚 进阶使用

### 多网关配置
```yaml
# 生产环境配置示例
enabled_gateways:
  - xtp
  - oes

xtp_config:
  enabled: true
  userid: "your_xtp_user"
  password: "your_xtp_password"
  client_id: 1
  software_key: "your_software_key"
  trade_ip: "xxx.xxx.xxx.xxx"
  quote_ip: "xxx.xxx.xxx.xxx"
  trade_port: 6001
  quote_port: 6002

oes_config:
  enabled: true
  username: "your_oes_user"
  password: "your_oes_password"
  ord_server: "tcp://xxx.xxx.xxx.xxx:xxxx"
  rpt_server: "tcp://xxx.xxx.xxx.xxx:xxxx"
  qry_server: "tcp://xxx.xxx.xxx.xxx:xxxx"
```

### 自定义告警规则
```python
from backend.core.tradingEngine.monitoring.domestic_gateway_monitor import AlertRule, AlertLevel, MetricType

# 创建自定义告警规则
custom_rule = AlertRule(
    name="my_latency_rule",
    metric_type=MetricType.LATENCY,
    condition=">=",
    threshold=200.0,  # 200ms
    level=AlertLevel.WARNING,
    consecutive_violations=2
)

monitor.add_alert_rule(custom_rule)
```

### 事件回调处理
```python
# 注册事件回调
async def on_order_update(order_data):
    print(f"订单更新: {order_data}")

async def on_trade_update(trade_data):
    print(f"成交更新: {trade_data}")

adapter.on('on_order_update', on_order_update)
adapter.on('on_trade_update', on_trade_update)
```

## 🎓 学习资源

### 文档
- [完整技术文档](docs/AllIntro/11_国内券商接口适配.md)
- [VnPy官方文档](https://www.vnpy.com/)
- [CTP API文档](http://www.sfit.com.cn/)

### 示例代码
- [完整使用示例](examples/domestic_gateways_usage_example.py)
- [测试用例](tests/test_domestic_gateways.py)
- [配置示例](config/domestic_gateways_example.yaml)

### 社区支持
- GitHub Issues
- VnPy社区论坛
- 量化交易群组

## 🚨 重要提醒

### 开发环境
- ✅ 使用SimNow仿真账号进行测试
- ✅ 先在测试环境验证所有功能
- ❌ 不要在开发环境使用真实资金

### 生产环境
- ✅ 确保已获得券商接入授权
- ✅ 完成充分的测试验证
- ✅ 配置完整的监控和告警
- ✅ 做好风险控制和资金管理

### 安全注意事项
- 🔐 妥善保管账号密码和密钥
- 🔐 不要在代码中硬编码敏感信息
- 🔐 定期更新密码和软件版本
- 🔐 监控异常交易和登录行为

---

## 🎉 开始您的量化交易之旅！

现在您已经完成了RedFire国内券商接口的快速配置，可以开始探索量化交易的无限可能了！

如有任何问题，请查看详细文档或联系技术支持。

祝您交易顺利！ 📈✨
