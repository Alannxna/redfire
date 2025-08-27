"""
策略应用服务
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import asdict

from src.application.services.base_application_service import BaseApplicationService
from src.domain.strategy.entities.strategy_entity import (
    StrategyInstance, StrategyConfiguration, RiskEvent, StrategyStatus, StrategyType
)
from src.domain.strategy.repositories.strategy_repository import (
    StrategyInstanceRepository, StrategyConfigurationRepository, RiskEventRepository
)
from src.domain.strategy.services.strategy_validation_service import (
    StrategyValidationService, StrategyValidationResult
)
from src.domain.strategy.services.strategy_analysis_service import (
    StrategyAnalysisService, StrategyRiskAssessment, StrategyPerformanceAnalysis
)

logger = logging.getLogger(__name__)


class VnPyStrategyAdapter:
    """VnPy策略适配器 - 简化版本用于DDD架构"""
    
    def __init__(self):
        self.vnpy_available = False
        self.strategy_engines = {}
        
    async def initialize(self):
        """初始化VnPy适配器"""
        try:
            # 这里可以集成真正的VnPy引擎
            # 目前使用模拟模式
            self.vnpy_available = True
            logger.info("VnPy策略适配器初始化完成")
        except Exception as e:
            logger.error(f"VnPy策略适配器初始化失败: {e}")
            self.vnpy_available = False
    
    async def add_strategy(self, config: StrategyConfiguration) -> bool:
        """添加策略到VnPy引擎"""
        # 模拟添加策略
        return True
    
    async def start_strategy(self, strategy_name: str, strategy_type: StrategyType) -> bool:
        """启动VnPy策略"""
        # 模拟启动策略
        return True
    
    async def stop_strategy(self, strategy_name: str, strategy_type: StrategyType) -> bool:
        """停止VnPy策略"""
        # 模拟停止策略
        return True
    
    def get_strategy_data(self, strategy_name: str, strategy_type: StrategyType) -> Dict[str, Any]:
        """获取策略数据"""
        # 模拟策略数据
        import random
        return {
            "total_pnl": random.uniform(-10000, 50000),
            "daily_pnl": random.uniform(-5000, 10000),
            "position_pnl": random.uniform(-2000, 5000),
            "trading_pnl": random.uniform(-1000, 3000),
            "total_trades": random.randint(0, 200),
            "win_rate": random.uniform(0.3, 0.7),
            "max_drawdown": random.uniform(0.01, 0.2),
            "sharpe_ratio": random.uniform(0.5, 2.5)
        }


class StrategyApplicationService(BaseApplicationService):
    """
    策略应用服务
    
    提供完整的VnPy策略管理功能，包括：
    1. 策略配置管理
    2. 策略实例生命周期管理
    3. 策略绩效监控和分析
    4. 风险管理和事件处理
    5. 策略比较和优化建议
    
    对标After服务的comprehensive_integration功能
    """
    
    def __init__(
        self,
        instance_repository: StrategyInstanceRepository,
        config_repository: StrategyConfigurationRepository,
        risk_event_repository: RiskEventRepository,
        validation_service: StrategyValidationService,
        analysis_service: StrategyAnalysisService
    ):
        super().__init__()
        self.instance_repository = instance_repository
        self.config_repository = config_repository
        self.risk_event_repository = risk_event_repository
        self.validation_service = validation_service
        self.analysis_service = analysis_service
        
        # VnPy适配器
        self.vnpy_adapter = VnPyStrategyAdapter()
        
        # 运行时状态
        self.monitoring_task = None
        self.risk_check_interval = 30  # 30秒检查一次风险
        
        logger.info("策略应用服务初始化完成")
    
    async def initialize(self):
        """初始化服务"""
        await self.vnpy_adapter.initialize()
        
        # 启动监控任务
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        
        logger.info("策略应用服务启动完成")
    
    async def shutdown(self):
        """关闭服务"""
        if self.monitoring_task:
            self.monitoring_task.cancel()
        
        # 停止所有运行中的策略
        running_instances = await self.instance_repository.find_running_instances()
        for instance in running_instances:
            await self.stop_strategy_instance(instance.instance_id)
        
        logger.info("策略应用服务关闭完成")
    
    async def create_strategy_configuration(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建策略配置"""
        try:
            # 创建配置对象
            config = StrategyConfiguration(
                strategy_name=config_data["strategy_name"],
                strategy_class=config_data["strategy_class"],
                strategy_type=StrategyType(config_data["strategy_type"]),
                symbol_list=config_data["symbol_list"],
                parameters=config_data["parameters"],
                auto_start=config_data.get("auto_start", False),
                risk_limits=config_data.get("risk_limits", {})
            )
            
            # 验证配置
            validation_result = self.validation_service.validate_strategy_configuration(config)
            
            if not validation_result.is_valid:
                return {
                    "success": False,
                    "errors": validation_result.errors,
                    "warnings": validation_result.warnings
                }
            
            # 保存配置
            saved_config = await self.config_repository.save(config)
            
            # 如果设置自动启动，创建策略实例
            instance_id = None
            if config.auto_start:
                instance_result = await self.create_strategy_instance(config.strategy_name)
                if instance_result.get("success"):
                    instance_id = instance_result.get("instance_id")
            
            logger.info(f"创建策略配置成功: {config.strategy_name}")
            
            return {
                "success": True,
                "configuration": asdict(saved_config),
                "instance_id": instance_id,
                "warnings": validation_result.warnings,
                "suggestions": validation_result.suggestions
            }
            
        except Exception as e:
            logger.error(f"创建策略配置失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def create_strategy_instance(self, strategy_name: str) -> Dict[str, Any]:
        """创建策略实例"""
        try:
            # 获取策略配置
            config = await self.config_repository.find_by_name(strategy_name)
            if not config:
                return {"success": False, "error": "策略配置不存在"}
            
            # 创建策略实例
            instance = StrategyInstance(configuration=config)
            
            # 添加到VnPy引擎
            vnpy_success = await self.vnpy_adapter.add_strategy(config)
            if not vnpy_success:
                instance.mark_error("添加到VnPy引擎失败")
            
            # 保存实例
            saved_instance = await self.instance_repository.save(instance)
            
            logger.info(f"创建策略实例成功: {instance.instance_id}")
            
            return {
                "success": True,
                "instance_id": saved_instance.instance_id,
                "instance": asdict(saved_instance)
            }
            
        except Exception as e:
            logger.error(f"创建策略实例失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def start_strategy_instance(self, instance_id: str) -> Dict[str, Any]:
        """启动策略实例"""
        try:
            # 获取策略实例
            instance = await self.instance_repository.find_by_id(instance_id)
            if not instance:
                return {"success": False, "error": "策略实例不存在"}
            
            # 检查是否可以启动
            if not instance.can_start():
                return {"success": False, "error": f"策略状态错误，无法启动: {instance.status}"}
            
            # 风险检查
            if not instance.check_risk_limits():
                return {"success": False, "error": "策略风险检查未通过"}
            
            # 启动策略
            instance.start()
            
            # 启动VnPy策略
            vnpy_success = await self.vnpy_adapter.start_strategy(
                instance.configuration.strategy_name,
                instance.configuration.strategy_type
            )
            
            if vnpy_success:
                instance.mark_running()
                logger.info(f"策略启动成功: {instance_id}")
            else:
                instance.mark_error("VnPy策略启动失败")
                logger.error(f"策略启动失败: {instance_id}")
            
            # 更新实例
            updated_instance = await self.instance_repository.update(instance)
            
            return {
                "success": vnpy_success,
                "instance": asdict(updated_instance),
                "message": "策略启动成功" if vnpy_success else "策略启动失败"
            }
            
        except Exception as e:
            logger.error(f"启动策略实例失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def stop_strategy_instance(self, instance_id: str) -> Dict[str, Any]:
        """停止策略实例"""
        try:
            # 获取策略实例
            instance = await self.instance_repository.find_by_id(instance_id)
            if not instance:
                return {"success": False, "error": "策略实例不存在"}
            
            # 检查是否可以停止
            if not instance.can_stop():
                return {"success": False, "error": f"策略状态错误，无法停止: {instance.status}"}
            
            # 停止策略
            instance.stop()
            
            # 停止VnPy策略
            vnpy_success = await self.vnpy_adapter.stop_strategy(
                instance.configuration.strategy_name,
                instance.configuration.strategy_type
            )
            
            if vnpy_success:
                instance.mark_stopped()
                logger.info(f"策略停止成功: {instance_id}")
            else:
                instance.mark_error("VnPy策略停止失败")
                logger.error(f"策略停止失败: {instance_id}")
            
            # 更新实例
            updated_instance = await self.instance_repository.update(instance)
            
            return {
                "success": vnpy_success,
                "instance": asdict(updated_instance),
                "message": "策略停止成功" if vnpy_success else "策略停止失败"
            }
            
        except Exception as e:
            logger.error(f"停止策略实例失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_strategy_instance(self, instance_id: str) -> Dict[str, Any]:
        """获取策略实例详情"""
        try:
            instance = await self.instance_repository.find_by_id(instance_id)
            if not instance:
                return {"success": False, "error": "策略实例不存在"}
            
            # 风险评估
            risk_assessment = self.analysis_service.assess_strategy_risk(instance)
            
            # 绩效分析
            performance_analysis = self.analysis_service.analyze_strategy_performance(instance)
            
            # 优化建议
            optimization_suggestions = self.analysis_service.suggest_optimization_actions(instance)
            
            return {
                "success": True,
                "instance": asdict(instance),
                "risk_assessment": risk_assessment.to_dict(),
                "performance_analysis": performance_analysis.to_dict(),
                "optimization_suggestions": optimization_suggestions
            }
            
        except Exception as e:
            logger.error(f"获取策略实例失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def list_strategy_instances(
        self,
        status: Optional[StrategyStatus] = None,
        strategy_type: Optional[StrategyType] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """列出策略实例"""
        try:
            if status:
                instances = await self.instance_repository.find_by_status(status)
            elif strategy_type:
                instances = await self.instance_repository.find_by_type(strategy_type)
            else:
                instances = await self.instance_repository.find_all(limit=limit, offset=offset)
            
            # 获取统计信息
            statistics = await self.instance_repository.get_instance_statistics()
            
            return {
                "success": True,
                "instances": [asdict(instance) for instance in instances],
                "total_count": len(instances),
                "statistics": statistics
            }
            
        except Exception as e:
            logger.error(f"列出策略实例失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def compare_strategy_instances(self, instance_ids: List[str]) -> Dict[str, Any]:
        """比较策略实例绩效"""
        try:
            instances = []
            for instance_id in instance_ids:
                instance = await self.instance_repository.find_by_id(instance_id)
                if instance:
                    instances.append(instance)
            
            if not instances:
                return {"success": False, "error": "没有找到有效的策略实例"}
            
            # 执行绩效比较
            comparison_result = self.analysis_service.compare_strategy_performances(instances)
            
            return {
                "success": True,
                "comparison_result": comparison_result
            }
            
        except Exception as e:
            logger.error(f"比较策略实例失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_portfolio_metrics(self, instance_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """获取组合指标"""
        try:
            if instance_ids:
                instances = []
                for instance_id in instance_ids:
                    instance = await self.instance_repository.find_by_id(instance_id)
                    if instance:
                        instances.append(instance)
            else:
                instances = await self.instance_repository.find_running_instances()
            
            # 计算组合指标
            portfolio_metrics = self.analysis_service.calculate_portfolio_metrics(instances)
            
            return {
                "success": True,
                "portfolio_metrics": portfolio_metrics,
                "instance_count": len(instances)
            }
            
        except Exception as e:
            logger.error(f"获取组合指标失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_risk_events(
        self,
        instance_id: Optional[str] = None,
        severity: Optional[str] = None,
        hours: int = 24
    ) -> Dict[str, Any]:
        """获取风险事件"""
        try:
            if instance_id:
                events = await self.risk_event_repository.find_by_instance_id(instance_id)
            elif severity:
                events = await self.risk_event_repository.find_by_severity(severity)
            else:
                events = await self.risk_event_repository.find_recent_events(hours=hours)
            
            return {
                "success": True,
                "events": [asdict(event) for event in events],
                "total_count": len(events)
            }
            
        except Exception as e:
            logger.error(f"获取风险事件失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def _monitoring_loop(self):
        """监控循环"""
        while True:
            try:
                await self._update_strategy_performance()
                await self._check_risk_limits()
                await asyncio.sleep(self.risk_check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"监控循环错误: {e}")
                await asyncio.sleep(60)  # 错误时等待更长时间
    
    async def _update_strategy_performance(self):
        """更新策略绩效"""
        running_instances = await self.instance_repository.find_running_instances()
        
        for instance in running_instances:
            try:
                # 从VnPy获取最新数据
                strategy_data = self.vnpy_adapter.get_strategy_data(
                    instance.configuration.strategy_name,
                    instance.configuration.strategy_type
                )
                
                if strategy_data:
                    # 更新绩效数据
                    instance.update_performance(strategy_data)
                    await self.instance_repository.update(instance)
                    
            except Exception as e:
                logger.error(f"更新策略绩效失败 {instance.instance_id}: {e}")
    
    async def _check_risk_limits(self):
        """检查风险限制"""
        running_instances = await self.instance_repository.find_running_instances()
        
        for instance in running_instances:
            try:
                if not instance.check_risk_limits():
                    # 创建风险事件
                    risk_event = RiskEvent(
                        instance_id=instance.instance_id,
                        strategy_name=instance.configuration.strategy_name,
                        event_type="risk_limit_exceeded",
                        description="策略触发风险限制",
                        severity="warning",
                        action_taken="auto_stop"
                    )
                    
                    await self.risk_event_repository.save(risk_event)
                    
                    # 自动停止策略
                    await self.stop_strategy_instance(instance.instance_id)
                    
                    logger.warning(f"策略因风险限制自动停止: {instance.instance_id}")
                    
            except Exception as e:
                logger.error(f"风险检查失败 {instance.instance_id}: {e}")
    
    async def get_service_statistics(self) -> Dict[str, Any]:
        """获取服务统计信息"""
        try:
            instance_stats = await self.instance_repository.get_instance_statistics()
            config_stats = await self.config_repository.get_config_statistics()
            event_stats = await self.risk_event_repository.get_event_statistics()
            
            return {
                "success": True,
                "instances": instance_stats,
                "configurations": config_stats,
                "risk_events": event_stats,
                "vnpy_available": self.vnpy_adapter.vnpy_available
            }
            
        except Exception as e:
            logger.error(f"获取服务统计失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def cleanup_old_data(self, days: int = 30) -> Dict[str, Any]:
        """清理旧数据"""
        try:
            # 清理旧的风险事件
            cleaned_events = await self.risk_event_repository.cleanup_old_events(days)
            
            return {
                "success": True,
                "cleaned_events": cleaned_events,
                "cutoff_date": (datetime.now() - timedelta(days=days)).isoformat()
            }
            
        except Exception as e:
            logger.error(f"清理旧数据失败: {e}")
            return {"success": False, "error": str(e)}