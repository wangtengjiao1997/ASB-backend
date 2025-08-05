from app.crud import live_card_crud
from app.schemas.live_card_schema import LiveCardCreate, LiveCardUpdate, LiveCardFilter, LiveCardIncrementalParams
from app.entities.live_card_entity import LiveCard
from typing import List, Tuple
from app.utils.cdn_mapper import map_cdn_url

class LiveCardService:
    def __init__(self):
        self.live_card_crud = live_card_crud
    
    async def create_live_card(self, data: LiveCardCreate) -> LiveCard:
        """创建Live Card"""
        existing = await self.live_card_crud.get_live_card_by_topic_title(data.topic_title)
        if existing:
            raise ValueError(f"Live Card已存在: {data.topic_title}")
        
        return await self.live_card_crud.create(data)
    
    async def update_live_card(self, live_card_id: str, data: LiveCardUpdate) -> LiveCard:
        """更新Live Card"""
        live_card = await self.live_card_crud.get(live_card_id)
        if not live_card:
            raise ValueError("Live Card不存在")
        
        return await self.live_card_crud.update(live_card_id, data)
    
    async def get_live_cards(self, filter_params: LiveCardFilter, incremental_params: LiveCardIncrementalParams) -> Tuple[List[LiveCard], bool, int]:
        """获取带统计的Live Cards"""
        live_cards, has_more, total = await self.live_card_crud.get_live_cards_incremental(filter_params, incremental_params)
        for live_card in live_cards:
            live_card.topic_image_url = map_cdn_url(live_card.topic_image_url)
        return live_cards, has_more, total
    
    async def get_subscribing_live_cards(self, user_id: str, filter_params: LiveCardFilter, incremental_params: LiveCardIncrementalParams) -> Tuple[List[LiveCard], bool, int]:
        """获取用户订阅的Live Cards"""
        live_cards, has_more, total = await self.live_card_crud.get_subscribing_live_cards(user_id, filter_params, incremental_params)
        for live_card in live_cards:
            live_card.topic_image_url = map_cdn_url(live_card.topic_image_url)
        return live_cards, has_more, total
    
    async def increment_share_count(self, live_card_id: str) -> bool:
        """增加分享次数"""
        return await self.live_card_crud.increment_field(live_card_id, "share_count", 1) is not None

# 全局服务实例
live_card_service = LiveCardService()