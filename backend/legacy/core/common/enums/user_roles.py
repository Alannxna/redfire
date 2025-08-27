"""
用户角色和权限枚举
==================

定义用户角色和交易权限的统一枚举
"""

from enum import Enum


class UserRole(Enum):
    """用户角色枚举"""
    ADMIN = "admin"
    TRADER = "trader"
    VIEWER = "viewer"
    GUEST = "guest"

    def __str__(self):
        return self.value

    @property
    def permissions(self) -> set:
        """获取角色对应的权限集合"""
        role_permissions = {
            UserRole.ADMIN: {"read", "write", "delete", "manage", "trade", "admin"},
            UserRole.TRADER: {"read", "write", "trade"},
            UserRole.VIEWER: {"read"},
            UserRole.GUEST: set()
        }
        return role_permissions.get(self, set())

    def can_trade(self) -> bool:
        """判断角色是否可以交易"""
        return "trade" in self.permissions

    def can_manage(self) -> bool:
        """判断角色是否可以管理"""
        return "admin" in self.permissions


class TradingPermission(Enum):
    """交易权限枚举"""
    DISABLED = "disabled"
    READ_ONLY = "read_only"
    DEMO_TRADING = "demo_trading"
    LIVE_TRADING = "live_trading"
    FULL_ACCESS = "full_access"

    def __str__(self):
        return self.value

    @property
    def can_place_orders(self) -> bool:
        """判断是否可以下单"""
        return self in [
            TradingPermission.DEMO_TRADING,
            TradingPermission.LIVE_TRADING,
            TradingPermission.FULL_ACCESS
        ]

    @property
    def can_live_trade(self) -> bool:
        """判断是否可以实盘交易"""
        return self in [
            TradingPermission.LIVE_TRADING,
            TradingPermission.FULL_ACCESS
        ]

    @property
    def risk_level(self) -> int:
        """获取风险级别（0-5）"""
        risk_levels = {
            TradingPermission.DISABLED: 0,
            TradingPermission.READ_ONLY: 1,
            TradingPermission.DEMO_TRADING: 2,
            TradingPermission.LIVE_TRADING: 4,
            TradingPermission.FULL_ACCESS: 5
        }
        return risk_levels.get(self, 0)


class UserStatus(Enum):
    """用户状态枚举"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    DELETED = "deleted"

    def __str__(self):
        return self.value

    @property
    def is_active(self) -> bool:
        """判断状态是否为活跃"""
        return self == UserStatus.ACTIVE

    @property
    def can_login(self) -> bool:
        """判断是否可以登录"""
        return self in [UserStatus.ACTIVE, UserStatus.INACTIVE]
