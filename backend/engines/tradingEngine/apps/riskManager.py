"""
风险管理应用 (Risk Manager App)

负责管理交易风险，包括：
- 仓位限制
- 损失限制
- 风险指标监控
- 风险预警
"""

import logging
import time
from typing import Dict, List, Optional, Any
from ..appBase import BaseTradingApp


class RiskManagerApp(BaseTradingApp):
    """
    风险管理应用类
    
    负责监控和控制交易风险
    """
    
    def __init__(self, main_engine=None, app_name: str = "RiskManager"):
        """
        初始化风险管理应用
        
        Args:
            main_engine: 主交易引擎实例
            app_name: 应用名称
        """
        super().__init__(main_engine, app_name)
        
        # 风险配置
        self.riskConfig = {
            'maxPositionSize': 1000000,  # 最大仓位大小
            'maxDailyLoss': 100000,      # 最大日损失
            'maxDrawdown': 0.1,          # 最大回撤比例
            'positionLimit': 0.8,        # 仓位限制比例
            'stopLossThreshold': 0.05    # 止损阈值
        }
        
        # 风险状态
        self.riskStatus = {
            'currentPosition': 0,
            'dailyPnL': 0,
            'maxDrawdown': 0,
            'riskLevel': 'LOW',
            'lastUpdate': time.time()
        }
        
        # 风险规则
        self.riskRules: List[Dict[str, Any]] = []
        
        # 风险事件
        self.riskEvents: List[Dict[str, Any]] = []
        
        # 初始化风险规则
        self._init_risk_rules()
    
    def _init_risk_rules(self):
        """初始化风险规则"""
        self.riskRules = [
            {
                'name': 'position_limit',
                'description': '仓位限制检查',
                'enabled': True,
                'check_function': self._check_position_limit
            },
            {
                'name': 'daily_loss_limit',
                'description': '日损失限制检查',
                'enabled': True,
                'check_function': self._check_daily_loss_limit
            },
            {
                'name': 'drawdown_limit',
                'description': '回撤限制检查',
                'enabled': True,
                'check_function': self._check_drawdown_limit
            }
        ]
    
    def startApp(self) -> bool:
        """
        启动风险管理应用
        
        Returns:
            bool: 启动是否成功
        """
        try:
            if self.isActive:
                self.logger.warning("风险管理应用已经在运行")
                return True
            
            self.logger.info("正在启动风险管理应用...")
            
            # 启动风险监控
            self._start_risk_monitoring()
            
            self.isActive = True
            self.logger.info("风险管理应用启动成功")
            return True
            
        except Exception as e:
            self.logger.error(f"启动风险管理应用失败: {e}")
            return False
    
    def stopApp(self) -> bool:
        """
        停止风险管理应用
        
        Returns:
            bool: 停止是否成功
        """
        try:
            if not self.isActive:
                self.logger.warning("风险管理应用已经停止")
                return True
            
            self.logger.info("正在停止风险管理应用...")
            
            # 停止风险监控
            self._stop_risk_monitoring()
            
            self.isActive = False
            self.logger.info("风险管理应用已停止")
            return True
            
        except Exception as e:
            self.logger.error(f"停止风险管理应用失败: {e}")
            return False
    
    def closeApp(self) -> bool:
        """
        关闭风险管理应用
        
        Returns:
            bool: 关闭是否成功
        """
        try:
            if self.isActive:
                self.stopApp()
            
            # 清理资源
            self._cleanup()
            
            self.logger.info("风险管理应用已关闭")
            return True
            
        except Exception as e:
            self.logger.error(f"关闭风险管理应用失败: {e}")
            return False
    
    def _start_risk_monitoring(self):
        """启动风险监控"""
        self.logger.info("风险监控已启动")
    
    def _stop_risk_monitoring(self):
        """停止风险监控"""
        self.logger.info("风险监控已停止")
    
    def _cleanup(self):
        """清理资源"""
        self.riskEvents.clear()
    
    def updateRiskStatus(self, position: float, pnl: float, drawdown: float):
        """
        更新风险状态
        
        Args:
            position: 当前仓位
            pnl: 盈亏
            drawdown: 回撤
        """
        try:
            self.riskStatus['currentPosition'] = position
            self.riskStatus['dailyPnL'] = pnl
            self.riskStatus['maxDrawdown'] = max(self.riskStatus['maxDrawdown'], drawdown)
            self.riskStatus['lastUpdate'] = time.time()
            
            # 检查风险规则
            self._check_risk_rules()
            
            # 更新风险等级
            self._update_risk_level()
            
        except Exception as e:
            self.logger.error(f"更新风险状态失败: {e}")
    
    def _check_risk_rules(self):
        """检查所有风险规则"""
        for rule in self.riskRules:
            if rule['enabled']:
                try:
                    rule['check_function']()
                except Exception as e:
                    self.logger.error(f"风险规则检查失败: {rule['name']} - {e}")
    
    def _check_position_limit(self):
        """检查仓位限制"""
        if abs(self.riskStatus['currentPosition']) > self.riskConfig['maxPositionSize']:
            self._trigger_risk_event('POSITION_LIMIT_EXCEEDED', {
                'current': self.riskStatus['currentPosition'],
                'limit': self.riskConfig['maxPositionSize']
            })
    
    def _check_daily_loss_limit(self):
        """检查日损失限制"""
        if self.riskStatus['dailyPnL'] < -self.riskConfig['maxDailyLoss']:
            self._trigger_risk_event('DAILY_LOSS_LIMIT_EXCEEDED', {
                'current': self.riskStatus['dailyPnL'],
                'limit': -self.riskConfig['maxDailyLoss']
            })
    
    def _check_drawdown_limit(self):
        """检查回撤限制"""
        if self.riskStatus['maxDrawdown'] > self.riskConfig['maxDrawdown']:
            self._trigger_risk_event('DRAWDOWN_LIMIT_EXCEEDED', {
                'current': self.riskStatus['maxDrawdown'],
                'limit': self.riskConfig['maxDrawdown']
            })
    
    def _trigger_risk_event(self, event_type: str, event_data: Dict[str, Any]):
        """
        触发风险事件
        
        Args:
            event_type: 事件类型
            event_data: 事件数据
        """
        risk_event = {
            'type': event_type,
            'data': event_data,
            'timestamp': time.time(),
            'riskLevel': self.riskStatus['riskLevel']
        }
        
        self.riskEvents.append(risk_event)
        
        # 记录风险事件
        self.logger.warning(f"风险事件触发: {event_type} - {event_data}")
        
        # 发送事件到主引擎（如果可用）
        if self.mainTradingEngine and hasattr(self.mainTradingEngine, 'eventTradingEngine'):
            self.mainTradingEngine.eventTradingEngine.putEvent('risk_event', risk_event)
    
    def _update_risk_level(self):
        """更新风险等级"""
        # 基于多个指标计算风险等级
        risk_score = 0
        
        # 仓位风险
        position_ratio = abs(self.riskStatus['currentPosition']) / self.riskConfig['maxPositionSize']
        if position_ratio > 0.8:
            risk_score += 3
        elif position_ratio > 0.6:
            risk_score += 2
        elif position_ratio > 0.4:
            risk_score += 1
        
        # 损失风险
        loss_ratio = abs(self.riskStatus['dailyPnL']) / self.riskConfig['maxDailyLoss']
        if loss_ratio > 0.8:
            risk_score += 3
        elif loss_ratio > 0.6:
            risk_score += 2
        elif loss_ratio > 0.4:
            risk_score += 1
        
        # 回撤风险
        if self.riskStatus['maxDrawdown'] > self.riskConfig['maxDrawdown'] * 0.8:
            risk_score += 2
        elif self.riskStatus['maxDrawdown'] > self.riskConfig['maxDrawdown'] * 0.6:
            risk_score += 1
        
        # 设置风险等级
        if risk_score >= 6:
            self.riskStatus['riskLevel'] = 'HIGH'
        elif risk_score >= 3:
            self.riskStatus['riskLevel'] = 'MEDIUM'
        else:
            self.riskStatus['riskLevel'] = 'LOW'
    
    def setRiskConfig(self, config: Dict[str, Any]) -> bool:
        """
        设置风险配置
        
        Args:
            config: 风险配置字典
            
        Returns:
            bool: 设置是否成功
        """
        try:
            for key, value in config.items():
                if key in self.riskConfig:
                    self.riskConfig[key] = value
            
            self.logger.info("风险配置已更新")
            return True
            
        except Exception as e:
            self.logger.error(f"设置风险配置失败: {e}")
            return False
    
    def getRiskStatus(self) -> Dict[str, Any]:
        """
        获取风险状态
        
        Returns:
            Dict[str, Any]: 风险状态字典
        """
        return {
            'appName': self.appName,
            'isActive': self.isActive,
            'riskConfig': self.riskConfig.copy(),
            'riskStatus': self.riskStatus.copy(),
            'riskEventCount': len(self.riskEvents),
            'lastRiskEvent': self.riskEvents[-1] if self.riskEvents else None
        }
    
    def getRiskEvents(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        获取风险事件列表
        
        Args:
            limit: 返回的事件数量限制
            
        Returns:
            List[Dict[str, Any]]: 风险事件列表
        """
        return self.riskEvents[-limit:] if self.riskEvents else []
    
    def clearRiskEvents(self) -> bool:
        """
        清空风险事件
        
        Returns:
            bool: 清空是否成功
        """
        try:
            self.riskEvents.clear()
            self.logger.info("风险事件已清空")
            return True
            
        except Exception as e:
            self.logger.error(f"清空风险事件失败: {e}")
            return False
