"""
配置管理器
==========

统一的配置管理入口，提供配置的创建、加载、验证、监控等功能。
"""

import os
import threading
from typing import Optional, Dict, Any, List, Callable
from pathlib import Path
from datetime import datetime
from loguru import logger

from .base_config import BaseConfig, ConfigRegistry, config_registry
from .environment_config import EnvironmentConfig, get_environment_config
from .unified_config import UnifiedConfig


class LegacyConfigManager:
    """配置管理器"""
    
    def __init__(self):
        self._lock = threading.RLock()
        self._config: Optional[UnifiedConfig] = None
        self._config_file_path: Optional[Path] = None
        self._watchers: List[Callable[[UnifiedConfig], None]] = []
        self._auto_reload = False
        
        # 注册配置类型
        self._register_config_types()
    
    def _register_config_types(self):
        """注册配置类型"""
        config_registry.register_config_type("environment", EnvironmentConfig)
        config_registry.register_config_type("unified", UnifiedConfig)
    
    def get_config(self) -> UnifiedConfig:
        """获取配置实例"""
        with self._lock:
            if self._config is None:
                self._config = self._create_default_config()
            return self._config
    
    def _create_default_config(self) -> UnifiedConfig:
        """创建默认配置"""
        try:
            # 尝试从环境变量文件加载
            env_files = [".env", "config.env", "config/config.env", "config/backend/config.env"]
            
            for env_file in env_files:
                if Path(env_file).exists():
                    logger.info(f"从环境文件加载配置: {env_file}")
                    self._config_file_path = Path(env_file)
                    return UnifiedConfig.from_env_file(env_file)
            
            # 如果没有环境文件，创建默认配置
            logger.info("创建默认配置")
            config = UnifiedConfig()
            
            # 创建默认环境文件
            self._create_default_env_file()
            
            return config
            
        except Exception as e:
            logger.error(f"创建配置失败: {e}")
            return UnifiedConfig()
    
    def _create_default_env_file(self):
        """创建默认环境文件"""
        env_file_path = Path(".env")
        
        if not env_file_path.exists():
            try:
                default_config = UnifiedConfig()
                default_config.export_to_env_file(str(env_file_path))
                self._config_file_path = env_file_path
                logger.info(f"已创建默认环境文件: {env_file_path}")
            except Exception as e:
                logger.error(f"创建默认环境文件失败: {e}")
    
    def set_config(self, config: UnifiedConfig):
        """设置配置实例"""
        with self._lock:
            old_config = self._config
            self._config = config
            
            # 通知监听器
            self._notify_watchers(config)
            
            logger.info("配置已更新")
    
    def reload_config(self) -> bool:
        """重新加载配置"""
        with self._lock:
            try:
                old_config = self._config
                
                if self._config_file_path and self._config_file_path.exists():
                    # 从文件重新加载
                    new_config = UnifiedConfig.from_env_file(str(self._config_file_path))
                else:
                    # 重新创建默认配置
                    new_config = self._create_default_config()
                
                self._config = new_config
                
                # 通知监听器
                self._notify_watchers(new_config)
                
                logger.info("配置重新加载成功")
                return True
                
            except Exception as e:
                logger.error(f"重新加载配置失败: {e}")
                return False
    
    def validate_config(self) -> Dict[str, Any]:
        """验证配置"""
        config = self.get_config()
        
        validation_result = {
            "valid": config.validate_config(),
            "timestamp": datetime.now().isoformat(),
            "errors": [],
            "warnings": [],
            "details": {}
        }
        
        try:
            # 详细验证
            details = {}
            
            # 验证环境配置
            env_valid = config.environment.validate_config()
            details["environment"] = env_valid
            if not env_valid:
                validation_result["errors"].append("环境配置验证失败")
            
            # 验证数据库配置
            try:
                config.database.build_connection_url()
                details["database"] = True
            except Exception as e:
                details["database"] = False
                validation_result["errors"].append(f"数据库配置错误: {e}")
            
            # 验证路径配置
            try:
                Path(config.paths.project_root).resolve()
                details["paths"] = True
            except Exception as e:
                details["paths"] = False
                validation_result["errors"].append(f"路径配置错误: {e}")
            
            # 验证端口配置
            ports = [
                config.port,
                config.services.vnpy_core_port,
                config.services.user_trading_port,
                config.services.strategy_data_port,
                config.services.gateway_port,
                config.services.monitor_port
            ]
            
            port_conflicts = []
            for i, port1 in enumerate(ports):
                for j, port2 in enumerate(ports[i+1:], i+1):
                    if port1 == port2:
                        port_conflicts.append(port1)
            
            if port_conflicts:
                details["ports"] = False
                validation_result["errors"].append(f"端口冲突: {port_conflicts}")
            else:
                details["ports"] = True
            
            validation_result["details"] = details
            validation_result["valid"] = len(validation_result["errors"]) == 0
            
        except Exception as e:
            validation_result["errors"].append(f"验证过程出错: {e}")
            validation_result["valid"] = False
        
        return validation_result
    
    def backup_config(self, backup_dir: str = "config_backups") -> Optional[Path]:
        """备份配置"""
        try:
            config = self.get_config()
            backup_path = config.create_backup(backup_dir)
            logger.info(f"配置已备份到: {backup_path}")
            return backup_path
        except Exception as e:
            logger.error(f"备份配置失败: {e}")
            return None
    
    def restore_config(self, backup_path: str) -> bool:
        """恢复配置"""
        try:
            config = self.get_config()
            if config.restore_from_backup(backup_path):
                self._notify_watchers(config)
                logger.info(f"从备份恢复配置: {backup_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"恢复配置失败: {e}")
            return False
    
    def export_config(self, file_path: str, format: str = "json") -> bool:
        """导出配置"""
        try:
            config = self.get_config()
            return config.save_to_file(file_path, format)
        except Exception as e:
            logger.error(f"导出配置失败: {e}")
            return False
    
    def import_config(self, file_path: str) -> bool:
        """导入配置"""
        try:
            new_config = UnifiedConfig.load_from_file(file_path)
            self.set_config(new_config)
            return True
        except Exception as e:
            logger.error(f"导入配置失败: {e}")
            return False
    
    def add_config_watcher(self, callback: Callable[[UnifiedConfig], None]):
        """添加配置监听器"""
        with self._lock:
            self._watchers.append(callback)
    
    def remove_config_watcher(self, callback: Callable[[UnifiedConfig], None]):
        """移除配置监听器"""
        with self._lock:
            if callback in self._watchers:
                self._watchers.remove(callback)
    
    def _notify_watchers(self, config: UnifiedConfig):
        """通知所有监听器"""
        for watcher in self._watchers:
            try:
                watcher(config)
            except Exception as e:
                logger.error(f"通知配置监听器失败: {e}")
    
    def enable_auto_reload(self, enable: bool = True):
        """启用自动重载"""
        self._auto_reload = enable
        if enable:
            logger.info("启用配置自动重载")
        else:
            logger.info("禁用配置自动重载")
    
    def get_config_summary(self) -> Dict[str, Any]:
        """获取配置摘要"""
        config = self.get_config()
        validation = self.validate_config()
        
        return {
            "config_type": "UnifiedConfig",
            "version": config.app_version,
            "environment": config.environment.environment.value,
            "validation": validation,
            "file_path": str(self._config_file_path) if self._config_file_path else None,
            "last_reload": datetime.now().isoformat(),
            "watchers_count": len(self._watchers),
            "auto_reload": self._auto_reload
        }
    
    def list_available_configs(self) -> List[str]:
        """列出可用的配置类型"""
        return config_registry.list_config_types()
    
    def create_config_instance(self, config_type: str, **kwargs) -> Optional[BaseConfig]:
        """创建配置实例"""
        return config_registry.create_config(config_type, **kwargs)


# 全局配置管理器实例
_config_manager: Optional[LegacyConfigManager] = None
_config_lock = threading.RLock()


def get_config_manager() -> LegacyConfigManager:
    """获取配置管理器实例"""
    global _config_manager
    with _config_lock:
        if _config_manager is None:
            _config_manager = LegacyConfigManager()
        return _config_manager


def get_config() -> UnifiedConfig:
    """获取配置实例"""
    return get_config_manager().get_config()


def reload_config() -> bool:
    """重新加载配置"""
    return get_config_manager().reload_config()


def validate_config() -> Dict[str, Any]:
    """验证配置"""
    return get_config_manager().validate_config()


def backup_config(backup_dir: str = "config_backups") -> Optional[Path]:
    """备份配置"""
    return get_config_manager().backup_config(backup_dir)


def export_config(file_path: str, format: str = "json") -> bool:
    """导出配置"""
    return get_config_manager().export_config(file_path, format)


def import_config(file_path: str) -> bool:
    """导入配置"""
    return get_config_manager().import_config(file_path)


def add_config_watcher(callback: Callable[[UnifiedConfig], None]):
    """添加配置监听器"""
    get_config_manager().add_config_watcher(callback)


def get_config_summary() -> Dict[str, Any]:
    """获取配置摘要"""
    return get_config_manager().get_config_summary()


# 便捷函数
def is_development() -> bool:
    """是否为开发环境"""
    return get_config().is_development()


def is_production() -> bool:
    """是否为生产环境"""
    return get_config().is_production()


def get_database_url() -> str:
    """获取数据库URL"""
    return get_config().get_database_url()


def get_service_config(service_name: str) -> Dict[str, Any]:
    """获取服务配置"""
    return get_config().get_service_config(service_name)


def get_logging_config() -> Dict[str, Any]:
    """获取日志配置"""
    return get_config().get_logging_config()


def get_security_config() -> Dict[str, Any]:
    """获取安全配置"""
    return get_config().get_security_config()
