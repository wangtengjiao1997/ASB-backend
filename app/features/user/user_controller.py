from fastapi import HTTPException, status
from app.features.user.user_service import UserService
from app.schemas.user_schema import (
    UserResponse, UserProfileResponse, WechatCode,
    WechatUserInfo, WechatLoginResponse, UserUpdate
)
from typing import Dict, Any, Optional, List
from fastapi import Form, File, UploadFile
from app.entities.user_entity import User

class UserController:
    def __init__(self):
        self.user_service = UserService()

    async def sync_user(self, token: str) -> WechatLoginResponse:
        """
        处理微信登录请求
        
        Args:
            code: 微信登录code
        """
        try:
            print(token.credentials)
            result = await self.user_service.sync_user(token.credentials)
            print(result)
            return WechatLoginResponse(
                session_info=result["session_info"],
                token=result["token"],
                user=result["user"]
            )
        except Exception as e:
            raise HTTPException(
                status_code=401,
                detail=f"微信登录失败: {str(e)}"
            )

    async def update_current_user_info(self, user: User, user_info: UserUpdate) -> UserResponse:
        result = await self.user_service.update_user_info(user.id, user_info)
        return UserResponse.model_validate(result.model_dump())