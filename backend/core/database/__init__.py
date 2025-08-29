"""
RedFire 统一数据库管理模块
=======================

提供完整的数据库管理解决方案，包括：
- 统一数据库连接管理
- 多数据库支持 (MySQL, PostgreSQL, Redis, InfluxDB, MongoDB)
- 连接池优化
- Redis缓存策略
- 时序数据存储
- 日志存储
- 读写分离
"""

from .unified_database_manager import (
    UnifiedDatabaseManager,
    DatabaseConfig,
    DatabaseType,
    get_database_manager,
    init_database_manager,
    get_db_session,
    get_async_db_session,
    get_redis_client,
    get_async_redis_client,
    get_influx_client,
    get_mongo_client
)

from .optimized_config import (
    OptimizedDatabaseConfig,
    RedisOptimizedConfig,
    DatabaseConfigManager,
    get_config_manager,
    get_optimized_mysql_config,
    get_optimized_redis_config
)

from .redis_cache_strategy import (
    RedisCacheManager,
    AsyncRedisCacheManager,
    CacheConfig,
    CacheDecorator,
    CacheFactory,
    get_cache_manager,
    cache,
    CACHE_CONFIGS
)

from .influxdb_manager import (
    InfluxDBManager,
    InfluxDBConfig,
    TimeSeriesPoint,
    TradingDataManager,
    get_influx_manager,
    get_trading_data_manager,
    init_influx_manager
)

from .mongodb_logger import (
    MongoDBManager,
    MongoDBConfig,
    LogManager,
    LogEntry,
    LogLevel,
    LogCategory,
    get_mongo_manager,
    get_log_manager,
    init_mongo_manager
)

from .read_write_split import (
    ReadWriteSplitManager,
    DatabaseNode,
    DatabaseNodeConfig,
    DatabaseRole,
    LoadBalanceStrategy,
    get_rw_split_manager,
    init_rw_split_manager,
    get_read_session,
    get_write_session,
    get_async_read_session,
    get_async_write_session
)

__all__ = [
    # 统一数据库管理
    "UnifiedDatabaseManager",
    "DatabaseConfig", 
    "DatabaseType",
    "get_database_manager",
    "init_database_manager",
    "get_db_session",
    "get_async_db_session",
    "get_redis_client",
    "get_async_redis_client",
    "get_influx_client",
    "get_mongo_client",
    
    # 优化配置
    "OptimizedDatabaseConfig",
    "RedisOptimizedConfig", 
    "DatabaseConfigManager",
    "get_config_manager",
    "get_optimized_mysql_config",
    "get_optimized_redis_config",
    
    # Redis缓存
    "RedisCacheManager",
    "AsyncRedisCacheManager",
    "CacheConfig",
    "CacheDecorator",
    "CacheFactory",
    "get_cache_manager",
    "cache",
    "CACHE_CONFIGS",
    
    # InfluxDB时序数据
    "InfluxDBManager",
    "InfluxDBConfig",
    "TimeSeriesPoint", 
    "TradingDataManager",
    "get_influx_manager",
    "get_trading_data_manager",
    "init_influx_manager",
    
    # MongoDB日志
    "MongoDBManager",
    "MongoDBConfig",
    "LogManager",
    "LogEntry",
    "LogLevel",
    "LogCategory",
    "get_mongo_manager",
    "get_log_manager", 
    "init_mongo_manager",
    
    # 读写分离
    "ReadWriteSplitManager",
    "DatabaseNode",
    "DatabaseNodeConfig",
    "DatabaseRole",
    "LoadBalanceStrategy",
    "get_rw_split_manager",
    "init_rw_split_manager",
    "get_read_session",
    "get_write_session",
    "get_async_read_session",
    "get_async_write_session"
]
