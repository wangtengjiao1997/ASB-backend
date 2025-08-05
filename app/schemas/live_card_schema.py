from typing import List, Optional
from pydantic import BaseModel, Field, computed_field   
from datetime import datetime, UTC
from app.utils.cdn_mapper import map_cdn_url

#######################
# 基础模型定义
#######################

# LiveCard 过滤器
class LiveCardFilter(BaseModel):
    live_card_id: Optional[str] = Field(None, description="Live Card ID")
    agent_id: Optional[str] = Field(None, description="代理ID")
    topic_title: Optional[str] = Field(None, description="网站名称")

#######################
# LiveCard 模型
#######################
class LiveCardBase(BaseModel):
    topic_title:str
    topic_description:str
    topic_image_url:str
    topic_content_type:str = Field(default="timeline", description="网站内容类型")
    schema_config: dict = Field(default_factory=dict, description="Schema数据")
    data_config: dict = Field(default_factory=dict, description="数据")
    ai_config: dict = Field(default_factory=dict, description="AI数据")
    categories: List[str] = Field(default=[], description="分类")
    trending_score: int = Field(default=0, description="趋势得分")
    like_count:int = Field(default=0, description="点赞数量")
    share_count:int = Field(default=0, description="分享数量")
    view_count:int = Field(default=0, description="浏览数量")
    user_id:str = Field(default="", description="用户ID")
    @computed_field
    def cdn_url(self) -> str:
        """返回 CDN URL，自动包含 SIZE_PLACEHOLDER"""
        return map_cdn_url(self.topic_image_url)

class LiveCardCreate(BaseModel):
    topic_title: str = Field(..., description="网站标题")
    topic_description: str = Field(..., description="网站描述")
    topic_image_url: str = Field(..., description="网站图片URL")
    topic_content_type: str = Field(default="timeline", description="网站内容类型")
    schema_config: dict = Field(default_factory=dict, description="Schema数据")
    data_config: dict = Field(default_factory=dict, description="数据")
    ai_config: dict = Field(default_factory=dict, description="AI数据")
    categories: List[str] = Field(default=[], description="分类")
    user_id:str = Field(default="", description="用户ID")

class LiveCardUpdate(BaseModel):
    topic_title: Optional[str] = None
    topic_description: Optional[str] = None
    topic_image_url: Optional[str] = None
    topic_content_type: Optional[str] = None
    categories: Optional[List[str]] = None
    schema_config: Optional[dict] = None
    data_config: Optional[dict] = None
    ai_config: Optional[dict] = None
    like_count: Optional[int] = None
    share_count: Optional[int] = None
    view_count: Optional[int] = None


#######################
# livecard response 模型
#######################
class LiveCardResponse(BaseModel):
    id: str = Field(..., description="ID")
    topic_title: str = Field("", description="网站标题")
    topic_description: str = Field("", description="网站描述")
    topic_image_url: str = Field("", description="网站图片URL")
    topic_content_type: str = Field("", description="网站内容类型")
    schema_config: dict = Field(default_factory=dict, description="Schema数据")
    data_config: dict = Field(default_factory=dict, description="数据")
    ai_config: dict = Field(default_factory=dict, description="AI数据")
    categories: List[str] = Field(default=[], description="分类")
    trending_score: int = Field(default=0, description="趋势得分")
    like_count:int = Field(default=0, description="点赞数量")
    subscribe_count:int = Field(default=0, description="订阅数量")
    share_count:int = Field(default=0, description="分享数量")
    view_count:int = Field(default=0, description="浏览数量")
    user_id:str = Field(default="", description="用户ID")
    is_liked: bool = Field(default=False, description="是否点赞")
    is_subscribed: bool = Field(default=False, description="是否订阅")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC), description="创建时间")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC), description="更新时间")
    model_config = {"from_attributes": True}

    @classmethod
    def from_base(cls, base: LiveCardBase) -> "LiveCardResponse":
        return cls(
            **base.model_dump(),
            topic_image_url=base.cdn_url
        )


    
#######################
# 分页响应模型
#######################
# 增量更新参数
class LiveCardIncrementalParams(BaseModel):
    last_id: Optional[str] = Field(None, description="最后一条Live Card ID，用于增量获取")
    limit: int = Field(default=20, ge=1, le=99999, description="限制数量")
    direction: str = Field(default="before", description="获取方向: after(之后的数据) 或 before(之前的数据)")
    sort_by: str = Field(default="updated_at", description="排序字段")

# 增量响应模型
class LiveCardIncrementalResponse(BaseModel):
    items: List[LiveCardResponse]
    has_more: bool = Field(description="是否还有更多数据")
    last_id: Optional[str] = Field(None, description="本次返回的最后一条Live Card ID")
    last_timestamp: Optional[datetime] = Field(None, description="本次返回的最后一条时间戳")
    total: int = Field(default=0, description="总数量")