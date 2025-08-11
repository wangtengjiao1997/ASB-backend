from typing import List, Optional, Set
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware


from app.infrastructure.wechat.wechat_auth import WechatAuth
from app.features.user.user_service import UserService
from app.entities.user_entity import User
from app.utils.logger_service import logger


class AuthMiddleware(BaseHTTPMiddleware):
    """
    Token验证中间件
    支持白名单路径和获取当前用户信息
    """
    
    def __init__(self, app):
        super().__init__(app)
        self.wechat_auth = WechatAuth()
        self.user_service = UserService()
        
        # 不需要token验证的路径前缀 - 前缀匹配
        self.excluded_prefixes = [
            "/api/v1/users"
        ]

        self.excluded_verify_prefixes = [
            "/api/v1/users/sync",
            "/health",
            "/favicon.ico",
            "/docs",
            "/redoc", 
            "/openapi.json",
        ]

    async def dispatch(self, request: Request, call_next):
        # 获取请求路径
        path = request.url.path
        method = request.method
        # 检查是否在排除路径中
        if self._is_excluded_path(path, method, self.excluded_verify_prefixes):
            return await call_next(request)
        
        if self._is_excluded_path(path, method, self.excluded_prefixes):
            # 尝试获取token，但不强制要求
            user = await self._get_user_optional(request)
            request.state.current_user = user
            request.state.is_authenticated = user is not None
            return await call_next(request)
        
        user = await self._get_user_required(request)
        request.state.current_user = user
        request.state.is_authenticated = True
        request.state.user_id = user.id
        
        # 继续处理请求
        response = await call_next(request)
        return response

    def _is_excluded_path(self, path: str, method: str, excluded_prefixes: List[str]) -> bool:
        """检查路径是否在排除列表中"""
        # 检查前缀匹配
        for prefix in excluded_prefixes:
            if path.startswith(prefix):
                return True

        return False

    async def _get_user_optional(self, request: Request) -> Optional[User]:
        """可选获取用户信息（不抛出异常）"""
    
        token = self._extract_token(request)
        if not token:
            return None
        return await self.user_service.get_current_user(token)
       

    async def _get_user_required(self, request: Request) -> User:
        """必须获取用户信息（会抛出异常）"""
        token = self._extract_token(request)
        if not token:
            raise HTTPException(
                status_code=401,
                detail={
                    "code": 4001,
                    "message": "缺少认证token"
                }
            )
        return await self.user_service.get_current_user(token)
        
    def _extract_token(self, request: Request) -> Optional[str]:
        """从请求中提取token"""
        # 从Authorization header中提取
        authorization = request.headers.get("Authorization")
        if authorization and authorization.startswith("Bearer "):
            return authorization[7:]  # 移除 "Bearer " 前缀
            
        # 从query参数中提取（备用方案）
        token = request.query_params.get("token")
        if token:
            return token
            
        # 从cookie中提取（备用方案）
        token = request.cookies.get("access_token")
        if token:
            return token
            
        return None


async def get_current_user_required(request: Request) -> User:
    """
    获取当前已认证用户（必须）
    如果用户未认证或不存在，抛出异常
    """
    if not hasattr(request.state, "current_user") or not request.state.current_user:
        raise HTTPException(
            status_code=401,
            detail={
                "code": 4001,
                "message": "需要用户认证"
            }
        )
    return request.state.current_user


async def get_current_user_optional(request: Request) -> Optional[User]:
    """
    获取当前用户（可选）
    如果用户未认证，返回None，不抛出异常
    """
    return getattr(request.state, "current_user", None)


async def get_user_id_required(request: Request) -> str:
    """
    获取当前用户ID（必须）
    """
    user = await get_current_user_required(request)
    return user.id


async def get_user_id_optional(request: Request) -> Optional[str]:
    """
    获取当前用户ID（可选）
    """
    user = await get_current_user_optional(request)
    return user.id if user else None


def is_authenticated(request: Request) -> bool:
    """
    检查用户是否已认证
    """
    return getattr(request.state, "is_authenticated", False)