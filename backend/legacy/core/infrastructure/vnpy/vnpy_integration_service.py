"""
VnPy集成服务
===========

基于Backend DDD架构的VnPy集成基础设施服务
"""

import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass, field

from ...base.infrastructure_service import BaseInfrastructureService, InfrastructureServiceConfig
from .vnpy_path_manager import VnPyPathManager, VnPyPaths
from .vnpy_config_loader import VnPyConfigLoader

logger = logging.getLogger(__name__)


@dataclass
class VnPyIntegrationConfig(InfrastructureServiceConfig):
    """VnPy集成服务配置"""
    service_name: str = "vnpy_integration"
    service_description: str = "VnPy核心引擎集成服务"
    
    # VnPy特定配置
    auto_setup_paths: bool = True
    auto_load_configs: bool = True
    vnpy_availability_check: bool = True
    fallback_enabled: bool = True
    
    # 路径覆盖配置
    path_overrides: Dict[str, str] = field(default_factory=dict)
    
    def __post_init__(self):
        super().__post_init__()


class VnPyIntegrationService(BaseInfrastructureService):
    """
    VnPy集成基础设施服务
    
    提供VnPy核心功能的集成支持：
    1. 路径管理和环境配置
    2. 配置加载和验证
    3. VnPy可用性检测
    4. 降级处理机制
    """
    
    def __init__(self, config: VnPyIntegrationConfig):
        super().__init__(config)
        self.vnpy_config = config
        
        # 核心组件
        self.path_manager = VnPyPathManager()
        self.config_loader = VnPyConfigLoader()
        
        # 状态管理
        self._vnpy_available: Optional[bool] = None
        self._integrated_config: Optional[Dict[str, Any]] = None
        self._setup_complete = False
        
        logger.info(f"VnPy集成服务初始化: {config.service_name}")
    
    async def start_service(self):
        """启动VnPy集成服务"""
        try:
            logger.info("VnPy集成服务启动中...")
            
            # 1. 设置路径
            if self.vnpy_config.auto_setup_paths:
                await self._setup_paths()
            
            # 2. 加载配置
            if self.vnpy_config.auto_load_configs:
                await self._load_configurations()
            
            # 3. 检查VnPy可用性
            if self.vnpy_config.vnpy_availability_check:
                await self._check_vnpy_availability()
            
            # 4. 创建集成配置
            await self._create_integrated_config()
            
            self._setup_complete = True
            await self.publish_service_event("service_started", {
                "vnpy_available": self._vnpy_available,
                "paths_configured": self.path_manager.paths is not None,
                "config_loaded": self._integrated_config is not None
            })
            
            logger.info("VnPy集成服务启动完成")
            
        except Exception as e:
            logger.error(f"VnPy集成服务启动失败: {e}")
            await self.handle_service_error("startup_failed", e)
            raise
    
    async def stop_service(self):
        """停止VnPy集成服务"""
        logger.info("VnPy集成服务停止中...")
        
        # 清理资源
        self._integrated_config = None
        self._setup_complete = False
        
        await self.publish_service_event("service_stopped", {})
        logger.info("VnPy集成服务已停止")
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        health_status = await super().health_check()
        
        # VnPy特定健康检查
        health_status.update({
            "vnpy_available": self._vnpy_available,
            "paths_configured": self.path_manager.paths is not None,
            "config_loaded": self._integrated_config is not None,
            "setup_complete": self._setup_complete
        })
        
        return health_status
    
    async def _setup_paths(self):
        """设置VnPy路径"""
        try:
            # 应用路径覆盖
            if self.vnpy_config.path_overrides:
                self._apply_path_overrides()
            
            # 设置路径
            paths = self.path_manager.setup_paths()
            
            # 创建必需目录
            creation_results = self.path_manager.create_required_directories()
            
            logger.info("VnPy路径设置完成")
            logger.debug(f"路径信息: {self.path_manager.get_path_info()}")
            
        except Exception as e:
            logger.error(f"VnPy路径设置失败: {e}")
            raise
    
    def _apply_path_overrides(self):
        """应用路径覆盖配置"""
        import os
        
        for path_type, path_value in self.vnpy_config.path_overrides.items():
            env_var_name = f"VNPY_{path_type.upper()}_PATH"
            os.environ[env_var_name] = path_value
            logger.info(f"应用路径覆盖: {env_var_name}={path_value}")
    
    async def _load_configurations(self):
        """加载配置"""
        try:
            # 加载Legacy配置
            legacy_config = self.config_loader.load_legacy_config()
            
            # 加载VnPy设置
            vt_setting = self.config_loader.load_vt_setting()
            
            logger.info("VnPy配置加载完成")
            
        except Exception as e:
            logger.error(f"VnPy配置加载失败: {e}")
            raise
    
    async def _check_vnpy_availability(self):
        """检查VnPy可用性"""
        try:
            # 检查路径
            if not self.path_manager.paths:
                self._vnpy_available = False
                return
            
            paths = self.path_manager.paths
            validation_results = self.path_manager.validate_paths()
            
            # 检查关键路径
            if not validation_results.get('vnpy_core', False):
                logger.warning("VnPy核心路径不存在")
                self._vnpy_available = False
                return
            
            # 尝试导入VnPy模块
            try:
                from vnpy.event import EventEngine
                from vnpy.trader.engine import MainEngine
                self._vnpy_available = True
                logger.info("VnPy模块导入成功，VnPy可用")
                
            except ImportError as e:
                logger.warning(f"VnPy模块导入失败: {e}")
                self._vnpy_available = False
                
        except Exception as e:
            logger.error(f"VnPy可用性检查失败: {e}")
            self._vnpy_available = False
    
    async def _create_integrated_config(self):
        """创建集成配置"""
        try:
            if self._vnpy_available:
                # VnPy可用，创建完整配置
                self._integrated_config = self.config_loader.create_integrated_config()
                self._integrated_config['vnpy_available'] = True
                
            else:
                # VnPy不可用，使用降级配置
                if self.vnpy_config.fallback_enabled:
                    self._integrated_config = self.config_loader.get_fallback_config()
                    logger.warning("VnPy不可用，使用降级配置")
                else:
                    raise RuntimeError("VnPy不可用且未启用降级模式")
            
            logger.info("VnPy集成配置创建完成")
            
        except Exception as e:
            logger.error(f"VnPy集成配置创建失败: {e}")
            raise
    
    # 公共接口方法
    
    def get_vnpy_paths(self) -> Optional[VnPyPaths]:
        """获取VnPy路径配置"""
        return self.path_manager.paths
    
    def get_vnpy_path(self, path_type: str) -> Optional[str]:
        """获取指定类型的VnPy路径"""
        return self.path_manager.get_path(path_type)
    
    def is_vnpy_available(self) -> bool:
        """检查VnPy是否可用"""
        return self._vnpy_available if self._vnpy_available is not None else False
    
    def get_integrated_config(self) -> Optional[Dict[str, Any]]:
        """获取集成配置"""
        return self._integrated_config
    
    def get_config_by_type(self, config_type: str) -> Dict[str, Any]:
        """获取指定类型的配置"""
        return self.config_loader.get_config(config_type)
    
    def validate_vnpy_environment(self) -> Dict[str, Any]:
        """验证VnPy环境"""
        validation_result = {
            "vnpy_available": self.is_vnpy_available(),
            "paths_valid": False,
            "config_loaded": self._integrated_config is not None,
            "setup_complete": self._setup_complete,
            "details": {}
        }
        
        if self.path_manager.paths:
            path_validation = self.path_manager.validate_paths()
            validation_result["paths_valid"] = all(path_validation.values())
            validation_result["details"]["path_validation"] = path_validation
            validation_result["details"]["path_info"] = self.path_manager.get_path_info()
        
        return validation_result
    
    async def reload_configuration(self) -> bool:
        """重新加载配置"""
        try:
            logger.info("重新加载VnPy配置...")
            
            # 重新加载配置
            await self._load_configurations()
            await self._create_integrated_config()
            
            await self.publish_service_event("config_reloaded", {
                "success": True,
                "vnpy_available": self._vnpy_available
            })
            
            logger.info("VnPy配置重新加载完成")
            return True
            
        except Exception as e:
            logger.error(f"VnPy配置重新加载失败: {e}")
            await self.handle_service_error("config_reload_failed", e)
            return False
    
    def get_service_info(self) -> Dict[str, Any]:
        """获取服务信息"""
        base_info = super().get_service_info()
        
        vnpy_info = {
            "vnpy_available": self.is_vnpy_available(),
            "setup_complete": self._setup_complete,
            "paths_configured": self.path_manager.paths is not None,
            "config_loaded": self._integrated_config is not None
        }
        
        if self.path_manager.paths:
            vnpy_info["path_summary"] = self.path_manager.get_path_info()["summary"]
        
        base_info.update(vnpy_info)
        return base_info


# 全局服务实例
_vnpy_integration_service: Optional[VnPyIntegrationService] = None


def get_vnpy_integration_service() -> Optional[VnPyIntegrationService]:
    """获取全局VnPy集成服务实例"""
    return _vnpy_integration_service


def create_vnpy_integration_service(config: Optional[VnPyIntegrationConfig] = None) -> VnPyIntegrationService:
    """创建VnPy集成服务"""
    global _vnpy_integration_service
    
    if config is None:
        config = VnPyIntegrationConfig()
    
    _vnpy_integration_service = VnPyIntegrationService(config)
    return _vnpy_integration_service


async def setup_vnpy_integration(config: Optional[VnPyIntegrationConfig] = None) -> VnPyIntegrationService:
    """设置VnPy集成"""
    service = create_vnpy_integration_service(config)
    await service.start_service()
    return service

