"""
研究领域服务
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from dataclasses import dataclass

from ..entities.research_project_entity import ResearchProject, ResearchPhase, ResearchMetrics
from ..entities.backtest_entity import Backtest, BacktestResult, BacktestConfiguration

logger = logging.getLogger(__name__)


@dataclass
class StrategyValidationResult:
    """策略验证结果"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    suggestions: List[str]


@dataclass
class RiskAssessment:
    """风险评估结果"""
    risk_score: float  # 0-100, 100为最高风险
    risk_level: str    # LOW, MEDIUM, HIGH, EXTREME
    risk_factors: List[str]
    recommendations: List[str]


class ResearchDomainService:
    """
    研究领域服务
    
    提供研究项目的业务逻辑和规则验证
    """
    
    def __init__(self):
        self.risk_thresholds = {
            "max_drawdown": 0.20,      # 20% 最大回撤
            "sharpe_ratio": 1.0,       # 夏普比率
            "volatility": 0.30,        # 30% 年化波动率
            "var_95": 0.05,            # 5% VaR
            "concentration": 0.30       # 30% 单一品种集中度
        }
    
    def validate_project_creation(
        self,
        name: str,
        symbols: List[str],
        start_date: datetime,
        end_date: datetime,
        initial_capital: float
    ) -> StrategyValidationResult:
        """
        验证研究项目创建参数
        
        Args:
            name: 项目名称
            symbols: 交易品种
            start_date: 开始日期
            end_date: 结束日期
            initial_capital: 初始资金
            
        Returns:
            StrategyValidationResult: 验证结果
        """
        errors = []
        warnings = []
        suggestions = []
        
        # 验证项目名称
        if not name or len(name.strip()) < 3:
            errors.append("项目名称至少需要3个字符")
        
        # 验证交易品种
        if not symbols:
            errors.append("至少需要选择一个交易品种")
        elif len(symbols) > 20:
            warnings.append("选择的品种过多，可能增加计算复杂度")
        
        # 验证时间范围
        if start_date >= end_date:
            errors.append("结束日期必须晚于开始日期")
        
        duration = (end_date - start_date).days
        if duration < 30:
            warnings.append("研究时间范围较短，可能影响统计显著性")
        elif duration > 3650:  # 10年
            warnings.append("研究时间范围过长，可能包含多个市场周期")
        
        # 验证初始资金
        if initial_capital <= 0:
            errors.append("初始资金必须大于0")
        elif initial_capital < 10000:
            warnings.append("初始资金较少，可能影响回测真实性")
        
        # 建议
        if duration < 252:  # 少于1年
            suggestions.append("建议至少包含一个完整年度的数据")
        
        if len(symbols) > 10:
            suggestions.append("考虑使用投资组合优化方法选择品种")
        
        return StrategyValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions
        )
    
    def validate_strategy_code(self, strategy_code: str) -> StrategyValidationResult:
        """
        验证策略代码
        
        Args:
            strategy_code: 策略代码
            
        Returns:
            StrategyValidationResult: 验证结果
        """
        errors = []
        warnings = []
        suggestions = []
        
        if not strategy_code or len(strategy_code.strip()) < 10:
            errors.append("策略代码不能为空且需要足够的内容")
            return StrategyValidationResult(False, errors, warnings, suggestions)
        
        # 检查必要的函数和方法
        required_keywords = ["def", "return"]
        for keyword in required_keywords:
            if keyword not in strategy_code:
                warnings.append(f"策略代码中缺少关键字: {keyword}")
        
        # 检查风险管理
        risk_keywords = ["stop_loss", "take_profit", "position_size", "risk"]
        risk_found = any(keyword in strategy_code.lower() for keyword in risk_keywords)
        if not risk_found:
            warnings.append("策略代码中未发现明显的风险管理逻辑")
        
        # 检查可能的问题
        if "import os" in strategy_code or "import sys" in strategy_code:
            errors.append("策略代码不应包含系统级导入")
        
        if "while True" in strategy_code:
            warnings.append("发现无限循环，可能导致性能问题")
        
        # 建议
        suggestions.append("建议在策略中添加详细的注释说明")
        suggestions.append("建议实施适当的风险管理措施")
        
        return StrategyValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions
        )
    
    def assess_project_risk(self, project: ResearchProject) -> RiskAssessment:
        """
        评估项目风险
        
        Args:
            project: 研究项目
            
        Returns:
            RiskAssessment: 风险评估结果
        """
        risk_score = 0.0
        risk_factors = []
        recommendations = []
        
        # 时间范围风险
        if project.start_date and project.end_date:
            duration_days = (project.end_date - project.start_date).days
            if duration_days < 90:
                risk_score += 20
                risk_factors.append("研究时间范围过短")
                recommendations.append("建议延长研究时间范围至少3个月")
        
        # 品种集中度风险
        if len(project.symbols) == 1:
            risk_score += 25
            risk_factors.append("单一品种集中度过高")
            recommendations.append("建议增加多个相关性较低的品种")
        elif len(project.symbols) > 15:
            risk_score += 15
            risk_factors.append("品种过于分散")
            recommendations.append("考虑使用投资组合优化选择核心品种")
        
        # 资金规模风险
        if project.initial_capital < 100000:
            risk_score += 10
            risk_factors.append("初始资金较少")
            recommendations.append("考虑增加初始资金以提高回测真实性")
        
        # 策略复杂度风险
        if project.strategy_code:
            code_lines = len(project.strategy_code.split('\n'))
            if code_lines > 500:
                risk_score += 15
                risk_factors.append("策略代码过于复杂")
                recommendations.append("建议简化策略逻辑，避免过度拟合")
        
        # 业绩指标风险
        if project.metrics.max_drawdown and project.metrics.max_drawdown > self.risk_thresholds["max_drawdown"]:
            risk_score += 30
            risk_factors.append(f"最大回撤过高: {project.metrics.max_drawdown:.2%}")
            recommendations.append("需要改进风险管理措施")
        
        if project.metrics.sharpe_ratio and project.metrics.sharpe_ratio < self.risk_thresholds["sharpe_ratio"]:
            risk_score += 20
            risk_factors.append(f"夏普比率过低: {project.metrics.sharpe_ratio:.2f}")
            recommendations.append("需要提高风险调整后收益")
        
        # 确定风险等级
        if risk_score <= 25:
            risk_level = "LOW"
        elif risk_score <= 50:
            risk_level = "MEDIUM"
        elif risk_score <= 75:
            risk_level = "HIGH"
        else:
            risk_level = "EXTREME"
        
        return RiskAssessment(
            risk_score=min(100.0, risk_score),
            risk_level=risk_level,
            risk_factors=risk_factors,
            recommendations=recommendations
        )
    
    def calculate_project_metrics(self, backtest_results: List[BacktestResult]) -> ResearchMetrics:
        """
        计算项目综合指标
        
        Args:
            backtest_results: 回测结果列表
            
        Returns:
            ResearchMetrics: 研究指标
        """
        if not backtest_results:
            return ResearchMetrics()
        
        # 计算平均指标
        total_return = np.mean([r.total_return for r in backtest_results])
        sharpe_ratio = np.mean([r.sharpe_ratio for r in backtest_results])
        max_drawdown = np.mean([r.max_drawdown for r in backtest_results])
        win_rate = np.mean([r.win_rate for r in backtest_results])
        profit_factor = np.mean([r.profit_factor for r in backtest_results])
        
        # 计算其他风险指标
        sortino_ratio = np.mean([r.sortino_ratio for r in backtest_results])
        calmar_ratio = np.mean([r.calmar_ratio for r in backtest_results])
        var_95 = np.mean([r.var_95 for r in backtest_results])
        cvar_95 = np.mean([r.cvar_95 for r in backtest_results])
        
        return ResearchMetrics(
            total_return=total_return,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            win_rate=win_rate,
            profit_factor=profit_factor,
            sortino_ratio=sortino_ratio,
            calmar_ratio=calmar_ratio,
            var_95=var_95,
            cvar_95=cvar_95
        )
    
    def suggest_next_phase(self, project: ResearchProject) -> Tuple[ResearchPhase, List[str]]:
        """
        建议下一个研究阶段
        
        Args:
            project: 研究项目
            
        Returns:
            Tuple[ResearchPhase, List[str]]: (建议阶段, 任务清单)
        """
        current_phase = project.phase
        tasks = []
        
        if current_phase == ResearchPhase.IDEA_GENERATION:
            next_phase = ResearchPhase.DATA_EXPLORATION
            tasks = [
                "收集和分析历史价格数据",
                "探索数据质量和完整性",
                "分析价格模式和相关性",
                "识别潜在的交易机会"
            ]
        
        elif current_phase == ResearchPhase.DATA_EXPLORATION:
            next_phase = ResearchPhase.STRATEGY_DEVELOPMENT
            tasks = [
                "设计交易信号生成逻辑",
                "定义入场和出场规则",
                "实现风险管理机制",
                "编写策略代码"
            ]
        
        elif current_phase == ResearchPhase.STRATEGY_DEVELOPMENT:
            next_phase = ResearchPhase.BACKTESTING
            tasks = [
                "配置回测参数",
                "执行历史数据回测",
                "分析回测结果",
                "识别策略优缺点"
            ]
        
        elif current_phase == ResearchPhase.BACKTESTING:
            next_phase = ResearchPhase.OPTIMIZATION
            tasks = [
                "识别可优化参数",
                "执行参数优化",
                "避免过度拟合",
                "验证优化结果"
            ]
        
        elif current_phase == ResearchPhase.OPTIMIZATION:
            next_phase = ResearchPhase.RISK_ANALYSIS
            tasks = [
                "计算风险指标",
                "压力测试",
                "情景分析",
                "制定风险控制措施"
            ]
        
        elif current_phase == ResearchPhase.RISK_ANALYSIS:
            next_phase = ResearchPhase.PRODUCTION_READY
            tasks = [
                "准备生产环境代码",
                "配置监控系统",
                "制定应急预案",
                "文档整理"
            ]
        
        else:  # PRODUCTION_READY
            next_phase = ResearchPhase.PRODUCTION_READY
            tasks = [
                "监控策略表现",
                "定期回顾和调整",
                "记录实盘交易",
                "持续改进"
            ]
        
        return next_phase, tasks
    
    def compare_strategies(
        self,
        strategy_results: List[BacktestResult]
    ) -> Dict[str, Any]:
        """
        比较多个策略的表现
        
        Args:
            strategy_results: 策略回测结果列表
            
        Returns:
            Dict[str, Any]: 比较分析结果
        """
        if not strategy_results:
            return {}
        
        metrics = ['total_return', 'sharpe_ratio', 'max_drawdown', 'win_rate', 'profit_factor']
        comparison = {}
        
        for metric in metrics:
            values = [getattr(result, metric) for result in strategy_results]
            comparison[metric] = {
                'best': max(values),
                'worst': min(values),
                'average': np.mean(values),
                'std': np.std(values),
                'ranking': sorted(enumerate(values), key=lambda x: x[1], reverse=True)
            }
        
        # 综合评分
        scores = []
        for result in strategy_results:
            score = (
                result.sharpe_ratio * 0.3 +
                (1 - result.max_drawdown) * 0.3 +
                result.win_rate * 0.2 +
                min(result.profit_factor, 3.0) / 3.0 * 0.2
            )
            scores.append(score)
        
        comparison['overall_score'] = {
            'scores': scores,
            'ranking': sorted(enumerate(scores), key=lambda x: x[1], reverse=True)
        }
        
        return comparison
