from app.entities.base import BaseDocument
from typing import Optional
from pydantic import Field
from datetime import datetime

class UserLiveCardRelation(BaseDocument):
    user_id: str  # 接收通知的用户ID
    live_card_id: str  # 触发通知的用户ID
    last_readed_at: datetime  # 最后阅读时间
    
    class Settings:
        name = "user_live_card_relation"
        indexes = [
            [("user_id", 1)],
            [("live_card_id", 1)],
            [("last_readed_at", -1)]  # 按最后阅读时间降序索引
        ]