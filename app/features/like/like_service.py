from app.crud import like_crud, live_card_crud
from app.schemas.like_schema import LikeCreate, LikeUpdate
from app.entities.like_entity import Like
from typing import Dict

class LikeService:
    def __init__(self):
        self.like_crud = like_crud
        self.live_card_crud = live_card_crud

    async def create_like(self, user_id: str, target_id: str, target_type: str) -> Dict:
        """创建点赞"""
        existing = await self.like_crud.find_one({"user_id": user_id, "target_id": target_id, "target_type": target_type})
        if existing:
            if existing.is_deleted:
                await self.like_crud.update(str(existing.id), LikeUpdate(is_deleted=False, deleted_at=None))
                await self.live_card_crud.increment_field(target_id, "like_count", 1)
                await self.live_card_crud.increment_field(target_id, "trending_score", 5)
        else:
            like_data = LikeCreate(
                user_id=user_id,
                target_id=target_id,
                target_type=target_type
            )
            await self.like_crud.create(like_data)
            await self.live_card_crud.increment_field(target_id, "like_count", 1)
            await self.live_card_crud.increment_field(target_id, "trending_score", 5)
        live_card = await self.live_card_crud.get(target_id)
        return {"success": True, "like_count": live_card.like_count}
    
    async def remove_like(self, user_id: str, target_id: str, target_type: str) -> Dict:
        """取消点赞"""
        like = await self.like_crud.find_one({"user_id": user_id, "target_id": target_id, "target_type": target_type, "is_deleted": False})
        if like:
            await self.like_crud.delete(str(like.id))
            await self.live_card_crud.increment_field(target_id, "like_count", -1)
            await self.live_card_crud.increment_field(target_id, "trending_score", -5)
        live_card = await self.live_card_crud.get(target_id)
        return {"success": True, "like_count": live_card.like_count}

# 全局服务实例
like_service = LikeService()