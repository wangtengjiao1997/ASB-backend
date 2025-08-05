from fastapi import APIRouter, Depends, Body, Security
from app.features.follow.follow_controller import follow_controller
from app.schemas.follow_schema import (
    FollowCreate, FollowUpdate, FollowResponse, FollowFilter,
    PaginationParams, PaginatedResponse, FollowClick,
    FollowIncrementalParams, FollowIncrementalResponse
)
from typing import Dict
from app.schemas.response_schema import BaseResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Security
from app.middleware.auth_middleware import get_current_user_required, get_current_user_optional
from app.entities.user_entity import User

router = APIRouter(prefix="/follows", tags=["关注管理"])

@router.post("/follow_click", response_model=BaseResponse[Dict])
async def follow_click(follow_click: FollowClick, current_user: User = Depends(get_current_user_required)):
    """关注点击"""
    data = await follow_controller.follow_click(current_user, follow_click)
    return BaseResponse.success(data=data)

@router.get("/follow_list", response_model=BaseResponse[FollowIncrementalResponse])
async def follow_list(
    current_user: User = Depends(get_current_user_required),
    incremental_params: FollowIncrementalParams = Depends(FollowIncrementalParams)
):
    """获取关注列表（带过滤和分页）"""
    data = await follow_controller.follow_list(current_user, incremental_params)
    return BaseResponse.success(data=data)