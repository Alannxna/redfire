"""
环境变量统一管理器

统一管理After和Backend的环境变量配置
"""

import os
import re
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class EnvironmentScope(str, Enum):
    """环境变量作用域"""
    GLOBAL = "global"           # 全局环境变量
    VNPY = "vnpy"              # VnPy相关
    DATABASE = "database"       # 数据库相关
    REDIS = "redis"            # Redis相关
    SERVICE = "service"        # 服务相关
    LOGGING = "logging"        # 日志相关
    SECURITY = "security"      # 安全相关
    DEVELOPMENT = "development" # 开发相关
    PRODUCTION = "production"   # 生产相关


@dataclass
class EnvironmentVariable:
    """环境变量定义"""
    name: str
    value: str
    scope: EnvironmentScope
    description: str = ""
    required: bool = False
    default_value: Optional[str] = None
    pattern: Optional[str] = None  # 正则表达式验证
    sensitive: bool = False        # 是否为敏感信息
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
    
    def validate(self) -> bool:
        """验证环境变量值"""
        if self.required and not self.value:
            return False
        
        if self.pattern and self.value:
            if not re.match(self.pattern, self.value):
                return False
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "value": "***" if self.sensitive else self.value,
            "scope": self.scope.value,
            "description": self.description,
            "required": self.required,
            "default_value": self.default_value,
            "pattern": self.pattern,
            "sensitive": self.sensitive,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


@dataclass
class EnvironmentProfile:
    """环境配置档案"""
    name: str
    description: str = ""
    variables: Dict[str, EnvironmentVariable] = field(default_factory=dict)
    active: bool = True
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
    
    def add_variable(self, variable: EnvironmentVariable):
        """添加环境变量"""
        self.variables[variable.name] = variable
    
    def remove_variable(self, name: str) -> bool:
        """移除环境变量"""
        if name in self.variables:
            del self.variables[name]
            return True
        return False
    
    def get_variable(self, name: str) -> Optional[EnvironmentVariable]:
        """获取环境变量"""
        return self.variables.get(name)
    
    def validate_all(self) -> Dict[str, bool]:
        """验证所有环境变量"""
        results = {}
        for name, var in self.variables.items():
            results[name] = var.validate()
        return results
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "description": self.description,
            "active": self.active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "variables": {name: var.to_dict() for name, var in self.variables.items()}
        }


class EnvironmentManager:
    """环境变量统一管理器"""
    
    def __init__(self):
        self.profiles: Dict[str, EnvironmentProfile] = {}
        self.current_profile: Optional[str] = None
        self.variable_registry: Dict[str, EnvironmentVariable] = {}
        self._cached_env: Dict[str, str] = {}
        self._load_system_env()
        self._setup_default_profiles()
        
        logger.info("环境变量管理器初始化完成")
    
    def _load_system_env(self):
        """加载系统环境变量"""
        self._cached_env = dict(os.environ)
        logger.info(f"已加载 {len(self._cached_env)} 个系统环境变量")
    
    def _setup_default_profiles(self):
        """设置默认环境配置档案"""
        # 开发环境档案
        dev_profile = self._create_development_profile()
        self.add_profile(dev_profile)
        
        # 生产环境档案
        prod_profile = self._create_production_profile()
        self.add_profile(prod_profile)
        
        # VnPy专用档案
        vnpy_profile = self._create_vnpy_profile()
        self.add_profile(vnpy_profile)
        
        # 设置默认档案
        self.current_profile = "development"
    
    def _create_development_profile(self) -> EnvironmentProfile:
        """创建开发环境档案"""
        profile = EnvironmentProfile(
            name="development",
            description="开发环境配置"
        )
        
        # 应用配置
        profile.add_variable(EnvironmentVariable(
            name="ENVIRONMENT",
            value="development",
            scope=EnvironmentScope.GLOBAL,
            description="运行环境",
            required=True,
            default_value="development"
        ))
        
        profile.add_variable(EnvironmentVariable(
            name="DEBUG",
            value="true",
            scope=EnvironmentScope.DEVELOPMENT,
            description="调试模式",
            default_value="true"
        ))
        
        profile.add_variable(EnvironmentVariable(
            name="LOG_LEVEL",
            value="DEBUG",
            scope=EnvironmentScope.LOGGING,
            description="日志级别",
            default_value="DEBUG",
            pattern=r"^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$"
        ))
        
        # 数据库配置
        profile.add_variable(EnvironmentVariable(
            name="DATABASE_HOST",
            value="127.0.0.1",
            scope=EnvironmentScope.DATABASE,
            description="数据库主机",
            required=True,
            default_value="127.0.0.1"
        ))
        
        profile.add_variable(EnvironmentVariable(
            name="DATABASE_PORT",
            value="3306",
            scope=EnvironmentScope.DATABASE,
            description="数据库端口",
            required=True,
            default_value="3306",
            pattern=r"^\d+$"
        ))
        
        profile.add_variable(EnvironmentVariable(
            name="DATABASE_USER",
            value="root",
            scope=EnvironmentScope.DATABASE,
            description="数据库用户",
            required=True,
            default_value="root"
        ))
        
        profile.add_variable(EnvironmentVariable(
            name="DATABASE_PASSWORD",
            value="root",
            scope=EnvironmentScope.DATABASE,
            description="数据库密码",
            required=True,
            default_value="root",
            sensitive=True
        ))
        
        profile.add_variable(EnvironmentVariable(
            name="DATABASE_NAME",
            value="vnpy_dev",
            scope=EnvironmentScope.DATABASE,
            description="数据库名称",
            required=True,
            default_value="vnpy_dev"
        ))
        
        # Redis配置
        profile.add_variable(EnvironmentVariable(
            name="REDIS_HOST",
            value="127.0.0.1",
            scope=EnvironmentScope.REDIS,
            description="Redis主机",
            default_value="127.0.0.1"
        ))
        
        profile.add_variable(EnvironmentVariable(
            name="REDIS_PORT",
            value="6379",
            scope=EnvironmentScope.REDIS,
            description="Redis端口",
            default_value="6379",
            pattern=r"^\d+$"
        ))
        
        # 安全配置
        profile.add_variable(EnvironmentVariable(
            name="SECRET_KEY",
            value="dev-secret-key-change-in-production",
            scope=EnvironmentScope.SECURITY,
            description="应用密钥",
            required=True,
            sensitive=True
        ))
        
        return profile
    
    def _create_production_profile(self) -> EnvironmentProfile:
        """创建生产环境档案"""
        profile = EnvironmentProfile(
            name="production",
            description="生产环境配置"
        )
        
        # 应用配置
        profile.add_variable(EnvironmentVariable(
            name="ENVIRONMENT",
            value="production",
            scope=EnvironmentScope.GLOBAL,
            description="运行环境",
            required=True
        ))
        
        profile.add_variable(EnvironmentVariable(
            name="DEBUG",
            value="false",
            scope=EnvironmentScope.PRODUCTION,
            description="调试模式",
            required=True
        ))
        
        profile.add_variable(EnvironmentVariable(
            name="LOG_LEVEL",
            value="WARNING",
            scope=EnvironmentScope.LOGGING,
            description="日志级别",
            required=True,
            pattern=r"^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$"
        ))
        
        # 数据库配置（生产环境需要外部配置）
        profile.add_variable(EnvironmentVariable(
            name="DATABASE_HOST",
            value="",
            scope=EnvironmentScope.DATABASE,
            description="数据库主机",
            required=True
        ))
        
        profile.add_variable(EnvironmentVariable(
            name="DATABASE_PORT",
            value="3306",
            scope=EnvironmentScope.DATABASE,
            description="数据库端口",
            required=True,
            pattern=r"^\d+$"
        ))
        
        profile.add_variable(EnvironmentVariable(
            name="DATABASE_USER",
            value="",
            scope=EnvironmentScope.DATABASE,
            description="数据库用户",
            required=True
        ))
        
        profile.add_variable(EnvironmentVariable(
            name="DATABASE_PASSWORD",
            value="",
            scope=EnvironmentScope.DATABASE,
            description="数据库密码",
            required=True,
            sensitive=True
        ))
        
        profile.add_variable(EnvironmentVariable(
            name="DATABASE_NAME",
            value="vnpy_prod",
            scope=EnvironmentScope.DATABASE,
            description="数据库名称",
            required=True
        ))
        
        # 安全配置
        profile.add_variable(EnvironmentVariable(
            name="SECRET_KEY",
            value="",
            scope=EnvironmentScope.SECURITY,
            description="应用密钥（必须在生产环境中设置）",
            required=True,
            sensitive=True,
            pattern=r"^.{32,}$"  # 至少32位
        ))
        
        return profile
    
    def _create_vnpy_profile(self) -> EnvironmentProfile:
        """创建VnPy专用环境档案"""
        profile = EnvironmentProfile(
            name="vnpy",
            description="VnPy框架专用配置"
        )
        
        # VnPy路径配置
        profile.add_variable(EnvironmentVariable(
            name="VNPY_CORE_PATH",
            value="",
            scope=EnvironmentScope.VNPY,
            description="VnPy核心代码路径"
        ))
        
        profile.add_variable(EnvironmentVariable(
            name="VNPY_FRAMEWORK_PATH",
            value="",
            scope=EnvironmentScope.VNPY,
            description="VnPy框架路径"
        ))
        
        profile.add_variable(EnvironmentVariable(
            name="VNPY_CONFIG_PATH",
            value="",
            scope=EnvironmentScope.VNPY,
            description="VnPy配置文件路径"
        ))
        
        profile.add_variable(EnvironmentVariable(
            name="VNPY_DATA_PATH",
            value="",
            scope=EnvironmentScope.VNPY,
            description="VnPy数据存储路径"
        ))
        
        profile.add_variable(EnvironmentVariable(
            name="VNPY_LOG_PATH",
            value="",
            scope=EnvironmentScope.VNPY,
            description="VnPy日志文件路径"
        ))
        
        # VnPy服务配置
        profile.add_variable(EnvironmentVariable(
            name="VNPY_API_PORT",
            value="8000",
            scope=EnvironmentScope.SERVICE,
            description="VnPy API服务端口",
            pattern=r"^\d+$"
        ))
        
        profile.add_variable(EnvironmentVariable(
            name="VNPY_WS_PORT",
            value="8001",
            scope=EnvironmentScope.SERVICE,
            description="VnPy WebSocket端口",
            pattern=r"^\d+$"
        ))
        
        profile.add_variable(EnvironmentVariable(
            name="VNPY_MAX_CONNECTIONS",
            value="100",
            scope=EnvironmentScope.SERVICE,
            description="最大连接数",
            pattern=r"^\d+$"
        ))
        
        return profile
    
    def add_profile(self, profile: EnvironmentProfile):
        """添加环境配置档案"""
        self.profiles[profile.name] = profile
        
        # 更新变量注册表
        for var in profile.variables.values():
            self.variable_registry[var.name] = var
        
        logger.info(f"已添加环境配置档案: {profile.name}")
    
    def remove_profile(self, name: str) -> bool:
        """移除环境配置档案"""
        if name in self.profiles:
            # 从变量注册表中移除相关变量
            profile = self.profiles[name]
            for var_name in profile.variables.keys():
                if var_name in self.variable_registry:
                    del self.variable_registry[var_name]
            
            del self.profiles[name]
            
            # 如果移除的是当前档案，切换到默认档案
            if self.current_profile == name:
                self.current_profile = "development" if "development" in self.profiles else None
            
            logger.info(f"已移除环境配置档案: {name}")
            return True
        
        return False
    
    def set_active_profile(self, name: str) -> bool:
        """设置活跃的环境配置档案"""
        if name in self.profiles:
            self.current_profile = name
            logger.info(f"已切换到环境配置档案: {name}")
            return True
        return False
    
    def get_profile(self, name: str) -> Optional[EnvironmentProfile]:
        """获取环境配置档案"""
        return self.profiles.get(name)
    
    def get_current_profile(self) -> Optional[EnvironmentProfile]:
        """获取当前活跃的环境配置档案"""
        if self.current_profile:
            return self.profiles.get(self.current_profile)
        return None
    
    def list_profiles(self) -> List[str]:
        """列出所有环境配置档案"""
        return list(self.profiles.keys())
    
    def get_variable(self, name: str, default: Optional[str] = None) -> Optional[str]:
        """获取环境变量值"""
        # 优先级：系统环境变量 > 当前档案 > 变量注册表 > 默认值
        
        # 1. 检查系统环境变量
        if name in self._cached_env:
            return self._cached_env[name]
        
        # 2. 检查当前档案
        current_profile = self.get_current_profile()
        if current_profile:
            var = current_profile.get_variable(name)
            if var and var.value:
                return var.value
        
        # 3. 检查变量注册表
        if name in self.variable_registry:
            var = self.variable_registry[name]
            if var.value:
                return var.value
            elif var.default_value:
                return var.default_value
        
        # 4. 返回默认值
        return default
    
    def set_variable(self, name: str, value: str, scope: EnvironmentScope = EnvironmentScope.GLOBAL) -> bool:
        """设置环境变量值"""
        try:
            # 更新系统环境变量
            os.environ[name] = value
            self._cached_env[name] = value
            
            # 更新当前档案
            current_profile = self.get_current_profile()
            if current_profile:
                var = current_profile.get_variable(name)
                if var:
                    var.value = value
                    var.updated_at = datetime.now()
                else:
                    # 创建新变量
                    new_var = EnvironmentVariable(
                        name=name,
                        value=value,
                        scope=scope,
                        description=f"运行时设置的变量"
                    )
                    current_profile.add_variable(new_var)
                    self.variable_registry[name] = new_var
            
            logger.info(f"已设置环境变量: {name}")
            return True
            
        except Exception as e:
            logger.error(f"设置环境变量失败: {name} - {e}")
            return False
    
    def unset_variable(self, name: str) -> bool:
        """删除环境变量"""
        try:
            # 从系统环境变量中删除
            if name in os.environ:
                del os.environ[name]
            
            if name in self._cached_env:
                del self._cached_env[name]
            
            # 从当前档案中删除
            current_profile = self.get_current_profile()
            if current_profile:
                current_profile.remove_variable(name)
            
            # 从变量注册表中删除
            if name in self.variable_registry:
                del self.variable_registry[name]
            
            logger.info(f"已删除环境变量: {name}")
            return True
            
        except Exception as e:
            logger.error(f"删除环境变量失败: {name} - {e}")
            return False
    
    def validate_environment(self, profile_name: Optional[str] = None) -> Dict[str, Any]:
        """验证环境配置"""
        profile = self.get_profile(profile_name) if profile_name else self.get_current_profile()
        
        if not profile:
            return {"valid": False, "errors": ["无效的环境配置档案"]}
        
        validation_results = profile.validate_all()
        
        errors = []
        warnings = []
        
        for var_name, is_valid in validation_results.items():
            var = profile.get_variable(var_name)
            if not var:
                continue
            
            if not is_valid:
                if var.required:
                    errors.append(f"必需的环境变量无效或缺失: {var_name}")
                else:
                    warnings.append(f"可选的环境变量无效: {var_name}")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "profile": profile.name,
            "total_variables": len(validation_results),
            "valid_variables": sum(validation_results.values()),
            "invalid_variables": sum(1 for v in validation_results.values() if not v)
        }
    
    def export_environment(self, profile_name: Optional[str] = None, format: str = "env") -> str:
        """导出环境配置"""
        profile = self.get_profile(profile_name) if profile_name else self.get_current_profile()
        
        if not profile:
            return ""
        
        if format.lower() == "env":
            return self._export_to_env_format(profile)
        elif format.lower() == "json":
            import json
            return json.dumps(profile.to_dict(), indent=2, ensure_ascii=False)
        elif format.lower() in ["yaml", "yml"]:
            import yaml
            return yaml.dump(profile.to_dict(), default_flow_style=False, allow_unicode=True)
        else:
            raise ValueError(f"不支持的导出格式: {format}")
    
    def _export_to_env_format(self, profile: EnvironmentProfile) -> str:
        """导出为.env文件格式"""
        lines = []
        lines.append(f"# {profile.description}")
        lines.append(f"# Generated at: {datetime.now().isoformat()}")
        lines.append("")
        
        # 按作用域分组
        grouped_vars = {}
        for var in profile.variables.values():
            scope = var.scope.value
            if scope not in grouped_vars:
                grouped_vars[scope] = []
            grouped_vars[scope].append(var)
        
        for scope, vars_list in grouped_vars.items():
            lines.append(f"# {scope.upper()} Configuration")
            for var in sorted(vars_list, key=lambda x: x.name):
                if var.description:
                    lines.append(f"# {var.description}")
                if var.required:
                    lines.append(f"# Required: Yes")
                if var.default_value:
                    lines.append(f"# Default: {var.default_value}")
                
                value = var.value if not var.sensitive else "***"
                lines.append(f"{var.name}={value}")
                lines.append("")
        
        return "\n".join(lines)
    
    def import_environment(self, source: Union[str, Path, Dict[str, Any]], profile_name: str, format: str = "env") -> bool:
        """导入环境配置"""
        try:
            if format.lower() == "env":
                if isinstance(source, (str, Path)):
                    return self._import_from_env_file(source, profile_name)
                else:
                    raise ValueError("ENV格式需要文件路径")
            elif format.lower() == "json":
                if isinstance(source, dict):
                    return self._import_from_dict(source, profile_name)
                elif isinstance(source, (str, Path)):
                    import json
                    with open(source, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    return self._import_from_dict(data, profile_name)
            elif format.lower() in ["yaml", "yml"]:
                if isinstance(source, dict):
                    return self._import_from_dict(source, profile_name)
                elif isinstance(source, (str, Path)):
                    import yaml
                    with open(source, 'r', encoding='utf-8') as f:
                        data = yaml.safe_load(f)
                    return self._import_from_dict(data, profile_name)
            
            return False
            
        except Exception as e:
            logger.error(f"导入环境配置失败: {e}")
            return False
    
    def _import_from_env_file(self, file_path: Union[str, Path], profile_name: str) -> bool:
        """从.env文件导入"""
        env_file = Path(file_path)
        if not env_file.exists():
            logger.error(f"环境文件不存在: {env_file}")
            return False
        
        profile = EnvironmentProfile(
            name=profile_name,
            description=f"从 {env_file} 导入的配置"
        )
        
        with open(env_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                
                if not line or line.startswith('#'):
                    continue
                
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    
                    var = EnvironmentVariable(
                        name=key,
                        value=value,
                        scope=self._infer_scope(key),
                        description=f"从 {env_file}:{line_num} 导入"
                    )
                    profile.add_variable(var)
        
        self.add_profile(profile)
        return True
    
    def _import_from_dict(self, data: Dict[str, Any], profile_name: str) -> bool:
        """从字典导入"""
        profile = EnvironmentProfile(
            name=profile_name,
            description=data.get("description", "从字典导入的配置")
        )
        
        variables_data = data.get("variables", {})
        for var_name, var_data in variables_data.items():
            var = EnvironmentVariable(
                name=var_name,
                value=var_data.get("value", ""),
                scope=EnvironmentScope(var_data.get("scope", "global")),
                description=var_data.get("description", ""),
                required=var_data.get("required", False),
                default_value=var_data.get("default_value"),
                pattern=var_data.get("pattern"),
                sensitive=var_data.get("sensitive", False)
            )
            profile.add_variable(var)
        
        self.add_profile(profile)
        return True
    
    def _infer_scope(self, var_name: str) -> EnvironmentScope:
        """推断环境变量的作用域"""
        name_lower = var_name.lower()
        
        if name_lower.startswith(('db_', 'database_')):
            return EnvironmentScope.DATABASE
        elif name_lower.startswith('redis_'):
            return EnvironmentScope.REDIS
        elif name_lower.startswith('vnpy_'):
            return EnvironmentScope.VNPY
        elif name_lower.startswith(('log_', 'logging_')):
            return EnvironmentScope.LOGGING
        elif name_lower.startswith(('secret_', 'key_', 'token_')):
            return EnvironmentScope.SECURITY
        elif name_lower.startswith(('service_', 'port_', 'host_')):
            return EnvironmentScope.SERVICE
        elif name_lower in ('debug', 'development'):
            return EnvironmentScope.DEVELOPMENT
        else:
            return EnvironmentScope.GLOBAL
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取环境管理统计信息"""
        total_vars = len(self.variable_registry)
        
        scope_counts = {}
        required_count = 0
        sensitive_count = 0
        
        for var in self.variable_registry.values():
            scope = var.scope.value
            scope_counts[scope] = scope_counts.get(scope, 0) + 1
            
            if var.required:
                required_count += 1
            if var.sensitive:
                sensitive_count += 1
        
        validation_result = self.validate_environment()
        
        return {
            "total_profiles": len(self.profiles),
            "current_profile": self.current_profile,
            "total_variables": total_vars,
            "required_variables": required_count,
            "sensitive_variables": sensitive_count,
            "scope_distribution": scope_counts,
            "validation": validation_result,
            "system_env_count": len(self._cached_env)
        }


# 全局环境管理器实例
_env_manager: Optional[EnvironmentManager] = None


def get_environment_manager() -> EnvironmentManager:
    """获取环境管理器实例"""
    global _env_manager
    if _env_manager is None:
        _env_manager = EnvironmentManager()
    return _env_manager


def get_env(name: str, default: Optional[str] = None) -> Optional[str]:
    """获取环境变量值的便捷函数"""
    manager = get_environment_manager()
    return manager.get_variable(name, default)


def set_env(name: str, value: str, scope: EnvironmentScope = EnvironmentScope.GLOBAL) -> bool:
    """设置环境变量值的便捷函数"""
    manager = get_environment_manager()
    return manager.set_variable(name, value, scope)
