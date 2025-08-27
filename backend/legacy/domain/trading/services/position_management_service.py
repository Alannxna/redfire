"""
Position Management Service
==========================

持仓管理服务，负责持仓的创建、更新、计算等核心业务逻辑。
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from decimal import Decimal

from ..entities.position_entity import Position
from ..entities.trade_entity import Trade
from ..entities.contract_entity import Contract
from ..enums import Direction, Offset, PositionStatus
from ..constants import DEFAULT_MAX_POSITION_RATIO

logger = logging.getLogger(__name__)


class PositionManagementService:
    """持仓管理服务"""
    
    def __init__(self):
        self._positions: Dict[str, Position] = {}
        self._contracts: Dict[str, Contract] = {}
        
        # 统计信息
        self._statistics = {
            "total_positions": 0,
            "active_positions": 0,
            "total_long_volume": 0,
            "total_short_volume": 0,
            "total_position_value": Decimal("0"),
            "total_unrealized_pnl": Decimal("0"),
            "total_realized_pnl": Decimal("0")
        }
    
    # ==================== 持仓创建和更新 ====================
    
    async def create_position(
        self,
        symbol: str,
        exchange: str,
        user_id: str,
        product: str = "",
        gateway_name: str = "",
        strategy_name: str = ""
    ) -> Position:
        """创建持仓"""
        try:
            position_key = self._get_position_key(symbol, exchange, user_id)
            
            if position_key in self._positions:
                raise ValueError(f"持仓已存在: {position_key}")
            
            position = Position(
                symbol=symbol,
                exchange=exchange,
                user_id=user_id,
                product=product,
                gateway_name=gateway_name,
                strategy_name=strategy_name
            )
            
            self._positions[position_key] = position
            self._update_statistics(position, "create")
            
            logger.info(f"创建持仓成功: {position_key}")
            return position
            
        except Exception as e:
            logger.error(f"创建持仓失败: {e}")
            raise
    
    async def update_position_from_trade(self, trade: Trade) -> Position:
        """根据成交更新持仓"""
        try:
            position_key = self._get_position_key(trade.symbol, trade.exchange, trade.user_id)
            
            # 获取或创建持仓
            if position_key not in self._positions:
                position = await self.create_position(
                    symbol=trade.symbol,
                    exchange=trade.exchange,
                    user_id=trade.user_id,
                    product=trade.product,
                    gateway_name=trade.gateway_name,
                    strategy_name=trade.strategy_name
                )
            else:
                position = self._positions[position_key]
            
            # 更新持仓
            is_open = trade.offset == Offset.OPEN
            position.update_position(
                direction=trade.direction.value,
                volume=trade.volume,
                price=trade.price,
                is_open=is_open
            )
            
            # 更新统计
            self._update_statistics(position, "update")
            
            logger.info(f"持仓更新成功: {position_key}, 成交: {trade.trade_id}")
            return position
            
        except Exception as e:
            logger.error(f"持仓更新失败: {e}")
            raise
    
    async def update_position_manually(
        self,
        symbol: str,
        exchange: str,
        user_id: str,
        direction: str,
        volume: int,
        price: Decimal,
        is_open: bool = True
    ) -> Position:
        """手动更新持仓"""
        try:
            position_key = self._get_position_key(symbol, exchange, user_id)
            
            if position_key not in self._positions:
                raise ValueError(f"持仓不存在: {position_key}")
            
            position = self._positions[position_key]
            position.update_position(direction, volume, price, is_open)
            
            # 更新统计
            self._update_statistics(position, "update")
            
            logger.info(f"手动更新持仓: {position_key}, {direction}, {volume}, {price}")
            return position
            
        except Exception as e:
            logger.error(f"手动更新持仓失败: {e}")
            raise
    
    # ==================== 持仓查询 ====================
    
    async def get_position(self, symbol: str, exchange: str, user_id: str) -> Optional[Position]:
        """获取持仓"""
        position_key = self._get_position_key(symbol, exchange, user_id)
        return self._positions.get(position_key)
    
    async def get_positions_by_user(self, user_id: str) -> List[Position]:
        """获取用户的持仓"""
        return [pos for pos in self._positions.values() if pos.user_id == user_id]
    
    async def get_positions_by_symbol(self, symbol: str) -> List[Position]:
        """获取指定品种的持仓"""
        return [pos for pos in self._positions.values() if pos.symbol == symbol]
    
    async def get_active_positions(self, user_id: str = "") -> List[Position]:
        """获取活跃持仓"""
        if user_id:
            return [pos for pos in self._positions.values() 
                   if pos.user_id == user_id and pos.status == PositionStatus.ACTIVE]
        else:
            return [pos for pos in self._positions.values() if pos.status == PositionStatus.ACTIVE]
    
    async def get_positions_by_status(self, status: PositionStatus) -> List[Position]:
        """根据状态获取持仓"""
        return [pos for pos in self._positions.values() if pos.status == status]
    
    # ==================== 持仓计算 ====================
    
    async def calculate_all_positions_pnl(self, market_data: Dict[str, Decimal]) -> None:
        """计算所有持仓的盈亏"""
        try:
            for position in self._positions.values():
                if position.status != PositionStatus.ACTIVE:
                    continue
                
                # 获取当前市场价格
                current_price = market_data.get(position.symbol)
                if current_price is not None:
                    position.calculate_pnl(current_price)
            
            # 更新统计
            self._update_total_statistics()
            
            logger.info("所有持仓盈亏计算完成")
            
        except Exception as e:
            logger.error(f"持仓盈亏计算失败: {e}")
    
    async def calculate_position_pnl(
        self,
        symbol: str,
        exchange: str,
        user_id: str,
        current_price: Decimal
    ) -> Optional[Decimal]:
        """计算指定持仓的盈亏"""
        try:
            position = await self.get_position(symbol, exchange, user_id)
            if not position:
                return None
            
            position.calculate_pnl(current_price)
            return position.unrealized_pnl
            
        except Exception as e:
            logger.error(f"持仓盈亏计算失败: {e}")
            return None
    
    # ==================== 持仓风险控制 ====================
    
    async def check_position_risk(
        self,
        symbol: str,
        exchange: str,
        user_id: str,
        new_volume: int,
        direction: Direction
    ) -> Dict[str, Any]:
        """检查持仓风险"""
        try:
            position = await self.get_position(symbol, exchange, user_id)
            current_volume = 0
            
            if position:
                if direction == Direction.LONG:
                    current_volume = position.long_volume
                else:
                    current_volume = position.short_volume
            
            # 计算新持仓数量
            new_total_volume = current_volume + new_volume
            
            # 获取合约信息
            contract = await self._get_contract(symbol, exchange)
            max_volume = contract.max_volume if contract else 999999999
            
            # 风险检查结果
            risk_result = {
                "is_safe": True,
                "warnings": [],
                "errors": []
            }
            
            # 检查持仓限额
            if new_total_volume > max_volume:
                risk_result["is_safe"] = False
                risk_result["errors"].append(f"持仓超过限额: {new_total_volume} > {max_volume}")
            
            # 检查持仓集中度
            if await self._check_position_concentration(symbol, exchange, user_id, new_total_volume):
                risk_result["warnings"].append("持仓集中度过高")
            
            # 检查风险度
            if await self._check_risk_degree(symbol, exchange, user_id, new_volume):
                risk_result["warnings"].append("风险度过高")
            
            return risk_result
            
        except Exception as e:
            logger.error(f"持仓风险检查失败: {e}")
            return {"is_safe": False, "warnings": [], "errors": [str(e)]}
    
    async def _check_position_concentration(
        self,
        symbol: str,
        exchange: str,
        user_id: str,
        new_volume: int
    ) -> bool:
        """检查持仓集中度"""
        try:
            # 获取用户所有持仓
            user_positions = await self.get_positions_by_user(user_id)
            
            if not user_positions:
                return False
            
            # 计算总持仓市值
            total_value = sum(pos.total_volume for pos in user_positions)
            new_position_value = new_volume
            
            # 计算集中度比例
            concentration_ratio = new_position_value / total_value if total_value > 0 else 0
            
            # 如果单个持仓超过30%，认为集中度过高
            return concentration_ratio > DEFAULT_MAX_POSITION_RATIO
            
        except Exception as e:
            logger.error(f"持仓集中度检查失败: {e}")
            return False
    
    async def _check_risk_degree(
        self,
        symbol: str,
        exchange: str,
        user_id: str,
        new_volume: int
    ) -> bool:
        """检查风险度"""
        try:
            # 这里应该实现具体的风险度计算逻辑
            # 暂时返回False
            return False
            
        except Exception as e:
            logger.error(f"风险度检查失败: {e}")
            return False
    
    # ==================== 持仓操作 ====================
    
    async def close_position(
        self,
        symbol: str,
        exchange: str,
        user_id: str
    ) -> bool:
        """平仓"""
        try:
            position = await self.get_position(symbol, exchange, user_id)
            if not position:
                return False
            
            position.close_position()
            self._update_statistics(position, "close")
            
            logger.info(f"持仓平仓成功: {symbol}.{exchange}.{user_id}")
            return True
            
        except Exception as e:
            logger.error(f"持仓平仓失败: {e}")
            return False
    
    async def reset_daily_pnl(self, user_id: str = "") -> None:
        """重置每日盈亏"""
        try:
            positions = await self.get_positions_by_user(user_id) if user_id else self._positions.values()
            
            for position in positions:
                position.reset_daily_pnl()
            
            logger.info(f"每日盈亏重置完成: {len(positions)}个持仓")
            
        except Exception as e:
            logger.error(f"每日盈亏重置失败: {e}")
    
    # ==================== 合约管理 ====================
    
    async def add_contract(self, contract: Contract) -> None:
        """添加合约"""
        contract_key = f"{contract.symbol}.{contract.exchange.value}"
        self._contracts[contract_key] = contract
        logger.info(f"添加合约: {contract_key}")
    
    async def _get_contract(self, symbol: str, exchange: str) -> Optional[Contract]:
        """获取合约"""
        contract_key = f"{symbol}.{exchange}"
        return self._contracts.get(contract_key)
    
    # ==================== 工具方法 ====================
    
    def _get_position_key(self, symbol: str, exchange: str, user_id: str) -> str:
        """获取持仓键"""
        return f"{symbol}.{exchange}.{user_id}"
    
    def _update_statistics(self, position: Position, action: str) -> None:
        """更新统计信息"""
        if action == "create":
            self._statistics["total_positions"] += 1
            self._statistics["active_positions"] += 1
        
        elif action == "update":
            # 更新持仓统计
            self._update_total_statistics()
        
        elif action == "close":
            self._statistics["active_positions"] -= 1
    
    def _update_total_statistics(self) -> None:
        """更新总统计信息"""
        try:
            total_long_volume = 0
            total_short_volume = 0
            total_position_value = Decimal("0")
            total_unrealized_pnl = Decimal("0")
            total_realized_pnl = Decimal("0")
            
            for position in self._positions.values():
                if position.status == PositionStatus.ACTIVE:
                    total_long_volume += position.long_volume
                    total_short_volume += position.short_volume
                    total_position_value += position.total_volume
                    total_unrealized_pnl += position.unrealized_pnl
                    total_realized_pnl += position.realized_pnl
            
            self._statistics.update({
                "total_long_volume": total_long_volume,
                "total_short_volume": total_short_volume,
                "total_position_value": total_position_value,
                "total_unrealized_pnl": total_unrealized_pnl,
                "total_realized_pnl": total_realized_pnl
            })
            
        except Exception as e:
            logger.error(f"统计信息更新失败: {e}")
    
    # ==================== 统计信息 ====================
    
    async def get_position_statistics(self) -> Dict[str, Any]:
        """获取持仓统计信息"""
        return {
            **self._statistics,
            "total_position_value": float(self._statistics["total_position_value"]),
            "total_unrealized_pnl": float(self._statistics["total_unrealized_pnl"]),
            "total_realized_pnl": float(self._statistics["total_realized_pnl"]),
            "net_position_volume": (
                self._statistics["total_long_volume"] - self._statistics["total_short_volume"]
            ),
            "average_position_size": (
                self._statistics["total_position_value"] / self._statistics["active_positions"]
                if self._statistics["active_positions"] > 0 else 0
            )
        }
    
    async def get_user_position_summary(self, user_id: str) -> Dict[str, Any]:
        """获取用户持仓摘要"""
        try:
            user_positions = await self.get_positions_by_user(user_id)
            
            if not user_positions:
                return {
                    "user_id": user_id,
                    "total_positions": 0,
                    "total_volume": 0,
                    "total_value": 0,
                    "total_pnl": 0
                }
            
            total_positions = len(user_positions)
            total_volume = sum(pos.total_volume for pos in user_positions)
            total_value = sum(pos.total_volume for pos in user_positions)
            total_pnl = sum(pos.total_pnl for pos in user_positions)
            
            return {
                "user_id": user_id,
                "total_positions": total_positions,
                "total_volume": total_volume,
                "total_value": float(total_value),
                "total_pnl": float(total_pnl),
                "positions": [pos.to_dict() for pos in user_positions]
            }
            
        except Exception as e:
            logger.error(f"获取用户持仓摘要失败: {e}")
            return {}
