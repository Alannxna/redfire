"""
UI领域服务

提供UI系统的核心业务逻辑
"""

import logging
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta

from src.domain.ui.entities.ui_entity import (
    UIComponent, UIEvent, UILogEntry, UISession, UIAlert, UIState,
    UIComponentType, UIEventType, LogLevel, AlertLevel
)

logger = logging.getLogger(__name__)


class UIComponentValidationService:
    """UI组件验证服务"""
    
    def validate_component_config(self, component_type: UIComponentType, config: Dict[str, Any]) -> tuple[bool, List[str]]:
        """验证组件配置"""
        errors = []
        
        # 基础验证
        if not isinstance(config, dict):
            errors.append("配置必须是字典类型")
            return False, errors
        
        # 根据组件类型进行特定验证
        if component_type == UIComponentType.TRADING_PANEL:
            errors.extend(self._validate_trading_panel_config(config))
        elif component_type == UIComponentType.CHART_PANEL:
            errors.extend(self._validate_chart_panel_config(config))
        elif component_type == UIComponentType.MARKET_DATA_PANEL:
            errors.extend(self._validate_market_data_panel_config(config))
        
        return len(errors) == 0, errors
    
    def _validate_trading_panel_config(self, config: Dict[str, Any]) -> List[str]:
        """验证交易面板配置"""
        errors = []
        
        # 检查符号列表
        if "symbols" in config:
            symbols = config["symbols"]
            if not isinstance(symbols, list):
                errors.append("symbols必须是列表类型")
            elif not symbols:
                errors.append("symbols列表不能为空")
        
        # 检查默认订单类型
        if "default_order_type" in config:
            valid_types = ["limit", "market", "stop", "stop_limit"]
            if config["default_order_type"] not in valid_types:
                errors.append(f"default_order_type必须是以下之一: {valid_types}")
        
        return errors
    
    def _validate_chart_panel_config(self, config: Dict[str, Any]) -> List[str]:
        """验证图表面板配置"""
        errors = []
        
        # 检查图表类型
        if "chart_type" in config:
            valid_types = ["candlestick", "line", "bar", "volume"]
            if config["chart_type"] not in valid_types:
                errors.append(f"chart_type必须是以下之一: {valid_types}")
        
        # 检查时间周期
        if "timeframe" in config:
            valid_timeframes = ["1m", "5m", "15m", "30m", "1h", "4h", "1d"]
            if config["timeframe"] not in valid_timeframes:
                errors.append(f"timeframe必须是以下之一: {valid_timeframes}")
        
        return errors
    
    def _validate_market_data_panel_config(self, config: Dict[str, Any]) -> List[str]:
        """验证行情面板配置"""
        errors = []
        
        # 检查订阅列表
        if "subscriptions" in config:
            subscriptions = config["subscriptions"]
            if not isinstance(subscriptions, list):
                errors.append("subscriptions必须是列表类型")
        
        return errors


class UILayoutService:
    """UI布局服务"""
    
    def __init__(self):
        self.default_layouts = {
            "trading": self._get_default_trading_layout(),
            "analysis": self._get_default_analysis_layout(),
            "monitoring": self._get_default_monitoring_layout()
        }
    
    def get_default_layout(self, layout_name: str) -> Dict[str, Any]:
        """获取默认布局"""
        return self.default_layouts.get(layout_name, {})
    
    def validate_layout(self, layout_config: Dict[str, Any]) -> tuple[bool, List[str]]:
        """验证布局配置"""
        errors = []
        
        if not isinstance(layout_config, dict):
            errors.append("布局配置必须是字典类型")
            return False, errors
        
        # 检查必需字段
        required_fields = ["name", "components"]
        for field in required_fields:
            if field not in layout_config:
                errors.append(f"缺少必需字段: {field}")
        
        # 验证组件配置
        if "components" in layout_config:
            components = layout_config["components"]
            if not isinstance(components, list):
                errors.append("components必须是列表类型")
            else:
                for i, component in enumerate(components):
                    component_errors = self._validate_layout_component(component)
                    for error in component_errors:
                        errors.append(f"组件{i}: {error}")
        
        return len(errors) == 0, errors
    
    def _validate_layout_component(self, component: Dict[str, Any]) -> List[str]:
        """验证布局组件"""
        errors = []
        
        required_fields = ["type", "position", "size"]
        for field in required_fields:
            if field not in component:
                errors.append(f"缺少必需字段: {field}")
        
        # 验证位置
        if "position" in component:
            position = component["position"]
            if not isinstance(position, dict) or "x" not in position or "y" not in position:
                errors.append("position必须包含x和y坐标")
        
        # 验证尺寸
        if "size" in component:
            size = component["size"]
            if not isinstance(size, dict) or "width" not in size or "height" not in size:
                errors.append("size必须包含width和height")
        
        return errors
    
    def _get_default_trading_layout(self) -> Dict[str, Any]:
        """获取默认交易布局"""
        return {
            "name": "trading",
            "description": "交易布局",
            "components": [
                {
                    "type": "trading_panel",
                    "position": {"x": 0, "y": 0},
                    "size": {"width": 400, "height": 300}
                },
                {
                    "type": "order_panel",
                    "position": {"x": 400, "y": 0},
                    "size": {"width": 400, "height": 300}
                },
                {
                    "type": "position_panel",
                    "position": {"x": 0, "y": 300},
                    "size": {"width": 400, "height": 300}
                },
                {
                    "type": "market_data_panel",
                    "position": {"x": 400, "y": 300},
                    "size": {"width": 400, "height": 300}
                }
            ]
        }
    
    def _get_default_analysis_layout(self) -> Dict[str, Any]:
        """获取默认分析布局"""
        return {
            "name": "analysis",
            "description": "分析布局",
            "components": [
                {
                    "type": "chart_panel",
                    "position": {"x": 0, "y": 0},
                    "size": {"width": 800, "height": 400}
                },
                {
                    "type": "strategy_panel",
                    "position": {"x": 0, "y": 400},
                    "size": {"width": 400, "height": 300}
                },
                {
                    "type": "risk_panel",
                    "position": {"x": 400, "y": 400},
                    "size": {"width": 400, "height": 300}
                }
            ]
        }
    
    def _get_default_monitoring_layout(self) -> Dict[str, Any]:
        """获取默认监控布局"""
        return {
            "name": "monitoring",
            "description": "监控布局",
            "components": [
                {
                    "type": "portfolio_panel",
                    "position": {"x": 0, "y": 0},
                    "size": {"width": 400, "height": 300}
                },
                {
                    "type": "log_panel",
                    "position": {"x": 400, "y": 0},
                    "size": {"width": 400, "height": 300}
                },
                {
                    "type": "risk_panel",
                    "position": {"x": 0, "y": 300},
                    "size": {"width": 800, "height": 300}
                }
            ]
        }


class UIEventProcessingService:
    """UI事件处理服务"""
    
    def __init__(self):
        self.event_handlers: Dict[UIEventType, List[Callable]] = {}
    
    def register_handler(self, event_type: UIEventType, handler: Callable[[UIEvent], None]):
        """注册事件处理器"""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)
    
    def unregister_handler(self, event_type: UIEventType, handler: Callable[[UIEvent], None]):
        """注销事件处理器"""
        if event_type in self.event_handlers:
            if handler in self.event_handlers[event_type]:
                self.event_handlers[event_type].remove(handler)
    
    async def process_event(self, event: UIEvent) -> bool:
        """处理事件"""
        try:
            if event.event_type in self.event_handlers:
                for handler in self.event_handlers[event.event_type]:
                    try:
                        await handler(event) if asyncio.iscoroutinefunction(handler) else handler(event)
                    except Exception as e:
                        logger.error(f"事件处理器执行失败: {e}")
            
            return True
        except Exception as e:
            logger.error(f"事件处理失败: {e}")
            return False
    
    def validate_event_data(self, event_type: UIEventType, data: Dict[str, Any]) -> tuple[bool, List[str]]:
        """验证事件数据"""
        errors = []
        
        if not isinstance(data, dict):
            errors.append("事件数据必须是字典类型")
            return False, errors
        
        # 根据事件类型进行特定验证
        if event_type == UIEventType.USER_ACTION:
            if "action" not in data:
                errors.append("用户操作事件必须包含action字段")
        elif event_type == UIEventType.DATA_UPDATED:
            if "data_type" not in data:
                errors.append("数据更新事件必须包含data_type字段")
        
        return len(errors) == 0, errors


class UIPermissionService:
    """UI权限服务"""
    
    def __init__(self):
        self.component_permissions = {
            UIComponentType.TRADING_PANEL: ["trading"],
            UIComponentType.STRATEGY_PANEL: ["strategy_management"],
            UIComponentType.RISK_PANEL: ["risk_management"],
            UIComponentType.PORTFOLIO_PANEL: ["portfolio_view"],
            UIComponentType.ORDER_PANEL: ["order_view"],
            UIComponentType.POSITION_PANEL: ["position_view"],
            UIComponentType.MARKET_DATA_PANEL: ["market_data"],
            UIComponentType.LOG_PANEL: ["log_view"],
            UIComponentType.CHART_PANEL: ["chart_view"]
        }
    
    def can_access_component(self, user_permissions: List[str], component_type: UIComponentType) -> bool:
        """检查用户是否能访问组件"""
        required_permissions = self.component_permissions.get(component_type, [])
        
        if not required_permissions:
            return True  # 无权限要求的组件
        
        return any(perm in user_permissions for perm in required_permissions)
    
    def filter_accessible_components(
        self,
        user_permissions: List[str],
        components: List[UIComponent]
    ) -> List[UIComponent]:
        """过滤用户可访问的组件"""
        accessible_components = []
        
        for component in components:
            if self.can_access_component(user_permissions, component.component_type):
                accessible_components.append(component)
        
        return accessible_components
    
    def can_perform_action(self, user_permissions: List[str], action: str) -> bool:
        """检查用户是否能执行操作"""
        action_permissions = {
            "create_order": ["trading"],
            "cancel_order": ["trading"],
            "modify_strategy": ["strategy_management"],
            "view_positions": ["portfolio_view"],
            "manage_risks": ["risk_management"]
        }
        
        required_permissions = action_permissions.get(action, [])
        
        if not required_permissions:
            return True  # 无权限要求的操作
        
        return any(perm in user_permissions for perm in required_permissions)


class UISessionManagementService:
    """UI会话管理服务"""
    
    def __init__(self):
        self.session_timeout_minutes = 30
        self.max_sessions_per_user = 5
    
    def validate_session(self, session: UISession) -> bool:
        """验证会话有效性"""
        if not session.is_active:
            return False
        
        if session.is_expired(self.session_timeout_minutes):
            return False
        
        return True
    
    def should_cleanup_session(self, session: UISession) -> bool:
        """判断是否应该清理会话"""
        return session.is_expired(self.session_timeout_minutes) or not session.is_active
    
    def can_create_new_session(self, user_id: str, existing_sessions: List[UISession]) -> bool:
        """判断是否可以创建新会话"""
        active_sessions = [s for s in existing_sessions if s.is_active and not s.is_expired()]
        return len(active_sessions) < self.max_sessions_per_user
