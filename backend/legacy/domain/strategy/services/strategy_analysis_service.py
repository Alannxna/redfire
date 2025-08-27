"""
策略分析服务
"""

import logging
from typing import Dict, Any, List

from src.domain.strategy.entities.strategy_entity import StrategyInstance

logger = logging.getLogger(__name__)


class StrategyRiskAssessment:
    """策略风险评估"""
    
    def __init__(self):
        self.risk_level: str = "low"  # low, medium, high, critical
        self.risk_score: float = 0.0  # 0-100
        self.risk_factors: List[str] = []
        self.recommendations: List[str] = []
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "risk_level": self.risk_level,
            "risk_score": self.risk_score,
            "risk_factors": self.risk_factors,
            "recommendations": self.recommendations
        }


class StrategyPerformanceAnalysis:
    """策略绩效分析"""
    
    def __init__(self):
        self.overall_score: float = 0.0  # 0-100
        self.performance_grade: str = "C"  # A, B, C, D, F
        self.strengths: List[str] = []
        self.weaknesses: List[str] = []
        self.improvement_suggestions: List[str] = []
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "overall_score": self.overall_score,
            "performance_grade": self.performance_grade,
            "strengths": self.strengths,
            "weaknesses": self.weaknesses,
            "improvement_suggestions": self.improvement_suggestions
        }


class StrategyAnalysisService:
    """策略分析服务"""
    
    def assess_strategy_risk(self, instance: StrategyInstance) -> StrategyRiskAssessment:
        """评估策略风险"""
        assessment = StrategyRiskAssessment()
        
        risk_score = 0.0
        risk_factors = []
        
        # 基于绩效的风险评估
        performance = instance.performance
        
        # 最大回撤风险
        if performance.max_drawdown > 0.2:  # 20%
            risk_score += 30
            risk_factors.append("最大回撤过大")
        elif performance.max_drawdown > 0.1:  # 10%
            risk_score += 15
            risk_factors.append("最大回撤较大")
        
        # 夏普比率风险
        if performance.sharpe_ratio < 0.5:
            risk_score += 20
            risk_factors.append("夏普比率过低")
        elif performance.sharpe_ratio < 1.0:
            risk_score += 10
            risk_factors.append("夏普比率较低")
        
        # 胜率风险
        if performance.win_rate < 0.3:
            risk_score += 15
            risk_factors.append("胜率过低")
        elif performance.win_rate < 0.4:
            risk_score += 8
            risk_factors.append("胜率较低")
        
        # 交易频率风险
        if instance.get_runtime_duration():
            runtime_hours = instance.get_runtime_duration() / 3600
            trades_per_hour = performance.total_trades / max(runtime_hours, 1)
            
            if trades_per_hour > 100:  # 过度交易
                risk_score += 25
                risk_factors.append("交易频率过高")
            elif trades_per_hour > 50:
                risk_score += 10
                risk_factors.append("交易频率较高")
        
        # 基于配置的风险评估
        if instance.configuration:
            config = instance.configuration
            
            # 品种集中度风险
            if len(config.symbol_list) == 1:
                risk_score += 10
                risk_factors.append("品种过于集中")
            elif len(config.symbol_list) > 10:
                risk_score += 15
                risk_factors.append("品种过于分散")
            
            # 风险限制检查
            limits = config.risk_limits
            if limits.max_daily_loss > limits.max_total_loss * 0.5:
                risk_score += 10
                risk_factors.append("日亏损限制相对宽松")
        
        # 设置风险等级
        assessment.risk_score = min(risk_score, 100.0)
        assessment.risk_factors = risk_factors
        
        if risk_score >= 80:
            assessment.risk_level = "critical"
            assessment.recommendations.extend([
                "立即停止策略运行",
                "重新评估策略逻辑",
                "降低仓位规模"
            ])
        elif risk_score >= 60:
            assessment.risk_level = "high"
            assessment.recommendations.extend([
                "密切监控策略表现",
                "考虑降低风险限制",
                "增加止损设置"
            ])
        elif risk_score >= 30:
            assessment.risk_level = "medium"
            assessment.recommendations.extend([
                "定期检查策略绩效",
                "优化参数设置"
            ])
        else:
            assessment.risk_level = "low"
            assessment.recommendations.append("维持当前设置")
        
        return assessment
    
    def analyze_strategy_performance(self, instance: StrategyInstance) -> StrategyPerformanceAnalysis:
        """分析策略绩效"""
        analysis = StrategyPerformanceAnalysis()
        
        if not instance.performance:
            return analysis
        
        performance = instance.performance
        score = 0.0
        strengths = []
        weaknesses = []
        suggestions = []
        
        # 收益率评分 (30分)
        if performance.total_pnl > 0:
            if performance.total_pnl > 100000:  # 10万以上
                score += 30
                strengths.append("收益表现优秀")
            elif performance.total_pnl > 50000:  # 5万以上
                score += 20
                strengths.append("收益表现良好")
            elif performance.total_pnl > 10000:  # 1万以上
                score += 15
                strengths.append("收益表现一般")
            else:
                score += 10
        else:
            weaknesses.append("策略处于亏损状态")
            suggestions.append("检查策略逻辑和市场适应性")
        
        # 夏普比率评分 (25分)
        if performance.sharpe_ratio >= 2.0:
            score += 25
            strengths.append("风险调整收益优秀")
        elif performance.sharpe_ratio >= 1.5:
            score += 20
            strengths.append("风险调整收益良好")
        elif performance.sharpe_ratio >= 1.0:
            score += 15
            strengths.append("风险调整收益一般")
        elif performance.sharpe_ratio >= 0.5:
            score += 10
        else:
            weaknesses.append("风险调整收益不佳")
            suggestions.append("优化风险控制措施")
        
        # 最大回撤评分 (20分)
        if performance.max_drawdown <= 0.05:  # 5%以内
            score += 20
            strengths.append("回撤控制优秀")
        elif performance.max_drawdown <= 0.1:  # 10%以内
            score += 15
            strengths.append("回撤控制良好")
        elif performance.max_drawdown <= 0.15:  # 15%以内
            score += 10
            strengths.append("回撤控制一般")
        elif performance.max_drawdown <= 0.2:  # 20%以内
            score += 5
        else:
            weaknesses.append("回撤过大")
            suggestions.append("加强止损和仓位管理")
        
        # 胜率评分 (15分)
        if performance.win_rate >= 0.6:  # 60%以上
            score += 15
            strengths.append("胜率表现优秀")
        elif performance.win_rate >= 0.5:  # 50%以上
            score += 12
            strengths.append("胜率表现良好")
        elif performance.win_rate >= 0.4:  # 40%以上
            score += 8
            strengths.append("胜率表现一般")
        elif performance.win_rate >= 0.3:  # 30%以上
            score += 5
        else:
            weaknesses.append("胜率偏低")
            suggestions.append("优化入场和出场时机")
        
        # 交易活跃度评分 (10分)
        if performance.total_trades >= 100:
            score += 10
            strengths.append("交易活跃度适中")
        elif performance.total_trades >= 50:
            score += 8
        elif performance.total_trades >= 20:
            score += 5
        elif performance.total_trades >= 10:
            score += 3
        else:
            weaknesses.append("交易次数较少")
            suggestions.append("可能需要调整策略频率")
        
        # 设置绩效等级
        analysis.overall_score = score
        analysis.strengths = strengths
        analysis.weaknesses = weaknesses
        analysis.improvement_suggestions = suggestions
        
        if score >= 85:
            analysis.performance_grade = "A"
        elif score >= 70:
            analysis.performance_grade = "B"
        elif score >= 55:
            analysis.performance_grade = "C"
        elif score >= 40:
            analysis.performance_grade = "D"
        else:
            analysis.performance_grade = "F"
        
        return analysis
    
    def compare_strategy_performances(self, instances: List[StrategyInstance]) -> Dict[str, Any]:
        """比较多个策略的绩效"""
        if not instances:
            return {"error": "没有策略可比较"}
        
        comparison_data = []
        
        for instance in instances:
            if instance.performance:
                analysis = self.analyze_strategy_performance(instance)
                comparison_data.append({
                    "instance_id": instance.instance_id,
                    "strategy_name": instance.configuration.strategy_name if instance.configuration else "Unknown",
                    "performance": instance.performance.to_dict(),
                    "analysis": analysis.to_dict()
                })
        
        if not comparison_data:
            return {"error": "没有有效的绩效数据"}
        
        # 计算排名
        comparison_data.sort(key=lambda x: x["analysis"]["overall_score"], reverse=True)
        for i, data in enumerate(comparison_data):
            data["rank"] = i + 1
        
        # 计算统计信息
        scores = [data["analysis"]["overall_score"] for data in comparison_data]
        statistics = {
            "total_strategies": len(comparison_data),
            "average_score": sum(scores) / len(scores),
            "best_score": max(scores),
            "worst_score": min(scores)
        }
        
        return {
            "comparison_data": comparison_data,
            "statistics": statistics
        }
    
    def calculate_portfolio_metrics(self, instances: List[StrategyInstance]) -> Dict[str, Any]:
        """计算组合指标"""
        if not instances:
            return {}
        
        total_pnl = 0.0
        total_trades = 0
        weighted_win_rate = 0.0
        max_drawdown = 0.0
        
        for instance in instances:
            if instance.performance:
                perf = instance.performance
                total_pnl += perf.total_pnl
                total_trades += perf.total_trades
                
                # 按交易次数加权胜率
                weighted_win_rate += perf.win_rate * perf.total_trades
                
                # 取最大回撤
                max_drawdown = max(max_drawdown, perf.max_drawdown)
        
        if total_trades > 0:
            weighted_win_rate /= total_trades
        
        return {
            "total_pnl": total_pnl,
            "total_trades": total_trades,
            "average_win_rate": weighted_win_rate,
            "max_portfolio_drawdown": max_drawdown,
            "strategy_count": len(instances)
        }
    
    def suggest_optimization_actions(self, instance: StrategyInstance) -> List[str]:
        """建议优化操作"""
        suggestions = []
        
        if not instance.performance:
            return ["收集更多绩效数据"]
        
        performance = instance.performance
        
        # 基于绩效的建议
        if performance.total_pnl < 0:
            suggestions.extend([
                "停止策略并分析亏损原因",
                "回测验证策略逻辑",
                "调整参数设置"
            ])
        
        if performance.max_drawdown > 0.15:
            suggestions.extend([
                "加强止损机制",
                "降低单笔交易风险",
                "优化仓位管理"
            ])
        
        if performance.win_rate < 0.4:
            suggestions.extend([
                "优化入场信号",
                "改善出场时机",
                "增加过滤条件"
            ])
        
        if performance.sharpe_ratio < 1.0:
            suggestions.extend([
                "平衡收益和风险",
                "减少不必要的交易",
                "优化资金使用效率"
            ])
        
        # 基于运行时间的建议
        runtime = instance.get_runtime_duration()
        if runtime and runtime > 86400:  # 超过1天
            trades_per_day = performance.total_trades / (runtime / 86400)
            if trades_per_day > 50:
                suggestions.append("考虑降低交易频率")
            elif trades_per_day < 1:
                suggestions.append("考虑增加交易机会")
        
        return suggestions
