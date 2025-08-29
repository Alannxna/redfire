"""
VnPy WebBuild 集成服务配置管理模块
===================================

统一管理集成服务架构的配置信息
新架构：VnPy集成核心服务 + 辅助微服务
支持环境变量覆盖，实现灵活的配置管理
"""

import os
from typing import Dict, Any, Optional
from dataclasses import dataclass
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings

from .path_config import get_path_config


@dataclass
class ServiceInfo:
    """单个微服务配置信息"""
    name: str
    port: int
    host: str
    description: str
    color: str
    endpoint: str = "docs"
    
    @property 
    def url(self) -> str:
        """获取服务完整URL"""
        return f"http://{self.host}:{self.port}"
    
    @property
    def api_url(self) -> str:
        """获取API文档URL"""
        return f"{self.url}/{self.endpoint}"


class ServicePortConfig(BaseSettings):
    """集成服务端口配置"""
    
    # === 核心服务端口配置 ===
    vnpy_core_port: int = Field(default=8006, env="VNPY_CORE_PORT")  # VnPy集成核心服务（包含策略管理）
    
    # === 辅助微服务端口配置 ===  
    user_trading_port: int = Field(default=8001, env="USER_TRADING_PORT")
    strategy_data_port: int = Field(default=8002, env="STRATEGY_DATA_PORT") 
    gateway_port: int = Field(default=8004, env="GATEWAY_PORT")
    monitor_port: int = Field(default=8005, env="MONITOR_PORT")
    
    # 注意：strategy_mgmt_port 已移除，策略管理功能已集成到 vnpy_core_port 中
    
    # === 服务器配置 ===
    service_host: str = Field(default="0.0.0.0", env="SERVICE_HOST")
    api_host: str = Field(default="127.0.0.1", env="API_HOST")  # 对外展示的主机
    
    # === 超时配置 ===
    service_start_timeout: int = Field(default=10, env="SERVICE_START_TIMEOUT")
    service_stop_timeout: int = Field(default=5, env="SERVICE_STOP_TIMEOUT")
    health_check_timeout: int = Field(default=3, env="HEALTH_CHECK_TIMEOUT")
    
    # === 网络配置 ===
    redis_host: str = Field(default="localhost", env="REDIS_HOST")
    redis_port: int = Field(default=6379, env="REDIS_PORT")
    redis_db: int = Field(default=0, env="REDIS_DB")
    
    # === CORS配置 ===
    cors_origins: str = Field(
        default="http://localhost:3000,http://localhost:8080,http://127.0.0.1:3000,http://127.0.0.1:8080",
        env="CORS_ORIGINS"
    )
    
    # === WebSocket配置 ===
    ws_heartbeat_interval: int = Field(default=30, env="WS_HEARTBEAT_INTERVAL")
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore"
    }
    
    @property
    def redis_url(self) -> str:
        """获取Redis连接URL"""
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"
    
    @property
    def cors_origins_list(self) -> list[str]:
        """获取CORS允许的源列表"""
        return [origin.strip() for origin in self.cors_origins.split(",")]


class ServiceRegistry:
    """微服务注册表"""
    
    def __init__(self, port_config: Optional[ServicePortConfig] = None):
        self.port_config = port_config or ServicePortConfig()
        self._services = self._init_services()
    
    def _init_services(self) -> Dict[str, ServiceInfo]:
        """初始化集成服务架构配置"""
        return {
            # 核心集成服务
            "vnpy_core": ServiceInfo(
                name="VnPy集成核心服务",
                port=self.port_config.vnpy_core_port,
                host=self.port_config.service_host,
                description="VnPy引擎管理、事件处理、网关连接、市场数据、策略管理、Redis消息队列",
                color="\033[91m",  # 红色
                endpoint="docs"
            ),
            
            # 辅助微服务（可选）
            "user_trading": ServiceInfo(
                name="用户交易服务",
                port=self.port_config.user_trading_port,
                host=self.port_config.service_host,
                description="用户认证、账户管理、订单交易、风险控制",
                color="\033[92m",  # 绿色
                endpoint="docs"
            ),
            "strategy_data": ServiceInfo(
                name="策略数据服务", 
                port=self.port_config.strategy_data_port,
                host=self.port_config.service_host,
                description="数据管理、回测分析、技术指标计算",
                color="\033[94m",  # 蓝色
                endpoint="docs"
            ),
            "gateway": ServiceInfo(
                name="网关适配服务",
                port=self.port_config.gateway_port,
                host=self.port_config.service_host,
                description="CTP接口适配、协议转换、订单路由",
                color="\033[95m",  # 紫色
                endpoint="docs"
            ),
            "monitor": ServiceInfo(
                name="监控通知服务",
                port=self.port_config.monitor_port,
                host=self.port_config.service_host,
                description="系统监控、告警通知、日志收集、性能分析",
                color="\033[93m",  # 黄色
                endpoint="docs"
            )
            
            # 注意：strategy_mgmt 服务已移除，功能已集成到 vnpy_core 服务中
        }
    
    def get_service(self, service_key: str) -> Optional[ServiceInfo]:
        """获取指定微服务配置"""
        return self._services.get(service_key)
    
    def get_all_services(self) -> Dict[str, ServiceInfo]:
        """获取所有微服务配置"""
        return self._services.copy()
    
    def get_service_ports(self) -> Dict[str, int]:
        """获取所有服务端口映射"""
        return {key: service.port for key, service in self._services.items()}
    
    def get_port_by_service(self, service_key: str) -> Optional[int]:
        """根据服务名获取端口"""
        service = self.get_service(service_key)
        return service.port if service else None
    
    def is_port_occupied(self, port: int) -> bool:
        """检查端口是否被其他服务占用"""
        return port in [service.port for service in self._services.values()]
    
    def get_service_by_port(self, port: int) -> Optional[str]:
        """根据端口获取服务名"""
        for key, service in self._services.items():
            if service.port == port:
                return key
        return None
    
    def validate_ports(self) -> Dict[str, Any]:
        """验证端口配置"""
        ports = [service.port for service in self._services.values()]
        duplicates = []
        
        for port in set(ports):
            if ports.count(port) > 1:
                services = [key for key, service in self._services.items() if service.port == port]
                duplicates.append({"port": port, "services": services})
        
        return {
            "valid": len(duplicates) == 0,
            "total_services": len(self._services),
            "unique_ports": len(set(ports)),
            "duplicates": duplicates,
            "port_range": {
                "min": min(ports),
                "max": max(ports)
            }
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "services": {
                key: {
                    "name": service.name,
                    "port": service.port,
                    "host": service.host,
                    "url": service.url,
                    "api_url": service.api_url,
                    "description": service.description,
                    "color": service.color
                }
                for key, service in self._services.items()
            },
            "config": {
                "service_host": self.port_config.service_host,
                "api_host": self.port_config.api_host,
                "redis_url": self.port_config.redis_url,
                "cors_origins": self.port_config.cors_origins_list,
                "timeouts": {
                    "service_start": self.port_config.service_start_timeout,
                    "service_stop": self.port_config.service_stop_timeout,
                    "health_check": self.port_config.health_check_timeout
                }
            }
        }


# === 全局服务注册表实例 ===
_service_registry: Optional[ServiceRegistry] = None


def get_service_registry() -> ServiceRegistry:
    """获取全局服务注册表实例（单例模式）"""
    global _service_registry
    
    if _service_registry is None:
        _service_registry = ServiceRegistry()
    
    return _service_registry


def reset_service_registry():
    """重置服务注册表（主要用于测试）"""
    global _service_registry
    _service_registry = None


# === 便捷函数 ===
def get_service_config(service_key: str) -> Optional[ServiceInfo]:
    """获取指定服务配置"""
    return get_service_registry().get_service(service_key)


def get_all_services() -> Dict[str, ServiceInfo]:
    """获取所有服务配置"""
    return get_service_registry().get_all_services()


def get_service_port(service_key: str) -> Optional[int]:
    """获取服务端口"""
    return get_service_registry().get_port_by_service(service_key)


def get_port_config() -> ServicePortConfig:
    """获取端口配置实例"""
    return get_service_registry().port_config


def validate_service_config() -> Dict[str, Any]:
    """验证服务配置"""
    return get_service_registry().validate_ports()


if __name__ == "__main__":
    # 测试代码
    registry = get_service_registry()
    
    print("=== VnPy WebBuild 微服务配置测试 ===")
    print(f"服务总数: {len(registry.get_all_services())}")
    
    print("\n服务端口映射:")
    for key, port in registry.get_service_ports().items():
        service = registry.get_service(key)
        print(f"  {key}: {service.name} -> {service.url}")
    
    print(f"\nRedis URL: {registry.port_config.redis_url}")
    print(f"CORS Origins: {registry.port_config.cors_origins_list}")
    
    validation = registry.validate_ports()
    print(f"\n端口验证: {'✅ 通过' if validation['valid'] else '❌ 失败'}")
    if not validation['valid']:
        print(f"重复端口: {validation['duplicates']}")
