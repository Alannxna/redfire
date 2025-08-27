# RedFire 数据库系统部署指南

## 🚀 快速部署

### 方式一：基于现有数据库（推荐）

如果您已经有运行的MySQL和Redis服务：

```bash
# 1. 进入项目目录
cd backend/core/database

# 2. 复制环境配置
cp .env.database .env

# 3. 编辑配置文件，设置您的数据库连接信息
# DB_HOST=localhost
# DB_PORT=3306
# DB_USER=root
# DB_PASSWORD=root
# DB_NAME=vnpy

# 4. 运行快速启动测试
python quick_start.py
```

### 方式二：Docker一键部署

如果需要完整的数据库环境：

```bash
# 1. 确保Docker和Docker Compose已安装
docker --version
docker-compose --version

# 2. 启动所有数据库服务
python scripts/start_databases.py start

# 3. 查看服务状态
python scripts/start_databases.py status

# 4. 访问管理界面
# MySQL管理: http://localhost:8080
# Redis管理: http://localhost:8081
# MongoDB管理: http://localhost:8082
# InfluxDB: http://localhost:8086
```

## 📋 系统要求

### 最小配置
- Python 3.8+
- MySQL 5.7+ 或 8.0+
- Redis 5.0+
- 内存: 2GB+
- 存储: 10GB+

### 推荐配置
- Python 3.10+
- MySQL 8.0+
- Redis 7.0+
- 内存: 8GB+
- 存储: 50GB+
- SSD存储

## 🔧 配置说明

### 环境变量配置

创建 `.env` 文件并配置：

```env
# =====基础数据库配置=====
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=vnpy

# 连接池优化
DB_POOL_SIZE=15
DB_MAX_OVERFLOW=30
DB_POOL_TIMEOUT=20

# =====Redis缓存配置=====
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_MAX_CONNECTIONS=20

# =====读写分离配置（可选）=====
DB_SLAVE_HOST=slave-host
DB_SLAVE_PORT=3306
DB_SLAVE_USER=readonly
DB_SLAVE_PASSWORD=readonly_password

# =====时序数据库配置（可选）=====
INFLUX_HOST=localhost
INFLUX_PORT=8086
INFLUX_TOKEN=your-token
INFLUX_ORG=redfire
INFLUX_BUCKET=trading_data

# =====日志存储配置（可选）=====
MONGO_HOST=localhost
MONGO_PORT=27017
MONGO_USER=admin
MONGO_PASSWORD=admin_password
MONGO_DATABASE=redfire_logs
```

## 📦 安装依赖

```bash
# 安装核心依赖
pip install sqlalchemy>=2.0.0
pip install PyMySQL>=1.1.0
pip install redis>=5.0.0

# 安装异步支持
pip install aiomysql>=0.2.0
pip install motor>=3.3.0

# 安装可选组件
pip install influxdb-client>=1.38.0  # InfluxDB支持
pip install pymongo>=4.5.0           # MongoDB支持

# 或者安装完整依赖
pip install -r requirements.txt
```

## 🗄️ 数据库初始化

### 自动初始化

```python
from backend.core.database import initialize_databases

# 自动创建表结构、索引和初始数据
success = initialize_databases()
if success:
    print("✅ 数据库初始化成功")
```

### 手动初始化

如果需要自定义初始化：

```sql
-- 1. 创建数据库
CREATE DATABASE vnpy CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 2. 创建用户
CREATE USER 'redfire'@'%' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON vnpy.* TO 'redfire'@'%';

-- 3. 运行初始化脚本
SOURCE backend/core/database/mysql/init.sql;
```

## 🔄 读写分离配置

### 1. MySQL主从配置

**主库配置 (my.cnf):**
```ini
[mysqld]
server-id = 1
log-bin = mysql-bin
binlog-format = ROW
```

**从库配置 (my.cnf):**
```ini
[mysqld]
server-id = 2
read-only = 1
super-read-only = 1
```

### 2. 应用配置

```env
# 主库（写操作）
DB_MASTER_HOST=master-host
DB_MASTER_PORT=3306
DB_MASTER_USER=root
DB_MASTER_PASSWORD=master_password

# 从库（读操作）
DB_SLAVE_HOST=slave-host
DB_SLAVE_PORT=3306
DB_SLAVE_USER=readonly
DB_SLAVE_PASSWORD=slave_password
```

## 📊 性能优化

### MySQL优化

```sql
-- 连接数优化
SET GLOBAL max_connections = 200;
SET GLOBAL thread_cache_size = 16;

-- 缓冲区优化
SET GLOBAL innodb_buffer_pool_size = 256M;
SET GLOBAL key_buffer_size = 32M;

-- 查询缓存
SET GLOBAL query_cache_type = 1;
SET GLOBAL query_cache_size = 32M;
```

### Redis优化

```conf
# 内存优化
maxmemory 256mb
maxmemory-policy allkeys-lru

# 持久化优化
save 900 1
save 300 10
save 60 10000
```

### 应用层优化

```python
# 连接池配置
DB_POOL_SIZE = 15          # 基础连接数
DB_MAX_OVERFLOW = 30       # 最大溢出连接
DB_POOL_TIMEOUT = 20       # 连接超时
DB_POOL_RECYCLE = 1800     # 连接回收时间

# 缓存配置
REDIS_MAX_CONNECTIONS = 20 # Redis最大连接数
CACHE_DEFAULT_TTL = 3600   # 默认缓存时间
```

## 🔍 监控和诊断

### 1. 健康检查

```python
from backend.core.database import get_database_manager

db_manager = get_database_manager()

# 测试所有连接
health_status = db_manager.test_all_connections()
print(health_status)

# 获取连接池状态
stats = db_manager.get_all_stats()
print(stats)
```

### 2. 性能监控

```python
# 缓存命中率
cache_stats = cache_manager.get_stats()
print(f"缓存命中率: {cache_stats['hit_rate']}")

# 读写分离统计
rw_stats = rw_manager.get_all_stats()
print(f"读请求: {rw_stats['read_queries']}")
print(f"写请求: {rw_stats['write_queries']}")
```

### 3. 日志监控

```bash
# MySQL慢查询日志
tail -f /var/log/mysql/slow.log

# Redis日志
tail -f /var/log/redis/redis.log

# 应用日志
tail -f logs/database.log
```

## 🚨 故障排除

### 常见问题

**1. MySQL连接失败**
```
错误: Can't connect to MySQL server
解决: 
- 检查MySQL服务状态: systemctl status mysql
- 检查端口占用: netstat -tlnp | grep 3306
- 检查防火墙: ufw status
- 验证用户权限: SHOW GRANTS FOR 'root'@'%';
```

**2. Redis连接超时**
```
错误: Redis connection timeout
解决:
- 检查Redis服务: systemctl status redis
- 检查配置文件: /etc/redis/redis.conf
- 测试连接: redis-cli ping
```

**3. 连接池耗尽**
```
错误: QueuePool limit exceeded
解决:
- 增加连接池大小: DB_POOL_SIZE=25
- 检查连接泄漏: 确保使用with语句
- 监控活跃连接数
```

**4. 字符集问题**
```
错误: Incorrect string value
解决:
- 确保数据库字符集: ALTER DATABASE vnpy CHARACTER SET utf8mb4;
- 检查表字符集: SHOW CREATE TABLE users;
- 验证连接字符集: SHOW VARIABLES LIKE 'character%';
```

### 诊断命令

```bash
# 检查数据库连接
python -c "from backend.core.database import get_config_manager; print(get_config_manager().test_mysql_connection())"

# 检查Redis连接
python -c "from backend.core.database import get_config_manager; print(get_config_manager().test_redis_connection())"

# 运行完整测试
python backend/core/database/quick_start.py

# 查看详细错误
python backend/core/database/test_database_system.py
```

## 📈 扩展配置

### 高可用配置

```yaml
# docker-compose.ha.yml
version: '3.8'
services:
  mysql-master:
    image: mysql:8.0
    # ... 主库配置
    
  mysql-slave-1:
    image: mysql:8.0
    # ... 从库1配置
    
  mysql-slave-2:
    image: mysql:8.0
    # ... 从库2配置
    
  redis-sentinel-1:
    image: redis:7-alpine
    # ... 哨兵配置
```

### 集群配置

```python
# 多Redis节点
REDIS_CLUSTER_NODES = [
    {"host": "redis-1", "port": 6379},
    {"host": "redis-2", "port": 6379},
    {"host": "redis-3", "port": 6379},
]

# 多InfluxDB节点
INFLUX_CLUSTER_URLS = [
    "http://influx-1:8086",
    "http://influx-2:8086",
]
```

## 🔒 安全配置

### 1. 数据库安全

```sql
-- 创建专用用户
CREATE USER 'redfire_app'@'%' IDENTIFIED BY 'strong_password';
GRANT SELECT, INSERT, UPDATE, DELETE ON vnpy.* TO 'redfire_app'@'%';

-- 只读用户
CREATE USER 'redfire_readonly'@'%' IDENTIFIED BY 'readonly_password';
GRANT SELECT ON vnpy.* TO 'redfire_readonly'@'%';
```

### 2. Redis安全

```conf
# 启用认证
requirepass your_strong_password

# 禁用危险命令
rename-command FLUSHDB ""
rename-command FLUSHALL ""
rename-command CONFIG "CONFIG_b8c2f3d4e5f6"
```

### 3. 网络安全

```bash
# 防火墙配置
ufw allow from 192.168.1.0/24 to any port 3306
ufw allow from 192.168.1.0/24 to any port 6379

# SSL/TLS配置
DB_SSL_DISABLED=false
DB_SSL_CA=/path/to/ca.pem
DB_SSL_CERT=/path/to/cert.pem
```

## 📝 维护指南

### 定期维护任务

```bash
# 1. 数据库优化
mysqlcheck -u root -p --optimize --all-databases

# 2. 清理日志
python -c "
from backend.core.database import get_log_manager
import asyncio
asyncio.run(get_log_manager().cleanup_old_logs(30))
"

# 3. 备份数据
mysqldump -u root -p vnpy > backup_$(date +%Y%m%d).sql

# 4. 监控磁盘空间
df -h
```

### 性能调优

```sql
-- 查看慢查询
SELECT * FROM mysql.slow_log ORDER BY start_time DESC LIMIT 10;

-- 分析表使用情况
SELECT table_schema, table_name, 
       ROUND(data_length/1024/1024, 2) AS data_mb,
       ROUND(index_length/1024/1024, 2) AS index_mb
FROM information_schema.tables 
WHERE table_schema = 'vnpy'
ORDER BY data_length DESC;

-- 优化表
OPTIMIZE TABLE users, trading_orders, positions;
```

## 🆘 技术支持

### 获取帮助

1. **查看日志**: `tail -f logs/database.log`
2. **运行诊断**: `python quick_start.py`
3. **检查配置**: `python -c "from backend.core.database import get_database_status; print(get_database_status())"`
4. **性能分析**: `python usage_examples.py`

### 联系方式

- 项目文档: `backend/core/database/README.md`
- 使用示例: `backend/core/database/usage_examples.py`
- 测试套件: `backend/core/database/test_database_system.py`

---

**RedFire数据库系统** - 企业级量化交易数据库解决方案 🚀
