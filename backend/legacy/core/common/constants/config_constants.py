"""
配置常量定义
============

定义配置相关的常量
"""

# 配置文件路径
CONFIG_FILE_PATHS = {
    "development": "config/environments/development.py",
    "staging": "config/environments/staging.py", 
    "production": "config/environments/production.py",
    "testing": "config/environments/testing.py"
}

# 日志级别
LOG_LEVELS = {
    "DEBUG": 10,
    "INFO": 20,
    "WARNING": 30,
    "ERROR": 40,
    "CRITICAL": 50
}

# 数据库连接池配置
DATABASE_POOL_SIZES = {
    "development": {"min": 2, "max": 10},
    "staging": {"min": 5, "max": 20},
    "production": {"min": 10, "max": 50},
    "testing": {"min": 1, "max": 5}
}

# 缓存TTL配置
CACHE_TTL_VALUES = {
    "user_session": 3600,       # 1小时
    "market_data": 5,           # 5秒
    "strategy_config": 300,     # 5分钟
    "account_info": 60,         # 1分钟
    "system_config": 86400      # 24小时
}

# Redis配置
REDIS_CONFIG = {
    "development": {
        "host": "localhost",
        "port": 6379,
        "db": 0,
        "password": None,
        "socket_timeout": 5,
        "socket_connect_timeout": 5
    },
    "production": {
        "host": "redis-cluster",
        "port": 6379,
        "db": 0,
        "password": "${REDIS_PASSWORD}",
        "socket_timeout": 3,
        "socket_connect_timeout": 3
    }
}

# 数据库配置
DATABASE_CONFIG = {
    "development": {
        "driver": "mysql+aiomysql",
        "host": "localhost",
        "port": 3306,
        "database": "vnpy_web_dev",
        "username": "vnpy_dev",
        "password": "dev_password",
        "pool_size": 10,
        "max_overflow": 20,
        "pool_timeout": 30,
        "pool_recycle": 3600
    },
    "production": {
        "driver": "mysql+aiomysql",
        "host": "${DB_HOST}",
        "port": "${DB_PORT}",
        "database": "${DB_NAME}",
        "username": "${DB_USER}",
        "password": "${DB_PASSWORD}",
        "pool_size": 20,
        "max_overflow": 50,
        "pool_timeout": 30,
        "pool_recycle": 3600
    }
}

# 消息队列配置
MESSAGE_QUEUE_CONFIG = {
    "development": {
        "broker": "redis://localhost:6379/1",
        "backend": "redis://localhost:6379/2",
        "task_routes": {
            "strategy.*": {"queue": "strategy"},
            "market_data.*": {"queue": "market_data"},
            "risk.*": {"queue": "risk"}
        }
    },
    "production": {
        "broker": "redis://${REDIS_HOST}:${REDIS_PORT}/1",
        "backend": "redis://${REDIS_HOST}:${REDIS_PORT}/2",
        "task_routes": {
            "strategy.*": {"queue": "strategy"},
            "market_data.*": {"queue": "market_data"},
            "risk.*": {"queue": "risk"}
        }
    }
}

# 监控配置
MONITORING_CONFIG = {
    "metrics": {
        "collection_interval": 60,
        "retention_days": 30,
        "aggregation_intervals": [60, 300, 3600]  # 1min, 5min, 1hour
    },
    "alerts": {
        "cpu_threshold": 80,
        "memory_threshold": 85,
        "disk_threshold": 90,
        "response_time_threshold": 5000  # 5秒
    },
    "health_checks": {
        "interval": 30,
        "timeout": 5,
        "failure_threshold": 3
    }
}

# 安全配置
SECURITY_CONFIG = {
    "jwt": {
        "algorithm": "HS256",
        "access_token_expire_minutes": 60,
        "refresh_token_expire_days": 7
    },
    "password": {
        "min_length": 8,
        "require_uppercase": True,
        "require_lowercase": True,
        "require_numbers": True,
        "require_special_chars": True,
        "bcrypt_rounds": 12
    },
    "session": {
        "cookie_secure": True,
        "cookie_httponly": True,
        "cookie_samesite": "strict",
        "session_timeout": 3600
    }
}

# API配置
API_CONFIG = {
    "version": "v1",
    "title": "VnPy Web API",
    "description": "VnPy Web量化交易系统API",
    "docs_url": "/docs",
    "redoc_url": "/redoc",
    "cors": {
        "allow_origins": ["*"],
        "allow_credentials": True,
        "allow_methods": ["*"],
        "allow_headers": ["*"]
    },
    "rate_limiting": {
        "default": "100/minute",
        "authenticated": "1000/minute",
        "admin": "unlimited"
    }
}

# 文件存储配置
FILE_STORAGE_CONFIG = {
    "local": {
        "base_path": "./uploads",
        "max_file_size": 10 * 1024 * 1024,  # 10MB
        "allowed_extensions": [".csv", ".xlsx", ".json", ".txt"]
    },
    "s3": {
        "bucket": "${S3_BUCKET}",
        "region": "${S3_REGION}",
        "access_key": "${S3_ACCESS_KEY}",
        "secret_key": "${S3_SECRET_KEY}"
    }
}

# WebSocket配置
WEBSOCKET_CONFIG = {
    "max_connections": 1000,
    "heartbeat_interval": 30,
    "connection_timeout": 60,
    "message_size_limit": 1024 * 1024,  # 1MB
    "compression": True
}

# 外部服务配置
EXTERNAL_SERVICES = {
    "vnpy": {
        "timeout": 30,
        "retry_attempts": 3,
        "retry_delay": 1
    },
    "tushare": {
        "token": "${TUSHARE_TOKEN}",
        "timeout": 10,
        "rate_limit": "500/minute"
    },
    "akshare": {
        "timeout": 15,
        "retry_attempts": 2
    }
}

# 环境变量映射
ENVIRONMENT_VARIABLES = {
    "DB_HOST": "database.host",
    "DB_PORT": "database.port",
    "DB_NAME": "database.name",
    "DB_USER": "database.username",
    "DB_PASSWORD": "database.password",
    "REDIS_HOST": "redis.host",
    "REDIS_PORT": "redis.port",
    "REDIS_PASSWORD": "redis.password",
    "SECRET_KEY": "security.secret_key",
    "TUSHARE_TOKEN": "external_services.tushare.token"
}
