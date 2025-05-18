from app.entities.base import BaseDocument
from typing import Dict, Any, Optional
from datetime import datetime
from bson import ObjectId
from pydantic import Field

class ReadStatus:
    UNREAD = "unread"
    READ = "read"

class FeedStatus:
    ACTIVE = "active"
    DELETED = "deleted"
    HIDDEN = "hidden"

class UserFeed(BaseDocument):
    userId: str
    postId: str
    agentId: str
    createdAt: datetime
    deliveredAt: Optional[datetime] = None
    readStatus: str = ReadStatus.UNREAD  # unread, read
    status: str = FeedStatus.ACTIVE      # active, deleted, hidden 等
    isChase: bool = False                # 是否是追踪的
    isFollow: bool = False               # 是否是关注的
    score: float = 0.0                   # 排序分数
    metadata: Dict[str, Any] = Field(default_factory=dict)  # 元数据

    model_config = {
        "arbitrary_types_allowed": True
    }

    class Settings:
        name = "user_feed"
        indexes = [
            [("userId", 1)],
            [("postId", 1)],
            [("userId", 1), ("postId", 1)],  # 联合索引
            [("userId", 1), ("createdAt", -1)],  # 用于按时间查询
            [("userId", 1), ("score", -1)]   # 用于按分数排序
        ] 