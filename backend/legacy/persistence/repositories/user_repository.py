"""
用户仓储实现
实现用户领域的数据访问逻辑
"""

from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc, asc
from sqlalchemy.orm import selectinload
from datetime import datetime, timedelta
import logging

from ...core.base.repository_base import BaseRepository
from ..models.user_models import UserModel, UserSessionModel, UserActivityLogModel
from ...domain.user.entities.user import User
from ...core.common.enums.user_roles import UserStatus
from ...domain.user.value_objects.user_id import UserId
from ...domain.shared.value_objects.email import Email
from ...core.common.enums.user_roles import UserRole
from ...domain.user.repositories.user_repository import IUserRepository
from ...core.common.exceptions import NotFoundException


logger = logging.getLogger(__name__)


class UserRepository(IUserRepository):
    """用户仓储实现"""
    
    def __init__(self, session: AsyncSession):
        self._session = session
    
    async def find_by_id(self, user_id: UserId) -> Optional[User]:
        """根据ID查找用户"""
        try:
            stmt = select(UserModel).where(
                and_(
                    UserModel.id == str(user_id),
                    UserModel.deleted_at.is_(None)
                )
            )
            result = await self._session.execute(stmt)
            user_model = result.scalar_one_or_none()
            
            if not user_model:
                return None
            
            return self._model_to_entity(user_model)
            
        except Exception as e:
            logger.error(f"根据ID查找用户失败: {e}")
            raise
    
    async def find_by_username(self, username) -> Optional[User]:
        """根据用户名查找用户"""
        try:
            stmt = select(UserModel).where(
                and_(
                    UserModel.username == username,
                    UserModel.deleted_at.is_(None)
                )
            )
            result = await self._session.execute(stmt)
            user_model = result.scalar_one_or_none()
            
            if not user_model:
                return None
            
            return self._model_to_entity(user_model)
            
        except Exception as e:
            logger.error(f"根据用户名查找用户失败: {e}")
            raise
    
    async def find_by_email(self, email: Email) -> Optional[User]:
        """根据邮箱查找用户"""
        try:
            stmt = select(UserModel).where(
                and_(
                    UserModel.email == str(email),
                    UserModel.deleted_at.is_(None)
                )
            )
            result = await self._session.execute(stmt)
            user_model = result.scalar_one_or_none()
            
            if not user_model:
                return None
            
            return self._model_to_entity(user_model)
            
        except Exception as e:
            logger.error(f"根据邮箱查找用户失败: {e}")
            raise
    
    async def find_paginated(
        self,
        page: int,
        size: int,
        filters: Optional[Dict[str, Any]] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> Tuple[List[User], int]:
        """分页查找用户"""
        try:
            # 构建基础查询
            stmt = select(UserModel).where(UserModel.deleted_at.is_(None))
            count_stmt = select(func.count(UserModel.id)).where(UserModel.deleted_at.is_(None))
            
            # 应用过滤条件
            if filters:
                conditions = self._build_filter_conditions(filters)
                if conditions:
                    stmt = stmt.where(and_(*conditions))
                    count_stmt = count_stmt.where(and_(*conditions))
            
            # 应用排序
            sort_column = getattr(UserModel, sort_by, UserModel.created_at)
            if sort_order.lower() == "desc":
                stmt = stmt.order_by(desc(sort_column))
            else:
                stmt = stmt.order_by(asc(sort_column))
            
            # 应用分页
            offset = (page - 1) * size
            stmt = stmt.offset(offset).limit(size)
            
            # 执行查询
            result = await self._session.execute(stmt)
            user_models = result.scalars().all()
            
            # 获取总数
            count_result = await self._session.execute(count_stmt)
            total = count_result.scalar()
            
            # 转换为实体
            users = [self._model_to_entity(model) for model in user_models]
            
            return users, total
            
        except Exception as e:
            logger.error(f"分页查找用户失败: {e}")
            raise
    
    async def search(
        self,
        keyword: str,
        limit: int = 10,
        include_inactive: bool = False
    ) -> List[User]:
        """搜索用户"""
        try:
            # 构建搜索条件
            search_conditions = [
                UserModel.username.ilike(f"%{keyword}%"),
                UserModel.email.ilike(f"%{keyword}%"),
                UserModel.full_name.ilike(f"%{keyword}%")
            ]
            
            # 基础查询条件
            base_conditions = [
                UserModel.deleted_at.is_(None),
                or_(*search_conditions)
            ]
            
            # 是否包含非活跃用户
            if not include_inactive:
                base_conditions.append(UserModel.status == UserStatus.ACTIVE)
            
            # 构建查询
            stmt = select(UserModel).where(
                and_(*base_conditions)
            ).order_by(
                UserModel.username
            ).limit(limit)
            
            # 执行查询
            result = await self._session.execute(stmt)
            user_models = result.scalars().all()
            
            # 转换为实体
            return [self._model_to_entity(model) for model in user_models]
            
        except Exception as e:
            logger.error(f"搜索用户失败: {e}")
            raise
    
    async def get_statistics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        group_by: str = "day"
    ) -> Dict[str, Any]:
        """获取用户统计信息"""
        try:
            # 基础条件
            conditions = [UserModel.deleted_at.is_(None)]
            
            # 时间范围
            if start_date:
                conditions.append(UserModel.created_at >= start_date)
            if end_date:
                conditions.append(UserModel.created_at <= end_date)
            
            # 总用户数
            total_stmt = select(func.count(UserModel.id)).where(and_(*conditions))
            total_result = await self._session.execute(total_stmt)
            total_users = total_result.scalar()
            
            # 活跃用户数
            active_stmt = select(func.count(UserModel.id)).where(
                and_(
                    *conditions,
                    UserModel.status == UserStatus.ACTIVE
                )
            )
            active_result = await self._session.execute(active_stmt)
            active_users = active_result.scalar()
            
            # 今日新用户
            today = datetime.now().date()
            today_stmt = select(func.count(UserModel.id)).where(
                and_(
                    UserModel.deleted_at.is_(None),
                    func.date(UserModel.created_at) == today
                )
            )
            today_result = await self._session.execute(today_stmt)
            new_users_today = today_result.scalar()
            
            # 本周新用户
            week_ago = datetime.now() - timedelta(days=7)
            week_stmt = select(func.count(UserModel.id)).where(
                and_(
                    UserModel.deleted_at.is_(None),
                    UserModel.created_at >= week_ago
                )
            )
            week_result = await self._session.execute(week_stmt)
            new_users_this_week = week_result.scalar()
            
            # 本月新用户
            month_ago = datetime.now() - timedelta(days=30)
            month_stmt = select(func.count(UserModel.id)).where(
                and_(
                    UserModel.deleted_at.is_(None),
                    UserModel.created_at >= month_ago
                )
            )
            month_result = await self._session.execute(month_stmt)
            new_users_this_month = month_result.scalar()
            
            return {
                "total_users": total_users,
                "active_users": active_users,
                "new_users_today": new_users_today,
                "new_users_this_week": new_users_this_week,
                "new_users_this_month": new_users_this_month,
                "user_growth_chart": []  # TODO: 实现增长图表数据
            }
            
        except Exception as e:
            logger.error(f"获取用户统计信息失败: {e}")
            raise
    
    async def save(self, user: User) -> None:
        """保存用户"""
        try:
            # 查找现有模型
            stmt = select(UserModel).where(UserModel.id == str(user.user_id))
            result = await self._session.execute(stmt)
            user_model = result.scalar_one_or_none()
            
            if user_model:
                # 更新现有用户
                self._update_model_from_entity(user_model, user)
            else:
                # 创建新用户
                user_model = self._entity_to_model(user)
                self._session.add(user_model)
            
            await self._session.flush()
            
        except Exception as e:
            logger.error(f"保存用户失败: {e}")
            raise
    
    async def delete(self, user_id: UserId) -> None:
        """删除用户（软删除）"""
        try:
            stmt = select(UserModel).where(UserModel.id == str(user_id))
            result = await self._session.execute(stmt)
            user_model = result.scalar_one_or_none()
            
            if not user_model:
                raise NotFoundException(f"用户不存在: {user_id}")
            
            # 软删除
            user_model.deleted_at = datetime.utcnow()
            await self._session.flush()
            
        except Exception as e:
            logger.error(f"删除用户失败: {e}")
            raise
    
    def _build_filter_conditions(self, filters: Dict[str, Any]) -> List:
        """构建过滤条件"""
        conditions = []
        
        if "role" in filters:
            conditions.append(UserModel.role == filters["role"])
        
        if "status" in filters:
            conditions.append(UserModel.status == filters["status"])
        
        if "search" in filters:
            keyword = filters["search"]
            search_conditions = [
                UserModel.username.ilike(f"%{keyword}%"),
                UserModel.email.ilike(f"%{keyword}%"),
                UserModel.full_name.ilike(f"%{keyword}%")
            ]
            conditions.append(or_(*search_conditions))
        
        if "created_after" in filters:
            conditions.append(UserModel.created_at >= filters["created_after"])
        
        if "created_before" in filters:
            conditions.append(UserModel.created_at <= filters["created_before"])
        
        if "last_login_after" in filters:
            conditions.append(UserModel.last_login_at >= filters["last_login_after"])
        
        if "last_login_before" in filters:
            conditions.append(UserModel.last_login_at <= filters["last_login_before"])
        
        return conditions
    
    def _model_to_entity(self, model: UserModel) -> User:
        """将数据模型转换为实体"""
        from ...domain.user.value_objects.username import Username
        
        return User(
            user_id=UserId(str(model.id)),
            username=Username(model.username),
            email=Email(model.email),
            hashed_password=model.password_hash,
            full_name=model.full_name,
            avatar_url=model.avatar_url,
            role=model.role,
            status=model.status,
            created_at=model.created_at,
            updated_at=model.updated_at,
            last_login_at=model.last_login_at
        )
    
    def _entity_to_model(self, entity: User) -> UserModel:
        """将实体转换为数据模型"""
        return UserModel(
            id=str(entity.user_id),
            username=str(entity.username),
            email=str(entity.email),
            password_hash=entity.hashed_password,
            full_name=entity.full_name,
            avatar_url=entity.avatar_url,
            role=entity.role,
            status=entity.status,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            last_login_at=entity.last_login_at
        )
    
    def _update_model_from_entity(self, model: UserModel, entity: User) -> None:
        """从实体更新数据模型"""
        model.username = str(entity.username)
        model.email = str(entity.email)
        model.password_hash = entity.hashed_password
        model.full_name = entity.full_name
        model.avatar_url = entity.avatar_url
        model.role = entity.role
        model.status = entity.status
        model.updated_at = entity.updated_at
        model.last_login_at = entity.last_login_at
    
    # 实现IUserRepository接口的缺失方法
    
    async def username_exists(self, username) -> bool:
        """检查用户名是否存在"""
        try:
            # 处理Username值对象或字符串
            username_str = str(username) if hasattr(username, 'value') else username
            
            stmt = select(func.count(UserModel.id)).where(
                and_(
                    UserModel.username == username_str,
                    UserModel.deleted_at.is_(None)
                )
            )
            result = await self._session.execute(stmt)
            count = result.scalar()
            return count > 0
            
        except Exception as e:
            logger.error(f"检查用户名是否存在失败: {e}")
            raise
    
    async def email_exists(self, email) -> bool:
        """检查邮箱是否存在"""
        try:
            # 处理Email值对象或字符串
            email_str = str(email) if hasattr(email, 'value') else email
            
            stmt = select(func.count(UserModel.id)).where(
                and_(
                    UserModel.email == email_str,
                    UserModel.deleted_at.is_(None)
                )
            )
            result = await self._session.execute(stmt)
            count = result.scalar()
            return count > 0
            
        except Exception as e:
            logger.error(f"检查邮箱是否存在失败: {e}")
            raise
    
    async def find_by_role(self, role: UserRole, limit: int = 100, offset: int = 0) -> List[User]:
        """根据角色查找用户"""
        try:
            stmt = select(UserModel).where(
                and_(
                    UserModel.role == role,
                    UserModel.deleted_at.is_(None)
                )
            ).order_by(UserModel.created_at.desc()).offset(offset).limit(limit)
            
            result = await self._session.execute(stmt)
            user_models = result.scalars().all()
            
            return [self._model_to_entity(model) for model in user_models]
            
        except Exception as e:
            logger.error(f"根据角色查找用户失败: {e}")
            raise
    
    async def find_by_status(self, status: UserStatus, limit: int = 100, offset: int = 0) -> List[User]:
        """根据状态查找用户"""
        try:
            stmt = select(UserModel).where(
                and_(
                    UserModel.status == status,
                    UserModel.deleted_at.is_(None)
                )
            ).order_by(UserModel.created_at.desc()).offset(offset).limit(limit)
            
            result = await self._session.execute(stmt)
            user_models = result.scalars().all()
            
            return [self._model_to_entity(model) for model in user_models]
            
        except Exception as e:
            logger.error(f"根据状态查找用户失败: {e}")
            raise
    
    async def find_active_users(self, limit: int = 100, offset: int = 0) -> List[User]:
        """查找活跃用户"""
        return await self.find_by_status(UserStatus.ACTIVE, limit, offset)
    
    async def find_users_created_after(self, date: datetime, limit: int = 100, offset: int = 0) -> List[User]:
        """查找指定日期后创建的用户"""
        try:
            stmt = select(UserModel).where(
                and_(
                    UserModel.created_at >= date,
                    UserModel.deleted_at.is_(None)
                )
            ).order_by(UserModel.created_at.desc()).offset(offset).limit(limit)
            
            result = await self._session.execute(stmt)
            user_models = result.scalars().all()
            
            return [self._model_to_entity(model) for model in user_models]
            
        except Exception as e:
            logger.error(f"查找指定日期后创建的用户失败: {e}")
            raise
    
    async def find_users_last_login_before(self, date: datetime, limit: int = 100, offset: int = 0) -> List[User]:
        """查找最后登录时间在指定日期之前的用户"""
        try:
            stmt = select(UserModel).where(
                and_(
                    UserModel.last_login_at < date,
                    UserModel.deleted_at.is_(None)
                )
            ).order_by(UserModel.last_login_at.desc()).offset(offset).limit(limit)
            
            result = await self._session.execute(stmt)
            user_models = result.scalars().all()
            
            return [self._model_to_entity(model) for model in user_models]
            
        except Exception as e:
            logger.error(f"查找最后登录时间在指定日期之前的用户失败: {e}")
            raise
    
    async def search_users(self, keyword: str, filters: Optional[Dict[str, Any]] = None,
                          limit: int = 100, offset: int = 0) -> List[User]:
        """搜索用户"""
        try:
            # 构建搜索条件
            search_conditions = [
                UserModel.username.ilike(f"%{keyword}%"),
                UserModel.email.ilike(f"%{keyword}%"),
                UserModel.full_name.ilike(f"%{keyword}%")
            ]
            
            # 基础查询条件
            base_conditions = [
                UserModel.deleted_at.is_(None),
                or_(*search_conditions)
            ]
            
            # 应用额外过滤条件
            if filters:
                filter_conditions = self._build_filter_conditions(filters)
                base_conditions.extend(filter_conditions)
            
            # 构建查询
            stmt = select(UserModel).where(
                and_(*base_conditions)
            ).order_by(
                UserModel.username
            ).offset(offset).limit(limit)
            
            # 执行查询
            result = await self._session.execute(stmt)
            user_models = result.scalars().all()
            
            # 转换为实体
            return [self._model_to_entity(model) for model in user_models]
            
        except Exception as e:
            logger.error(f"搜索用户失败: {e}")
            raise
    
    async def count_users_by_status(self, status: UserStatus) -> int:
        """统计指定状态的用户数量"""
        try:
            stmt = select(func.count(UserModel.id)).where(
                and_(
                    UserModel.status == status,
                    UserModel.deleted_at.is_(None)
                )
            )
            result = await self._session.execute(stmt)
            return result.scalar()
            
        except Exception as e:
            logger.error(f"统计指定状态的用户数量失败: {e}")
            raise
    
    async def count_users_by_role(self, role: UserRole) -> int:
        """统计指定角色的用户数量"""
        try:
            stmt = select(func.count(UserModel.id)).where(
                and_(
                    UserModel.role == role,
                    UserModel.deleted_at.is_(None)
                )
            )
            result = await self._session.execute(stmt)
            return result.scalar()
            
        except Exception as e:
            logger.error(f"统计指定角色的用户数量失败: {e}")
            raise
    
    async def get_user_statistics(self) -> Dict[str, Any]:
        """获取用户统计信息"""
        try:
            # 总用户数
            total_stmt = select(func.count(UserModel.id)).where(UserModel.deleted_at.is_(None))
            total_result = await self._session.execute(total_stmt)
            total_users = total_result.scalar()
            
            # 活跃用户数
            active_stmt = select(func.count(UserModel.id)).where(
                and_(
                    UserModel.status == UserStatus.ACTIVE,
                    UserModel.deleted_at.is_(None)
                )
            )
            active_result = await self._session.execute(active_stmt)
            active_users = active_result.scalar()
            
            # 按角色统计
            role_stats = {}
            for role in UserRole:
                count = await self.count_users_by_role(role)
                role_stats[role.value] = count
            
            # 按状态统计
            status_stats = {}
            for status in UserStatus:
                count = await self.count_users_by_status(status)
                status_stats[status.value] = count
            
            # 今日新用户
            today = datetime.now().date()
            today_stmt = select(func.count(UserModel.id)).where(
                and_(
                    func.date(UserModel.created_at) == today,
                    UserModel.deleted_at.is_(None)
                )
            )
            today_result = await self._session.execute(today_stmt)
            new_users_today = today_result.scalar()
            
            # 本周新用户
            week_ago = datetime.now() - timedelta(days=7)
            week_stmt = select(func.count(UserModel.id)).where(
                and_(
                    UserModel.created_at >= week_ago,
                    UserModel.deleted_at.is_(None)
                )
            )
            week_result = await self._session.execute(week_stmt)
            new_users_this_week = week_result.scalar()
            
            # 本月新用户
            month_ago = datetime.now() - timedelta(days=30)
            month_stmt = select(func.count(UserModel.id)).where(
                and_(
                    UserModel.created_at >= month_ago,
                    UserModel.deleted_at.is_(None)
                )
            )
            month_result = await self._session.execute(month_stmt)
            new_users_this_month = month_result.scalar()
            
            return {
                "total_users": total_users,
                "active_users": active_users,
                "role_distribution": role_stats,
                "status_distribution": status_stats,
                "new_users_today": new_users_today,
                "new_users_this_week": new_users_this_week,
                "new_users_this_month": new_users_this_month,
                "activity_rate": (active_users / total_users * 100) if total_users > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"获取用户统计信息失败: {e}")
            raise
    
    # 增强的分页查询方法
    async def find_paginated_with_search(
        self,
        page: int = 1,
        size: int = 20,
        search: Optional[str] = None,
        role: Optional[UserRole] = None,
        status: Optional[UserStatus] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> Tuple[List[User], int]:
        """增强的分页查询，支持搜索和过滤"""
        try:
            # 构建基础查询
            conditions = [UserModel.deleted_at.is_(None)]
            
            # 搜索条件
            if search:
                search_conditions = [
                    UserModel.username.ilike(f"%{search}%"),
                    UserModel.email.ilike(f"%{search}%"),
                    UserModel.full_name.ilike(f"%{search}%")
                ]
                conditions.append(or_(*search_conditions))
            
            # 角色过滤
            if role:
                conditions.append(UserModel.role == role)
            
            # 状态过滤
            if status:
                conditions.append(UserModel.status == status)
            
            # 构建查询语句
            stmt = select(UserModel).where(and_(*conditions))
            count_stmt = select(func.count(UserModel.id)).where(and_(*conditions))
            
            # 应用排序
            sort_column = getattr(UserModel, sort_by, UserModel.created_at)
            if sort_order.lower() == "desc":
                stmt = stmt.order_by(desc(sort_column))
            else:
                stmt = stmt.order_by(asc(sort_column))
            
            # 应用分页
            offset = (page - 1) * size
            stmt = stmt.offset(offset).limit(size)
            
            # 执行查询
            result = await self._session.execute(stmt)
            user_models = result.scalars().all()
            
            # 获取总数
            count_result = await self._session.execute(count_stmt)
            total = count_result.scalar()
            
            # 转换为实体
            users = [self._model_to_entity(model) for model in user_models]
            
            return users, total
            
        except Exception as e:
            logger.error(f"增强分页查询失败: {e}")
            raise
    
    def _build_filter_conditions(self, filters: Dict[str, Any]) -> List:
        """构建过滤条件"""
        conditions = []
        
        # 角色过滤
        if "role" in filters and filters["role"]:
            conditions.append(UserModel.role == filters["role"])
        
        # 状态过滤
        if "status" in filters and filters["status"]:
            conditions.append(UserModel.status == filters["status"])
        
        # 创建时间范围
        if "created_after" in filters and filters["created_after"]:
            conditions.append(UserModel.created_at >= filters["created_after"])
        
        if "created_before" in filters and filters["created_before"]:
            conditions.append(UserModel.created_at <= filters["created_before"])
        
        # 最后登录时间范围
        if "last_login_after" in filters and filters["last_login_after"]:
            conditions.append(UserModel.last_login_at >= filters["last_login_after"])
        
        if "last_login_before" in filters and filters["last_login_before"]:
            conditions.append(UserModel.last_login_at <= filters["last_login_before"])
        
        # 邮箱验证状态
        if "email_verified" in filters:
            conditions.append(UserModel.email_verified == filters["email_verified"])
        
        return conditions
