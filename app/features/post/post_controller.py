from fastapi import HTTPException, status, Depends
from app.features.post.post_service import PostService
from app.schemas.post_shema import (
    PostCreate, PostUpdate, PostResponse, PostFilter, 
    PaginationParams, PostPaginatedResponse
)
from typing import Dict, Any, List
import math

class PostController:
    @staticmethod
    async def create_post(post_data: PostCreate) -> Dict[str, Any]:
        """处理创建帖子请求"""
        try:
            post = await PostService.create_post(post_data)
            return PostResponse.model_validate(post)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"创建帖子失败: {str(e)}"
            )

    @staticmethod
    async def get_post(post_id: str) -> Dict[str, Any]:
        """处理获取帖子请求"""
        try:
            post = await PostService.get_post(post_id)
            if not post:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="帖子不存在"
                )
            return PostResponse.model_validate(post)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"获取帖子失败: {str(e)}"
            )

    @staticmethod
    async def update_post(post_id: str, update_data: PostUpdate) -> Dict[str, Any]:
        """处理更新帖子请求"""
        try:
            post = await PostService.update_post(post_id, update_data)
            if not post:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="帖子不存在"
                )
            return PostResponse.model_validate(post)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"更新失败: {str(e)}"
            )

    @staticmethod
    async def delete_post(post_id: str) -> Dict[str, bool]:
        """处理删除帖子请求"""
        try:
            success = await PostService.delete_post(post_id)
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="帖子不存在"
                )
            return {"success": True}
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"删除失败: {str(e)}"
            )

    @staticmethod
    async def list_posts(
        filter_params: PostFilter = Depends(),
        pagination: PaginationParams = Depends()
    ) -> PostPaginatedResponse:
        """处理获取帖子列表请求（带分页和过滤）"""
        posts, total = await PostService.get_posts_with_filter(filter_params, pagination)
        
        # 计算分页信息
        current_page = pagination.page
        total_pages = math.ceil(total / pagination.page_size)
        
        # 将帖子列表转换为响应对象
        post_responses = [PostResponse.model_validate(post) for post in posts]
        
        return PostPaginatedResponse(
            total=total,
            items=post_responses,
            page=current_page,
            page_size=pagination.page_size,
            total_pages=total_pages
        )