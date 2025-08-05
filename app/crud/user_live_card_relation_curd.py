from typing import Optional, Dict, Any
from datetime import datetime, UTC
from app.entities.user_live_card_relation_entity import UserLiveCardRelation
from app.schemas.user_live_card_relation import (
    UserLiveCardRelationCreate, 
    UserLiveCardRelationUpdate
)
from app.crud.base_crud import BaseCRUD
from app.utils.logger_service import logger

class UserLiveCardRelationCRUD(BaseCRUD[UserLiveCardRelation, UserLiveCardRelationCreate, UserLiveCardRelationUpdate]):
    def __init__(self):
        super().__init__(UserLiveCardRelation)
    
    async def get_last_read_time(self, user_id: str, live_card_id: str) -> Optional[datetime]:
        """
        获取用户对指定直播卡片的最近阅读时间
        
        Args:
            user_id: 用户ID
            live_card_id: 直播卡片ID
            
        Returns:
            最近阅读时间，如果没有记录则返回None
        """
        relation = await UserLiveCardRelation.find_one({
            "user_id": user_id,
            "live_card_id": live_card_id,
            "is_deleted": False
        })
        
        if relation:
            return relation.last_readed_at
        return None
            
    
    async def update_last_read_time(self, user_id: str, live_card_id: str, read_time: Optional[datetime] = None) -> bool:
        """
        更新用户对指定直播卡片的最近阅读时间
        
        Args:
            user_id: 用户ID
            live_card_id: 直播卡片ID
            read_time: 阅读时间，如果为None则使用当前时间
            
        Returns:
            是否更新成功
        """
        if read_time is None:
            read_time = datetime.now(UTC)
        
        # 查找现有记录
        relation = await UserLiveCardRelation.find_one({
            "user_id": user_id,
            "live_card_id": live_card_id,
            "is_deleted": False
        })
        
        if relation:
            # 更新现有记录
            relation.last_readed_at = read_time
            await relation.save()
            logger.info(f"更新用户阅读时间成功: user_id={user_id}, live_card_id={live_card_id}")
        else:
            # 创建新记录
            new_relation = UserLiveCardRelation(
                user_id=user_id,
                live_card_id=live_card_id,
                last_readed_at=read_time,
            )
            await new_relation.save()
            logger.info(f"创建用户阅读记录成功: user_id={user_id}, live_card_id={live_card_id}")
        
        return True

# 创建实例
user_live_card_relation_crud = UserLiveCardRelationCRUD()