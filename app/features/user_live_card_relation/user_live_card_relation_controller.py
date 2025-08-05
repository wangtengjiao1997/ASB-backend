from fastapi import HTTPException
from app.features.user_live_card_relation.user_live_card_relation_service import user_live_card_relation_service
from app.utils.logger_service import logger
from app.entities.user_entity import User

class UserLiveCardRelationController:
    def __init__(self):
        self.service = user_live_card_relation_service
    
    async def get_last_read_time(self, current_user: User, live_card_id: str):
        try:
            result = await self.service.get_last_read_time(current_user, live_card_id)
            return {"last_read_time": result}
        except Exception as e:
            logger.error(f"获取阅读时间失败: {str(e)}")
            raise HTTPException(status_code=500, detail="获取阅读时间失败")
    
    async def update_last_read_time(self, current_user: User, live_card_id: str):
        try:
            result = await self.service.update_last_read_time(current_user, live_card_id)
            return {"success": result}
        except Exception as e:
            logger.error(f"更新阅读时间失败: {str(e)}")
            raise HTTPException(status_code=500, detail="更新阅读时间失败")

# 创建控制器实例
user_live_card_relation_controller = UserLiveCardRelationController()