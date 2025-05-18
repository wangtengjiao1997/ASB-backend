from fastapi import APIRouter, Depends, Body, Security
from app.features.user.user_controller import UserController
from app.schemas.user_schema import (
    UserCreate, UserUpdate, UserResponse, UserFilter,                                                                                                                                                                                         
    PaginationParams, PaginatedResponse
)
from typing import Dict
from app.schemas.response_schema import BaseResponse
from app.core.auth.auth import auth
from fastapi_auth0 import Auth0User

router = APIRouter(prefix="/users", tags=["用户管理"])

@router.post("/create_user", response_model=BaseResponse[UserResponse])
async def create_user(user_data: UserCreate):
    """创建用户"""
    data = await UserController.create_user(user_data)
    return BaseResponse.success(data=data)

@router.get("/get_user_by_id/{user_id}", response_model=BaseResponse[UserResponse])
async def get_user_by_id(
    user_id: str,
):
    """获取用户信息 - 需要有效的Auth0 token和read:users权限"""
    data = await UserController.get_user_by_id(user_id)
    return BaseResponse.success(data=data)

@router.get("/get_current_user", dependencies=[Depends(auth.implicit_scheme)], response_model=BaseResponse[Dict])
async def get_current_user(
    user: Auth0User = Security(auth.get_user)
):
    """获取当前用户信息 - 基于token"""
    user_info = {
        "id": user.id,
        "email": user.email,
        "permissions": user.permissions
    }
    return BaseResponse.success(data=user_info)

@router.put("/update_user_by_id/{user_id}", response_model=BaseResponse[UserResponse])
async def update_user_by_id(user_id: str, update_data: UserUpdate):
    """更新用户信息"""
    data = await UserController.update_user_by_id(user_id, update_data)
    return BaseResponse.success(data=data)

@router.delete("/delete_user_by_id/{user_id}", response_model=BaseResponse[bool])
async def delete_user_by_id(user_id: str):
    """删除用户"""
    data = await UserController.delete_user_by_id(user_id)
    return BaseResponse.success(data=data)

@router.get("/get_users_with_filter", response_model=BaseResponse[PaginatedResponse])
async def get_users_with_filter(
    filter_params: UserFilter = Depends(),
    pagination: PaginationParams = Depends()
):
    """获取用户列表（带过滤和分页）"""
    data = await UserController.get_users_with_filter(filter_params, pagination)
    return BaseResponse.success(data=data)