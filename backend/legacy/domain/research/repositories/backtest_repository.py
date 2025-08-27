"""
回测仓储接口
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..entities.backtest_entity import Backtest, BacktestStatus, BacktestType


class BacktestRepository(ABC):
    """
    回测仓储接口
    
    定义回测数据的持久化操作
    """
    
    @abstractmethod
    async def save(self, backtest: Backtest) -> Backtest:
        """保存回测"""
        pass
    
    @abstractmethod
    async def find_by_id(self, backtest_id: str) -> Optional[Backtest]:
        """根据ID查找回测"""
        pass
    
    @abstractmethod
    async def find_by_project_id(self, project_id: str) -> List[Backtest]:
        """根据项目ID查找回测"""
        pass
    
    @abstractmethod
    async def find_by_status(self, status: BacktestStatus) -> List[Backtest]:
        """根据状态查找回测"""
        pass
    
    @abstractmethod
    async def find_by_type(self, backtest_type: BacktestType) -> List[Backtest]:
        """根据类型查找回测"""
        pass
    
    @abstractmethod
    async def find_running_backtests(self) -> List[Backtest]:
        """查找所有运行中的回测"""
        pass
    
    @abstractmethod
    async def find_completed_backtests(
        self,
        limit: Optional[int] = None,
        project_id: Optional[str] = None
    ) -> List[Backtest]:
        """查找已完成的回测"""
        pass
    
    @abstractmethod
    async def find_all(
        self,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        order_by: str = "created_at",
        order_direction: str = "desc"
    ) -> List[Backtest]:
        """查找所有回测"""
        pass
    
    @abstractmethod
    async def update(self, backtest: Backtest) -> Backtest:
        """更新回测"""
        pass
    
    @abstractmethod
    async def delete(self, backtest_id: str) -> bool:
        """删除回测"""
        pass
    
    @abstractmethod
    async def exists(self, backtest_id: str) -> bool:
        """检查回测是否存在"""
        pass
    
    @abstractmethod
    async def count_by_status(self, status: BacktestStatus) -> int:
        """统计指定状态的回测数量"""
        pass
    
    @abstractmethod
    async def count_by_project(self, project_id: str) -> int:
        """统计指定项目的回测数量"""
        pass
    
    @abstractmethod
    async def find_backtests_created_between(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[Backtest]:
        """查找指定时间范围内创建的回测"""
        pass
    
    @abstractmethod
    async def get_backtest_statistics(self) -> Dict[str, Any]:
        """获取回测统计信息"""
        pass
    
    @abstractmethod
    async def cleanup_old_backtests(self, cutoff_date: datetime) -> int:
        """清理旧的回测记录"""
        pass
