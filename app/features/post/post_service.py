from typing import List, Optional, Dict, Any, Tuple
from app.schemas.post_shema import PostFilter, PaginationParams, PostCreate, PostUpdate
from app.entities.post_entity import Post
from app.crud.post_crud import post_crud

class PostService:
    @staticmethod
    async def create_post(post_data: PostCreate) -> Post:
        """创建帖子"""
        return await post_crud.create(post_data)

    @staticmethod
    async def get_post(post_id: str) -> Optional[Post]:
        """根据ID获取帖子"""
        return await post_crud.get(post_id)

    @staticmethod
    async def update_post(post_id: str, update_data: PostUpdate) -> Optional[Post]:
        """更新帖子信息"""
        return await post_crud.update(post_id, update_data)

    @staticmethod
    async def delete_post(post_id: str) -> bool:
        """删除帖子"""
        return await post_crud.delete(post_id)

    @staticmethod
    async def get_posts_with_filter(
        filter_params: PostFilter,
        pagination: PaginationParams
    ) -> Tuple[List[Post], int]:
        """带分页和过滤的帖子列表查询"""
        return await post_crud.get_posts_with_filter(filter_params, pagination)