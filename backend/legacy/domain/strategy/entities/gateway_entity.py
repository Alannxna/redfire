"""
交易网关实体
定义交易网关的核心属性和行为
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum
import uuid


class GatewayStatus(str, Enum):
    """网关状态"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTING = "disconnecting"
    ERROR = "error"
    MAINTENANCE = "maintenance"


class GatewayType(str, Enum):
    """网关类型"""
    CTP = "ctp"  # 期货CTP
    XTP = "xtp"  # 股票XTP
    IB = "ib"    # 盈透证券
    OANDA = "oanda"  # 外汇OANDA
    BINANCE = "binance"  # 币安
    CUSTOM = "custom"  # 自定义


@dataclass
class ConnectionInfo:
    """连接信息"""
    host: str
    port: int
    username: Optional[str] = None
    password: Optional[str] = None
    api_key: Optional[str] = None
    secret_key: Optional[str] = None
    app_id: Optional[str] = None
    auth_code: Optional[str] = None
    extra_params: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "host": self.host,
            "port": self.port,
            "username": self.username,
            "password": self.password,
            "api_key": self.api_key,
            "secret_key": self.secret_key,
            "app_id": self.app_id,
            "auth_code": self.auth_code,
            "extra_params": self.extra_params
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConnectionInfo':
        """从字典创建"""
        return cls(**data)


@dataclass
class GatewayHealth:
    """网关健康状态"""
    is_healthy: bool = True
    last_heartbeat: Optional[datetime] = None
    response_time: Optional[float] = None  # 毫秒
    error_count: int = 0
    last_error: Optional[str] = None
    connection_uptime: Optional[float] = None  # 秒
    
    def update_heartbeat(self, response_time: float = None):
        """更新心跳"""
        self.last_heartbeat = datetime.now()
        if response_time is not None:
            self.response_time = response_time
        self.is_healthy = True
        self.error_count = 0
    
    def record_error(self, error_message: str):
        """记录错误"""
        self.last_error = error_message
        self.error_count += 1
        self.is_healthy = False
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "is_healthy": self.is_healthy,
            "last_heartbeat": self.last_heartbeat.isoformat() if self.last_heartbeat else None,
            "response_time": self.response_time,
            "error_count": self.error_count,
            "last_error": self.last_error,
            "connection_uptime": self.connection_uptime
        }


@dataclass
class TradingGateway:
    """交易网关实体"""
    
    gateway_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    gateway_name: str = ""
    gateway_type: GatewayType = GatewayType.CUSTOM
    status: GatewayStatus = GatewayStatus.DISCONNECTED
    
    # 连接信息
    connection_info: ConnectionInfo = field(default_factory=ConnectionInfo)
    
    # 状态信息
    is_connected: bool = False
    last_connection: Optional[datetime] = None
    last_disconnection: Optional[datetime] = None
    
    # 健康状态
    health: GatewayHealth = field(default_factory=GatewayHealth)
    
    # 元数据
    description: Optional[str] = None
    version: str = "1.0.0"
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    # 配置信息
    auto_reconnect: bool = True
    max_reconnect_attempts: int = 3
    heartbeat_interval: int = 30  # 秒
    timeout: int = 10  # 秒
    
    def connect(self) -> bool:
        """连接网关"""
        if self.is_connected:
            return True
        
        try:
            self.status = GatewayStatus.CONNECTING
            # 这里应该实现实际的连接逻辑
            # 目前只是模拟连接成功
            
            self.is_connected = True
            self.status = GatewayStatus.CONNECTED
            self.last_connection = datetime.now()
            self.health.update_heartbeat()
            self.updated_at = datetime.now()
            
            return True
            
        except Exception as e:
            self.status = GatewayStatus.ERROR
            self.health.record_error(str(e))
            self.updated_at = datetime.now()
            return False
    
    def disconnect(self) -> bool:
        """断开网关连接"""
        if not self.is_connected:
            return True
        
        try:
            self.status = GatewayStatus.DISCONNECTING
            # 这里应该实现实际的断开逻辑
            
            self.is_connected = False
            self.status = GatewayStatus.DISCONNECTED
            self.last_disconnection = datetime.now()
            self.updated_at = datetime.now()
            
            return True
            
        except Exception as e:
            self.status = GatewayStatus.ERROR
            self.health.record_error(str(e))
            self.updated_at = datetime.now()
            return False
    
    def update_health(self, response_time: float = None):
        """更新健康状态"""
        self.health.update_heartbeat(response_time)
        self.updated_at = datetime.now()
    
    def record_error(self, error_message: str):
        """记录错误"""
        self.health.record_error(error_message)
        self.updated_at = datetime.now()
    
    def get_connection_uptime(self) -> Optional[float]:
        """获取连接运行时间"""
        if not self.last_connection:
            return None
        
        if self.is_connected:
            return (datetime.now() - self.last_connection).total_seconds()
        else:
            return None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "gateway_id": self.gateway_id,
            "gateway_name": self.gateway_name,
            "gateway_type": self.gateway_type.value,
            "status": self.status.value,
            "connection_info": self.connection_info.to_dict(),
            "is_connected": self.is_connected,
            "last_connection": self.last_connection.isoformat() if self.last_connection else None,
            "last_disconnection": self.last_disconnection.isoformat() if self.last_disconnection else None,
            "health": self.health.to_dict(),
            "description": self.description,
            "version": self.version,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "auto_reconnect": self.auto_reconnect,
            "max_reconnect_attempts": self.max_reconnect_attempts,
            "heartbeat_interval": self.heartbeat_interval,
            "timeout": self.timeout
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TradingGateway':
        """从字典创建"""
        # 处理枚举类型
        if 'gateway_type' in data and isinstance(data['gateway_type'], str):
            data['gateway_type'] = GatewayType(data['gateway_type'])
        
        if 'status' in data and isinstance(data['status'], str):
            data['status'] = GatewayStatus(data['status'])
        
        # 处理连接信息
        if 'connection_info' in data:
            data['connection_info'] = ConnectionInfo.from_dict(data['connection_info'])
        
        # 处理健康状态
        if 'health' in data:
            data['health'] = GatewayHealth(**data['health'])
        
        # 处理时间字段
        for time_field in ['created_at', 'updated_at', 'last_connection', 'last_disconnection']:
            if time_field in data and data[time_field]:
                data[time_field] = datetime.fromisoformat(data[time_field])
        
        return cls(**data)
    
    def __post_init__(self):
        """初始化后处理"""
        if not self.gateway_id:
            self.gateway_id = str(uuid.uuid4())
        
        if not self.created_at:
            self.created_at = datetime.now()
        
        if not self.updated_at:
            self.updated_at = datetime.now()
