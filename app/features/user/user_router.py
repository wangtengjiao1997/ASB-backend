from fastapi import APIRouter, Depends, Body, Security, Header
from app.features.user.user_controller import UserController
from app.schemas.user_schema import (
    UserResponse, UserLogin, UserProfileResponse
)
from typing import Dict, Any, Optional
from fastapi import Form, File, UploadFile
from app.schemas.response_schema import BaseResponse
from fastapi.security import HTTPBearer
from app.infrastructure.auth.auth0 import Auth0
from app.entities.user_entity import User
from app.middleware.auth_middleware import get_current_user_required, get_current_user_optional


router = APIRouter(prefix="/users", tags=["用户管理"])

token_auth_scheme = HTTPBearer()
auth = Auth0()

@router.post("/sync_user", response_model=BaseResponse[UserResponse])
async def sync_user(
    token: str = Depends(token_auth_scheme),
    user_controller: UserController = Depends(UserController)
):
    """同步用户"""
    data = await user_controller.sync_user(token)
    return BaseResponse.success(data= data)

@router.get("/get_current_user", response_model=BaseResponse[UserResponse])
async def get_current_user(
    current_user: User = Depends(get_current_user_required),
):
    """获取当前用户信息 - 基于token"""
    return BaseResponse.success(data=current_user)

@router.put("/update", response_model=BaseResponse[UserResponse])
async def update(
    current_user: User = Depends(get_current_user_required),
    name: Optional[str] = Form(None),
    bio: Optional[str] = Form(None),
    status: Optional[str] = Form(None),
    password: Optional[str] = Form(None),
    picture: Optional[UploadFile] = File(None),
    user_controller: UserController = Depends(UserController)
):
    """更新用户信息"""
    data = await user_controller.update(current_user, name, bio, status, password, picture)
    return BaseResponse.success(data=data)

@router.get("/get_current_user_profile", response_model=BaseResponse[UserProfileResponse])
async def get_current_user_profile(
    current_user: User = Depends(get_current_user_required),
    user_controller: UserController = Depends(UserController)
):
    """获取用户信息"""
    data = await user_controller.get_user_profile(current_user)
    return BaseResponse.success(data=data)


@router.post("/login_by_email", response_model=BaseResponse[Dict[str, Any]])
async def login_user(login_data: UserLogin,
    user_controller: UserController = Depends(UserController)
):
    """
    用户登录接口
    
    Args:
        login_data: 包含邮箱和密码的用户登录数据
        
    Returns:
        Dict: 包含access_token和用户信息的结果
    """
    data = await user_controller.login_user(login_data)
    return BaseResponse.success(data=data)

@router.post("/add_fcm_token", response_model=BaseResponse[UserResponse])
async def add_fcm_token(
    current_user: User = Depends(get_current_user_required),
    device_id: str = Body(..., embed=True), 
    fcm_token: str = Body(..., embed=True),
    user_controller: UserController = Depends(UserController)
):
    """
    链接fcm token
    """
    data = await user_controller.add_fcm_token(current_user, device_id, fcm_token)
    return BaseResponse.success(data=data)