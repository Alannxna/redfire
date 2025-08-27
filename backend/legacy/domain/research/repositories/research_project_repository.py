"""
研究项目仓储接口
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..entities.research_project_entity import ResearchProject, ResearchPhase, ProjectStatus


class ResearchProjectRepository(ABC):
    """
    研究项目仓储接口
    
    定义研究项目数据的持久化操作
    """
    
    @abstractmethod
    async def save(self, project: ResearchProject) -> ResearchProject:
        """保存研究项目"""
        pass
    
    @abstractmethod
    async def find_by_id(self, project_id: str) -> Optional[ResearchProject]:
        """根据ID查找项目"""
        pass
    
    @abstractmethod
    async def find_by_name(self, name: str) -> Optional[ResearchProject]:
        """根据名称查找项目"""
        pass
    
    @abstractmethod
    async def find_by_status(self, status: ProjectStatus) -> List[ResearchProject]:
        """根据状态查找项目"""
        pass
    
    @abstractmethod
    async def find_by_phase(self, phase: ResearchPhase) -> List[ResearchProject]:
        """根据研究阶段查找项目"""
        pass
    
    @abstractmethod
    async def find_by_tags(self, tags: List[str]) -> List[ResearchProject]:
        """根据标签查找项目"""
        pass
    
    @abstractmethod
    async def find_all(
        self,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        order_by: str = "created_at",
        order_direction: str = "desc"
    ) -> List[ResearchProject]:
        """查找所有项目"""
        pass
    
    @abstractmethod
    async def update(self, project: ResearchProject) -> ResearchProject:
        """更新项目"""
        pass
    
    @abstractmethod
    async def delete(self, project_id: str) -> bool:
        """删除项目"""
        pass
    
    @abstractmethod
    async def exists(self, project_id: str) -> bool:
        """检查项目是否存在"""
        pass
    
    @abstractmethod
    async def count_by_status(self, status: ProjectStatus) -> int:
        """统计指定状态的项目数量"""
        pass
    
    @abstractmethod
    async def find_projects_created_between(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[ResearchProject]:
        """查找指定时间范围内创建的项目"""
        pass
    
    @abstractmethod
    async def find_projects_with_symbols(self, symbols: List[str]) -> List[ResearchProject]:
        """查找包含指定交易品种的项目"""
        pass
    
    @abstractmethod
    async def get_project_statistics(self) -> Dict[str, Any]:
        """获取项目统计信息"""
        pass
