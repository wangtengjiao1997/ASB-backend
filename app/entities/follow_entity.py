from app.entities.base import BaseDocument
from typing import Optional
from datetime import datetime

class Follow(BaseDocument):
    user_id: str  # 关注者ID
    target_id: str  # 被关注的ID
    target_type: str = "user"  # 被关注的类型
    status: str = "active"  # 状态: active, blocked
    
    class Settings:
        name = "follow"
        indexes = [
            [("user_id", 1)],
            [("target_id", 1)],
            [("user_id", 1), ("target_id", 1)]  # 复合索引，保证一个用户只能关注一个代理一次
        ]