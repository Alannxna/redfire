"""
WebSocket权限系统配置
定义基于角色的WebSocket权限控制规则
"""

from typing import Dict, List, Set
from enum import Enum


class UserRole(str, Enum):
    """用户角色枚举"""
    ADMIN = "admin"
    TRADER = "trader"
    VIEWER = "viewer"
    GUEST = "guest"


class WebSocketPermissions:
    """WebSocket权限定义"""
    
    # 基础权限
    WEBSOCKET_CONNECT = "websocket:connect"
    
    # 图表相关权限
    CHART_VIEW = "chart:view"
    CHART_SUBSCRIBE = "chart:subscribe"
    CHART_VIEW_ALL = "chart:view_all"
    CHART_MANAGE = "chart:manage"
    
    # 交易相关权限
    TRADING_VIEW = "trading:view"
    TRADING_VIEW_ALL = "trading:view_all"
    TRADING_EXECUTE = "trading:execute"
    TRADING_MANAGE = "trading:manage"
    
    # 策略相关权限
    STRATEGY_VIEW = "strategy:view"
    STRATEGY_VIEW_ALL = "strategy:view_all"
    STRATEGY_EXECUTE = "strategy:execute"
    STRATEGY_MANAGE = "strategy:manage"
    
    # 数据相关权限
    DATA_VIEW = "data:view"
    DATA_SUBSCRIBE = "data:subscribe"
    DATA_MANAGE = "data:manage"
    
    # 管理相关权限
    ADMIN_VIEW = "admin:view"
    ADMIN_MANAGE = "admin:manage"
    USER_MANAGE = "user:manage"


class WebSocketPermissionManager:
    """WebSocket权限管理器"""
    
    def __init__(self):
        self.role_permissions = self._initialize_role_permissions()
    
    def _initialize_role_permissions(self) -> Dict[UserRole, Set[str]]:
        """初始化角色权限映射"""
        return {
            UserRole.ADMIN: {
                # 管理员拥有所有权限
                WebSocketPermissions.WEBSOCKET_CONNECT,
                WebSocketPermissions.CHART_VIEW,
                WebSocketPermissions.CHART_SUBSCRIBE,
                WebSocketPermissions.CHART_VIEW_ALL,
                WebSocketPermissions.CHART_MANAGE,
                WebSocketPermissions.TRADING_VIEW,
                WebSocketPermissions.TRADING_VIEW_ALL,
                WebSocketPermissions.TRADING_EXECUTE,
                WebSocketPermissions.TRADING_MANAGE,
                WebSocketPermissions.STRATEGY_VIEW,
                WebSocketPermissions.STRATEGY_VIEW_ALL,
                WebSocketPermissions.STRATEGY_EXECUTE,
                WebSocketPermissions.STRATEGY_MANAGE,
                WebSocketPermissions.DATA_VIEW,
                WebSocketPermissions.DATA_SUBSCRIBE,
                WebSocketPermissions.DATA_MANAGE,
                WebSocketPermissions.ADMIN_VIEW,
                WebSocketPermissions.ADMIN_MANAGE,
                WebSocketPermissions.USER_MANAGE,
            },
            
            UserRole.TRADER: {
                # 交易者权限
                WebSocketPermissions.WEBSOCKET_CONNECT,
                WebSocketPermissions.CHART_VIEW,
                WebSocketPermissions.CHART_SUBSCRIBE,
                WebSocketPermissions.TRADING_VIEW,
                WebSocketPermissions.TRADING_EXECUTE,
                WebSocketPermissions.STRATEGY_VIEW,
                WebSocketPermissions.STRATEGY_EXECUTE,
                WebSocketPermissions.DATA_VIEW,
                WebSocketPermissions.DATA_SUBSCRIBE,
            },
            
            UserRole.VIEWER: {
                # 观察者权限（只读）
                WebSocketPermissions.WEBSOCKET_CONNECT,
                WebSocketPermissions.CHART_VIEW,
                WebSocketPermissions.CHART_SUBSCRIBE,
                WebSocketPermissions.TRADING_VIEW,
                WebSocketPermissions.STRATEGY_VIEW,
                WebSocketPermissions.DATA_VIEW,
                WebSocketPermissions.DATA_SUBSCRIBE,
            },
            
            UserRole.GUEST: {
                # 访客权限（基础只读）
                WebSocketPermissions.WEBSOCKET_CONNECT,
                WebSocketPermissions.CHART_VIEW,
                WebSocketPermissions.DATA_VIEW,
            }
        }
    
    def get_user_permissions(self, role: str) -> Set[str]:
        """
        获取用户角色的权限列表
        
        Args:
            role: 用户角色
            
        Returns:
            Set[str]: 权限集合
        """
        try:
            user_role = UserRole(role)
            return self.role_permissions.get(user_role, set())
        except ValueError:
            # 未知角色，返回最小权限
            return self.role_permissions.get(UserRole.GUEST, set())
    
    def check_permission(self, user_role: str, permission: str) -> bool:
        """
        检查用户是否有指定权限
        
        Args:
            user_role: 用户角色
            permission: 权限名称
            
        Returns:
            bool: 是否有权限
        """
        user_permissions = self.get_user_permissions(user_role)
        return permission in user_permissions
    
    def get_all_permissions(self) -> List[str]:
        """获取所有权限列表"""
        all_permissions = set()
        for permissions in self.role_permissions.values():
            all_permissions.update(permissions)
        return list(all_permissions)
    
    def get_role_info(self, role: str) -> Dict[str, any]:
        """
        获取角色信息
        
        Args:
            role: 用户角色
            
        Returns:
            Dict: 角色信息
        """
        permissions = self.get_user_permissions(role)
        return {
            "role": role,
            "permissions": list(permissions),
            "permission_count": len(permissions),
            "can_trade": self.check_permission(role, WebSocketPermissions.TRADING_EXECUTE),
            "can_view_all": self.check_permission(role, WebSocketPermissions.CHART_VIEW_ALL),
            "is_admin": self.check_permission(role, WebSocketPermissions.ADMIN_MANAGE)
        }


class WebSocketResourcePermissions:
    """WebSocket资源权限管理"""
    
    def __init__(self, permission_manager: WebSocketPermissionManager):
        self.permission_manager = permission_manager
    
    def can_access_chart(self, user_role: str, chart_id: str, user_id: str = None) -> bool:
        """
        检查是否可以访问图表
        
        Args:
            user_role: 用户角色
            chart_id: 图表ID
            user_id: 用户ID
            
        Returns:
            bool: 是否可以访问
        """
        # 管理员可以访问所有图表
        if self.permission_manager.check_permission(user_role, WebSocketPermissions.CHART_VIEW_ALL):
            return True
        
        # 其他用户需要基础图表查看权限
        if not self.permission_manager.check_permission(user_role, WebSocketPermissions.CHART_VIEW):
            return False
        
        # TODO: 实现具体的图表所有权检查逻辑
        # 例如：检查图表是否属于当前用户，或者是否为公开图表
        return True
    
    def can_execute_trade(self, user_role: str, user_id: str = None) -> bool:
        """
        检查是否可以执行交易
        
        Args:
            user_role: 用户角色
            user_id: 用户ID
            
        Returns:
            bool: 是否可以执行交易
        """
        # 检查交易执行权限
        if not self.permission_manager.check_permission(user_role, WebSocketPermissions.TRADING_EXECUTE):
            return False
        
        # TODO: 实现具体的交易权限检查逻辑
        # 例如：检查用户账户状态，资金余额等
        return True
    
    def can_view_user_data(self, user_role: str, target_user_id: str, current_user_id: str) -> bool:
        """
        检查是否可以查看其他用户的数据
        
        Args:
            user_role: 用户角色
            target_user_id: 目标用户ID
            current_user_id: 当前用户ID
            
        Returns:
            bool: 是否可以查看
        """
        # 用户可以查看自己的数据
        if target_user_id == current_user_id:
            return True
        
        # 管理员可以查看所有用户数据
        if self.permission_manager.check_permission(user_role, WebSocketPermissions.TRADING_VIEW_ALL):
            return True
        
        return False
    
    def get_accessible_data_types(self, user_role: str) -> List[str]:
        """
        获取用户可访问的数据类型列表
        
        Args:
            user_role: 用户角色
            
        Returns:
            List[str]: 可访问的数据类型
        """
        data_types = []
        
        if self.permission_manager.check_permission(user_role, WebSocketPermissions.CHART_VIEW):
            data_types.append("chart_data")
        
        if self.permission_manager.check_permission(user_role, WebSocketPermissions.TRADING_VIEW):
            data_types.extend(["order_data", "position_data", "account_data"])
        
        if self.permission_manager.check_permission(user_role, WebSocketPermissions.STRATEGY_VIEW):
            data_types.append("strategy_data")
        
        if self.permission_manager.check_permission(user_role, WebSocketPermissions.DATA_VIEW):
            data_types.extend(["market_data", "historical_data"])
        
        if self.permission_manager.check_permission(user_role, WebSocketPermissions.ADMIN_VIEW):
            data_types.extend(["system_data", "user_data", "log_data"])
        
        return data_types


# 全局权限管理器实例
permission_manager = WebSocketPermissionManager()
resource_permissions = WebSocketResourcePermissions(permission_manager)


def get_permission_manager() -> WebSocketPermissionManager:
    """获取权限管理器"""
    return permission_manager


def get_resource_permissions() -> WebSocketResourcePermissions:
    """获取资源权限管理器"""
    return resource_permissions
