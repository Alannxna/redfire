"""
VnPy集成配置模块

管理VnPy系统的路径和集成配置
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class VnPyPaths:
    """VnPy路径配置"""
    project_root: str
    vnpy_core_path: Optional[str] = None
    vnpy_path: Optional[str] = None
    config_path: Optional[str] = None
    data_path: Optional[str] = None
    log_path: Optional[str] = None


class VnPyIntegrationConfig:
    """VnPy集成配置管理器"""
    
    def __init__(self):
        self.paths = None
        self._setup_completed = False
    
    def setup_paths(self) -> VnPyPaths:
        """设置VnPy路径"""
        if self.paths is not None:
            return self.paths
        
        logger.info("开始设置VnPy路径...")
        
        # 获取项目根路径
        project_root = str(Path.cwd())
        
        # 初始化路径配置
        self.paths = VnPyPaths(project_root=project_root)
        
        # 设置VnPy核心路径
        self.paths.vnpy_core_path = self._find_vnpy_core_path()
        
        # 设置VnPy主路径
        self.paths.vnpy_path = self._find_vnpy_path()
        
        # 设置配置路径
        self.paths.config_path = self._find_config_path()
        
        # 设置数据路径
        self.paths.data_path = self._get_data_path()
        
        # 设置日志路径
        self.paths.log_path = self._get_log_path()
        
        # 添加到Python路径
        self._add_to_python_path()
        
        logger.info(f"VnPy路径设置完成: {self.paths}")
        return self.paths
    
    def _find_vnpy_core_path(self) -> Optional[str]:
        """查找vnpy-core路径"""
        # 检查环境变量
        vnpy_core_path = os.getenv("VNPY_CORE_PATH")
        if vnpy_core_path and Path(vnpy_core_path).exists():
            logger.info(f"从环境变量获取vnpy-core路径: {vnpy_core_path}")
            return str(Path(vnpy_core_path).resolve())
        
        # 自动检测路径
        possible_paths = [
            "../vnpy-core",
            "../../vnpy-core",
            "./vnpy-core",
            "../vnpy/vnpy",
            "../../vnpy/vnpy",
            "./vnpy/vnpy"
        ]
        
        for path in possible_paths:
            test_path = Path(path).resolve()
            # 检查是否是vnpy-core目录（包含__init__.py或特定文件）
            if test_path.exists() and (
                (test_path / "__init__.py").exists() or
                (test_path / "trader" / "__init__.py").exists() or
                (test_path / "app").exists()
            ):
                logger.info(f"自动检测到vnpy-core路径: {test_path}")
                return str(test_path)
        
        logger.warning("未找到vnpy-core路径")
        return None
    
    def _find_vnpy_path(self) -> Optional[str]:
        """查找vnpy主路径"""
        # 检查环境变量
        vnpy_path = os.getenv("VNPY_PATH")
        if vnpy_path and Path(vnpy_path).exists():
            logger.info(f"从环境变量获取vnpy路径: {vnpy_path}")
            return str(Path(vnpy_path).resolve())
        
        # 如果有vnpy-core路径，尝试推导vnpy路径
        if self.paths.vnpy_core_path:
            vnpy_core_parent = Path(self.paths.vnpy_core_path).parent
            possible_vnpy_paths = [
                vnpy_core_parent / "vnpy",
                vnpy_core_parent
            ]
            
            for path in possible_vnpy_paths:
                if path.exists() and (path / "__init__.py").exists():
                    logger.info(f"从vnpy-core推导vnpy路径: {path}")
                    return str(path)
        
        # 自动检测路径
        possible_paths = [
            "../vnpy",
            "../../vnpy",
            "./vnpy"
        ]
        
        for path in possible_paths:
            test_path = Path(path).resolve()
            if test_path.exists() and (test_path / "__init__.py").exists():
                logger.info(f"自动检测到vnpy路径: {test_path}")
                return str(test_path)
        
        logger.warning("未找到vnpy路径")
        return None
    
    def _find_config_path(self) -> Optional[str]:
        """查找配置路径"""
        possible_paths = [
            "./config",
            "../config",
            "../../config",
            self.paths.project_root + "/config"
        ]
        
        for path in possible_paths:
            config_path = Path(path)
            if config_path.exists() and config_path.is_dir():
                logger.info(f"找到配置路径: {config_path.resolve()}")
                return str(config_path.resolve())
        
        # 创建默认配置目录
        default_config = Path(self.paths.project_root) / "config"
        default_config.mkdir(exist_ok=True)
        logger.info(f"创建默认配置路径: {default_config}")
        return str(default_config)
    
    def _get_data_path(self) -> str:
        """获取数据路径"""
        data_path = Path(self.paths.project_root) / "data"
        data_path.mkdir(exist_ok=True)
        return str(data_path)
    
    def _get_log_path(self) -> str:
        """获取日志路径"""
        log_path = Path(self.paths.project_root) / "logs"
        log_path.mkdir(exist_ok=True)
        return str(log_path)
    
    def _add_to_python_path(self):
        """添加路径到Python搜索路径"""
        paths_to_add = []
        
        if self.paths.vnpy_core_path:
            paths_to_add.append(self.paths.vnpy_core_path)
        
        if self.paths.vnpy_path:
            paths_to_add.append(self.paths.vnpy_path)
        
        # 添加配置路径的父目录
        if self.paths.config_path:
            config_parent = str(Path(self.paths.config_path).parent)
            paths_to_add.append(config_parent)
        
        for path in paths_to_add:
            if path not in sys.path:
                sys.path.insert(0, path)
                logger.debug(f"添加到Python路径: {path}")
    
    def is_vnpy_available(self) -> bool:
        """检查VnPy是否可用"""
        try:
            if self.paths.vnpy_core_path:
                vnpy_trader_path = Path(self.paths.vnpy_core_path) / "trader"
                if vnpy_trader_path.exists():
                    return True
            
            # 尝试导入vnpy
            import vnpy
            return True
        except ImportError:
            return False
    
    def get_vnpy_version(self) -> Optional[str]:
        """获取VnPy版本"""
        try:
            import vnpy
            return getattr(vnpy, '__version__', 'unknown')
        except ImportError:
            return None
    
    def get_paths_dict(self) -> Dict[str, Any]:
        """获取路径配置字典"""
        if not self.paths:
            self.setup_paths()
        
        return {
            'project_root': self.paths.project_root,
            'vnpy_core_path': self.paths.vnpy_core_path,
            'vnpy_path': self.paths.vnpy_path,
            'config_path': self.paths.config_path,
            'data_path': self.paths.data_path,
            'log_path': self.paths.log_path,
            'vnpy_available': self.is_vnpy_available(),
            'vnpy_version': self.get_vnpy_version()
        }
    
    def validate_paths(self) -> List[str]:
        """验证路径配置，返回错误列表"""
        errors = []
        
        if not self.paths:
            errors.append("路径配置未初始化")
            return errors
        
        # 检查项目根路径
        if not Path(self.paths.project_root).exists():
            errors.append(f"项目根路径不存在: {self.paths.project_root}")
        
        # 检查VnPy路径（可选）
        if self.paths.vnpy_core_path and not Path(self.paths.vnpy_core_path).exists():
            errors.append(f"VnPy核心路径不存在: {self.paths.vnpy_core_path}")
        
        if self.paths.vnpy_path and not Path(self.paths.vnpy_path).exists():
            errors.append(f"VnPy路径不存在: {self.paths.vnpy_path}")
        
        # 检查配置路径
        if self.paths.config_path and not Path(self.paths.config_path).exists():
            errors.append(f"配置路径不存在: {self.paths.config_path}")
        
        return errors


# 全局VnPy集成配置实例
_vnpy_integration_config: Optional[VnPyIntegrationConfig] = None


def get_vnpy_integration_config() -> VnPyIntegrationConfig:
    """获取全局VnPy集成配置实例"""
    global _vnpy_integration_config
    if _vnpy_integration_config is None:
        _vnpy_integration_config = VnPyIntegrationConfig()
    return _vnpy_integration_config


def setup_vnpy_paths() -> VnPyPaths:
    """设置VnPy路径的便捷函数"""
    return get_vnpy_integration_config().setup_paths()


def is_vnpy_available() -> bool:
    """检查VnPy是否可用的便捷函数"""
    return get_vnpy_integration_config().is_vnpy_available()


def get_vnpy_path(path_type: str = "vnpy_core") -> Optional[str]:
    """获取指定类型的VnPy路径"""
    config = get_vnpy_integration_config()
    paths = config.setup_paths()
    
    if path_type == "vnpy_core":
        return paths.vnpy_core_path
    elif path_type == "vnpy":
        return paths.vnpy_path
    elif path_type == "config":
        return paths.config_path
    elif path_type == "data":
        return paths.data_path
    elif path_type == "log":
        return paths.log_path
    elif path_type == "project_root":
        return paths.project_root
    else:
        return None
