from typing import List, Optional, Dict, Any, Tuple
from app.entities.follow_entity import Follow
from app.schemas.follow_schema import FollowCreate, FollowUpdate, FollowFilter, PaginationParams, FollowIncrementalParams
from app.crud.base_crud import BaseCRUD

class FollowCRUD(BaseCRUD[Follow, FollowCreate, FollowUpdate]):
    def __init__(self):
        super().__init__(Follow)
    
    async def _build_filter_query(self, filter_params: FollowFilter) -> Dict:
        """构建关注过滤查询条件"""
        query = {"is_deleted": False}
        
        if filter_params.user_id:
            query["user_id"] = filter_params.user_id
            
        if filter_params.agent_id:
            query["agent_id"] = filter_params.agent_id
            
        if filter_params.status:
            query["status"] = filter_params.status
            
        if filter_params.created_after:
            query["created_at"] = {"$gte": filter_params.created_after}
            
        if filter_params.created_before:
            if "created_at" in query:
                query["created_at"]["$lte"] = filter_params.created_before
            else:
                query["created_at"] = {"$lte": filter_params.created_before}
                
        return query

    async def check_is_followed(self, user_id: str, target_id: str, target_type: str) -> bool:
        """检查用户是否关注了目标"""
        return await Follow.find_one({"user_id": user_id, "target_id": target_id, "target_type": target_type, "is_deleted": False}) is not None
    
    async def get_follows_incremental(
        self,
        current_user_id: str,
        incremental_params: FollowIncrementalParams
    ) -> Tuple[List[Dict], int, int]:
        """获取关注列表（带分页和过滤）"""
        query = {"user_id": current_user_id,"is_deleted": False}
        total_follows = await self.count(query)

        if incremental_params.direction == "before":  # before - 获取历史关注
            if incremental_params.last_id:
                last_follow = await Follow.find_one({"_id": incremental_params.last_id})
                if last_follow:
                    query["created_at"] = {"$lt": last_follow.created_at}           
        else:
            if incremental_params.last_id:
                last_follow = await Follow.find_one({"_id": incremental_params.last_id})
                if last_follow:
                    query["created_at"] = {"$gt": last_follow.created_at}
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
        follows = await Follow.get_motor_collection().aggregate(pipeline).to_list(length=None)
        
        # 判断是否还有更多
        has_more = len(follows) > incremental_params.limit
        if has_more:
            follows = follows[:-1]  # 移除多查的那一条
        
        return follows, has_more, total_follows
    
    async def get_following_targets(self, user_id: str, target_type: str) -> List[str]:
        """获取用户关注的代理ID列表"""
        follows = await self.model.find({"user_id": user_id, "target_type": target_type, "is_deleted": False}).to_list()
        return [follow.target_id for follow in follows]
    
    
# 创建单例实例
follow_crud = FollowCRUD()