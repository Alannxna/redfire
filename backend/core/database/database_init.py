"""
数据库初始化脚本
=============

为RedFire量化交易平台提供完整的数据库初始化功能
包括数据库创建、表结构初始化、索引创建、数据迁移等
"""

import os
import sys
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime
import logging

from sqlalchemy import create_engine, text, MetaData, Table, Column, Integer, String, DateTime, Float, Boolean, Text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from .unified_database_manager import get_database_manager, DatabaseType, DatabaseConfig
from .optimized_config import get_config_manager
from .influxdb_manager import get_influx_manager
from .mongodb_logger import get_mongo_manager
from .read_write_split import get_rw_split_manager

logger = logging.getLogger(__name__)

Base = declarative_base()


class DatabaseInitializer:
    """数据库初始化器"""
    
    def __init__(self):
        self.db_manager = get_database_manager()
        self.config_manager = get_config_manager()
        self.rw_manager = get_rw_split_manager()
        
        self._initialized_databases = set()
    
    def initialize_all(self) -> bool:
        """初始化所有数据库"""
        success = True
        
        try:
            logger.info("开始初始化数据库系统...")
            
            # 1. 初始化主数据库 (MySQL)
            if self._initialize_mysql():
                logger.info("✅ MySQL数据库初始化成功")
            else:
                logger.error("❌ MySQL数据库初始化失败")
                success = False
            
            # 2. 初始化Redis缓存
            if self._initialize_redis():
                logger.info("✅ Redis缓存初始化成功")
            else:
                logger.error("❌ Redis缓存初始化失败")
                success = False
            
            # 3. 初始化InfluxDB时序数据库
            if self._initialize_influxdb():
                logger.info("✅ InfluxDB时序数据库初始化成功")
            else:
                logger.warning("⚠️ InfluxDB时序数据库初始化失败（可选组件）")
            
            # 4. 初始化MongoDB日志存储
            if self._initialize_mongodb():
                logger.info("✅ MongoDB日志存储初始化成功")
            else:
                logger.warning("⚠️ MongoDB日志存储初始化失败（可选组件）")
            
            # 5. 初始化读写分离
            if self._initialize_read_write_split():
                logger.info("✅ 数据库读写分离初始化成功")
            else:
                logger.warning("⚠️ 数据库读写分离初始化失败")
            
            if success:
                logger.info("🎉 数据库系统初始化完成！")
            else:
                logger.error("💥 数据库系统初始化失败！")
            
            return success
            
        except Exception as e:
            logger.error(f"数据库系统初始化异常: {e}")
            return False
    
    def _initialize_mysql(self) -> bool:
        """初始化MySQL数据库"""
        try:
            # 测试连接
            if not self.config_manager.test_mysql_connection():
                logger.error("MySQL连接测试失败")
                return False
            
            # 获取数据库连接
            pool = self.db_manager.get_pool("main")
            
            # 创建数据库表
            self._create_mysql_tables(pool)
            
            # 创建索引
            self._create_mysql_indexes(pool)
            
            # 插入初始数据
            self._insert_initial_data(pool)
            
            self._initialized_databases.add("mysql")
            return True
            
        except Exception as e:
            logger.error(f"MySQL数据库初始化失败: {e}")
            return False
    
    def _create_mysql_tables(self, pool):
        """创建MySQL数据表"""
        try:
            with pool.get_session_factory()() as session:
                # 创建用户表
                session.execute(text("""
                CREATE TABLE IF NOT EXISTS users (
                    id BIGINT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(50) NOT NULL UNIQUE,
                    email VARCHAR(100) NOT NULL UNIQUE,
                    password_hash VARCHAR(255) NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    is_superuser BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_username (username),
                    INDEX idx_email (email),
                    INDEX idx_created_at (created_at)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """))
                
                # 创建交易策略表
                session.execute(text("""
                CREATE TABLE IF NOT EXISTS trading_strategies (
                    id BIGINT AUTO_INCREMENT PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    name VARCHAR(100) NOT NULL,
                    description TEXT,
                    strategy_type VARCHAR(50) NOT NULL,
                    parameters JSON,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    INDEX idx_user_id (user_id),
                    INDEX idx_strategy_type (strategy_type),
                    INDEX idx_is_active (is_active)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """))
                
                # 创建交易订单表
                session.execute(text("""
                CREATE TABLE IF NOT EXISTS trading_orders (
                    id BIGINT AUTO_INCREMENT PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    strategy_id BIGINT,
                    symbol VARCHAR(20) NOT NULL,
                    side ENUM('BUY', 'SELL') NOT NULL,
                    order_type ENUM('MARKET', 'LIMIT', 'STOP', 'STOP_LIMIT') NOT NULL,
                    quantity DECIMAL(20, 8) NOT NULL,
                    price DECIMAL(20, 8),
                    status ENUM('PENDING', 'PARTIAL', 'FILLED', 'CANCELLED', 'REJECTED') NOT NULL,
                    filled_quantity DECIMAL(20, 8) DEFAULT 0,
                    avg_price DECIMAL(20, 8),
                    commission DECIMAL(20, 8) DEFAULT 0,
                    order_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (strategy_id) REFERENCES trading_strategies(id),
                    INDEX idx_user_id (user_id),
                    INDEX idx_strategy_id (strategy_id),
                    INDEX idx_symbol (symbol),
                    INDEX idx_status (status),
                    INDEX idx_order_time (order_time)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """))
                
                # 创建持仓表
                session.execute(text("""
                CREATE TABLE IF NOT EXISTS positions (
                    id BIGINT AUTO_INCREMENT PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    symbol VARCHAR(20) NOT NULL,
                    quantity DECIMAL(20, 8) NOT NULL,
                    avg_price DECIMAL(20, 8) NOT NULL,
                    market_value DECIMAL(20, 2),
                    unrealized_pnl DECIMAL(20, 2),
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    UNIQUE KEY uk_user_symbol (user_id, symbol),
                    INDEX idx_user_id (user_id),
                    INDEX idx_symbol (symbol)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """))
                
                # 创建账户资金表
                session.execute(text("""
                CREATE TABLE IF NOT EXISTS account_balance (
                    id BIGINT AUTO_INCREMENT PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    currency VARCHAR(10) NOT NULL DEFAULT 'CNY',
                    total_balance DECIMAL(20, 2) NOT NULL DEFAULT 0,
                    available_balance DECIMAL(20, 2) NOT NULL DEFAULT 0,
                    frozen_balance DECIMAL(20, 2) NOT NULL DEFAULT 0,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    UNIQUE KEY uk_user_currency (user_id, currency),
                    INDEX idx_user_id (user_id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """))
                
                session.commit()
                logger.info("MySQL数据表创建完成")
                
        except Exception as e:
            logger.error(f"创建MySQL数据表失败: {e}")
            raise
    
    def _create_mysql_indexes(self, pool):
        """创建MySQL索引"""
        try:
            with pool.get_session_factory()() as session:
                # 创建复合索引
                indexes = [
                    "CREATE INDEX IF NOT EXISTS idx_orders_user_time ON trading_orders(user_id, order_time DESC)",
                    "CREATE INDEX IF NOT EXISTS idx_orders_symbol_time ON trading_orders(symbol, order_time DESC)",
                    "CREATE INDEX IF NOT EXISTS idx_strategies_user_active ON trading_strategies(user_id, is_active)",
                ]
                
                for index_sql in indexes:
                    try:
                        session.execute(text(index_sql))
                    except Exception as e:
                        logger.warning(f"创建索引失败: {index_sql}, 错误: {e}")
                
                session.commit()
                logger.info("MySQL索引创建完成")
                
        except Exception as e:
            logger.error(f"创建MySQL索引失败: {e}")
    
    def _insert_initial_data(self, pool):
        """插入初始数据"""
        try:
            with pool.get_session_factory()() as session:
                # 检查是否已有用户数据
                result = session.execute(text("SELECT COUNT(*) FROM users"))
                user_count = result.scalar()
                
                if user_count == 0:
                    # 插入默认管理员用户
                    from passlib.context import CryptContext
                    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
                    hashed_password = pwd_context.hash("admin123")
                    
                    session.execute(text("""
                    INSERT INTO users (username, email, password_hash, is_superuser) 
                    VALUES ('admin', 'admin@redfire.com', :password, TRUE)
                    """), {"password": hashed_password})
                    
                    logger.info("插入默认管理员用户: admin/admin123")
                
                session.commit()
                
        except Exception as e:
            logger.warning(f"插入初始数据失败: {e}")
    
    def _initialize_redis(self) -> bool:
        """初始化Redis缓存"""
        try:
            # 测试连接
            if not self.config_manager.test_redis_connection():
                logger.error("Redis连接测试失败")
                return False
            
            # 清理旧的缓存键（可选）
            redis_client = self.db_manager.get_redis("cache")
            
            # 设置一些默认配置
            redis_client.set("redfire:system:initialized", datetime.now().isoformat())
            redis_client.expire("redfire:system:initialized", 86400)  # 24小时过期
            
            self._initialized_databases.add("redis")
            return True
            
        except Exception as e:
            logger.error(f"Redis缓存初始化失败: {e}")
            return False
    
    def _initialize_influxdb(self) -> bool:
        """初始化InfluxDB时序数据库"""
        try:
            # 检查InfluxDB是否配置
            if not os.getenv("INFLUX_HOST"):
                logger.info("InfluxDB未配置，跳过初始化")
                return True
            
            influx_manager = get_influx_manager()
            
            # 测试连接
            if not influx_manager.test_connection():
                logger.error("InfluxDB连接测试失败")
                return False
            
            # 创建示例数据点（验证写入功能）
            from .influxdb_manager import TimeSeriesPoint
            test_point = TimeSeriesPoint(
                measurement="system_init",
                fields={"status": 1, "timestamp": datetime.now().timestamp()},
                tags={"source": "database_init"}
            )
            
            if influx_manager.write_point(test_point):
                logger.info("InfluxDB写入测试成功")
            
            self._initialized_databases.add("influxdb")
            return True
            
        except Exception as e:
            logger.error(f"InfluxDB初始化失败: {e}")
            return False
    
    def _initialize_mongodb(self) -> bool:
        """初始化MongoDB日志存储"""
        try:
            # 检查MongoDB是否配置
            if not os.getenv("MONGO_HOST"):
                logger.info("MongoDB未配置，跳过初始化")
                return True
            
            mongo_manager = get_mongo_manager()
            
            # 测试连接
            if not mongo_manager.test_sync_connection():
                logger.error("MongoDB连接测试失败")
                return False
            
            # 创建索引（异步操作）
            async def create_indexes():
                await mongo_manager.create_indexes()
            
            # 运行异步任务
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            loop.run_until_complete(create_indexes())
            
            self._initialized_databases.add("mongodb")
            return True
            
        except Exception as e:
            logger.error(f"MongoDB初始化失败: {e}")
            return False
    
    def _initialize_read_write_split(self) -> bool:
        """初始化读写分离"""
        try:
            # 测试读写节点
            stats = self.rw_manager.get_all_stats()
            
            healthy_masters = stats.get("healthy_master_nodes", 0)
            total_masters = stats.get("total_master_nodes", 0)
            
            if healthy_masters == 0:
                logger.error("没有健康的主数据库节点")
                return False
            
            logger.info(f"主节点状态: {healthy_masters}/{total_masters} 健康")
            
            if stats.get("total_slave_nodes", 0) > 0:
                healthy_slaves = stats.get("healthy_slave_nodes", 0)
                total_slaves = stats.get("total_slave_nodes", 0)
                logger.info(f"从节点状态: {healthy_slaves}/{total_slaves} 健康")
            else:
                logger.info("未配置从节点，读写操作将使用主节点")
            
            self._initialized_databases.add("read_write_split")
            return True
            
        except Exception as e:
            logger.error(f"读写分离初始化失败: {e}")
            return False
    
    def get_initialization_status(self) -> Dict[str, Any]:
        """获取初始化状态"""
        status = {
            "initialized_databases": list(self._initialized_databases),
            "mysql": "mysql" in self._initialized_databases,
            "redis": "redis" in self._initialized_databases,
            "influxdb": "influxdb" in self._initialized_databases,
            "mongodb": "mongodb" in self._initialized_databases,
            "read_write_split": "read_write_split" in self._initialized_databases,
            "initialization_time": datetime.now().isoformat()
        }
        
        # 添加连接统计
        try:
            status["database_stats"] = self.db_manager.get_all_stats()
        except Exception as e:
            logger.warning(f"获取数据库统计失败: {e}")
        
        try:
            status["rw_split_stats"] = self.rw_manager.get_all_stats()
        except Exception as e:
            logger.warning(f"获取读写分离统计失败: {e}")
        
        return status
    
    def cleanup(self):
        """清理资源"""
        try:
            self.db_manager.close_all()
            self.rw_manager.close_all()
            logger.info("数据库资源清理完成")
        except Exception as e:
            logger.error(f"数据库资源清理失败: {e}")


def initialize_databases() -> bool:
    """初始化数据库系统"""
    initializer = DatabaseInitializer()
    return initializer.initialize_all()


def get_database_status() -> Dict[str, Any]:
    """获取数据库状态"""
    initializer = DatabaseInitializer()
    return initializer.get_initialization_status()


if __name__ == "__main__":
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 初始化数据库
    success = initialize_databases()
    
    if success:
        print("✅ 数据库初始化成功！")
        sys.exit(0)
    else:
        print("❌ 数据库初始化失败！")
        sys.exit(1)
