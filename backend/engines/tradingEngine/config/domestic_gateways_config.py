"""
国内券商网关配置管理系统
支持多环境配置、动态更新、配置验证等功能
"""

import os
import yaml
import json
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime

from ..adapters.domestic_gateways_adapter import DomesticGatewayConfig, DomesticGatewayType


class ConfigEnvironment:
    """配置环境枚举"""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


@dataclass
class CtptestConfig:
    """CTP测试配置"""
    enabled: bool = True
    userid: str = ""
    password: str = ""
    brokerid: str = "9999"
    appid: str = ""
    auth_code: str = ""
    product_info: str = ""
    td_address: str = "tcp://180.168.146.187:10101"
    md_address: str = "tcp://180.168.146.187:10111"
    environment: str = "simnow"  # simnow, test, production


@dataclass
class XtpConfig:
    """中泰XTP配置"""
    enabled: bool = True
    userid: str = ""
    password: str = ""
    client_id: int = 1
    software_key: str = ""
    quote_ip: str = ""
    quote_port: int = 0
    trade_ip: str = ""
    trade_port: int = 0
    quote_protocol: str = "TCP"
    trade_protocol: str = "TCP"
    heartbeat_interval: int = 15


@dataclass
class OesConfig:
    """宽睿OES配置"""
    enabled: bool = True
    username: str = ""
    password: str = ""
    hdd_serial: str = ""
    mac_address: str = ""
    ip_address: str = ""
    ord_server: str = ""
    rpt_server: str = ""
    qry_server: str = ""
    mode: str = "PRODUCT"  # PRODUCT/SIMULATION


class DomesticGatewaysConfigManager:
    """
    国内券商网关配置管理器
    
    功能:
    - 多环境配置管理
    - 配置文件加载和保存
    - 配置验证和校验
    - 动态配置更新
    - 配置备份和恢复
    """
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        
        self.logger = logging.getLogger(f"{__name__}.ConfigManager")
        
        # 当前环境
        self.current_environment = os.getenv("TRADING_ENV", ConfigEnvironment.DEVELOPMENT)
        
        # 配置缓存
        self.config_cache: Dict[str, DomesticGatewayConfig] = {}
        
        # 配置文件路径
        self.config_files = {
            ConfigEnvironment.DEVELOPMENT: self.config_dir / "domestic_gateways_dev.yaml",
            ConfigEnvironment.TESTING: self.config_dir / "domestic_gateways_test.yaml",
            ConfigEnvironment.STAGING: self.config_dir / "domestic_gateways_staging.yaml",
            ConfigEnvironment.PRODUCTION: self.config_dir / "domestic_gateways_prod.yaml"
        }
        
        # 默认配置
        self.default_configs = self._create_default_configs()
        
        # 初始化配置文件
        self._initialize_config_files()
        
        self.logger.info(f"配置管理器初始化完成，当前环境: {self.current_environment}")
    
    def _create_default_configs(self) -> Dict[str, DomesticGatewayConfig]:
        """创建默认配置"""
        return {
            ConfigEnvironment.DEVELOPMENT: DomesticGatewayConfig(
                enabled_gateways=[DomesticGatewayType.CTPTEST],
                ctptest_config=asdict(CtptestConfig(
                    userid="test_user",
                    password="test_pass",
                    environment="simnow"
                )),
                xtp_config=asdict(XtpConfig(enabled=False)),
                oes_config=asdict(OesConfig(enabled=False)),
                enable_auto_reconnect=True,
                reconnect_interval=5,
                max_reconnect_attempts=5,
                enable_monitoring=True
            ),
            
            ConfigEnvironment.TESTING: DomesticGatewayConfig(
                enabled_gateways=[DomesticGatewayType.CTPTEST, DomesticGatewayType.XTP],
                ctptest_config=asdict(CtptestConfig(environment="test")),
                xtp_config=asdict(XtpConfig()),
                oes_config=asdict(OesConfig(enabled=False)),
                enable_auto_reconnect=True,
                reconnect_interval=3,
                max_reconnect_attempts=10
            ),
            
            ConfigEnvironment.STAGING: DomesticGatewayConfig(
                enabled_gateways=[DomesticGatewayType.XTP, DomesticGatewayType.OES],
                ctptest_config=asdict(CtptestConfig(enabled=False)),
                xtp_config=asdict(XtpConfig()),
                oes_config=asdict(OesConfig()),
                enable_auto_reconnect=True,
                reconnect_interval=2,
                max_reconnect_attempts=15
            ),
            
            ConfigEnvironment.PRODUCTION: DomesticGatewayConfig(
                enabled_gateways=[DomesticGatewayType.XTP, DomesticGatewayType.OES],
                ctptest_config=asdict(CtptestConfig(enabled=False)),
                xtp_config=asdict(XtpConfig()),
                oes_config=asdict(OesConfig()),
                enable_auto_reconnect=True,
                reconnect_interval=1,
                max_reconnect_attempts=20,
                heartbeat_interval=15,
                order_timeout=10,
                max_concurrent_orders=500
            )
        }
    
    def _initialize_config_files(self):
        """初始化配置文件"""
        for env, config_file in self.config_files.items():
            if not config_file.exists():
                # 创建默认配置文件
                default_config = self.default_configs[env]
                self._save_config_to_file(default_config, config_file)
                self.logger.info(f"创建默认配置文件: {config_file}")
    
    def load_config(self, environment: Optional[str] = None) -> DomesticGatewayConfig:
        """
        加载配置
        
        Args:
            environment: 环境名称，为空则使用当前环境
            
        Returns:
            配置对象
        """
        env = environment or self.current_environment
        
        # 检查缓存
        if env in self.config_cache:
            return self.config_cache[env]
        
        # 加载配置文件
        config_file = self.config_files.get(env)
        if not config_file or not config_file.exists():
            self.logger.warning(f"配置文件不存在: {env}，使用默认配置")
            config = self.default_configs.get(env, self.default_configs[ConfigEnvironment.DEVELOPMENT])
        else:
            config = self._load_config_from_file(config_file)
        
        # 验证配置
        if self.validate_config(config):
            self.config_cache[env] = config
            self.logger.info(f"配置加载成功: {env}")
        else:
            self.logger.error(f"配置验证失败: {env}")
            raise ValueError(f"Invalid configuration for environment: {env}")
        
        return config
    
    def save_config(self, config: DomesticGatewayConfig, 
                   environment: Optional[str] = None) -> bool:
        """
        保存配置
        
        Args:
            config: 配置对象
            environment: 环境名称，为空则使用当前环境
            
        Returns:
            保存是否成功
        """
        try:
            env = environment or self.current_environment
            
            # 验证配置
            if not self.validate_config(config):
                self.logger.error("配置验证失败，无法保存")
                return False
            
            # 备份现有配置
            config_file = self.config_files[env]
            if config_file.exists():
                self._backup_config_file(config_file)
            
            # 保存新配置
            self._save_config_to_file(config, config_file)
            
            # 更新缓存
            self.config_cache[env] = config
            
            self.logger.info(f"配置保存成功: {env}")
            return True
            
        except Exception as e:
            self.logger.error(f"保存配置失败: {e}")
            return False
    
    def _load_config_from_file(self, config_file: Path) -> DomesticGatewayConfig:
        """从文件加载配置"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                if config_file.suffix.lower() == '.yaml':
                    data = yaml.safe_load(f)
                else:
                    data = json.load(f)
            
            # 转换为配置对象
            return DomesticGatewayConfig(**data)
            
        except Exception as e:
            self.logger.error(f"加载配置文件失败 {config_file}: {e}")
            raise
    
    def _save_config_to_file(self, config: DomesticGatewayConfig, config_file: Path):
        """保存配置到文件"""
        try:
            # 转换为字典
            config_dict = asdict(config)
            
            # 处理枚举类型
            if 'enabled_gateways' in config_dict:
                config_dict['enabled_gateways'] = [
                    gateway.value if hasattr(gateway, 'value') else gateway
                    for gateway in config_dict['enabled_gateways']
                ]
            
            with open(config_file, 'w', encoding='utf-8') as f:
                if config_file.suffix.lower() == '.yaml':
                    yaml.dump(config_dict, f, default_flow_style=False, 
                             allow_unicode=True, indent=2)
                else:
                    json.dump(config_dict, f, indent=2, ensure_ascii=False)
            
        except Exception as e:
            self.logger.error(f"保存配置文件失败 {config_file}: {e}")
            raise
    
    def _backup_config_file(self, config_file: Path):
        """备份配置文件"""
        try:
            backup_dir = self.config_dir / "backups"
            backup_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = backup_dir / f"{config_file.stem}_{timestamp}{config_file.suffix}"
            
            import shutil
            shutil.copy2(config_file, backup_file)
            
            self.logger.info(f"配置文件备份: {backup_file}")
            
        except Exception as e:
            self.logger.warning(f"备份配置文件失败: {e}")
    
    def validate_config(self, config: DomesticGatewayConfig) -> bool:
        """
        验证配置
        
        Args:
            config: 配置对象
            
        Returns:
            验证是否通过
        """
        try:
            # 基本验证
            if not isinstance(config.enabled_gateways, list):
                self.logger.error("enabled_gateways must be a list")
                return False
            
            # 验证启用的网关配置
            for gateway_type in config.enabled_gateways:
                if not self._validate_gateway_config(gateway_type, config):
                    return False
            
            # 验证数值范围
            if config.reconnect_interval < 1:
                self.logger.error("reconnect_interval must be >= 1")
                return False
            
            if config.max_reconnect_attempts < 1:
                self.logger.error("max_reconnect_attempts must be >= 1")
                return False
            
            if config.heartbeat_interval < 5:
                self.logger.error("heartbeat_interval must be >= 5")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"配置验证异常: {e}")
            return False
    
    def _validate_gateway_config(self, gateway_type: DomesticGatewayType, 
                                config: DomesticGatewayConfig) -> bool:
        """验证单个网关配置"""
        try:
            if gateway_type == DomesticGatewayType.CTPTEST:
                return self._validate_ctptest_config(config.ctptest_config)
            elif gateway_type == DomesticGatewayType.XTP:
                return self._validate_xtp_config(config.xtp_config)
            elif gateway_type == DomesticGatewayType.OES:
                return self._validate_oes_config(config.oes_config)
            
            return False
            
        except Exception as e:
            self.logger.error(f"验证网关配置失败 {gateway_type}: {e}")
            return False
    
    def _validate_ctptest_config(self, config: Dict[str, Any]) -> bool:
        """验证CTP测试配置"""
        required_fields = ['userid', 'password', 'brokerid']
        
        for field in required_fields:
            if not config.get(field):
                self.logger.error(f"CTPTest配置缺少必要字段: {field}")
                return False
        
        # 验证服务器地址
        if not config.get('td_address') or not config.get('md_address'):
            self.logger.error("CTPTest配置缺少服务器地址")
            return False
        
        return True
    
    def _validate_xtp_config(self, config: Dict[str, Any]) -> bool:
        """验证XTP配置"""
        if not config.get('enabled', True):
            return True
        
        required_fields = ['userid', 'password', 'client_id', 'software_key']
        
        for field in required_fields:
            if not config.get(field):
                self.logger.error(f"XTP配置缺少必要字段: {field}")
                return False
        
        # 验证服务器配置
        if not config.get('trade_ip') or not config.get('quote_ip'):
            self.logger.error("XTP配置缺少服务器地址")
            return False
        
        if not config.get('trade_port') or not config.get('quote_port'):
            self.logger.error("XTP配置缺少服务器端口")
            return False
        
        return True
    
    def _validate_oes_config(self, config: Dict[str, Any]) -> bool:
        """验证OES配置"""
        if not config.get('enabled', True):
            return True
        
        required_fields = ['username', 'password']
        
        for field in required_fields:
            if not config.get(field):
                self.logger.error(f"OES配置缺少必要字段: {field}")
                return False
        
        # 验证服务器配置
        if not config.get('ord_server') or not config.get('rpt_server'):
            self.logger.error("OES配置缺少服务器地址")
            return False
        
        return True
    
    def get_available_environments(self) -> List[str]:
        """获取可用环境列表"""
        return list(self.config_files.keys())
    
    def get_current_environment(self) -> str:
        """获取当前环境"""
        return self.current_environment
    
    def set_environment(self, environment: str):
        """设置当前环境"""
        if environment in self.config_files:
            self.current_environment = environment
            self.logger.info(f"切换到环境: {environment}")
        else:
            raise ValueError(f"未知环境: {environment}")
    
    def reload_config(self, environment: Optional[str] = None) -> DomesticGatewayConfig:
        """重新加载配置"""
        env = environment or self.current_environment
        
        # 清除缓存
        if env in self.config_cache:
            del self.config_cache[env]
        
        # 重新加载
        return self.load_config(env)
    
    def export_config(self, config: DomesticGatewayConfig, 
                     export_file: str, format: str = "yaml") -> bool:
        """
        导出配置
        
        Args:
            config: 配置对象
            export_file: 导出文件路径
            format: 导出格式 (yaml/json)
            
        Returns:
            导出是否成功
        """
        try:
            export_path = Path(export_file)
            
            if format.lower() == "yaml":
                export_path = export_path.with_suffix(".yaml")
            else:
                export_path = export_path.with_suffix(".json")
            
            self._save_config_to_file(config, export_path)
            self.logger.info(f"配置导出成功: {export_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"导出配置失败: {e}")
            return False
    
    def import_config(self, import_file: str) -> Optional[DomesticGatewayConfig]:
        """
        导入配置
        
        Args:
            import_file: 导入文件路径
            
        Returns:
            导入的配置对象
        """
        try:
            import_path = Path(import_file)
            
            if not import_path.exists():
                self.logger.error(f"导入文件不存在: {import_path}")
                return None
            
            config = self._load_config_from_file(import_path)
            
            if self.validate_config(config):
                self.logger.info(f"配置导入成功: {import_path}")
                return config
            else:
                self.logger.error("导入的配置验证失败")
                return None
            
        except Exception as e:
            self.logger.error(f"导入配置失败: {e}")
            return None
    
    def get_config_summary(self, environment: Optional[str] = None) -> Dict[str, Any]:
        """
        获取配置摘要
        
        Args:
            environment: 环境名称
            
        Returns:
            配置摘要
        """
        try:
            config = self.load_config(environment)
            
            return {
                'environment': environment or self.current_environment,
                'enabled_gateways': [
                    gateway.value if hasattr(gateway, 'value') else gateway
                    for gateway in config.enabled_gateways
                ],
                'auto_reconnect': config.enable_auto_reconnect,
                'monitoring': config.enable_monitoring,
                'reconnect_settings': {
                    'interval': config.reconnect_interval,
                    'max_attempts': config.max_reconnect_attempts
                },
                'performance_settings': {
                    'heartbeat_interval': config.heartbeat_interval,
                    'order_timeout': config.order_timeout,
                    'max_concurrent_orders': config.max_concurrent_orders
                }
            }
            
        except Exception as e:
            self.logger.error(f"获取配置摘要失败: {e}")
            return {}


# 全局配置管理器实例
config_manager = DomesticGatewaysConfigManager()


def get_config_manager() -> DomesticGatewaysConfigManager:
    """获取配置管理器实例"""
    return config_manager


def load_domestic_config(environment: Optional[str] = None) -> DomesticGatewayConfig:
    """加载国内券商配置的便捷函数"""
    return config_manager.load_config(environment)


def save_domestic_config(config: DomesticGatewayConfig, 
                        environment: Optional[str] = None) -> bool:
    """保存国内券商配置的便捷函数"""
    return config_manager.save_config(config, environment)
