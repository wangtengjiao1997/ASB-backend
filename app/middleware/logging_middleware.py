import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from app.utils.logger_service import logger

class LoggingMiddleware(BaseHTTPMiddleware):
    """
    日志中间件
    记录所有API请求的详细信息
    """
    async def dispatch(self, request: Request, call_next):
        # 记录请求开始时间
        start_time = time.time()
        
        try:
            # 处理请求
            response = await call_next(request)
            
            # 计算响应时间
            process_time = (time.time() - start_time) * 1000
            
            # 记录请求信息
            logger.api_request(
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                response_time=process_time,
                user_id=request.headers.get("X-User-ID")
            )
            
            return response
            
        except Exception as e:
            # 记录错误信息
            process_time = (time.time() - start_time) * 1000
            logger.api_error(
                method=request.method,
                path=request.url.path,
                status_code=500,
                error_message=str(e),
                user_id=request.headers.get("X-User-ID")
            )
            raise 