"""
优化的数据库配置管理
==================

针对RedFire量化交易平台的数据库配置优化
包括连接池优化、字符集配置、性能调优等
"""

import os
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


@dataclass
class OptimizedDatabaseConfig:
    """优化的数据库配置"""
    
    # 基础连接配置
    host: str = "localhost"
    port: int = 3306
    username: str = "root"
    password: str = "root"
    database: str = "vnpy"
    
    # 连接池优化配置
    pool_size: int = 15  # 增加基础连接池大小
    max_overflow: int = 30  # 增加溢出连接数
    pool_timeout: int = 20  # 减少超时时间，快速失败
    pool_recycle: int = 1800  # 30分钟回收连接，防止连接过期
    pool_pre_ping: bool = True  # 启用连接前ping检查
    
    # MySQL特定优化
    charset: str = "utf8mb4"
    collation: str = "utf8mb4_unicode_ci"
    sql_mode: str = "STRICT_TRANS_TABLES,NO_ZERO_DATE,NO_ZERO_IN_DATE,ERROR_FOR_DIVISION_BY_ZERO"
    isolation_level: str = "READ_COMMITTED"
    timezone: str = "+08:00"
    
    # 性能优化参数
    autocommit: bool = False
    echo: bool = False  # 生产环境关闭SQL日志
    echo_pool: bool = False  # 关闭连接池日志
    
    # SSL配置
    ssl_disabled: bool = True  # 本地开发禁用SSL
    ssl_ca: Optional[str] = None
    ssl_cert: Optional[str] = None
    ssl_key: Optional[str] = None
    
    # 连接参数优化
    connect_timeout: int = 10  # 连接超时
    read_timeout: int = 30  # 读取超时
    write_timeout: int = 30  # 写入超时
    
    # 额外的MySQL参数
    extra_mysql_args: Dict[str, Any] = field(default_factory=lambda: {
        # 网络优化
        "net_read_timeout": 30,
        "net_write_timeout": 30,
        "wait_timeout": 28800,  # 8小时
        "interactive_timeout": 28800,
        
        # 缓冲区优化
        "max_allowed_packet": "64M",
        "innodb_buffer_pool_size": "256M",
        
        # 事务优化
        "innodb_flush_log_at_trx_commit": 2,  # 性能优化，每秒刷新日志
        "innodb_log_buffer_size": "16M",
        
        # 查询缓存（MySQL 5.7及以下）
        "query_cache_type": "ON",
        "query_cache_size": "32M",
    })
    
    def build_connection_url(self, async_mode: bool = False) -> str:
        """构建优化的数据库连接URL"""
        driver = "mysql+aiomysql" if async_mode else "mysql+pymysql"
        
        # URL编码密码中的特殊字符
        from urllib.parse import quote_plus
        encoded_password = quote_plus(self.password)
        
        # 构建基础URL
        url = f"{driver}://{self.username}:{encoded_password}@{self.host}:{self.port}/{self.database}"
        
        # 添加优化参数
        params = [
            f"charset={self.charset}",
            f"collation={self.collation}",
            "autocommit=false",
            f"connect_timeout={self.connect_timeout}",
            f"read_timeout={self.read_timeout}",
            f"write_timeout={self.write_timeout}"
        ]
        
        if self.ssl_disabled:
            params.append("ssl_disabled=true")
        
        # 添加时区参数
        params.append("init_command=SET sql_mode=%27" + self.sql_mode + "%27")
        
        return f"{url}?{'&'.join(params)}"
    
    def get_engine_kwargs(self) -> Dict[str, Any]:
        """获取SQLAlchemy引擎参数"""
        connect_args = {
            "charset": self.charset,
            "autocommit": self.autocommit,
            "connect_timeout": self.connect_timeout,
            "read_timeout": self.read_timeout,
            "write_timeout": self.write_timeout,
            "sql_mode": self.sql_mode,
            "init_command": f"SET NAMES {self.charset} COLLATE {self.collation}; SET time_zone = '{self.timezone}'; SET SESSION TRANSACTION ISOLATION LEVEL {self.isolation_level};"
        }
        
        if self.ssl_disabled:
            connect_args["ssl_disabled"] = True
        
        return {
            "pool_size": self.pool_size,
            "max_overflow": self.max_overflow,
            "pool_timeout": self.pool_timeout,
            "pool_recycle": self.pool_recycle,
            "pool_pre_ping": self.pool_pre_ping,
            "echo": self.echo,
            "echo_pool": self.echo_pool,
            "connect_args": connect_args,
            "execution_options": {
                "isolation_level": self.isolation_level,
                "autocommit": self.autocommit
            }
        }
    
    @classmethod
    def from_current_config(cls) -> "OptimizedDatabaseConfig":
        """基于当前用户配置创建优化配置"""
        return cls(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", "3306")),
            username=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", "root"),
            database=os.getenv("DB_NAME", "vnpy"),
            
            # 应用优化配置
            pool_size=int(os.getenv("DB_POOL_SIZE", "15")),
            max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "30")),
            pool_timeout=int(os.getenv("DB_POOL_TIMEOUT", "20")),
            pool_recycle=int(os.getenv("DB_POOL_RECYCLE", "1800")),
            
            echo=os.getenv("DB_ECHO", "false").lower() == "true"
        )
    
    def validate_config(self) -> bool:
        """验证配置有效性"""
        try:
            # 检查必需参数
            if not all([self.host, self.username, self.password, self.database]):
                logger.error("数据库连接参数不完整")
                return False
            
            # 检查端口范围
            if not (1 <= self.port <= 65535):
                logger.error(f"数据库端口无效: {self.port}")
                return False
            
            # 检查连接池配置
            if self.pool_size <= 0 or self.max_overflow < 0:
                logger.error("连接池配置无效")
                return False
            
            logger.info("数据库配置验证通过")
            return True
            
        except Exception as e:
            logger.error(f"数据库配置验证失败: {e}")
            return False
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "host": self.host,
            "port": self.port,
            "username": self.username,
            "password": "***",  # 隐藏密码
            "database": self.database,
            "pool_size": self.pool_size,
            "max_overflow": self.max_overflow,
            "pool_timeout": self.pool_timeout,
            "pool_recycle": self.pool_recycle,
            "charset": self.charset,
            "timezone": self.timezone,
            "ssl_disabled": self.ssl_disabled
        }


@dataclass
class RedisOptimizedConfig:
    """优化的Redis配置"""
    
    host: str = "localhost"
    port: int = 6379
    password: Optional[str] = None
    db: int = 0
    
    # 连接池优化
    max_connections: int = 20
    connection_pool_kwargs: Dict[str, Any] = field(default_factory=lambda: {
        "retry_on_timeout": True,
        "health_check_interval": 30,
        "socket_timeout": 5,
        "socket_connect_timeout": 5,
        "socket_keepalive": True,
        "socket_keepalive_options": {}
    })
    
    # 缓存策略配置
    default_ttl: int = 3600  # 1小时默认过期时间
    max_ttl: int = 86400  # 最大24小时
    
    # 序列化配置
    decode_responses: bool = True
    encoding: str = "utf-8"
    
    def build_url(self) -> str:
        """构建Redis连接URL"""
        password_part = f":{self.password}@" if self.password else ""
        return f"redis://{password_part}{self.host}:{self.port}/{self.db}"
    
    def get_connection_kwargs(self) -> Dict[str, Any]:
        """获取Redis连接参数"""
        return {
            "host": self.host,
            "port": self.port,
            "password": self.password,
            "db": self.db,
            "decode_responses": self.decode_responses,
            "encoding": self.encoding,
            "max_connections": self.max_connections,
            **self.connection_pool_kwargs
        }
    
    @classmethod
    def from_env(cls) -> "RedisOptimizedConfig":
        """从环境变量创建Redis配置"""
        return cls(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", "6379")),
            password=os.getenv("REDIS_PASSWORD"),
            db=int(os.getenv("REDIS_DB", "0")),
            max_connections=int(os.getenv("REDIS_MAX_CONNECTIONS", "20"))
        )


class DatabaseConfigManager:
    """数据库配置管理器"""
    
    def __init__(self):
        self._mysql_config: Optional[OptimizedDatabaseConfig] = None
        self._redis_config: Optional[RedisOptimizedConfig] = None
        self._config_loaded = False
    
    def load_configs(self):
        """加载所有数据库配置"""
        if self._config_loaded:
            return
        
        try:
            # 加载MySQL配置
            self._mysql_config = OptimizedDatabaseConfig.from_current_config()
            if not self._mysql_config.validate_config():
                raise ValueError("MySQL配置验证失败")
            
            # 加载Redis配置
            self._redis_config = RedisOptimizedConfig.from_env()
            
            self._config_loaded = True
            logger.info("数据库配置加载完成")
            
        except Exception as e:
            logger.error(f"数据库配置加载失败: {e}")
            raise
    
    @property
    def mysql_config(self) -> OptimizedDatabaseConfig:
        """获取MySQL配置"""
        if not self._config_loaded:
            self.load_configs()
        return self._mysql_config
    
    @property
    def redis_config(self) -> RedisOptimizedConfig:
        """获取Redis配置"""
        if not self._config_loaded:
            self.load_configs()
        return self._redis_config
    
    def get_mysql_url(self, async_mode: bool = False) -> str:
        """获取MySQL连接URL"""
        return self.mysql_config.build_connection_url(async_mode)
    
    def get_redis_url(self) -> str:
        """获取Redis连接URL"""
        return self.redis_config.build_url()
    
    def test_mysql_connection(self) -> bool:
        """测试MySQL连接"""
        try:
            from sqlalchemy import create_engine, text
            
            url = self.get_mysql_url()
            engine_kwargs = self.mysql_config.get_engine_kwargs()
            
            # 创建测试引擎
            engine = create_engine(url, **engine_kwargs)
            
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            engine.dispose()
            logger.info("MySQL连接测试成功")
            return True
            
        except Exception as e:
            logger.error(f"MySQL连接测试失败: {e}")
            return False
    
    def test_redis_connection(self) -> bool:
        """测试Redis连接"""
        try:
            import redis
            
            conn_kwargs = self.redis_config.get_connection_kwargs()
            redis_client = redis.Redis(**conn_kwargs)
            
            redis_client.ping()
            redis_client.close()
            
            logger.info("Redis连接测试成功")
            return True
            
        except Exception as e:
            logger.error(f"Redis连接测试失败: {e}")
            return False
    
    def get_config_summary(self) -> Dict[str, Any]:
        """获取配置摘要"""
        return {
            "mysql": self.mysql_config.to_dict(),
            "redis": {
                "host": self.redis_config.host,
                "port": self.redis_config.port,
                "db": self.redis_config.db,
                "max_connections": self.redis_config.max_connections
            }
        }


# 全局配置管理器实例
_config_manager: Optional[DatabaseConfigManager] = None


def get_config_manager() -> DatabaseConfigManager:
    """获取全局配置管理器"""
    global _config_manager
    if _config_manager is None:
        _config_manager = DatabaseConfigManager()
    return _config_manager


def get_optimized_mysql_config() -> OptimizedDatabaseConfig:
    """获取优化的MySQL配置"""
    return get_config_manager().mysql_config


def get_optimized_redis_config() -> RedisOptimizedConfig:
    """获取优化的Redis配置"""
    return get_config_manager().redis_config
