"""
用户仓储接口

定义用户聚合的持久化操作接口
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from datetime import datetime

from ..entities.user import User, UserStatus
from ..value_objects.user_id import UserId
from ..value_objects.username import Username
from ...shared.value_objects.email import Email
from ....core.base.repository_base import BaseRepository
from ....core.common.enums.user_roles import UserRole


class IUserRepository(BaseRepository[User, UserId], ABC):
    """用户仓储接口
    
    定义用户聚合的所有持久化操作
    """
    
    @abstractmethod
    async def find_by_username(self, username: Username) -> Optional[User]:
        """根据用户名查找用户
        
        Args:
            username: 用户名值对象
            
        Returns:
            用户实体或None
        """
        pass
    
    @abstractmethod
    async def find_by_email(self, email: Email) -> Optional[User]:
        """根据邮箱查找用户
        
        Args:
            email: 邮箱值对象
            
        Returns:
            用户实体或None
        """
        pass
    
    @abstractmethod
    async def username_exists(self, username: Username) -> bool:
        """检查用户名是否存在
        
        Args:
            username: 用户名值对象
            
        Returns:
            是否存在
        """
        pass
    
    @abstractmethod
    async def email_exists(self, email: Email) -> bool:
        """检查邮箱是否存在
        
        Args:
            email: 邮箱值对象
            
        Returns:
            是否存在
        """
        pass
    
    @abstractmethod
    async def find_by_role(self, role: UserRole, limit: int = 100, offset: int = 0) -> List[User]:
        """根据角色查找用户
        
        Args:
            role: 用户角色
            limit: 限制数量
            offset: 偏移量
            
        Returns:
            用户列表
        """
        pass
    
    @abstractmethod
    async def find_by_status(self, status: UserStatus, limit: int = 100, offset: int = 0) -> List[User]:
        """根据状态查找用户
        
        Args:
            status: 用户状态
            limit: 限制数量
            offset: 偏移量
            
        Returns:
            用户列表
        """
        pass
    
    @abstractmethod
    async def find_active_users(self, limit: int = 100, offset: int = 0) -> List[User]:
        """查找活跃用户
        
        Args:
            limit: 限制数量
            offset: 偏移量
            
        Returns:
            活跃用户列表
        """
        pass
    
    @abstractmethod
    async def find_users_created_after(self, date: datetime, limit: int = 100, offset: int = 0) -> List[User]:
        """查找指定日期后创建的用户
        
        Args:
            date: 指定日期
            limit: 限制数量
            offset: 偏移量
            
        Returns:
            用户列表
        """
        pass
    
    @abstractmethod
    async def find_users_last_login_before(self, date: datetime, limit: int = 100, offset: int = 0) -> List[User]:
        """查找最后登录时间在指定日期之前的用户
        
        Args:
            date: 指定日期
            limit: 限制数量
            offset: 偏移量
            
        Returns:
            用户列表
        """
        pass
    
    @abstractmethod
    async def search_users(self, keyword: str, filters: Optional[Dict[str, Any]] = None,
                          limit: int = 100, offset: int = 0) -> List[User]:
        """搜索用户
        
        Args:
            keyword: 搜索关键词
            filters: 过滤条件
            limit: 限制数量
            offset: 偏移量
            
        Returns:
            用户列表
        """
        pass
    
    @abstractmethod
    async def count_users_by_status(self, status: UserStatus) -> int:
        """统计指定状态的用户数量
        
        Args:
            status: 用户状态
            
        Returns:
            用户数量
        """
        pass
    
    @abstractmethod
    async def count_users_by_role(self, role: UserRole) -> int:
        """统计指定角色的用户数量
        
        Args:
            role: 用户角色
            
        Returns:
            用户数量
        """
        pass
    
    @abstractmethod
    async def get_user_statistics(self) -> Dict[str, Any]:
        """获取用户统计信息
        
        Returns:
            统计信息字典
        """
        pass
