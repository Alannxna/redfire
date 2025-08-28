# Logs 模块介绍

## 🎯 概述

`logs` 是 RedFire 量化交易平台的日志管理模块，负责收集、存储和管理系统运行过程中的各种日志信息。该模块提供结构化的日志记录、日志分析和监控功能，确保系统的可观测性和问题排查能力。

## 📁 目录结构

```
logs/
├── access/                   # 🌐 访问日志
├── audit/                    # 🔍 审计日志
├── error/                    # ❌ 错误日志
└── application/              # 📝 应用日志
```

## 📝 日志分类详解

### 1. **访问日志** (`access/`)

**作用**: 记录用户访问和API调用信息

**记录内容**:
- HTTP请求日志
- API调用记录
- 用户访问统计
- 性能指标

**日志格式**:
```json
{
  "timestamp": "2024-01-01T10:00:00Z",
  "level": "INFO",
  "type": "access",
  "user_id": "user123",
  "ip_address": "192.168.1.100",
  "method": "POST",
  "path": "/api/orders",
  "status_code": 200,
  "response_time": 150,
  "user_agent": "Mozilla/5.0...",
  "request_size": 1024,
  "response_size": 512
}
```

### 2. **审计日志** (`audit/`)

**作用**: 记录系统操作和变更审计信息

**记录内容**:
- 用户操作记录
- 系统配置变更
- 权限变更
- 数据修改记录

**日志格式**:
```json
{
  "timestamp": "2024-01-01T10:00:00Z",
  "level": "INFO",
  "type": "audit",
  "user_id": "user123",
  "action": "CREATE_ORDER",
  "resource": "orders",
  "resource_id": "order456",
  "details": {
    "symbol": "AAPL",
    "quantity": 100,
    "price": 150.00
  },
  "ip_address": "192.168.1.100",
  "session_id": "session789"
}
```

### 3. **错误日志** (`error/`)

**作用**: 记录系统错误和异常信息

**记录内容**:
- 系统异常
- 业务错误
- 连接失败
- 性能问题

**日志格式**:
```json
{
  "timestamp": "2024-01-01T10:00:00Z",
  "level": "ERROR",
  "type": "error",
  "error_code": "DB_CONNECTION_FAILED",
  "error_message": "Database connection timeout",
  "stack_trace": "Traceback (most recent call last)...",
  "context": {
    "user_id": "user123",
    "request_id": "req456",
    "module": "database"
  },
  "severity": "HIGH"
}
```

### 4. **应用日志** (`application/`)

**作用**: 记录应用程序运行信息

**记录内容**:
- 应用启动/关闭
- 业务逻辑执行
- 性能监控
- 调试信息

**日志格式**:
```json
{
  "timestamp": "2024-01-01T10:00:00Z",
  "level": "INFO",
  "type": "application",
  "module": "trading_engine",
  "function": "process_order",
  "message": "Order processed successfully",
  "data": {
    "order_id": "order123",
    "processing_time": 50
  }
}
```

## 🔧 日志管理功能

### **1. 日志收集**

```python
class LogCollector:
    def __init__(self, config):
        self.config = config
        self.loggers = {}
    
    def setup_logger(self, name, log_type):
        """设置日志记录器"""
        logger = logging.getLogger(name)
        logger.setLevel(logging.INFO)
        
        # 文件处理器
        file_handler = logging.FileHandler(
            f"logs/{log_type}/{name}.log"
        )
        file_handler.setFormatter(self.get_formatter())
        logger.addHandler(file_handler)
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(self.get_formatter())
        logger.addHandler(console_handler)
        
        self.loggers[name] = logger
        return logger
    
    def get_formatter(self):
        """获取日志格式器"""
        return logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def log_access(self, request, response, response_time):
        """记录访问日志"""
        logger = self.loggers.get('access')
        if logger:
            log_data = {
                'timestamp': datetime.now().isoformat(),
                'user_id': request.user.id if hasattr(request, 'user') else None,
                'ip_address': request.client.host,
                'method': request.method,
                'path': request.url.path,
                'status_code': response.status_code,
                'response_time': response_time,
                'user_agent': request.headers.get('user-agent')
            }
            logger.info(json.dumps(log_data))
    
    def log_audit(self, user_id, action, resource, details):
        """记录审计日志"""
        logger = self.loggers.get('audit')
        if logger:
            log_data = {
                'timestamp': datetime.now().isoformat(),
                'user_id': user_id,
                'action': action,
                'resource': resource,
                'details': details
            }
            logger.info(json.dumps(log_data))
    
    def log_error(self, error, context=None):
        """记录错误日志"""
        logger = self.loggers.get('error')
        if logger:
            log_data = {
                'timestamp': datetime.now().isoformat(),
                'error_code': getattr(error, 'code', 'UNKNOWN'),
                'error_message': str(error),
                'stack_trace': traceback.format_exc(),
                'context': context or {}
            }
            logger.error(json.dumps(log_data))
```

### **2. 日志分析**

```python
class LogAnalyzer:
    def __init__(self, logs_path):
        self.logs_path = logs_path
    
    def analyze_access_patterns(self, start_time, end_time):
        """分析访问模式"""
        access_logs = self.load_logs('access', start_time, end_time)
        
        analysis = {
            'total_requests': len(access_logs),
            'unique_users': len(set(log['user_id'] for log in access_logs if log['user_id'])),
            'top_endpoints': self.get_top_endpoints(access_logs),
            'response_time_stats': self.get_response_time_stats(access_logs),
            'error_rate': self.calculate_error_rate(access_logs)
        }
        
        return analysis
    
    def analyze_error_patterns(self, start_time, end_time):
        """分析错误模式"""
        error_logs = self.load_logs('error', start_time, end_time)
        
        analysis = {
            'total_errors': len(error_logs),
            'error_types': self.group_by_error_type(error_logs),
            'most_frequent_errors': self.get_most_frequent_errors(error_logs),
            'error_trends': self.get_error_trends(error_logs)
        }
        
        return analysis
    
    def analyze_user_activity(self, user_id, start_time, end_time):
        """分析用户活动"""
        access_logs = self.load_logs('access', start_time, end_time)
        user_logs = [log for log in access_logs if log.get('user_id') == user_id]
        
        analysis = {
            'total_actions': len(user_logs),
            'action_types': self.group_by_action_type(user_logs),
            'peak_activity_hours': self.get_peak_activity_hours(user_logs),
            'frequently_accessed_resources': self.get_frequent_resources(user_logs)
        }
        
        return analysis
```

### **3. 日志监控**

```python
class LogMonitor:
    def __init__(self, alert_config):
        self.alert_config = alert_config
        self.alert_handlers = []
    
    def add_alert_handler(self, handler):
        """添加告警处理器"""
        self.alert_handlers.append(handler)
    
    def monitor_error_rate(self, threshold=0.05):
        """监控错误率"""
        current_error_rate = self.calculate_current_error_rate()
        
        if current_error_rate > threshold:
            alert = {
                'type': 'ERROR_RATE_HIGH',
                'message': f'Error rate {current_error_rate:.2%} exceeds threshold {threshold:.2%}',
                'severity': 'HIGH',
                'timestamp': datetime.now()
            }
            self.send_alert(alert)
    
    def monitor_response_time(self, threshold=1000):
        """监控响应时间"""
        current_avg_response_time = self.calculate_avg_response_time()
        
        if current_avg_response_time > threshold:
            alert = {
                'type': 'RESPONSE_TIME_HIGH',
                'message': f'Average response time {current_avg_response_time}ms exceeds threshold {threshold}ms',
                'severity': 'MEDIUM',
                'timestamp': datetime.now()
            }
            self.send_alert(alert)
    
    def monitor_unusual_activity(self):
        """监控异常活动"""
        unusual_patterns = self.detect_unusual_patterns()
        
        for pattern in unusual_patterns:
            alert = {
                'type': 'UNUSUAL_ACTIVITY',
                'message': f'Detected unusual activity: {pattern["description"]}',
                'severity': 'LOW',
                'timestamp': datetime.now(),
                'details': pattern
            }
            self.send_alert(alert)
    
    def send_alert(self, alert):
        """发送告警"""
        for handler in self.alert_handlers:
            handler.handle_alert(alert)
```

## 📊 日志存储和检索

### **1. 日志存储**

```python
class LogStorage:
    def __init__(self, storage_config):
        self.storage_config = storage_config
        self.storage_backend = self.create_storage_backend()
    
    def create_storage_backend(self):
        """创建存储后端"""
        if self.storage_config['type'] == 'elasticsearch':
            return ElasticsearchStorage(self.storage_config)
        elif self.storage_config['type'] == 'file':
            return FileStorage(self.storage_config)
        else:
            raise ValueError(f"Unsupported storage type: {self.storage_config['type']}")
    
    def store_log(self, log_data):
        """存储日志"""
        return self.storage_backend.store(log_data)
    
    def search_logs(self, query, start_time=None, end_time=None, limit=100):
        """搜索日志"""
        return self.storage_backend.search(query, start_time, end_time, limit)
    
    def get_log_statistics(self, start_time, end_time):
        """获取日志统计"""
        return self.storage_backend.get_statistics(start_time, end_time)
```

### **2. 日志检索**

```python
class LogRetriever:
    def __init__(self, storage):
        self.storage = storage
    
    def search_by_user(self, user_id, start_time=None, end_time=None):
        """按用户搜索日志"""
        query = {'user_id': user_id}
        return self.storage.search_logs(query, start_time, end_time)
    
    def search_by_error_type(self, error_type, start_time=None, end_time=None):
        """按错误类型搜索日志"""
        query = {'error_code': error_type}
        return self.storage.search_logs(query, start_time, end_time)
    
    def search_by_time_range(self, start_time, end_time):
        """按时间范围搜索日志"""
        return self.storage.search_logs({}, start_time, end_time)
    
    def search_by_keyword(self, keyword, start_time=None, end_time=None):
        """按关键词搜索日志"""
        query = {'message': {'$regex': keyword, '$options': 'i'}}
        return self.storage.search_logs(query, start_time, end_time)
```

## 🔍 日志可视化

### **1. 实时监控面板**

```python
class LogDashboard:
    def __init__(self, log_analyzer):
        self.log_analyzer = log_analyzer
    
    def get_real_time_metrics(self):
        """获取实时指标"""
        now = datetime.now()
        start_time = now - timedelta(hours=1)
        
        return {
            'requests_per_minute': self.calculate_requests_per_minute(start_time, now),
            'error_rate': self.calculate_error_rate(start_time, now),
            'average_response_time': self.calculate_avg_response_time(start_time, now),
            'active_users': self.calculate_active_users(start_time, now)
        }
    
    def get_trend_chart_data(self, metric, hours=24):
        """获取趋势图表数据"""
        now = datetime.now()
        start_time = now - timedelta(hours=hours)
        
        data_points = []
        for i in range(hours):
            point_time = start_time + timedelta(hours=i)
            value = self.get_metric_value(metric, point_time)
            data_points.append({
                'timestamp': point_time.isoformat(),
                'value': value
            })
        
        return data_points
```

### **2. 日志报表**

```python
class LogReporter:
    def __init__(self, log_analyzer):
        self.log_analyzer = log_analyzer
    
    def generate_daily_report(self, date):
        """生成日报"""
        start_time = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(days=1)
        
        report = {
            'date': date.date().isoformat(),
            'summary': self.get_daily_summary(start_time, end_time),
            'access_analysis': self.log_analyzer.analyze_access_patterns(start_time, end_time),
            'error_analysis': self.log_analyzer.analyze_error_patterns(start_time, end_time),
            'top_users': self.get_top_users(start_time, end_time),
            'performance_metrics': self.get_performance_metrics(start_time, end_time)
        }
        
        return report
    
    def generate_weekly_report(self, week_start):
        """生成周报"""
        end_time = week_start + timedelta(weeks=1)
        
        report = {
            'week_start': week_start.date().isoformat(),
            'summary': self.get_weekly_summary(week_start, end_time),
            'trends': self.get_weekly_trends(week_start, end_time),
            'comparison': self.compare_with_previous_week(week_start, end_time)
        }
        
        return report
```

## 🛡️ 日志安全

### **1. 敏感信息过滤**

```python
class LogSanitizer:
    def __init__(self, sensitive_fields):
        self.sensitive_fields = sensitive_fields
    
    def sanitize_log_data(self, log_data):
        """清理日志数据中的敏感信息"""
        sanitized_data = log_data.copy()
        
        for field in self.sensitive_fields:
            if field in sanitized_data:
                sanitized_data[field] = '***REDACTED***'
        
        return sanitized_data
    
    def mask_password(self, text):
        """掩码密码"""
        import re
        return re.sub(r'password["\']?\s*[:=]\s*["\']?[^"\s]+["\']?', 
                     'password="***REDACTED***"', text, flags=re.IGNORECASE)
```

### **2. 日志加密**

```python
class LogEncryption:
    def __init__(self, encryption_key):
        self.encryption_key = encryption_key
    
    def encrypt_log(self, log_data):
        """加密日志数据"""
        from cryptography.fernet import Fernet
        
        cipher = Fernet(self.encryption_key)
        encrypted_data = cipher.encrypt(json.dumps(log_data).encode())
        return encrypted_data
    
    def decrypt_log(self, encrypted_data):
        """解密日志数据"""
        from cryptography.fernet import Fernet
        
        cipher = Fernet(self.encryption_key)
        decrypted_data = cipher.decrypt(encrypted_data)
        return json.loads(decrypted_data.decode())
```

## 📈 日志性能优化

### **1. 日志轮转**

```python
class LogRotator:
    def __init__(self, config):
        self.config = config
    
    def rotate_logs(self):
        """轮转日志文件"""
        for log_type in ['access', 'audit', 'error', 'application']:
            log_dir = f"logs/{log_type}"
            self.rotate_log_directory(log_dir)
    
    def rotate_log_directory(self, log_dir):
        """轮转指定目录的日志"""
        import os
        import shutil
        
        for filename in os.listdir(log_dir):
            if filename.endswith('.log'):
                file_path = os.path.join(log_dir, filename)
                file_size = os.path.getsize(file_path)
                
                if file_size > self.config['max_file_size']:
                    # 创建备份文件
                    backup_name = f"{filename}.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    backup_path = os.path.join(log_dir, backup_name)
                    shutil.move(file_path, backup_path)
                    
                    # 压缩备份文件
                    self.compress_file(backup_path)
```

### **2. 日志压缩**

```python
class LogCompressor:
    def compress_file(self, file_path):
        """压缩文件"""
        import gzip
        
        with open(file_path, 'rb') as f_in:
            with gzip.open(f"{file_path}.gz", 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        # 删除原文件
        os.remove(file_path)
    
    def decompress_file(self, compressed_path):
        """解压文件"""
        import gzip
        
        with gzip.open(compressed_path, 'rb') as f_in:
            with open(compressed_path[:-3], 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
```

---

**总结**: Logs模块提供了完整的日志管理解决方案，包括日志收集、存储、分析、监控和可视化功能。通过结构化的日志记录和强大的分析工具，确保系统的可观测性和问题排查能力，为系统运维和性能优化提供重要支持。
