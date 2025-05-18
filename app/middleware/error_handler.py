from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from app.schemas.response_schema import BaseResponse
from app.utils.logger_service import logger
import time

class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        request_path = request.url.path
        request_method = request.method
        
        try:
            # 处理请求
            response = await call_next(request)
            
            # 记录成功的请求
            process_time = (time.time() - start_time) * 1000
            logger.api_request(request_method, request_path, response.status_code, process_time)
            
            return response
        except ValueError as ve:
            # 参数验证错误
            logger.api_error(request_method, request_path, 400, str(ve))
            return JSONResponse(
                status_code=400,
                content=BaseResponse.bad_request(str(ve)).dict()
            )
        except KeyError as ke:
            # 键错误
            error_msg = f"无效的键: {str(ke)}"
            logger.api_error(request_method, request_path, 400, error_msg)
            return JSONResponse(
                status_code=400,
                content=BaseResponse.bad_request(error_msg).dict()
            )
        except TypeError as te:
            # 类型错误
            logger.api_error(request_method, request_path, 400, str(te))
            return JSONResponse(
                status_code=400,
                content=BaseResponse.bad_request(str(te)).dict()
            )
        except Exception as e:
            # 其他未知异常 (如果是HTTPException，保留其状态码)
            status_code = getattr(e, 'status_code', 500)
            detail = getattr(e, 'detail', str(e))
            
            logger.api_error(request_method, request_path, status_code, detail)
            
            if status_code == 404:
                return JSONResponse(
                    status_code=status_code,
                    content=BaseResponse.not_found(detail).dict()
                )
            elif status_code >= 400 and status_code < 500:
                return JSONResponse(
                    status_code=status_code,
                    content=BaseResponse.error(status_code, detail).dict()
                )
            else:
                return JSONResponse(
                    status_code=status_code,
                    content=BaseResponse.server_error(detail).dict()
                ) 