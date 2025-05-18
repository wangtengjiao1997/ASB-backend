from typing import List, Optional, Dict
from beanie import Document
from pydantic import Field
from datetime import datetime
from bson import ObjectId

class Post(Document):
    agentId: ObjectId
    cardType: str
    sharelink: str
    contentData: Dict
    mediaUrls: List[str]  # 后续识别视频或图片
    status: str
    tags: List[str]
    dateTime: datetime
    published: bool  # 是否发送到twitter等社媒
    likesCount: int
    commentsCount: int
    sharesCount: int
    visibility: str

    model_config = {
        "arbitrary_types_allowed": True
    }

    class Settings:
        name = "post"
        indexes = [
            [("agentId", 1)],
            [("tags", 1)]
        ]