# 🔧 RedFire外部配置管理服务 - Pydantic配置模型
# 完全舍弃DDD架构，采用简单直接的配置模型

from pydantic import BaseModel, Field, validator, SecretStr
from pydantic_settings import BaseSettings
from typing import Dict, Any, Optional, List, Union
from enum import Enum
import os
from pathlib import Path
import yaml
import json

# =============================================================================
# 基础配置枚举
# =============================================================================

class Environment(str, Enum):
    """环境枚举"""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"

class LogLevel(str, Enum):
    """日志级别枚举"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class CacheBackend(str, Enum):
    """缓存后端枚举"""
    REDIS = "redis"
    MEMORY = "memory"
    MEMCACHED = "memcached"

class DatabaseEngine(str, Enum):
    """数据库引擎枚举"""
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    SQLITE = "sqlite"

# =============================================================================
# 数据库配置模型
# =============================================================================

class DatabaseConfig(BaseSettings):
    """数据库配置模型"""
    
    # 基础连接配置
    engine: DatabaseEngine = Field(DatabaseEngine.POSTGRESQL, description="数据库引擎类型")
    host: str = Field("localhost", description="数据库主机地址")
    port: int = Field(5432, description="数据库端口", ge=1, le=65535)
    database: str = Field(..., description="数据库名称")
    username: str = Field(..., description="数据库用户名")
    password: SecretStr = Field(..., description="数据库密码")
    
    # 连接池配置
    pool_size: int = Field(20, description="连接池大小", ge=1, le=100)
    max_overflow: int = Field(30, description="连接池最大溢出", ge=0, le=50)
    pool_timeout: int = Field(30, description="连接池超时时间(秒)", ge=1, le=300)
    pool_recycle: int = Field(3600, description="连接回收时间(秒)", ge=300, le=7200)
    
    # 性能配置
    echo: bool = Field(False, description="是否输出SQL日志")
    echo_pool: bool = Field(False, description="是否输出连接池日志")
    pool_pre_ping: bool = Field(True, description="连接前是否ping检查")
    
    # SSL配置
    ssl_mode: str = Field("prefer", description="SSL模式")
    ssl_cert: Optional[str] = Field(None, description="SSL证书路径")
    ssl_key: Optional[str] = Field(None, description="SSL密钥路径")
    ssl_ca: Optional[str] = Field(None, description="SSL CA证书路径")
    
    class Config:
        env_prefix = "DB_"
        case_sensitive = False
    
    @validator('port')
    def validate_port(cls, v):
        if not 1 <= v <= 65535:
            raise ValueError('端口必须在1-65535之间')
        return v
    
    @validator('engine')
    def validate_engine(cls, v):
        if v not in DatabaseEngine:
            raise ValueError(f'不支持的数据库引擎: {v}')
        return v
    
    @property
    def url(self) -> str:
        """构建数据库连接URL"""
        password = self.password.get_secret_value()
        return f"{self.engine.value}://{self.username}:{password}@{self.host}:{self.port}/{self.database}"
    
    @property
    def async_url(self) -> str:
        """构建异步数据库连接URL"""
        if self.engine == DatabaseEngine.POSTGRESQL:
            return self.url.replace('postgresql://', 'postgresql+asyncpg://')
        elif self.engine == DatabaseEngine.MYSQL:
            return self.url.replace('mysql://', 'mysql+aiomysql://')
        else:
            return self.url

# =============================================================================
# Redis配置模型
# =============================================================================

class RedisConfig(BaseSettings):
    """Redis配置模型"""
    
    # 基础连接配置
    host: str = Field("localhost", description="Redis主机地址")
    port: int = Field(6379, description="Redis端口", ge=1, le=65535)
    db: int = Field(0, description="Redis数据库索引", ge=0, le=15)
    password: Optional[SecretStr] = Field(None, description="Redis密码")
    username: Optional[str] = Field(None, description="Redis用户名")
    
    # 连接池配置
    max_connections: int = Field(50, description="最大连接数", ge=1, le=1000)
    retry_on_timeout: bool = Field(True, description="超时时是否重试")
    socket_timeout: float = Field(5.0, description="套接字超时时间(秒)")
    socket_connect_timeout: float = Field(5.0, description="连接超时时间(秒)")
    socket_keepalive: bool = Field(True, description="是否启用keepalive")
    socket_keepalive_options: Dict[str, int] = Field(default_factory=dict, description="keepalive选项")
    
    # 集群配置
    cluster_mode: bool = Field(False, description="是否为集群模式")
    cluster_nodes: List[str] = Field(default_factory=list, description="集群节点列表")
    
    # 性能配置
    encoding: str = Field("utf-8", description="编码格式")
    decode_responses: bool = Field(True, description="是否解码响应")
    
    # SSL配置
    ssl: bool = Field(False, description="是否启用SSL")
    ssl_cert_reqs: Optional[str] = Field(None, description="SSL证书要求")
    ssl_ca_certs: Optional[str] = Field(None, description="SSL CA证书路径")
    ssl_certfile: Optional[str] = Field(None, description="SSL证书文件路径")
    ssl_keyfile: Optional[str] = Field(None, description="SSL密钥文件路径")
    
    class Config:
        env_prefix = "REDIS_"
        case_sensitive = False
    
    @validator('port')
    def validate_port(cls, v):
        if not 1 <= v <= 65535:
            raise ValueError('端口必须在1-65535之间')
        return v
    
    @validator('db')
    def validate_db(cls, v):
        if not 0 <= v <= 15:
            raise ValueError('数据库索引必须在0-15之间')
        return v
    
    @property
    def url(self) -> str:
        """构建Redis连接URL"""
        url = f"redis://"
        if self.username:
            url += f"{self.username}:"
        if self.password:
            url += f"{self.password.get_secret_value()}@"
        elif self.username:
            url += "@"
        url += f"{self.host}:{self.port}/{self.db}"
        return url

# =============================================================================
# VnPy配置模型
# =============================================================================

class VnPyGatewayConfig(BaseModel):
    """VnPy网关配置"""
    
    name: str = Field(..., description="网关名称")
    class_name: str = Field(..., description="网关类名")
    enabled: bool = Field(True, description="是否启用")
    
    # 连接配置
    host: Optional[str] = Field(None, description="服务器地址")
    port: Optional[int] = Field(None, description="服务器端口")
    username: Optional[str] = Field(None, description="用户名")
    password: Optional[SecretStr] = Field(None, description="密码")
    
    # 认证配置
    app_id: Optional[str] = Field(None, description="应用ID")
    app_secret: Optional[SecretStr] = Field(None, description="应用密钥")
    auth_code: Optional[str] = Field(None, description="授权码")
    product_info: Optional[str] = Field(None, description="产品信息")
    
    # 连接参数
    timeout: int = Field(30, description="连接超时时间(秒)", ge=1, le=300)
    retry_count: int = Field(3, description="重试次数", ge=0, le=10)
    retry_interval: int = Field(5, description="重试间隔(秒)", ge=1, le=60)
    
    # 扩展配置
    extra_config: Dict[str, Any] = Field(default_factory=dict, description="扩展配置")

class VnPyConfig(BaseSettings):
    """VnPy配置模型"""
    
    # 基础配置
    log_level: LogLevel = Field(LogLevel.INFO, description="VnPy日志级别")
    data_path: str = Field("./vnpy_data", description="VnPy数据目录")
    temp_path: str = Field("./vnpy_temp", description="VnPy临时目录")
    
    # 网关配置
    gateways: List[VnPyGatewayConfig] = Field(default_factory=list, description="网关配置列表")
    default_gateway: Optional[str] = Field(None, description="默认网关")
    
    # 策略配置
    strategy_path: str = Field("./strategies", description="策略文件路径")
    strategy_data_path: str = Field("./strategy_data", description="策略数据路径")
    
    # 数据配置
    tick_data_enabled: bool = Field(True, description="是否启用tick数据")
    bar_data_enabled: bool = Field(True, description="是否启用bar数据")
    database_config: Optional[DatabaseConfig] = Field(None, description="VnPy数据库配置")
    
    # 性能配置
    event_queue_size: int = Field(100000, description="事件队列大小", ge=1000, le=1000000)
    worker_threads: int = Field(4, description="工作线程数", ge=1, le=32)
    
    class Config:
        env_prefix = "VNPY_"
        case_sensitive = False

# =============================================================================
# 安全配置模型
# =============================================================================

class SecurityConfig(BaseSettings):
    """安全配置模型"""
    
    # JWT配置
    secret_key: SecretStr = Field(..., description="JWT密钥")
    algorithm: str = Field("HS256", description="JWT算法")
    access_token_expire_minutes: int = Field(30, description="访问令牌过期时间(分钟)", ge=1, le=10080)
    refresh_token_expire_days: int = Field(7, description="刷新令牌过期时间(天)", ge=1, le=30)
    
    # CORS配置
    cors_origins: List[str] = Field(default_factory=lambda: ["*"], description="CORS允许的源")
    cors_methods: List[str] = Field(default_factory=lambda: ["*"], description="CORS允许的方法")
    cors_headers: List[str] = Field(default_factory=lambda: ["*"], description="CORS允许的头部")
    cors_credentials: bool = Field(True, description="是否允许CORS凭证")
    
    # 速率限制配置
    rate_limit_enabled: bool = Field(True, description="是否启用速率限制")
    rate_limit_requests: int = Field(100, description="速率限制请求数", ge=1, le=10000)
    rate_limit_window: int = Field(60, description="速率限制时间窗口(秒)", ge=1, le=3600)
    
    # 加密配置
    password_hash_algorithm: str = Field("bcrypt", description="密码哈希算法")
    password_salt_rounds: int = Field(12, description="密码盐轮数", ge=4, le=20)
    
    # SSL/TLS配置
    ssl_enabled: bool = Field(False, description="是否启用SSL")
    ssl_cert_file: Optional[str] = Field(None, description="SSL证书文件路径")
    ssl_key_file: Optional[str] = Field(None, description="SSL密钥文件路径")
    
    class Config:
        env_prefix = "SECURITY_"
        case_sensitive = False
    
    @validator('secret_key')
    def validate_secret_key(cls, v):
        secret = v.get_secret_value() if isinstance(v, SecretStr) else v
        if len(secret) < 32:
            raise ValueError('JWT密钥长度必须至少32个字符')
        return v
    
    @validator('algorithm')
    def validate_algorithm(cls, v):
        allowed_algorithms = ['HS256', 'HS384', 'HS512', 'RS256', 'RS384', 'RS512']
        if v not in allowed_algorithms:
            raise ValueError(f'不支持的JWT算法: {v}，支持的算法: {allowed_algorithms}')
        return v

# =============================================================================
# 监控配置模型
# =============================================================================

class PrometheusConfig(BaseModel):
    """Prometheus配置"""
    
    enabled: bool = Field(True, description="是否启用Prometheus")
    host: str = Field("localhost", description="Prometheus主机")
    port: int = Field(9090, description="Prometheus端口")
    scrape_interval: str = Field("15s", description="抓取间隔")
    evaluation_interval: str = Field("15s", description="评估间隔")
    
class GrafanaConfig(BaseModel):
    """Grafana配置"""
    
    enabled: bool = Field(True, description="是否启用Grafana")
    host: str = Field("localhost", description="Grafana主机")
    port: int = Field(3000, description="Grafana端口")
    admin_user: str = Field("admin", description="管理员用户名")
    admin_password: SecretStr = Field(..., description="管理员密码")

class MonitoringConfig(BaseSettings):
    """监控配置模型"""
    
    # 基础配置
    enabled: bool = Field(True, description="是否启用监控")
    metrics_path: str = Field("/metrics", description="指标路径")
    health_check_path: str = Field("/health", description="健康检查路径")
    
    # Prometheus配置
    prometheus: PrometheusConfig = Field(default_factory=PrometheusConfig, description="Prometheus配置")
    
    # Grafana配置
    grafana: GrafanaConfig = Field(default_factory=lambda: GrafanaConfig(admin_password=SecretStr("admin")), description="Grafana配置")
    
    # 日志配置
    log_level: LogLevel = Field(LogLevel.INFO, description="监控日志级别")
    log_file: Optional[str] = Field(None, description="日志文件路径")
    log_rotation: bool = Field(True, description="是否启用日志轮转")
    log_max_size: str = Field("100MB", description="日志文件最大大小")
    log_backup_count: int = Field(5, description="日志备份数量")
    
    # 告警配置
    alerting_enabled: bool = Field(True, description="是否启用告警")
    webhook_url: Optional[str] = Field(None, description="告警Webhook URL")
    email_enabled: bool = Field(False, description="是否启用邮件告警")
    smtp_host: Optional[str] = Field(None, description="SMTP主机")
    smtp_port: Optional[int] = Field(587, description="SMTP端口")
    smtp_username: Optional[str] = Field(None, description="SMTP用户名")
    smtp_password: Optional[SecretStr] = Field(None, description="SMTP密码")
    
    class Config:
        env_prefix = "MONITORING_"
        case_sensitive = False

# =============================================================================
# API网关配置模型
# =============================================================================

class APIGatewayConfig(BaseSettings):
    """API网关配置模型"""
    
    # 基础配置
    host: str = Field("0.0.0.0", description="网关监听主机")
    port: int = Field(8080, description="网关监听端口", ge=1, le=65535)
    workers: int = Field(4, description="工作进程数", ge=1, le=32)
    
    # 路由配置
    api_prefix: str = Field("/api", description="API前缀")
    api_version: str = Field("v1", description="API版本")
    docs_url: str = Field("/docs", description="文档URL")
    redoc_url: str = Field("/redoc", description="ReDoc URL")
    openapi_url: str = Field("/openapi.json", description="OpenAPI规范URL")
    
    # 超时配置
    request_timeout: int = Field(30, description="请求超时时间(秒)", ge=1, le=300)
    keep_alive_timeout: int = Field(5, description="Keep-Alive超时时间(秒)", ge=1, le=60)
    
    # 限制配置
    max_request_size: int = Field(16 * 1024 * 1024, description="最大请求大小(字节)")
    max_concurrent_requests: int = Field(1000, description="最大并发请求数", ge=1, le=10000)
    
    # 服务发现配置
    service_discovery_enabled: bool = Field(True, description="是否启用服务发现")
    consul_host: str = Field("localhost", description="Consul主机")
    consul_port: int = Field(8500, description="Consul端口")
    
    # 负载均衡配置
    load_balancer_algorithm: str = Field("round_robin", description="负载均衡算法")
    health_check_interval: int = Field(30, description="健康检查间隔(秒)")
    
    class Config:
        env_prefix = "GATEWAY_"
        case_sensitive = False

# =============================================================================
# 主配置模型
# =============================================================================

class AppConfig(BaseSettings):
    """应用主配置模型"""
    
    # 基础配置
    app_name: str = Field("RedFire Config Service", description="应用名称")
    app_version: str = Field("1.0.0", description="应用版本")
    environment: Environment = Field(Environment.DEVELOPMENT, description="运行环境")
    debug: bool = Field(False, description="是否启用调试模式")
    
    # 服务配置
    host: str = Field("0.0.0.0", description="服务监听主机")
    port: int = Field(8000, description="服务监听端口", ge=1, le=65535)
    workers: int = Field(1, description="工作进程数", ge=1, le=32)
    
    # 日志配置
    log_level: LogLevel = Field(LogLevel.INFO, description="日志级别")
    log_format: str = Field("%(asctime)s - %(name)s - %(levelname)s - %(message)s", description="日志格式")
    
    # 组件配置
    database: DatabaseConfig = Field(..., description="数据库配置")
    redis: RedisConfig = Field(default_factory=RedisConfig, description="Redis配置")
    vnpy: VnPyConfig = Field(default_factory=VnPyConfig, description="VnPy配置")
    security: SecurityConfig = Field(..., description="安全配置")
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig, description="监控配置")
    api_gateway: APIGatewayConfig = Field(default_factory=APIGatewayConfig, description="API网关配置")
    
    # 扩展配置
    extra_config: Dict[str, Any] = Field(default_factory=dict, description="扩展配置字段")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        # 允许嵌套环境变量，使用双下划线分隔
        env_nested_delimiter = "__"
        
        @classmethod
        def customise_sources(
            cls,
            init_settings,
            env_settings,
            file_secret_settings,
        ):
            """自定义配置源优先级"""
            return (
                init_settings,  # 最高优先级：直接传入的参数
                env_settings,   # 中等优先级：环境变量
                file_secret_settings,  # 最低优先级：文件配置
            )
    
    @validator('environment')
    def validate_environment(cls, v):
        if v == Environment.PRODUCTION and cls.__fields__['debug'].default:
            raise ValueError('生产环境不能启用调试模式')
        return v
    
    @validator('workers')
    def validate_workers(cls, v):
        import os
        cpu_count = os.cpu_count() or 1
        if v > cpu_count * 2:
            raise ValueError(f'工作进程数不能超过CPU核心数的2倍 (当前CPU核心数: {cpu_count})')
        return v
    
    def is_development(self) -> bool:
        """是否为开发环境"""
        return self.environment == Environment.DEVELOPMENT
    
    def is_production(self) -> bool:
        """是否为生产环境"""
        return self.environment == Environment.PRODUCTION
    
    def is_testing(self) -> bool:
        """是否为测试环境"""
        return self.environment == Environment.TESTING

# =============================================================================
# 配置工厂函数
# =============================================================================

def create_config_from_dict(config_dict: Dict[str, Any]) -> AppConfig:
    """从字典创建配置"""
    return AppConfig(**config_dict)

def create_config_from_file(config_file: Union[str, Path]) -> AppConfig:
    """从文件创建配置"""
    config_path = Path(config_file)
    
    if not config_path.exists():
        raise FileNotFoundError(f"配置文件不存在: {config_path}")
    
    # 根据文件扩展名选择解析器
    if config_path.suffix.lower() in ['.yml', '.yaml']:
        with open(config_path, 'r', encoding='utf-8') as f:
            config_dict = yaml.safe_load(f)
    elif config_path.suffix.lower() == '.json':
        with open(config_path, 'r', encoding='utf-8') as f:
            config_dict = json.load(f)
    else:
        raise ValueError(f"不支持的配置文件格式: {config_path.suffix}")
    
    return create_config_from_dict(config_dict)

def create_config_from_env() -> AppConfig:
    """从环境变量创建配置"""
    return AppConfig()

# =============================================================================
# 配置验证函数
# =============================================================================

def validate_config(config: AppConfig) -> List[str]:
    """验证配置完整性"""
    errors = []
    
    # 验证数据库连接
    try:
        db_url = config.database.url
        if not db_url:
            errors.append("数据库连接URL为空")
    except Exception as e:
        errors.append(f"数据库配置错误: {e}")
    
    # 验证Redis连接
    try:
        redis_url = config.redis.url
        if not redis_url:
            errors.append("Redis连接URL为空")
    except Exception as e:
        errors.append(f"Redis配置错误: {e}")
    
    # 验证安全配置
    if config.is_production():
        secret_key = config.security.secret_key.get_secret_value()
        if len(secret_key) < 32:
            errors.append("生产环境JWT密钥长度必须至少32个字符")
        
        if config.debug:
            errors.append("生产环境不能启用调试模式")
    
    # 验证监控配置
    if config.monitoring.enabled:
        if config.monitoring.email_enabled:
            if not config.monitoring.smtp_host:
                errors.append("启用邮件告警时必须配置SMTP主机")
    
    return errors

# =============================================================================
# 配置导出函数
# =============================================================================

def export_config_template(output_path: Union[str, Path], format: str = "yaml") -> None:
    """导出配置模板"""
    # 创建示例配置
    example_config = {
        "app_name": "RedFire Config Service",
        "app_version": "1.0.0",
        "environment": "development",
        "debug": True,
        "host": "0.0.0.0",
        "port": 8000,
        "workers": 1,
        "log_level": "INFO",
        "database": {
            "engine": "postgresql",
            "host": "localhost",
            "port": 5432,
            "database": "redfire",
            "username": "redfire",
            "password": "password",
            "pool_size": 20,
            "max_overflow": 30
        },
        "redis": {
            "host": "localhost",
            "port": 6379,
            "db": 0,
            "max_connections": 50
        },
        "security": {
            "secret_key": "your-super-secret-jwt-key-min-32-chars",
            "algorithm": "HS256",
            "access_token_expire_minutes": 30
        },
        "monitoring": {
            "enabled": True,
            "log_level": "INFO"
        }
    }
    
    output_path = Path(output_path)
    
    if format.lower() in ['yml', 'yaml']:
        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(example_config, f, default_flow_style=False, allow_unicode=True, indent=2)
    elif format.lower() == 'json':
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(example_config, f, indent=2, ensure_ascii=False)
    else:
        raise ValueError(f"不支持的格式: {format}")

if __name__ == "__main__":
    # 示例用法
    print("🔧 RedFire配置模型示例")
    
    # 1. 从环境变量创建配置
    try:
        config = create_config_from_env()
        print("✅ 从环境变量创建配置成功")
    except Exception as e:
        print(f"❌ 从环境变量创建配置失败: {e}")
    
    # 2. 导出配置模板
    try:
        export_config_template("config_template.yaml", "yaml")
        print("✅ 配置模板导出成功: config_template.yaml")
    except Exception as e:
        print(f"❌ 配置模板导出失败: {e}")
