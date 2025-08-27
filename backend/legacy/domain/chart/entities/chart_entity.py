"""
图表实体 - 图表的核心业务对象
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass, field
from uuid import uuid4

from ..value_objects.chart_config import ChartConfig
from ..value_objects.chart_type import ChartType
from ..value_objects.interval import Interval


@dataclass
class Chart:
    """
    图表实体
    
    聚合根，管理图表的配置、数据和状态
    """
    chart_id: str = field(default_factory=lambda: str(uuid4()))
    symbol: str = ""
    chart_type: ChartType = ChartType.CANDLESTICK
    interval: Interval = Interval.MINUTE_1
    title: str = ""
    description: str = ""
    config: ChartConfig = field(default_factory=lambda: ChartConfig())
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    is_active: bool = True
    
    # 运行时状态
    _bar_count: int = 0
    _last_update: Optional[datetime] = None
    _subscribers: List[str] = field(default_factory=list)
    
    def add_subscriber(self, subscriber_id: str) -> None:
        """添加订阅者"""
        if subscriber_id not in self._subscribers:
            self._subscribers.append(subscriber_id)
    
    def remove_subscriber(self, subscriber_id: str) -> None:
        """移除订阅者"""
        if subscriber_id in self._subscribers:
            self._subscribers.remove(subscriber_id)
    
    def update_config(self, config: ChartConfig) -> None:
        """更新图表配置"""
        self.config = config
        self.updated_at = datetime.now()
    
    def activate(self) -> None:
        """激活图表"""
        self.is_active = True
        self.updated_at = datetime.now()
    
    def deactivate(self) -> None:
        """停用图表"""
        self.is_active = False
        self.updated_at = datetime.now()
    
    def update_bar_count(self, count: int) -> None:
        """更新K线数量"""
        self._bar_count = count
        self._last_update = datetime.now()
    
    @property
    def subscriber_count(self) -> int:
        """订阅者数量"""
        return len(self._subscribers)
    
    @property
    def bar_count(self) -> int:
        """K线数量"""
        return self._bar_count
    
    @property 
    def last_update(self) -> Optional[datetime]:
        """最后更新时间"""
        return self._last_update
    
    def has_subscribers(self) -> bool:
        """检查是否有订阅者"""
        return len(self._subscribers) > 0
    
    @classmethod
    def create(
        cls,
        symbol: str,
        chart_type: ChartType = ChartType.CANDLESTICK,
        interval: Interval = Interval.MINUTE_1,
        title: Optional[str] = None,
        description: str = ""
    ) -> 'Chart':
        """创建新图表"""
        if title is None:
            title = f"{symbol} {chart_type.value} Chart"
        
        return cls(
            symbol=symbol,
            chart_type=chart_type,
            interval=interval,
            title=title,
            description=description
        )
    
    def update_info(self, title: Optional[str] = None, description: Optional[str] = None) -> None:
        """更新图表信息"""
        if title is not None:
            self.title = title
        if description is not None:
            self.description = description
        # 确保时间戳不同
        import time
        time.sleep(0.001)  # 等待1毫秒
        self.updated_at = datetime.now()
