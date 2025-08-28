"""
MongoDB日志存储管理器
==================

为RedFire量化交易平台提供高效的日志存储和查询功能
支持结构化日志、操作审计、系统监控等数据的存储管理
"""

import os
from typing import Dict, List, Optional, Any, Union, AsyncGenerator
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import logging
import json
import asyncio
from urllib.parse import quote_plus

try:
    from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection
    import pymongo
    from pymongo import MongoClient
    from pymongo.errors import PyMongoError, ConnectionFailure, ServerSelectionTimeoutError
    from bson import ObjectId
    MONGODB_AVAILABLE = True
except ImportError:
    MONGODB_AVAILABLE = False

logger = logging.getLogger(__name__)


class LogLevel(str, Enum):
    """日志级别"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogCategory(str, Enum):
    """日志分类"""
    SYSTEM = "system"
    TRADING = "trading"
    STRATEGY = "strategy"
    API = "api"
    DATABASE = "database"
    SECURITY = "security"
    PERFORMANCE = "performance"
    AUDIT = "audit"


@dataclass
class MongoDBConfig:
    """MongoDB配置"""
    host: str = "localhost"
    port: int = 27017
    username: Optional[str] = None
    password: Optional[str] = None
    database: str = "redfire_logs"
    auth_source: str = "admin"
    
    # 连接配置
    max_pool_size: int = 50
    min_pool_size: int = 0
    max_idle_time_ms: int = 30000
    server_selection_timeout_ms: int = 30000
    connect_timeout_ms: int = 20000
    socket_timeout_ms: int = 20000
    
    # SSL配置
    tls: bool = False
    tls_ca_file: Optional[str] = None
    tls_cert_file: Optional[str] = None
    tls_key_file: Optional[str] = None
    
    # 其他配置
    replica_set: Optional[str] = None
    read_preference: str = "primaryPreferred"
    write_concern: int = 1
    
    def build_uri(self) -> str:
        """构建MongoDB连接URI"""
        if self.username and self.password:
            auth_part = f"{quote_plus(self.username)}:{quote_plus(self.password)}@"
        else:
            auth_part = ""
        
        uri = f"mongodb://{auth_part}{self.host}:{self.port}/{self.database}"
        
        # 添加查询参数
        params = []
        if self.auth_source:
            params.append(f"authSource={self.auth_source}")
        if self.replica_set:
            params.append(f"replicaSet={self.replica_set}")
        if self.tls:
            params.append("tls=true")
        
        params.extend([
            f"maxPoolSize={self.max_pool_size}",
            f"minPoolSize={self.min_pool_size}",
            f"maxIdleTimeMS={self.max_idle_time_ms}",
            f"serverSelectionTimeoutMS={self.server_selection_timeout_ms}",
            f"connectTimeoutMS={self.connect_timeout_ms}",
            f"socketTimeoutMS={self.socket_timeout_ms}",
            f"readPreference={self.read_preference}",
            f"w={self.write_concern}"
        ])
        
        if params:
            uri += "?" + "&".join(params)
        
        return uri
    
    @classmethod
    def from_env(cls) -> "MongoDBConfig":
        """从环境变量创建配置"""
        return cls(
            host=os.getenv("MONGO_HOST", "localhost"),
            port=int(os.getenv("MONGO_PORT", "27017")),
            username=os.getenv("MONGO_USER"),
            password=os.getenv("MONGO_PASSWORD"),
            database=os.getenv("MONGO_DATABASE", "redfire_logs"),
            auth_source=os.getenv("MONGO_AUTH_SOURCE", "admin"),
            max_pool_size=int(os.getenv("MONGO_MAX_POOL_SIZE", "50")),
            tls=os.getenv("MONGO_TLS", "false").lower() == "true"
        )


@dataclass
class LogEntry:
    """日志条目"""
    level: LogLevel
    category: LogCategory
    message: str
    timestamp: datetime = field(default_factory=datetime.now)
    source: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    
    # 额外数据
    data: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    
    # 异常信息
    exception: Optional[str] = None
    stack_trace: Optional[str] = None
    
    # 性能数据
    duration_ms: Optional[float] = None
    memory_usage: Optional[int] = None
    cpu_usage: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        doc = {
            "timestamp": self.timestamp,
            "level": self.level,
            "category": self.category,
            "message": self.message,
        }
        
        # 添加可选字段
        optional_fields = [
            "source", "user_id", "session_id", "request_id",
            "data", "tags", "exception", "stack_trace",
            "duration_ms", "memory_usage", "cpu_usage"
        ]
        
        for field in optional_fields:
            value = getattr(self, field)
            if value is not None:
                doc[field] = value
        
        return doc


class MongoDBManager:
    """MongoDB管理器"""
    
    def __init__(self, config: MongoDBConfig):
        if not MONGODB_AVAILABLE:
            raise RuntimeError("MongoDB不可用，请安装motor和pymongo包")
        
        self.config = config
        self._client: Optional[AsyncIOMotorClient] = None
        self._sync_client: Optional[MongoClient] = None
        self._database: Optional[AsyncIOMotorDatabase] = None
        self._sync_database = None
        
        # 统计信息
        self._stats = {
            "documents_inserted": 0,
            "documents_queried": 0,
            "documents_updated": 0,
            "documents_deleted": 0,
            "errors": 0,
            "last_operation_time": None
        }
    
    @property
    def client(self) -> AsyncIOMotorClient:
        """获取异步MongoDB客户端"""
        if self._client is None:
            self._connect()
        return self._client
    
    @property
    def sync_client(self) -> MongoClient:
        """获取同步MongoDB客户端"""
        if self._sync_client is None:
            self._connect_sync()
        return self._sync_client
    
    @property
    def database(self) -> AsyncIOMotorDatabase:
        """获取异步数据库对象"""
        if self._database is None:
            self._database = self.client[self.config.database]
        return self._database
    
    @property
    def sync_database(self):
        """获取同步数据库对象"""
        if self._sync_database is None:
            self._sync_database = self.sync_client[self.config.database]
        return self._sync_database
    
    def _connect(self):
        """异步连接到MongoDB"""
        try:
            uri = self.config.build_uri()
            self._client = AsyncIOMotorClient(uri)
            logger.info(f"MongoDB异步连接成功: {self.config.host}:{self.config.port}")
            
        except Exception as e:
            logger.error(f"MongoDB异步连接失败: {e}")
            raise
    
    def _connect_sync(self):
        """同步连接到MongoDB"""
        try:
            uri = self.config.build_uri()
            self._sync_client = MongoClient(uri)
            
            # 测试连接
            self._sync_client.admin.command('ping')
            logger.info(f"MongoDB同步连接成功: {self.config.host}:{self.config.port}")
            
        except Exception as e:
            logger.error(f"MongoDB同步连接失败: {e}")
            raise
    
    async def test_connection(self) -> bool:
        """测试连接"""
        try:
            await self.client.admin.command('ping')
            logger.info("MongoDB连接测试成功")
            return True
        except Exception as e:
            logger.error(f"MongoDB连接测试失败: {e}")
            return False
    
    def test_sync_connection(self) -> bool:
        """同步测试连接"""
        try:
            self.sync_client.admin.command('ping')
            logger.info("MongoDB同步连接测试成功")
            return True
        except Exception as e:
            logger.error(f"MongoDB同步连接测试失败: {e}")
            return False
    
    async def create_indexes(self):
        """创建索引"""
        try:
            # 日志集合索引
            logs_collection = self.database.logs
            await logs_collection.create_index([("timestamp", -1)])
            await logs_collection.create_index([("level", 1)])
            await logs_collection.create_index([("category", 1)])
            await logs_collection.create_index([("source", 1)])
            await logs_collection.create_index([("user_id", 1)])
            await logs_collection.create_index([("session_id", 1)])
            await logs_collection.create_index([("request_id", 1)])
            await logs_collection.create_index([("tags", 1)])
            
            # 复合索引
            await logs_collection.create_index([("category", 1), ("timestamp", -1)])
            await logs_collection.create_index([("level", 1), ("timestamp", -1)])
            await logs_collection.create_index([("user_id", 1), ("timestamp", -1)])
            
            # 审计日志集合索引
            audit_collection = self.database.audit_logs
            await audit_collection.create_index([("timestamp", -1)])
            await audit_collection.create_index([("user_id", 1)])
            await audit_collection.create_index([("action", 1)])
            await audit_collection.create_index([("resource", 1)])
            
            # 性能监控集合索引
            metrics_collection = self.database.performance_metrics
            await metrics_collection.create_index([("timestamp", -1)])
            await metrics_collection.create_index([("metric_type", 1)])
            await metrics_collection.create_index([("source", 1)])
            
            logger.info("MongoDB索引创建完成")
            
        except Exception as e:
            logger.error(f"创建MongoDB索引失败: {e}")
            raise
    
    def get_collection(self, collection_name: str) -> AsyncIOMotorCollection:
        """获取集合"""
        return self.database[collection_name]
    
    def get_sync_collection(self, collection_name: str):
        """获取同步集合"""
        return self.sync_database[collection_name]
    
    async def insert_document(self, collection_name: str, document: Dict[str, Any]) -> Optional[str]:
        """插入文档"""
        try:
            collection = self.get_collection(collection_name)
            result = await collection.insert_one(document)
            
            self._stats["documents_inserted"] += 1
            self._stats["last_operation_time"] = datetime.now()
            
            return str(result.inserted_id)
            
        except Exception as e:
            logger.error(f"插入文档失败: {e}")
            self._stats["errors"] += 1
            return None
    
    async def insert_documents(self, collection_name: str, documents: List[Dict[str, Any]]) -> List[str]:
        """批量插入文档"""
        try:
            if not documents:
                return []
            
            collection = self.get_collection(collection_name)
            result = await collection.insert_many(documents)
            
            self._stats["documents_inserted"] += len(documents)
            self._stats["last_operation_time"] = datetime.now()
            
            return [str(obj_id) for obj_id in result.inserted_ids]
            
        except Exception as e:
            logger.error(f"批量插入文档失败: {e}")
            self._stats["errors"] += 1
            return []
    
    async def find_documents(self, collection_name: str, filter_dict: Dict[str, Any] = None,
                           projection: Dict[str, int] = None, sort: List[tuple] = None,
                           limit: int = None, skip: int = 0) -> List[Dict[str, Any]]:
        """查询文档"""
        try:
            collection = self.get_collection(collection_name)
            cursor = collection.find(filter_dict or {}, projection)
            
            if sort:
                cursor = cursor.sort(sort)
            if skip > 0:
                cursor = cursor.skip(skip)
            if limit:
                cursor = cursor.limit(limit)
            
            documents = await cursor.to_list(length=limit)
            
            # 转换ObjectId为字符串
            for doc in documents:
                if "_id" in doc:
                    doc["_id"] = str(doc["_id"])
            
            self._stats["documents_queried"] += len(documents)
            self._stats["last_operation_time"] = datetime.now()
            
            return documents
            
        except Exception as e:
            logger.error(f"查询文档失败: {e}")
            self._stats["errors"] += 1
            return []
    
    async def count_documents(self, collection_name: str, filter_dict: Dict[str, Any] = None) -> int:
        """统计文档数量"""
        try:
            collection = self.get_collection(collection_name)
            count = await collection.count_documents(filter_dict or {})
            return count
            
        except Exception as e:
            logger.error(f"统计文档数量失败: {e}")
            self._stats["errors"] += 1
            return 0
    
    async def update_document(self, collection_name: str, filter_dict: Dict[str, Any],
                            update_dict: Dict[str, Any]) -> bool:
        """更新文档"""
        try:
            collection = self.get_collection(collection_name)
            result = await collection.update_one(filter_dict, {"$set": update_dict})
            
            if result.modified_count > 0:
                self._stats["documents_updated"] += result.modified_count
                self._stats["last_operation_time"] = datetime.now()
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"更新文档失败: {e}")
            self._stats["errors"] += 1
            return False
    
    async def delete_documents(self, collection_name: str, filter_dict: Dict[str, Any]) -> int:
        """删除文档"""
        try:
            collection = self.get_collection(collection_name)
            result = await collection.delete_many(filter_dict)
            
            self._stats["documents_deleted"] += result.deleted_count
            self._stats["last_operation_time"] = datetime.now()
            
            return result.deleted_count
            
        except Exception as e:
            logger.error(f"删除文档失败: {e}")
            self._stats["errors"] += 1
            return 0
    
    async def aggregate(self, collection_name: str, pipeline: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """聚合查询"""
        try:
            collection = self.get_collection(collection_name)
            cursor = collection.aggregate(pipeline)
            
            results = await cursor.to_list(length=None)
            
            # 转换ObjectId为字符串
            for result in results:
                if "_id" in result and isinstance(result["_id"], ObjectId):
                    result["_id"] = str(result["_id"])
            
            self._stats["documents_queried"] += len(results)
            self._stats["last_operation_time"] = datetime.now()
            
            return results
            
        except Exception as e:
            logger.error(f"聚合查询失败: {e}")
            self._stats["errors"] += 1
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self._stats.copy()
    
    def reset_stats(self):
        """重置统计信息"""
        for key in self._stats:
            if key == "last_operation_time":
                self._stats[key] = None
            else:
                self._stats[key] = 0
    
    async def close(self):
        """关闭连接"""
        try:
            if self._client:
                self._client.close()
            if self._sync_client:
                self._sync_client.close()
            
            logger.info("MongoDB连接已关闭")
            
        except Exception as e:
            logger.error(f"关闭MongoDB连接失败: {e}")


class LogManager:
    """日志管理器"""
    
    def __init__(self, mongo_manager: MongoDBManager):
        self.mongo = mongo_manager
        self._log_collection = "logs"
        self._audit_collection = "audit_logs"
        self._metrics_collection = "performance_metrics"
    
    async def write_log(self, log_entry: LogEntry) -> Optional[str]:
        """写入日志"""
        document = log_entry.to_dict()
        return await self.mongo.insert_document(self._log_collection, document)
    
    async def write_logs(self, log_entries: List[LogEntry]) -> List[str]:
        """批量写入日志"""
        documents = [entry.to_dict() for entry in log_entries]
        return await self.mongo.insert_documents(self._log_collection, documents)
    
    async def write_audit_log(self, user_id: str, action: str, resource: str, 
                            details: Optional[Dict[str, Any]] = None,
                            ip_address: Optional[str] = None,
                            user_agent: Optional[str] = None) -> Optional[str]:
        """写入审计日志"""
        document = {
            "timestamp": datetime.now(),
            "user_id": user_id,
            "action": action,
            "resource": resource,
            "details": details or {},
            "ip_address": ip_address,
            "user_agent": user_agent
        }
        
        return await self.mongo.insert_document(self._audit_collection, document)
    
    async def write_performance_metric(self, metric_type: str, source: str, 
                                     value: float, unit: str = "",
                                     tags: Optional[Dict[str, str]] = None) -> Optional[str]:
        """写入性能指标"""
        document = {
            "timestamp": datetime.now(),
            "metric_type": metric_type,
            "source": source,
            "value": value,
            "unit": unit,
            "tags": tags or {}
        }
        
        return await self.mongo.insert_document(self._metrics_collection, document)
    
    async def query_logs(self, level: Optional[LogLevel] = None,
                        category: Optional[LogCategory] = None,
                        start_time: Optional[datetime] = None,
                        end_time: Optional[datetime] = None,
                        user_id: Optional[str] = None,
                        source: Optional[str] = None,
                        tags: Optional[List[str]] = None,
                        limit: int = 100, skip: int = 0) -> List[Dict[str, Any]]:
        """查询日志"""
        filter_dict = {}
        
        if level:
            filter_dict["level"] = level
        if category:
            filter_dict["category"] = category
        if user_id:
            filter_dict["user_id"] = user_id
        if source:
            filter_dict["source"] = source
        if tags:
            filter_dict["tags"] = {"$in": tags}
        
        # 时间范围过滤
        if start_time or end_time:
            time_filter = {}
            if start_time:
                time_filter["$gte"] = start_time
            if end_time:
                time_filter["$lte"] = end_time
            filter_dict["timestamp"] = time_filter
        
        return await self.mongo.find_documents(
            self._log_collection, 
            filter_dict,
            sort=[("timestamp", -1)],
            limit=limit,
            skip=skip
        )
    
    async def get_log_statistics(self, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """获取日志统计信息"""
        pipeline = [
            {
                "$match": {
                    "timestamp": {"$gte": start_time, "$lte": end_time}
                }
            },
            {
                "$group": {
                    "_id": {
                        "level": "$level",
                        "category": "$category"
                    },
                    "count": {"$sum": 1}
                }
            }
        ]
        
        results = await self.mongo.aggregate(self._log_collection, pipeline)
        
        # 重新组织数据
        stats = {"total": 0, "by_level": {}, "by_category": {}}
        
        for result in results:
            level = result["_id"]["level"]
            category = result["_id"]["category"]
            count = result["count"]
            
            stats["total"] += count
            
            if level not in stats["by_level"]:
                stats["by_level"][level] = 0
            stats["by_level"][level] += count
            
            if category not in stats["by_category"]:
                stats["by_category"][category] = 0
            stats["by_category"][category] += count
        
        return stats
    
    async def cleanup_old_logs(self, days_to_keep: int = 30) -> int:
        """清理旧日志"""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        deleted_count = await self.mongo.delete_documents(
            self._log_collection,
            {"timestamp": {"$lt": cutoff_date}}
        )
        
        logger.info(f"清理了 {deleted_count} 条旧日志")
        return deleted_count


# 全局MongoDB管理器实例
_mongo_manager: Optional[MongoDBManager] = None
_log_manager: Optional[LogManager] = None


def get_mongo_manager() -> MongoDBManager:
    """获取全局MongoDB管理器"""
    global _mongo_manager
    if _mongo_manager is None:
        config = MongoDBConfig.from_env()
        _mongo_manager = MongoDBManager(config)
    return _mongo_manager


def get_log_manager() -> LogManager:
    """获取日志管理器"""
    global _log_manager
    if _log_manager is None:
        mongo_manager = get_mongo_manager()
        _log_manager = LogManager(mongo_manager)
    return _log_manager


def init_mongo_manager(manager: MongoDBManager):
    """初始化全局MongoDB管理器"""
    global _mongo_manager
    _mongo_manager = manager
