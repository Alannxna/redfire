"""
Settlement Service
==================

结算服务，负责日终结算、盈亏计算、费用结算等核心业务逻辑。
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta, date
from decimal import Decimal
from dataclasses import dataclass, field

from ..entities.position_entity import Position
from ..entities.account_entity import Account
from ..entities.order_entity import Order
from ..entities.trade_entity import Trade
from ..enums import OrderStatus, PositionStatus

logger = logging.getLogger(__name__)


@dataclass
class SettlementRecord:
    """结算记录"""
    settlement_id: str
    user_id: str
    settlement_date: date
    total_pnl: Decimal = Decimal("0")
    realized_pnl: Decimal = Decimal("0")
    unrealized_pnl: Decimal = Decimal("0")
    commission: Decimal = Decimal("0")
    fees: Decimal = Decimal("0")
    margin_used: Decimal = Decimal("0")
    available_funds: Decimal = Decimal("0")
    create_time: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "settlement_id": self.settlement_id,
            "user_id": self.user_id,
            "settlement_date": self.settlement_date.isoformat(),
            "total_pnl": float(self.total_pnl),
            "realized_pnl": float(self.realized_pnl),
            "unrealized_pnl": float(self.unrealized_pnl),
            "commission": float(self.commission),
            "fees": float(self.fees),
            "margin_used": float(self.margin_used),
            "available_funds": float(self.available_funds),
            "create_time": self.create_time.isoformat()
        }


@dataclass
class DailyReport:
    """日报"""
    report_id: str
    user_id: str
    report_date: date
    opening_balance: Decimal = Decimal("0")
    closing_balance: Decimal = Decimal("0")
    daily_pnl: Decimal = Decimal("0")
    total_commission: Decimal = Decimal("0")
    total_trades: int = 0
    positions_count: int = 0
    max_margin_used: Decimal = Decimal("0")
    create_time: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "report_id": self.report_id,
            "user_id": self.user_id,
            "report_date": self.report_date.isoformat(),
            "opening_balance": float(self.opening_balance),
            "closing_balance": float(self.closing_balance),
            "daily_pnl": float(self.daily_pnl),
            "total_commission": float(self.total_commission),
            "total_trades": self.total_trades,
            "positions_count": self.positions_count,
            "max_margin_used": float(self.max_margin_used),
            "create_time": self.create_time.isoformat()
        }


class SettlementService:
    """结算服务"""
    
    def __init__(self):
        self._settlement_records: Dict[str, List[SettlementRecord]] = {}
        self._daily_reports: Dict[str, List[DailyReport]] = {}
        self._commission_rates: Dict[str, Decimal] = {
            "stock": Decimal("0.0003"),  # 股票手续费0.03%
            "futures": Decimal("0.0001"),  # 期货手续费0.01%
            "forex": Decimal("0.0002"),  # 外汇手续费0.02%
        }
        self._fee_rates: Dict[str, Decimal] = {
            "stamp_tax": Decimal("0.001"),  # 印花税0.1%
            "transfer_fee": Decimal("0.00002"),  # 过户费0.002%
        }
    
    # ==================== 日终结算 ====================
    
    async def daily_settlement(
        self,
        settlement_date: date,
        accounts: List[Account],
        positions: List[Position],
        trades: List[Trade],
        market_data: Dict[str, Decimal]
    ) -> Dict[str, SettlementRecord]:
        """执行日终结算"""
        try:
            settlement_results = {}
            
            # 按用户分组处理结算
            user_accounts = {acc.user_id: acc for acc in accounts}
            user_positions = {}
            user_trades = {}
            
            # 分组数据
            for position in positions:
                if position.user_id not in user_positions:
                    user_positions[position.user_id] = []
                user_positions[position.user_id].append(position)
            
            for trade in trades:
                if trade.trade_time.date() == settlement_date:
                    if trade.user_id not in user_trades:
                        user_trades[trade.user_id] = []
                    user_trades[trade.user_id].append(trade)
            
            # 为每个用户执行结算
            for user_id, account in user_accounts.items():
                user_pos = user_positions.get(user_id, [])
                user_trd = user_trades.get(user_id, [])
                
                settlement_record = await self._settle_user_account(
                    user_id, settlement_date, account, user_pos, user_trd, market_data
                )
                
                settlement_results[user_id] = settlement_record
                
                # 保存结算记录
                await self._save_settlement_record(settlement_record)
            
            logger.info(f"日终结算完成: {settlement_date}, 处理用户数: {len(settlement_results)}")
            return settlement_results
            
        except Exception as e:
            logger.error(f"日终结算失败: {e}")
            raise
    
    async def _settle_user_account(
        self,
        user_id: str,
        settlement_date: date,
        account: Account,
        positions: List[Position],
        trades: List[Trade],
        market_data: Dict[str, Decimal]
    ) -> SettlementRecord:
        """结算用户账户"""
        try:
            settlement_id = f"STL_{settlement_date.strftime('%Y%m%d')}_{user_id}"
            
            # 计算盈亏
            total_pnl, realized_pnl, unrealized_pnl = await self._calculate_user_pnl(
                positions, trades, market_data
            )
            
            # 计算手续费
            commission = await self._calculate_commission(trades)
            
            # 计算其他费用
            fees = await self._calculate_fees(trades)
            
            # 计算保证金占用
            margin_used = await self._calculate_margin_used(positions, market_data)
            
            # 更新账户余额
            account.balance += realized_pnl - commission - fees
            account.margin = margin_used
            account.available = account.balance - margin_used
            
            # 创建结算记录
            settlement_record = SettlementRecord(
                settlement_id=settlement_id,
                user_id=user_id,
                settlement_date=settlement_date,
                total_pnl=total_pnl,
                realized_pnl=realized_pnl,
                unrealized_pnl=unrealized_pnl,
                commission=commission,
                fees=fees,
                margin_used=margin_used,
                available_funds=account.available
            )
            
            return settlement_record
            
        except Exception as e:
            logger.error(f"用户账户结算失败: {user_id}, {e}")
            raise
    
    async def _calculate_user_pnl(
        self,
        positions: List[Position],
        trades: List[Trade],
        market_data: Dict[str, Decimal]
    ) -> Tuple[Decimal, Decimal, Decimal]:
        """计算用户盈亏"""
        try:
            realized_pnl = Decimal("0")
            unrealized_pnl = Decimal("0")
            
            # 计算已实现盈亏（从交易记录）
            for trade in trades:
                if trade.offset.value == "CLOSE":
                    # 平仓交易产生已实现盈亏
                    if trade.direction.value == "LONG":
                        # 平多仓
                        realized_pnl += trade.get_amount()  # 简化计算
                    else:
                        # 平空仓
                        realized_pnl += trade.get_amount()  # 简化计算
            
            # 计算未实现盈亏（从持仓）
            for position in positions:
                if position.status == PositionStatus.ACTIVE:
                    current_price = market_data.get(position.symbol, Decimal("0"))
                    if current_price > 0:
                        position.calculate_pnl(current_price)
                        unrealized_pnl += position.unrealized_pnl
            
            total_pnl = realized_pnl + unrealized_pnl
            
            return total_pnl, realized_pnl, unrealized_pnl
            
        except Exception as e:
            logger.error(f"盈亏计算失败: {e}")
            return Decimal("0"), Decimal("0"), Decimal("0")
    
    async def _calculate_commission(self, trades: List[Trade]) -> Decimal:
        """计算手续费"""
        try:
            total_commission = Decimal("0")
            
            for trade in trades:
                # 根据交易品种获取费率
                product_type = self._get_product_type(trade.symbol)
                rate = self._commission_rates.get(product_type, Decimal("0.0003"))
                
                # 计算手续费
                commission = trade.get_amount() * rate
                total_commission += commission
            
            return total_commission
            
        except Exception as e:
            logger.error(f"手续费计算失败: {e}")
            return Decimal("0")
    
    async def _calculate_fees(self, trades: List[Trade]) -> Decimal:
        """计算其他费用（印花税、过户费等）"""
        try:
            total_fees = Decimal("0")
            
            for trade in trades:
                # 印花税（仅卖出收取）
                if trade.direction.value == "SHORT":
                    stamp_tax = trade.get_amount() * self._fee_rates.get("stamp_tax", Decimal("0"))
                    total_fees += stamp_tax
                
                # 过户费
                transfer_fee = trade.get_amount() * self._fee_rates.get("transfer_fee", Decimal("0"))
                total_fees += transfer_fee
            
            return total_fees
            
        except Exception as e:
            logger.error(f"费用计算失败: {e}")
            return Decimal("0")
    
    async def _calculate_margin_used(
        self,
        positions: List[Position],
        market_data: Dict[str, Decimal]
    ) -> Decimal:
        """计算保证金占用"""
        try:
            total_margin = Decimal("0")
            
            for position in positions:
                if position.status == PositionStatus.ACTIVE and position.total_volume > 0:
                    current_price = market_data.get(position.symbol, position.long_avg_price)
                    
                    # 计算持仓市值
                    position_value = position.total_volume * current_price
                    
                    # 保证金比例（根据品种不同）
                    margin_ratio = self._get_margin_ratio(position.symbol)
                    
                    # 计算保证金占用
                    margin = position_value * margin_ratio
                    total_margin += margin
            
            return total_margin
            
        except Exception as e:
            logger.error(f"保证金计算失败: {e}")
            return Decimal("0")
    
    def _get_product_type(self, symbol: str) -> str:
        """获取产品类型"""
        if symbol.endswith(('.SZ', '.SH')):
            return "stock"
        elif symbol.startswith('FOREX'):
            return "forex"
        else:
            return "futures"
    
    def _get_margin_ratio(self, symbol: str) -> Decimal:
        """获取保证金比例"""
        product_type = self._get_product_type(symbol)
        
        margin_ratios = {
            "stock": Decimal("1.0"),  # 股票全额
            "futures": Decimal("0.1"),  # 期货10%
            "forex": Decimal("0.01"),  # 外汇1%
        }
        
        return margin_ratios.get(product_type, Decimal("0.1"))
    
    async def _save_settlement_record(self, record: SettlementRecord) -> None:
        """保存结算记录"""
        try:
            user_id = record.user_id
            if user_id not in self._settlement_records:
                self._settlement_records[user_id] = []
            
            self._settlement_records[user_id].append(record)
            logger.info(f"结算记录已保存: {record.settlement_id}")
            
        except Exception as e:
            logger.error(f"保存结算记录失败: {e}")
            raise
    
    # ==================== 实时结算功能 ====================
    
    async def real_time_settlement(
        self,
        user_id: str,
        positions: List[Position],
        market_data: Dict[str, Decimal]
    ) -> Dict[str, Any]:
        """实时结算计算"""
        try:
            # 计算实时盈亏
            total_unrealized_pnl = Decimal("0")
            position_details = []
            
            for position in positions:
                if position.status == PositionStatus.ACTIVE and position.user_id == user_id:
                    current_price = market_data.get(position.symbol, Decimal("0"))
                    if current_price > 0:
                        position.calculate_pnl(current_price)
                        total_unrealized_pnl += position.unrealized_pnl
                        
                        position_details.append({
                            "symbol": position.symbol,
                            "volume": position.total_volume,
                            "avg_price": float(position.long_avg_price if position.is_long else position.short_avg_price),
                            "current_price": float(current_price),
                            "unrealized_pnl": float(position.unrealized_pnl),
                            "pnl_ratio": float(position.unrealized_pnl / (position.total_volume * current_price)) if position.total_volume > 0 else 0
                        })
            
            # 计算保证金占用
            margin_used = await self._calculate_margin_used(positions, market_data)
            
            return {
                "user_id": user_id,
                "total_unrealized_pnl": float(total_unrealized_pnl),
                "margin_used": float(margin_used),
                "position_count": len([p for p in positions if p.status == PositionStatus.ACTIVE and p.user_id == user_id]),
                "position_details": position_details,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"实时结算计算失败: {user_id}, {e}")
            return {"error": str(e)}
    
    # ==================== 报告生成 ====================
    
    async def generate_daily_report(
        self,
        user_id: str,
        report_date: date,
        account: Account,
        positions: List[Position],
        trades: List[Trade]
    ) -> DailyReport:
        """生成日报"""
        try:
            report_id = f"RPT_{report_date.strftime('%Y%m%d')}_{user_id}"
            
            # 获取当日开始和结束时的余额  
            opening_balance = account.balance - sum(
                trade.get_amount() for trade in trades 
                if trade.trade_time.date() == report_date
            )
            closing_balance = account.balance
            
            # 计算当日盈亏
            daily_pnl = closing_balance - opening_balance
            
            # 计算当日手续费
            daily_trades = [t for t in trades if t.trade_time.date() == report_date]
            total_commission = await self._calculate_commission(daily_trades)
            
            # 统计数据
            total_trades = len(daily_trades)
            active_positions = [p for p in positions if p.status == PositionStatus.ACTIVE and p.user_id == user_id]
            positions_count = len(active_positions)
            
            # 计算最大保证金占用（简化处理）
            max_margin_used = account.margin
            
            # 创建日报
            daily_report = DailyReport(
                report_id=report_id,
                user_id=user_id,
                report_date=report_date,
                opening_balance=opening_balance,
                closing_balance=closing_balance,
                daily_pnl=daily_pnl,
                total_commission=total_commission,
                total_trades=total_trades,
                positions_count=positions_count,
                max_margin_used=max_margin_used
            )
            
            # 保存日报
            await self._save_daily_report(daily_report)
            
            return daily_report
            
        except Exception as e:
            logger.error(f"日报生成失败: {user_id}, {report_date}, {e}")
            raise
    
    async def _save_daily_report(self, report: DailyReport) -> None:
        """保存日报"""
        try:
            user_id = report.user_id
            if user_id not in self._daily_reports:
                self._daily_reports[user_id] = []
            
            self._daily_reports[user_id].append(report)
            logger.info(f"日报已保存: {report.report_id}")
            
        except Exception as e:
            logger.error(f"保存日报失败: {e}")
            raise
    
    async def generate_monthly_report(
        self,
        user_id: str,
        year: int,
        month: int
    ) -> Dict[str, Any]:
        """生成月报"""
        try:
            # 获取月度日报
            user_reports = self._daily_reports.get(user_id, [])
            monthly_reports = [
                r for r in user_reports 
                if r.report_date.year == year and r.report_date.month == month
            ]
            
            if not monthly_reports:
                return {"error": "没有找到月度数据"}
            
            # 计算月度统计
            monthly_pnl = sum(r.daily_pnl for r in monthly_reports)
            total_commission = sum(r.total_commission for r in monthly_reports)
            total_trades = sum(r.total_trades for r in monthly_reports)
            avg_positions = sum(r.positions_count for r in monthly_reports) / len(monthly_reports)
            
            # 获取月初和月末余额
            opening_balance = monthly_reports[0].opening_balance if monthly_reports else Decimal("0")
            closing_balance = monthly_reports[-1].closing_balance if monthly_reports else Decimal("0")
            
            return {
                "user_id": user_id,
                "year": year,
                "month": month,
                "opening_balance": float(opening_balance),
                "closing_balance": float(closing_balance),
                "monthly_pnl": float(monthly_pnl),
                "total_commission": float(total_commission),
                "total_trades": total_trades,
                "trading_days": len(monthly_reports),
                "avg_positions": round(avg_positions, 2),
                "best_day": float(max(r.daily_pnl for r in monthly_reports)),
                "worst_day": float(min(r.daily_pnl for r in monthly_reports)),
                "daily_reports": [r.to_dict() for r in monthly_reports]
            }
            
        except Exception as e:
            logger.error(f"月报生成失败: {user_id}, {year}-{month}, {e}")
            return {"error": str(e)}
    
    # ==================== 查询接口 ====================
    
    async def get_settlement_records(
        self,
        user_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[SettlementRecord]:
        """获取结算记录"""
        try:
            user_records = self._settlement_records.get(user_id, [])
            
            if start_date or end_date:
                filtered_records = []
                for record in user_records:
                    if start_date and record.settlement_date < start_date:
                        continue
                    if end_date and record.settlement_date > end_date:
                        continue
                    filtered_records.append(record)
                return filtered_records
            
            return user_records
            
        except Exception as e:
            logger.error(f"获取结算记录失败: {user_id}, {e}")
            return []
    
    async def get_daily_reports(
        self,
        user_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[DailyReport]:
        """获取日报列表"""
        try:
            user_reports = self._daily_reports.get(user_id, [])
            
            if start_date or end_date:
                filtered_reports = []
                for report in user_reports:
                    if start_date and report.report_date < start_date:
                        continue
                    if end_date and report.report_date > end_date:
                        continue
                    filtered_reports.append(report)
                return filtered_reports
            
            return user_reports
            
        except Exception as e:
            logger.error(f"获取日报失败: {user_id}, {e}")
            return []
    
    # ==================== 配置管理 ====================
    
    async def set_commission_rate(self, product_type: str, rate: Decimal) -> None:
        """设置手续费率"""
        try:
            self._commission_rates[product_type] = rate
            logger.info(f"手续费率已更新: {product_type} = {rate}")
            
        except Exception as e:
            logger.error(f"设置手续费率失败: {e}")
            raise
    
    async def set_fee_rate(self, fee_type: str, rate: Decimal) -> None:
        """设置费用率"""
        try:
            self._fee_rates[fee_type] = rate
            logger.info(f"费用率已更新: {fee_type} = {rate}")
            
        except Exception as e:
            logger.error(f"设置费用率失败: {e}")
            raise
    
    async def get_settlement_summary(self, user_id: str) -> Dict[str, Any]:
        """获取结算摘要"""
        try:
            records = await self.get_settlement_records(user_id)
            
            if not records:
                return {"message": "没有结算记录"}
            
            # 计算汇总数据
            total_pnl = sum(r.total_pnl for r in records)
            total_commission = sum(r.commission for r in records)
            total_fees = sum(r.fees for r in records)
            
            latest_record = records[-1] if records else None
            
            return {
                "user_id": user_id,
                "total_records": len(records),
                "total_pnl": float(total_pnl),
                "total_commission": float(total_commission),
                "total_fees": float(total_fees),
                "latest_settlement": latest_record.to_dict() if latest_record else None,
                "first_settlement_date": records[0].settlement_date.isoformat() if records else None,
                "last_settlement_date": records[-1].settlement_date.isoformat() if records else None
            }
            
        except Exception as e:
            logger.error(f"获取结算摘要失败: {user_id}, {e}")
            return {"error": str(e)}
