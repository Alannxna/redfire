"""
Risk Management Service
=======================

风险管理服务，负责风险计算、监控、控制等核心业务逻辑。
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from decimal import Decimal
import math

from ..entities.position_entity import Position
from ..entities.account_entity import Account
from ..entities.order_entity import Order
from ..enums import Direction, OrderStatus
from ..constants import (
    DEFAULT_MAX_POSITION_RATIO, DEFAULT_STOP_LOSS_RATIO,
    DEFAULT_TAKE_PROFIT_RATIO, MAX_DAILY_LOSS_RATIO
)

logger = logging.getLogger(__name__)


class RiskManagementService:
    """风险管理服务"""
    
    def __init__(self):
        self._risk_limits: Dict[str, Dict[str, Any]] = {}
        self._risk_alerts: List[Dict[str, Any]] = []
        self._risk_history: List[Dict[str, Any]] = []
        
        # 风险指标
        self._risk_metrics = {
            "total_risk": Decimal("0"),
            "position_risk": Decimal("0"),
            "concentration_risk": Decimal("0"),
            "liquidity_risk": Decimal("0"),
            "market_risk": Decimal("0")
        }
    
    # ==================== 风险限额管理 ====================
    
    async def set_risk_limits(
        self,
        user_id: str,
        max_position_ratio: Decimal = DEFAULT_MAX_POSITION_RATIO,
        max_daily_loss_ratio: Decimal = MAX_DAILY_LOSS_RATIO,
        max_single_position_ratio: Decimal = Decimal("0.2"),
        max_concentration_ratio: Decimal = Decimal("0.3"),
        stop_loss_ratio: Decimal = DEFAULT_STOP_LOSS_RATIO,
        take_profit_ratio: Decimal = DEFAULT_TAKE_PROFIT_RATIO
    ) -> None:
        """设置风险限额"""
        try:
            self._risk_limits[user_id] = {
                "max_position_ratio": max_position_ratio,
                "max_daily_loss_ratio": max_daily_loss_ratio,
                "max_single_position_ratio": max_single_position_ratio,
                "max_concentration_ratio": max_concentration_ratio,
                "stop_loss_ratio": stop_loss_ratio,
                "take_profit_ratio": take_profit_ratio,
                "create_time": datetime.now(),
                "update_time": datetime.now()
            }
            
            logger.info(f"设置风险限额成功: {user_id}")
            
        except Exception as e:
            logger.error(f"设置风险限额失败: {e}")
            raise
    
    async def get_risk_limits(self, user_id: str) -> Optional[Dict[str, Any]]:
        """获取风险限额"""
        return self._risk_limits.get(user_id)
    
    async def update_risk_limits(
        self,
        user_id: str,
        **kwargs
    ) -> bool:
        """更新风险限额"""
        try:
            if user_id not in self._risk_limits:
                return False
            
            limits = self._risk_limits[user_id]
            limits.update(kwargs)
            limits["update_time"] = datetime.now()
            
            logger.info(f"更新风险限额成功: {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"更新风险限额失败: {e}")
            return False
    
    # ==================== 风险计算 ====================
    
    async def calculate_position_risk(
        self,
        positions: List[Position],
        market_data: Dict[str, Decimal]
    ) -> Dict[str, Any]:
        """计算持仓风险"""
        try:
            if not positions:
                return {"total_risk": 0, "risk_breakdown": {}}
            
            total_risk = Decimal("0")
            risk_breakdown = {}
            
            for position in positions:
                if position.status.value != "ACTIVE":
                    continue
                
                # 获取当前市场价格
                current_price = market_data.get(position.symbol, Decimal("0"))
                if current_price == 0:
                    continue
                
                # 计算单个持仓风险
                position_risk = await self._calculate_single_position_risk(
                    position, current_price
                )
                
                risk_breakdown[position.symbol] = position_risk
                total_risk += position_risk["risk_value"]
            
            return {
                "total_risk": float(total_risk),
                "risk_breakdown": risk_breakdown,
                "position_count": len(positions)
            }
            
        except Exception as e:
            logger.error(f"持仓风险计算失败: {e}")
            return {"total_risk": 0, "risk_breakdown": {}, "error": str(e)}
    
    async def _calculate_single_position_risk(
        self,
        position: Position,
        current_price: Decimal
    ) -> Dict[str, Any]:
        """计算单个持仓风险"""
        try:
            # 计算未实现盈亏
            unrealized_pnl = position.unrealized_pnl
            
            # 计算持仓市值
            position_value = position.total_volume * current_price
            
            # 计算风险值（基于盈亏和持仓市值的综合评估）
            risk_value = abs(unrealized_pnl) + (position_value * Decimal("0.1"))
            
            # 计算风险等级
            if risk_value > position_value * Decimal("0.5"):
                risk_level = "HIGH"
            elif risk_value > position_value * Decimal("0.2"):
                risk_level = "MEDIUM"
            else:
                risk_level = "LOW"
            
            return {
                "symbol": position.symbol,
                "position_value": float(position_value),
                "unrealized_pnl": float(unrealized_pnl),
                "risk_value": float(risk_value),
                "risk_level": risk_level,
                "risk_ratio": float(risk_value / position_value) if position_value > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"单个持仓风险计算失败: {e}")
            return {"error": str(e)}
    
    async def calculate_concentration_risk(
        self,
        positions: List[Position],
        market_data: Dict[str, Decimal]
    ) -> Dict[str, Any]:
        """计算集中度风险"""
        try:
            if not positions:
                return {"concentration_risk": 0, "concentration_breakdown": {}}
            
            # 计算总持仓市值
            total_value = Decimal("0")
            symbol_values = {}
            
            for position in positions:
                if position.status.value != "ACTIVE":
                    continue
                
                current_price = market_data.get(position.symbol, Decimal("0"))
                if current_price == 0:
                    continue
                
                position_value = position.total_volume * current_price
                symbol_values[position.symbol] = position_value
                total_value += position_value
            
            if total_value == 0:
                return {"concentration_risk": 0, "concentration_breakdown": {}}
            
            # 计算集中度
            concentration_risk = Decimal("0")
            concentration_breakdown = {}
            
            for symbol, value in symbol_values.items():
                concentration_ratio = value / total_value
                concentration_breakdown[symbol] = {
                    "value": float(value),
                    "ratio": float(concentration_ratio),
                    "risk_level": "HIGH" if concentration_ratio > Decimal("0.3") else "MEDIUM"
                }
                
                # 集中度风险 = 最大集中度比例
                if concentration_ratio > concentration_risk:
                    concentration_risk = concentration_ratio
            
            return {
                "concentration_risk": float(concentration_risk),
                "concentration_breakdown": concentration_breakdown,
                "total_value": float(total_value)
            }
            
        except Exception as e:
            logger.error(f"集中度风险计算失败: {e}")
            return {"concentration_risk": 0, "concentration_breakdown": {}, "error": str(e)}
    
    async def calculate_var(
        self,
        positions: List[Position],
        market_data: Dict[str, Decimal],
        confidence_level: float = 0.95,
        time_horizon: int = 1
    ) -> Dict[str, Any]:
        """计算VaR (Value at Risk)"""
        try:
            if not positions:
                return {"var": 0, "confidence_level": confidence_level, "time_horizon": time_horizon}
            
            # 计算投资组合总价值
            portfolio_value = Decimal("0")
            position_returns = []
            
            for position in positions:
                if position.status.value != "ACTIVE":
                    continue
                
                current_price = market_data.get(position.symbol, Decimal("0"))
                if current_price == 0:
                    continue
                
                position_value = position.total_volume * current_price
                portfolio_value += position_value
                
                # 计算持仓收益率（简化计算）
                if position.long_avg_price > 0:
                    return_rate = (current_price - position.long_avg_price) / position.long_avg_price
                    position_returns.append(float(return_rate))
            
            if not position_returns or portfolio_value == 0:
                return {"var": 0, "confidence_level": confidence_level, "time_horizon": time_horizon}
            
            # 计算收益率统计
            mean_return = sum(position_returns) / len(position_returns)
            variance = sum((r - mean_return) ** 2 for r in position_returns) / len(position_returns)
            std_dev = math.sqrt(variance)
            
            # 计算VaR (假设正态分布)
            z_score = self._get_z_score(confidence_level)
            var = portfolio_value * std_dev * z_score * math.sqrt(time_horizon)
            
            return {
                "var": float(var),
                "confidence_level": confidence_level,
                "time_horizon": time_horizon,
                "portfolio_value": float(portfolio_value),
                "mean_return": mean_return,
                "std_dev": std_dev,
                "z_score": z_score
            }
            
        except Exception as e:
            logger.error(f"VaR计算失败: {e}")
            return {"var": 0, "confidence_level": confidence_level, "time_horizon": time_horizon, "error": str(e)}
    
    def _get_z_score(self, confidence_level: float) -> float:
        """获取Z分数"""
        # 简化的Z分数映射
        z_scores = {
            0.90: 1.28,
            0.95: 1.65,
            0.99: 2.33
        }
        return z_scores.get(confidence_level, 1.65)
    
    # ==================== 风险检查 ====================
    
    async def check_order_risk(
        self,
        order: Order,
        account: Account,
        positions: List[Position],
        market_data: Dict[str, Decimal]
    ) -> Dict[str, Any]:
        """检查订单风险"""
        try:
            risk_result = {
                "is_safe": True,
                "warnings": [],
                "errors": [],
                "risk_level": "LOW"
            }
            
            # 检查资金风险
            if not await self._check_fund_risk(order, account):
                risk_result["is_safe"] = False
                risk_result["errors"].append("资金风险检查未通过")
            
            # 检查持仓风险
            if not await self._check_position_risk(order, positions):
                risk_result["is_safe"] = False
                risk_result["errors"].append("持仓风险检查未通过")
            
            # 检查集中度风险
            if not await self._check_concentration_risk(order, positions, market_data):
                risk_result["warnings"].append("持仓集中度过高")
            
            # 检查止损止盈
            if not await self._check_stop_loss_take_profit(order, positions, market_data):
                risk_result["warnings"].append("建议设置止损止盈")
            
            # 确定风险等级
            if risk_result["errors"]:
                risk_result["risk_level"] = "HIGH"
            elif risk_result["warnings"]:
                risk_result["risk_level"] = "MEDIUM"
            
            return risk_result
            
        except Exception as e:
            logger.error(f"订单风险检查失败: {e}")
            return {
                "is_safe": False,
                "warnings": [],
                "errors": [str(e)],
                "risk_level": "HIGH"
            }
    
    async def _check_fund_risk(self, order: Order, account: Account) -> bool:
        """检查资金风险"""
        try:
            # 检查账户状态
            if not account.is_active or not account.is_trading:
                return False
            
            # 检查可用资金
            required_amount = order.volume * (order.price or Decimal("100"))
            if not account.can_trade(required_amount):
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"资金风险检查失败: {e}")
            return False
    
    async def _check_position_risk(self, order: Order, positions: List[Position]) -> bool:
        """检查持仓风险"""
        try:
            # 检查持仓限额
            if order.offset.value == "OPEN":
                # 计算新持仓数量
                current_position = next(
                    (p for p in positions if p.symbol == order.symbol), None
                )
                
                if current_position:
                    new_total_volume = current_position.total_volume + order.volume
                    # 这里应该检查具体的持仓限额
                    if new_total_volume > 1000000:  # 假设限额100万
                        return False
            
            return True
            
        except Exception as e:
            logger.error(f"持仓风险检查失败: {e}")
            return False
    
    async def _check_concentration_risk(
        self,
        order: Order,
        positions: List[Position],
        market_data: Dict[str, Decimal]
    ) -> bool:
        """检查集中度风险"""
        try:
            # 计算新订单的市值
            order_value = order.volume * (order.price or Decimal("100"))
            
            # 计算总持仓市值
            total_value = sum(
                p.total_volume * market_data.get(p.symbol, Decimal("0"))
                for p in positions if p.status.value == "ACTIVE"
            )
            
            if total_value > 0:
                concentration_ratio = order_value / total_value
                return concentration_ratio <= Decimal("0.3")  # 30%集中度限制
            
            return True
            
        except Exception as e:
            logger.error(f"集中度风险检查失败: {e}")
            return False
    
    async def _check_stop_loss_take_profit(
        self,
        order: Order,
        positions: List[Position],
        market_data: Dict[str, Decimal]
    ) -> bool:
        """检查止损止盈"""
        try:
            # 检查是否已有止损止盈设置
            if order.stop_price:
                return True
            
            # 检查持仓是否有止损止盈
            current_position = next(
                (p for p in positions if p.symbol == order.symbol), None
            )
            
            if current_position and current_position.total_volume > 0:
                # 建议设置止损止盈
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"止损止盈检查失败: {e}")
            return True
    
    # ==================== 风险监控 ====================
    
    async def monitor_risk(
        self,
        positions: List[Position],
        accounts: List[Account],
        market_data: Dict[str, Decimal]
    ) -> Dict[str, Any]:
        """监控风险"""
        try:
            risk_status = {
                "overall_risk": "LOW",
                "alerts": [],
                "metrics": {},
                "timestamp": datetime.now().isoformat()
            }
            
            # 计算各项风险指标
            position_risk = await self.calculate_position_risk(positions, market_data)
            concentration_risk = await self.calculate_concentration_risk(positions, market_data)
            var_result = await self.calculate_var(positions, market_data)
            
            # 更新风险指标
            self._risk_metrics.update({
                "position_risk": Decimal(str(position_risk.get("total_risk", 0))),
                "concentration_risk": Decimal(str(concentration_risk.get("concentration_risk", 0))),
                "market_risk": Decimal(str(var_result.get("var", 0)))
            })
            
            # 综合风险评估
            overall_risk = await self._assess_overall_risk()
            risk_status["overall_risk"] = overall_risk
            
            # 生成风险告警
            alerts = await self._generate_risk_alerts(positions, accounts, market_data)
            risk_status["alerts"] = alerts
            
            # 风险指标
            risk_status["metrics"] = {
                "position_risk": float(self._risk_metrics["position_risk"]),
                "concentration_risk": float(self._risk_metrics["concentration_risk"]),
                "market_risk": float(self._risk_metrics["market_risk"]),
                "var_95_1d": float(var_result.get("var", 0))
            }
            
            # 记录风险历史
            self._risk_history.append(risk_status)
            
            return risk_status
            
        except Exception as e:
            logger.error(f"风险监控失败: {e}")
            return {"error": str(e)}
    
    async def _assess_overall_risk(self) -> str:
        """评估整体风险"""
        try:
            # 基于各项风险指标综合评估
            risk_score = 0
            
            if self._risk_metrics["position_risk"] > 1000000:  # 100万
                risk_score += 3
            elif self._risk_metrics["position_risk"] > 500000:  # 50万
                risk_score += 2
            elif self._risk_metrics["position_risk"] > 100000:  # 10万
                risk_score += 1
            
            if self._risk_metrics["concentration_risk"] > Decimal("0.5"):
                risk_score += 3
            elif self._risk_metrics["concentration_risk"] > Decimal("0.3"):
                risk_score += 2
            elif self._risk_metrics["concentration_risk"] > Decimal("0.1"):
                risk_score += 1
            
            if self._risk_metrics["market_risk"] > 500000:  # 50万
                risk_score += 3
            elif self._risk_metrics["market_risk"] > 200000:  # 20万
                risk_score += 2
            elif self._risk_metrics["market_risk"] > 50000:  # 5万
                risk_score += 1
            
            # 确定风险等级
            if risk_score >= 7:
                return "HIGH"
            elif risk_score >= 4:
                return "MEDIUM"
            else:
                return "LOW"
                
        except Exception as e:
            logger.error(f"整体风险评估失败: {e}")
            return "MEDIUM"
    
    async def _generate_risk_alerts(
        self,
        positions: List[Position],
        accounts: List[Account],
        market_data: Dict[str, Decimal]
    ) -> List[Dict[str, Any]]:
        """生成风险告警"""
        try:
            alerts = []
            
            # 检查持仓风险
            for position in positions:
                if position.status.value != "ACTIVE":
                    continue
                
                current_price = market_data.get(position.symbol, Decimal("0"))
                if current_price == 0:
                    continue
                
                # 检查止损
                if position.is_long and current_price < position.long_avg_price * (1 - DEFAULT_STOP_LOSS_RATIO):
                    alerts.append({
                        "type": "STOP_LOSS",
                        "symbol": position.symbol,
                        "message": f"持仓{position.symbol}触发止损预警",
                        "severity": "HIGH",
                        "timestamp": datetime.now().isoformat()
                    })
                
                # 检查止盈
                if position.is_long and current_price > position.long_avg_price * (1 + DEFAULT_TAKE_PROFIT_RATIO):
                    alerts.append({
                        "type": "TAKE_PROFIT",
                        "symbol": position.symbol,
                        "message": f"持仓{position.symbol}触发止盈预警",
                        "severity": "MEDIUM",
                        "timestamp": datetime.now().isoformat()
                    })
            
            # 检查账户风险
            for account in accounts:
                if account.risk_level == "DANGER":
                    alerts.append({
                        "type": "ACCOUNT_RISK",
                        "account_id": account.account_id,
                        "message": f"账户{account.account_id}风险等级为危险",
                        "severity": "HIGH",
                        "timestamp": datetime.now().isoformat()
                    })
                elif account.risk_level == "WARNING":
                    alerts.append({
                        "type": "ACCOUNT_RISK",
                        "account_id": account.account_id,
                        "message": f"账户{account.account_id}风险等级为警告",
                        "severity": "MEDIUM",
                        "timestamp": datetime.now().isoformat()
                    })
            
            # 保存告警
            self._risk_alerts.extend(alerts)
            
            return alerts
            
        except Exception as e:
            logger.error(f"风险告警生成失败: {e}")
            return []
    
    # ==================== 风险报告 ====================
    
    async def get_risk_report(
        self,
        user_id: str = "",
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """获取风险报告"""
        try:
            if not start_date:
                start_date = datetime.now() - timedelta(days=30)
            if not end_date:
                end_date = datetime.now()
            
            # 过滤风险历史
            filtered_history = [
                h for h in self._risk_history
                if start_date <= datetime.fromisoformat(h["timestamp"]) <= end_date
            ]
            
            # 过滤风险告警
            filtered_alerts = [
                a for a in self._risk_alerts
                if start_date <= datetime.fromisoformat(a["timestamp"]) <= end_date
            ]
            
            return {
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                "risk_summary": {
                    "total_alerts": len(filtered_alerts),
                    "high_severity_alerts": len([a for a in filtered_alerts if a["severity"] == "HIGH"]),
                    "medium_severity_alerts": len([a for a in filtered_alerts if a["severity"] == "MEDIUM"]),
                    "low_severity_alerts": len([a for a in filtered_alerts if a["severity"] == "LOW"])
                },
                "risk_trends": filtered_history,
                "recent_alerts": filtered_alerts[-10:],  # 最近10条告警
                "current_metrics": self._risk_metrics
            }
            
        except Exception as e:
            logger.error(f"风险报告生成失败: {e}")
            return {"error": str(e)}
    
    async def get_risk_alerts(self, severity: str = "") -> List[Dict[str, Any]]:
        """获取风险告警"""
        try:
            if severity:
                return [a for a in self._risk_alerts if a["severity"] == severity]
            return self._risk_alerts
            
        except Exception as e:
            logger.error(f"获取风险告警失败: {e}")
            return []
    
    async def clear_risk_alerts(self) -> None:
        """清除风险告警"""
        try:
            self._risk_alerts.clear()
            logger.info("风险告警已清除")
            
        except Exception as e:
            logger.error(f"清除风险告警失败: {e}")
