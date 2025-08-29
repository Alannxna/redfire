"""
VnPy Web 统一路径配置管理模块
==================================

统一管理所有的文件路径、目录路径和项目路径配置
解决路径配置分散和硬编码的问题
"""

import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass
from pydantic import BaseModel, Field


@dataclass
class PathConfig:
    """统一的路径配置类"""
    
    def __init__(self, project_root: Optional[str] = None):
        """
        初始化路径配置
        
        Args:
            project_root: 项目根目录路径，如果不提供则自动检测
        """
        # 项目根目录检测
        if project_root:
            self.project_root = Path(project_root).resolve()
        else:
            self.project_root = self._detect_project_root()
        
        # 初始化所有路径
        self._init_paths()
        
        # 确保必要目录存在
        self._ensure_directories()
    
    def _detect_project_root(self) -> Path:
        """自动检测项目根目录"""
        # 从当前文件向上查找包含backend的vnpy项目根目录
        current_path = Path(__file__).resolve()
        
        # 如果当前就在backend目录下
        if "backend" in current_path.parts:
            # 找到backend目录的索引
            backend_index = current_path.parts.index("backend")
            # 返回backend的父目录（项目根目录）
            return Path(*current_path.parts[:backend_index])
        
        # 向上查找包含backend子目录的父目录
        for parent in current_path.parents:
            if (parent / "backend").exists() and (parent / "frontend").exists():
                return parent
        
        # 如果找不到，使用当前文件的上级目录作为备选
        return current_path.parents[1]
    
    def _init_paths(self):
        """初始化所有路径配置"""
        
        # === 项目核心目录 ===
        self.vnpy_root = self.project_root  # VnPy项目根目录
        self.backend_dir = self.project_root / "backend"
        self.frontend_dir = self.project_root / "frontend"
        self.src_dir = self.backend_dir / "src"
        self.config_dir = self.backend_dir / "config"
        self.tools_dir = self.project_root / "tools"
        self.tests_dir = self.backend_dir / "tests"
        self.docs_dir = self.project_root / "docs"
        
        # === 数据目录 ===
        self.data_dir = self.backend_dir / "data"
        self.uploads_dir = self.backend_dir / "uploads"
        self.vnpy_data_dir = self.project_root / "vnpy_data"
        self.vnpy_config_dir = self.project_root / "vnpy_config"
        self.backup_dir = self.data_dir / "backup"
        
        # === 日志目录 ===
        self.logs_dir = self.project_root / "logs"
        self.backend_logs_dir = self.backend_dir / "logs"
        self.error_log = self.logs_dir / "error.log"
        self.app_log = self.logs_dir / "vnpy_web.log"
        self.service_log = self.logs_dir / "services.log"
        
        # === 数据库文件 ===
        # 注意：现在使用MySQL，这些SQLite文件路径仅供参考
        self.database_file = self.data_dir / "vnpy_web.db"
        self.test_database_file = self.data_dir / "test_vnpy_web.db"
        
        # === 配置文件 ===
        self.env_file = self.project_root / ".env"
        self.mysql_schema = self.config_dir / "mysql_schema.sql"
        
        # === API和服务相关路径 ===
        self.api_dir = self.src_dir / "api"
        self.services_dir = self.src_dir / "services"
        self.models_dir = self.src_dir / "models"
        self.database_dir = self.src_dir / "database"
        self.utils_dir = self.src_dir / "utils"
        
        # === 前端和报表路径 ===
        self.reports_dir = self.docs_dir / "reports"
        self.dashboard_dir = self.reports_dir / "04_仪表板"
        self.charts_dir = self.reports_dir / "03_图表可视化" / "charts"
        
        # === VnPy 核心框架目录 ===
        self.vnpy_framework_dir = self.project_root / "vnpy"
        
        # === 启动脚本 ===
        self.start_services_script = self.backend_dir / "run_services.py"
        self.start_all_script = self.project_root / "start_all_services.py"
        
        # === 临时文件目录 ===
        self.temp_dir = self.project_root / "temp"
        self.cache_dir = self.project_root / "cache"
    
    def _ensure_directories(self):
        """确保必要的目录存在"""
        directories_to_create = [
            self.data_dir,
            self.uploads_dir,
            self.vnpy_data_dir,
            self.backup_dir,
            self.logs_dir,
            self.temp_dir,
            self.cache_dir
        ]
        
        for directory in directories_to_create:
            directory.mkdir(parents=True, exist_ok=True)
    
    def add_to_python_path(self):
        """将项目路径添加到Python路径中"""
        paths_to_add = [
            str(self.project_root),       # VnPy项目根目录
            str(self.backend_dir),        # 后端目录
            str(self.src_dir),            # src目录
            str(self.vnpy_framework_dir)  # VnPy框架目录
        ]
        
        for path in paths_to_add:
            if path not in sys.path:
                sys.path.insert(0, path)
    
    def get_relative_path(self, target_path: Path, base_path: Optional[Path] = None) -> str:
        """获取相对路径"""
        if base_path is None:
            base_path = self.project_root
        
        try:
            return str(target_path.relative_to(base_path))
        except ValueError:
            # 如果无法生成相对路径，返回绝对路径
            return str(target_path.resolve())
    
    def get_database_url(self, use_test_db: bool = False) -> str:
        """获取数据库URL"""
        # 注意：现在使用MySQL，这个方法仅供参考
        # 实际的数据库URL由config.py中的环境变量决定
        db_file = self.test_database_file if use_test_db else self.database_file
        return f"sqlite:///{db_file}"
    
    def get_upload_path(self) -> str:
        """获取文件上传路径"""
        return str(self.uploads_dir)
    
    def get_log_file_path(self) -> str:
        """获取日志文件路径"""
        return str(self.app_log)
    
    def get_vnpy_data_path(self) -> str:
        """获取VnPy数据路径"""
        return str(self.vnpy_data_dir)
    
    def to_dict(self) -> Dict[str, str]:
        """将所有路径配置转换为字典"""
        paths = {}
        
        for attr_name in dir(self):
            if not attr_name.startswith('_') and not callable(getattr(self, attr_name)):
                attr_value = getattr(self, attr_name)
                if isinstance(attr_value, Path):
                    paths[attr_name] = str(attr_value)
        
        return paths
    
    def __str__(self) -> str:
        """字符串表示"""
        return f"PathConfig(project_root={self.project_root})"
    
    def __repr__(self) -> str:
        """详细字符串表示"""
        return self.__str__()


class PathSettings(BaseModel):
    """路径配置的Pydantic模型（用于与现有Settings集成）"""
    
    # 基础路径
    project_root: str = Field(description="项目根目录")
    data_dir: str = Field(description="数据目录")
    logs_dir: str = Field(description="日志目录")
    
    # 数据库配置
    database_url: str = Field(description="数据库URL")
    test_database_url: str = Field(description="测试数据库URL")
    
    # VnPy配置
    vnpy_data_path: str = Field(description="VnPy数据路径")
    
    # 文件上传配置
    upload_path: str = Field(description="文件上传路径")
    
    # 日志配置
    log_file_path: str = Field(description="日志文件路径")
    
    @classmethod
    def from_path_config(cls, path_config: PathConfig) -> "PathSettings":
        """从PathConfig创建PathSettings实例"""
        return cls(
            project_root=str(path_config.project_root),
            data_dir=str(path_config.data_dir),
            logs_dir=str(path_config.logs_dir),
            database_url=path_config.get_database_url(),
            test_database_url=path_config.get_database_url(use_test_db=True),
            vnpy_data_path=path_config.get_vnpy_data_path(),
            upload_path=path_config.get_upload_path(),
            log_file_path=path_config.get_log_file_path()
        )


# === 全局路径配置实例 ===
_path_config: Optional[PathConfig] = None


def get_path_config(project_root: Optional[str] = None) -> PathConfig:
    """获取全局路径配置实例（单例模式）"""
    global _path_config
    
    if _path_config is None:
        _path_config = PathConfig(project_root)
        # 自动添加到Python路径
        _path_config.add_to_python_path()
    
    return _path_config


def reset_path_config():
    """重置路径配置（主要用于测试）"""
    global _path_config
    _path_config = None


# === 便捷函数 ===
def get_project_root() -> Path:
    """获取项目根目录"""
    return get_path_config().project_root


def get_database_url(use_test_db: bool = False) -> str:
    """获取数据库URL"""
    return get_path_config().get_database_url(use_test_db)


def get_vnpy_data_path() -> str:
    """获取VnPy数据路径"""
    return get_path_config().get_vnpy_data_path()


def get_upload_path() -> str:
    """获取上传路径"""
    return get_path_config().get_upload_path()


def get_log_file_path() -> str:
    """获取日志文件路径"""
    return get_path_config().get_log_file_path()


def add_project_to_path():
    """将项目路径添加到Python路径"""
    get_path_config().add_to_python_path()


if __name__ == "__main__":
    # 测试代码
    config = get_path_config()
    print("=== VnPy Web 路径配置 ===")
    print(f"项目根目录: {config.project_root}")
    print(f"数据目录: {config.data_dir}")
    print(f"日志目录: {config.logs_dir}")
    print(f"数据库URL: {config.get_database_url()}")
    print(f"VnPy数据路径: {config.get_vnpy_data_path()}")
    print()
    print("所有路径配置:")
    for name, path in config.to_dict().items():
        print(f"  {name}: {path}")
