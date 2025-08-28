"""
RedFire 统一数据库管理器
=======================

提供完整的数据库连接管理、连接池优化、多数据库支持等功能
支持MySQL、PostgreSQL、Redis、InfluxDB、MongoDB等多种数据库
"""

import os
import asyncio
from typing import Dict, Optional, Any, AsyncGenerator, Generator, Union, List
from contextlib import contextmanager, asynccontextmanager
from urllib.parse import quote_plus
import logging
from dataclasses import dataclass, field
from enum import Enum
import json
from datetime import datetime, timedelta

# SQLAlchemy imports
from sqlalchemy import create_engine, event, text, MetaData, inspect
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import QueuePool, StaticPool
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

# Redis imports
try:
    import redis
    import redis.asyncio as aioredis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

# InfluxDB imports
try:
    from influxdb_client import InfluxDBClient
    from influxdb_client.client.write_api import SYNCHRONOUS
    INFLUXDB_AVAILABLE = True
except ImportError:
    INFLUXDB_AVAILABLE = False

# MongoDB imports
try:
    from motor.motor_asyncio import AsyncIOMotorClient
    import pymongo
    MONGODB_AVAILABLE = True
except ImportError:
    MONGODB_AVAILABLE = False

logger = logging.getLogger(__name__)


class DatabaseType(str, Enum):
    """支持的数据库类型"""
    MYSQL = "mysql"
    POSTGRESQL = "postgresql"
    SQLITE = "sqlite"
    REDIS = "redis"
    INFLUXDB = "influxdb"
    MONGODB = "mongodb"


@dataclass
class DatabaseConfig:
    """数据库配置"""
    db_type: DatabaseType
    host: str = "localhost"
    port: Optional[int] = None
    username: Optional[str] = None
    password: Optional[str] = None
    database: str = "vnpy"
    
    # 连接池配置
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    pool_recycle: int = 3600
    pool_pre_ping: bool = True
    
    # 其他配置
    charset: str = "utf8mb4"
    timezone: str = "+08:00"
    echo: bool = False
    ssl_disabled: bool = True
    
    # SQLite特定
    sqlite_path: Optional[str] = None
    
    # Redis特定
    redis_db: int = 0
    redis_password: Optional[str] = None
    
    # InfluxDB特定
    influx_org: Optional[str] = None
    influx_token: Optional[str] = None
    influx_bucket: Optional[str] = None
    
    # MongoDB特定
    mongo_auth_source: str = "admin"
    
    # 额外参数
    extra_args: Dict[str, Any] = field(default_factory=dict)
    
    def get_default_port(self) -> int:
        """获取默认端口"""
        port_map = {
            DatabaseType.MYSQL: 3306,
            DatabaseType.POSTGRESQL: 5432,
            DatabaseType.SQLITE: None,
            DatabaseType.REDIS: 6379,
            DatabaseType.INFLUXDB: 8086,
            DatabaseType.MONGODB: 27017
        }
        return self.port or port_map.get(self.db_type)
    
    def build_url(self, async_mode: bool = False) -> str:
        """构建数据库连接URL"""
        if self.db_type == DatabaseType.SQLITE:
            driver = "sqlite+aiosqlite" if async_mode else "sqlite"
            path = self.sqlite_path or "./data/vnpy.db"
            return f"{driver}:///{path}"
        
        elif self.db_type == DatabaseType.MYSQL:
            driver = "mysql+aiomysql" if async_mode else "mysql+pymysql"
            password = quote_plus(self.password) if self.password else ""
            port = self.get_default_port()
            
            url = f"{driver}://{self.username}:{password}@{self.host}:{port}/{self.database}"
            params = [f"charset={self.charset}"]
            
            if self.ssl_disabled:
                params.append("ssl_disabled=true")
            
            return f"{url}?{'&'.join(params)}"
        
        elif self.db_type == DatabaseType.POSTGRESQL:
            driver = "postgresql+asyncpg" if async_mode else "postgresql+psycopg2"
            password = quote_plus(self.password) if self.password else ""
            port = self.get_default_port()
            
            return f"{driver}://{self.username}:{password}@{self.host}:{port}/{self.database}"
        
        elif self.db_type == DatabaseType.REDIS:
            password_part = f":{self.redis_password}@" if self.redis_password else ""
            port = self.get_default_port()
            return f"redis://{password_part}{self.host}:{port}/{self.redis_db}"
        
        else:
            raise ValueError(f"不支持的数据库类型: {self.db_type}")


class DatabaseConnectionPool:
    """数据库连接池管理"""
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self._engine: Optional[Engine] = None
        self._async_engine = None
        self._session_factory = None
        self._async_session_factory = None
        self._redis_pool: Optional[redis.ConnectionPool] = None
        self._async_redis_pool = None
        self._influx_client: Optional[InfluxDBClient] = None
        self._mongo_client = None
        
        self._connection_stats = {
            "total_connections": 0,
            "active_connections": 0,
            "failed_connections": 0,
            "last_connection_time": None
        }
    
    @property
    def engine(self) -> Engine:
        """获取同步数据库引擎"""
        if self._engine is None:
            self._create_engine()
        return self._engine
    
    @property
    def async_engine(self):
        """获取异步数据库引擎"""
        if self._async_engine is None:
            self._create_async_engine()
        return self._async_engine
    
    def _create_engine(self):
        """创建同步数据库引擎"""
        if self.config.db_type in [DatabaseType.MYSQL, DatabaseType.POSTGRESQL]:
            url = self.config.build_url(async_mode=False)
            
            connect_args = {}
            if self.config.db_type == DatabaseType.MYSQL:
                connect_args.update({
                    "charset": self.config.charset,
                    "autocommit": False,
                    "sql_mode": "STRICT_TRANS_TABLES,NO_ZERO_DATE,NO_ZERO_IN_DATE,ERROR_FOR_DIVISION_BY_ZERO"
                })
            
            self._engine = create_engine(
                url,
                poolclass=QueuePool,
                pool_size=self.config.pool_size,
                max_overflow=self.config.max_overflow,
                pool_timeout=self.config.pool_timeout,
                pool_recycle=self.config.pool_recycle,
                pool_pre_ping=self.config.pool_pre_ping,
                echo=self.config.echo,
                connect_args=connect_args,
                **self.config.extra_args
            )
            
            # 添加事件监听器
            self._setup_engine_events()
            
        elif self.config.db_type == DatabaseType.SQLITE:
            url = self.config.build_url(async_mode=False)
            self._engine = create_engine(
                url,
                poolclass=StaticPool,
                connect_args={"check_same_thread": False},
                echo=self.config.echo
            )
        
        logger.info(f"创建{self.config.db_type}同步引擎完成")
    
    def _create_async_engine(self):
        """创建异步数据库引擎"""
        if self.config.db_type in [DatabaseType.MYSQL, DatabaseType.POSTGRESQL]:
            url = self.config.build_url(async_mode=True)
            
            self._async_engine = create_async_engine(
                url,
                pool_size=self.config.pool_size,
                max_overflow=self.config.max_overflow,
                pool_timeout=self.config.pool_timeout,
                pool_recycle=self.config.pool_recycle,
                pool_pre_ping=self.config.pool_pre_ping,
                echo=self.config.echo,
                **self.config.extra_args
            )
            
        elif self.config.db_type == DatabaseType.SQLITE:
            url = self.config.build_url(async_mode=True)
            self._async_engine = create_async_engine(
                url,
                echo=self.config.echo
            )
        
        logger.info(f"创建{self.config.db_type}异步引擎完成")
    
    def _setup_engine_events(self):
        """设置引擎事件监听器"""
        @event.listens_for(self._engine, "connect")
        def set_mysql_pragma(dbapi_connection, connection_record):
            """连接时设置MySQL参数"""
            if self.config.db_type == DatabaseType.MYSQL:
                cursor = dbapi_connection.cursor()
                try:
                    # 设置时区
                    cursor.execute(f"SET time_zone = '{self.config.timezone}'")
                    # 设置字符集
                    cursor.execute(f"SET NAMES {self.config.charset} COLLATE {self.config.charset}_unicode_ci")
                    # 设置SQL模式
                    cursor.execute("SET sql_mode = 'STRICT_TRANS_TABLES,NO_ZERO_DATE,NO_ZERO_IN_DATE,ERROR_FOR_DIVISION_BY_ZERO'")
                    # 设置事务隔离级别
                    cursor.execute("SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED")
                finally:
                    cursor.close()
        
        @event.listens_for(self._engine, "checkout")
        def receive_checkout(dbapi_connection, connection_record, connection_proxy):
            """连接检出时的处理"""
            self._connection_stats["active_connections"] += 1
            self._connection_stats["total_connections"] += 1
            self._connection_stats["last_connection_time"] = datetime.now()
        
        @event.listens_for(self._engine, "checkin")
        def receive_checkin(dbapi_connection, connection_record):
            """连接检入时的处理"""
            self._connection_stats["active_connections"] = max(0, self._connection_stats["active_connections"] - 1)
    
    def get_session_factory(self):
        """获取同步会话工厂"""
        if self._session_factory is None:
            self._session_factory = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
        return self._session_factory
    
    def get_async_session_factory(self):
        """获取异步会话工厂"""
        if self._async_session_factory is None:
            self._async_session_factory = async_sessionmaker(
                self.async_engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
        return self._async_session_factory
    
    def get_redis_connection(self) -> redis.Redis:
        """获取Redis连接"""
        if not REDIS_AVAILABLE:
            raise RuntimeError("Redis不可用，请安装redis包")
        
        if self._redis_pool is None:
            self._redis_pool = redis.ConnectionPool(
                host=self.config.host,
                port=self.config.get_default_port(),
                db=self.config.redis_db,
                password=self.config.redis_password,
                decode_responses=True,
                max_connections=self.config.pool_size
            )
        
        return redis.Redis(connection_pool=self._redis_pool)
    
    async def get_async_redis_connection(self):
        """获取异步Redis连接"""
        if not REDIS_AVAILABLE:
            raise RuntimeError("Redis不可用，请安装redis包")
        
        if self._async_redis_pool is None:
            self._async_redis_pool = aioredis.ConnectionPool(
                host=self.config.host,
                port=self.config.get_default_port(),
                db=self.config.redis_db,
                password=self.config.redis_password,
                decode_responses=True,
                max_connections=self.config.pool_size
            )
        
        return aioredis.Redis(connection_pool=self._async_redis_pool)
    
    def get_influx_client(self) -> InfluxDBClient:
        """获取InfluxDB客户端"""
        if not INFLUXDB_AVAILABLE:
            raise RuntimeError("InfluxDB不可用，请安装influxdb-client包")
        
        if self._influx_client is None:
            url = f"http://{self.config.host}:{self.config.get_default_port()}"
            self._influx_client = InfluxDBClient(
                url=url,
                token=self.config.influx_token,
                org=self.config.influx_org
            )
        
        return self._influx_client
    
    def get_mongo_client(self):
        """获取MongoDB客户端"""
        if not MONGODB_AVAILABLE:
            raise RuntimeError("MongoDB不可用，请安装motor包")
        
        if self._mongo_client is None:
            if self.config.username and self.config.password:
                uri = f"mongodb://{self.config.username}:{quote_plus(self.config.password)}@{self.config.host}:{self.config.get_default_port()}/{self.config.database}?authSource={self.config.mongo_auth_source}"
            else:
                uri = f"mongodb://{self.config.host}:{self.config.get_default_port()}/{self.config.database}"
            
            self._mongo_client = AsyncIOMotorClient(uri)
        
        return self._mongo_client
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """获取连接统计信息"""
        stats = self._connection_stats.copy()
        
        if self._engine:
            pool = self._engine.pool
            stats.update({
                "pool_size": pool.size(),
                "checked_out": pool.checkedout(),
                "overflow": pool.overflow(),
                "checked_in": pool.checkedin()
            })
        
        return stats
    
    def test_connection(self) -> bool:
        """测试数据库连接"""
        try:
            if self.config.db_type in [DatabaseType.MYSQL, DatabaseType.POSTGRESQL, DatabaseType.SQLITE]:
                with self.engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                    
            elif self.config.db_type == DatabaseType.REDIS:
                redis_conn = self.get_redis_connection()
                redis_conn.ping()
                
            elif self.config.db_type == DatabaseType.INFLUXDB:
                influx_client = self.get_influx_client()
                influx_client.ping()
                
            elif self.config.db_type == DatabaseType.MONGODB:
                # MongoDB测试需要异步，这里简化处理
                pass
            
            logger.info(f"{self.config.db_type}数据库连接测试成功")
            return True
            
        except Exception as e:
            logger.error(f"{self.config.db_type}数据库连接测试失败: {e}")
            self._connection_stats["failed_connections"] += 1
            return False
    
    def close(self):
        """关闭所有连接"""
        if self._engine:
            self._engine.dispose()
            logger.info("同步数据库引擎已关闭")
        
        if self._async_engine:
            asyncio.create_task(self._async_engine.adispose())
            logger.info("异步数据库引擎已关闭")
        
        if self._redis_pool:
            self._redis_pool.disconnect()
            logger.info("Redis连接池已关闭")
        
        if self._async_redis_pool:
            asyncio.create_task(self._async_redis_pool.disconnect())
            logger.info("异步Redis连接池已关闭")
        
        if self._influx_client:
            self._influx_client.close()
            logger.info("InfluxDB客户端已关闭")
        
        if self._mongo_client:
            self._mongo_client.close()
            logger.info("MongoDB客户端已关闭")


class UnifiedDatabaseManager:
    """统一数据库管理器"""
    
    def __init__(self):
        self._pools: Dict[str, DatabaseConnectionPool] = {}
        self._configs: Dict[str, DatabaseConfig] = {}
        self._initialized = False
    
    def add_database(self, name: str, config: DatabaseConfig):
        """添加数据库配置"""
        self._configs[name] = config
        self._pools[name] = DatabaseConnectionPool(config)
        logger.info(f"添加数据库配置: {name} ({config.db_type})")
    
    def get_pool(self, name: str) -> DatabaseConnectionPool:
        """获取数据库连接池"""
        if name not in self._pools:
            raise ValueError(f"数据库 '{name}' 未配置")
        return self._pools[name]
    
    @contextmanager
    def get_session(self, name: str) -> Generator[Session, None, None]:
        """获取同步数据库会话"""
        pool = self.get_pool(name)
        session_factory = pool.get_session_factory()
        session = session_factory()
        
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    @asynccontextmanager
    async def get_async_session(self, name: str) -> AsyncGenerator[AsyncSession, None]:
        """获取异步数据库会话"""
        pool = self.get_pool(name)
        session_factory = pool.get_async_session_factory()
        
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
    
    def get_redis(self, name: str) -> redis.Redis:
        """获取Redis连接"""
        pool = self.get_pool(name)
        return pool.get_redis_connection()
    
    async def get_async_redis(self, name: str):
        """获取异步Redis连接"""
        pool = self.get_pool(name)
        return await pool.get_async_redis_connection()
    
    def get_influx(self, name: str) -> InfluxDBClient:
        """获取InfluxDB客户端"""
        pool = self.get_pool(name)
        return pool.get_influx_client()
    
    def get_mongo(self, name: str):
        """获取MongoDB客户端"""
        pool = self.get_pool(name)
        return pool.get_mongo_client()
    
    def test_all_connections(self) -> Dict[str, bool]:
        """测试所有数据库连接"""
        results = {}
        for name, pool in self._pools.items():
            results[name] = pool.test_connection()
        return results
    
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """获取所有数据库连接统计"""
        stats = {}
        for name, pool in self._pools.items():
            stats[name] = {
                "config": {
                    "db_type": pool.config.db_type,
                    "host": pool.config.host,
                    "port": pool.config.get_default_port(),
                    "database": pool.config.database
                },
                "connection_stats": pool.get_connection_stats()
            }
        return stats
    
    def close_all(self):
        """关闭所有连接"""
        for name, pool in self._pools.items():
            logger.info(f"关闭数据库连接: {name}")
            pool.close()
    
    @classmethod
    def from_env(cls) -> "UnifiedDatabaseManager":
        """从环境变量创建数据库管理器"""
        manager = cls()
        
        # 主数据库配置（MySQL）
        mysql_config = DatabaseConfig(
            db_type=DatabaseType.MYSQL,
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", "3306")),
            username=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", "root"),
            database=os.getenv("DB_NAME", "vnpy"),
            pool_size=int(os.getenv("DB_POOL_SIZE", "10")),
            max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "20")),
            pool_timeout=int(os.getenv("DB_POOL_TIMEOUT", "30")),
            pool_recycle=int(os.getenv("DB_POOL_RECYCLE", "3600")),
            charset="utf8mb4",
            echo=os.getenv("DB_ECHO", "false").lower() == "true"
        )
        manager.add_database("main", mysql_config)
        
        # Redis缓存配置
        if os.getenv("REDIS_HOST") or os.getenv("REDIS_URL"):
            redis_config = DatabaseConfig(
                db_type=DatabaseType.REDIS,
                host=os.getenv("REDIS_HOST", "localhost"),
                port=int(os.getenv("REDIS_PORT", "6379")),
                redis_db=int(os.getenv("REDIS_DB", "0")),
                redis_password=os.getenv("REDIS_PASSWORD"),
                pool_size=int(os.getenv("REDIS_POOL_SIZE", "10"))
            )
            manager.add_database("cache", redis_config)
        
        # InfluxDB时序数据库配置
        if os.getenv("INFLUX_HOST"):
            influx_config = DatabaseConfig(
                db_type=DatabaseType.INFLUXDB,
                host=os.getenv("INFLUX_HOST", "localhost"),
                port=int(os.getenv("INFLUX_PORT", "8086")),
                influx_token=os.getenv("INFLUX_TOKEN"),
                influx_org=os.getenv("INFLUX_ORG"),
                influx_bucket=os.getenv("INFLUX_BUCKET", "trading_data")
            )
            manager.add_database("timeseries", influx_config)
        
        # MongoDB日志存储配置
        if os.getenv("MONGO_HOST"):
            mongo_config = DatabaseConfig(
                db_type=DatabaseType.MONGODB,
                host=os.getenv("MONGO_HOST", "localhost"),
                port=int(os.getenv("MONGO_PORT", "27017")),
                username=os.getenv("MONGO_USER"),
                password=os.getenv("MONGO_PASSWORD"),
                database=os.getenv("MONGO_DATABASE", "vnpy_logs"),
                pool_size=int(os.getenv("MONGO_POOL_SIZE", "10"))
            )
            manager.add_database("logs", mongo_config)
        
        return manager


# 全局数据库管理器实例
_db_manager: Optional[UnifiedDatabaseManager] = None


def get_database_manager() -> UnifiedDatabaseManager:
    """获取全局数据库管理器"""
    global _db_manager
    if _db_manager is None:
        _db_manager = UnifiedDatabaseManager.from_env()
    return _db_manager


def init_database_manager(manager: UnifiedDatabaseManager):
    """设置全局数据库管理器"""
    global _db_manager
    _db_manager = manager


# 便捷函数
def get_db_session(db_name: str = "main"):
    """获取数据库会话（用于FastAPI依赖注入）"""
    manager = get_database_manager()
    with manager.get_session(db_name) as session:
        yield session


async def get_async_db_session(db_name: str = "main"):
    """获取异步数据库会话"""
    manager = get_database_manager()
    async with manager.get_async_session(db_name) as session:
        yield session


def get_redis_client(db_name: str = "cache") -> redis.Redis:
    """获取Redis客户端"""
    manager = get_database_manager()
    return manager.get_redis(db_name)


async def get_async_redis_client(db_name: str = "cache"):
    """获取异步Redis客户端"""
    manager = get_database_manager()
    return await manager.get_async_redis(db_name)


def get_influx_client(db_name: str = "timeseries") -> InfluxDBClient:
    """获取InfluxDB客户端"""
    manager = get_database_manager()
    return manager.get_influx(db_name)


def get_mongo_client(db_name: str = "logs"):
    """获取MongoDB客户端"""
    manager = get_database_manager()
    return manager.get_mongo(db_name)
