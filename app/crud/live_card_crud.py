from typing import List, Dict, Tuple, Optional
from app.entities.live_card_entity import LiveCard
from app.schemas.live_card_schema import (
    LiveCardCreate, 
    LiveCardUpdate, 
    LiveCardFilter, 
    LiveCardIncrementalParams
)
from app.crud.base_crud import BaseCRUD

class LiveCardCRUD(BaseCRUD[LiveCard, LiveCardCreate, LiveCardUpdate]):
    def __init__(self):
        super().__init__(LiveCard)
    
    def _build_filter_query(self, filter_params: LiveCardFilter) -> Dict:
        """构建 Live Card 过滤查询条件"""
        query = {"is_deleted": False}
        if filter_params.topic_title:
            query["topic_title"] = filter_params.topic_title
        return query
    
    async def _build_incremental_filters(self, incremental_params: LiveCardIncrementalParams) -> List[Dict]:
        """构建增量查询的过滤条件"""
        pipeline = []
        sort_field = incremental_params.sort_by
        if incremental_params.direction == "before":  # before - 获取历史帖子
            if incremental_params.last_id:
                last_live_card = await LiveCard.find_one({"_id": incremental_params.last_id})
                if last_live_card:
                    pipeline.append({"$match": {sort_field: {"$lt": sort_field}}})
        else:
            if incremental_params.last_id:
                last_live_card = await LiveCard.find_one({"_id": incremental_params.last_id})
                if last_live_card:
                    pipeline.append({"$match": {sort_field: {"$gt": sort_field}}})

        if incremental_params.direction == "before":
            pipeline.append({"$sort": {sort_field: -1}})
        else:
            pipeline.append({"$sort": {sort_field: 1}})

        pipeline.append({"$limit": incremental_params.limit + 1})

        return pipeline

    async def get_live_card_by_topic_title(self, topic_title: str) -> Optional[LiveCard]:
        """根据 topic_title 获取 Live Card"""
        return await LiveCard.find_one({"topic_title": topic_title})

    async def get_live_cards_incremental(
        self,
        filter_params: LiveCardFilter,
        incremental_params: LiveCardIncrementalParams
    ) -> Tuple[List[LiveCard], bool, int]:
        """获取 Live Card 列表（增量更新）"""

        query = self._build_filter_query(filter_params)
        
        # 获取总数
        total = await LiveCard.find(query).count()
        sort_field = incremental_params.sort_by

        if incremental_params.direction == "before":
            if incremental_params.last_id:
                last_live_card = await LiveCard.find_one({"_id": incremental_params.last_id})
                if last_live_card:
                    query[sort_field] = {"$lt": sort_field}
        else:
            if incremental_params.last_id:
                last_live_card = await LiveCard.find_one({"_id": incremental_params.last_id})
                if last_live_card:
                    query["sort_field"] = {"$gt": sort_field}
        
        
        # 查询结果
        live_cards = await LiveCard.find(query).sort(
            [(sort_field, -1 if incremental_params.direction == "before" else 1)]
        ).limit(incremental_params.limit + 1).to_list()
        
        # 判断是否还有更多
        has_more = len(live_cards) > incremental_params.limit
        if has_more:
            live_cards = live_cards[:-1]  # 移除多查的那一条
            
        return live_cards, has_more, total

    async def get_subscribing_live_cards(
        self, 
        user_id: str, 
        filter_params: LiveCardFilter, 
        incremental_params: LiveCardIncrementalParams
    ) -> Tuple[List[LiveCard], bool, int]:
        """获取用户订阅的 Live Card 列表"""
        query = self._build_filter_query(filter_params)
        pipeline = [
            {
                "$match": query
            },
            {
                "$lookup": {
                    "from": "subscribes",  
                    "localField": "_id", 
                    "foreignField": "target_id",
                    "as": "subscribes"
                }
            },
            {
                "$match": {
                    "subscribes.user_id": user_id
                }
            },
            *await self._build_incremental_filters(incremental_params)
        ]
    
        # 执行聚合查询
        results = await LiveCard.aggregate(pipeline, projection_model=LiveCard).to_list()
        
        # 处理分页逻辑
        has_more = len(results) > incremental_params.limit
        if has_more:
            results = results[:-1]  # 移除多查询的那一条
        
        return results, has_more, len(results)
    
# 创建单例实例
live_card_crud = LiveCardCRUD()