"""
VnPy配置加载器
=============

负责加载和解析VnPy相关的配置文件
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import os

from .vnpy_path_manager import get_path_manager

logger = logging.getLogger(__name__)


class VnPyConfigLoader:
    """VnPy配置加载器"""
    
    def __init__(self):
        self.path_manager = get_path_manager()
        self._loaded_configs: Dict[str, Any] = {}
        
    def load_legacy_config(self) -> Dict[str, Any]:
        """
        加载原有config目录中的配置文件
        
        Returns:
            合并后的配置字典
        """
        paths = self.path_manager.setup_paths()
        
        config_sources = []
        project_root = Path(paths.project_root)
        
        # 1. 加载主配置目录
        main_config_dir = project_root / "config"
        if main_config_dir.exists():
            config_sources.extend(self._scan_config_directory(main_config_dir))
        
        # 2. 加载后端配置目录
        backend_config_dir = main_config_dir / "backend"
        if backend_config_dir.exists():
            config_sources.extend(self._scan_config_directory(backend_config_dir))
        
        # 3. 加载VnPy设置
        vt_setting_file = main_config_dir / "vt_setting.json"
        if vt_setting_file.exists():
            config_sources.append(vt_setting_file)
        
        # 合并所有配置
        merged_config = {}
        for config_file in config_sources:
            try:
                file_config = self._load_config_file(str(config_file))
                merged_config.update(file_config)
                logger.info(f"已加载配置文件: {config_file}")
            except Exception as e:
                logger.warning(f"配置文件加载失败 {config_file}: {e}")
        
        self._loaded_configs["legacy"] = merged_config
        return merged_config
    
    def _scan_config_directory(self, config_dir: Path) -> List[Path]:
        """扫描配置目录"""
        config_files = []
        
        # 支持的配置文件扩展名
        supported_extensions = {'.env', '.json', '.yaml', '.yml', '.toml', '.py'}
        
        for file_path in config_dir.rglob('*'):
            if file_path.is_file() and file_path.suffix in supported_extensions:
                # 排除__pycache__等目录
                if '__pycache__' not in str(file_path):
                    config_files.append(file_path)
        
        return sorted(config_files)
    
    def _load_config_file(self, file_path: str) -> Dict[str, Any]:
        """加载单个配置文件"""
        file_path_obj = Path(file_path)
        
        if not file_path_obj.exists():
            return {}
            
        try:
            if file_path_obj.suffix == '.json':
                return self._load_json_config(file_path_obj)
            elif file_path_obj.suffix in ['.yaml', '.yml']:
                return self._load_yaml_config(file_path_obj)
            elif file_path_obj.suffix == '.toml':
                return self._load_toml_config(file_path_obj)
            elif file_path_obj.suffix == '.env':
                return self._load_env_config(file_path_obj)
            elif file_path_obj.suffix == '.py':
                return self._load_python_config(file_path_obj)
            else:
                logger.warning(f"不支持的配置文件格式: {file_path}")
                return {}
                
        except Exception as e:
            logger.error(f"配置文件加载失败 {file_path}: {e}")
            return {}
    
    def _load_json_config(self, file_path: Path) -> Dict[str, Any]:
        """加载JSON配置文件"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _load_yaml_config(self, file_path: Path) -> Dict[str, Any]:
        """加载YAML配置文件"""
        try:
            import yaml
            with open(file_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except ImportError:
            logger.warning("YAML支持未安装，跳过YAML配置文件")
            return {}
    
    def _load_toml_config(self, file_path: Path) -> Dict[str, Any]:
        """加载TOML配置文件"""
        try:
            import tomli
            with open(file_path, 'rb') as f:
                return tomli.load(f)
        except ImportError:
            logger.warning("TOML支持未安装，跳过TOML配置文件")
            return {}
    
    def _load_env_config(self, file_path: Path) -> Dict[str, Any]:
        """加载环境变量文件"""
        config = {}
        
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip().strip('"').strip("'")
        
        return config
    
    def _load_python_config(self, file_path: Path) -> Dict[str, Any]:
        """加载Python配置文件"""
        import importlib.util
        
        spec = importlib.util.spec_from_file_location("config_module", file_path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # 提取配置变量
            config = {}
            for attr_name in dir(module):
                if not attr_name.startswith('_'):
                    attr_value = getattr(module, attr_name)
                    if not callable(attr_value):
                        config[attr_name] = attr_value
            
            return config
        
        return {}
    
    def load_vt_setting(self) -> Dict[str, Any]:
        """
        加载VnPy的vt_setting.json配置
        
        Returns:
            VnPy设置字典
        """
        paths = self.path_manager.setup_paths()
        vt_setting_file = Path(paths.project_root) / "config" / "vt_setting.json"
        
        if vt_setting_file.exists():
            config = self._load_json_config(vt_setting_file)
            self._loaded_configs["vt_setting"] = config
            return config
        else:
            logger.warning("未找到vt_setting.json配置文件")
            return {}
    
    def _convert_database_config(self, db_config: Dict[str, Any]) -> Dict[str, Any]:
        """转换数据库配置格式"""
        return {
            'type': db_config.get('name', 'mysql'),
            'host': db_config.get('host', '127.0.0.1'),
            'port': db_config.get('port', 3306),
            'username': db_config.get('user', 'root'),
            'password': db_config.get('password', ''),
            'database': db_config.get('database', 'vnpy'),
            'timezone': db_config.get('timezone', 'Asia/Shanghai'),
            'charset': 'utf8mb4',
            'pool_size': 10,
            'max_overflow': 20
        }
    
    def _create_service_config(self) -> Dict[str, Any]:
        """创建服务配置"""
        return {
            'vnpy_core': {
                'name': 'VnPy集成核心服务',
                'port': 8006,
                'host': '0.0.0.0',
                'description': 'VnPy引擎管理、事件处理、网关连接、策略管理'
            },
            'user_trading': {
                'name': '用户交易服务',
                'port': 8001,
                'host': '0.0.0.0',
                'description': '用户认证、账户管理、订单交易、风险控制'
            },
            'strategy_data': {
                'name': '策略数据服务',
                'port': 8002,
                'host': '0.0.0.0',
                'description': '策略管理和历史数据服务'
            },
            'gateway': {
                'name': '网关适配服务',
                'port': 8004,
                'host': '0.0.0.0',
                'description': '交易网关适配服务'
            },
            'monitor': {
                'name': '监控通知服务',
                'port': 8005,
                'host': '0.0.0.0',
                'description': '系统监控和通知服务'
            }
        }
    
    def _create_vnpy_config(self) -> Dict[str, Any]:
        """创建VnPy特定配置"""
        paths = self.path_manager.paths
        
        return {
            'data_path': paths.vnpy_data if paths else './vnpy_data',
            'log_path': paths.vnpy_logs if paths else './vnpy_logs',
            'config_path': paths.vnpy_config if paths else './vnpy_config',
            'gateway_settings': {
                'ctp': {
                    'enabled': True,
                    'settings_file': 'ctp_connect.json'
                },
                'binance': {
                    'enabled': False,
                    'settings_file': 'binance_connect.json'
                }
            },
            'strategy_settings': {
                'auto_start': False,
                'risk_check': True,
                'position_limit': 1000000
            }
        }
    
    def create_integrated_config(self) -> Dict[str, Any]:
        """
        创建集成配置，合并所有配置源
        
        Returns:
            集成后的配置字典
        """
        integrated_config = {}
        
        # 1. 加载VnPy路径配置
        paths = self.path_manager.setup_paths()
        integrated_config['paths'] = paths.__dict__
        
        # 2. 加载原有配置
        legacy_config = self.load_legacy_config()
        integrated_config.update(legacy_config)
        
        # 3. 设置数据库配置（从原有配置转换）
        if 'database' in legacy_config:
            integrated_config['database'] = self._convert_database_config(legacy_config['database'])
        
        # 4. 设置服务配置
        integrated_config['services'] = self._create_service_config()
        
        # 5. 设置VnPy特定配置
        integrated_config['vnpy'] = self._create_vnpy_config()
        
        self._loaded_configs["integrated"] = integrated_config
        logger.info("VnPy集成配置创建完成")
        
        return integrated_config
    
    def get_config(self, config_type: str = "integrated") -> Dict[str, Any]:
        """
        获取指定类型的配置
        
        Args:
            config_type: 配置类型 (integrated, legacy, vt_setting)
            
        Returns:
            配置字典
        """
        if config_type not in self._loaded_configs:
            if config_type == "integrated":
                return self.create_integrated_config()
            elif config_type == "legacy":
                return self.load_legacy_config()
            elif config_type == "vt_setting":
                return self.load_vt_setting()
        
        return self._loaded_configs.get(config_type, {})
    
    def get_fallback_config(self) -> Dict[str, Any]:
        """
        获取降级配置（当VnPy不可用时）
        
        Returns:
            降级配置字典
        """
        return {
            'vnpy_available': False,
            'mock_mode': True,
            'services': {
                'strategy_engine': {
                    'enabled': False,
                    'fallback_message': 'VnPy引擎不可用，已启用模拟模式'
                }
            },
            'database': {
                'type': 'sqlite',
                'path': './data/fallback.db'
            }
        }

