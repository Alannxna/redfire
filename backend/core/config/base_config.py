"""
基础配置类
==========

所有配置类的基类，提供通用的配置验证和管理功能
"""

import os
import logging
from typing import Any, Dict, List, Optional
from pathlib import Path
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class BaseConfig(BaseSettings):
    """基础配置类"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8", 
        case_sensitive=False,
        extra="ignore",  # 忽略额外字段以兼容旧配置
        validate_assignment=True
    )
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._validate_config()
        self._post_init()
        
    def _validate_config(self):
        """配置验证，子类可重写"""
        pass
        
    def _post_init(self):
        """初始化后处理，子类可重写"""
        pass
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return self.model_dump()
    
    def update_from_dict(self, data: Dict[str, Any]):
        """从字典更新配置"""
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                logger.warning(f"忽略未知配置项: {key}")
    
    def create_directories(self):
        """创建必需的目录，子类可重写"""
        pass
    
    def validate_environment(self):
        """环境验证，子类可重写"""
        return True
    
    @classmethod
    def from_env_file(cls, env_file: Optional[str] = None):
        """从环境文件加载配置"""
        if env_file:
            os.environ.setdefault('ENV_FILE', env_file)
        return cls()
    
    def get_env_value(self, key: str, default: Any = None) -> Any:
        """获取环境变量值"""
        return os.getenv(key, default)
    
    def set_env_value(self, key: str, value: str):
        """设置环境变量值"""
        os.environ[key] = str(value)
