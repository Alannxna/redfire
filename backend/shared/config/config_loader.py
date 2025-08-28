"""
统一配置加载器
================

符合新架构的配置加载器，整合外部微服务配置管理器
兼容现有系统的配置加载需求
"""

import os
import json
import logging
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional, List, Union, Type
from dataclasses import dataclass
from enum import Enum
import aiofiles
import httpx

# 导入统一工具模块
try:
    from .utils.config_utils import (
        ConfigFileLoader,
        ConfigEnvLoader,
        ConfigTypeConverter,
        ConfigMerger,
        ConfigCache,
        load_config_file,
        load_env_config
    )
    from .cache.global_cache_manager import (
        global_cache_manager,
        CacheType,
        cache_get,
        cache_set
    )
except ImportError:
    # 测试环境中的导入
    from utils.config_utils import (
        ConfigFileLoader,
        ConfigEnvLoader,
        ConfigTypeConverter,
        ConfigMerger,
        ConfigCache,
        load_config_file,
        load_env_config
    )
    from cache.global_cache_manager import (
        global_cache_manager,
        CacheType,
        cache_get,
        cache_set
    )

# 外部服务标准（可选导入）
try:
    from .external_service_standards import (
        ExternalServiceConfigStandard,
        ServiceType,
        validate_service_config_compliance,
        generate_service_config_template
    )
    HAS_EXTERNAL_STANDARDS = True
except ImportError:
    logger.warning("外部服务标准模块未找到，将使用基础功能")
    HAS_EXTERNAL_STANDARDS = False
    
    # 提供基础实现
    class ExternalServiceConfigStandard:
        """基础服务配置标准"""
        pass
    
    class ServiceType:
        """基础服务类型"""
        USER_SERVICE = "user"
        TRADING_SERVICE = "trading"
    
    def validate_service_config_compliance(config, service_type):
        """基础配置验证"""
        return True
    
    def generate_service_config_template(service_type):
        """基础配置模板"""
        return {}

logger = logging.getLogger(__name__)


class ConfigSource(str, Enum):
    """配置源类型"""
    FILE = "file"
    ENV = "env"
    SERVICE = "service"  # 外部配置服务
    DICT = "dict"
    REMOTE = "remote"


@dataclass
class ConfigLoadResult:
    """配置加载结果"""
    success: bool
    data: Dict[str, Any]
    source: ConfigSource
    error: Optional[str] = None
    load_time: Optional[float] = None


class ConfigLoaderError(Exception):
    """配置加载器异常"""
    pass


class SharedConfigLoader:
    """
    共享配置加载器 - 符合外部微服务架构
    
    特性:
    - 多源配置加载 (文件、环境变量、外部配置服务、字典)
    - 配置优先级管理 (SERVICE > DICT > REMOTE > ENV > FILE)
    - 异步加载支持
    - 配置验证和转换
    - 故障回退机制
    - 缓存机制
    - 外部微服务集成
    """
    
    def __init__(self, 
                 config_service_url: Optional[str] = None,
                 enable_cache: bool = True,
                 cache_ttl: int = 300):
        """
        初始化配置加载器
        
        Args:
            config_service_url: 外部配置服务URL
            enable_cache: 是否启用缓存
            cache_ttl: 缓存TTL(秒)
        """
        self.config_service_url = config_service_url or os.getenv(
            'REDFIRE_CONFIG_SERVICE_URL', 
            ExternalServiceConfigStandard.DEFAULT_CONFIG_SERVICE_URL
        )
        self.enable_cache = enable_cache
        self.cache_ttl = cache_ttl
        
        # 使用全局缓存管理器
        self.enable_cache = enable_cache
        if enable_cache:
            self._cache = global_cache_manager.get_cache(CacheType.SHARED_CONFIG)
        else:
            self._cache = None
        
        # 配置源优先级 (数字越大优先级越高)
        self._source_priority = {
            ConfigSource.FILE: 1,
            ConfigSource.ENV: 2,
            ConfigSource.SERVICE: 3,
            ConfigSource.DICT: 4,
            ConfigSource.REMOTE: 5
        }
        
        # HTTP客户端
        self._http_client: Optional[httpx.AsyncClient] = None
        
    async def __aenter__(self):
        """异步上下文管理器入口"""
        self._http_client = httpx.AsyncClient(timeout=30.0)
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self._http_client:
            await self._http_client.aclose()
    
    # =========================================================================
    # 核心加载方法
    # =========================================================================
    
    async def load_config(self,
                         config_name: str,
                         sources: Optional[List[ConfigSource]] = None,
                         fallback_config: Optional[Dict[str, Any]] = None,
                         **kwargs) -> ConfigLoadResult:
        """
        加载配置
        
        Args:
            config_name: 配置名称
            sources: 配置源列表，按优先级顺序
            fallback_config: 降级配置
            **kwargs: 额外参数
            
        Returns:
            配置加载结果
        """
        if sources is None:
            sources = [
                ConfigSource.SERVICE,  # 优先从配置服务加载
                ConfigSource.FILE,     # 文件配置
                ConfigSource.ENV       # 环境变量
            ]
        
        # 检查缓存
        cache_key = f"{config_name}:{':'.join(sources)}"
        if self.enable_cache:
            cached_data = cache_get(CacheType.SHARED_CONFIG, cache_key)
            if cached_data is not None:
                logger.debug(f"配置缓存命中: {config_name}")
                return ConfigLoadResult(
                    success=True,
                    data=cached_data,
                    source=ConfigSource.SERVICE,  # 缓存标记为服务源
                )
        
        # 按优先级尝试加载配置
        results: List[ConfigLoadResult] = []
        
        for source in sources:
            try:
                result = await self._load_from_source(
                    source, config_name, **kwargs
                )
                results.append(result)
                
                if result.success and result.data:
                    # 缓存成功结果
                    if self.enable_cache:
                        cache_set(CacheType.SHARED_CONFIG, cache_key, result.data)
                    
                    logger.info(f"配置加载成功: {config_name} from {source}")
                    return result
                    
            except Exception as e:
                logger.warning(f"配置源 {source} 加载失败: {e}")
                results.append(ConfigLoadResult(
                    success=False,
                    data={},
                    source=source,
                    error=str(e)
                ))
        
        # 所有源都失败，使用降级配置
        if fallback_config:
            logger.warning(f"所有配置源失败，使用降级配置: {config_name}")
            return ConfigLoadResult(
                success=True,
                data=fallback_config,
                source=ConfigSource.DICT
            )
        
        # 完全失败
        error_msg = f"配置加载失败: {config_name}, 尝试的源: {sources}"
        logger.error(error_msg)
        raise ConfigLoaderError(error_msg)
    
    async def _load_from_source(self, 
                               source: ConfigSource,
                               config_name: str,
                               **kwargs) -> ConfigLoadResult:
        """从指定源加载配置"""
        
        if source == ConfigSource.SERVICE:
            return await self._load_from_service(config_name, **kwargs)
        elif source == ConfigSource.FILE:
            return await self._load_from_file(config_name, **kwargs)
        elif source == ConfigSource.ENV:
            return await self._load_from_env(config_name, **kwargs)
        elif source == ConfigSource.DICT:
            return await self._load_from_dict(config_name, **kwargs)
        elif source == ConfigSource.REMOTE:
            return await self._load_from_remote(config_name, **kwargs)
        else:
            raise ConfigLoaderError(f"不支持的配置源: {source}")
    
    # =========================================================================
    # 配置服务加载
    # =========================================================================
    
    async def _load_from_service(self, 
                                config_name: str,
                                **kwargs) -> ConfigLoadResult:
        """从外部配置服务加载"""
        try:
            if not self._http_client:
                self._http_client = httpx.AsyncClient(timeout=30.0)
            
            # 使用标准化认证令牌
            token = kwargs.get('token') or os.getenv('REDFIRE_CONFIG_SERVICE_TOKEN', 
                                                   ExternalServiceConfigStandard.DEFAULT_CONFIG_SERVICE_TOKEN)
            
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            # 根据配置名称构建URL
            if config_name == "app":
                url = f"{self.config_service_url}/config"
            else:
                # 使用标准化配置服务API路径
                service_name = kwargs.get('service', 'shared')
                url = ExternalServiceConfigStandard.get_service_config_url(service_name, config_name)
            
            response = await self._http_client.get(url, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    return ConfigLoadResult(
                        success=True,
                        data=result.get('data', {}),
                        source=ConfigSource.SERVICE
                    )
                else:
                    return ConfigLoadResult(
                        success=False,
                        data={},
                        source=ConfigSource.SERVICE,
                        error=result.get('message', '配置服务返回错误')
                    )
            else:
                return ConfigLoadResult(
                    success=False,
                    data={},
                    source=ConfigSource.SERVICE,
                    error=f"HTTP {response.status_code}: {response.text}"
                )
                
        except Exception as e:
            return ConfigLoadResult(
                success=False,
                data={},
                source=ConfigSource.SERVICE,
                error=f"配置服务连接失败: {e}"
            )
    
    # =========================================================================
    # 文件加载
    # =========================================================================
    
    async def _load_from_file(self, 
                             config_name: str,
                             **kwargs) -> ConfigLoadResult:
        """从文件加载配置"""
        try:
            # 配置文件路径构建
            config_file = kwargs.get('config_file')
            if not config_file:
                # 使用标准化配置路径
                service_name = kwargs.get('service', 'shared')
                environment = os.getenv('REDFIRE_ENVIRONMENT', 'development')
                
                possible_paths = [
                    ExternalServiceConfigStandard.get_config_path(service_name, config_name, environment),
                    f"config/{service_name}/{config_name}.yaml",
                    f"config/shared/{config_name}.yaml",
                    f"config/{config_name}.yaml",  # 兜底路径
                ]
                
                for path in possible_paths:
                    if Path(path).exists():
                        config_file = path
                        break
                
                if not config_file:
                    return ConfigLoadResult(
                        success=False,
                        data={},
                        source=ConfigSource.FILE,
                        error=f"未找到配置文件: {config_name}"
                    )
            
            config_path = Path(config_file)
            
            if not config_path.exists():
                return ConfigLoadResult(
                    success=False,
                    data={},
                    source=ConfigSource.FILE,
                    error=f"配置文件不存在: {config_file}"
                )
            
            # 使用统一文件加载器
            try:
                data = load_config_file(config_path)
            except Exception as e:
                return ConfigLoadResult(
                    success=False,
                    data={},
                    source=ConfigSource.FILE,
                    error=f"配置文件解析失败: {e}"
                )
            
            return ConfigLoadResult(
                success=True,
                data=data,
                source=ConfigSource.FILE
            )
            
        except Exception as e:
            return ConfigLoadResult(
                success=False,
                data={},
                source=ConfigSource.FILE,
                error=f"文件加载失败: {e}"
            )
    

    
    # =========================================================================
    # 环境变量加载
    # =========================================================================
    
    async def _load_from_env(self, 
                            config_name: str,
                            **kwargs) -> ConfigLoadResult:
        """从环境变量加载配置"""
        try:
            # 使用标准化环境变量前缀
            service_name = kwargs.get('service', 'shared')
            prefix = kwargs.get('env_prefix', f"REDFIRE_{service_name.upper()}_{config_name.upper()}_")
            
            # 使用统一环境变量加载器
            env_config = load_env_config(prefix)
            
            if not env_config:
                return ConfigLoadResult(
                    success=False,
                    data={},
                    source=ConfigSource.ENV,
                    error=f"未找到环境变量: {prefix}*"
                )
            
            return ConfigLoadResult(
                success=True,
                data=env_config,
                source=ConfigSource.ENV
            )
            
        except Exception as e:
            return ConfigLoadResult(
                success=False,
                data={},
                source=ConfigSource.ENV,
                error=f"环境变量加载失败: {e}"
            )
    

    
    # =========================================================================
    # 字典加载
    # =========================================================================
    
    async def _load_from_dict(self, 
                             config_name: str,
                             **kwargs) -> ConfigLoadResult:
        """从字典加载配置"""
        try:
            config_dict = kwargs.get('config_dict')
            
            if not config_dict:
                return ConfigLoadResult(
                    success=False,
                    data={},
                    source=ConfigSource.DICT,
                    error="未提供配置字典"
                )
            
            return ConfigLoadResult(
                success=True,
                data=config_dict,
                source=ConfigSource.DICT
            )
            
        except Exception as e:
            return ConfigLoadResult(
                success=False,
                data={},
                source=ConfigSource.DICT,
                error=f"字典加载失败: {e}"
            )
    
    # =========================================================================
    # 远程加载
    # =========================================================================
    
    async def _load_from_remote(self, 
                               config_name: str,
                               **kwargs) -> ConfigLoadResult:
        """从远程URL加载配置"""
        try:
            remote_url = kwargs.get('remote_url')
            
            if not remote_url:
                return ConfigLoadResult(
                    success=False,
                    data={},
                    source=ConfigSource.REMOTE,
                    error="未提供远程URL"
                )
            
            if not self._http_client:
                self._http_client = httpx.AsyncClient(timeout=30.0)
            
            response = await self._http_client.get(remote_url)
            
            if response.status_code == 200:
                # 根据Content-Type解析
                content_type = response.headers.get('content-type', '').lower()
                
                if 'json' in content_type:
                    data = response.json()
                elif 'yaml' in content_type:
                    data = self._parse_yaml(response.text)
                else:
                    # 尝试JSON解析
                    try:
                        data = response.json()
                    except:
                        data = self._parse_yaml(response.text)
                
                return ConfigLoadResult(
                    success=True,
                    data=data,
                    source=ConfigSource.REMOTE
                )
            else:
                return ConfigLoadResult(
                    success=False,
                    data={},
                    source=ConfigSource.REMOTE,
                    error=f"HTTP {response.status_code}: {response.text}"
                )
                
        except Exception as e:
            return ConfigLoadResult(
                success=False,
                data={},
                source=ConfigSource.REMOTE,
                error=f"远程加载失败: {e}"
            )
    
    # =========================================================================
    # 缓存管理
    # =========================================================================
    

    
    def clear_cache(self, config_name: Optional[str] = None):
        """清除缓存"""
        if self.enable_cache:
            if config_name:
                # 清除特定配置的缓存
                logger.warning(f"全局缓存管理器暂不支持按配置名称清除，已清除共享配置缓存")
                global_cache_manager.clear(CacheType.SHARED_CONFIG)
            else:
                # 清除所有缓存
                global_cache_manager.clear(CacheType.SHARED_CONFIG)
    
    # =========================================================================
    # 配置验证和标准化
    # =========================================================================
    
    def validate_config(self, config_name: str, config_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """验证配置是否符合外部微服务标准"""
        service_name = kwargs.get('service', 'shared')
        return validate_service_config_compliance(service_name, config_data)
    
    def generate_config_template(self, service: str, environment: str = "development") -> Dict[str, Any]:
        """生成符合标准的配置模板"""
        return generate_service_config_template(service, environment)
    
    # =========================================================================
    # 便捷方法
    # =========================================================================
    
    async def load_app_config(self, **kwargs) -> Dict[str, Any]:
        """加载应用主配置"""
        result = await self.load_config('app', **kwargs)
        return result.data
    
    async def load_database_config(self, **kwargs) -> Dict[str, Any]:
        """加载数据库配置"""
        result = await self.load_config('database', **kwargs)
        return result.data
    
    async def load_redis_config(self, **kwargs) -> Dict[str, Any]:
        """加载Redis配置"""
        result = await self.load_config('redis', **kwargs)
        return result.data
    
    async def load_vnpy_config(self, **kwargs) -> Dict[str, Any]:
        """加载VnPy配置"""
        result = await self.load_config('vnpy', **kwargs)
        return result.data
    
    # =========================================================================
    # 健康检查
    # =========================================================================
    
    async def health_check(self) -> Dict[str, Any]:
        """配置加载器健康检查"""
        status = {
            'config_loader': 'healthy',
            'config_service': 'unknown',
            'cache_enabled': self.enable_cache,
            'cached_configs': len(self._cache)
        }
        
        # 检查配置服务状态
        try:
            if not self._http_client:
                self._http_client = httpx.AsyncClient(timeout=10.0)
            
            response = await self._http_client.get(
                f"{self.config_service_url}/health"
            )
            
            if response.status_code == 200:
                status['config_service'] = 'healthy'
            else:
                status['config_service'] = 'unhealthy'
                
        except Exception as e:
            status['config_service'] = 'unreachable'
            status['config_service_error'] = str(e)
        
        return status


# =============================================================================
# 全局配置加载器实例
# =============================================================================

_global_loader: Optional[SharedConfigLoader] = None


def get_config_loader() -> SharedConfigLoader:
    """获取共享配置加载器实例"""
    global _global_loader
    
    if _global_loader is None:
        _global_loader = SharedConfigLoader()
    
    return _global_loader


# =============================================================================
# 便捷函数
# =============================================================================

async def load_config(config_name: str, **kwargs) -> Dict[str, Any]:
    """加载配置的便捷函数"""
    loader = get_config_loader()
    
    async with loader:
        result = await loader.load_config(config_name, **kwargs)
        return result.data


async def load_app_config(**kwargs) -> Dict[str, Any]:
    """加载应用配置的便捷函数"""
    return await load_config('app', **kwargs)


async def load_database_config(**kwargs) -> Dict[str, Any]:
    """加载数据库配置的便捷函数"""
    return await load_config('database', **kwargs)


# =============================================================================
# 向后兼容支持
# =============================================================================

class LegacyConfigAdapter:
    """Legacy配置系统适配器"""
    
    def __init__(self, loader: SharedConfigLoader):
        self.loader = loader
    
    def load_config(self, config_name: str = "app") -> Dict[str, Any]:
        """同步配置加载 (向后兼容)"""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(
            self.loader.load_config(config_name)
        ).data
    
    def get_app_config(self) -> Dict[str, Any]:
        """获取应用配置 (向后兼容)"""
        return self.load_config('app')


def create_legacy_adapter() -> LegacyConfigAdapter:
    """创建Legacy配置适配器"""
    return LegacyConfigAdapter(get_config_loader())
