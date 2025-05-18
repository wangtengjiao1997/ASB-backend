from fastapi import APIRouter, Depends, Body
from app.features.post.post_controller import PostController
from app.schemas.post_shema import (
    PostCreate, PostUpdate, PostResponse, PostFilter, 
    PaginationParams, PostPaginatedResponse
)
from typing import Dict, Any
from app.schemas.response_schema import BaseResponse
router = APIRouter(prefix="/posts", tags=["帖子管理"])

@router.post("/create_post", response_model=BaseResponse[PostResponse])
async def create_post(post_data: PostCreate):
    """创建帖子"""
    data = await PostController.create_post(post_data)
    return BaseResponse.success(data=data)

@router.get("/get_post_by_id/{post_id}", response_model=BaseResponse[PostResponse])
async def get_post(post_id: str):
    """获取帖子信息"""
    data = await PostController.get_post(post_id)
    return BaseResponse.success(data=data)

@router.put("/update_post_by_id/{post_id}", response_model=BaseResponse[PostResponse])
async def update_post(post_id: str, update_data: PostUpdate):
    """更新帖子信息"""
    data = await PostController.update_post(post_id, update_data)
    return BaseResponse.success(data=data)

@router.delete("/delete_post_by_id/{post_id}", response_model=Dict[str, bool])
async def delete_post(post_id: str):
    """删除帖子"""
    data = await PostController.delete_post(post_id)
    return BaseResponse.success(data=data)

@router.get("/get_posts_with_filter", response_model=BaseResponse[PostPaginatedResponse])
async def get_posts_with_filter(
    filter_params: PostFilter = Depends(),
    pagination: PaginationParams = Depends()
):
    """获取帖子列表（带过滤和分页）"""
    data = await PostController.get_posts_with_filter(filter_params, pagination)
    return BaseResponse.success(data=data)