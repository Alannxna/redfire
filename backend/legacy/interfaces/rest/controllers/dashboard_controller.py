"""
仪表盘控制器
==============

处理系统监控和服务状态相关的HTTP请求
"""

import psutil
import socket
import requests
from datetime import datetime
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, status, Request
from fastapi.responses import HTMLResponse
import logging
import os

from ..models.common import APIResponse
from ..models.dashboard_models import (
    SystemInfoResponse, ServiceStatusResponse, ServiceHealthResponse,
    DashboardOverviewResponse, ServiceConfigModel
)
from ....application.services.dashboard_application_service import DashboardApplicationService
from ....core.infrastructure.service_registry import get_service_registry


class DashboardController:
    """仪表盘控制器"""
    
    def __init__(self):
        self.router = APIRouter()
        self._logger = logging.getLogger(self.__class__.__name__)
        
        # 创建仪表盘应用服务
        self._dashboard_service = DashboardApplicationService()
        
        # 服务配置
        self._services_config = {
            'vnpy_backend': {
                'name': 'VnPy后端API',
                'port': 8000,
                'description': 'FastAPI后端服务 - DDD架构',
                'health_check': 'http://localhost:8000/health',
                'type': 'api'
            },
            'frontend': {
                'name': '前端开发服务器',
                'port': 3000,
                'description': 'Vue 3 + Element Plus + TypeScript',
                'health_check': 'http://localhost:3000',
                'type': 'web'
            },
            'vnpy_core': {
                'name': 'VnPy核心服务',
                'port': 8006,
                'description': '引擎管理 + 策略管理 + 交易引擎',
                'health_check': 'http://localhost:8006/health',
                'type': 'api'
            },
            'user_trading': {
                'name': '用户交易服务',
                'port': 8001,
                'description': '用户认证、账户管理、订单交易',
                'health_check': 'http://localhost:8001/health',
                'type': 'service'
            },
            'strategy_data': {
                'name': '策略数据服务',
                'port': 8002,
                'description': '策略管理和历史数据服务',
                'health_check': 'http://localhost:8002/health',
                'type': 'service'
            },
            'gateway': {
                'name': '网关适配服务',
                'port': 8004,
                'description': '交易网关适配服务',
                'health_check': 'http://localhost:8004/health',
                'type': 'service'
            },
            'monitor': {
                'name': '监控通知服务',
                'port': 8005,
                'description': '系统监控、告警通知',
                'health_check': 'http://localhost:8005/health',
                'type': 'service'
            }
        }
        
        # 设置路由
        self._setup_routes()
    
    def _setup_routes(self):
        """设置路由"""
        
        @self.router.get("/", response_class=HTMLResponse)
        async def dashboard_home():
            """仪表盘主页"""
            return await self._get_dashboard_html()
        
        @self.router.get("/api/overview", response_model=DashboardOverviewResponse)
        async def get_dashboard_overview():
            """获取仪表盘概览"""
            try:
                overview = await self._dashboard_service.get_dashboard_overview()
                return DashboardOverviewResponse(**overview)
            except Exception as e:
                self._logger.error(f"获取仪表盘概览失败: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="获取仪表盘概览失败"
                )
        
        @self.router.get("/api/services", response_model=List[ServiceStatusResponse])
        async def get_services_status():
            """获取所有服务状态"""
            try:
                services_status = await self._get_services_status()
                return [ServiceStatusResponse(**service) for service in services_status]
            except Exception as e:
                self._logger.error(f"获取服务状态失败: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="获取服务状态失败"
                )
        
        @self.router.get("/api/services/{service_name}/health", response_model=ServiceHealthResponse)
        async def get_service_health(service_name: str):
            """获取特定服务的健康状态"""
            try:
                if service_name not in self._services_config:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"服务 {service_name} 不存在"
                    )
                
                health = await self._check_service_health(service_name)
                return ServiceHealthResponse(**health)
            except HTTPException:
                raise
            except Exception as e:
                self._logger.error(f"获取服务健康状态失败: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="获取服务健康状态失败"
                )
        
        @self.router.get("/api/system", response_model=SystemInfoResponse)
        async def get_system_info():
            """获取系统信息"""
            try:
                system_info = await self._dashboard_service.get_system_info()
                return SystemInfoResponse(**system_info)
            except Exception as e:
                self._logger.error(f"获取系统信息失败: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="获取系统信息失败"
                )
        
        @self.router.get("/health")
        async def dashboard_health():
            """仪表盘健康检查"""
            return {
                "status": "healthy",
                "service": "dashboard",
                "timestamp": datetime.now().isoformat()
            }
    
    async def _get_dashboard_html(self) -> str:
        """获取仪表盘HTML页面"""
        # 获取当前文件的目录路径
        current_dir = os.path.dirname(__file__)
        templates_dir = os.path.join(os.path.dirname(current_dir), "templates")
        dashboard_path = os.path.join(templates_dir, "dashboard.html")
        
        try:
            with open(dashboard_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            return html_content
        except FileNotFoundError:
            return """
            <html>
                <head><title>VnPy 仪表盘</title></head>
                <body>
                    <h1>VnPy 服务监控仪表盘</h1>
                    <p>仪表盘模板文件未找到，请检查路径配置。</p>
                    <p>模板路径: """ + dashboard_path + """</p>
                    <p>API端点可用: <a href="/dashboard/api/services">/dashboard/api/services</a></p>
                </body>
            </html>
            """
    
    async def _get_services_status(self) -> List[Dict[str, Any]]:
        """获取所有服务状态"""
        services_status = []
        
        for service_id, config in self._services_config.items():
            # 检查端口状态
            port_active = self._check_port_status(config['port'])
            
            # 检查健康状态
            health_ok = False
            health_details = {}
            
            if port_active and 'health_check' in config:
                health_result = await self._check_service_health_endpoint(config['health_check'])
                health_ok = health_result['healthy']
                health_details = health_result.get('details', {})
            
            # 获取内部服务状态（如果是后端服务）
            internal_status = None
            if service_id == 'vnpy_backend':
                internal_status = await self._get_internal_service_status()
            
            service_status = {
                'service_id': service_id,
                'name': config['name'],
                'port': config['port'],
                'description': config['description'],
                'type': config['type'],
                'port_active': port_active,
                'health_ok': health_ok,
                'status': 'online' if (port_active and health_ok) else ('partial' if port_active else 'offline'),
                'last_check': datetime.now().isoformat(),
                'health_details': health_details,
                'internal_status': internal_status
            }
            
            services_status.append(service_status)
        
        return services_status
    
    def _check_port_status(self, port: int) -> bool:
        """检查端口是否在使用"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('localhost', port))
            sock.close()
            return result == 0
        except Exception:
            return False
    
    async def _check_service_health_endpoint(self, health_url: str) -> Dict[str, Any]:
        """检查服务健康状态端点"""
        try:
            response = requests.get(health_url, timeout=3)
            return {
                'healthy': response.status_code == 200,
                'details': response.json() if response.status_code == 200 else {'error': 'HTTP错误'},
                'response_time': response.elapsed.total_seconds()
            }
        except requests.exceptions.RequestException as e:
            return {
                'healthy': False,
                'details': {'error': str(e)},
                'response_time': None
            }
    
    async def _check_service_health(self, service_name: str) -> Dict[str, Any]:
        """检查特定服务健康状态"""
        config = self._services_config[service_name]
        
        port_active = self._check_port_status(config['port'])
        health_result = await self._check_service_health_endpoint(config['health_check'])
        
        return {
            'service_id': service_name,
            'name': config['name'],
            'healthy': health_result['healthy'],
            'port_active': port_active,
            'details': health_result['details'],
            'response_time': health_result['response_time'],
            'last_check': datetime.now().isoformat()
        }
    
    async def _get_internal_service_status(self) -> Optional[Dict[str, Any]]:
        """获取内部服务状态（从服务注册中心）"""
        try:
            service_registry = get_service_registry()
            if service_registry:
                return await service_registry.health_check_all()
            return None
        except Exception as e:
            self._logger.warning(f"获取内部服务状态失败: {e}")
            return None
