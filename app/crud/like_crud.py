from typing import List, Optional, Dict, Any, Tuple
from app.entities.like_entity import Like
from app.schemas.like_schema import LikeCreate, LikeUpdate, LikeFilter, LikeIncrementalParams
from app.crud.base_crud import BaseCRUD

class LikeCRUD(BaseCRUD[Like, LikeCreate, LikeUpdate]):
    def __init__(self):
        super().__init__(Like)
    
    async def count_target_likes(self, target_id: str, target_type: str) -> int:
        """计算目标的点赞数量"""
        return await Like.find({
            "target_id": target_id, 
            "target_type": target_type,
            "is_deleted": False
        }).count()
    
    async def count_user_likes(self, user_id: str, target_type: Optional[str] = None) -> int:
        """计算用户的点赞数量"""
        query = {"user_id": user_id, "is_deleted": False}
        if target_type:
            query["target_type"] = target_type
        return await Like.find(query).count()

    
    async def _build_filter_query(self, current_user_id: str) -> Dict:
        """构建点赞过滤查询条件"""
        query = {"is_deleted": False,"target_type": "live_card"}
        
        if current_user_id:
            query["user_id"] = current_user_id
                
        return query
    
    async def get_likes_live_cards_incremental(
        self,
        current_user_id: str,
        incremental_params: LikeIncrementalParams
    ) -> Tuple[List[Dict], bool, int]:
        """
        增量获取消息
        
        Args:
            filter_params: 消息过滤条件
            incremental_params: 增量参数
            
        Returns:
            Tuple[List[Message], bool]: 消息列表和是否还有更多
        """
        query = await self._build_filter_query(current_user_id)
        total_likes = await self.count_user_likes(current_user_id, "live_card")
        if incremental_params.direction == "before":  # before - 获取历史点赞
            if incremental_params.last_id:
                last_like = await Like.find_one({"_id": incremental_params.last_id})
                if last_like:
                    query["created_at"] = {"$lt": last_like.created_at}           
        else:
            if incremental_params.last_id:
                last_like = await Like.find_one({"_id": incremental_params.last_id})
                if last_like:
                    query["created_at"] = {"$gt": last_like.created_at}
        sort_direction = -1
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
            {"$lookup": {
                "from": "user",
                "localField": "user_id",
                "foreignField": "_id",
                "as": "user_info"
            }},
            {"$unwind": "$user_info"},
        ]
        likes = await Like.get_motor_collection().aggregate(pipeline).to_list(length=None)
        # 判断是否还有更多
        has_more = len(likes) > incremental_params.limit
        if has_more:
            likes = likes[:-1]  # 移除多查的那一条
        
        return likes, has_more, total_likes

    
    async def get_like(self, user_id: str, target_id: str, target_type: str) -> Optional[Like]:
        """获取特定用户对特定目标的点赞记录"""
        return await Like.find_one({
            "user_id": user_id,
            "target_id": target_id,
            "target_type": target_type,
            "is_deleted": False
        })
    async def get_like_with_deleted(self, user_id: str, target_id: str, target_type: str) -> Optional[Like]:
        """获取特定用户对特定目标的点赞记录，包括已删除的"""
        return await Like.find_one({
            "user_id": user_id,
            "target_id": target_id,
            "target_type": target_type,
        })
    async def get_is_liked(self, user_id: str, target_id: str) -> bool:
        """获取特定用户对特定目标的点赞记录"""
        return await Like.find_one({
            "user_id": user_id,
            "target_id": target_id,
            "is_deleted": False
        }) is not None
    
  
# 创建单例实例
like_crud = LikeCRUD()