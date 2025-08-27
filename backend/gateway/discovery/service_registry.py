"""
服务注册与发现
=============

基于Redis的服务注册与发现机制
"""

import json
import time
import logging
import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import redis.asyncio as redis
from enum import Enum

from ..config.gateway_config import RegistryConfig

logger = logging.getLogger(__name__)


class ServiceStatus(Enum):
    """服务状态"""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    STARTING = "starting"
    STOPPING = "stopping"


@dataclass
class ServiceInfo:
    """服务信息"""
    name: str
    host: str
    port: int
    version: str = "1.0.0"
    status: ServiceStatus = ServiceStatus.HEALTHY
    metadata: Dict[str, Any] = None
    tags: List[str] = None
    health_check_url: str = "/health"
    
    # 服务指标
    last_heartbeat: float = 0
    register_time: float = 0
    weight: int = 1
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.tags is None:
            self.tags = []
        if self.register_time == 0:
            self.register_time = time.time()
        if self.last_heartbeat == 0:
            self.last_heartbeat = time.time()
    
    @property
    def service_id(self) -> str:
        """服务唯一ID"""
        return f"{self.name}:{self.host}:{self.port}"
    
    @property
    def url(self) -> str:
        """服务URL"""
        return f"http://{self.host}:{self.port}"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data['status'] = self.status.value
        data['last_heartbeat'] = self.last_heartbeat
        data['register_time'] = self.register_time
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ServiceInfo":
        """从字典创建"""
        data = data.copy()
        if 'status' in data:
            data['status'] = ServiceStatus(data['status'])
        return cls(**data)


class ServiceRegistry:
    """服务注册中心"""
    
    def __init__(self, config: RegistryConfig):
        self.config = config
        self.redis: Optional[redis.Redis] = None
        self.local_services: Dict[str, ServiceInfo] = {}
        
        # Redis键前缀
        self.service_prefix = "redfire:services"
        self.heartbeat_prefix = "redfire:heartbeat"
        
        # 健康检查任务
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._cleanup_task: Optional[asyncio.Task] = None
    
    async def initialize(self):
        """初始化注册中心"""
        logger.info("初始化服务注册中心...")
        
        # 连接Redis
        self.redis = redis.from_url(
            self.config.redis_url,
            decode_responses=True
        )
        
        # 测试连接
        try:
            await self.redis.ping()
            logger.info("Redis连接成功")
        except Exception as e:
            logger.error(f"Redis连接失败: {e}")
            raise
        
        # 启动后台任务
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        
        logger.info("服务注册中心初始化完成")
    
    async def register_service(self, service: ServiceInfo) -> bool:
        """注册服务"""
        try:
            service_key = f"{self.service_prefix}:{service.service_id}"
            heartbeat_key = f"{self.heartbeat_prefix}:{service.service_id}"
            
            # 更新心跳时间
            service.last_heartbeat = time.time()
            
            # 存储服务信息
            await self.redis.hset(service_key, mapping=service.to_dict())
            await self.redis.expire(service_key, self.config.service_ttl * 2)
            
            # 设置心跳
            await self.redis.set(heartbeat_key, time.time(), ex=self.config.service_ttl)
            
            # 缓存到本地
            self.local_services[service.service_id] = service
            
            logger.info(f"服务注册成功: {service.service_id}")
            return True
            
        except Exception as e:
            logger.error(f"服务注册失败 {service.service_id}: {e}")
            return False
    
    async def unregister_service(self, service_name: str, host: str = None, port: int = None) -> bool:
        """注销服务"""
        try:
            if host and port:
                service_id = f"{service_name}:{host}:{port}"
                await self._remove_service(service_id)
            else:
                # 注销所有同名服务
                services = await self.discover_services(service_name)
                for service in services:
                    await self._remove_service(service.service_id)
            
            logger.info(f"服务注销成功: {service_name}")
            return True
            
        except Exception as e:
            logger.error(f"服务注销失败 {service_name}: {e}")
            return False
    
    async def _remove_service(self, service_id: str):
        """移除服务"""
        service_key = f"{self.service_prefix}:{service_id}"
        heartbeat_key = f"{self.heartbeat_prefix}:{service_id}"
        
        await self.redis.delete(service_key)
        await self.redis.delete(heartbeat_key)
        
        if service_id in self.local_services:
            del self.local_services[service_id]
    
    async def discover_services(self, service_name: str) -> List[ServiceInfo]:
        """发现服务实例"""
        try:
            pattern = f"{self.service_prefix}:{service_name}:*"
            service_keys = await self.redis.keys(pattern)
            
            services = []
            for key in service_keys:
                service_data = await self.redis.hgetall(key)
                if service_data:
                    try:
                        service = ServiceInfo.from_dict(service_data)
                        
                        # 检查心跳
                        if await self._is_service_alive(service.service_id):
                            services.append(service)
                        else:
                            # 服务心跳超时，标记为不健康
                            service.status = ServiceStatus.UNHEALTHY
                            services.append(service)
                    except Exception as e:
                        logger.warning(f"解析服务信息失败 {key}: {e}")
            
            return services
            
        except Exception as e:
            logger.error(f"发现服务失败 {service_name}: {e}")
            return []
    
    async def get_healthy_services(self) -> Dict[str, List[ServiceInfo]]:
        """获取所有健康的服务"""
        try:
            pattern = f"{self.service_prefix}:*"
            service_keys = await self.redis.keys(pattern)
            
            services_by_name: Dict[str, List[ServiceInfo]] = {}
            
            for key in service_keys:
                service_data = await self.redis.hgetall(key)
                if service_data:
                    try:
                        service = ServiceInfo.from_dict(service_data)
                        
                        # 只返回健康的服务
                        if (service.status == ServiceStatus.HEALTHY and 
                            await self._is_service_alive(service.service_id)):
                            
                            if service.name not in services_by_name:
                                services_by_name[service.name] = []
                            services_by_name[service.name].append(service)
                            
                    except Exception as e:
                        logger.warning(f"解析服务信息失败 {key}: {e}")
            
            return services_by_name
            
        except Exception as e:
            logger.error(f"获取健康服务失败: {e}")
            return {}
    
    async def update_service_status(self, service_id: str, status: ServiceStatus):
        """更新服务状态"""
        try:
            service_key = f"{self.service_prefix}:{service_id}"
            await self.redis.hset(service_key, "status", status.value)
            
            if service_id in self.local_services:
                self.local_services[service_id].status = status
            
            logger.debug(f"更新服务状态: {service_id} -> {status.value}")
            
        except Exception as e:
            logger.error(f"更新服务状态失败 {service_id}: {e}")
    
    async def heartbeat(self, service_id: str) -> bool:
        """发送心跳"""
        try:
            heartbeat_key = f"{self.heartbeat_prefix}:{service_id}"
            service_key = f"{self.service_prefix}:{service_id}"
            
            # 更新心跳时间
            now = time.time()
            await self.redis.set(heartbeat_key, now, ex=self.config.service_ttl)
            await self.redis.hset(service_key, "last_heartbeat", now)
            
            # 更新本地缓存
            if service_id in self.local_services:
                self.local_services[service_id].last_heartbeat = now
            
            return True
            
        except Exception as e:
            logger.error(f"心跳发送失败 {service_id}: {e}")
            return False
    
    async def _is_service_alive(self, service_id: str) -> bool:
        """检查服务是否存活"""
        try:
            heartbeat_key = f"{self.heartbeat_prefix}:{service_id}"
            heartbeat_time = await self.redis.get(heartbeat_key)
            
            if not heartbeat_time:
                return False
            
            now = time.time()
            return (now - float(heartbeat_time)) < self.config.service_ttl
            
        except Exception:
            return False
    
    async def perform_health_checks(self):
        """执行健康检查"""
        for service_id, service in self.local_services.items():
            if not await self._is_service_alive(service_id):
                logger.warning(f"服务心跳超时: {service_id}")
                await self.update_service_status(service_id, ServiceStatus.UNHEALTHY)
    
    async def _heartbeat_loop(self):
        """心跳循环"""
        while True:
            try:
                for service_id in list(self.local_services.keys()):
                    await self.heartbeat(service_id)
                
                await asyncio.sleep(self.config.refresh_interval)
                
            except Exception as e:
                logger.error(f"心跳循环错误: {e}")
                await asyncio.sleep(5)
    
    async def _cleanup_loop(self):
        """清理循环"""
        while True:
            try:
                # 清理过期的服务
                pattern = f"{self.service_prefix}:*"
                service_keys = await self.redis.keys(pattern)
                
                for key in service_keys:
                    service_id = key.split(":", 2)[2]
                    if not await self._is_service_alive(service_id):
                        await self._remove_service(service_id)
                        logger.info(f"清理过期服务: {service_id}")
                
                await asyncio.sleep(60)  # 每分钟清理一次
                
            except Exception as e:
                logger.error(f"清理循环错误: {e}")
                await asyncio.sleep(10)
    
    async def get_registry_stats(self) -> Dict[str, Any]:
        """获取注册中心统计信息"""
        try:
            services_by_name = await self.get_healthy_services()
            
            stats = {
                "total_services": len(services_by_name),
                "total_instances": sum(len(instances) for instances in services_by_name.values()),
                "services": {}
            }
            
            for name, instances in services_by_name.items():
                stats["services"][name] = {
                    "instance_count": len(instances),
                    "instances": [
                        {
                            "id": instance.service_id,
                            "host": instance.host,
                            "port": instance.port,
                            "status": instance.status.value,
                            "version": instance.version
                        }
                        for instance in instances
                    ]
                }
            
            return stats
            
        except Exception as e:
            logger.error(f"获取注册中心统计失败: {e}")
            return {}
    
    async def close(self):
        """关闭注册中心"""
        logger.info("关闭服务注册中心...")
        
        # 停止后台任务
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
        if self._cleanup_task:
            self._cleanup_task.cancel()
        
        # 注销所有本地服务
        for service_id in list(self.local_services.keys()):
            await self._remove_service(service_id)
        
        # 关闭Redis连接
        if self.redis:
            await self.redis.close()
        
        logger.info("服务注册中心已关闭")
