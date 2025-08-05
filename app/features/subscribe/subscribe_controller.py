from app.features.subscribe.subscribe_service import subscribe_service
from app.entities.user_entity import User
from app.schemas.subscribe_schema import SubscribeClick
from typing import List

class SubscribeController:
    def __init__(self):
        self.service = subscribe_service
    
    async def subscribe_click(self, subscribe_click: SubscribeClick, user: User) -> dict:
        """切换订阅状态"""
        local_user_id = user.id
        if subscribe_click.is_subscribe:
            data = await self.service.create_subscribe(local_user_id, subscribe_click.target_id, subscribe_click.target_type)
        else:
            data = await self.service.remove_subscribe(local_user_id, subscribe_click.target_id)
        return data
# 全局Controller实例
subscribe_controller = SubscribeController()