from typing import List, Optional, Tuple, Dict
from app.schemas.follow_schema import FollowUpdate, FollowResponse, FollowIncrementalParams, FollowCreate
from app.entities.follow_entity import Follow
from app.crud import follow_crud, user_crud
from fastapi import HTTPException
from app.entities.user_entity import User

class FollowService:
    def __init__(self):
        self.follow_crud = follow_crud
        self.user_crud = user_crud
    
    async def create_follow(self, user_id: str, target_id: str, target_type: str) -> Dict:
        """创建关注关系"""
        # 检查是否存在该用户
        existing = await self.follow_crud.find_one({"user_id": user_id, "target_id": target_id, "target_type": target_type})
        if existing:
            if existing.is_deleted:
                await self.follow_crud.update(existing.id, FollowUpdate(is_deleted=False))
                await self.user_crud.increment_field(target_id, "follower_count", 1)
                await self.user_crud.increment_field(user_id, "following_count", 1)
                await self.user_crud.increment_field(target_id, "trending_score", 5)
        else:
            follow_data = FollowCreate(
                user_id=user_id,
                target_id=target_id,
                target_type=target_type
            )
            await self.follow_crud.create(follow_data)
            await self.user_crud.increment_field(target_id, "follower_count", 1)
            await self.user_crud.increment_field(user_id, "following_count", 1)
            await self.user_crud.increment_field(target_id, "trending_score", 5)
        user = await self.user_crud.get(target_id)
        return {"success": True, "follower_count": user.follower_count}

    async def remove_follow(self, user_id: str, target_id: str, target_type: str) -> Dict:
        """取消关注"""
        follow = await self.follow_crud.find_one({"user_id": user_id, "target_id": target_id, "target_type": target_type, "is_deleted": False})
        if follow:
            await self.follow_crud.delete(follow.id)
            await self.user_crud.increment_field(target_id, "follower_count", -1)
            await self.user_crud.increment_field(user_id, "following_count", -1)
            await self.user_crud.increment_field(target_id, "trending_score", -5)
        user = await self.user_crud.get(target_id)
        return {"success": True, "follower_count": user.follower_count}

    async def follow_list(
        self,
        current_user: User,
        incremental_params: FollowIncrementalParams
    ) -> Tuple[List[FollowResponse], bool, int]:
        """处理获取关注列表请求（带分页和过滤）"""
        follows_list, has_more, total = await self.follow_crud.get_follows_incremental(current_user.id, incremental_params)
        follows_responses = []
        for follow in follows_list:
            follow_base = FollowResponse(**{
                k: v for k, v in follow.items()
                if k not in ["is_deleted", "deleted_at"]
            }, id=str(follow.get("_id")))
            follows_responses.append(follow_base)   
        return follows_responses, has_more, total

# 全局服务实例
follow_service = FollowService()