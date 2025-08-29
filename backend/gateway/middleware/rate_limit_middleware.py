"""
限流中间件
=========

实现API请求限流保护
"""

import time
import logging
from typing import Dict, Optional, Any
from dataclasses import dataclass
from fastapi import HTTPException, status, Request
import redis.asyncio as redis
import asyncio
from collections import defaultdict, deque

from ..config.gateway_config import RateLimitConfig

logger = logging.getLogger(__name__)


@dataclass
class RateLimitInfo:
    """限流信息"""
    requests_count: int
    window_start: float
    last_request: float


class MemoryRateLimiter:
    """内存限流器"""
    
    def __init__(self, config: RateLimitConfig):
        self.config = config
        self.buckets: Dict[str, deque] = defaultdict(deque)
        self.lock = asyncio.Lock()
    
    async def is_allowed(self, key: str, limit: int, window: int) -> bool:
        """检查是否允许请求"""
        async with self.lock:
            now = time.time()
            bucket = self.buckets[key]
            
            # 清理过期的请求记录
            while bucket and bucket[0] <= now - window:
                bucket.popleft()
            
            # 检查是否超过限制
            if len(bucket) >= limit:
                return False
            
            # 记录请求
            bucket.append(now)
            return True
    
    async def get_remaining(self, key: str, limit: int, window: int) -> int:
        """获取剩余请求数"""
        async with self.lock:
            now = time.time()
            bucket = self.buckets[key]
            
            # 清理过期记录
            while bucket and bucket[0] <= now - window:
                bucket.popleft()
            
            return max(0, limit - len(bucket))


class RedisRateLimiter:
    """Redis限流器"""
    
    def __init__(self, config: RateLimitConfig):
        self.config = config
        self.redis: Optional[redis.Redis] = None
        
        # Lua脚本用于原子性操作
        self.rate_limit_script = """
        local key = KEYS[1]
        local limit = tonumber(ARGV[1])
        local window = tonumber(ARGV[2])
        local now = tonumber(ARGV[3])
        
        -- 清理过期的请求
        redis.call('ZREMRANGEBYSCORE', key, 0, now - window)
        
        -- 获取当前请求数
        local current = redis.call('ZCARD', key)
        
        if current < limit then
            -- 允许请求，记录时间戳
            redis.call('ZADD', key, now, now)
            redis.call('EXPIRE', key, window)
            return {1, limit - current - 1, window}
        else
            -- 拒绝请求
            return {0, 0, window}
        end
        """
    
    async def initialize(self):
        """初始化Redis连接"""
        if self.config.redis_url:
            self.redis = redis.from_url(
                self.config.redis_url,
                decode_responses=True
            )
    
    async def is_allowed(self, key: str, limit: int, window: int) -> bool:
        """检查是否允许请求"""
        if not self.redis:
            return True
        
        try:
            now = time.time()
            result = await self.redis.eval(
                self.rate_limit_script,
                1,
                f"rate_limit:{key}",
                limit,
                window,
                now
            )
            return bool(result[0])
        except Exception as e:
            logger.error(f"Redis限流检查失败: {e}")
            return True  # 失败时允许请求
    
    async def get_remaining(self, key: str, limit: int, window: int) -> int:
        """获取剩余请求数"""
        if not self.redis:
            return limit
        
        try:
            now = time.time()
            # 清理过期记录
            await self.redis.zremrangebyscore(
                f"rate_limit:{key}",
                0,
                now - window
            )
            
            # 获取当前请求数
            current = await self.redis.zcard(f"rate_limit:{key}")
            return max(0, limit - current)
        except Exception as e:
            logger.error(f"获取剩余请求数失败: {e}")
            return limit
    
    async def close(self):
        """关闭Redis连接"""
        if self.redis:
            await self.redis.close()


class RateLimitMiddleware:
    """限流中间件"""
    
    def __init__(self, config: RateLimitConfig):
        self.config = config
        
        if config.storage_type == "redis":
            self.limiter = RedisRateLimiter(config)
        else:
            self.limiter = MemoryRateLimiter(config)
        
        # 路径特定限制
        self.path_limits = {
            "/api/v1/auth/login": {"limit": 10, "window": 60},  # 登录限制更严格
            "/api/v1/auth/register": {"limit": 5, "window": 300},  # 注册限制
            "/api/v1/trading": {"limit": 50, "window": 60},  # 交易API限制
        }
    
    async def initialize(self):
        """初始化中间件"""
        if hasattr(self.limiter, 'initialize'):
            await self.limiter.initialize()
    
    async def check_rate_limit(self, request: Request):
        """检查限流"""
        if not self.config.enabled:
            return
        
        # 生成限流key
        rate_limit_key = self._generate_key(request)
        
        # 获取限制参数
        limit_config = self._get_limit_config(request.url.path)
        limit = limit_config["limit"]
        window = limit_config["window"]
        
        # 检查是否允许请求
        allowed = await self.limiter.is_allowed(rate_limit_key, limit, window)
        
        if not allowed:
            # 获取剩余请求数和重置时间
            remaining = await self.limiter.get_remaining(rate_limit_key, limit, window)
            reset_time = int(time.time()) + window
            
            # 添加限流头
            headers = {
                "X-RateLimit-Limit": str(limit),
                "X-RateLimit-Remaining": str(remaining),
                "X-RateLimit-Reset": str(reset_time),
                "Retry-After": str(window)
            }
            
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"请求频率过高，请在 {window} 秒后重试",
                headers=headers
            )
        
        # 为成功的请求添加限流信息头
        remaining = await self.limiter.get_remaining(rate_limit_key, limit, window)
        request.state.rate_limit_headers = {
            "X-RateLimit-Limit": str(limit),
            "X-RateLimit-Remaining": str(remaining),
            "X-RateLimit-Reset": str(int(time.time()) + window)
        }
    
    def _generate_key(self, request: Request) -> str:
        """生成限流key"""
        # 基于IP + 用户ID（如果有）
        client_ip = self._get_client_ip(request)
        user_id = getattr(request.state, 'user_context', None)
        
        if user_id and hasattr(user_id, 'user_id'):
            return f"{client_ip}:{user_id.user_id}"
        else:
            return client_ip
    
    def _get_client_ip(self, request: Request) -> str:
        """获取客户端IP"""
        # 检查代理头
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"
    
    def _get_limit_config(self, path: str) -> Dict[str, int]:
        """获取路径的限流配置"""
        # 检查路径特定限制
        for pattern, config in self.path_limits.items():
            if path.startswith(pattern):
                return config
        
        # 返回默认限制
        return {
            "limit": self.config.default_limit,
            "window": self.config.window_size
        }
    
    def add_path_limit(self, path: str, limit: int, window: int = 60):
        """动态添加路径限制"""
        self.path_limits[path] = {"limit": limit, "window": window}
    
    def remove_path_limit(self, path: str):
        """移除路径限制"""
        if path in self.path_limits:
            del self.path_limits[path]
    
    async def get_stats(self) -> Dict[str, Any]:
        """获取限流统计信息"""
        stats = {
            "enabled": self.config.enabled,
            "storage_type": self.config.storage_type,
            "default_limit": self.config.default_limit,
            "window_size": self.config.window_size,
            "path_limits": self.path_limits
        }
        
        if isinstance(self.limiter, MemoryRateLimiter):
            stats["active_buckets"] = len(self.limiter.buckets)
        
        return stats
    
    async def close(self):
        """关闭中间件"""
        if hasattr(self.limiter, 'close'):
            await self.limiter.close()
