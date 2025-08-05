from app.entities.base import BaseDocument

class Like(BaseDocument):
    user_id: str  # 用户ID
    target_id: str  # 点赞目标的ID
    target_type: str  # 点赞目标的类型，如 "post", "comment", "agent" 等
    
    class Settings:
        name = "like"
        indexes = [
            [("user_id", 1)],
            [("target_id", 1)],
            [("target_type", 1)],
            [("user_id", 1), ("target_id", 1), ("target_type", 1)]  # 复合索引，保证一个用户只能点赞一个特定类型的目标一次
        ]