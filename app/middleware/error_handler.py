import sys
import os
from fastapi import Request, FastAPI
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable, Dict, Any
from uuid import uuid4
from datetime import datetime
from app.utils.logger_service import logger


def determine_status_code(exc_type: str) -> int:
    """根据异常类型确定适当的HTTP状态码"""
    status_code_map = {
        "ValidationError": 400,
        "RequestValidationError": 400,
        "HTTPException": 400,  # FastAPI的HTTPException会单独处理
        "UnauthorizedException": 401,
        "UnauthenticatedException": 401,
        "PermissionError": 403,
        "NotFoundError": 404,
        "TimeoutError": 504,
        "ConnectionError": 503,
        "AttributeError": 500,
        "KeyError": 500,
        "ValueError": 400,
        "TypeError": 500,
    }
    
    return status_code_map.get(exc_type, 500)


# 错误处理中间件
class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable):
        # 生成请求ID
        request_id = str(uuid4())
        # 附加请求ID到请求对象，方便后续使用
        request.state.request_id = request_id
        
        try:
            # 尝试处理请求
            response = await call_next(request)
            return response
            
        except Exception as e:
            # 捕获所有异常
            exc_info = sys.exc_info()
            
            # 获取异常信息
            exc_type = exc_info[0].__name__
            exc_msg = str(exc_info[1])
            
            # 记录结构化的错误日志
            logger.api_error(
                method=request.method,
                path=request.url.path,
                status_code=determine_status_code(exc_type),
                error_message=exc_msg,
                exc_info=exc_info,
                user_id=getattr(request.state, "user_id", None)
            )
            
            # 提取简化的错误信息用于客户端响应
            error_detail = self._get_client_error_detail(exc_info)
            
            # 确定HTTP状态码
            status_code = determine_status_code(exc_type)
            
            # 返回简化的JSON错误响应
            return JSONResponse(
                status_code=status_code,
                content={
                    "code": status_code,
                    "message": exc_msg
                }
            )
    
    def _get_client_error_detail(self, exc_info) -> Dict[str, Any]:
        """提取适合发送给客户端的错误细节"""
        tb = exc_info[2]
        frames = []
        
        while tb:
            frame = tb.tb_frame
            filename = os.path.basename(frame.f_code.co_filename)
            lineno = tb.tb_lineno
            function = frame.f_code.co_name
            
            # 跳过框架内部堆栈
            if not self._is_framework_code(frame.f_code.co_filename):
                frames.append({
                    "file": filename,
                    "line": lineno,
                    "function": function
                })
            
            tb = tb.tb_next
        
        # 异常信息
        exc_type = exc_info[0].__name__
        exc_msg = str(exc_info[1])
        
        return {
            "type": exc_type,
            "message": exc_msg,
            "stack": frames
        }
    
    def _is_framework_code(self, filename: str) -> bool:
        """检查是否为框架内部代码"""
        # 跳过常见的第三方包路径
        framework_paths = [
            "site-packages",
            "dist-packages",
            "/usr/lib/python",
            "lib/python"
        ]
        return any(path in filename for path in framework_paths)
    
    
    
    def _is_production(self) -> bool:
        """检查是否为生产环境"""
        return os.environ.get("ENVIRONMENT", "development") == "production"

# 注册中间件
def register_error_handler(app: FastAPI):
    """注册错误处理中间件到FastAPI应用"""
    app.add_middleware(ErrorHandlerMiddleware)
    
    # 单独处理FastAPI的ValidationError，因为它在中间件之前处理
    from fastapi.exceptions import RequestValidationError
    from starlette.exceptions import HTTPException
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        # 记录验证错误
        error_detail = str(exc.errors())
        logger.api_error(
            method=request.method,
            path=request.url.path,
            status_code=400,
            error_message=f"请求验证错误: {error_detail}",
            exc_info=sys.exc_info()
        )
        
        # 返回简化错误响应
        return JSONResponse(
            status_code=400,
            content={
                "code": 400,
                "message": "请求参数验证失败"
            }
        )
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        # 记录HTTP异常
        logger.api_error(
            method=request.method,
            path=request.url.path,
            status_code=exc.status_code,
            error_message=str(exc.detail),
            exc_info=sys.exc_info()
        )
        
        # 返回简化错误响应
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "code": exc.detail.get("code", 500) if exc.detail and isinstance(exc.detail, dict) else 500,
                "message": str(exc.detail.get("message", "服务器内部错误") if exc.detail and isinstance(exc.detail, dict) else exc)
            }
        )
    
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        # 记录详细错误到日志
        logger.api_error(
            method=request.method,
            path=request.url.path,
            status_code=exc.status_code if hasattr(exc, "status_code") else 500,
            error_message=f"未被错误中间件捕获的异常: {str(exc)}",
            exc_info=sys.exc_info()
        )
        
        # 返回简化错误响应
        return JSONResponse(
            status_code=exc.status_code if hasattr(exc, "status_code") else 500,
            content={
                "code": exc.detail.get("code", 500) if hasattr(exc, "detail") and isinstance(exc.detail, dict) else 500,
                "message": exc.detail.get("message", "服务器内部错误") if hasattr(exc, "detail") and isinstance(exc.detail, dict) else str(exc)
            }
        )