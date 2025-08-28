"""
服务路由器
=========

处理API路径到服务的路由映射
"""

import re
import logging
from typing import Dict, List, Optional, Pattern
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class RouteRule:
    """路由规则"""
    pattern: Pattern[str]
    service_name: str
    path_rewrite: Optional[str] = None
    strip_prefix: bool = True
    priority: int = 0
    
    def matches(self, path: str) -> bool:
        """检查路径是否匹配"""
        return bool(self.pattern.match(path))
    
    def rewrite_path(self, path: str) -> str:
        """重写路径"""
        if self.path_rewrite:
            return self.pattern.sub(self.path_rewrite, path)
        elif self.strip_prefix:
            # 移除匹配的前缀
            match = self.pattern.match(path)
            if match:
                # 获取前缀长度
                prefix_end = match.end()
                return path[prefix_end:] or "/"
        return path


class ServiceRouter:
    """服务路由器"""
    
    def __init__(self, service_registry=None):
        self.service_registry = service_registry
        self.routes: List[RouteRule] = []
        
        # 添加默认路由规则
        self._setup_default_routes()
    
    def _setup_default_routes(self):
        """设置默认路由规则"""
        default_routes = [
            # 用户服务
            ("/api/v1/auth/.*", "user_service"),
            ("/api/v1/users/.*", "user_service"),
            
            # 策略服务
            ("/api/v1/strategies/.*", "strategy_service"),
            
            # 数据服务
            ("/api/v1/data/.*", "data_service"),
            ("/api/v1/market/.*", "data_service"),
            
            # 网关适配服务
            ("/api/v1/gateway/.*", "gateway_service"),
            
            # VnPy服务
            ("/api/v1/vnpy/.*", "vnpy_service"),
            ("/api/v1/trading/.*", "vnpy_service"),
            
            # 监控服务
            ("/api/v1/monitoring/.*", "monitoring_service"),
            ("/api/v1/alerts/.*", "monitoring_service"),
        ]
        
        for pattern, service in default_routes:
            self.add_route(pattern, service)
    
    def add_route(self, pattern: str, service_name: str, 
                  path_rewrite: Optional[str] = None,
                  strip_prefix: bool = True,
                  priority: int = 0):
        """添加路由规则"""
        try:
            compiled_pattern = re.compile(pattern)
            route = RouteRule(
                pattern=compiled_pattern,
                service_name=service_name,
                path_rewrite=path_rewrite,
                strip_prefix=strip_prefix,
                priority=priority
            )
            
            # 按优先级插入
            inserted = False
            for i, existing_route in enumerate(self.routes):
                if priority > existing_route.priority:
                    self.routes.insert(i, route)
                    inserted = True
                    break
            
            if not inserted:
                self.routes.append(route)
            
            logger.info(f"添加路由规则: {pattern} -> {service_name}")
            
        except re.error as e:
            logger.error(f"无效的路由模式 {pattern}: {e}")
    
    def remove_route(self, pattern: str):
        """移除路由规则"""
        self.routes = [r for r in self.routes if r.pattern.pattern != pattern]
        logger.info(f"移除路由规则: {pattern}")
    
    def get_service_name(self, path: str) -> Optional[str]:
        """根据路径获取服务名"""
        for route in self.routes:
            if route.matches(path):
                logger.debug(f"路径 {path} 匹配服务 {route.service_name}")
                return route.service_name
        
        logger.warning(f"路径 {path} 没有匹配的服务")
        return None
    
    def get_route_info(self, path: str) -> Optional[RouteRule]:
        """获取路由信息"""
        for route in self.routes:
            if route.matches(path):
                return route
        return None
    
    def rewrite_path(self, path: str) -> str:
        """重写路径"""
        route = self.get_route_info(path)
        if route:
            return route.rewrite_path(path)
        return path
    
    def list_routes(self) -> List[Dict[str, any]]:
        """列出所有路由规则"""
        return [
            {
                "pattern": route.pattern.pattern,
                "service_name": route.service_name,
                "path_rewrite": route.path_rewrite,
                "strip_prefix": route.strip_prefix,
                "priority": route.priority
            }
            for route in self.routes
        ]
    
    def add_service_routes(self, service_name: str, path_prefixes: List[str]):
        """批量添加服务路由"""
        for prefix in path_prefixes:
            pattern = f"{prefix}/.*" if not prefix.endswith("/.*") else prefix
            self.add_route(pattern, service_name)
    
    def update_from_registry(self):
        """从服务注册中心更新路由"""
        if not self.service_registry:
            return
        
        # 这里可以实现从服务注册中心动态更新路由规则的逻辑
        # 例如服务注册时自动添加路由规则
        pass
