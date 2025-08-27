"""
RedFire 智能限流和防护机制
========================

TODO-15: 安全防护机制优化
提供多层级的智能限流和防护功能

功能特性：
- 🚦 多算法智能限流（令牌桶、滑动窗口、固定窗口）
- 🔄 分布式限流支持
- 🎯 精细化限流策略（IP、用户、端点）
- 📊 动态限流调整
- 🛡️ DDoS防护和异常检测
"""

import asyncio
import time
import json
import hashlib
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import redis.asyncio as redis
from fastapi import Request, HTTPException, status

from .security_config import SecurityConfigManager, RateLimitConfig


logger = logging.getLogger(__name__)


class LimitAlgorithm(str, Enum):
    """限流算法"""
    TOKEN_BUCKET = "token_bucket"        # 令牌桶
    SLIDING_WINDOW = "sliding_window"    # 滑动窗口
    FIXED_WINDOW = "fixed_window"        # 固定窗口
    ADAPTIVE = "adaptive"                # 自适应算法


class LimitScope(str, Enum):
    """限流范围"""
    GLOBAL = "global"        # 全局限流
    IP = "ip"               # IP限流
    USER = "user"           # 用户限流
    ENDPOINT = "endpoint"   # 端点限流
    CUSTOM = "custom"       # 自定义限流


@dataclass
class RateLimitRule:
    """限流规则"""
    scope: LimitScope
    algorithm: LimitAlgorithm
    requests_per_minute: int
    requests_per_hour: int
    burst_capacity: int = 0  # 突发容量
    key_pattern: str = ""    # 键模式
    enabled: bool = True
    priority: int = 0        # 优先级，数字越大优先级越高


@dataclass
class RateLimitResult:
    """限流结果"""
    allowed: bool
    remaining: int
    reset_time: datetime
    retry_after: Optional[int] = None
    rule_name: str = ""
    current_usage: int = 0
    limit: int = 0


class TokenBucket:
    """令牌桶算法实现"""
    
    def __init__(self, capacity: int, refill_rate: float, redis_client: Optional[redis.Redis] = None):
        self.capacity = capacity
        self.refill_rate = refill_rate  # 每秒添加的令牌数
        self.redis_client = redis_client
        self._local_buckets: Dict[str, Dict] = {}
    
    async def consume(self, key: str, tokens: int = 1) -> Tuple[bool, int]:
        """消费令牌"""
        if self.redis_client:
            return await self._consume_redis(key, tokens)
        else:
            return await self._consume_local(key, tokens)
    
    async def _consume_redis(self, key: str, tokens: int) -> Tuple[bool, int]:
        """Redis分布式令牌桶"""
        lua_script = """
        local key = KEYS[1]
        local capacity = tonumber(ARGV[1])
        local refill_rate = tonumber(ARGV[2])
        local tokens_requested = tonumber(ARGV[3])
        local current_time = tonumber(ARGV[4])
        
        -- 获取当前桶状态
        local bucket = redis.call('HMGET', key, 'tokens', 'last_refill')
        local current_tokens = tonumber(bucket[1]) or capacity
        local last_refill = tonumber(bucket[2]) or current_time
        
        -- 计算需要添加的令牌
        local time_elapsed = current_time - last_refill
        local new_tokens = math.min(capacity, current_tokens + (time_elapsed * refill_rate))
        
        -- 检查是否有足够的令牌
        if new_tokens >= tokens_requested then
            new_tokens = new_tokens - tokens_requested
            redis.call('HMSET', key, 
                'tokens', new_tokens, 
                'last_refill', current_time)
            redis.call('EXPIRE', key, 3600)  -- 1小时过期
            return {1, new_tokens}
        else
            redis.call('HMSET', key, 
                'tokens', new_tokens, 
                'last_refill', current_time)
            redis.call('EXPIRE', key, 3600)
            return {0, new_tokens}
        end
        """
        
        try:
            result = await self.redis_client.eval(
                lua_script, 1, key, 
                self.capacity, self.refill_rate, tokens, time.time()
            )
            return bool(result[0]), int(result[1])
        except Exception as e:
            logger.warning(f"Redis令牌桶操作失败，降级到本地: {e}")
            return await self._consume_local(key, tokens)
    
    async def _consume_local(self, key: str, tokens: int) -> Tuple[bool, int]:
        """本地内存令牌桶"""
        current_time = time.time()
        
        if key not in self._local_buckets:
            self._local_buckets[key] = {
                'tokens': self.capacity,
                'last_refill': current_time
            }
        
        bucket = self._local_buckets[key]
        time_elapsed = current_time - bucket['last_refill']
        
        # 添加新令牌
        new_tokens = min(self.capacity, bucket['tokens'] + (time_elapsed * self.refill_rate))
        
        if new_tokens >= tokens:
            bucket['tokens'] = new_tokens - tokens
            bucket['last_refill'] = current_time
            return True, int(bucket['tokens'])
        else:
            bucket['tokens'] = new_tokens
            bucket['last_refill'] = current_time
            return False, int(bucket['tokens'])


class SlidingWindowLimiter:
    """滑动窗口限流器"""
    
    def __init__(self, window_size: int, max_requests: int, redis_client: Optional[redis.Redis] = None):
        self.window_size = window_size  # 窗口大小（秒）
        self.max_requests = max_requests
        self.redis_client = redis_client
        self._local_windows: Dict[str, List[float]] = {}
    
    async def is_allowed(self, key: str) -> Tuple[bool, int]:
        """检查是否允许请求"""
        if self.redis_client:
            return await self._check_redis(key)
        else:
            return await self._check_local(key)
    
    async def _check_redis(self, key: str) -> Tuple[bool, int]:
        """Redis分布式滑动窗口"""
        lua_script = """
        local key = KEYS[1]
        local window_size = tonumber(ARGV[1])
        local max_requests = tonumber(ARGV[2])
        local current_time = tonumber(ARGV[3])
        local window_start = current_time - window_size
        
        -- 清理过期记录
        redis.call('ZREMRANGEBYSCORE', key, 0, window_start)
        
        -- 获取当前窗口内的请求数
        local current_requests = redis.call('ZCARD', key)
        
        if current_requests < max_requests then
            -- 添加当前请求
            redis.call('ZADD', key, current_time, current_time)
            redis.call('EXPIRE', key, window_size + 1)
            return {1, max_requests - current_requests - 1}
        else
            return {0, 0}
        end
        """
        
        try:
            result = await self.redis_client.eval(
                lua_script, 1, key,
                self.window_size, self.max_requests, time.time()
            )
            return bool(result[0]), int(result[1])
        except Exception as e:
            logger.warning(f"Redis滑动窗口操作失败，降级到本地: {e}")
            return await self._check_local(key)
    
    async def _check_local(self, key: str) -> Tuple[bool, int]:
        """本地内存滑动窗口"""
        current_time = time.time()
        window_start = current_time - self.window_size
        
        if key not in self._local_windows:
            self._local_windows[key] = []
        
        # 清理过期记录
        self._local_windows[key] = [
            req_time for req_time in self._local_windows[key]
            if req_time > window_start
        ]
        
        current_requests = len(self._local_windows[key])
        
        if current_requests < self.max_requests:
            self._local_windows[key].append(current_time)
            return True, self.max_requests - current_requests - 1
        else:
            return False, 0


class AdaptiveLimiter:
    """自适应限流器"""
    
    def __init__(self, base_limit: int, redis_client: Optional[redis.Redis] = None):
        self.base_limit = base_limit
        self.redis_client = redis_client
        self._metrics: Dict[str, Dict] = {}
        self._last_adjustment = time.time()
    
    async def is_allowed(self, key: str, current_load: float = 1.0) -> Tuple[bool, int]:
        """自适应检查"""
        # 获取当前限制
        current_limit = await self._get_adaptive_limit(key, current_load)
        
        # 使用滑动窗口检查
        limiter = SlidingWindowLimiter(60, current_limit, self.redis_client)
        return await limiter.is_allowed(f"adaptive:{key}")
    
    async def _get_adaptive_limit(self, key: str, current_load: float) -> int:
        """获取自适应限制"""
        current_time = time.time()
        
        # 更新指标
        if key not in self._metrics:
            self._metrics[key] = {
                'success_rate': 1.0,
                'avg_response_time': 0.1,
                'current_limit': self.base_limit,
                'last_update': current_time
            }
        
        metrics = self._metrics[key]
        
        # 自适应调整逻辑
        if current_time - metrics['last_update'] > 60:  # 每分钟调整一次
            adjustment_factor = 1.0
            
            # 基于成功率调整
            if metrics['success_rate'] > 0.95:
                adjustment_factor *= 1.1  # 增加限制
            elif metrics['success_rate'] < 0.8:
                adjustment_factor *= 0.8  # 减少限制
            
            # 基于响应时间调整
            if metrics['avg_response_time'] > 1.0:  # 响应时间过长
                adjustment_factor *= 0.9
            
            # 基于系统负载调整
            if current_load > 0.8:
                adjustment_factor *= 0.8
            
            # 应用调整
            new_limit = int(metrics['current_limit'] * adjustment_factor)
            new_limit = max(10, min(self.base_limit * 2, new_limit))  # 限制调整范围
            
            metrics['current_limit'] = new_limit
            metrics['last_update'] = current_time
        
        return metrics['current_limit']
    
    def update_metrics(self, key: str, success: bool, response_time: float):
        """更新指标"""
        if key not in self._metrics:
            return
        
        metrics = self._metrics[key]
        
        # 指数移动平均
        alpha = 0.1
        metrics['success_rate'] = (1 - alpha) * metrics['success_rate'] + alpha * (1.0 if success else 0.0)
        metrics['avg_response_time'] = (1 - alpha) * metrics['avg_response_time'] + alpha * response_time


class DDoSProtector:
    """DDoS防护器"""
    
    def __init__(self, config: SecurityConfigManager):
        self.config = config
        self.redis_client: Optional[redis.Redis] = None
        self._setup_redis()
        
        # DDoS检测阈值
        self.ddos_threshold = 1000  # 1分钟内1000个请求
        self.ddos_window = 60       # 检测窗口60秒
        self.blacklist_duration = 3600  # 黑名单持续1小时
    
    async def _setup_redis(self):
        """设置Redis连接"""
        try:
            import os
            self.redis_client = redis.Redis(
                host=os.getenv("REDIS_HOST", "localhost"),
                port=int(os.getenv("REDIS_PORT", "6379")),
                decode_responses=True
            )
            await self.redis_client.ping()
        except Exception as e:
            logger.warning(f"DDoS防护器Redis连接失败: {e}")
            self.redis_client = None
    
    async def check_ddos(self, ip: str) -> Tuple[bool, str]:
        """检查DDoS攻击"""
        # 检查是否在黑名单中
        if await self._is_blacklisted(ip):
            return False, "IP已被列入黑名单"
        
        # 检查请求频率
        if await self._check_request_frequency(ip):
            await self._add_to_blacklist(ip)
            return False, "检测到DDoS攻击，IP已被暂时屏蔽"
        
        # 记录请求
        await self._record_request(ip)
        
        return True, ""
    
    async def _is_blacklisted(self, ip: str) -> bool:
        """检查IP是否在黑名单中"""
        if not self.redis_client:
            return False
        
        try:
            return await self.redis_client.exists(f"ddos:blacklist:{ip}")
        except Exception:
            return False
    
    async def _check_request_frequency(self, ip: str) -> bool:
        """检查请求频率"""
        if not self.redis_client:
            return False
        
        try:
            key = f"ddos:requests:{ip}"
            current_time = time.time()
            window_start = current_time - self.ddos_window
            
            # 清理过期记录
            await self.redis_client.zremrangebyscore(key, 0, window_start)
            
            # 获取当前窗口内的请求数
            request_count = await self.redis_client.zcard(key)
            
            return request_count >= self.ddos_threshold
        except Exception:
            return False
    
    async def _record_request(self, ip: str):
        """记录请求"""
        if not self.redis_client:
            return
        
        try:
            key = f"ddos:requests:{ip}"
            current_time = time.time()
            
            await self.redis_client.zadd(key, {str(current_time): current_time})
            await self.redis_client.expire(key, self.ddos_window + 10)
        except Exception:
            pass
    
    async def _add_to_blacklist(self, ip: str):
        """添加到黑名单"""
        if not self.redis_client:
            return
        
        try:
            key = f"ddos:blacklist:{ip}"
            await self.redis_client.setex(key, self.blacklist_duration, "1")
            logger.warning(f"IP {ip} 已被添加到DDoS黑名单")
        except Exception:
            pass


class SmartRateLimiter:
    """智能限流器主类"""
    
    def __init__(self, config: SecurityConfigManager):
        self.config = config
        self.redis_client: Optional[redis.Redis] = None
        self._setup_redis()
        
        # 初始化各种限流器
        self.token_bucket = TokenBucket(
            capacity=config.rate_limit.global_requests_per_minute,
            refill_rate=config.rate_limit.global_requests_per_minute / 60.0,
            redis_client=self.redis_client
        )
        
        self.sliding_window = SlidingWindowLimiter(
            window_size=60,
            max_requests=config.rate_limit.global_requests_per_minute,
            redis_client=self.redis_client
        )
        
        self.adaptive_limiter = AdaptiveLimiter(
            base_limit=config.rate_limit.global_requests_per_minute,
            redis_client=self.redis_client
        )
        
        self.ddos_protector = DDoSProtector(config)
        
        # 限流规则
        self.rules = self._build_rate_limit_rules()
    
    async def _setup_redis(self):
        """设置Redis连接"""
        if not self.config.rate_limit.distributed_mode:
            return
        
        try:
            import os
            self.redis_client = redis.Redis(
                host=os.getenv("REDIS_HOST", "localhost"),
                port=int(os.getenv("REDIS_PORT", "6379")),
                decode_responses=True
            )
            await self.redis_client.ping()
            logger.info("智能限流器Redis连接成功")
        except Exception as e:
            logger.warning(f"智能限流器Redis连接失败，使用本地限流: {e}")
            self.redis_client = None
    
    def _build_rate_limit_rules(self) -> List[RateLimitRule]:
        """构建限流规则"""
        rules = []
        
        # 全局限流规则
        if self.config.rate_limit.global_enabled:
            rules.append(RateLimitRule(
                scope=LimitScope.GLOBAL,
                algorithm=LimitAlgorithm.TOKEN_BUCKET,
                requests_per_minute=self.config.rate_limit.global_requests_per_minute,
                requests_per_hour=self.config.rate_limit.global_requests_per_hour,
                key_pattern="global",
                priority=1
            ))
        
        # IP级限流规则
        if self.config.rate_limit.ip_enabled:
            rules.append(RateLimitRule(
                scope=LimitScope.IP,
                algorithm=LimitAlgorithm.SLIDING_WINDOW,
                requests_per_minute=self.config.rate_limit.ip_requests_per_minute,
                requests_per_hour=self.config.rate_limit.ip_requests_per_hour,
                key_pattern="ip:{ip}",
                priority=2
            ))
        
        # 用户级限流规则
        if self.config.rate_limit.user_enabled:
            rules.append(RateLimitRule(
                scope=LimitScope.USER,
                algorithm=LimitAlgorithm.TOKEN_BUCKET,
                requests_per_minute=self.config.rate_limit.user_requests_per_minute,
                requests_per_hour=self.config.rate_limit.user_requests_per_hour,
                key_pattern="user:{user_id}",
                priority=3
            ))
        
        # 端点级限流规则
        for endpoint, limits in self.config.rate_limit.endpoint_limits.items():
            rules.append(RateLimitRule(
                scope=LimitScope.ENDPOINT,
                algorithm=LimitAlgorithm.SLIDING_WINDOW,
                requests_per_minute=limits.get("per_minute", 60),
                requests_per_hour=limits.get("per_hour", 1000),
                key_pattern=f"endpoint:{endpoint}:{{ip}}",
                priority=4
            ))
        
        # 按优先级排序
        rules.sort(key=lambda x: x.priority, reverse=True)
        return rules
    
    async def check_rate_limit(self, request: Request, user_id: Optional[str] = None) -> RateLimitResult:
        """检查限流"""
        client_ip = self._get_client_ip(request)
        endpoint = str(request.url.path)
        
        # DDoS检查
        ddos_allowed, ddos_reason = await self.ddos_protector.check_ddos(client_ip)
        if not ddos_allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=ddos_reason,
                headers={"Retry-After": "3600"}
            )
        
        # 检查各个限流规则
        for rule in self.rules:
            if not rule.enabled:
                continue
            
            result = await self._check_rule(rule, request, client_ip, user_id, endpoint)
            if not result.allowed:
                return result
        
        # 所有规则都通过
        return RateLimitResult(
            allowed=True,
            remaining=100,
            reset_time=datetime.now() + timedelta(minutes=1)
        )
    
    async def _check_rule(
        self, 
        rule: RateLimitRule, 
        request: Request, 
        client_ip: str, 
        user_id: Optional[str], 
        endpoint: str
    ) -> RateLimitResult:
        """检查单个限流规则"""
        # 构建限流键
        key = self._build_limit_key(rule, client_ip, user_id, endpoint)
        
        # 选择限流算法
        if rule.algorithm == LimitAlgorithm.TOKEN_BUCKET:
            allowed, remaining = await self.token_bucket.consume(key)
        elif rule.algorithm == LimitAlgorithm.SLIDING_WINDOW:
            limiter = SlidingWindowLimiter(60, rule.requests_per_minute, self.redis_client)
            allowed, remaining = await limiter.is_allowed(key)
        elif rule.algorithm == LimitAlgorithm.ADAPTIVE:
            allowed, remaining = await self.adaptive_limiter.is_allowed(key)
        else:
            # 默认使用令牌桶
            allowed, remaining = await self.token_bucket.consume(key)
        
        # 计算重置时间
        reset_time = datetime.now() + timedelta(minutes=1)
        retry_after = 60 if not allowed else None
        
        return RateLimitResult(
            allowed=allowed,
            remaining=remaining,
            reset_time=reset_time,
            retry_after=retry_after,
            rule_name=f"{rule.scope.value}_{rule.algorithm.value}",
            current_usage=rule.requests_per_minute - remaining,
            limit=rule.requests_per_minute
        )
    
    def _build_limit_key(
        self, 
        rule: RateLimitRule, 
        client_ip: str, 
        user_id: Optional[str], 
        endpoint: str
    ) -> str:
        """构建限流键"""
        key_pattern = rule.key_pattern
        
        # 替换占位符
        key = key_pattern.format(
            ip=client_ip,
            user_id=user_id or "anonymous",
            endpoint=endpoint.replace("/", "_")
        )
        
        # 添加前缀
        prefix = self.config.rate_limit.redis_key_prefix
        return f"{prefix}:{key}"
    
    def _get_client_ip(self, request: Request) -> str:
        """获取客户端IP"""
        # 考虑代理和负载均衡器
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"
    
    async def update_metrics(self, key: str, success: bool, response_time: float):
        """更新指标（用于自适应限流）"""
        await self.adaptive_limiter.update_metrics(key, success, response_time)
    
    async def get_rate_limit_status(self, client_ip: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """获取限流状态"""
        status = {}
        
        for rule in self.rules:
            if not rule.enabled:
                continue
            
            key = self._build_limit_key(rule, client_ip, user_id, "")
            
            # 获取当前状态（不消费令牌）
            if rule.algorithm == LimitAlgorithm.TOKEN_BUCKET:
                # 这里需要实现获取令牌桶状态的方法
                pass
            
            status[rule.scope.value] = {
                "algorithm": rule.algorithm.value,
                "limit_per_minute": rule.requests_per_minute,
                "limit_per_hour": rule.requests_per_hour,
                "enabled": rule.enabled
            }
        
        return status


# 导入依赖
import os
