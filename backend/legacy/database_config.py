# RedFire 数据库配置
# 数据库类型: mysql 或 sqlite
DATABASE_TYPE = "mysql"

# MySQL配置
MYSQL_HOST = "localhost"
MYSQL_PORT = 3306
MYSQL_DATABASE = "vnpy"
MYSQL_USERNAME = "root"
MYSQL_PASSWORD = "root"

# SQLite配置（备用）
SQLITE_DATABASE = "redfire.db"

# 连接池配置
DATABASE_POOL_SIZE = 10
DATABASE_MAX_OVERFLOW = 20
DATABASE_POOL_TIMEOUT = 30

# 其他配置
DATABASE_ECHO = false  # 是否显示SQL语句
DATABASE_AUTOCOMMIT = true
