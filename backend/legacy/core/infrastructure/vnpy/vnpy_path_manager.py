"""
VnPy路径管理器
=============

负责VnPy相关路径的检测、配置和管理
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
    vnpy_core: str
    vnpy_framework: str
    vnpy_config: str
    vnpy_data: str
    vnpy_logs: str
    project_root: str
    backend_root: str


class VnPyPathManager:
    """VnPy路径管理器"""
    
    def __init__(self):
        self.paths: Optional[VnPyPaths] = None
        self._python_paths_added = False
        
    def setup_paths(self) -> VnPyPaths:
        """
        设置VnPy相关路径，支持环境变量覆盖
        
        Returns:
            VnPy路径配置
        """
        if self.paths is not None:
            return self.paths
            
        # 路径检测 - 从backend/src/core/infrastructure/vnpy开始
        current_file = Path(__file__).resolve()
        backend_root = current_file.parents[4]  # backend目录
        project_root = backend_root.parent      # vnpy项目根目录
        
        # 默认路径配置
        paths_dict = {
            "vnpy_core": os.getenv("VNPY_CORE_PATH", str(project_root / "vnpy-core")),
            "vnpy_framework": os.getenv("VNPY_FRAMEWORK_PATH", str(project_root / "vnpy")),
            "vnpy_config": os.getenv("VNPY_CONFIG_PATH", str(project_root / "vnpy_config")),
            "vnpy_data": os.getenv("VNPY_DATA_PATH", str(project_root / "vnpy_data")),
            "vnpy_logs": os.getenv("VNPY_LOG_PATH", str(project_root / "vnpy_logs")),
            "project_root": str(project_root),
            "backend_root": str(backend_root)
        }
        
        # 创建VnPyPaths实例
        self.paths = VnPyPaths(**paths_dict)
        
        # 添加到Python路径
        self._add_to_python_path()
        
        logger.info("VnPy路径配置完成")
        return self.paths
    
    def _add_to_python_path(self):
        """将VnPy路径添加到Python路径"""
        if not self.paths or self._python_paths_added:
            return
            
        paths_to_add = [
            self.paths.vnpy_core,
            self.paths.vnpy_framework,
            self.paths.project_root,
        ]
        
        for path_value in paths_to_add:
            if path_value and Path(path_value).exists():
                if path_value not in sys.path:
                    sys.path.insert(0, path_value)
                    logger.info(f"已添加路径到Python路径: {path_value}")
            else:
                logger.warning(f"路径不存在: {path_value}")
        
        self._python_paths_added = True
    
    def validate_paths(self) -> Dict[str, bool]:
        """
        验证VnPy路径是否有效
        
        Returns:
            路径验证结果
        """
        if not self.paths:
            return {}
            
        validation_results = {}
        
        for field_name in self.paths.__dataclass_fields__:
            path_value = getattr(self.paths, field_name)
            validation_results[field_name] = Path(path_value).exists() if path_value else False
            
        return validation_results
    
    def get_path(self, path_type: str) -> Optional[str]:
        """
        获取指定类型的路径
        
        Args:
            path_type: 路径类型
            
        Returns:
            路径字符串或None
        """
        if not self.paths:
            self.setup_paths()
        
        return getattr(self.paths, path_type, None)
    
    def create_required_directories(self) -> Dict[str, bool]:
        """
        创建必需的目录
        
        Returns:
            目录创建结果
        """
        if not self.paths:
            return {}
            
        creation_results = {}
        
        # 需要创建的目录
        dirs_to_create = [
            self.paths.vnpy_config,
            self.paths.vnpy_data,
            self.paths.vnpy_logs
        ]
        
        for dir_path in dirs_to_create:
            try:
                Path(dir_path).mkdir(parents=True, exist_ok=True)
                creation_results[dir_path] = True
                logger.info(f"目录创建成功: {dir_path}")
            except Exception as e:
                creation_results[dir_path] = False
                logger.error(f"目录创建失败 {dir_path}: {e}")
                
        return creation_results
    
    def get_path_info(self) -> Dict[str, Any]:
        """
        获取路径信息总览
        
        Returns:
            路径信息字典
        """
        if not self.paths:
            return {}
            
        validation_results = self.validate_paths()
        
        return {
            "paths": self.paths.__dict__,
            "validation": validation_results,
            "python_paths_added": self._python_paths_added,
            "summary": {
                "total_paths": len(validation_results),
                "valid_paths": sum(validation_results.values()),
                "invalid_paths": len(validation_results) - sum(validation_results.values())
            }
        }


# 全局路径管理器实例
_path_manager: Optional[VnPyPathManager] = None


def get_path_manager() -> VnPyPathManager:
    """获取全局路径管理器实例"""
    global _path_manager
    if _path_manager is None:
        _path_manager = VnPyPathManager()
    return _path_manager


def get_vnpy_path(path_type: str = "vnpy_core") -> Optional[str]:
    """获取VnPy路径"""
    return get_path_manager().get_path(path_type)


def setup_vnpy_paths() -> VnPyPaths:
    """设置VnPy路径"""
    return get_path_manager().setup_paths()

