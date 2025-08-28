"""
RedFire 企业级安全防护中间件
==========================

TODO-15: 安全防护机制优化
提供全面的Web应用安全防护

功能特性：
- 🛡️ WAF Web应用防火墙
- 🔒 SQL注入和XSS防护
- 🌐 CSRF防护和安全响应头
- 📊 请求验证和数据清理
- 🚨 威胁检测和阻断
"""

import re
import json
import hashlib
import secrets
import ipaddress
import asyncio
import logging
from typing import Dict, List, Optional, Set, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import redis.asyncio as redis

from .security_config import SecurityConfigManager, ProtectionMode, SecurityLevel


logger = logging.getLogger(__name__)


@dataclass
class SecurityThreat:
    """安全威胁记录"""
    threat_type: str
    severity: SecurityLevel
    source_ip: str
    user_agent: str
    request_path: str
    threat_data: Dict[str, Any]
    timestamp: datetime
    blocked: bool


class SecurityPattern:
    """安全检测模式库"""
    
    # SQL注入检测模式
    SQL_INJECTION_PATTERNS = [
        r'(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b)',
        r'(\b(OR|AND)\s+\d+\s*=\s*\d+)',
        r'(\b(OR|AND)\s+[\'"]?\w+[\'"]?\s*=\s*[\'"]?\w+[\'"]?)',
        r'([\'"]\s*;\s*(DROP|DELETE|INSERT|UPDATE|CREATE|ALTER))',
        r'(\bUNION\s+SELECT\b)',
        r'(\/\*.*\*\/)',
        r'(--\s*[^\r\n]*)',
        r'(\b(EXEC|EXECUTE)\s*\()',
        r'(\b(CHAR|NCHAR|VARCHAR|NVARCHAR)\s*\()',
        r'(\b(CAST|CONVERT)\s*\()',
        r'(\b(WAITFOR|DELAY)\s*[\'"]?\d+[\'"]?)',
        r'(\b(XP_|SP_)\w+)',
        r'(\b(LOAD_FILE|INTO\s+OUTFILE|INTO\s+DUMPFILE)\b)',
        r'(\b(BENCHMARK|SLEEP)\s*\()'
    ]
    
    # XSS检测模式
    XSS_PATTERNS = [
        r'(<script[^>]*>.*?</script>)',
        r'(<iframe[^>]*>.*?</iframe>)',
        r'(<object[^>]*>.*?</object>)',
        r'(<embed[^>]*>.*?</embed>)',
        r'(<form[^>]*>.*?</form>)',
        r'(javascript:)',
        r'(vbscript:)',
        r'(on\w+\s*=)',
        r'(<img[^>]*src\s*=\s*[\'"]?javascript:)',
        r'(<a[^>]*href\s*=\s*[\'"]?javascript:)',
        r'(expression\s*\()',
        r'(@import)',
        r'(eval\s*\()',
        r'(document\.write)',
        r'(document\.cookie)',
        r'(window\.location)',
        r'(alert\s*\()',
        r'(confirm\s*\()',
        r'(prompt\s*\()'
    ]
    
    # 命令注入检测模式
    COMMAND_INJECTION_PATTERNS = [
        r'(;\s*(ls|dir|cat|type|more|less|head|tail|pwd|whoami|id|uname)\b)',
        r'(\|\s*(ls|dir|cat|type|more|less|head|tail|pwd|whoami|id|uname)\b)',
        r'(&\s*(ls|dir|cat|type|more|less|head|tail|pwd|whoami|id|uname)\b)',
        r'(`[^`]*`)',
        r'(\$\([^)]*\))',
        r'(>\s*/[a-z/]*)',
        r'(<\s*/[a-z/]*)',
        r'(\|\s*nc\b)',
        r'(\|\s*netcat\b)',
        r'(\|\s*telnet\b)',
        r'(\|\s*ssh\b)',
        r'(\|\s*curl\b)',
        r'(\|\s*wget\b)',
        r'(rm\s+-rf)',
        r'(chmod\s+\d+)',
        r'(chown\s+)',
        r'(kill\s+-\d+)'
    ]
    
    # 路径遍历检测模式
    PATH_TRAVERSAL_PATTERNS = [
        r'(\.\.\/)',
        r'(\.\.\\)',
        r'(%2e%2e%2f)',
        r'(%2e%2e%5c)',
        r'(%252e%252e%252f)',
        r'(%252e%252e%255c)',
        r'(\/etc\/passwd)',
        r'(\/etc\/shadow)',
        r'(\/etc\/hosts)',
        r'(\/proc\/)',
        r'(\/sys\/)',
        r'(\\windows\\system32\\)',
        r'(\\boot\.ini)',
        r'(\\windows\\win\.ini)'
    ]
    
    # 恶意用户代理检测
    MALICIOUS_USER_AGENTS = [
        'sqlmap', 'nmap', 'nikto', 'burp', 'zaproxy', 'w3af', 'arachni',
        'acunetix', 'nessus', 'openvas', 'metasploit', 'beef', 'havij',
        'pangolin', 'sqlninja', 'bsqlbf', 'bobcat', 'n-stealth'
    ]
    
    @classmethod
    def compile_patterns(cls):
        """编译正则表达式模式"""
        cls.sql_injection_regex = [re.compile(pattern, re.IGNORECASE) for pattern in cls.SQL_INJECTION_PATTERNS]
        cls.xss_regex = [re.compile(pattern, re.IGNORECASE) for pattern in cls.XSS_PATTERNS]
        cls.command_injection_regex = [re.compile(pattern, re.IGNORECASE) for pattern in cls.COMMAND_INJECTION_PATTERNS]
        cls.path_traversal_regex = [re.compile(pattern, re.IGNORECASE) for pattern in cls.PATH_TRAVERSAL_PATTERNS]


# 编译模式
SecurityPattern.compile_patterns()


class WAFEngine:
    """Web应用防火墙引擎"""
    
    def __init__(self, config: SecurityConfigManager):
        self.config = config
        self.redis_client: Optional[redis.Redis] = None
        self._setup_redis()
    
    async def _setup_redis(self):
        """设置Redis连接"""
        try:
            self.redis_client = redis.Redis(
                host=os.getenv("REDIS_HOST", "localhost"),
                port=int(os.getenv("REDIS_PORT", "6379")),
                decode_responses=True
            )
            await self.redis_client.ping()
        except Exception as e:
            logger.warning(f"Redis连接失败，使用内存存储: {e}")
            self.redis_client = None
    
    async def analyze_request(self, request: Request) -> Optional[SecurityThreat]:
        """分析请求安全性"""
        threats = []
        
        # 1. IP安全检查
        client_ip = self._get_client_ip(request)
        if not self.config.network.is_ip_allowed(client_ip):
            threats.append(SecurityThreat(
                threat_type="blocked_ip",
                severity=SecurityLevel.HIGH,
                source_ip=client_ip,
                user_agent=str(request.headers.get("user-agent", "")),
                request_path=str(request.url.path),
                threat_data={"reason": "IP not allowed"},
                timestamp=datetime.now(),
                blocked=True
            ))
        
        # 2. 用户代理检查
        user_agent = str(request.headers.get("user-agent", "")).lower()
        for malicious_ua in SecurityPattern.MALICIOUS_USER_AGENTS:
            if malicious_ua in user_agent:
                threats.append(SecurityThreat(
                    threat_type="malicious_user_agent",
                    severity=SecurityLevel.HIGH,
                    source_ip=client_ip,
                    user_agent=user_agent,
                    request_path=str(request.url.path),
                    threat_data={"detected_pattern": malicious_ua},
                    timestamp=datetime.now(),
                    blocked=True
                ))
        
        # 3. 请求参数检查
        if self.config.waf.enabled:
            # URL参数检查
            for key, value in request.query_params.items():
                threat = await self._check_parameter_security(
                    param_name=key,
                    param_value=value,
                    param_type="query",
                    request=request
                )
                if threat:
                    threats.append(threat)
            
            # 请求体检查
            if request.method in ["POST", "PUT", "PATCH"]:
                body_threat = await self._check_request_body(request)
                if body_threat:
                    threats.append(body_threat)
        
        # 4. 路径检查
        path_threat = await self._check_path_security(request)
        if path_threat:
            threats.append(path_threat)
        
        # 返回最严重的威胁
        if threats:
            threats.sort(key=lambda x: ["LOW", "MEDIUM", "HIGH", "CRITICAL"].index(x.severity))
            return threats[-1]  # 返回最严重的威胁
        
        return None
    
    async def _check_parameter_security(
        self, 
        param_name: str, 
        param_value: str, 
        param_type: str, 
        request: Request
    ) -> Optional[SecurityThreat]:
        """检查参数安全性"""
        client_ip = self._get_client_ip(request)
        user_agent = str(request.headers.get("user-agent", ""))
        
        # SQL注入检查
        if self.config.waf.sql_injection_protection:
            for pattern in SecurityPattern.sql_injection_regex:
                if pattern.search(param_value):
                    return SecurityThreat(
                        threat_type="sql_injection",
                        severity=self.config.waf.sql_injection_sensitivity,
                        source_ip=client_ip,
                        user_agent=user_agent,
                        request_path=str(request.url.path),
                        threat_data={
                            "parameter": param_name,
                            "value": param_value[:100],  # 限制记录长度
                            "pattern": pattern.pattern,
                            "type": param_type
                        },
                        timestamp=datetime.now(),
                        blocked=self.config.waf.protection_mode != ProtectionMode.MONITOR
                    )
        
        # XSS检查
        if self.config.waf.xss_protection:
            for pattern in SecurityPattern.xss_regex:
                if pattern.search(param_value):
                    return SecurityThreat(
                        threat_type="xss_attack",
                        severity=self.config.waf.xss_sensitivity,
                        source_ip=client_ip,
                        user_agent=user_agent,
                        request_path=str(request.url.path),
                        threat_data={
                            "parameter": param_name,
                            "value": param_value[:100],
                            "pattern": pattern.pattern,
                            "type": param_type
                        },
                        timestamp=datetime.now(),
                        blocked=self.config.waf.protection_mode != ProtectionMode.MONITOR
                    )
        
        # 命令注入检查
        if self.config.waf.command_injection_protection:
            for pattern in SecurityPattern.command_injection_regex:
                if pattern.search(param_value):
                    return SecurityThreat(
                        threat_type="command_injection",
                        severity=SecurityLevel.HIGH,
                        source_ip=client_ip,
                        user_agent=user_agent,
                        request_path=str(request.url.path),
                        threat_data={
                            "parameter": param_name,
                            "value": param_value[:100],
                            "pattern": pattern.pattern,
                            "type": param_type
                        },
                        timestamp=datetime.now(),
                        blocked=self.config.waf.protection_mode != ProtectionMode.MONITOR
                    )
        
        return None
    
    async def _check_request_body(self, request: Request) -> Optional[SecurityThreat]:
        """检查请求体安全性"""
        try:
            # 读取请求体
            body = await request.body()
            if not body:
                return None
            
            body_str = body.decode('utf-8', errors='ignore')
            content_type = request.headers.get("content-type", "")
            
            # JSON数据检查
            if "application/json" in content_type:
                try:
                    json_data = json.loads(body_str)
                    return await self._check_json_security(json_data, request)
                except json.JSONDecodeError:
                    pass
            
            # 表单数据检查
            elif "application/x-www-form-urlencoded" in content_type:
                # 简单的表单数据解析和检查
                for param in body_str.split('&'):
                    if '=' in param:
                        key, value = param.split('=', 1)
                        threat = await self._check_parameter_security(
                            param_name=key,
                            param_value=value,
                            param_type="form",
                            request=request
                        )
                        if threat:
                            return threat
            
            # 文件上传检查
            elif "multipart/form-data" in content_type:
                return await self._check_file_upload_security(request)
        
        except Exception as e:
            logger.warning(f"请求体安全检查失败: {e}")
        
        return None
    
    async def _check_json_security(self, json_data: Any, request: Request) -> Optional[SecurityThreat]:
        """检查JSON数据安全性"""
        def check_value(value: Any, path: str = "") -> Optional[SecurityThreat]:
            if isinstance(value, str):
                threat = asyncio.create_task(self._check_parameter_security(
                    param_name=path or "json_field",
                    param_value=value,
                    param_type="json",
                    request=request
                ))
                return asyncio.run(threat)
            elif isinstance(value, dict):
                for k, v in value.items():
                    threat = check_value(v, f"{path}.{k}" if path else k)
                    if threat:
                        return threat
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    threat = check_value(item, f"{path}[{i}]" if path else f"[{i}]")
                    if threat:
                        return threat
            return None
        
        return check_value(json_data)
    
    async def _check_file_upload_security(self, request: Request) -> Optional[SecurityThreat]:
        """检查文件上传安全性"""
        if not self.config.waf.file_upload_protection:
            return None
        
        # 这里应该实现文件上传的详细检查
        # 包括文件类型、大小、内容扫描等
        # 由于需要解析multipart数据，这里简化实现
        
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.config.waf.max_file_size:
            return SecurityThreat(
                threat_type="oversized_upload",
                severity=SecurityLevel.MEDIUM,
                source_ip=self._get_client_ip(request),
                user_agent=str(request.headers.get("user-agent", "")),
                request_path=str(request.url.path),
                threat_data={
                    "file_size": content_length,
                    "max_allowed": self.config.waf.max_file_size
                },
                timestamp=datetime.now(),
                blocked=True
            )
        
        return None
    
    async def _check_path_security(self, request: Request) -> Optional[SecurityThreat]:
        """检查请求路径安全性"""
        path = str(request.url.path)
        
        # 路径遍历检查
        if self.config.waf.path_traversal_protection:
            for pattern in SecurityPattern.path_traversal_regex:
                if pattern.search(path):
                    return SecurityThreat(
                        threat_type="path_traversal",
                        severity=SecurityLevel.HIGH,
                        source_ip=self._get_client_ip(request),
                        user_agent=str(request.headers.get("user-agent", "")),
                        request_path=path,
                        threat_data={
                            "pattern": pattern.pattern,
                            "detected_path": path
                        },
                        timestamp=datetime.now(),
                        blocked=True
                    )
        
        return None
    
    def _get_client_ip(self, request: Request) -> str:
        """获取客户端真实IP"""
        # 考虑代理和负载均衡器
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"


class CSRFProtection:
    """CSRF防护"""
    
    def __init__(self, config: SecurityConfigManager):
        self.config = config
        self.token_expiry = timedelta(seconds=config.waf.csrf_token_expiry)
    
    def generate_csrf_token(self, session_id: str) -> str:
        """生成CSRF令牌"""
        timestamp = int(datetime.now().timestamp())
        data = f"{session_id}:{timestamp}"
        signature = hashlib.sha256(
            f"{data}:{self.config.get_jwt_secret_key()}".encode()
        ).hexdigest()
        token = f"{timestamp}.{signature}"
        return token
    
    def verify_csrf_token(self, token: str, session_id: str) -> bool:
        """验证CSRF令牌"""
        if not token or '.' not in token:
            return False
        
        try:
            timestamp_str, signature = token.split('.', 1)
            timestamp = int(timestamp_str)
            
            # 检查令牌是否过期
            token_time = datetime.fromtimestamp(timestamp)
            if datetime.now() - token_time > self.token_expiry:
                return False
            
            # 验证签名
            data = f"{session_id}:{timestamp}"
            expected_signature = hashlib.sha256(
                f"{data}:{self.config.get_jwt_secret_key()}".encode()
            ).hexdigest()
            
            return signature == expected_signature
        
        except (ValueError, IndexError):
            return False


class SecurityHeadersManager:
    """安全响应头管理器"""
    
    def __init__(self, config: SecurityConfigManager):
        self.config = config
    
    def apply_security_headers(self, response: Response):
        """应用安全响应头"""
        headers_config = self.config.headers
        
        # 基础安全头
        response.headers["X-Content-Type-Options"] = headers_config.x_content_type_options
        response.headers["X-Frame-Options"] = headers_config.x_frame_options
        response.headers["X-XSS-Protection"] = headers_config.x_xss_protection
        
        # HSTS
        if headers_config.strict_transport_security:
            hsts_value = f"max-age={headers_config.hsts_max_age}"
            if headers_config.hsts_include_subdomains:
                hsts_value += "; includeSubDomains"
            if headers_config.hsts_preload:
                hsts_value += "; preload"
            response.headers["Strict-Transport-Security"] = hsts_value
        
        # CSP
        if headers_config.content_security_policy:
            csp_parts = [
                f"default-src {headers_config.csp_default_src}",
                f"script-src {headers_config.csp_script_src}",
                f"style-src {headers_config.csp_style_src}",
                f"img-src {headers_config.csp_img_src}",
                f"font-src {headers_config.csp_font_src}",
                f"connect-src {headers_config.csp_connect_src}",
                f"frame-ancestors {headers_config.csp_frame_ancestors}"
            ]
            response.headers["Content-Security-Policy"] = "; ".join(csp_parts)
        
        # 权限策略
        if headers_config.permissions_policy:
            permissions_parts = [
                f"camera={headers_config.permissions_camera}",
                f"microphone={headers_config.permissions_microphone}",
                f"geolocation={headers_config.permissions_geolocation}",
                f"payment={headers_config.permissions_payment}"
            ]
            response.headers["Permissions-Policy"] = ", ".join(permissions_parts)
        
        # 其他安全头
        response.headers["Referrer-Policy"] = headers_config.referrer_policy
        response.headers["Cross-Origin-Embedder-Policy"] = headers_config.cross_origin_embedder_policy
        response.headers["Cross-Origin-Opener-Policy"] = headers_config.cross_origin_opener_policy
        response.headers["Cross-Origin-Resource-Policy"] = headers_config.cross_origin_resource_policy


class SecurityMiddleware(BaseHTTPMiddleware):
    """企业级安全防护中间件"""
    
    def __init__(self, app, config: SecurityConfigManager):
        super().__init__(app)
        self.config = config
        self.waf = WAFEngine(config)
        self.csrf = CSRFProtection(config)
        self.headers_manager = SecurityHeadersManager(config)
        self.threat_cache: Dict[str, List[SecurityThreat]] = {}
        
        # 威胁计数器
        self.threat_counters: Dict[str, int] = {}
        self.last_cleanup = datetime.now()
    
    async def dispatch(self, request: Request, call_next):
        """处理请求"""
        start_time = datetime.now()
        
        try:
            # 1. 安全威胁分析
            threat = await self.waf.analyze_request(request)
            
            if threat and threat.blocked:
                # 记录威胁
                await self._record_threat(threat)
                
                # 阻断请求
                if self.config.waf.protection_mode == ProtectionMode.BLOCK:
                    return await self._create_blocked_response(threat)
            
            # 2. CSRF检查（对状态改变的请求）
            if request.method in ["POST", "PUT", "PATCH", "DELETE"]:
                csrf_valid = await self._check_csrf_protection(request)
                if not csrf_valid and self.config.waf.csrf_protection:
                    csrf_threat = SecurityThreat(
                        threat_type="csrf_attack",
                        severity=SecurityLevel.HIGH,
                        source_ip=self.waf._get_client_ip(request),
                        user_agent=str(request.headers.get("user-agent", "")),
                        request_path=str(request.url.path),
                        threat_data={"reason": "Invalid or missing CSRF token"},
                        timestamp=datetime.now(),
                        blocked=True
                    )
                    await self._record_threat(csrf_threat)
                    return await self._create_blocked_response(csrf_threat)
            
            # 3. 调用下一个中间件
            response = await call_next(request)
            
            # 4. 应用安全响应头
            self.headers_manager.apply_security_headers(response)
            
            # 5. 记录安全日志
            if self.config.monitoring.security_logging:
                await self._log_security_event(request, response, start_time)
            
            return response
        
        except HTTPException as e:
            # 记录HTTP异常
            if self.config.monitoring.audit_failed_requests:
                await self._log_security_event(request, None, start_time, error=str(e))
            raise e
        
        except Exception as e:
            # 记录未知异常
            logger.error(f"安全中间件异常: {e}")
            if self.config.monitoring.audit_failed_requests:
                await self._log_security_event(request, None, start_time, error=str(e))
            
            # 返回通用错误响应
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"error": "Internal server error", "status_code": 500}
            )
    
    async def _check_csrf_protection(self, request: Request) -> bool:
        """检查CSRF防护"""
        if not self.config.waf.csrf_protection:
            return True
        
        # 获取CSRF令牌
        csrf_token = request.headers.get("X-CSRF-Token")
        if not csrf_token:
            csrf_token = request.query_params.get("csrf_token")
        
        if not csrf_token:
            return False
        
        # 获取会话ID（这里简化处理，实际应该从认证系统获取）
        session_id = request.headers.get("Authorization", "")
        if session_id.startswith("Bearer "):
            session_id = session_id[7:]
        
        return self.csrf.verify_csrf_token(csrf_token, session_id)
    
    async def _record_threat(self, threat: SecurityThreat):
        """记录安全威胁"""
        # 记录到缓存
        ip = threat.source_ip
        if ip not in self.threat_cache:
            self.threat_cache[ip] = []
        self.threat_cache[ip].append(threat)
        
        # 更新计数器
        threat_key = f"{ip}:{threat.threat_type}"
        self.threat_counters[threat_key] = self.threat_counters.get(threat_key, 0) + 1
        
        # 检查是否需要升级防护
        if self.threat_counters[threat_key] >= 5:  # 5次相同威胁
            logger.warning(f"检测到重复威胁 {threat.threat_type} 来自 {ip}，建议加强防护")
        
        # 清理过期记录
        await self._cleanup_threat_cache()
        
        # 记录日志
        logger.warning(
            f"安全威胁检测: {threat.threat_type} | "
            f"IP: {ip} | "
            f"路径: {threat.request_path} | "
            f"严重级别: {threat.severity} | "
            f"已阻断: {threat.blocked}"
        )
    
    async def _cleanup_threat_cache(self):
        """清理过期的威胁缓存"""
        if datetime.now() - self.last_cleanup < timedelta(minutes=5):
            return
        
        self.last_cleanup = datetime.now()
        cutoff_time = datetime.now() - timedelta(hours=1)
        
        # 清理威胁缓存
        for ip in list(self.threat_cache.keys()):
            self.threat_cache[ip] = [
                threat for threat in self.threat_cache[ip]
                if threat.timestamp > cutoff_time
            ]
            if not self.threat_cache[ip]:
                del self.threat_cache[ip]
        
        # 清理计数器
        self.threat_counters.clear()
    
    async def _create_blocked_response(self, threat: SecurityThreat) -> JSONResponse:
        """创建阻断响应"""
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={
                "error": "Request blocked by security policy",
                "threat_type": threat.threat_type,
                "timestamp": threat.timestamp.isoformat(),
                "reference_id": hashlib.md5(
                    f"{threat.timestamp}{threat.source_ip}{threat.threat_type}".encode()
                ).hexdigest()[:8]
            }
        )
    
    async def _log_security_event(
        self, 
        request: Request, 
        response: Optional[Response], 
        start_time: datetime,
        error: Optional[str] = None
    ):
        """记录安全事件日志"""
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        log_data = {
            "timestamp": start_time.isoformat(),
            "client_ip": self.waf._get_client_ip(request),
            "method": request.method,
            "path": str(request.url.path),
            "user_agent": str(request.headers.get("user-agent", "")),
            "processing_time_ms": processing_time,
            "status_code": response.status_code if response else None,
            "error": error
        }
        
        logger.info(f"安全事件: {json.dumps(log_data, ensure_ascii=False)}")


# 导入依赖
import os


def create_security_middleware(config: SecurityConfigManager) -> SecurityMiddleware:
    """创建安全中间件实例"""
    return SecurityMiddleware(None, config)


# 便捷函数
def get_csrf_token(session_id: str, config: SecurityConfigManager) -> str:
    """获取CSRF令牌"""
    csrf = CSRFProtection(config)
    return csrf.generate_csrf_token(session_id)
