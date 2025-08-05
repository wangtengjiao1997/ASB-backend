from datetime import datetime
from typing import Any, List, Dict
from app.entities.base import BaseDocument
from pydantic import Field

class LiveCard(BaseDocument):
    topic_title:str
    topic_description:str
    topic_image_url:str
    topic_content_type:str = Field(default="timeline", description="网站内容类型")
    categories: List[str] = Field(default=[], description="分类")
    trending_score: int = Field(default=0, description="趋势得分")
    ############# ai 配置
    schema_config: dict = Field(default_factory=dict, description="Schema数据")
    data_config: dict = Field(default_factory=dict, description="数据")
    ai_config: dict = Field(default_factory=dict, description="AI数据")
    ############# 用户互动
    like_count:int = Field(default=0, description="点赞数量")
    # comment_count:int = Field(default=0, description="评论数量")
    subscribe_count:int = Field(default=0, description="订阅数量")
    share_count:int = Field(default=0, description="分享数量")
    view_count:int = Field(default=0, description="浏览数量")
    user_id:str = Field(default="", description="用户ID")

    class Settings:
        name = "live_card"
        indexes = [
            [("user_id", 1)],
            [("topic_title", 1)],
            [("topic_content_type", 1)]
        ]
