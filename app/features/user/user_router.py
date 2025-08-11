from fastapi import APIRouter, Depends, Body
from app.features.user.user_controller import UserController
from app.schemas.user_schema import (
    UserResponse, UserProfileResponse, WechatCode,
    WechatUserInfo, WechatLoginResponse, UserUpdate
)
from typing import Dict, Any, Optional
from fastapi import Form
from app.schemas.response_schema import BaseResponse
from app.entities.user_entity import User
from app.middleware.auth_middleware import get_current_user_required, get_current_user_optional
from fastapi.security import HTTPBearer

router = APIRouter(prefix="/users", tags=["用户管理"])
token_auth_scheme = HTTPBearer()

@router.post("/sync", response_model=BaseResponse[WechatLoginResponse])
async def sync_user(
    token: str = Depends(token_auth_scheme),
    user_controller: UserController = Depends(UserController)
):
    """
    微信小程序登录
    
    Args:
        code_data: 包含微信登录code的数据
    """
    data = await user_controller.sync_user(token)
    return BaseResponse.success(data=data)

@router.post("/update_current_user_info", response_model=BaseResponse[UserResponse])
async def update_current_user_info(
    user_info: UserUpdate,
    user: User = Depends(get_current_user_required),
    user_controller: UserController = Depends(UserController)
):
    data = await user_controller.update_current_user_info(user, user_info)
    return BaseResponse.success(data=data)