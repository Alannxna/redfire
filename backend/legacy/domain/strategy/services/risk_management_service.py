"""
风险管理领域服务
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

from ..entities.strategy_instance import StrategyInstance

logger = logging.getLogger(__name__)


class RiskManagementService:
    """风险管理领域服务"""
    
    def __init__(self, storage_path: str = "./strategy_data"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # 风险规则
        self.risk_rules: Dict[str, Dict[str, Any]] = {}
        
        # 风险事件
        self.risk_events: List[Dict[str, Any]] = []
        
        # 加载已有的风险规则和事件
        self._load_risk_data()
    
    def add_risk_rule(self, strategy_name: str, rule_config: Dict[str, Any]) -> None:
        """添加风险规则"""
        self.risk_rules[strategy_name] = rule_config
        self._save_risk_rules()
        logger.info(f"添加风险规则: {strategy_name}")
    
    def remove_risk_rule(self, strategy_name: str) -> bool:
        """移除风险规则"""
        if strategy_name in self.risk_rules:
            del self.risk_rules[strategy_name]
            self._save_risk_rules()
            logger.info(f"移除风险规则: {strategy_name}")
            return True
        return False
    
    async def check_strategy_risk(self, instance: StrategyInstance) -> bool:
        """检查策略风险"""
        strategy_name = instance.config.strategy_name
        
        # 检查时间限制
        if not self._check_time_limit(strategy_name):
            logger.warning(f"策略时间限制检查失败: {strategy_name}")
            return False
        
        # 检查盈亏限制
        current_pnl = instance.performance.get("daily_pnl", 0.0)
        if not self._check_pnl_limit(strategy_name, current_pnl):
            logger.warning(f"策略盈亏限制检查失败: {strategy_name}, 当前PnL: {current_pnl}")
            return False
        
        # 检查持仓限制
        if not self._check_position_limit(strategy_name, instance):
            logger.warning(f"策略持仓限制检查失败: {strategy_name}")
            return False
        
        return True
    
    def _check_time_limit(self, strategy_name: str) -> bool:
        """检查时间限制"""
        if strategy_name not in self.risk_rules:
            return True
        
        limits = self.risk_rules[strategy_name].get("time_limits", {})
        
        now = datetime.now()
        start_time = limits.get("start_time")
        end_time = limits.get("end_time")
        
        if start_time and end_time:
            try:
                start_dt = datetime.strptime(start_time, "%H:%M:%S").time()
                end_dt = datetime.strptime(end_time, "%H:%M:%S").time()
                current_time = now.time()
                
                return start_dt <= current_time <= end_dt
            except ValueError:
                logger.error(f"时间格式错误: {start_time}, {end_time}")
                return True
        
        return True
    
    def _check_pnl_limit(self, strategy_name: str, current_pnl: float) -> bool:
        """检查盈亏限制"""
        if strategy_name not in self.risk_rules:
            return True
        
        limits = self.risk_rules[strategy_name].get("pnl_limits", {})
        max_loss = limits.get("max_daily_loss", float('inf'))
        
        return current_pnl > -max_loss
    
    def _check_position_limit(self, strategy_name: str, instance: StrategyInstance) -> bool:
        """检查持仓限制"""
        if strategy_name not in self.risk_rules:
            return True
        
        limits = self.risk_rules[strategy_name].get("position_limits", {})
        
        # 获取当前持仓（这里需要根据实际情况调整）
        current_position = instance.performance.get("position", 0)
        max_position = limits.get("max_position", float('inf'))
        
        return abs(current_position) <= max_position
    
    async def record_risk_event(self, event: Dict[str, Any]) -> None:
        """记录风险事件"""
        event["id"] = len(self.risk_events) + 1
        event["recorded_at"] = datetime.now().isoformat()
        
        self.risk_events.append(event)
        
        # 保持最近1000个事件
        if len(self.risk_events) > 1000:
            self.risk_events = self.risk_events[-1000:]
        
        self._save_risk_events()
        logger.warning(f"记录风险事件: {event}")
    
    async def get_risk_events(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取风险事件"""
        return self.risk_events[-limit:]
    
    def _load_risk_data(self) -> None:
        """加载风险数据"""
        # 加载风险规则
        rules_file = self.storage_path / "risk_rules.json"
        if rules_file.exists():
            try:
                with open(rules_file, 'r', encoding='utf-8') as f:
                    self.risk_rules = json.load(f)
                logger.info(f"加载了 {len(self.risk_rules)} 个风险规则")
            except Exception as e:
                logger.error(f"风险规则加载失败: {e}")
        
        # 加载风险事件
        events_file = self.storage_path / "risk_events.json"
        if events_file.exists():
            try:
                with open(events_file, 'r', encoding='utf-8') as f:
                    self.risk_events = json.load(f)
                logger.info(f"加载了 {len(self.risk_events)} 个风险事件")
            except Exception as e:
                logger.error(f"风险事件加载失败: {e}")
    
    def _save_risk_rules(self) -> None:
        """保存风险规则"""
        rules_file = self.storage_path / "risk_rules.json"
        try:
            with open(rules_file, 'w', encoding='utf-8') as f:
                json.dump(self.risk_rules, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"风险规则保存失败: {e}")
    
    def _save_risk_events(self) -> None:
        """保存风险事件"""
        events_file = self.storage_path / "risk_events.json"
        try:
            with open(events_file, 'w', encoding='utf-8') as f:
                json.dump(self.risk_events, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"风险事件保存失败: {e}")
