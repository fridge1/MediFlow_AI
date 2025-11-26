"""
API 限流中间件
"""
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Optional
import time

from app.core.redis_client import redis_client
from app.core.config import settings
from app.utils.logger import logger


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """API 限流中间件"""
    
    def __init__(self, app, rate_limit: int = None):
        super().__init__(app)
        self.rate_limit = rate_limit or settings.RATE_LIMIT_PER_MINUTE
    
    async def dispatch(self, request: Request, call_next):
        """处理请求"""
        
        # 跳过特定路径的限流
        if self._should_skip_rate_limit(request.url.path):
            return await call_next(request)
        
        # 获取客户端标识
        client_id = await self._get_client_id(request)
        if not client_id:
            return await call_next(request)
        
        # 端点级限流
        limit = self._get_endpoint_limit(request.url.path)
        from app.middleware.rate_limiter import AdvancedRateLimiter
        is_allowed, remaining = await AdvancedRateLimiter.check_limit(client_id, request.url.path, default_limit=limit)
        
        if not is_allowed:
            logger.warning(f"Rate limit exceeded for {client_id} on {request.url.path}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"请求过于频繁，请稍后再试。限制：{limit}次/分钟",
                headers={"Retry-After": "60"}
            )
        
        # 处理请求
        response = await call_next(request)
        
        # 添加限流信息到响应头
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(time.time()) + 60)
        
        return response
    
    def _should_skip_rate_limit(self, path: str) -> bool:
        """判断是否跳过限流"""
        skip_paths = [
            "/docs",
            "/redoc",
            "/openapi.json",
            "/health",
            "/",
        ]
        return any(path.startswith(skip_path) for skip_path in skip_paths)

    def _get_endpoint_limit(self, path: str) -> int:
        """获取端点对应的限流阈值"""
        from app.middleware.rate_limiter import AdvancedRateLimiter
        for pattern, pattern_limit in AdvancedRateLimiter.ENDPOINT_LIMITS.items():
            if path.startswith(pattern):
                return pattern_limit
        return self.rate_limit
    
    async def _get_client_id(self, request: Request) -> Optional[str]:
        """获取客户端标识"""
        # 优先使用用户ID（如果已认证）
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            from app.core.security import decode_access_token
            token = auth_header.replace("Bearer ", "")
            payload = decode_access_token(token)
            if payload:
                return f"user:{payload.get('sub')}"
        
        # 使用 IP 地址
        client_ip = request.client.host if request.client else "unknown"
        return f"ip:{client_ip}"
    
    async def _check_rate_limit(self, client_id: str, endpoint: str) -> tuple[bool, int]:
        """
        检查限流
        
        Returns:
            (是否允许, 剩余次数)
        """
        # 使用滑动窗口算法
        key = f"rate_limit:{client_id}:{endpoint}"
        current_time = int(time.time())
        window_start = current_time - 60  # 1分钟窗口
        
        try:
            # 获取当前计数
            count_str = await redis_client.get(key)
            count = int(count_str) if count_str else 0
            
            if count >= self.rate_limit:
                return False, 0
            
            # 增加计数
            new_count = await redis_client.incr(key)
            
            # 设置过期时间（首次）
            if new_count == 1:
                await redis_client.expire(key, 60)
            
            remaining = max(0, self.rate_limit - new_count)
            return True, remaining
            
        except Exception as e:
            logger.error(f"Rate limit check error: {e}")
            # 限流检查失败时允许请求通过
            return True, self.rate_limit


class AdvancedRateLimiter:
    """高级限流器（支持不同端点不同限制）"""
    
    # 端点限流配置
    ENDPOINT_LIMITS = {
        "/api/v1/auth/register": 5,
        "/api/v1/auth/login": 10,
        "/api/v1/conversations": 30,
        "/api/v1/messages": 20,
        "/api/v1/messages/stream": 15,
    }
    
    @staticmethod
    async def check_limit(client_id: str, endpoint: str, default_limit: int = 60) -> tuple[bool, int]:
        """
        检查特定端点的限流
        
        Args:
            client_id: 客户端标识
            endpoint: API端点
            default_limit: 默认限制
        
        Returns:
            (是否允许, 剩余次数)
        """
        # 获取该端点的限流配置
        limit = default_limit
        for pattern, pattern_limit in AdvancedRateLimiter.ENDPOINT_LIMITS.items():
            if endpoint.startswith(pattern):
                limit = pattern_limit
                break
        
        key = f"rate_limit:{client_id}:{endpoint}"
        
        try:
            count_str = await redis_client.get(key)
            count = int(count_str) if count_str else 0
            
            if count >= limit:
                return False, 0
            
            new_count = await redis_client.incr(key)
            if new_count == 1:
                await redis_client.expire(key, 60)
            
            remaining = max(0, limit - new_count)
            return True, remaining
            
        except Exception as e:
            logger.error(f"Advanced rate limit check error: {e}")
            return True, limit
