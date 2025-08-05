from app.features.like.like_service import like_service
from app.crud import user_crud, live_card_crud
from app.entities.user_entity import User
from app.schemas.like_schema import LikeResponse, LikeClick
from typing import Optional, Dict

class LikeController:
    def __init__(self):
        self.like_service = like_service
        self.user_crud = user_crud
        self.live_card_crud = live_card_crud
    
    async def like_click(
        self, 
        like_click: LikeClick,
        user: User
    ) -> Dict:
        """切换点赞状态，返回组装后的结果"""
        local_user_id = user.id
        if like_click.is_like:
            data = await self.like_service.create_like(local_user_id, like_click.target_id, like_click.target_type)
        else:
            data = await self.like_service.remove_like(local_user_id, like_click.target_id, like_click.target_type)
        return data
# 全局Controller实例
like_controller = LikeController()