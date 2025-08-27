"""
应用服务基类
============

应用层服务的基类，负责业务流程编排和跨领域服务协调
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
import asyncio

from .service_base import BaseService, ServiceConfig


@dataclass
class ApplicationServiceConfig(ServiceConfig):
    """应用服务配置"""
    workflow_enabled: bool = True
    saga_enabled: bool = False
    orchestration_mode: str = "choreography"  # choreography 或 orchestration
    transaction_timeout: int = 300  # 事务超时时间(秒)
    max_concurrent_workflows: int = 100
    workflow_persistence: bool = True
    compensation_enabled: bool = True


@dataclass
class WorkflowStep:
    """工作流步骤"""
    step_id: str
    step_name: str
    service_name: str
    method_name: str
    input_data: Dict[str, Any] = field(default_factory=dict)
    compensation_method: Optional[str] = None
    retry_count: int = 3
    timeout: int = 30
    depends_on: List[str] = field(default_factory=list)


@dataclass
class WorkflowDefinition:
    """工作流定义"""
    workflow_id: str
    workflow_name: str
    description: str
    steps: List[WorkflowStep]
    version: str = "1.0.0"
    enabled: bool = True


class BaseApplicationService(BaseService, ABC):
    """
    应用服务基类
    
    提供应用层功能：
    - 工作流编排
    - 跨服务协调
    - 事务管理
    - 补偿机制
    - Saga模式支持
    """
    
    def __init__(self, config: ApplicationServiceConfig):
        super().__init__(config)
        self.app_config = config
        
        # 工作流管理
        self.workflow_definitions: Dict[str, WorkflowDefinition] = {}
        self.running_workflows: Dict[str, Dict[str, Any]] = {}
        self.workflow_history: List[Dict[str, Any]] = []
        
        # 服务协调
        self.service_registry: Dict[str, Any] = {}
        self.service_dependencies: Dict[str, List[str]] = {}
        
        # 事务管理
        self.active_transactions: Dict[str, Dict[str, Any]] = {}
        self.compensation_handlers: Dict[str, Callable] = {}
        
        self.logger.info(f"应用服务初始化完成")
    
    async def register_workflow(self, workflow_def: WorkflowDefinition):
        """
        注册工作流定义
        
        Args:
            workflow_def: 工作流定义
        """
        self.workflow_definitions[workflow_def.workflow_id] = workflow_def
        self.logger.info(f"注册工作流: {workflow_def.workflow_name}")
    
    async def start_workflow(self, workflow_id: str, input_data: Dict[str, Any]) -> str:
        """
        启动工作流
        
        Args:
            workflow_id: 工作流ID
            input_data: 输入数据
            
        Returns:
            str: 工作流实例ID
        """
        if workflow_id not in self.workflow_definitions:
            raise ValueError(f"工作流未找到: {workflow_id}")
        
        workflow_def = self.workflow_definitions[workflow_id]
        instance_id = f"{workflow_id}-{self._generate_instance_id()}"
        
        workflow_instance = {
            "instance_id": instance_id,
            "workflow_id": workflow_id,
            "workflow_name": workflow_def.workflow_name,
            "status": "running",
            "input_data": input_data,
            "current_step": 0,
            "completed_steps": [],
            "failed_steps": [],
            "start_time": self._get_current_timestamp(),
            "end_time": None,
            "error": None
        }
        
        self.running_workflows[instance_id] = workflow_instance
        
        # 启动工作流执行
        asyncio.create_task(self._execute_workflow(instance_id))
        
        self.logger.info(f"启动工作流实例: {instance_id}")
        return instance_id
    
    async def cancel_workflow(self, instance_id: str) -> bool:
        """
        取消工作流
        
        Args:
            instance_id: 工作流实例ID
            
        Returns:
            bool: 是否成功取消
        """
        if instance_id not in self.running_workflows:
            return False
        
        workflow_instance = self.running_workflows[instance_id]
        workflow_instance["status"] = "cancelled"
        workflow_instance["end_time"] = self._get_current_timestamp()
        
        # 执行补偿操作
        await self._compensate_workflow(instance_id)
        
        # 移到历史记录
        self.workflow_history.append(workflow_instance)
        del self.running_workflows[instance_id]
        
        self.logger.info(f"取消工作流实例: {instance_id}")
        return True
    
    async def get_workflow_status(self, instance_id: str) -> Optional[Dict[str, Any]]:
        """
        获取工作流状态
        
        Args:
            instance_id: 工作流实例ID
            
        Returns:
            Optional[Dict[str, Any]]: 工作流状态
        """
        if instance_id in self.running_workflows:
            return self.running_workflows[instance_id]
        
        # 在历史记录中查找
        for workflow in self.workflow_history:
            if workflow["instance_id"] == instance_id:
                return workflow
        
        return None
    
    async def register_service(self, service_name: str, service_instance: Any, dependencies: List[str] = None):
        """
        注册服务
        
        Args:
            service_name: 服务名称
            service_instance: 服务实例
            dependencies: 依赖的服务列表
        """
        self.service_registry[service_name] = service_instance
        if dependencies:
            self.service_dependencies[service_name] = dependencies
        
        self.logger.info(f"注册服务: {service_name}")
    
    async def register_compensation_handler(self, operation: str, handler: Callable):
        """
        注册补偿处理器
        
        Args:
            operation: 操作名称
            handler: 补偿处理器
        """
        self.compensation_handlers[operation] = handler
        self.logger.debug(f"注册补偿处理器: {operation}")
    
    async def _execute_workflow(self, instance_id: str):
        """
        执行工作流
        
        Args:
            instance_id: 工作流实例ID
        """
        try:
            workflow_instance = self.running_workflows[instance_id]
            workflow_def = self.workflow_definitions[workflow_instance["workflow_id"]]
            
            for i, step in enumerate(workflow_def.steps):
                if workflow_instance["status"] != "running":
                    break
                
                # 检查依赖
                if not await self._check_step_dependencies(step, workflow_instance):
                    workflow_instance["status"] = "failed"
                    workflow_instance["error"] = f"步骤依赖未满足: {step.step_name}"
                    break
                
                # 执行步骤
                success = await self._execute_workflow_step(step, workflow_instance)
                
                if success:
                    workflow_instance["completed_steps"].append(step.step_id)
                    workflow_instance["current_step"] = i + 1
                else:
                    workflow_instance["failed_steps"].append(step.step_id)
                    workflow_instance["status"] = "failed"
                    workflow_instance["error"] = f"步骤执行失败: {step.step_name}"
                    
                    # 执行补偿
                    await self._compensate_workflow(instance_id)
                    break
            
            # 工作流完成
            if workflow_instance["status"] == "running":
                workflow_instance["status"] = "completed"
            
            workflow_instance["end_time"] = self._get_current_timestamp()
            
            # 移到历史记录
            self.workflow_history.append(workflow_instance)
            del self.running_workflows[instance_id]
            
        except Exception as e:
            self.logger.exception(f"工作流执行异常: {instance_id}, 错误: {e}")
            if instance_id in self.running_workflows:
                workflow_instance = self.running_workflows[instance_id]
                workflow_instance["status"] = "error"
                workflow_instance["error"] = str(e)
                workflow_instance["end_time"] = self._get_current_timestamp()
                
                self.workflow_history.append(workflow_instance)
                del self.running_workflows[instance_id]
    
    async def _execute_workflow_step(self, step: WorkflowStep, workflow_instance: Dict[str, Any]) -> bool:
        """
        执行工作流步骤
        
        Args:
            step: 工作流步骤
            workflow_instance: 工作流实例
            
        Returns:
            bool: 是否执行成功
        """
        try:
            service = self.service_registry.get(step.service_name)
            if not service:
                self.logger.error(f"服务未找到: {step.service_name}")
                return False
            
            method = getattr(service, step.method_name, None)
            if not method:
                self.logger.error(f"方法未找到: {step.service_name}.{step.method_name}")
                return False
            
            # 准备输入数据
            input_data = {**workflow_instance["input_data"], **step.input_data}
            
            # 执行方法
            if asyncio.iscoroutinefunction(method):
                result = await asyncio.wait_for(method(input_data), timeout=step.timeout)
            else:
                result = method(input_data)
            
            # 保存结果
            workflow_instance.setdefault("step_results", {})[step.step_id] = result
            
            self.logger.debug(f"工作流步骤执行成功: {step.step_name}")
            return True
            
        except asyncio.TimeoutError:
            self.logger.error(f"工作流步骤超时: {step.step_name}")
            return False
        except Exception as e:
            self.logger.exception(f"工作流步骤执行失败: {step.step_name}, 错误: {e}")
            return False
    
    async def _check_step_dependencies(self, step: WorkflowStep, workflow_instance: Dict[str, Any]) -> bool:
        """
        检查步骤依赖
        
        Args:
            step: 工作流步骤
            workflow_instance: 工作流实例
            
        Returns:
            bool: 依赖是否满足
        """
        if not step.depends_on:
            return True
        
        completed_steps = workflow_instance.get("completed_steps", [])
        
        for dependency in step.depends_on:
            if dependency not in completed_steps:
                return False
        
        return True
    
    async def _compensate_workflow(self, instance_id: str):
        """
        执行工作流补偿
        
        Args:
            instance_id: 工作流实例ID
        """
        if not self.app_config.compensation_enabled:
            return
        
        try:
            workflow_instance = self.running_workflows.get(instance_id)
            if not workflow_instance:
                return
            
            completed_steps = workflow_instance.get("completed_steps", [])
            workflow_def = self.workflow_definitions[workflow_instance["workflow_id"]]
            
            # 逆序执行补偿
            for step_id in reversed(completed_steps):
                step = next((s for s in workflow_def.steps if s.step_id == step_id), None)
                if step and step.compensation_method:
                    await self._execute_compensation(step, workflow_instance)
            
            self.logger.info(f"工作流补偿完成: {instance_id}")
            
        except Exception as e:
            self.logger.exception(f"工作流补偿失败: {instance_id}, 错误: {e}")
    
    async def _execute_compensation(self, step: WorkflowStep, workflow_instance: Dict[str, Any]):
        """
        执行补偿操作
        
        Args:
            step: 工作流步骤
            workflow_instance: 工作流实例
        """
        try:
            service = self.service_registry.get(step.service_name)
            if not service:
                return
            
            compensation_method = getattr(service, step.compensation_method, None)
            if not compensation_method:
                return
            
            # 获取步骤结果用于补偿
            step_result = workflow_instance.get("step_results", {}).get(step.step_id)
            
            if asyncio.iscoroutinefunction(compensation_method):
                await compensation_method(step_result)
            else:
                compensation_method(step_result)
            
            self.logger.debug(f"补偿操作执行成功: {step.step_name}")
            
        except Exception as e:
            self.logger.exception(f"补偿操作执行失败: {step.step_name}, 错误: {e}")
    
    def _generate_instance_id(self) -> str:
        """生成工作流实例ID"""
        import uuid
        return uuid.uuid4().hex[:8]
    
    def _get_current_timestamp(self) -> str:
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    async def get_application_metrics(self) -> Dict[str, Any]:
        """
        获取应用层监控指标
        
        Returns:
            Dict[str, Any]: 应用指标
        """
        return {
            "total_workflows": len(self.workflow_definitions),
            "running_workflows": len(self.running_workflows),
            "completed_workflows": len([w for w in self.workflow_history if w["status"] == "completed"]),
            "failed_workflows": len([w for w in self.workflow_history if w["status"] in ["failed", "error"]]),
            "registered_services": len(self.service_registry),
            "active_transactions": len(self.active_transactions),
            "compensation_handlers": len(self.compensation_handlers)
        }
    
    async def _health_check_impl(self) -> Dict[str, Any]:
        """应用服务健康检查实现"""
        app_metrics = await self.get_application_metrics()
        
        return {
            "application_healthy": True,
            "application_metrics": app_metrics,
            "workflow_enabled": self.app_config.workflow_enabled,
            "saga_enabled": self.app_config.saga_enabled,
            "orchestration_mode": self.app_config.orchestration_mode
        }
    
    # 子类需要实现的抽象方法
    @abstractmethod
    async def _initialize_workflows(self):
        """初始化工作流定义"""
        pass
    
    @abstractmethod
    async def _initialize_services(self):
        """初始化服务注册"""
        pass
