import time
from typing import Dict, Optional
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from app.infrastructure.redis.redis_client import redis_client
from app.utils.logger_service import logger


class RateLimiter(BaseHTTPMiddleware):
    """API限流中间件"""
    
    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.redis = redis_client
    
    async def dispatch(self, request: Request, call_next):
        # 获取客户端标识
        client_id = self._get_client_id(request)
        
        # 检查限流
        if await self._is_rate_limited(client_id):
            raise HTTPException(
                status_code=429,
                detail="请求过于频繁，请稍后再试"
            )
        
        # 记录请求
        await self._record_request(client_id)
        
        response = await call_next(request)
        return response
    
    def _get_client_id(self, request: Request) -> str:
        """获取客户端标识"""
        # 优先使用用户ID，否则使用IP
        if hasattr(request.state, 'current_user') and request.state.current_user:
            return f"user:{request.state.current_user.id}"
        else:
            return f"ip:{request.client.host}"
    
    async def _is_rate_limited(self, client_id: str) -> bool:
        """检查是否达到限流阈值"""
        key = f"rate_limit:{client_id}"
        current_requests = await self.redis.get(key)
        
        if current_requests is None:
            return False
        
        return int(current_requests) >= self.requests_per_minute
    
    async def _record_request(self, client_id: str):
        """记录请求"""
        key = f"rate_limit:{client_id}"
        await self.redis.incr(key)
        await self.redis.expire(key, 60)  # 1分钟过期