"""
RedFire 安全防护系统集成模块
===========================

TODO-15: 安全防护机制优化
提供安全防护系统的统一集成和配置接口

功能特性：
- 🔧 一键集成所有安全组件
- ⚙️ 统一配置管理
- 🚀 FastAPI完整集成
- 📊 安全仪表板API
- 🛡️ 中间件链管理
"""

import logging
import asyncio
from typing import Optional
from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.middleware.base import BaseHTTPMiddleware

from .security_config import SecurityConfigManager, security_config
from .security_middleware import SecurityMiddleware, create_security_middleware, get_csrf_token
from .rate_limiter import SmartRateLimiter, RateLimitResult
from .security_monitor import SecurityMonitor, SecurityEvent, EventType, SecurityLevel


logger = logging.getLogger(__name__)


class SecurityIntegration:
    """安全防护系统集成器"""
    
    def __init__(self, app: FastAPI, config: Optional[SecurityConfigManager] = None):
        self.app = app
        self.config = config or security_config
        
        # 初始化安全组件
        self.security_middleware = create_security_middleware(self.config)
        self.rate_limiter = SmartRateLimiter(self.config)
        self.security_monitor = SecurityMonitor(self.config)
        
        # 集成到FastAPI
        self._integrate_middleware()
        self._setup_security_routes()
        
        logger.info("RedFire安全防护系统集成完成")
    
    def _integrate_middleware(self):
        """集成中间件"""
        # 添加安全中间件
        self.app.add_middleware(SecurityMiddleware, config=self.config)
        
        # 添加速率限制中间件
        @self.app.middleware("http")
        async def rate_limit_middleware(request: Request, call_next):
            try:
                # 获取用户ID（如果已认证）
                user_id = getattr(request.state, 'user_id', None)
                
                # 检查限流
                limit_result = await self.rate_limiter.check_rate_limit(request, user_id)
                
                if not limit_result.allowed:
                    # 记录限流事件
                    await self._record_rate_limit_event(request, limit_result)
                    
                    return JSONResponse(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        content={
                            "error": "Rate limit exceeded",
                            "retry_after": limit_result.retry_after,
                            "limit": limit_result.limit,
                            "remaining": limit_result.remaining
                        },
                        headers={
                            "X-RateLimit-Limit": str(limit_result.limit),
                            "X-RateLimit-Remaining": str(limit_result.remaining),
                            "X-RateLimit-Reset": str(int(limit_result.reset_time.timestamp())),
                            "Retry-After": str(limit_result.retry_after or 60)
                        }
                    )
                
                # 添加限流信息到响应头
                response = await call_next(request)
                response.headers["X-RateLimit-Limit"] = str(limit_result.limit)
                response.headers["X-RateLimit-Remaining"] = str(limit_result.remaining)
                response.headers["X-RateLimit-Reset"] = str(int(limit_result.reset_time.timestamp()))
                
                return response
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"限流中间件异常: {e}")
                # 在异常情况下允许请求通过
                return await call_next(request)
    
    def _setup_security_routes(self):
        """设置安全路由"""
        
        @self.app.get("/api/security/status")
        async def security_status():
            """获取安全状态"""
            return await self.security_monitor.get_security_dashboard()
        
        @self.app.get("/api/security/csrf-token")
        async def get_csrf_token_endpoint(request: Request):
            """获取CSRF令牌"""
            # 从认证信息获取会话ID
            session_id = request.headers.get("Authorization", "")
            if session_id.startswith("Bearer "):
                session_id = session_id[7:]
            
            if not session_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="需要认证才能获取CSRF令牌"
                )
            
            token = get_csrf_token(session_id, self.config)
            return {"csrf_token": token}
        
        @self.app.get("/api/security/rate-limits")
        async def get_rate_limits(request: Request):
            """获取当前用户的限流状态"""
            client_ip = self._get_client_ip(request)
            user_id = getattr(request.state, 'user_id', None)
            
            status_info = await self.rate_limiter.get_rate_limit_status(client_ip, user_id)
            return status_info
        
        @self.app.post("/api/security/report-incident")
        async def report_security_incident(request: Request, incident_data: dict):
            """报告安全事件"""
            client_ip = self._get_client_ip(request)
            user_id = getattr(request.state, 'user_id', None)
            
            # 创建安全事件
            event = SecurityEvent(
                event_id=f"manual_{int(asyncio.get_event_loop().time())}",
                event_type=EventType.SUSPICIOUS_ACTIVITY,
                severity=SecurityLevel.MEDIUM,
                timestamp=asyncio.get_event_loop().time(),
                source_ip=client_ip,
                user_id=user_id,
                user_agent=str(request.headers.get("user-agent", "")),
                request_path=str(request.url.path),
                event_data=incident_data,
                risk_score=0.5,
                blocked=False,
                description=f"用户报告的安全事件: {incident_data.get('description', 'N/A')}"
            )
            
            await self.security_monitor.record_event(event)
            
            return {"message": "安全事件已记录", "event_id": event.event_id}
        
        @self.app.get("/api/security/alerts")
        async def get_security_alerts():
            """获取安全告警列表"""
            alerts = list(self.security_monitor.alert_manager.active_alerts.values())
            return {
                "alerts": [
                    {
                        "alert_id": alert.alert_id,
                        "title": alert.title,
                        "severity": alert.severity,
                        "created_at": alert.created_at.isoformat(),
                        "acknowledged": alert.acknowledged,
                        "resolved": alert.resolved_at is not None,
                        "event_count": len(alert.events)
                    }
                    for alert in alerts
                ]
            }
        
        @self.app.post("/api/security/alerts/{alert_id}/acknowledge")
        async def acknowledge_alert(alert_id: str, request: Request):
            """确认告警"""
            user_id = getattr(request.state, 'user_id', 'system')
            self.security_monitor.alert_manager.acknowledge_alert(alert_id, user_id)
            return {"message": "告警已确认"}
        
        @self.app.post("/api/security/alerts/{alert_id}/resolve")
        async def resolve_alert(alert_id: str):
            """解决告警"""
            self.security_monitor.alert_manager.resolve_alert(alert_id)
            return {"message": "告警已解决"}
        
        @self.app.get("/api/security/config")
        async def get_security_config():
            """获取安全配置（脱敏）"""
            config_dict = self.config.export_config()
            
            # 脱敏处理
            sensitive_fields = ['jwt_secret_key', 'smtp_password', 'webhook_url']
            for field in sensitive_fields:
                if field in config_dict:
                    config_dict[field] = "***"
            
            return config_dict
    
    async def _record_rate_limit_event(self, request: Request, limit_result: RateLimitResult):
        """记录限流事件"""
        client_ip = self._get_client_ip(request)
        user_id = getattr(request.state, 'user_id', None)
        
        event = SecurityEvent(
            event_id=f"ratelimit_{int(asyncio.get_event_loop().time())}",
            event_type=EventType.SUSPICIOUS_ACTIVITY,
            severity=SecurityLevel.LOW,
            timestamp=asyncio.get_event_loop().time(),
            source_ip=client_ip,
            user_id=user_id,
            user_agent=str(request.headers.get("user-agent", "")),
            request_path=str(request.url.path),
            event_data={
                "rule_name": limit_result.rule_name,
                "current_usage": limit_result.current_usage,
                "limit": limit_result.limit,
                "retry_after": limit_result.retry_after
            },
            risk_score=0.3,
            blocked=True,
            description=f"触发限流规则: {limit_result.rule_name}"
        )
        
        await self.security_monitor.record_event(event)
    
    def _get_client_ip(self, request: Request) -> str:
        """获取客户端IP"""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"
    
    async def record_security_event(
        self,
        event_type: EventType,
        request: Request,
        severity: SecurityLevel = SecurityLevel.MEDIUM,
        description: str = "",
        event_data: dict = None,
        blocked: bool = False
    ):
        """记录安全事件的便捷方法"""
        client_ip = self._get_client_ip(request)
        user_id = getattr(request.state, 'user_id', None)
        
        event = SecurityEvent(
            event_id=f"{event_type.value}_{int(asyncio.get_event_loop().time())}",
            event_type=event_type,
            severity=severity,
            timestamp=asyncio.get_event_loop().time(),
            source_ip=client_ip,
            user_id=user_id,
            user_agent=str(request.headers.get("user-agent", "")),
            request_path=str(request.url.path),
            event_data=event_data or {},
            risk_score=self._calculate_risk_score(severity, event_type),
            blocked=blocked,
            description=description
        )
        
        await self.security_monitor.record_event(event)
        return event
    
    def _calculate_risk_score(self, severity: SecurityLevel, event_type: EventType) -> float:
        """计算风险分数"""
        base_scores = {
            SecurityLevel.LOW: 0.2,
            SecurityLevel.MEDIUM: 0.5,
            SecurityLevel.HIGH: 0.8,
            SecurityLevel.CRITICAL: 1.0
        }
        
        event_multipliers = {
            EventType.SQL_INJECTION: 1.2,
            EventType.XSS_ATTACK: 1.1,
            EventType.DDOS_ATTACK: 1.3,
            EventType.SYSTEM_COMPROMISE: 1.5,
            EventType.DATA_EXFILTRATION: 1.4,
        }
        
        base_score = base_scores.get(severity, 0.5)
        multiplier = event_multipliers.get(event_type, 1.0)
        
        return min(1.0, base_score * multiplier)


# 便捷的集成函数
def setup_security(app: FastAPI, config: Optional[SecurityConfigManager] = None) -> SecurityIntegration:
    """
    一键设置安全防护系统
    
    Args:
        app: FastAPI应用实例
        config: 安全配置（可选，默认使用全局配置）
    
    Returns:
        SecurityIntegration: 安全集成实例
    """
    integration = SecurityIntegration(app, config)
    
    # 添加启动事件
    @app.on_event("startup")
    async def security_startup():
        logger.info("安全防护系统已启动")
        
        # 验证配置
        warnings = integration.config.validate_config()
        for warning in warnings:
            logger.warning(f"安全配置警告: {warning}")
    
    @app.on_event("shutdown")
    async def security_shutdown():
        logger.info("安全防护系统已关闭")
    
    return integration


# 安全事件装饰器
def log_security_event(
    event_type: EventType,
    severity: SecurityLevel = SecurityLevel.MEDIUM,
    description: str = ""
):
    """安全事件记录装饰器"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # 查找Request参数
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            if not request:
                # 从kwargs查找
                request = kwargs.get('request')
            
            try:
                result = await func(*args, **kwargs)
                
                # 记录成功事件
                if request and hasattr(request.app, 'security_integration'):
                    await request.app.security_integration.record_security_event(
                        event_type=event_type,
                        request=request,
                        severity=SecurityLevel.LOW,
                        description=f"操作成功: {description}",
                        blocked=False
                    )
                
                return result
                
            except Exception as e:
                # 记录失败事件
                if request and hasattr(request.app, 'security_integration'):
                    await request.app.security_integration.record_security_event(
                        event_type=event_type,
                        request=request,
                        severity=severity,
                        description=f"操作失败: {description} - {str(e)}",
                        event_data={"error": str(e)},
                        blocked=False
                    )
                
                raise
        
        return wrapper
    return decorator


# 示例使用
if __name__ == "__main__":
    from fastapi import FastAPI
    
    # 创建FastAPI应用
    app = FastAPI(title="RedFire Security Demo")
    
    # 一键集成安全防护
    security_integration = setup_security(app)
    
    # 示例路由
    @app.get("/")
    async def root():
        return {"message": "RedFire安全防护系统演示"}
    
    @app.get("/protected")
    @log_security_event(EventType.AUTHORIZATION_FAILURE, SecurityLevel.MEDIUM, "访问受保护资源")
    async def protected_resource(request: Request):
        return {"message": "这是受保护的资源"}
    
    print("安全防护系统集成完成，可以启动应用进行测试")
