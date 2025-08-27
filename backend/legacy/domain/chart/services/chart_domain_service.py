"""
图表领域服务
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from ..entities.chart_entity import Chart
from ..entities.bar_data_entity import BarData
from ..value_objects.interval import Interval
from ..value_objects.chart_type import ChartType


class ChartDomainService:
    """
    图表领域服务
    
    处理图表相关的核心业务逻辑
    """
    
    def validate_chart_creation(self, symbol: str, chart_type: ChartType, interval: Interval) -> bool:
        """验证图表创建的有效性"""
        if not symbol or not symbol.strip():
            return False
        
        if not chart_type.is_price_based() and interval.is_high_frequency():
            # 非价格基础图表不支持高频周期
            return False
        
        return True
    
    def calculate_required_bars(self, interval: Interval, days: int = 30) -> int:
        """计算指定天数需要的K线数量"""
        seconds_per_day = 24 * 60 * 60
        total_seconds = days * seconds_per_day
        
        interval_seconds = interval.to_seconds()
        if not interval_seconds:
            return 0
        
        # 考虑交易时间（假设每天8小时交易）
        if interval.is_intraday():
            trading_hours_per_day = 8
            trading_seconds_per_day = trading_hours_per_day * 60 * 60
            total_trading_seconds = days * trading_seconds_per_day
            return int(total_trading_seconds / interval_seconds)
        else:
            return int(total_seconds / interval_seconds)
    
    def filter_bars_by_time_range(
        self, 
        bars: List[BarData], 
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[BarData]:
        """按时间范围过滤K线数据"""
        filtered_bars = bars
        
        if start_time:
            filtered_bars = [bar for bar in filtered_bars if bar.datetime >= start_time]
        
        if end_time:
            filtered_bars = [bar for bar in filtered_bars if bar.datetime <= end_time]
        
        return sorted(filtered_bars, key=lambda x: x.datetime)
    
    def resample_bars(self, bars: List[BarData], target_interval: Interval) -> List[BarData]:
        """重新采样K线数据到目标时间周期"""
        if not bars:
            return []
        
        # 简化实现，实际应该根据时间周期进行聚合
        # 这里只是返回原数据，真实实现需要按照target_interval进行聚合
        return bars
    
    def validate_bar_data_quality(self, bar: BarData) -> Dict[str, Any]:
        """验证单根K线数据质量"""
        issues = []
        
        # 价格逻辑检查
        if bar.high_price < max(bar.open_price, bar.close_price):
            issues.append("最高价低于开盘价或收盘价")
        
        if bar.low_price > min(bar.open_price, bar.close_price):
            issues.append("最低价高于开盘价或收盘价")
        
        # 成交量检查
        if bar.volume < 0:
            issues.append("成交量为负数")
        
        # 价格为零检查
        if any(price <= 0 for price in [bar.open_price, bar.high_price, bar.low_price, bar.close_price]):
            issues.append("价格包含零值或负值")
        
        # 异常波动检查（简化版）
        price_change_pct = abs(bar.price_change_pct)
        if price_change_pct > 50:  # 单根K线涨跌超过50%
            issues.append(f"异常价格波动: {price_change_pct:.2f}%")
        
        return {
            "is_valid": len(issues) == 0,
            "issues": issues,
            "bar_datetime": bar.datetime,
            "symbol": bar.symbol
        }
    
    def calculate_chart_statistics(self, bars: List[BarData]) -> Dict[str, Any]:
        """计算图表统计信息"""
        if not bars:
            return {
                "bar_count": 0,
                "time_range": None,
                "price_range": None,
                "volume_stats": None
            }
        
        sorted_bars = sorted(bars, key=lambda x: x.datetime)
        
        # 时间范围
        time_range = {
            "start": sorted_bars[0].datetime,
            "end": sorted_bars[-1].datetime,
            "duration": sorted_bars[-1].datetime - sorted_bars[0].datetime
        }
        
        # 价格范围
        all_highs = [bar.high_price for bar in bars]
        all_lows = [bar.low_price for bar in bars]
        price_range = {
            "highest": max(all_highs),
            "lowest": min(all_lows),
            "range": max(all_highs) - min(all_lows)
        }
        
        # 成交量统计
        volumes = [bar.volume for bar in bars]
        volume_stats = {
            "total": sum(volumes),
            "average": sum(volumes) / len(volumes),
            "max": max(volumes),
            "min": min(volumes)
        }
        
        return {
            "bar_count": len(bars),
            "time_range": time_range,
            "price_range": price_range,
            "volume_stats": volume_stats
        }
