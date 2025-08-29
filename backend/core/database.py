#!/usr/bin/env python3
"""
数据库连接管理器
适配现有MySQL数据库结构
"""

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
import os
import logging
from typing import Generator, Optional
from models.database_models import Base

logger = logging.getLogger(__name__)

class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self):
        self.engine = None
        self.SessionLocal = None
        self._initialized = False
    
    def initialize(self, database_url: Optional[str] = None):
        """初始化数据库连接"""
        if self._initialized:
            logger.info("数据库已经初始化")
            return
        
        # 使用提供的URL或从环境变量构建
        if not database_url:
            database_url = self._build_database_url()
        
        logger.info(f"初始化数据库连接: {self._mask_password(database_url)}")
        
        # 创建引擎
        self.engine = create_engine(
            database_url,
            poolclass=QueuePool,
            pool_size=int(os.getenv('DB_POOL_SIZE', 10)),
            max_overflow=int(os.getenv('DB_MAX_OVERFLOW', 20)),
            pool_timeout=int(os.getenv('DB_POOL_TIMEOUT', 30)),
            pool_recycle=int(os.getenv('DB_POOL_RECYCLE', 3600)),
            echo=os.getenv('DB_ECHO', 'false').lower() == 'true',
            pool_pre_ping=True,  # 连接前检查连接有效性
            connect_args={
                "charset": "utf8mb4",
                "autocommit": False,
            }
        )
        
        # 添加连接事件监听器
        self._setup_engine_events()
        
        # 创建会话工厂
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
        
        self._initialized = True
        logger.info("数据库初始化完成")
    
    def _build_database_url(self) -> str:
        """构建数据库URL"""
        # 从环境变量或配置文件读取数据库配置
        db_type = os.getenv('DB_TYPE', 'mysql')
        
        if db_type.lower() == 'mysql':
            host = os.getenv('DB_HOST', 'localhost')
            port = os.getenv('DB_PORT', '3306')
            user = os.getenv('DB_USER', 'root')
            password = os.getenv('DB_PASSWORD', 'root')
            database = os.getenv('DB_NAME', 'vnpy')
            
            return f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"
        else:
            raise ValueError(f"不支持的数据库类型: {db_type}")
    
    def _mask_password(self, url: str) -> str:
        """隐藏数据库URL中的密码"""
        if '@' in url and ':' in url:
            parts = url.split('@')
            if len(parts) == 2:
                user_pass = parts[0].split('://')[-1]
                if ':' in user_pass:
                    user, _ = user_pass.split(':', 1)
                    return f"{parts[0].split('://')[0]}://{user}:***@{parts[1]}"
        return url
    
    def _setup_engine_events(self):
        """设置引擎事件监听器"""
        @event.listens_for(self.engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            """连接时设置MySQL参数"""
            if 'mysql' in str(self.engine.url):
                cursor = dbapi_connection.cursor()
                # 设置时区
                cursor.execute("SET time_zone = '+08:00'")
                # 设置字符集
                cursor.execute("SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci")
                cursor.close()
        
        @event.listens_for(self.engine, "checkout")
        def receive_checkout(dbapi_connection, connection_record, connection_proxy):
            """连接检出时的处理"""
            logger.debug("数据库连接已检出")
        
        @event.listens_for(self.engine, "checkin")
        def receive_checkin(dbapi_connection, connection_record):
            """连接检入时的处理"""
            logger.debug("数据库连接已检入")
    
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """获取数据库会话上下文管理器"""
        if not self._initialized:
            raise RuntimeError("数据库未初始化，请先调用initialize()")
        
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def get_session_direct(self) -> Session:
        """直接获取数据库会话（需要手动管理）"""
        if not self._initialized:
            raise RuntimeError("数据库未初始化，请先调用initialize()")
        
        return self.SessionLocal()
    
    def test_connection(self) -> bool:
        """测试数据库连接"""
        try:
            with self.get_session() as session:
                session.execute(text("SELECT 1"))
                logger.info("数据库连接测试成功")
                return True
        except Exception as e:
            logger.error(f"数据库连接测试失败: {e}")
            return False
    
    def create_tables(self):
        """创建所有表（仅用于新数据库）"""
        if not self._initialized:
            raise RuntimeError("数据库未初始化，请先调用initialize()")
        
        logger.info("创建数据库表...")
        Base.metadata.create_all(bind=self.engine)
        logger.info("数据库表创建完成")
    
    def drop_tables(self):
        """删除所有表（危险操作）"""
        if not self._initialized:
            raise RuntimeError("数据库未初始化，请先调用initialize()")
        
        logger.warning("删除所有数据库表...")
        Base.metadata.drop_all(bind=self.engine)
        logger.warning("所有数据库表已删除")
    
    def get_table_info(self):
        """获取表信息"""
        if not self._initialized:
            raise RuntimeError("数据库未初始化，请先调用initialize()")
        
        with self.get_session() as session:
            # 获取所有表名
            if 'mysql' in str(self.engine.url):
                result = session.execute(text("SHOW TABLES"))
                tables = [row[0] for row in result]
            else:
                # SQLite
                result = session.execute(
                    text("SELECT name FROM sqlite_master WHERE type='table'")
                )
                tables = [row[0] for row in result]
            
            return {
                'database_url': self._mask_password(str(self.engine.url)),
                'tables': tables,
                'table_count': len(tables)
            }
    
    def close(self):
        """关闭数据库连接"""
        if self.engine:
            self.engine.dispose()
            logger.info("数据库连接已关闭")

# 全局数据库管理器实例
db_manager = DatabaseManager()

# 便捷函数
def get_db_session() -> Generator[Session, None, None]:
    """获取数据库会话的便捷函数"""
    return db_manager.get_session()

def init_database(database_url: Optional[str] = None):
    """初始化数据库的便捷函数"""
    db_manager.initialize(database_url)

def test_db_connection() -> bool:
    """测试数据库连接的便捷函数"""
    return db_manager.test_connection()

def get_db_info():
    """获取数据库信息的便捷函数"""
    return db_manager.get_table_info()

# 依赖注入函数（用于FastAPI）
def get_db() -> Generator[Session, None, None]:
    """FastAPI依赖注入函数"""
    with get_db_session() as session:
        yield session
