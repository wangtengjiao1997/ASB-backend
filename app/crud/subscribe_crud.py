from app.crud.base_crud import BaseCRUD
from app.entities.subscribe_entity import Subscribe
from app.schemas.subscribe_schema import SubscribeCreate, SubscribeUpdate, SubscribeIncrementalParams, SubscribeFilter
from datetime import datetime
from typing import List, Tuple, Dict, Optional

class SubscribeCRUD(BaseCRUD[Subscribe, SubscribeCreate, SubscribeUpdate]):
    def __init__(self):
        super().__init__(Subscribe)
    
    async def get_subscribes_by_user_id_target_id_with_deleted(self, user_id: str, target_id: str) -> Subscribe:
        """根据用户ID和目标ID获取订阅"""
        return await Subscribe.find_one({"user_id": user_id, "target_id": target_id})
    
    async def get_subscribes_incremental(
        self,
        current_user_id: str,
        incremental_params: SubscribeIncrementalParams
    ) -> Tuple[List[Dict], int, int]:
        """获取订阅列表（带分页和过滤）"""
        query = {"user_id": current_user_id,"is_deleted": False}
        total_subscribes = await self.count(query)

        if incremental_params.direction == "before":  # before - 获取历史关注
            if incremental_params.last_id:
                last_subscribe = await Subscribe.find_one({"_id": incremental_params.last_id})
                if last_subscribe:
                    query["created_at"] = {"$lt": last_subscribe.created_at}           
        else:
            if incremental_params.last_id:
                last_subscribe = await Subscribe.find_one({"_id": incremental_params.last_id})
                if last_subscribe:
                    query["created_at"] = {"$gt": last_subscribe.created_at}
        sort_direction = -1
        
        # 执行查询，多查一条用于判断是否还有更多
        pipeline = [
            {"$match": query},
            {"$sort": {"created_at": sort_direction}},
            {"$limit": incremental_params.limit + 1},
            {"$lookup": {
                "from": "live_card",
                "localField": "target_id",
                "foreignField": "_id",
                "as": "live_card_info"
            }},
            {"$unwind": "$live_card_info"},
        ]
        subscribes = await Subscribe.get_motor_collection().aggregate(pipeline).to_list(length=None)
        
        # 判断是否还有更多
        has_more = len(subscribes) > incremental_params.limit
        if has_more:
            subscribes = subscribes[:-1]  # 移除多查的那一条
        
        return subscribes, has_more, total_subscribes

subscribe_crud = SubscribeCRUD()