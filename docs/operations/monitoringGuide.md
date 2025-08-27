# 📊 RedFire监控运维指南

## 📋 概述

本指南介绍RedFire系统的监控体系、运维流程和故障处理，帮助运维人员有效管理系统的健康状态。

## 🔍 监控体系

### 1. 系统监控
- **CPU使用率**: 实时监控CPU负载
- **内存使用率**: 监控内存占用情况
- **磁盘I/O**: 监控磁盘读写性能
- **网络流量**: 监控网络带宽使用

### 2. 应用监控
- **服务状态**: 监控各服务运行状态
- **响应时间**: 监控API接口响应时间
- **错误率**: 监控系统错误和异常
- **吞吐量**: 监控系统处理能力

### 3. 业务监控
- **交易量**: 监控交易订单数量
- **成功率**: 监控交易成功率
- **风险指标**: 监控风险控制指标
- **用户活跃度**: 监控用户使用情况

## 🛠️ 监控工具

### Prometheus + Grafana
```yaml
# prometheus.yml 配置
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'redfire-backend'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
    
  - job_name: 'redfire-frontend'
    static_configs:
      - targets: ['localhost:3000']
    metrics_path: '/metrics'
```

### ELK Stack
```yaml
# logstash.conf 配置
input {
  beats {
    port => 5044
  }
}

filter {
  if [fields][service] == "redfire-backend" {
    grok {
      match => { "message" => "%{TIMESTAMP_ISO8601:timestamp} %{LOGLEVEL:level} %{GREEDYDATA:message}" }
    }
  }
}

output {
  elasticsearch {
    hosts => ["localhost:9200"]
    index => "redfire-logs-%{+YYYY.MM.dd}"
  }
}
```

### 自定义监控指标
```python
# 监控指标定义
from prometheus_client import Counter, Histogram, Gauge

# 交易订单计数器
ORDER_COUNTER = Counter('redfire_orders_total', 'Total number of orders', ['status', 'symbol'])

# API响应时间直方图
API_RESPONSE_TIME = Histogram('redfire_api_response_time_seconds', 'API response time', ['endpoint'])

# 系统状态指标
SYSTEM_STATUS = Gauge('redfire_system_status', 'System status indicator')

# 记录订单
def record_order(status: str, symbol: str):
    ORDER_COUNTER.labels(status=status, symbol=symbol).inc()

# 记录API响应时间
def record_api_time(endpoint: str, duration: float):
    API_RESPONSE_TIME.labels(endpoint=endpoint).observe(duration)
```

## 📊 告警配置

### 告警规则
```yaml
# alerting.yml 配置
groups:
  - name: redfire-alerts
    rules:
      - alert: HighCPUUsage
        expr: cpu_usage > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "CPU使用率过高"
          description: "CPU使用率超过80%持续5分钟"
      
      - alert: HighMemoryUsage
        expr: memory_usage > 85
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "内存使用率过高"
          description: "内存使用率超过85%持续5分钟"
      
      - alert: APISlowResponse
        expr: api_response_time > 2
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "API响应时间过长"
          description: "API响应时间超过2秒持续2分钟"
```

### 告警通知
```python
# 告警通知配置
class AlertNotifier:
    def __init__(self):
        self.webhook_url = os.getenv('ALERT_WEBHOOK_URL')
        self.email_config = self.load_email_config()
    
    def send_webhook(self, alert_data):
        """发送Webhook通知"""
        try:
            response = requests.post(
                self.webhook_url,
                json=alert_data,
                timeout=10
            )
            response.raise_for_status()
        except Exception as e:
            logger.error(f"Webhook通知发送失败: {e}")
    
    def send_email(self, alert_data):
        """发送邮件通知"""
        try:
            msg = MIMEText(alert_data['description'])
            msg['Subject'] = f"RedFire告警: {alert_data['summary']}"
            msg['From'] = self.email_config['from']
            msg['To'] = self.email_config['to']
            
            with smtplib.SMTP(self.email_config['smtp_server']) as server:
                server.login(self.email_config['username'], self.email_config['password'])
                server.send_message(msg)
        except Exception as e:
            logger.error(f"邮件通知发送失败: {e}")
```

## 🔧 运维脚本

### 健康检查脚本
```python
#!/usr/bin/env python3
"""系统健康检查脚本"""

import requests
import psutil
import redis
import psycopg2
import logging
from datetime import datetime

class HealthChecker:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.health_status = {}
    
    def check_system_health(self):
        """检查系统健康状态"""
        self.check_cpu_usage()
        self.check_memory_usage()
        self.check_disk_usage()
        self.check_network_status()
        
        return self.health_status
    
    def check_cpu_usage(self):
        """检查CPU使用率"""
        cpu_percent = psutil.cpu_percent(interval=1)
        self.health_status['cpu_usage'] = cpu_percent
        
        if cpu_percent > 80:
            self.logger.warning(f"CPU使用率过高: {cpu_percent}%")
    
    def check_memory_usage(self):
        """检查内存使用率"""
        memory = psutil.virtual_memory()
        self.health_status['memory_usage'] = memory.percent
        
        if memory.percent > 85:
            self.logger.warning(f"内存使用率过高: {memory.percent}%")
    
    def check_disk_usage(self):
        """检查磁盘使用率"""
        disk = psutil.disk_usage('/')
        self.health_status['disk_usage'] = disk.percent
        
        if disk.percent > 90:
            self.logger.warning(f"磁盘使用率过高: {disk.percent}%")
    
    def check_network_status(self):
        """检查网络状态"""
        try:
            # 检查网络连接
            response = requests.get('https://www.google.com', timeout=5)
            self.health_status['network_status'] = 'connected'
        except Exception as e:
            self.health_status['network_status'] = 'disconnected'
            self.logger.error(f"网络连接失败: {e}")

if __name__ == "__main__":
    checker = HealthChecker()
    status = checker.check_system_health()
    print(f"健康检查结果: {status}")
```

### 日志分析脚本
```python
#!/usr/bin/env python3
"""日志分析脚本"""

import re
import json
from collections import Counter
from datetime import datetime, timedelta

class LogAnalyzer:
    def __init__(self, log_file_path):
        self.log_file_path = log_file_path
        self.error_patterns = {
            'database_error': r'DatabaseError|ConnectionError',
            'api_error': r'APIError|HTTPError',
            'trading_error': r'TradingError|OrderError',
            'system_error': r'SystemError|RuntimeError'
        }
    
    def analyze_errors(self, hours=24):
        """分析指定时间范围内的错误"""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        
        error_counts = Counter()
        error_details = []
        
        with open(self.log_file_path, 'r') as f:
            for line in f:
                try:
                    # 解析日志时间
                    time_match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
                    if time_match:
                        log_time = datetime.strptime(time_match.group(1), '%Y-%m-%d %H:%M:%S')
                        
                        if start_time <= log_time <= end_time:
                            # 检查错误类型
                            for error_type, pattern in self.error_patterns.items():
                                if re.search(pattern, line, re.IGNORECASE):
                                    error_counts[error_type] += 1
                                    error_details.append({
                                        'time': log_time.isoformat(),
                                        'type': error_type,
                                        'message': line.strip()
                                    })
                except Exception as e:
                    continue
        
        return {
            'error_counts': dict(error_counts),
            'error_details': error_details,
            'total_errors': sum(error_counts.values())
        }
    
    def generate_report(self, hours=24):
        """生成错误分析报告"""
        analysis = self.analyze_errors(hours)
        
        report = f"""
RedFire系统错误分析报告
生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
分析范围: 最近{hours}小时
总错误数: {analysis['total_errors']}

错误类型统计:
"""
        
        for error_type, count in analysis['error_counts'].items():
            report += f"- {error_type}: {count}次\n"
        
        if analysis['error_details']:
            report += "\n详细错误信息:\n"
            for error in analysis['error_details'][:10]:  # 只显示前10个
                report += f"- {error['time']} [{error['type']}]: {error['message']}\n"
        
        return report

if __name__ == "__main__":
    analyzer = LogAnalyzer('/var/log/redfire/app.log')
    report = analyzer.generate_report(24)
    print(report)
```

## 🚨 故障处理

### 常见故障及解决方案

#### 1. 服务无法启动
```bash
# 检查服务状态
systemctl status redfire-backend

# 查看服务日志
journalctl -u redfire-backend -f

# 检查端口占用
netstat -tlnp | grep :8000

# 重启服务
systemctl restart redfire-backend
```

#### 2. 数据库连接失败
```bash
# 检查数据库服务状态
systemctl status postgresql

# 测试数据库连接
psql -h localhost -U redfire -d redfire -c "SELECT 1;"

# 检查数据库日志
tail -f /var/log/postgresql/postgresql-*.log

# 重启数据库服务
systemctl restart postgresql
```

#### 3. 内存不足
```bash
# 查看内存使用情况
free -h

# 查看内存占用进程
ps aux --sort=-%mem | head -10

# 清理缓存
echo 3 > /proc/sys/vm/drop_caches

# 重启高内存占用服务
systemctl restart redis
```

### 故障升级流程
1. **一级故障**: 运维人员处理
2. **二级故障**: 开发团队协助
3. **三级故障**: 架构师介入
4. **紧急故障**: 立即通知管理层

## 📈 性能优化

### 系统优化
```bash
# 优化内核参数
echo 'vm.swappiness=10' >> /etc/sysctl.conf
echo 'net.core.somaxconn=65535' >> /etc/sysctl.conf
sysctl -p

# 优化文件系统
echo 'noatime,nodiratime' >> /etc/fstab
mount -o remount /

# 优化网络参数
echo 'net.ipv4.tcp_fin_timeout=30' >> /etc/sysctl.conf
echo 'net.ipv4.tcp_keepalive_time=1200' >> /etc/sysctl.conf
```

### 应用优化
```python
# 数据库连接池优化
DATABASE_CONFIG = {
    'min_size': 5,
    'max_size': 20,
    'max_queries': 50000,
    'max_inactive_connection_lifetime': 300.0
}

# Redis连接池优化
REDIS_CONFIG = {
    'max_connections': 20,
    'retry_on_timeout': True,
    'socket_keepalive': True
}

# 异步任务优化
CELERY_CONFIG = {
    'worker_prefetch_multiplier': 1,
    'task_acks_late': True,
    'worker_max_tasks_per_child': 1000
}
```

## 📋 运维检查清单

### 日常检查
- [ ] 系统资源使用情况
- [ ] 服务运行状态
- [ ] 数据库连接状态
- [ ] 日志文件大小
- [ ] 磁盘空间使用

### 周期性检查
- [ ] 性能指标分析
- [ ] 错误日志分析
- [ ] 安全漏洞扫描
- [ ] 备份状态检查
- [ ] 监控告警测试

### 应急响应
- [ ] 故障快速定位
- [ ] 服务快速恢复
- [ ] 影响范围评估
- [ ] 用户通知发布
- [ ] 事后分析报告

---

*RedFire监控运维指南 - 保障系统稳定运行，提升运维效率* 🔥
