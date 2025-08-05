from app.crud import subscribe_crud, live_card_crud
from app.schemas.subscribe_schema import SubscribeCreate, SubscribeUpdate
from typing import Dict

class SubscribeService:
    def __init__(self):
        self.subscribe_crud = subscribe_crud
        self.live_card_crud = live_card_crud
    
    async def create_subscribe(self, user_id: str, target_id: str, target_type: str) -> Dict:
        """创建订阅"""
        # 检查Live Card是否存在
        if target_type == "live_card":
            live_card = await self.live_card_crud.get(target_id)
            if not live_card:
                raise ValueError("Live Card不存在")
        
        # 检查是否已订阅
        existing = await self.subscribe_crud.find_one({"user_id": user_id, "target_id": target_id, "target_type": target_type})
        if existing:
            if existing.is_deleted:
                await self.subscribe_crud.update(str(existing.id), SubscribeUpdate(is_deleted=False, deleted_at=None))
                await self.live_card_crud.increment_field(target_id, "subscribe_count", 1)
                await self.live_card_crud.increment_field(target_id, "trending_score", 10)
        else:
            subscribe_data = SubscribeCreate(user_id=user_id, target_id=target_id, target_type=target_type)
            await self.subscribe_crud.create(subscribe_data)
            await self.live_card_crud.increment_field(target_id, "subscribe_count", 1)
            await self.live_card_crud.increment_field(target_id, "trending_score", 10)

        live_card = await self.live_card_crud.get(target_id)
        return {"success": True, "subscribe_count": live_card.subscribe_count}
    
    async def remove_subscribe(self, user_id: str, target_id: str, target_type: str) -> Dict:
        """取消订阅"""
        subscribe = await self.subscribe_crud.find_one({
            "user_id": user_id,
            "target_id": target_id,
            "target_type": target_type,
            "is_deleted": False
        })
        if subscribe:
            await self.subscribe_crud.delete(str(subscribe.id))
            await self.live_card_crud.increment_field(target_id, "subscribe_count", -1)
            await self.live_card_crud.increment_field(target_id, "trending_score", -10)
        live_card = await self.live_card_crud.get(target_id)
        return {"success": True, "subscribe_count": live_card.subscribe_count}


# 全局服务实例
subscribe_service = SubscribeService()