from typing import Generic, TypeVar, Optional, Any
from pydantic import BaseModel

T = TypeVar('T')

class BaseResponse(BaseModel, Generic[T]):
    """
    基础响应模型
    """
    code: int = 200
    message: str = "success"
    data: Optional[T] = None

    @classmethod
    def success(cls, data: T = None, message: str = "success") -> "BaseResponse[T]":
        """
        成功响应
        """
        return cls(code=200, message=message, data=data)

    @classmethod
    def error(cls, code: int, message: str, data: T = None) -> "BaseResponse[T]":
        """
        错误响应
        """
        return cls(code=code, message=message, data=data)

    @classmethod
    def not_found(cls, message: str = "资源不存在") -> "BaseResponse[None]":
        """
        404响应
        """
        return cls.error(404, message)

    @classmethod
    def bad_request(cls, message: str = "请求参数错误") -> "BaseResponse[None]":
        """
        400响应
        """
        return cls.error(400, message)

    @classmethod
    def unauthorized(cls, message: str = "未授权") -> "BaseResponse[None]":
        """
        401响应
        """
        return cls.error(401, message)

    @classmethod
    def forbidden(cls, message: str = "禁止访问") -> "BaseResponse[None]":
        """
        403响应
        """
        return cls.error(403, message)

    @classmethod
    def server_error(cls, message: str = "服务器内部错误") -> "BaseResponse[None]":
        """
        500响应
        """
        return cls.error(500, message)

    @classmethod
    def database_operation_error(cls, message: str = "数据库操作错误") -> "BaseResponse[None]":
        """
        数据库操作错误
        """
        return cls.error(501, message)
   