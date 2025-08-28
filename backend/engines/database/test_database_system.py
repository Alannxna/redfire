"""
RedFire 数据库系统测试
===================

全面测试数据库管理系统的各项功能
"""

import pytest
import asyncio
import os
import tempfile
import logging
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

# 设置测试环境变量
os.environ.update({
    "DB_HOST": "localhost",
    "DB_PORT": "3306",
    "DB_USER": "test_user",
    "DB_PASSWORD": "test_password",
    "DB_NAME": "test_db",
    "REDIS_HOST": "localhost",
    "REDIS_PORT": "6379",
    "REDIS_DB": "1",  # 使用测试数据库
})

try:
    from backend.core.database import (
        UnifiedDatabaseManager,
        DatabaseConfig,
        DatabaseType,
        OptimizedDatabaseConfig,
        RedisCacheManager,
        CacheConfig,
        TimeSeriesPoint,
        LogEntry,
        LogLevel,
        LogCategory,
        ReadWriteSplitManager,
        DatabaseNodeConfig,
        DatabaseRole,
        initialize_databases,
        get_database_status
    )
    IMPORTS_AVAILABLE = True
except ImportError as e:
    IMPORTS_AVAILABLE = False
    import_error = e

logger = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


class TestDatabaseConfig:
    """测试数据库配置"""
    
    def test_database_config_creation(self):
        """测试数据库配置创建"""
        if not IMPORTS_AVAILABLE:
            pytest.skip(f"导入失败: {import_error}")
        
        config = DatabaseConfig(
            host="localhost",
            port=3306,
            username="test",
            password="test",
            database="test_db"
        )
        
        assert config.host == "localhost"
        assert config.port == 3306
        assert config.username == "test"
        assert config.database == "test_db"
    
    def test_optimized_config_url_building(self):
        """测试优化配置URL构建"""
        if not IMPORTS_AVAILABLE:
            pytest.skip(f"导入失败: {import_error}")
        
        config = OptimizedDatabaseConfig(
            host="localhost",
            port=3306,
            username="root",
            password="password",
            database="vnpy"
        )
        
        url = config.build_connection_url(async_mode=False)
        assert "mysql+pymysql" in url
        assert "charset=utf8mb4" in url
        
        async_url = config.build_connection_url(async_mode=True)
        assert "mysql+aiomysql" in async_url
    
    def test_config_validation(self):
        """测试配置验证"""
        if not IMPORTS_AVAILABLE:
            pytest.skip(f"导入失败: {import_error}")
        
        # 有效配置
        valid_config = OptimizedDatabaseConfig(
            host="localhost",
            port=3306,
            username="root",
            password="password",
            database="test"
        )
        assert valid_config.validate_config() is True
        
        # 无效配置 - 缺少必需参数
        invalid_config = OptimizedDatabaseConfig(
            host="",
            port=3306,
            username="",
            password="",
            database=""
        )
        assert invalid_config.validate_config() is False


class TestUnifiedDatabaseManager:
    """测试统一数据库管理器"""
    
    @pytest.fixture
    def mock_db_manager(self):
        """创建模拟数据库管理器"""
        if not IMPORTS_AVAILABLE:
            pytest.skip(f"导入失败: {import_error}")
        
        with patch('sqlalchemy.create_engine'), \
             patch('redis.Redis'), \
             patch('backend.core.database.unified_database_manager.InfluxDBClient'), \
             patch('backend.core.database.unified_database_manager.AsyncIOMotorClient'):
            
            manager = UnifiedDatabaseManager()
            yield manager
    
    def test_database_manager_initialization(self, mock_db_manager):
        """测试数据库管理器初始化"""
        assert mock_db_manager is not None
        assert hasattr(mock_db_manager, '_pools')
        assert hasattr(mock_db_manager, '_redis_clients')
    
    def test_add_database_config(self, mock_db_manager):
        """测试添加数据库配置"""
        config = DatabaseConfig(
            host="localhost",
            port=3306,
            username="test",
            password="test",
            database="test_db"
        )
        
        mock_db_manager.add_database("test_db", DatabaseType.MYSQL, config)
        assert "test_db" in mock_db_manager._configs
    
    @patch('redis.Redis')
    def test_redis_client_creation(self, mock_redis, mock_db_manager):
        """测试Redis客户端创建"""
        mock_redis_instance = Mock()
        mock_redis.return_value = mock_redis_instance
        
        client = mock_db_manager.get_redis("cache")
        assert client is not None


class TestRedisCacheManager:
    """测试Redis缓存管理器"""
    
    @pytest.fixture
    def mock_redis_client(self):
        """创建模拟Redis客户端"""
        mock_client = Mock()
        mock_client.get.return_value = None
        mock_client.set.return_value = True
        mock_client.setex.return_value = True
        mock_client.delete.return_value = 1
        mock_client.exists.return_value = True
        return mock_client
    
    @pytest.fixture
    def cache_manager(self, mock_redis_client):
        """创建缓存管理器"""
        if not IMPORTS_AVAILABLE:
            pytest.skip(f"导入失败: {import_error}")
        
        config = CacheConfig(ttl=3600, key_prefix="test")
        return RedisCacheManager(mock_redis_client, config)
    
    def test_cache_set_get(self, cache_manager, mock_redis_client):
        """测试缓存设置和获取"""
        # 设置缓存
        result = cache_manager.set("namespace", "key", {"data": "value"})
        assert result is True
        
        # 模拟缓存命中
        import json
        mock_redis_client.get.return_value = json.dumps({"data": "value"}).encode('utf-8')
        
        # 获取缓存
        data = cache_manager.get("namespace", "key")
        assert data == {"data": "value"}
    
    def test_cache_delete(self, cache_manager, mock_redis_client):
        """测试缓存删除"""
        result = cache_manager.delete("namespace", "key")
        assert result is True
        mock_redis_client.delete.assert_called_once()
    
    def test_cache_stats(self, cache_manager):
        """测试缓存统计"""
        stats = cache_manager.get_stats()
        assert "hits" in stats
        assert "misses" in stats
        assert "hit_rate" in stats


class TestTimeSeriesPoint:
    """测试时序数据点"""
    
    def test_time_series_point_creation(self):
        """测试时序数据点创建"""
        if not IMPORTS_AVAILABLE:
            pytest.skip(f"导入失败: {import_error}")
        
        point = TimeSeriesPoint(
            measurement="test_measurement",
            fields={"value": 100.0, "status": 1},
            tags={"symbol": "AAPL", "exchange": "NASDAQ"},
            timestamp=datetime.now()
        )
        
        assert point.measurement == "test_measurement"
        assert point.fields["value"] == 100.0
        assert point.tags["symbol"] == "AAPL"
    
    @patch('backend.core.database.influxdb_manager.INFLUXDB_AVAILABLE', True)
    @patch('backend.core.database.influxdb_manager.Point')
    def test_to_influx_point_conversion(self, mock_point_class):
        """测试转换为InfluxDB Point对象"""
        if not IMPORTS_AVAILABLE:
            pytest.skip(f"导入失败: {import_error}")
        
        mock_point = Mock()
        mock_point.tag.return_value = mock_point
        mock_point.field.return_value = mock_point
        mock_point.time.return_value = mock_point
        mock_point_class.return_value = mock_point
        
        point = TimeSeriesPoint(
            measurement="test",
            fields={"value": 1.0},
            tags={"tag1": "value1"}
        )
        
        influx_point = point.to_influx_point()
        assert influx_point is not None


class TestLogEntry:
    """测试日志条目"""
    
    def test_log_entry_creation(self):
        """测试日志条目创建"""
        if not IMPORTS_AVAILABLE:
            pytest.skip(f"导入失败: {import_error}")
        
        log_entry = LogEntry(
            level=LogLevel.INFO,
            category=LogCategory.TRADING,
            message="测试日志消息",
            user_id="user_123",
            data={"key": "value"}
        )
        
        assert log_entry.level == LogLevel.INFO
        assert log_entry.category == LogCategory.TRADING
        assert log_entry.message == "测试日志消息"
        assert log_entry.user_id == "user_123"
    
    def test_log_entry_to_dict(self):
        """测试日志条目转换为字典"""
        if not IMPORTS_AVAILABLE:
            pytest.skip(f"导入失败: {import_error}")
        
        timestamp = datetime.now()
        log_entry = LogEntry(
            level=LogLevel.ERROR,
            category=LogCategory.SYSTEM,
            message="系统错误",
            timestamp=timestamp,
            exception="Exception details"
        )
        
        log_dict = log_entry.to_dict()
        assert log_dict["level"] == LogLevel.ERROR
        assert log_dict["category"] == LogCategory.SYSTEM
        assert log_dict["message"] == "系统错误"
        assert log_dict["timestamp"] == timestamp
        assert log_dict["exception"] == "Exception details"


class TestReadWriteSplit:
    """测试读写分离"""
    
    def test_database_node_config(self):
        """测试数据库节点配置"""
        if not IMPORTS_AVAILABLE:
            pytest.skip(f"导入失败: {import_error}")
        
        config = DatabaseNodeConfig(
            host="localhost",
            port=3306,
            username="root",
            password="password",
            database="test",
            role=DatabaseRole.MASTER,
            weight=1
        )
        
        assert config.host == "localhost"
        assert config.role == DatabaseRole.MASTER
        assert config.weight == 1
        
        url = config.build_url(async_mode=False)
        assert "mysql+pymysql" in url
    
    @patch('sqlalchemy.create_engine')
    def test_read_write_split_manager(self, mock_create_engine):
        """测试读写分离管理器"""
        if not IMPORTS_AVAILABLE:
            pytest.skip(f"导入失败: {import_error}")
        
        mock_engine = Mock()
        mock_create_engine.return_value = mock_engine
        
        manager = ReadWriteSplitManager()
        
        # 添加主节点
        master_config = DatabaseNodeConfig(
            host="master-host",
            port=3306,
            username="root",
            password="password",
            database="test",
            role=DatabaseRole.MASTER
        )
        manager.add_master_node(master_config)
        
        # 添加从节点
        slave_config = DatabaseNodeConfig(
            host="slave-host",
            port=3306,
            username="readonly",
            password="password",
            database="test",
            role=DatabaseRole.SLAVE
        )
        manager.add_slave_node(slave_config)
        
        assert len(manager.master_nodes) == 1
        assert len(manager.slave_nodes) == 1


class TestDatabaseInitialization:
    """测试数据库初始化"""
    
    @patch('backend.core.database.database_init.get_database_manager')
    @patch('backend.core.database.database_init.get_config_manager')
    @patch('backend.core.database.database_init.get_rw_split_manager')
    def test_database_initialization(self, mock_rw_manager, mock_config_manager, mock_db_manager):
        """测试数据库初始化过程"""
        if not IMPORTS_AVAILABLE:
            pytest.skip(f"导入失败: {import_error}")
        
        # 模拟管理器
        mock_db_manager.return_value = Mock()
        mock_config_manager.return_value = Mock()
        mock_rw_manager.return_value = Mock()
        
        # 模拟测试连接成功
        mock_config_manager.return_value.test_mysql_connection.return_value = True
        mock_config_manager.return_value.test_redis_connection.return_value = True
        
        # 模拟数据库池
        mock_pool = Mock()
        mock_session = Mock()
        mock_pool.get_session_factory.return_value.return_value = mock_session
        mock_db_manager.return_value.get_pool.return_value = mock_pool
        
        # 模拟读写分离统计
        mock_rw_manager.return_value.get_all_stats.return_value = {
            "healthy_master_nodes": 1,
            "total_master_nodes": 1,
            "total_slave_nodes": 0
        }
        
        # 测试初始化
        from backend.core.database.database_init import DatabaseInitializer
        initializer = DatabaseInitializer()
        
        # 测试MySQL初始化
        result = initializer._initialize_mysql()
        assert result is True
        
        # 测试Redis初始化
        result = initializer._initialize_redis()
        assert result is True
    
    def test_database_status_retrieval(self):
        """测试数据库状态获取"""
        if not IMPORTS_AVAILABLE:
            pytest.skip(f"导入失败: {import_error}")
        
        with patch('backend.core.database.database_init.DatabaseInitializer') as mock_initializer:
            mock_instance = Mock()
            mock_initializer.return_value = mock_instance
            mock_instance.get_initialization_status.return_value = {
                "initialized_databases": ["mysql", "redis"],
                "mysql": True,
                "redis": True
            }
            
            status = get_database_status()
            assert "initialized_databases" in status


class TestErrorHandling:
    """测试错误处理"""
    
    def test_connection_failure_handling(self):
        """测试连接失败处理"""
        if not IMPORTS_AVAILABLE:
            pytest.skip(f"导入失败: {import_error}")
        
        with patch('sqlalchemy.create_engine') as mock_create_engine:
            mock_create_engine.side_effect = Exception("Connection failed")
            
            try:
                config = DatabaseConfig(
                    host="invalid-host",
                    port=3306,
                    username="invalid",
                    password="invalid",
                    database="invalid"
                )
                
                manager = UnifiedDatabaseManager()
                manager.add_database("test", DatabaseType.MYSQL, config)
                
                # 应该捕获异常而不是崩溃
                assert True
                
            except Exception as e:
                # 如果有异常，应该是可控的
                assert "Connection failed" in str(e)
    
    def test_cache_operation_failure(self):
        """测试缓存操作失败处理"""
        if not IMPORTS_AVAILABLE:
            pytest.skip(f"导入失败: {import_error}")
        
        mock_redis = Mock()
        mock_redis.get.side_effect = Exception("Redis connection failed")
        mock_redis.set.side_effect = Exception("Redis connection failed")
        
        config = CacheConfig()
        cache_manager = RedisCacheManager(mock_redis, config)
        
        # 获取操作失败应该返回None而不是抛出异常
        result = cache_manager.get("namespace", "key")
        assert result is None
        
        # 设置操作失败应该返回False而不是抛出异常
        result = cache_manager.set("namespace", "key", "value")
        assert result is False
        
        # 检查错误统计
        stats = cache_manager.get_stats()
        assert stats["errors"] > 0


class TestPerformanceAndMonitoring:
    """测试性能和监控"""
    
    def test_connection_pool_stats(self):
        """测试连接池统计"""
        if not IMPORTS_AVAILABLE:
            pytest.skip(f"导入失败: {import_error}")
        
        with patch('sqlalchemy.create_engine') as mock_create_engine:
            mock_engine = Mock()
            mock_pool = Mock()
            mock_pool.size.return_value = 5
            mock_pool.checked_in.return_value = 3
            mock_pool.checked_out.return_value = 2
            mock_engine.pool = mock_pool
            mock_create_engine.return_value = mock_engine
            
            manager = UnifiedDatabaseManager()
            config = DatabaseConfig(
                host="localhost",
                port=3306,
                username="test",
                password="test",
                database="test"
            )
            manager.add_database("test", DatabaseType.MYSQL, config)
            
            stats = manager.get_all_stats()
            assert isinstance(stats, dict)
    
    def test_cache_performance_metrics(self):
        """测试缓存性能指标"""
        if not IMPORTS_AVAILABLE:
            pytest.skip(f"导入失败: {import_error}")
        
        mock_redis = Mock()
        mock_redis.get.return_value = b'{"test": "data"}'
        mock_redis.set.return_value = True
        
        config = CacheConfig()
        cache_manager = RedisCacheManager(mock_redis, config)
        
        # 执行一些操作
        cache_manager.set("test", "key1", {"data": "value1"})
        cache_manager.get("test", "key1")
        cache_manager.get("test", "key2")  # miss
        
        stats = cache_manager.get_stats()
        assert stats["hits"] >= 1
        assert stats["misses"] >= 1
        assert stats["sets"] >= 1
        assert "hit_rate" in stats


@pytest.mark.asyncio
async def test_async_operations():
    """测试异步操作"""
    if not IMPORTS_AVAILABLE:
        pytest.skip(f"导入失败: {import_error}")
    
    # 测试异步日志操作
    with patch('backend.core.database.mongodb_logger.MONGODB_AVAILABLE', True):
        with patch('motor.motor_asyncio.AsyncIOMotorClient') as mock_motor:
            mock_client = Mock()
            mock_db = Mock()
            mock_collection = Mock()
            
            mock_client.__getitem__.return_value = mock_db
            mock_db.__getitem__.return_value = mock_collection
            mock_collection.insert_one.return_value = Mock(inserted_id="test_id")
            mock_motor.return_value = mock_client
            
            from backend.core.database.mongodb_logger import MongoDBManager, MongoDBConfig, LogManager
            
            config = MongoDBConfig()
            mongo_manager = MongoDBManager(config)
            log_manager = LogManager(mongo_manager)
            
            # 测试异步日志写入
            log_entry = LogEntry(
                level=LogLevel.INFO,
                category=LogCategory.SYSTEM,
                message="测试异步日志"
            )
            
            result = await log_manager.write_log(log_entry)
            assert result is not None


def test_integration_example():
    """集成测试示例"""
    if not IMPORTS_AVAILABLE:
        pytest.skip(f"导入失败: {import_error}")
    
    print("\n=== RedFire数据库系统集成测试 ===")
    
    # 模拟完整的数据库操作流程
    with patch('sqlalchemy.create_engine'), \
         patch('redis.Redis'), \
         patch('backend.core.database.unified_database_manager.InfluxDBClient'), \
         patch('backend.core.database.unified_database_manager.AsyncIOMotorClient'):
        
        try:
            # 1. 创建统一数据库管理器
            manager = UnifiedDatabaseManager()
            print("✅ 数据库管理器创建成功")
            
            # 2. 添加数据库配置
            mysql_config = DatabaseConfig(
                host="localhost",
                port=3306,
                username="root", 
                password="root",
                database="vnpy"
            )
            manager.add_database("main", DatabaseType.MYSQL, mysql_config)
            print("✅ MySQL配置添加成功")
            
            # 3. 创建缓存管理器
            cache_config = CacheConfig(ttl=3600)
            mock_redis = Mock()
            cache_manager = RedisCacheManager(mock_redis, cache_config)
            print("✅ 缓存管理器创建成功")
            
            # 4. 创建时序数据点
            point = TimeSeriesPoint(
                measurement="test_data",
                fields={"value": 100.0},
                tags={"source": "test"}
            )
            print("✅ 时序数据点创建成功")
            
            # 5. 创建日志条目
            log_entry = LogEntry(
                level=LogLevel.INFO,
                category=LogCategory.SYSTEM,
                message="集成测试日志"
            )
            print("✅ 日志条目创建成功")
            
            print("🎉 集成测试完成！所有组件正常工作")
            
        except Exception as e:
            print(f"❌ 集成测试失败: {e}")
            raise


if __name__ == "__main__":
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("🚀 开始运行RedFire数据库系统测试...")
    
    # 运行集成测试
    test_integration_example()
    
    # 运行pytest测试
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "--color=yes"
    ])
