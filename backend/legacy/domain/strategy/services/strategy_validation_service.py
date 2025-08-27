"""
策略验证服务
"""

import logging
from typing import List
from datetime import datetime

from src.domain.strategy.entities.strategy_entity import StrategyConfiguration, StrategyType

logger = logging.getLogger(__name__)


class StrategyValidationResult:
    """策略验证结果"""
    
    def __init__(self):
        self.is_valid = True
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.suggestions: List[str] = []
    
    def add_error(self, message: str):
        """添加错误"""
        self.errors.append(message)
        self.is_valid = False
    
    def add_warning(self, message: str):
        """添加警告"""
        self.warnings.append(message)
    
    def add_suggestion(self, message: str):
        """添加建议"""
        self.suggestions.append(message)


class StrategyValidationService:
    """策略验证服务"""
    
    def validate_strategy_configuration(self, config: StrategyConfiguration) -> StrategyValidationResult:
        """验证策略配置"""
        result = StrategyValidationResult()
        
        # 基础验证
        config_errors = config.validate()
        for error in config_errors:
            result.add_error(error)
        
        # 业务规则验证
        self._validate_strategy_class(config, result)
        self._validate_symbols(config, result)
        self._validate_parameters(config, result)
        self._validate_risk_limits(config, result)
        
        return result
    
    def _validate_strategy_class(self, config: StrategyConfiguration, result: StrategyValidationResult):
        """验证策略类"""
        # 检查策略类名格式
        if not config.strategy_class.endswith(('Strategy', 'Template')):
            result.add_warning("策略类名建议以Strategy或Template结尾")
        
        # 检查策略类型与类名的一致性
        type_prefixes = {
            StrategyType.CTA: ['Cta', 'CTA'],
            StrategyType.PORTFOLIO: ['Portfolio', 'Port'],
            StrategyType.SPREAD: ['Spread', 'Arbitrage'],
            StrategyType.OPTION: ['Option', 'Vol']
        }
        
        if config.strategy_type in type_prefixes:
            prefixes = type_prefixes[config.strategy_type]
            if not any(config.strategy_class.startswith(prefix) for prefix in prefixes):
                result.add_suggestion(f"策略类名建议以{'/'.join(prefixes)}开头")
    
    def _validate_symbols(self, config: StrategyConfiguration, result: StrategyValidationResult):
        """验证交易品种"""
        if len(config.symbol_list) > 20:
            result.add_warning("交易品种过多可能影响策略性能")
        
        # 检查品种格式
        for symbol in config.symbol_list:
            if not symbol or '.' not in symbol:
                result.add_error(f"无效的品种格式: {symbol}")
            
        # 不同策略类型的品种数量建议
        if config.strategy_type == StrategyType.CTA and len(config.symbol_list) > 5:
            result.add_suggestion("CTA策略建议交易品种不超过5个")
        elif config.strategy_type == StrategyType.SPREAD and len(config.symbol_list) != 2:
            result.add_warning("价差策略通常需要2个品种")
    
    def _validate_parameters(self, config: StrategyConfiguration, result: StrategyValidationResult):
        """验证参数"""
        params = config.parameters
        
        # 检查必要参数
        required_params = {
            StrategyType.CTA: ['fast_window', 'slow_window'],
            StrategyType.PORTFOLIO: ['rebalance_frequency'],
            StrategyType.SPREAD: ['spread_threshold']
        }
        
        if config.strategy_type in required_params:
            for param in required_params[config.strategy_type]:
                if param not in params:
                    result.add_suggestion(f"建议设置参数: {param}")
        
        # 检查参数合理性
        if 'fast_window' in params and 'slow_window' in params:
            if params['fast_window'] >= params['slow_window']:
                result.add_error("快速窗口应小于慢速窗口")
        
        # 检查数值范围
        for param, value in params.items():
            if isinstance(value, (int, float)):
                if value <= 0 and param.endswith(('_window', '_period', '_threshold')):
                    result.add_error(f"参数{param}应为正数")
    
    def _validate_risk_limits(self, config: StrategyConfiguration, result: StrategyValidationResult):
        """验证风险限制"""
        limits = config.risk_limits
        
        # 检查限制合理性
        if limits.max_position <= 0:
            result.add_error("最大持仓应为正数")
        
        if limits.max_daily_loss <= 0:
            result.add_error("最大日亏损应为正数")
        
        if limits.max_daily_loss >= limits.max_total_loss:
            result.add_warning("最大日亏损接近或超过最大总亏损")
        
        # 检查时间限制
        time_limits = limits.time_limits
        if 'start_time' in time_limits and 'end_time' in time_limits:
            try:
                start_time = datetime.strptime(time_limits['start_time'], "%H:%M:%S").time()
                end_time = datetime.strptime(time_limits['end_time'], "%H:%M:%S").time()
                
                if start_time >= end_time:
                    result.add_error("开始时间应早于结束时间")
            except ValueError:
                result.add_error("时间格式错误，应为HH:MM:SS")
