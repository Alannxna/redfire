"""
数据库连接管理
==============

提供统一的数据库连接和管理功能
"""

import logging
from typing import Optional
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

logger = logging.getLogger(__name__)

# 导入认证模型的Base
try:
    from auth.models import Base
except ImportError:
    # 如果认证模型不可用，创建一个默认的Base
    Base = declarative_base()


class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self):
        self.engine = None
        self.SessionLocal = None
        self.database_url: Optional[str] = None
        
    async def initialize(self, database_url: str):
        """初始化数据库连接"""
        try:
            self.database_url = database_url
            
            # 创建引擎
            if database_url.startswith('sqlite'):
                # SQLite特殊配置
                self.engine = create_engine(
                    database_url,
                    connect_args={"check_same_thread": False},
                    poolclass=StaticPool,
                    echo=False
                )
            else:
                # MySQL/PostgreSQL配置
                self.engine = create_engine(
                    database_url,
                    pool_size=10,
                    max_overflow=20,
                    pool_timeout=30,
                    pool_recycle=3600,
                    echo=False
                )
            
            # 创建会话工厂
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            
            # 测试连接
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            logger.info(f"数据库连接初始化成功: {database_url}")
            
        except Exception as e:
            logger.error(f"数据库连接初始化失败: {e}")
            raise
    
    def get_session(self):
        """获取数据库会话"""
        if not self.SessionLocal:
            raise RuntimeError("数据库未初始化")
        return self.SessionLocal()
    
    def create_tables(self):
        """创建所有表"""
        if not self.engine:
            raise RuntimeError("数据库引擎未初始化")
        
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("数据库表创建完成")
        except Exception as e:
            logger.error(f"创建数据库表失败: {e}")
            raise
    
    async def close(self):
        """关闭数据库连接"""
        if self.engine:
            self.engine.dispose()
            logger.info("数据库连接已关闭")


# 全局数据库管理器实例
_db_manager: Optional[DatabaseManager] = None


def get_database_manager() -> DatabaseManager:
    """获取数据库管理器"""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager


def get_db():
    """获取数据库会话依赖"""
    db_manager = get_database_manager()
    db = db_manager.get_session()
    try:
        yield db
    finally:
        db.close()