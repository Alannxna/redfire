"""
Advanced Settlement Service
===========================

高级结算服务，提供完整的日终结算流程、多种报告生成、批量处理等高级功能。
"""

import asyncio
import logging
import uuid
from typing import Dict, List, Optional, Any, Tuple, Set
from datetime import datetime, timedelta, date
from decimal import Decimal, ROUND_HALF_UP
from dataclasses import dataclass, field
from collections import defaultdict
from enum import Enum

from .settlement_service import SettlementService, SettlementRecord, DailyReport
from ..entities.position_entity import Position
from ..entities.account_entity import Account
from ..entities.order_entity import Order
from ..entities.trade_entity import Trade
from ..enums import OrderStatus, PositionStatus, Direction, Product

logger = logging.getLogger(__name__)


class SettlementStatus(Enum):
    """结算状态"""
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class ReportFormat(Enum):
    """报告格式"""
    JSON = "JSON"
    CSV = "CSV"
    EXCEL = "EXCEL"
    PDF = "PDF"


@dataclass
class SettlementBatch:
    """结算批次"""
    batch_id: str
    settlement_date: date
    status: SettlementStatus = SettlementStatus.PENDING
    user_ids: List[str] = field(default_factory=list)
    total_users: int = 0
    processed_users: int = 0
    failed_users: List[str] = field(default_factory=list)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "batch_id": self.batch_id,
            "settlement_date": self.settlement_date.isoformat(),
            "status": self.status.value,
            "user_ids": self.user_ids,
            "total_users": self.total_users,
            "processed_users": self.processed_users,
            "failed_users": self.failed_users,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat(),
            "progress_percent": (self.processed_users / self.total_users * 100) if self.total_users > 0 else 0
        }


@dataclass
class AdvancedSettlementRecord(SettlementRecord):
    """增强结算记录"""
    # 基础信息继承自SettlementRecord
    
    # 扩展字段
    total_commission: Decimal = Decimal("0")
    total_fees: Decimal = Decimal("0")
    pnl_by_product: Dict[str, Decimal] = field(default_factory=dict)
    commission_by_product: Dict[str, Decimal] = field(default_factory=dict)
    fees_by_product: Dict[str, Decimal] = field(default_factory=dict)
    trade_count_by_product: Dict[str, int] = field(default_factory=dict)
    position_summary: Dict[str, Any] = field(default_factory=dict)
    risk_metrics: Dict[str, Any] = field(default_factory=dict)
    settlement_notes: Optional[str] = None
    batch_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        base_dict = super().to_dict()
        base_dict.update({
            "total_commission": float(self.total_commission),
            "total_fees": float(self.total_fees),
            "pnl_by_product": {k: float(v) for k, v in self.pnl_by_product.items()},
            "commission_by_product": {k: float(v) for k, v in self.commission_by_product.items()},
            "fees_by_product": {k: float(v) for k, v in self.fees_by_product.items()},
            "trade_count_by_product": self.trade_count_by_product,
            "position_summary": self.position_summary,
            "risk_metrics": self.risk_metrics,
            "settlement_notes": self.settlement_notes,
            "batch_id": self.batch_id
        })
        return base_dict


@dataclass
class SettlementSummary:
    """结算汇总"""
    summary_id: str
    period_type: str  # daily, weekly, monthly, yearly
    start_date: date
    end_date: date
    total_users: int
    total_pnl: Decimal = Decimal("0")
    total_commission: Decimal = Decimal("0")
    total_fees: Decimal = Decimal("0")
    net_pnl: Decimal = Decimal("0")
    avg_pnl_per_user: Decimal = Decimal("0")
    profitable_users: int = 0
    loss_users: int = 0
    total_trades: int = 0
    product_breakdown: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "summary_id": self.summary_id,
            "period_type": self.period_type,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "total_users": self.total_users,
            "total_pnl": float(self.total_pnl),
            "total_commission": float(self.total_commission),
            "total_fees": float(self.total_fees),
            "net_pnl": float(self.net_pnl),
            "avg_pnl_per_user": float(self.avg_pnl_per_user),
            "profitable_users": self.profitable_users,
            "loss_users": self.loss_users,
            "total_trades": self.total_trades,
            "product_breakdown": self.product_breakdown,
            "created_at": self.created_at.isoformat()
        }


class AdvancedSettlementService(SettlementService):
    """高级结算服务"""
    
    def __init__(self):
        super().__init__()
        
        # 高级功能存储
        self._settlement_batches: Dict[str, SettlementBatch] = {}
        self._advanced_records: Dict[str, AdvancedSettlementRecord] = {}
        self._settlement_summaries: Dict[str, SettlementSummary] = {}
        
        # 批处理配置
        self._batch_size = 50  # 批处理大小
        self._max_concurrent_settlements = 10  # 最大并发结算数
        self._settlement_timeout = 300  # 结算超时时间（秒）
        
        # 风险监控配置
        self._risk_thresholds = {
            "max_daily_loss": Decimal("-50000"),  # 最大日亏损
            "max_position_concentration": 0.3,  # 最大持仓集中度
            "max_leverage": 10.0,  # 最大杠杆比例
            "min_margin_ratio": 0.15  # 最小保证金比例
        }
        
        # 报告生成器
        self._report_generators = {}
        
    # ==================== 批量结算功能 ====================
    
    async def create_settlement_batch(
        self,
        settlement_date: date,
        user_ids: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> str:
        """创建结算批次"""
        try:
            batch_id = str(uuid.uuid4())
            
            # 确定需要结算的用户
            if user_ids is None:
                # 获取所有活跃用户
                user_ids = await self._get_active_users(settlement_date, filters)
            
            batch = SettlementBatch(
                batch_id=batch_id,
                settlement_date=settlement_date,
                user_ids=user_ids,
                total_users=len(user_ids)
            )
            
            self._settlement_batches[batch_id] = batch
            
            logger.info(f"创建结算批次: {batch_id}, 用户数: {len(user_ids)}")
            
            return batch_id
            
        except Exception as e:
            logger.error(f"创建结算批次失败: {e}")
            raise
    
    async def process_settlement_batch(self, batch_id: str) -> Dict[str, Any]:
        """处理结算批次"""
        try:
            if batch_id not in self._settlement_batches:
                raise ValueError(f"结算批次不存在: {batch_id}")
            
            batch = self._settlement_batches[batch_id]
            
            if batch.status != SettlementStatus.PENDING:
                raise ValueError(f"批次状态不允许处理: {batch.status}")
            
            # 更新批次状态
            batch.status = SettlementStatus.PROCESSING
            batch.start_time = datetime.now()
            
            logger.info(f"开始处理结算批次: {batch_id}")
            
            # 分批处理用户
            user_batches = [
                batch.user_ids[i:i + self._batch_size]
                for i in range(0, len(batch.user_ids), self._batch_size)
            ]
            
            # 并发处理批次
            semaphore = asyncio.Semaphore(self._max_concurrent_settlements)
            
            async def process_user_batch(user_batch: List[str]):
                async with semaphore:
                    return await self._process_user_batch(batch.settlement_date, user_batch, batch_id)
            
            # 执行批处理
            results = await asyncio.gather(
                *[process_user_batch(user_batch) for user_batch in user_batches],
                return_exceptions=True
            )
            
            # 汇总结果
            total_processed = 0
            failed_users = []
            
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"批处理异常: {result}")
                    failed_users.extend(batch.user_ids)  # 假设整批失败
                else:
                    total_processed += result["processed"]
                    failed_users.extend(result["failed"])
            
            # 更新批次状态
            batch.processed_users = total_processed
            batch.failed_users = failed_users
            batch.end_time = datetime.now()
            
            if failed_users:
                batch.status = SettlementStatus.FAILED if total_processed == 0 else SettlementStatus.COMPLETED
                batch.error_message = f"部分用户处理失败: {len(failed_users)} 个"
            else:
                batch.status = SettlementStatus.COMPLETED
            
            duration = (batch.end_time - batch.start_time).total_seconds()
            
            logger.info(f"结算批次处理完成: {batch_id}, 耗时: {duration:.2f}秒")
            
            return {
                "batch_id": batch_id,
                "status": batch.status.value,
                "total_users": batch.total_users,
                "processed_users": batch.processed_users,
                "failed_users": len(batch.failed_users),
                "duration_seconds": duration,
                "throughput": batch.processed_users / duration if duration > 0 else 0
            }
            
        except Exception as e:
            # 更新批次状态为失败
            if batch_id in self._settlement_batches:
                batch = self._settlement_batches[batch_id]
                batch.status = SettlementStatus.FAILED
                batch.error_message = str(e)
                batch.end_time = datetime.now()
            
            logger.error(f"处理结算批次失败: {e}")
            raise
    
    async def get_batch_status(self, batch_id: str) -> Dict[str, Any]:
        """获取批次状态"""
        try:
            if batch_id not in self._settlement_batches:
                raise ValueError(f"结算批次不存在: {batch_id}")
            
            batch = self._settlement_batches[batch_id]
            return batch.to_dict()
            
        except Exception as e:
            logger.error(f"获取批次状态失败: {e}")
            raise
    
    async def cancel_settlement_batch(self, batch_id: str) -> bool:
        """取消结算批次"""
        try:
            if batch_id not in self._settlement_batches:
                raise ValueError(f"结算批次不存在: {batch_id}")
            
            batch = self._settlement_batches[batch_id]
            
            if batch.status in [SettlementStatus.COMPLETED, SettlementStatus.FAILED]:
                raise ValueError(f"无法取消已完成的批次: {batch.status}")
            
            batch.status = SettlementStatus.CANCELLED
            batch.end_time = datetime.now()
            
            logger.info(f"结算批次已取消: {batch_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"取消结算批次失败: {e}")
            return False
    
    # ==================== 增强结算功能 ====================
    
    async def advanced_daily_settlement(
        self,
        user_id: str,
        settlement_date: date,
        include_risk_analysis: bool = True,
        include_performance_metrics: bool = True
    ) -> AdvancedSettlementRecord:
        """高级日终结算"""
        try:
            # 执行基础结算
            basic_record = await self.daily_settlement(user_id, settlement_date)
            
            # 获取详细交易数据
            trades = await self._get_user_trades(user_id, settlement_date)
            positions = await self._get_user_positions(user_id, settlement_date)
            account = await self._get_user_account(user_id)
            
            # 创建高级结算记录
            advanced_record = AdvancedSettlementRecord(
                settlement_id=basic_record.settlement_id,
                user_id=user_id,
                settlement_date=settlement_date,
                total_pnl=basic_record.total_pnl,
                realized_pnl=basic_record.realized_pnl,
                unrealized_pnl=basic_record.unrealized_pnl,
                commission=basic_record.commission,
                fees=basic_record.fees,
                margin_used=basic_record.margin_used,
                available_funds=basic_record.available_funds
            )
            
            # 按产品分类计算
            await self._calculate_product_breakdown(advanced_record, trades, positions)
            
            # 计算持仓汇总
            advanced_record.position_summary = await self._calculate_position_summary(positions)
            
            # 风险分析
            if include_risk_analysis:
                advanced_record.risk_metrics = await self._calculate_risk_metrics(
                    user_id, positions, account, trades
                )
            
            # 保存高级记录
            self._advanced_records[advanced_record.settlement_id] = advanced_record
            
            logger.info(f"高级日终结算完成: {user_id}, {settlement_date}")
            
            return advanced_record
            
        except Exception as e:
            logger.error(f"高级日终结算失败: {e}")
            raise
    
    async def _calculate_product_breakdown(
        self,
        record: AdvancedSettlementRecord,
        trades: List[Trade],
        positions: List[Position]
    ):
        """计算产品分类明细"""
        try:
            # 按产品类型分组
            for trade in trades:
                product_type = self._get_product_type(trade.symbol)
                
                # 计算盈亏
                if product_type not in record.pnl_by_product:
                    record.pnl_by_product[product_type] = Decimal("0")
                    record.commission_by_product[product_type] = Decimal("0")
                    record.fees_by_product[product_type] = Decimal("0")
                    record.trade_count_by_product[product_type] = 0
                
                # 累计数据
                record.pnl_by_product[product_type] += trade.total_amount
                record.commission_by_product[product_type] += trade.commission
                record.fees_by_product[product_type] += trade.fee
                record.trade_count_by_product[product_type] += 1
            
            # 计算总计
            record.total_commission = sum(record.commission_by_product.values())
            record.total_fees = sum(record.fees_by_product.values())
            
        except Exception as e:
            logger.error(f"计算产品分类明细失败: {e}")
            raise
    
    async def _calculate_position_summary(self, positions: List[Position]) -> Dict[str, Any]:
        """计算持仓汇总"""
        try:
            summary = {
                "total_positions": len(positions),
                "long_positions": 0,
                "short_positions": 0,
                "total_market_value": Decimal("0"),
                "total_unrealized_pnl": Decimal("0"),
                "largest_position": None,
                "product_distribution": defaultdict(int),
                "concentration_risk": {}
            }
            
            market_values = []
            
            for position in positions:
                if position.direction == Direction.LONG:
                    summary["long_positions"] += 1
                else:
                    summary["short_positions"] += 1
                
                market_value = position.volume * position.avg_price
                summary["total_market_value"] += market_value
                summary["total_unrealized_pnl"] += position.unrealized_pnl
                
                market_values.append((position.symbol, float(market_value)))
                
                # 产品分布
                product_type = self._get_product_type(position.symbol)
                summary["product_distribution"][product_type] += 1
            
            # 找出最大持仓
            if market_values:
                largest = max(market_values, key=lambda x: x[1])
                summary["largest_position"] = {
                    "symbol": largest[0],
                    "market_value": largest[1]
                }
                
                # 计算集中度风险
                total_value = float(summary["total_market_value"])
                if total_value > 0:
                    concentration = largest[1] / total_value
                    summary["concentration_risk"] = {
                        "largest_position_ratio": concentration,
                        "is_concentrated": concentration > self._risk_thresholds["max_position_concentration"]
                    }
            
            # 转换为可序列化格式
            summary["total_market_value"] = float(summary["total_market_value"])
            summary["total_unrealized_pnl"] = float(summary["total_unrealized_pnl"])
            summary["product_distribution"] = dict(summary["product_distribution"])
            
            return summary
            
        except Exception as e:
            logger.error(f"计算持仓汇总失败: {e}")
            return {}
    
    async def _calculate_risk_metrics(
        self,
        user_id: str,
        positions: List[Position],
        account: Account,
        trades: List[Trade]
    ) -> Dict[str, Any]:
        """计算风险指标"""
        try:
            risk_metrics = {
                "leverage_ratio": 0.0,
                "margin_ratio": 0.0,
                "concentration_risk": 0.0,
                "daily_var": 0.0,
                "max_drawdown": 0.0,
                "volatility": 0.0,
                "risk_alerts": []
            }
            
            # 计算杠杆比例
            total_market_value = sum(pos.volume * pos.avg_price for pos in positions)
            if account.balance > 0:
                risk_metrics["leverage_ratio"] = float(total_market_value / account.balance)
            
            # 计算保证金比例
            if account.balance > 0:
                risk_metrics["margin_ratio"] = float(account.available / account.balance)
            
            # 计算集中度风险
            if total_market_value > 0:
                max_position_value = max((pos.volume * pos.avg_price for pos in positions), default=Decimal("0"))
                risk_metrics["concentration_risk"] = float(max_position_value / total_market_value)
            
            # 计算每日VaR（简化版）
            daily_pnls = [float(trade.total_amount) for trade in trades]
            if len(daily_pnls) > 1:
                import statistics
                risk_metrics["volatility"] = statistics.stdev(daily_pnls)
                # 简化的VaR计算（95%置信度）
                risk_metrics["daily_var"] = statistics.quantile(daily_pnls, 0.05) if len(daily_pnls) >= 20 else min(daily_pnls, default=0)
            
            # 生成风险告警
            alerts = []
            
            if risk_metrics["leverage_ratio"] > self._risk_thresholds["max_leverage"]:
                alerts.append({
                    "type": "HIGH_LEVERAGE",
                    "message": f"杠杆比例过高: {risk_metrics['leverage_ratio']:.2f}",
                    "severity": "HIGH"
                })
            
            if risk_metrics["margin_ratio"] < self._risk_thresholds["min_margin_ratio"]:
                alerts.append({
                    "type": "LOW_MARGIN",
                    "message": f"保证金比例过低: {risk_metrics['margin_ratio']:.2%}",
                    "severity": "CRITICAL"
                })
            
            if risk_metrics["concentration_risk"] > self._risk_thresholds["max_position_concentration"]:
                alerts.append({
                    "type": "CONCENTRATION_RISK",
                    "message": f"持仓集中度过高: {risk_metrics['concentration_risk']:.2%}",
                    "severity": "MEDIUM"
                })
            
            # 检查每日亏损
            daily_pnl = sum(float(trade.total_amount) for trade in trades)
            if daily_pnl < float(self._risk_thresholds["max_daily_loss"]):
                alerts.append({
                    "type": "DAILY_LOSS_LIMIT",
                    "message": f"日亏损超过限额: {daily_pnl:.2f}",
                    "severity": "CRITICAL"
                })
            
            risk_metrics["risk_alerts"] = alerts
            
            return risk_metrics
            
        except Exception as e:
            logger.error(f"计算风险指标失败: {e}")
            return {}
    
    # ==================== 高级报告生成 ====================
    
    async def generate_annual_report(
        self,
        user_id: str,
        year: int,
        format: ReportFormat = ReportFormat.JSON
    ) -> Dict[str, Any]:
        """生成年度结算报告"""
        try:
            # 获取年度所有记录
            start_date = date(year, 1, 1)
            end_date = date(year + 1, 1, 1)
            
            annual_records = [
                record for record in self._advanced_records.values()
                if (record.user_id == user_id and 
                    start_date <= record.settlement_date < end_date)
            ]
            
            if not annual_records:
                return {
                    "year": year,
                    "user_id": user_id,
                    "total_days": 0,
                    "summary": {},
                    "monthly_breakdown": {},
                    "performance_metrics": {}
                }
            
            # 年度汇总计算
            total_pnl = sum(record.total_pnl for record in annual_records)
            total_commission = sum(record.total_commission for record in annual_records)
            total_fees = sum(record.total_fees for record in annual_records)
            net_pnl = total_pnl - total_commission - total_fees
            
            # 月度分解
            monthly_breakdown = await self._calculate_monthly_breakdown(annual_records, year)
            
            # 绩效指标计算
            performance_metrics = await self._calculate_performance_metrics(annual_records)
            
            # 风险分析
            risk_analysis = await self._calculate_annual_risk_analysis(annual_records)
            
            # 产品分析
            product_analysis = await self._calculate_product_performance(annual_records)
            
            report = {
                "year": year,
                "user_id": user_id,
                "total_days": len(annual_records),
                "summary": {
                    "total_pnl": float(total_pnl),
                    "total_commission": float(total_commission),
                    "total_fees": float(total_fees),
                    "net_pnl": float(net_pnl),
                    "cost_ratio": float((total_commission + total_fees) / total_pnl) if total_pnl != 0 else 0,
                    "average_daily_pnl": float(net_pnl / len(annual_records)) if annual_records else 0
                },
                "monthly_breakdown": monthly_breakdown,
                "performance_metrics": performance_metrics,
                "risk_analysis": risk_analysis,
                "product_analysis": product_analysis,
                "generated_at": datetime.now().isoformat(),
                "format": format.value
            }
            
            # 根据格式处理报告
            if format == ReportFormat.CSV:
                report["csv_data"] = await self._generate_csv_data(annual_records)
            elif format == ReportFormat.EXCEL:
                report["excel_file"] = await self._generate_excel_file(annual_records, report)
            elif format == ReportFormat.PDF:
                report["pdf_file"] = await self._generate_pdf_file(annual_records, report)
            
            return report
            
        except Exception as e:
            logger.error(f"生成年度报告失败: {e}")
            raise
    
    async def generate_custom_report(
        self,
        user_id: str,
        start_date: date,
        end_date: date,
        report_type: str = "comprehensive",
        filters: Optional[Dict[str, Any]] = None,
        format: ReportFormat = ReportFormat.JSON
    ) -> Dict[str, Any]:
        """生成自定义期间报告"""
        try:
            # 获取指定期间的记录
            period_records = [
                record for record in self._advanced_records.values()
                if (record.user_id == user_id and 
                    start_date <= record.settlement_date <= end_date)
            ]
            
            # 应用筛选器
            if filters:
                period_records = await self._apply_filters(period_records, filters)
            
            if not period_records:
                return {
                    "period": f"{start_date} to {end_date}",
                    "user_id": user_id,
                    "report_type": report_type,
                    "total_days": 0,
                    "data": {}
                }
            
            # 根据报告类型生成不同内容
            if report_type == "comprehensive":
                data = await self._generate_comprehensive_report_data(period_records)
            elif report_type == "summary":
                data = await self._generate_summary_report_data(period_records)
            elif report_type == "risk":
                data = await self._generate_risk_report_data(period_records)
            elif report_type == "performance":
                data = await self._generate_performance_report_data(period_records)
            elif report_type == "product":
                data = await self._generate_product_report_data(period_records)
            else:
                data = {"error": f"不支持的报告类型: {report_type}"}
            
            report = {
                "period": f"{start_date} to {end_date}",
                "user_id": user_id,
                "report_type": report_type,
                "total_days": len(period_records),
                "filters_applied": filters or {},
                "data": data,
                "generated_at": datetime.now().isoformat(),
                "format": format.value
            }
            
            return report
            
        except Exception as e:
            logger.error(f"生成自定义报告失败: {e}")
            raise
    
    async def generate_settlement_summary(
        self,
        period_type: str,  # daily, weekly, monthly, yearly
        start_date: date,
        end_date: Optional[date] = None
    ) -> SettlementSummary:
        """生成结算汇总"""
        try:
            if end_date is None:
                end_date = start_date
            
            summary_id = str(uuid.uuid4())
            
            # 获取期间内所有结算记录
            period_records = [
                record for record in self._advanced_records.values()
                if start_date <= record.settlement_date <= end_date
            ]
            
            # 统计数据
            user_ids = set(record.user_id for record in period_records)
            total_pnl = sum(record.total_pnl for record in period_records)
            total_commission = sum(record.total_commission for record in period_records)
            total_fees = sum(record.total_fees for record in period_records)
            net_pnl = total_pnl - total_commission - total_fees
            
            # 用户盈亏统计
            user_pnl = defaultdict(Decimal)
            for record in period_records:
                user_pnl[record.user_id] += record.total_pnl - record.total_commission - record.total_fees
            
            profitable_users = len([pnl for pnl in user_pnl.values() if pnl > 0])
            loss_users = len([pnl for pnl in user_pnl.values() if pnl < 0])
            
            # 交易统计
            total_trades = sum(
                sum(record.trade_count_by_product.values()) 
                for record in period_records
            )
            
            # 产品分解
            product_breakdown = await self._calculate_summary_product_breakdown(period_records)
            
            summary = SettlementSummary(
                summary_id=summary_id,
                period_type=period_type,
                start_date=start_date,
                end_date=end_date,
                total_users=len(user_ids),
                total_pnl=total_pnl,
                total_commission=total_commission,
                total_fees=total_fees,
                net_pnl=net_pnl,
                avg_pnl_per_user=net_pnl / len(user_ids) if user_ids else Decimal("0"),
                profitable_users=profitable_users,
                loss_users=loss_users,
                total_trades=total_trades,
                product_breakdown=product_breakdown
            )
            
            self._settlement_summaries[summary_id] = summary
            
            logger.info(f"结算汇总生成完成: {summary_id}")
            
            return summary
            
        except Exception as e:
            logger.error(f"生成结算汇总失败: {e}")
            raise
    
    # ==================== 私有辅助方法 ====================
    
    async def _get_active_users(
        self,
        settlement_date: date,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """获取活跃用户列表"""
        # 模拟获取活跃用户
        # 实际实现应该从数据库查询
        active_users = ["user_001", "user_002", "user_003", "user_004", "user_005"]
        
        if filters:
            # 应用筛选器
            if "min_balance" in filters:
                # 筛选最小余额
                pass
            if "product_types" in filters:
                # 筛选产品类型
                pass
        
        return active_users
    
    async def _process_user_batch(
        self,
        settlement_date: date,
        user_ids: List[str],
        batch_id: str
    ) -> Dict[str, Any]:
        """处理用户批次"""
        try:
            processed = 0
            failed = []
            
            for user_id in user_ids:
                try:
                    # 执行高级结算
                    record = await self.advanced_daily_settlement(user_id, settlement_date)
                    record.batch_id = batch_id
                    processed += 1
                    
                except Exception as e:
                    logger.error(f"用户结算失败: {user_id}, {e}")
                    failed.append(user_id)
            
            return {
                "processed": processed,
                "failed": failed
            }
            
        except Exception as e:
            logger.error(f"处理用户批次失败: {e}")
            return {
                "processed": 0,
                "failed": user_ids
            }
    
    async def _get_user_trades(self, user_id: str, settlement_date: date) -> List[Trade]:
        """获取用户交易记录"""
        # 模拟数据，实际应该从数据库查询
        from decimal import Decimal
        from datetime import datetime
        
        trades = [
            Trade(
                trade_id="trade_001",
                order_id="order_001",
                user_id=user_id,
                symbol="AAPL",
                direction=Direction.LONG,
                volume=100,
                price=Decimal("150.50"),
                trade_time=datetime.now(),
                commission=Decimal("5.00"),
                fee=Decimal("1.00")
            )
        ]
        return trades
    
    async def _get_user_positions(self, user_id: str, settlement_date: date) -> List[Position]:
        """获取用户持仓"""
        # 模拟数据
        positions = [
            Position(
                position_id="pos_001",
                user_id=user_id,
                symbol="AAPL",
                direction=Direction.LONG,
                volume=100,
                avg_price=Decimal("150.00"),
                current_price=Decimal("152.00"),
                unrealized_pnl=Decimal("200.00")
            )
        ]
        return positions
    
    async def _get_user_account(self, user_id: str) -> Account:
        """获取用户账户"""
        # 模拟数据
        return Account(
            account_id="acc_001",
            user_id=user_id,
            balance=Decimal("100000.00"),
            available=Decimal("80000.00"),
            frozen=Decimal("20000.00")
        )
    
    def _get_product_type(self, symbol: str) -> str:
        """获取产品类型"""
        # 简化实现，实际应该有完整的产品映射表
        if symbol.startswith(("AAPL", "GOOGL", "MSFT", "TSLA")):
            return "STOCK"
        elif symbol.startswith(("IF", "IH", "IC")):
            return "INDEX_FUTURE"
        elif symbol.startswith(("CU", "AL", "ZN")):
            return "COMMODITY_FUTURE"
        else:
            return "OTHER"
    
    async def _calculate_monthly_breakdown(
        self,
        annual_records: List[AdvancedSettlementRecord],
        year: int
    ) -> Dict[str, Any]:
        """计算月度分解"""
        monthly_breakdown = {}
        
        for month in range(1, 13):
            month_records = [
                record for record in annual_records
                if record.settlement_date.month == month
            ]
            
            if month_records:
                month_pnl = sum(record.total_pnl for record in month_records)
                month_commission = sum(record.total_commission for record in month_records)
                month_fees = sum(record.total_fees for record in month_records)
                month_net_pnl = month_pnl - month_commission - month_fees
                
                monthly_breakdown[f"{month:02d}"] = {
                    "trading_days": len(month_records),
                    "pnl": float(month_pnl),
                    "commission": float(month_commission),
                    "fees": float(month_fees),
                    "net_pnl": float(month_net_pnl),
                    "win_days": len([r for r in month_records if r.total_pnl > 0]),
                    "loss_days": len([r for r in month_records if r.total_pnl < 0]),
                    "avg_daily_pnl": float(month_net_pnl / len(month_records)) if month_records else 0
                }
        
        return monthly_breakdown
    
    async def _calculate_performance_metrics(
        self,
        records: List[AdvancedSettlementRecord]
    ) -> Dict[str, Any]:
        """计算绩效指标"""
        if not records:
            return {}
        
        daily_net_pnls = [
            float(record.total_pnl - record.total_commission - record.total_fees)
            for record in records
        ]
        
        import statistics
        
        # 基础统计
        total_return = sum(daily_net_pnls)
        avg_return = statistics.mean(daily_net_pnls)
        return_std = statistics.stdev(daily_net_pnls) if len(daily_net_pnls) > 1 else 0
        
        # 夏普比率（年化）
        # 假设无风险利率为3%
        risk_free_rate = 0.03 / 252  # 日化无风险利率
        excess_returns = [r - risk_free_rate for r in daily_net_pnls]
        sharpe_ratio = statistics.mean(excess_returns) / statistics.stdev(excess_returns) if len(excess_returns) > 1 and statistics.stdev(excess_returns) > 0 else 0
        sharpe_ratio_annualized = sharpe_ratio * (252 ** 0.5)  # 年化
        
        # 最大回撤
        cumulative_pnl = 0
        max_drawdown = 0
        peak = 0
        
        for daily_pnl in daily_net_pnls:
            cumulative_pnl += daily_pnl
            if cumulative_pnl > peak:
                peak = cumulative_pnl
            drawdown = peak - cumulative_pnl
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        
        # 胜率
        win_rate = len([p for p in daily_net_pnls if p > 0]) / len(daily_net_pnls)
        
        # 盈利因子
        profits = [p for p in daily_net_pnls if p > 0]
        losses = [abs(p) for p in daily_net_pnls if p < 0]
        profit_factor = sum(profits) / sum(losses) if losses else float('inf') if profits else 0
        
        return {
            "total_return": total_return,
            "annualized_return": total_return * 252 / len(records),
            "average_daily_return": avg_return,
            "volatility": return_std,
            "annualized_volatility": return_std * (252 ** 0.5),
            "sharpe_ratio": sharpe_ratio_annualized,
            "max_drawdown": max_drawdown,
            "win_rate": win_rate,
            "profit_factor": profit_factor,
            "max_daily_profit": max(daily_net_pnls),
            "max_daily_loss": min(daily_net_pnls),
            "trading_days": len(records),
            "profitable_days": len(profits),
            "loss_days": len(losses)
        }
    
    async def _calculate_annual_risk_analysis(
        self,
        records: List[AdvancedSettlementRecord]
    ) -> Dict[str, Any]:
        """计算年度风险分析"""
        risk_alerts_count = defaultdict(int)
        leverage_history = []
        margin_history = []
        
        for record in records:
            # 统计风险告警
            if record.risk_metrics and "risk_alerts" in record.risk_metrics:
                for alert in record.risk_metrics["risk_alerts"]:
                    risk_alerts_count[alert["type"]] += 1
            
            # 收集历史数据
            if record.risk_metrics:
                if "leverage_ratio" in record.risk_metrics:
                    leverage_history.append(record.risk_metrics["leverage_ratio"])
                if "margin_ratio" in record.risk_metrics:
                    margin_history.append(record.risk_metrics["margin_ratio"])
        
        return {
            "total_risk_alerts": sum(risk_alerts_count.values()),
            "alert_breakdown": dict(risk_alerts_count),
            "average_leverage": statistics.mean(leverage_history) if leverage_history else 0,
            "max_leverage": max(leverage_history) if leverage_history else 0,
            "average_margin_ratio": statistics.mean(margin_history) if margin_history else 0,
            "min_margin_ratio": min(margin_history) if margin_history else 0,
            "risk_score": self._calculate_risk_score(risk_alerts_count, leverage_history, margin_history)
        }
    
    def _calculate_risk_score(
        self,
        alerts: Dict[str, int],
        leverage_history: List[float],
        margin_history: List[float]
    ) -> float:
        """计算风险评分 (0-100, 分数越高风险越大)"""
        score = 0
        
        # 告警权重
        alert_weights = {
            "HIGH_LEVERAGE": 20,
            "LOW_MARGIN": 25,
            "CONCENTRATION_RISK": 15,
            "DAILY_LOSS_LIMIT": 30
        }
        
        # 根据告警计算分数
        for alert_type, count in alerts.items():
            weight = alert_weights.get(alert_type, 10)
            score += min(count * weight, 50)  # 单项最高50分
        
        # 根据杠杆历史计算分数
        if leverage_history:
            avg_leverage = statistics.mean(leverage_history)
            max_leverage = max(leverage_history)
            
            if avg_leverage > 5:
                score += 15
            if max_leverage > 10:
                score += 20
        
        # 根据保证金历史计算分数
        if margin_history:
            min_margin = min(margin_history)
            if min_margin < 0.1:
                score += 25
            elif min_margin < 0.2:
                score += 15
        
        return min(score, 100)  # 最高100分
    
    # 其他辅助方法...
    async def _calculate_product_performance(self, records: List[AdvancedSettlementRecord]) -> Dict[str, Any]:
        """计算产品绩效"""
        product_stats = defaultdict(lambda: {
            "total_pnl": Decimal("0"),
            "total_commission": Decimal("0"),
            "total_fees": Decimal("0"),
            "trade_count": 0,
            "trading_days": 0
        })
        
        for record in records:
            for product_type, pnl in record.pnl_by_product.items():
                stats = product_stats[product_type]
                stats["total_pnl"] += pnl
                stats["total_commission"] += record.commission_by_product.get(product_type, Decimal("0"))
                stats["total_fees"] += record.fees_by_product.get(product_type, Decimal("0"))
                stats["trade_count"] += record.trade_count_by_product.get(product_type, 0)
                stats["trading_days"] += 1
        
        result = {}
        for product_type, stats in product_stats.items():
            net_pnl = stats["total_pnl"] - stats["total_commission"] - stats["total_fees"]
            result[product_type] = {
                "total_pnl": float(stats["total_pnl"]),
                "total_commission": float(stats["total_commission"]),
                "total_fees": float(stats["total_fees"]),
                "net_pnl": float(net_pnl),
                "trade_count": stats["trade_count"],
                "trading_days": stats["trading_days"],
                "avg_pnl_per_trade": float(stats["total_pnl"] / stats["trade_count"]) if stats["trade_count"] > 0 else 0,
                "roi": float(net_pnl / (stats["total_commission"] + stats["total_fees"])) if (stats["total_commission"] + stats["total_fees"]) > 0 else 0
            }
        
        return result
    
    async def _apply_filters(
        self,
        records: List[AdvancedSettlementRecord],
        filters: Dict[str, Any]
    ) -> List[AdvancedSettlementRecord]:
        """应用筛选器"""
        filtered_records = records
        
        if "min_pnl" in filters:
            min_pnl = Decimal(str(filters["min_pnl"]))
            filtered_records = [r for r in filtered_records if r.total_pnl >= min_pnl]
        
        if "max_pnl" in filters:
            max_pnl = Decimal(str(filters["max_pnl"]))
            filtered_records = [r for r in filtered_records if r.total_pnl <= max_pnl]
        
        if "product_types" in filters:
            product_types = set(filters["product_types"])
            filtered_records = [
                r for r in filtered_records
                if any(product in r.pnl_by_product for product in product_types)
            ]
        
        if "has_risk_alerts" in filters and filters["has_risk_alerts"]:
            filtered_records = [
                r for r in filtered_records
                if (r.risk_metrics and 
                    r.risk_metrics.get("risk_alerts") and 
                    len(r.risk_metrics["risk_alerts"]) > 0)
            ]
        
        return filtered_records
    
    # 报告生成辅助方法
    async def _generate_comprehensive_report_data(self, records: List[AdvancedSettlementRecord]) -> Dict[str, Any]:
        """生成综合报告数据"""
        return {
            "summary": await self._generate_summary_report_data(records),
            "performance": await self._calculate_performance_metrics(records),
            "risk_analysis": await self._calculate_annual_risk_analysis(records),
            "product_analysis": await self._calculate_product_performance(records),
            "daily_records": [record.to_dict() for record in records[-30:]]  # 最近30天详细记录
        }
    
    async def _generate_summary_report_data(self, records: List[AdvancedSettlementRecord]) -> Dict[str, Any]:
        """生成汇总报告数据"""
        if not records:
            return {}
        
        total_pnl = sum(record.total_pnl for record in records)
        total_commission = sum(record.total_commission for record in records)
        total_fees = sum(record.total_fees for record in records)
        net_pnl = total_pnl - total_commission - total_fees
        
        return {
            "total_pnl": float(total_pnl),
            "total_commission": float(total_commission),
            "total_fees": float(total_fees),
            "net_pnl": float(net_pnl),
            "average_daily_pnl": float(net_pnl / len(records)) if records else 0,
            "win_days": len([r for r in records if r.total_pnl > 0]),
            "loss_days": len([r for r in records if r.total_pnl < 0]),
            "flat_days": len([r for r in records if r.total_pnl == 0]),
            "total_trades": sum(sum(record.trade_count_by_product.values()) for record in records),
            "trading_days": len(records),
            "cost_ratio": float((total_commission + total_fees) / total_pnl) if total_pnl != 0 else 0
        }
    
    async def _generate_risk_report_data(self, records: List[AdvancedSettlementRecord]) -> Dict[str, Any]:
        """生成风险报告数据"""
        return await self._calculate_annual_risk_analysis(records)
    
    async def _generate_performance_report_data(self, records: List[AdvancedSettlementRecord]) -> Dict[str, Any]:
        """生成绩效报告数据"""
        return await self._calculate_performance_metrics(records)
    
    async def _generate_product_report_data(self, records: List[AdvancedSettlementRecord]) -> Dict[str, Any]:
        """生成产品报告数据"""
        return await self._calculate_product_performance(records)
    
    async def _calculate_summary_product_breakdown(self, records: List[AdvancedSettlementRecord]) -> Dict[str, Any]:
        """计算汇总产品分解"""
        return await self._calculate_product_performance(records)
    
    # 文件导出方法（简化实现）
    async def _generate_csv_data(self, records: List[AdvancedSettlementRecord]) -> str:
        """生成CSV数据"""
        # 简化实现，实际应该使用pandas或csv模块
        return "CSV data would be generated here"
    
    async def _generate_excel_file(self, records: List[AdvancedSettlementRecord], report: Dict[str, Any]) -> str:
        """生成Excel文件"""
        # 简化实现，实际应该使用openpyxl或xlswriter
        return "Excel file path would be returned here"
    
    async def _generate_pdf_file(self, records: List[AdvancedSettlementRecord], report: Dict[str, Any]) -> str:
        """生成PDF文件"""
        # 简化实现，实际应该使用reportlab或weasyprint
        return "PDF file path would be returned here"
