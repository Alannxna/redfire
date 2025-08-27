"""
基础服务抽象类
==============

所有服务的基础抽象类，定义统一的服务接口和生命周期管理
"""

import asyncio
import uuid
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

# 使用统一的枚举定义
from ..common.enums import ServiceStatus
# TODO: 导入路径需要根据实际情况调整
# from src.core.logging import get_logger

def get_logger(name: str):
    """临时日志函数，待统一日志系统实现后替换"""
    import logging
    return logging.getLogger(name)


@dataclass
class ServiceConfig:
    """服务配置基类"""
    service_name: str
    version: str = "1.0.0"
    description: str = ""
    dependencies: List[str] = field(default_factory=list)
    auto_start: bool = True
    health_check_interval: int = 30  # 健康检查间隔(秒)
    retry_count: int = 3
    retry_delay: int = 5
    timeout: int = 30
    config_data: Dict[str, Any] = field(default_factory=dict)


class BaseService(ABC):
    """
    基础服务抽象类
    
    定义所有服务的基本接口和行为：
    - 生命周期管理 (启动/停止/暂停/恢复)
    - 健康检查
    - 事件处理
    - 错误处理和恢复
    - 性能监控
    """
    
    def __init__(self, config: ServiceConfig):
        self.config = config
        self.service_id = f"{config.service_name}-{uuid.uuid4().hex[:8]}"
        self.status = ServiceStatus.STOPPED
        self.logger = get_logger(self.config.service_name)
        
        # 运行时信息
        self.start_time: Optional[datetime] = None
        self.last_health_check: Optional[datetime] = None
        self.error_count = 0
        self.restart_count = 0
        
        # 事件处理器
        self.event_handlers: Dict[str, List[Callable]] = {}
        self.health_check_callbacks: List[Callable] = []
        
        # 内部状态
        self._running = False
        self._health_check_task: Optional[asyncio.Task] = None
        
        self.logger.info(f"服务 {self.service_id} 初始化完成")
    
    @property
    def is_running(self) -> bool:
        """检查服务是否运行中"""
        return self.status == ServiceStatus.RUNNING
    
    @property
    def uptime(self) -> Optional[float]:
        """获取服务运行时间(秒)"""
        if self.start_time:
            return (datetime.now() - self.start_time).total_seconds()
        return None
    
    async def start(self) -> bool:
        """
        启动服务
        
        Returns:
            bool: 启动是否成功
        """
        if self.status == ServiceStatus.RUNNING:
            self.logger.warning(f"服务 {self.service_id} 已在运行中")
            return True
        
        try:
            self.status = ServiceStatus.STARTING
            self.logger.info(f"正在启动服务 {self.service_id}")
            
            # 调用具体实现的启动逻辑
            success = await self._start_impl()
            
            if success:
                self.status = ServiceStatus.RUNNING
                self.start_time = datetime.now()
                self._running = True
                
                # 启动健康检查
                await self._start_health_check()
                
                # 触发启动事件
                await self._emit_event("service_started", {"service_id": self.service_id})
                
                self.logger.info(f"服务 {self.service_id} 启动成功")
                return True
            else:
                self.status = ServiceStatus.ERROR
                self.error_count += 1
                self.logger.error(f"服务 {self.service_id} 启动失败")
                return False
                
        except Exception as e:
            self.status = ServiceStatus.ERROR
            self.error_count += 1
            self.logger.exception(f"服务 {self.service_id} 启动异常: {e}")
            return False
    
    async def stop(self) -> bool:
        """
        停止服务
        
        Returns:
            bool: 停止是否成功
        """
        if self.status == ServiceStatus.STOPPED:
            self.logger.warning(f"服务 {self.service_id} 已停止")
            return True
        
        try:
            self.status = ServiceStatus.STOPPING
            self.logger.info(f"正在停止服务 {self.service_id}")
            
            # 停止健康检查
            await self._stop_health_check()
            
            # 调用具体实现的停止逻辑
            success = await self._stop_impl()
            
            if success:
                self.status = ServiceStatus.STOPPED
                self._running = False
                self.start_time = None
                
                # 触发停止事件
                await self._emit_event("service_stopped", {"service_id": self.service_id})
                
                self.logger.info(f"服务 {self.service_id} 停止成功")
                return True
            else:
                self.status = ServiceStatus.ERROR
                self.error_count += 1
                self.logger.error(f"服务 {self.service_id} 停止失败")
                return False
                
        except Exception as e:
            self.status = ServiceStatus.ERROR
            self.error_count += 1
            self.logger.exception(f"服务 {self.service_id} 停止异常: {e}")
            return False
    
    async def restart(self) -> bool:
        """
        重启服务
        
        Returns:
            bool: 重启是否成功
        """
        self.logger.info(f"正在重启服务 {self.service_id}")
        self.restart_count += 1
        
        # 先停止
        stop_success = await self.stop()
        if not stop_success:
            return False
        
        # 等待一下再启动
        await asyncio.sleep(self.config.retry_delay)
        
        # 再启动
        return await self.start()
    
    async def pause(self) -> bool:
        """
        暂停服务
        
        Returns:
            bool: 暂停是否成功
        """
        if self.status != ServiceStatus.RUNNING:
            self.logger.warning(f"服务 {self.service_id} 不在运行状态，无法暂停")
            return False
        
        try:
            self.status = ServiceStatus.PAUSED
            success = await self._pause_impl()
            
            if success:
                await self._emit_event("service_paused", {"service_id": self.service_id})
                self.logger.info(f"服务 {self.service_id} 暂停成功")
            else:
                self.status = ServiceStatus.RUNNING  # 恢复到运行状态
                self.logger.error(f"服务 {self.service_id} 暂停失败")
            
            return success
            
        except Exception as e:
            self.status = ServiceStatus.RUNNING  # 恢复到运行状态
            self.logger.exception(f"服务 {self.service_id} 暂停异常: {e}")
            return False
    
    async def resume(self) -> bool:
        """
        恢复服务
        
        Returns:
            bool: 恢复是否成功
        """
        if self.status != ServiceStatus.PAUSED:
            self.logger.warning(f"服务 {self.service_id} 不在暂停状态，无法恢复")
            return False
        
        try:
            success = await self._resume_impl()
            
            if success:
                self.status = ServiceStatus.RUNNING
                await self._emit_event("service_resumed", {"service_id": self.service_id})
                self.logger.info(f"服务 {self.service_id} 恢复成功")
            else:
                self.logger.error(f"服务 {self.service_id} 恢复失败")
            
            return success
            
        except Exception as e:
            self.logger.exception(f"服务 {self.service_id} 恢复异常: {e}")
            return False
    
    async def health_check(self) -> Dict[str, Any]:
        """
        健康检查
        
        Returns:
            Dict[str, Any]: 健康状态信息
        """
        try:
            # 基础健康信息
            health_info = {
                "service_id": self.service_id,
                "service_name": self.config.service_name,
                "status": self.status.value,
                "uptime": self.uptime,
                "error_count": self.error_count,
                "restart_count": self.restart_count,
                "last_check": datetime.now().isoformat(),
                "healthy": True
            }
            
            # 调用具体实现的健康检查
            impl_health = await self._health_check_impl()
            health_info.update(impl_health)
            
            # 运行健康检查回调
            for callback in self.health_check_callbacks:
                try:
                    await callback(health_info)
                except Exception as e:
                    self.logger.warning(f"健康检查回调执行失败: {e}")
            
            self.last_health_check = datetime.now()
            return health_info
            
        except Exception as e:
            self.logger.exception(f"健康检查失败: {e}")
            return {
                "service_id": self.service_id,
                "status": ServiceStatus.ERROR.value,
                "healthy": False,
                "error": str(e),
                "last_check": datetime.now().isoformat()
            }
    
    def add_event_handler(self, event_type: str, handler: Callable):
        """添加事件处理器"""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)
    
    def add_health_check_callback(self, callback: Callable):
        """添加健康检查回调"""
        self.health_check_callbacks.append(callback)
    
    async def _emit_event(self, event_type: str, data: Dict[str, Any]):
        """触发事件"""
        if event_type in self.event_handlers:
            for handler in self.event_handlers[event_type]:
                try:
                    await handler(data)
                except Exception as e:
                    self.logger.warning(f"事件处理器执行失败: {e}")
    
    async def _start_health_check(self):
        """启动健康检查任务"""
        if self.config.health_check_interval > 0:
            self._health_check_task = asyncio.create_task(self._health_check_loop())
    
    async def _stop_health_check(self):
        """停止健康检查任务"""
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
            self._health_check_task = None
    
    async def _health_check_loop(self):
        """健康检查循环"""
        while self._running:
            try:
                await self.health_check()
                await asyncio.sleep(self.config.health_check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.warning(f"健康检查循环异常: {e}")
                await asyncio.sleep(self.config.health_check_interval)
    
    # 子类需要实现的抽象方法
    @abstractmethod
    async def _start_impl(self) -> bool:
        """具体服务的启动实现"""
        pass
    
    @abstractmethod
    async def _stop_impl(self) -> bool:
        """具体服务的停止实现"""
        pass
    
    async def _pause_impl(self) -> bool:
        """具体服务的暂停实现（可选重写）"""
        return True
    
    async def _resume_impl(self) -> bool:
        """具体服务的恢复实现（可选重写）"""
        return True
    
    async def _health_check_impl(self) -> Dict[str, Any]:
        """具体服务的健康检查实现（可选重写）"""
        return {}
    
    def get_status_info(self) -> Dict[str, Any]:
        """获取服务状态信息"""
        return {
            "service_id": self.service_id,
            "service_name": self.config.service_name,
            "version": self.config.version,
            "description": self.config.description,
            "status": self.status.value,
            "uptime": self.uptime,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "last_health_check": self.last_health_check.isoformat() if self.last_health_check else None,
            "error_count": self.error_count,
            "restart_count": self.restart_count,
            "config": {
                "auto_start": self.config.auto_start,
                "health_check_interval": self.config.health_check_interval,
                "retry_count": self.config.retry_count,
                "dependencies": self.config.dependencies
            }
        }
