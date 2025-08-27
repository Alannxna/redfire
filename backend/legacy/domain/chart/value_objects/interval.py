"""
时间间隔值对象
"""

from enum import Enum
from typing import Optional
from datetime import timedelta


class Interval(str, Enum):
    """
    时间间隔枚举
    
    定义K线数据的时间周期
    """
    # 分钟级别
    MINUTE_1 = "1m"
    MINUTE_5 = "5m"
    MINUTE_15 = "15m"
    MINUTE_30 = "30m"
    
    # 小时级别
    HOUR_1 = "1h"
    HOUR_2 = "2h"
    HOUR_4 = "4h"
    HOUR_6 = "6h"
    HOUR_8 = "8h"
    HOUR_12 = "12h"
    
    # 日级别
    DAY_1 = "1d"
    DAY_3 = "3d"
    
    # 周月级别
    WEEK_1 = "1w"
    MONTH_1 = "1M"
    
    # 秒级别（高频交易）
    SECOND_1 = "1s"
    SECOND_5 = "5s"
    SECOND_15 = "15s"
    SECOND_30 = "30s"
    
    @classmethod
    def get_default(cls) -> 'Interval':
        """获取默认时间间隔"""
        return cls.MINUTE_1
    
    @classmethod
    def get_minute_intervals(cls) -> list:
        """获取分钟级别间隔"""
        return [cls.MINUTE_1, cls.MINUTE_5, cls.MINUTE_15, cls.MINUTE_30]
    
    @classmethod
    def get_hour_intervals(cls) -> list:
        """获取小时级别间隔"""
        return [cls.HOUR_1, cls.HOUR_2, cls.HOUR_4, cls.HOUR_6, cls.HOUR_8, cls.HOUR_12]
    
    @classmethod
    def get_day_intervals(cls) -> list:
        """获取日级别间隔"""
        return [cls.DAY_1, cls.DAY_3, cls.WEEK_1, cls.MONTH_1]
    
    def to_timedelta(self) -> Optional[timedelta]:
        """转换为timedelta对象"""
        mapping = {
            self.SECOND_1: timedelta(seconds=1),
            self.SECOND_5: timedelta(seconds=5),
            self.SECOND_15: timedelta(seconds=15),
            self.SECOND_30: timedelta(seconds=30),
            self.MINUTE_1: timedelta(minutes=1),
            self.MINUTE_5: timedelta(minutes=5),
            self.MINUTE_15: timedelta(minutes=15),
            self.MINUTE_30: timedelta(minutes=30),
            self.HOUR_1: timedelta(hours=1),
            self.HOUR_2: timedelta(hours=2),
            self.HOUR_4: timedelta(hours=4),
            self.HOUR_6: timedelta(hours=6),
            self.HOUR_8: timedelta(hours=8),
            self.HOUR_12: timedelta(hours=12),
            self.DAY_1: timedelta(days=1),
            self.DAY_3: timedelta(days=3),
            self.WEEK_1: timedelta(weeks=1),
            self.MONTH_1: timedelta(days=30),  # 近似值
        }
        return mapping.get(self)
    
    def to_seconds(self) -> Optional[int]:
        """转换为秒数"""
        td = self.to_timedelta()
        return int(td.total_seconds()) if td else None
    
    def is_intraday(self) -> bool:
        """是否为日内周期"""
        return self in [
            self.SECOND_1, self.SECOND_5, self.SECOND_15, self.SECOND_30,
            self.MINUTE_1, self.MINUTE_5, self.MINUTE_15, self.MINUTE_30,
            self.HOUR_1, self.HOUR_2, self.HOUR_4, self.HOUR_6, self.HOUR_8, self.HOUR_12
        ]
    
    def is_high_frequency(self) -> bool:
        """是否为高频周期（1分钟以下）"""
        return self in [
            self.SECOND_1, self.SECOND_5, self.SECOND_15, self.SECOND_30
        ]
