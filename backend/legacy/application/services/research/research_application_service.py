"""
研究应用服务
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import asdict
import json

from src.application.services.base_application_service import BaseApplicationService
from src.domain.research.entities.research_project_entity import ResearchProject, ResearchPhase, ProjectStatus
from src.domain.research.entities.backtest_entity import Backtest, BacktestResult, BacktestConfiguration, BacktestStatus, BacktestType
from src.domain.research.repositories.research_project_repository import ResearchProjectRepository
from src.domain.research.repositories.backtest_repository import BacktestRepository
from src.domain.research.services.research_domain_service import ResearchDomainService

logger = logging.getLogger(__name__)


class ResearchApplicationService(BaseApplicationService):
    """
    研究应用服务
    
    提供完整的量化研究功能，包括：
    1. 研究项目管理
    2. 策略开发和测试
    3. 回测执行和分析
    4. 风险评估和优化
    5. 结果报告和可视化
    
    对标After服务的enhanced_research_service功能
    """
    
    def __init__(
        self,
        project_repository: ResearchProjectRepository,
        backtest_repository: BacktestRepository,
        research_domain_service: ResearchDomainService
    ):
        super().__init__()
        self.project_repository = project_repository
        self.backtest_repository = backtest_repository
        self.research_domain_service = research_domain_service
        
        # 运行时状态管理
        self.running_backtests: Dict[str, asyncio.Task] = {}
        self.backtest_progress: Dict[str, float] = {}
        
        # 配置
        self.max_concurrent_backtests = 5
        self.default_backtest_timeout = 3600  # 1小时
        
        logger.info("研究应用服务初始化完成")
    
    async def create_project(
        self,
        name: str,
        description: str,
        symbols: List[str],
        start_date: datetime,
        end_date: datetime,
        initial_capital: float = 1000000.0,
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """创建新的研究项目"""
        try:
            # 验证输入参数
            validation_result = self.research_domain_service.validate_project_creation(
                name, symbols, start_date, end_date, initial_capital
            )
            
            if not validation_result.is_valid:
                return {
                    "success": False,
                    "errors": validation_result.errors,
                    "warnings": validation_result.warnings
                }
            
            # 创建项目
            project = ResearchProject(
                name=name,
                description=description,
                symbols=symbols,
                start_date=start_date,
                end_date=end_date,
                initial_capital=initial_capital,
                tags=tags or []
            )
            
            saved_project = await self.project_repository.save(project)
            
            logger.info(f"创建研究项目成功: {name}")
            
            return {
                "success": True,
                "project": asdict(saved_project),
                "warnings": validation_result.warnings,
                "suggestions": validation_result.suggestions
            }
            
        except Exception as e:
            logger.error(f"创建研究项目失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_project(self, project_id: str) -> Dict[str, Any]:
        """获取研究项目详情"""
        try:
            project = await self.project_repository.find_by_id(project_id)
            if not project:
                return {"success": False, "error": "项目不存在"}
            
            # 获取相关回测
            backtests = await self.backtest_repository.find_by_project_id(project_id)
            
            # 风险评估
            risk_assessment = self.research_domain_service.assess_project_risk(project)
            
            # 阶段建议
            next_phase, tasks = self.research_domain_service.suggest_next_phase(project)
            
            return {
                "success": True,
                "project": asdict(project),
                "backtests": [asdict(bt) for bt in backtests],
                "risk_assessment": asdict(risk_assessment),
                "next_phase": next_phase.value,
                "suggested_tasks": tasks
            }
            
        except Exception as e:
            logger.error(f"获取研究项目失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def update_project_strategy(
        self,
        project_id: str,
        strategy_code: str,
        strategy_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """更新项目策略代码"""
        try:
            project = await self.project_repository.find_by_id(project_id)
            if not project:
                return {"success": False, "error": "项目不存在"}
            
            # 验证策略代码
            validation_result = self.research_domain_service.validate_strategy_code(strategy_code)
            
            if validation_result.is_valid:
                project.update_strategy(strategy_code, strategy_config or {})
                
                # 如果处于想法生成阶段，推进到策略开发阶段
                if project.phase == ResearchPhase.IDEA_GENERATION:
                    project.phase = ResearchPhase.STRATEGY_DEVELOPMENT
                
                updated_project = await self.project_repository.update(project)
                
                return {
                    "success": True,
                    "project": asdict(updated_project),
                    "warnings": validation_result.warnings,
                    "suggestions": validation_result.suggestions
                }
            else:
                return {
                    "success": False,
                    "errors": validation_result.errors,
                    "warnings": validation_result.warnings
                }
                
        except Exception as e:
            logger.error(f"更新策略代码失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def start_backtest(
        self,
        project_id: str,
        backtest_name: str,
        backtest_type: BacktestType = BacktestType.SINGLE_STRATEGY,
        custom_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """启动回测"""
        try:
            project = await self.project_repository.find_by_id(project_id)
            if not project:
                return {"success": False, "error": "项目不存在"}
            
            if not project.has_strategy:
                return {"success": False, "error": "项目未包含策略代码"}
            
            # 检查并发限制
            if len(self.running_backtests) >= self.max_concurrent_backtests:
                return {"success": False, "error": "已达到最大并发回测数量限制"}
            
            # 创建回测配置
            config = BacktestConfiguration(
                start_date=project.start_date,
                end_date=project.end_date,
                initial_capital=project.initial_capital,
                symbols=project.symbols,
                **(custom_config or {})
            )
            
            # 创建回测实例
            backtest = Backtest(
                project_id=project_id,
                name=backtest_name,
                backtest_type=backtest_type,
                configuration=config,
                strategy_code=project.strategy_code,
                strategy_config=project.strategy_config
            )
            
            saved_backtest = await self.backtest_repository.save(backtest)
            
            # 启动异步回测任务
            task = asyncio.create_task(self._execute_backtest(saved_backtest))
            self.running_backtests[saved_backtest.backtest_id] = task
            
            logger.info(f"启动回测: {backtest_name} (项目: {project.name})")
            
            return {
                "success": True,
                "backtest": asdict(saved_backtest),
                "message": "回测已启动"
            }
            
        except Exception as e:
            logger.error(f"启动回测失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_backtest_progress(self, backtest_id: str) -> Dict[str, Any]:
        """获取回测进度"""
        try:
            backtest = await self.backtest_repository.find_by_id(backtest_id)
            if not backtest:
                return {"success": False, "error": "回测不存在"}
            
            progress = self.backtest_progress.get(backtest_id, 0.0)
            is_running = backtest_id in self.running_backtests
            
            return {
                "success": True,
                "backtest_id": backtest_id,
                "status": backtest.status.value,
                "progress": progress,
                "is_running": is_running,
                "error_message": backtest.error_message
            }
            
        except Exception as e:
            logger.error(f"获取回测进度失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def cancel_backtest(self, backtest_id: str) -> Dict[str, Any]:
        """取消回测"""
        try:
            if backtest_id in self.running_backtests:
                task = self.running_backtests[backtest_id]
                task.cancel()
                del self.running_backtests[backtest_id]
                
                # 更新回测状态
                backtest = await self.backtest_repository.find_by_id(backtest_id)
                if backtest:
                    backtest.cancel()
                    await self.backtest_repository.update(backtest)
                
                return {"success": True, "message": "回测已取消"}
            else:
                return {"success": False, "error": "回测未在运行中"}
                
        except Exception as e:
            logger.error(f"取消回测失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_backtest_results(self, backtest_id: str) -> Dict[str, Any]:
        """获取回测结果"""
        try:
            backtest = await self.backtest_repository.find_by_id(backtest_id)
            if not backtest:
                return {"success": False, "error": "回测不存在"}
            
            if not backtest.is_completed:
                return {"success": False, "error": "回测尚未完成"}
            
            return {
                "success": True,
                "backtest": asdict(backtest),
                "result": backtest.result.to_dict() if backtest.result else None
            }
            
        except Exception as e:
            logger.error(f"获取回测结果失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def list_projects(
        self,
        status: Optional[ProjectStatus] = None,
        phase: Optional[ResearchPhase] = None,
        tags: Optional[List[str]] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """列出研究项目"""
        try:
            if status:
                projects = await self.project_repository.find_by_status(status)
            elif phase:
                projects = await self.project_repository.find_by_phase(phase)
            elif tags:
                projects = await self.project_repository.find_by_tags(tags)
            else:
                projects = await self.project_repository.find_all(limit=limit, offset=offset)
            
            # 获取项目统计
            stats = await self.project_repository.get_project_statistics()
            
            return {
                "success": True,
                "projects": [asdict(project) for project in projects],
                "total_count": len(projects),
                "statistics": stats
            }
            
        except Exception as e:
            logger.error(f"列出研究项目失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def advance_project_phase(self, project_id: str) -> Dict[str, Any]:
        """推进项目到下一阶段"""
        try:
            project = await self.project_repository.find_by_id(project_id)
            if not project:
                return {"success": False, "error": "项目不存在"}
            
            old_phase = project.phase
            project.advance_phase()
            
            updated_project = await self.project_repository.update(project)
            
            # 获取新阶段的任务建议
            _, tasks = self.research_domain_service.suggest_next_phase(updated_project)
            
            return {
                "success": True,
                "project": asdict(updated_project),
                "old_phase": old_phase.value,
                "new_phase": updated_project.phase.value,
                "suggested_tasks": tasks
            }
            
        except Exception as e:
            logger.error(f"推进项目阶段失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def compare_project_strategies(self, project_ids: List[str]) -> Dict[str, Any]:
        """比较多个项目的策略表现"""
        try:
            comparison_data = []
            
            for project_id in project_ids:
                project = await self.project_repository.find_by_id(project_id)
                if not project:
                    continue
                
                backtests = await self.backtest_repository.find_completed_backtests(project_id=project_id)
                completed_backtests = [bt for bt in backtests if bt.result]
                
                if completed_backtests:
                    # 取最佳回测结果
                    best_backtest = max(completed_backtests, key=lambda bt: bt.result.sharpe_ratio)
                    comparison_data.append({
                        "project": asdict(project),
                        "best_result": best_backtest.result.to_dict()
                    })
            
            if not comparison_data:
                return {"success": False, "error": "没有可比较的项目结果"}
            
            # 执行策略比较
            results = [data["best_result"] for data in comparison_data]
            backtest_results = []
            for result_dict in results:
                # 这里需要将字典转换回BacktestResult对象
                # 为简化，直接使用字典进行比较
                pass
            
            return {
                "success": True,
                "comparison_data": comparison_data,
                "projects_count": len(comparison_data)
            }
            
        except Exception as e:
            logger.error(f"比较项目策略失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def _execute_backtest(self, backtest: Backtest) -> None:
        """
        执行回测的内部方法
        
        Args:
            backtest: 回测实例
        """
        try:
            # 更新状态为运行中
            backtest.start()
            await self.backtest_repository.update(backtest)
            
            logger.info(f"开始执行回测: {backtest.name}")
            
            # 模拟回测执行过程
            # 实际实现中这里会调用真正的回测引擎
            for i in range(101):
                if backtest.backtest_id not in self.running_backtests:
                    # 回测被取消
                    return
                
                # 更新进度
                progress = i
                backtest.update_progress(progress)
                self.backtest_progress[backtest.backtest_id] = progress
                
                # 模拟计算延迟
                await asyncio.sleep(0.1)
            
            # 模拟生成回测结果
            result = BacktestResult(
                total_return=0.15,  # 15% 总收益
                annual_return=0.12,  # 12% 年化收益
                sharpe_ratio=1.2,
                max_drawdown=0.08,
                win_rate=0.55,
                profit_factor=1.8,
                total_trades=150,
                winning_trades=83,
                losing_trades=67
            )
            
            # 完成回测
            backtest.complete(result)
            await self.backtest_repository.update(backtest)
            
            # 更新项目指标
            project = await self.project_repository.find_by_id(backtest.project_id)
            if project:
                # 获取项目所有回测结果并计算综合指标
                all_backtests = await self.backtest_repository.find_completed_backtests(project_id=project.project_id)
                backtest_results = [bt.result for bt in all_backtests if bt.result]
                
                if backtest_results:
                    metrics = self.research_domain_service.calculate_project_metrics(backtest_results)
                    project.update_metrics(metrics)
                    await self.project_repository.update(project)
            
            logger.info(f"回测执行完成: {backtest.name}")
            
        except asyncio.CancelledError:
            logger.info(f"回测被取消: {backtest.name}")
            backtest.cancel()
            await self.backtest_repository.update(backtest)
            
        except Exception as e:
            logger.error(f"回测执行失败: {backtest.name}, 错误: {e}")
            backtest.fail(str(e))
            await self.backtest_repository.update(backtest)
            
        finally:
            # 清理运行状态
            if backtest.backtest_id in self.running_backtests:
                del self.running_backtests[backtest.backtest_id]
            if backtest.backtest_id in self.backtest_progress:
                del self.backtest_progress[backtest.backtest_id]
    
    async def cleanup_old_data(self, days: int = 90) -> Dict[str, Any]:
        """清理旧数据"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # 清理旧的回测记录
            cleaned_backtests = await self.backtest_repository.cleanup_old_backtests(cutoff_date)
            
            return {
                "success": True,
                "cleaned_backtests": cleaned_backtests,
                "cutoff_date": cutoff_date.isoformat()
            }
            
        except Exception as e:
            logger.error(f"清理旧数据失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_service_statistics(self) -> Dict[str, Any]:
        """获取服务统计信息"""
        try:
            project_stats = await self.project_repository.get_project_statistics()
            backtest_stats = await self.backtest_repository.get_backtest_statistics()
            
            return {
                "success": True,
                "projects": project_stats,
                "backtests": backtest_stats,
                "running_backtests": len(self.running_backtests),
                "max_concurrent_backtests": self.max_concurrent_backtests
            }
            
        except Exception as e:
            logger.error(f"获取服务统计失败: {e}")
            return {"success": False, "error": str(e)}
