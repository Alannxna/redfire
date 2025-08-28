"""
数据库读写分离管理器
================

为RedFire量化交易平台提供数据库读写分离功能
支持主从数据库配置、读写路由、故障转移等
"""

import random
import time
from typing import Dict, List, Optional, Any, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
from contextlib import contextmanager, asynccontextmanager
import logging
import threading
from datetime import datetime, timedelta

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import QueuePool
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError, DisconnectionError

logger = logging.getLogger(__name__)


class DatabaseRole(str, Enum):
    """数据库角色"""
    MASTER = "master"
    SLAVE = "slave"
    READ_ONLY = "read_only"


class LoadBalanceStrategy(str, Enum):
    """负载均衡策略"""
    ROUND_ROBIN = "round_robin"
    RANDOM = "random"
    WEIGHTED = "weighted"
    LEAST_CONNECTIONS = "least_connections"


@dataclass
class DatabaseNodeConfig:
    """数据库节点配置"""
    host: str
    port: int
    username: str
    password: str
    database: str
    role: DatabaseRole
    weight: int = 1
    max_connections: int = 10
    
    # 健康检查配置
    health_check_interval: int = 30  # 秒
    max_failures: int = 3
    recovery_timeout: int = 60  # 秒
    
    # 连接配置
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    pool_recycle: int = 3600
    
    def build_url(self, async_mode: bool = False) -> str:
        """构建数据库连接URL"""
        driver = "mysql+aiomysql" if async_mode else "mysql+pymysql"
        
        from urllib.parse import quote_plus
        encoded_password = quote_plus(self.password)
        
        url = f"{driver}://{self.username}:{encoded_password}@{self.host}:{self.port}/{self.database}"
        params = [
            "charset=utf8mb4",
            "ssl_disabled=true",
            "autocommit=false"
        ]
        
        return f"{url}?{'&'.join(params)}"
    
    def get_engine_kwargs(self) -> Dict[str, Any]:
        """获取引擎配置"""
        return {
            "pool_size": self.pool_size,
            "max_overflow": self.max_overflow,
            "pool_timeout": self.pool_timeout,
            "pool_recycle": self.pool_recycle,
            "pool_pre_ping": True,
            "echo": False,
            "connect_args": {
                "charset": "utf8mb4",
                "autocommit": False
            }
        }


@dataclass
class DatabaseNode:
    """数据库节点"""
    config: DatabaseNodeConfig
    engine: Optional[Engine] = None
    async_engine = None
    session_factory: Optional[sessionmaker] = None
    async_session_factory = None
    
    # 状态信息
    is_healthy: bool = True
    failure_count: int = 0
    last_failure_time: Optional[datetime] = None
    last_health_check: Optional[datetime] = None
    active_connections: int = 0
    total_queries: int = 0
    
    def __post_init__(self):
        """初始化后处理"""
        self._lock = threading.RLock()
    
    def create_engine(self):
        """创建数据库引擎"""
        if self.engine is None:
            url = self.config.build_url(async_mode=False)
            engine_kwargs = self.config.get_engine_kwargs()
            
            self.engine = create_engine(url, **engine_kwargs)
            
            # 添加事件监听器
            @event.listens_for(self.engine, "checkout")
            def receive_checkout(dbapi_connection, connection_record, connection_proxy):
                with self._lock:
                    self.active_connections += 1
            
            @event.listens_for(self.engine, "checkin")
            def receive_checkin(dbapi_connection, connection_record):
                with self._lock:
                    self.active_connections = max(0, self.active_connections - 1)
            
            logger.info(f"创建数据库引擎: {self.config.host}:{self.config.port} ({self.config.role})")
    
    def create_async_engine(self):
        """创建异步数据库引擎"""
        if self.async_engine is None:
            url = self.config.build_url(async_mode=True)
            engine_kwargs = self.config.get_engine_kwargs()
            # 移除不支持的异步参数
            engine_kwargs.pop("connect_args", None)
            
            self.async_engine = create_async_engine(url, **engine_kwargs)
            logger.info(f"创建异步数据库引擎: {self.config.host}:{self.config.port} ({self.config.role})")
    
    def get_session_factory(self):
        """获取会话工厂"""
        if self.session_factory is None:
            if self.engine is None:
                self.create_engine()
            
            self.session_factory = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
        
        return self.session_factory
    
    def get_async_session_factory(self):
        """获取异步会话工厂"""
        if self.async_session_factory is None:
            if self.async_engine is None:
                self.create_async_engine()
            
            self.async_session_factory = async_sessionmaker(
                self.async_engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
        
        return self.async_session_factory
    
    def health_check(self) -> bool:
        """健康检查"""
        try:
            if self.engine is None:
                self.create_engine()
            
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            # 重置失败计数
            with self._lock:
                if not self.is_healthy:
                    logger.info(f"数据库节点恢复: {self.config.host}:{self.config.port}")
                
                self.is_healthy = True
                self.failure_count = 0
                self.last_failure_time = None
                self.last_health_check = datetime.now()
            
            return True
            
        except Exception as e:
            logger.error(f"数据库节点健康检查失败 {self.config.host}:{self.config.port}: {e}")
            
            with self._lock:
                self.failure_count += 1
                self.last_failure_time = datetime.now()
                self.last_health_check = datetime.now()
                
                if self.failure_count >= self.config.max_failures:
                    if self.is_healthy:
                        logger.warning(f"数据库节点标记为不健康: {self.config.host}:{self.config.port}")
                    self.is_healthy = False
            
            return False
    
    def can_recover(self) -> bool:
        """检查是否可以尝试恢复"""
        if self.is_healthy:
            return True
        
        if self.last_failure_time is None:
            return True
        
        recovery_time = self.last_failure_time + timedelta(seconds=self.config.recovery_timeout)
        return datetime.now() >= recovery_time
    
    def get_stats(self) -> Dict[str, Any]:
        """获取节点统计信息"""
        with self._lock:
            return {
                "host": f"{self.config.host}:{self.config.port}",
                "role": self.config.role,
                "weight": self.config.weight,
                "is_healthy": self.is_healthy,
                "failure_count": self.failure_count,
                "last_failure_time": self.last_failure_time,
                "last_health_check": self.last_health_check,
                "active_connections": self.active_connections,
                "total_queries": self.total_queries
            }
    
    def close(self):
        """关闭连接"""
        try:
            if self.engine:
                self.engine.dispose()
                logger.info(f"关闭数据库引擎: {self.config.host}:{self.config.port}")
            
            if self.async_engine:
                import asyncio
                asyncio.create_task(self.async_engine.adispose())
                logger.info(f"关闭异步数据库引擎: {self.config.host}:{self.config.port}")
                
        except Exception as e:
            logger.error(f"关闭数据库连接失败: {e}")


class LoadBalancer:
    """负载均衡器"""
    
    def __init__(self, strategy: LoadBalanceStrategy = LoadBalanceStrategy.ROUND_ROBIN):
        self.strategy = strategy
        self._round_robin_index = 0
        self._lock = threading.RLock()
    
    def select_node(self, nodes: List[DatabaseNode]) -> Optional[DatabaseNode]:
        """选择数据库节点"""
        healthy_nodes = [node for node in nodes if node.is_healthy]
        
        if not healthy_nodes:
            # 尝试恢复节点
            recovery_nodes = [node for node in nodes if node.can_recover()]
            for node in recovery_nodes:
                if node.health_check():
                    healthy_nodes = [node]
                    break
        
        if not healthy_nodes:
            logger.error("没有可用的数据库节点")
            return None
        
        if self.strategy == LoadBalanceStrategy.ROUND_ROBIN:
            return self._round_robin_select(healthy_nodes)
        elif self.strategy == LoadBalanceStrategy.RANDOM:
            return self._random_select(healthy_nodes)
        elif self.strategy == LoadBalanceStrategy.WEIGHTED:
            return self._weighted_select(healthy_nodes)
        elif self.strategy == LoadBalanceStrategy.LEAST_CONNECTIONS:
            return self._least_connections_select(healthy_nodes)
        else:
            return healthy_nodes[0]
    
    def _round_robin_select(self, nodes: List[DatabaseNode]) -> DatabaseNode:
        """轮询选择"""
        with self._lock:
            node = nodes[self._round_robin_index % len(nodes)]
            self._round_robin_index += 1
            return node
    
    def _random_select(self, nodes: List[DatabaseNode]) -> DatabaseNode:
        """随机选择"""
        return random.choice(nodes)
    
    def _weighted_select(self, nodes: List[DatabaseNode]) -> DatabaseNode:
        """加权选择"""
        total_weight = sum(node.config.weight for node in nodes)
        if total_weight == 0:
            return random.choice(nodes)
        
        random_weight = random.randint(1, total_weight)
        current_weight = 0
        
        for node in nodes:
            current_weight += node.config.weight
            if random_weight <= current_weight:
                return node
        
        return nodes[-1]
    
    def _least_connections_select(self, nodes: List[DatabaseNode]) -> DatabaseNode:
        """最少连接选择"""
        return min(nodes, key=lambda node: node.active_connections)


class ReadWriteSplitManager:
    """读写分离管理器"""
    
    def __init__(self, load_balance_strategy: LoadBalanceStrategy = LoadBalanceStrategy.ROUND_ROBIN):
        self.master_nodes: List[DatabaseNode] = []
        self.slave_nodes: List[DatabaseNode] = []
        self.read_load_balancer = LoadBalancer(load_balance_strategy)
        self.write_load_balancer = LoadBalancer(LoadBalanceStrategy.ROUND_ROBIN)  # 写操作使用轮询
        
        self._health_check_thread = None
        self._health_check_running = False
        
        # 统计信息
        self._stats = {
            "read_queries": 0,
            "write_queries": 0,
            "read_failures": 0,
            "write_failures": 0,
            "failovers": 0
        }
    
    def add_master_node(self, config: DatabaseNodeConfig):
        """添加主节点"""
        config.role = DatabaseRole.MASTER
        node = DatabaseNode(config)
        self.master_nodes.append(node)
        logger.info(f"添加主数据库节点: {config.host}:{config.port}")
    
    def add_slave_node(self, config: DatabaseNodeConfig):
        """添加从节点"""
        config.role = DatabaseRole.SLAVE
        node = DatabaseNode(config)
        self.slave_nodes.append(node)
        logger.info(f"添加从数据库节点: {config.host}:{config.port}")
    
    def start_health_check(self, interval: int = 30):
        """启动健康检查"""
        if self._health_check_running:
            return
        
        self._health_check_running = True
        
        def health_check_worker():
            while self._health_check_running:
                try:
                    # 检查主节点
                    for node in self.master_nodes:
                        node.health_check()
                    
                    # 检查从节点
                    for node in self.slave_nodes:
                        node.health_check()
                    
                    time.sleep(interval)
                    
                except Exception as e:
                    logger.error(f"健康检查异常: {e}")
                    time.sleep(5)  # 异常时短暂等待
        
        self._health_check_thread = threading.Thread(
            target=health_check_worker, 
            daemon=True, 
            name="DatabaseHealthCheck"
        )
        self._health_check_thread.start()
        logger.info("数据库健康检查已启动")
    
    def stop_health_check(self):
        """停止健康检查"""
        self._health_check_running = False
        if self._health_check_thread and self._health_check_thread.is_alive():
            self._health_check_thread.join(timeout=5)
        logger.info("数据库健康检查已停止")
    
    def get_read_node(self) -> Optional[DatabaseNode]:
        """获取读节点"""
        # 优先使用从节点
        if self.slave_nodes:
            node = self.read_load_balancer.select_node(self.slave_nodes)
            if node:
                return node
        
        # 从节点不可用时，使用主节点
        if self.master_nodes:
            node = self.read_load_balancer.select_node(self.master_nodes)
            if node:
                self._stats["failovers"] += 1
                logger.warning("从节点不可用，读操作转移到主节点")
                return node
        
        return None
    
    def get_write_node(self) -> Optional[DatabaseNode]:
        """获取写节点"""
        return self.write_load_balancer.select_node(self.master_nodes)
    
    @contextmanager
    def get_read_session(self):
        """获取读会话"""
        node = self.get_read_node()
        if not node:
            raise RuntimeError("没有可用的读数据库节点")
        
        session_factory = node.get_session_factory()
        session = session_factory()
        
        try:
            with node._lock:
                node.total_queries += 1
            self._stats["read_queries"] += 1
            
            yield session
            session.commit()
            
        except Exception as e:
            session.rollback()
            self._stats["read_failures"] += 1
            logger.error(f"读操作失败: {e}")
            raise
        finally:
            session.close()
    
    @contextmanager
    def get_write_session(self):
        """获取写会话"""
        node = self.get_write_node()
        if not node:
            raise RuntimeError("没有可用的写数据库节点")
        
        session_factory = node.get_session_factory()
        session = session_factory()
        
        try:
            with node._lock:
                node.total_queries += 1
            self._stats["write_queries"] += 1
            
            yield session
            session.commit()
            
        except Exception as e:
            session.rollback()
            self._stats["write_failures"] += 1
            logger.error(f"写操作失败: {e}")
            raise
        finally:
            session.close()
    
    @asynccontextmanager
    async def get_async_read_session(self):
        """获取异步读会话"""
        node = self.get_read_node()
        if not node:
            raise RuntimeError("没有可用的读数据库节点")
        
        session_factory = node.get_async_session_factory()
        
        async with session_factory() as session:
            try:
                with node._lock:
                    node.total_queries += 1
                self._stats["read_queries"] += 1
                
                yield session
                await session.commit()
                
            except Exception as e:
                await session.rollback()
                self._stats["read_failures"] += 1
                logger.error(f"异步读操作失败: {e}")
                raise
    
    @asynccontextmanager
    async def get_async_write_session(self):
        """获取异步写会话"""
        node = self.get_write_node()
        if not node:
            raise RuntimeError("没有可用的写数据库节点")
        
        session_factory = node.get_async_session_factory()
        
        async with session_factory() as session:
            try:
                with node._lock:
                    node.total_queries += 1
                self._stats["write_queries"] += 1
                
                yield session
                await session.commit()
                
            except Exception as e:
                await session.rollback()
                self._stats["write_failures"] += 1
                logger.error(f"异步写操作失败: {e}")
                raise
    
    def get_all_stats(self) -> Dict[str, Any]:
        """获取所有统计信息"""
        stats = self._stats.copy()
        
        # 添加节点统计
        stats["master_nodes"] = [node.get_stats() for node in self.master_nodes]
        stats["slave_nodes"] = [node.get_stats() for node in self.slave_nodes]
        
        # 计算健康节点数量
        healthy_masters = sum(1 for node in self.master_nodes if node.is_healthy)
        healthy_slaves = sum(1 for node in self.slave_nodes if node.is_healthy)
        
        stats["healthy_master_nodes"] = healthy_masters
        stats["healthy_slave_nodes"] = healthy_slaves
        stats["total_master_nodes"] = len(self.master_nodes)
        stats["total_slave_nodes"] = len(self.slave_nodes)
        
        return stats
    
    def reset_stats(self):
        """重置统计信息"""
        for key in self._stats:
            self._stats[key] = 0
        
        # 重置节点统计
        for node in self.master_nodes + self.slave_nodes:
            with node._lock:
                node.total_queries = 0
    
    def close_all(self):
        """关闭所有连接"""
        self.stop_health_check()
        
        for node in self.master_nodes + self.slave_nodes:
            node.close()
        
        logger.info("所有数据库连接已关闭")


# 全局读写分离管理器
_rw_split_manager: Optional[ReadWriteSplitManager] = None


def get_rw_split_manager() -> ReadWriteSplitManager:
    """获取读写分离管理器"""
    global _rw_split_manager
    if _rw_split_manager is None:
        _rw_split_manager = ReadWriteSplitManager()
        
        # 从环境变量配置主从节点
        import os
        
        # 主节点配置
        master_config = DatabaseNodeConfig(
            host=os.getenv("DB_MASTER_HOST", os.getenv("DB_HOST", "localhost")),
            port=int(os.getenv("DB_MASTER_PORT", os.getenv("DB_PORT", "3306"))),
            username=os.getenv("DB_MASTER_USER", os.getenv("DB_USER", "root")),
            password=os.getenv("DB_MASTER_PASSWORD", os.getenv("DB_PASSWORD", "root")),
            database=os.getenv("DB_MASTER_NAME", os.getenv("DB_NAME", "vnpy")),
            role=DatabaseRole.MASTER,
            weight=1
        )
        _rw_split_manager.add_master_node(master_config)
        
        # 从节点配置（如果配置了的话）
        slave_host = os.getenv("DB_SLAVE_HOST")
        if slave_host:
            slave_config = DatabaseNodeConfig(
                host=slave_host,
                port=int(os.getenv("DB_SLAVE_PORT", "3306")),
                username=os.getenv("DB_SLAVE_USER", os.getenv("DB_USER", "root")),
                password=os.getenv("DB_SLAVE_PASSWORD", os.getenv("DB_PASSWORD", "root")),
                database=os.getenv("DB_SLAVE_NAME", os.getenv("DB_NAME", "vnpy")),
                role=DatabaseRole.SLAVE,
                weight=1
            )
            _rw_split_manager.add_slave_node(slave_config)
        
        # 启动健康检查
        _rw_split_manager.start_health_check()
    
    return _rw_split_manager


def init_rw_split_manager(manager: ReadWriteSplitManager):
    """初始化读写分离管理器"""
    global _rw_split_manager
    _rw_split_manager = manager


# 便捷函数
def get_read_session():
    """获取读会话（用于FastAPI依赖注入）"""
    manager = get_rw_split_manager()
    with manager.get_read_session() as session:
        yield session


def get_write_session():
    """获取写会话（用于FastAPI依赖注入）"""
    manager = get_rw_split_manager()
    with manager.get_write_session() as session:
        yield session


async def get_async_read_session():
    """获取异步读会话"""
    manager = get_rw_split_manager()
    async with manager.get_async_read_session() as session:
        yield session


async def get_async_write_session():
    """获取异步写会话"""
    manager = get_rw_split_manager()
    async with manager.get_async_write_session() as session:
        yield session
