from app.features.live_card.live_card_service import live_card_service
from app.crud import user_crud, like_crud, subscribe_crud
from app.schemas.live_card_schema import LiveCardResponse, LiveCardCreate, LiveCardUpdate, LiveCardFilter, LiveCardIncrementalParams, LiveCardIncrementalResponse
from app.entities.user_entity import User
from app.entities.live_card_entity import LiveCard
from typing import List, Optional, Set, Tuple, Dict
from datetime import datetime
import asyncio

class LiveCardController:
    def __init__(self):
        self.live_card_service = live_card_service
        self.user_crud = user_crud
        self.like_crud = like_crud
        self.subscribe_crud = subscribe_crud
    
    async def _get_user_interaction_status(
        self,
        current_user: Optional[User],
        live_card_ids: List[str]
    ) -> Tuple[Set[str], Set[str]]:
        """获取用户对live_card的交互状态（点赞、订阅）
        
        Args:
            current_user: 当前用户
            live_card_ids: live_card ID列表
            
        Returns:
            Tuple[Set[str], Set[str]]: (点赞的live_card_ids, 订阅的live_card_ids)
        """
        user_likes = set()
        user_subscribes = set()
        
        if not current_user or not live_card_ids:
            return user_likes, user_subscribes
        
        # 批量获取点赞状态和订阅状态
        likes_task = self.like_crud.find({
            "user_id": current_user.id, 
            "target_id": {"$in": live_card_ids}, 
            "target_type": "live_card",
            "is_deleted": False
        })
        
        subscribes_task = self.subscribe_crud.find({
            "user_id": current_user.id,
            "target_id": {"$in": live_card_ids},
            "target_type": "live_card",
            "is_deleted": False
        })
        
        # 并发执行两个查询
        likes, subscribes = await asyncio.gather(likes_task, subscribes_task)
        
        user_likes = {like.target_id for like in likes}
        user_subscribes = {sub.target_id for sub in subscribes}
        
        return user_likes, user_subscribes

    async def _build_live_card_responses(
        self,
        live_cards: List[LiveCard],
        user_likes: Set[str],
        user_subscribes: Set[str]
    ) -> List[LiveCardResponse]:
        """构建LiveCard响应列表
        
        Args:
            live_cards: LiveCard对象列表
            user_likes: 用户点赞的live_card_ids集合
            user_subscribes: 用户订阅的live_card_ids集合
            
        Returns:
            List[LiveCardResponse]: 响应对象列表
        """
        responses = []
        for card in live_cards:
            card_id = str(card.id)
            response = LiveCardResponse(
                **card.model_dump(),
                is_liked=card_id in user_likes,
                is_subscribed=card_id in user_subscribes
            )
            responses.append(response)
        
        return responses

    async def create_live_card(self, data: LiveCardCreate) -> LiveCardResponse:
        """创建Live Card并组装响应数据"""
        live_card = await self.live_card_service.create_live_card(data)
        
        # 获取创建者信息
        creator = await self.user_crud.get(live_card.creator_id) if hasattr(live_card, 'creator_id') else None
        
        return LiveCardResponse(
            **live_card.model_dump(),
            is_liked=False,
            is_subscribed=False,
        )
    
    async def update_live_card(self, live_card_id: str, data: LiveCardUpdate) -> LiveCardResponse:
        """更新Live Card"""
        live_card = await self.live_card_service.update_live_card(live_card_id, data)
        return LiveCardResponse(**live_card.model_dump())

    async def get_explore_live_cards(
        self, 
        filter_params: LiveCardFilter, 
        incremental_params: LiveCardIncrementalParams,
        current_user: Optional[User]
    ) -> LiveCardIncrementalResponse:
        """为用户组装Live Card列表数据"""
        live_cards, has_more, total = await self.live_card_service.get_live_cards(filter_params, incremental_params)

        if not live_cards:
            return LiveCardIncrementalResponse(
                items=[],
                has_more=False,
                last_id="",
                last_timestamp=datetime.now(),
                total=total
            )

        live_card_ids = [str(card.id) for card in live_cards]

         # 使用抽取的方法获取用户交互状态
        user_likes, user_subscribes = await self._get_user_interaction_status(
            current_user, live_card_ids
        )

        # 使用抽取的方法构建响应
        responses = await self._build_live_card_responses(
            live_cards, user_likes, user_subscribes
        )
        
        return LiveCardIncrementalResponse(
            items=responses,
            has_more=has_more,
            last_id=live_cards[-1].id if live_cards else "",
            last_timestamp=live_cards[-1].updated_at if live_cards else datetime.now(),
            total=total
        )

    async def get_subscribing_live_cards(
        self, 
        filter_params: LiveCardFilter, 
        incremental_params: LiveCardIncrementalParams,
        current_user: Optional[User]
    ) -> LiveCardIncrementalResponse:
        """获取用户订阅的Live Card列表"""
        if not current_user:
            return LiveCardIncrementalResponse(
                items=[], 
                has_more=False, 
                last_id="", 
                last_timestamp=datetime.now(), 
                total=0
            )

        # 使用聚合管道获取订阅的live_cards
        live_cards, has_more, total = await self.live_card_service.get_subscribing_live_cards(
            current_user.id, filter_params, incremental_params
        )

        if not live_cards:
            return LiveCardIncrementalResponse(
                items=[], 
                has_more=False, 
                last_id="", 
                last_timestamp=datetime.now(), 
                total=total
            )

        live_card_ids = [str(card.id) for card in live_cards]

        # 复用相同的交互状态获取逻辑
        user_likes, user_subscribes = await self._get_user_interaction_status(
            current_user, live_card_ids
        )
        
        # 对于订阅查询，所有live_card都是已订阅的，可以优化
        user_subscribes = set(live_card_ids)  # 直接设置为全部已订阅
        
        # 复用响应构建逻辑
        responses = await self._build_live_card_responses(
            live_cards, user_likes, user_subscribes
        )

        return LiveCardIncrementalResponse(
            items=responses,
            has_more=has_more,
            last_id=live_cards[-1].id if live_cards else "",
            last_timestamp=live_cards[-1].updated_at if live_cards else datetime.now(),
            total=total
        )

    async def add_share_count(self, live_card_id: str) -> dict:
        """增加分享次数"""
        success = await self.live_card_service.increment_share_count(live_card_id)
        return {"success": success}

# 全局Controller实例
live_card_controller = LiveCardController()