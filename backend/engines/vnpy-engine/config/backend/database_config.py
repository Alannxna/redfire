"""
数据库配置管理模块
支持MySQL、PostgreSQL、SQLite等多种数据库
"""

from typing import Dict, Optional, Any, Union
from pydantic import BaseModel, Field, validator
from enum import Enum
import os
from pathlib import Path
from urllib.parse import quote_plus
from loguru import logger


class DatabaseType(str, Enum):
    """支持的数据库类型"""
    SQLITE = "sqlite"
    MYSQL = "mysql"
    POSTGRESQL = "postgresql"
    MARIADB = "mariadb"


class DatabaseConfig(BaseModel):
    """数据库配置模型"""
    
    # 数据库类型
    db_type: DatabaseType = Field(default=DatabaseType.SQLITE, description="数据库类型")
    
    # 数据库URL（可选，优先使用）
    database_url: Optional[str] = Field(default=None, description="数据库连接URL")
    
    # 连接参数
    host: Optional[str] = Field(default=None, description="数据库主机")
    port: Optional[int] = Field(default=None, description="数据库端口")
    username: Optional[str] = Field(default=None, description="用户名")
    password: Optional[str] = Field(default=None, description="密码")
    database: Optional[str] = Field(default=None, description="数据库名")
    
    # SQLite特定参数
    sqlite_path: Optional[str] = Field(default=None, description="SQLite文件路径")
    
    # 连接池配置
    pool_size: int = Field(default=10, description="连接池大小")
    max_overflow: int = Field(default=20, description="最大溢出连接数")
    pool_timeout: int = Field(default=30, description="连接池超时时间")
    pool_recycle: int = Field(default=3600, description="连接回收时间")
    pool_pre_ping: bool = Field(default=True, description="连接前ping检查")
    
    # 其他配置
    echo: bool = Field(default=False, description="是否打印SQL语句")
    charset: str = Field(default="utf8mb4", description="字符集")
    timezone: str = Field(default="+08:00", description="时区")
    
    # SSL配置
    ssl_ca: Optional[str] = Field(default=None, description="SSL CA证书路径")
    ssl_cert: Optional[str] = Field(default=None, description="SSL客户端证书路径")
    ssl_key: Optional[str] = Field(default=None, description="SSL客户端密钥路径")
    ssl_disabled: bool = Field(default=False, description="是否禁用SSL")
    
    @validator('port')
    def validate_port(cls, v, values):
        """验证端口号"""
        if v is not None and (v < 1 or v > 65535):
            raise ValueError('端口号必须在1-65535之间')
        return v
    
    @validator('db_type')
    def validate_db_type(cls, v):
        """验证数据库类型"""
        if v not in DatabaseType:
            raise ValueError(f'不支持的数据库类型: {v}')
        return v
    
    def get_default_port(self) -> int:
        """获取默认端口"""
        port_map = {
            DatabaseType.MYSQL: 3306,
            DatabaseType.POSTGRESQL: 5432,
            DatabaseType.MARIADB: 3306,
            DatabaseType.SQLITE: None
        }
        return port_map.get(self.db_type)
    
    def get_driver_name(self) -> str:
        """获取驱动名称"""
        driver_map = {
            DatabaseType.MYSQL: "mysql+pymysql",
            DatabaseType.POSTGRESQL: "postgresql+psycopg2",
            DatabaseType.MARIADB: "mysql+pymysql",
            DatabaseType.SQLITE: "sqlite"
        }
        return driver_map.get(self.db_type, "sqlite")
    
    def get_async_driver_name(self) -> str:
        """获取异步驱动名称"""
        async_driver_map = {
            DatabaseType.MYSQL: "mysql+aiomysql",
            DatabaseType.POSTGRESQL: "postgresql+asyncpg",
            DatabaseType.MARIADB: "mysql+aiomysql",
            DatabaseType.SQLITE: "sqlite+aiosqlite"
        }
        return async_driver_map.get(self.db_type, "sqlite+aiosqlite")
    
    def build_connection_url(self, async_mode: bool = False) -> str:
        """构建数据库连接URL"""
        if self.db_type == DatabaseType.SQLITE:
            return self._build_sqlite_url(async_mode)
        else:
            return self._build_server_url(async_mode)
    
    def _build_sqlite_url(self, async_mode: bool = False) -> str:
        """构建SQLite连接URL"""
        driver = self.get_async_driver_name() if async_mode else self.get_driver_name()
        
        if self.sqlite_path:
            db_path = self.sqlite_path
        else:
            # 默认路径
            from .path_config import get_path_config
            path_config = get_path_config()
            db_path = str(path_config.data_dir / "vnpy_web.db")
        
        # 确保目录存在
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        return f"{driver}:///{db_path}"
    
    def _build_server_url(self, async_mode: bool = False) -> str:
        """构建服务器数据库连接URL"""
        driver = self.get_async_driver_name() if async_mode else self.get_driver_name()
        
        # 验证必需参数
        if not all([self.host, self.username, self.password, self.database]):
            raise ValueError(f"{self.db_type}数据库需要提供host、username、password、database参数")
        
        # URL编码密码中的特殊字符
        encoded_password = quote_plus(self.password)
        
        # 获取端口
        port = self.port or self.get_default_port()
        
        # 构建基础URL
        url = f"{driver}://{self.username}:{encoded_password}@{self.host}:{port}/{self.database}"
        
        # 添加查询参数
        params = []
        
        if self.db_type in [DatabaseType.MYSQL, DatabaseType.MARIADB]:
            params.append(f"charset={self.charset}")
            if not self.ssl_disabled and not any([self.ssl_ca, self.ssl_cert, self.ssl_key]):
                params.append("ssl_disabled=true")
        
        if self.db_type == DatabaseType.POSTGRESQL:
            params.append("client_encoding=utf8")
        
        # 添加SSL参数
        if self.ssl_ca:
            params.append(f"ssl_ca={self.ssl_ca}")
        if self.ssl_cert:
            params.append(f"ssl_cert={self.ssl_cert}")
        if self.ssl_key:
            params.append(f"ssl_key={self.ssl_key}")
        
        if params:
            url += "?" + "&".join(params)
        
        return url
    
    def get_engine_kwargs(self) -> Dict[str, Any]:
        """获取数据库引擎参数"""
        kwargs = {
            "echo": self.echo,
            "pool_pre_ping": self.pool_pre_ping,
        }
        
        if self.db_type != DatabaseType.SQLITE:
            kwargs.update({
                "pool_size": self.pool_size,
                "max_overflow": self.max_overflow,
                "pool_timeout": self.pool_timeout,
                "pool_recycle": self.pool_recycle,
            })
        else:
            # SQLite特定配置
            kwargs["connect_args"] = {"check_same_thread": False}
        
        return kwargs
    
    def test_connection(self) -> bool:
        """测试数据库连接"""
        try:
            from sqlalchemy import create_engine
            
            url = self.build_connection_url(async_mode=False)
            engine_kwargs = self.get_engine_kwargs()
            
            from sqlalchemy import text
            engine = create_engine(url, **engine_kwargs)
            
            with engine.connect() as conn:
                if self.db_type == DatabaseType.SQLITE:
                    conn.execute(text("SELECT 1"))
                elif self.db_type in [DatabaseType.MYSQL, DatabaseType.MARIADB]:
                    conn.execute(text("SELECT 1"))
                elif self.db_type == DatabaseType.POSTGRESQL:
                    conn.execute(text("SELECT 1"))
            
            engine.dispose()
            return True
            
        except Exception as e:
            logger.error(f"数据库连接测试失败: {e}")
            return False
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return self.dict(exclude_none=True)
    
    @classmethod
    def from_env(cls) -> "DatabaseConfig":
        """从环境变量创建配置"""
        # 确保加载config.env文件
        try:
            from dotenv import load_dotenv
            load_dotenv("config.env", override=False)
        except ImportError:
            pass
        
        # 检查DATABASE_URL环境变量
        database_url = os.getenv("DATABASE_URL")
        if database_url:
            return cls.from_url(database_url)
        
        # 从单独的环境变量创建
        db_type = os.getenv("DB_TYPE", "sqlite").lower()
        
        config_data = {
            "db_type": db_type,
            "host": os.getenv("DB_HOST"),
            "port": int(os.getenv("DB_PORT")) if os.getenv("DB_PORT") else None,
            "username": os.getenv("DB_USER") or os.getenv("DB_USERNAME"),
            "password": os.getenv("DB_PASSWORD"),
            "database": os.getenv("DB_NAME") or os.getenv("DB_DATABASE"),
            "sqlite_path": os.getenv("DB_SQLITE_PATH"),
            "charset": os.getenv("DB_CHARSET", "utf8mb4"),
            "echo": os.getenv("DB_ECHO", "false").lower() == "true",
        }
        
        # 移除None值
        config_data = {k: v for k, v in config_data.items() if v is not None}
        
        return cls(**config_data)
    
    @classmethod
    def from_url(cls, url: str) -> "DatabaseConfig":
        """从数据库URL创建配置"""
        from urllib.parse import urlparse, parse_qs
        
        parsed = urlparse(url)
        
        # 解析数据库类型
        scheme = parsed.scheme.lower()
        if scheme.startswith("sqlite"):
            db_type = DatabaseType.SQLITE
            sqlite_path = parsed.path.lstrip("/")
        elif scheme.startswith("mysql"):
            db_type = DatabaseType.MYSQL
        elif scheme.startswith("postgresql"):
            db_type = DatabaseType.POSTGRESQL
        elif scheme.startswith("mariadb"):
            db_type = DatabaseType.MARIADB
        else:
            raise ValueError(f"不支持的数据库URL: {url}")
        
        config_data = {"db_type": db_type}
        
        if db_type == DatabaseType.SQLITE:
            config_data["sqlite_path"] = sqlite_path
        else:
            config_data.update({
                "host": parsed.hostname,
                "port": parsed.port,
                "username": parsed.username,
                "password": parsed.password,
                "database": parsed.path.lstrip("/"),
            })
            
            # 解析查询参数
            query_params = parse_qs(parsed.query)
            if "charset" in query_params:
                config_data["charset"] = query_params["charset"][0]
        
        return cls(**config_data)


class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self._engine = None
        self._async_engine = None
        self._session_factory = None
        self._async_session_factory = None
    
    @property
    def engine(self):
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
        from sqlalchemy import create_engine
        
        url = self.config.build_connection_url(async_mode=False)
        kwargs = self.config.get_engine_kwargs()
        
        self._engine = create_engine(url, **kwargs)
        logger.info(f"创建同步数据库引擎: {self.config.db_type}")
    
    def _create_async_engine(self):
        """创建异步数据库引擎"""
        from sqlalchemy.ext.asyncio import create_async_engine
        
        url = self.config.build_connection_url(async_mode=True)
        kwargs = self.config.get_engine_kwargs()
        # 异步引擎不支持某些参数
        kwargs.pop("connect_args", None)
        
        self._async_engine = create_async_engine(url, **kwargs)
        logger.info(f"创建异步数据库引擎: {self.config.db_type}")
    
    def get_session_factory(self):
        """获取同步会话工厂"""
        if self._session_factory is None:
            from sqlalchemy.orm import sessionmaker
            self._session_factory = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
        return self._session_factory
    
    def get_async_session_factory(self):
        """获取异步会话工厂"""
        if self._async_session_factory is None:
            from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
            self._async_session_factory = async_sessionmaker(
                self.async_engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
        return self._async_session_factory
    
    def create_tables(self, base):
        """创建数据表"""
        base.metadata.create_all(bind=self.engine)
        logger.info("数据表创建完成")
    
    async def create_tables_async(self, base):
        """异步创建数据表"""
        async with self.async_engine.begin() as conn:
            await conn.run_sync(base.metadata.create_all)
        logger.info("异步数据表创建完成")
    
    def drop_tables(self, base):
        """删除数据表"""
        base.metadata.drop_all(bind=self.engine)
        logger.info("数据表删除完成")
    
    async def drop_tables_async(self, base):
        """异步删除数据表"""
        async with self.async_engine.begin() as conn:
            await conn.run_sync(base.metadata.drop_all)
        logger.info("异步数据表删除完成")
    
    def test_connection(self) -> bool:
        """测试连接"""
        return self.config.test_connection()
    
    def close(self):
        """关闭连接"""
        if self._engine:
            self._engine.dispose()
        if self._async_engine:
            self._async_engine.sync_close()
        logger.info("数据库连接已关闭")


# 全局数据库配置实例
_db_config: Optional[DatabaseConfig] = None
_db_manager: Optional[DatabaseManager] = None


def get_database_config() -> DatabaseConfig:
    """获取数据库配置"""
    global _db_config
    if _db_config is None:
        _db_config = DatabaseConfig.from_env()
    return _db_config


def set_database_config(config: DatabaseConfig):
    """设置数据库配置"""
    global _db_config, _db_manager
    _db_config = config
    _db_manager = None  # 重置管理器


def get_database_manager() -> DatabaseManager:
    """获取数据库管理器"""
    global _db_manager
    if _db_manager is None:
        config = get_database_config()
        _db_manager = DatabaseManager(config)
    return _db_manager


def create_database_config_from_dict(config_dict: Dict[str, Any]) -> DatabaseConfig:
    """从字典创建数据库配置"""
    return DatabaseConfig(**config_dict)


def create_mysql_config(
    host: str,
    username: str,
    password: str,
    database: str,
    port: int = 3306,
    **kwargs
) -> DatabaseConfig:
    """创建MySQL配置"""
    return DatabaseConfig(
        db_type=DatabaseType.MYSQL,
        host=host,
        port=port,
        username=username,
        password=password,
        database=database,
        **kwargs
    )


def create_sqlite_config(
    sqlite_path: Optional[str] = None,
    **kwargs
) -> DatabaseConfig:
    """创建SQLite配置"""
    return DatabaseConfig(
        db_type=DatabaseType.SQLITE,
        sqlite_path=sqlite_path,
        **kwargs
    )


def create_postgresql_config(
    host: str,
    username: str,
    password: str,
    database: str,
    port: int = 5432,
    **kwargs
) -> DatabaseConfig:
    """创建PostgreSQL配置"""
    return DatabaseConfig(
        db_type=DatabaseType.POSTGRESQL,
        host=host,
        port=port,
        username=username,
        password=password,
        database=database,
        **kwargs
    )