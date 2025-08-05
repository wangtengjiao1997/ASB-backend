from datetime import datetime
from typing import Optional
from app.crud.user_live_card_relation_curd import user_live_card_relation_crud
from app.utils.logger_service import logger
from app.entities.user_entity import User

class UserLiveCardRelationService:
    def __init__(self):
        self.user_live_card_relation_crud = user_live_card_relation_crud

    async def get_last_read_time(self, current_user: User, live_card_id: str) -> Optional[datetime]:
        user_id = current_user.id
        return await self.user_live_card_relation_crud.get_last_read_time(user_id, live_card_id)
    
    async def update_last_read_time(self, current_user: User, live_card_id: str) -> bool:
        user_id = current_user.id
        return await self.user_live_card_relation_crud.update_last_read_time(user_id, live_card_id)

# 创建服务实例
user_live_card_relation_service = UserLiveCardRelationService()