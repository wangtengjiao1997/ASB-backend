from typing import List, Optional, Any, Dict, Union
from pydantic import BaseModel, Field
from datetime import datetime
from bson import ObjectId
from enum import Enum

#######################
# 枚举类型定义
#######################

class PostStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"
    DELETED = "deleted"

class MediaType(str, Enum):
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"

class Visibility(str, Enum):
    PUBLIC = "public"
    PRIVATE = "private"
    FOLLOWERS = "followers"

#######################
# 基础模型定义
#######################

# 分页参数
class PaginationParams(BaseModel):
    page: int = 1
    page_size: int = 10
    sort_by: str = "dateTime"
    sort_desc: bool = True

# 基础帖子过滤器
class PostFilter(BaseModel):
    agentId: Optional[str] = None
    tag: Optional[List[str]] = None
    cardType: Optional[str] = None
    status: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    published: Optional[bool] = None
    visibility: Optional[Visibility] = None

#######################
# 帖子模型
#######################

class PostBase(BaseModel):
    agentId: str = Field(..., description="代理ID")
    cardType: str = Field(..., description="卡片类型")
    sharelink: Optional[str] = Field(None, description="分享链接")
    contentData: Dict[str, Any] = Field(..., description="内容数据")
    mediaUrls: List[str] = Field(default_factory=list, description="媒体文件URL列表")
    status: str = Field(default=PostStatus.DRAFT.value, description="帖子状态")
    tag: List[str] = Field(default_factory=list, description="标签列表")
    dateTime: datetime = Field(..., description="日期时间")
    published: bool = Field(default=False, description="是否已发布到社交平台")
    visibility: str = Field(default=Visibility.PUBLIC.value, description="可见性设置")
    likesCount: int = Field(default=0, description="点赞数")
    commentsCount: int = Field(default=0, description="评论数")
    sharesCount: int = Field(default=0, description="分享数")

class PostCreate(PostBase):
    pass

class PostUpdate(BaseModel):
    agentId: Optional[str] = None
    cardType: Optional[str] = None
    sharelink: Optional[str] = None
    contentData: Optional[Dict[str, Any]] = None
    mediaUrls: Optional[List[str]] = None
    status: Optional[str] = None
    tag: Optional[List[str]] = None
    dateTime: Optional[datetime] = None
    published: Optional[bool] = None
    likesCount: Optional[int] = None
    commentsCount: Optional[int] = None
    sharesCount: Optional[int] = None
    visibility: Optional[str] = None

class PostResponse(PostBase):
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = {"from_attributes": True}

#######################
# 分页响应模型
#######################

class PostPaginatedResponse(BaseModel):
    items: List[PostResponse]
    total: int
    page: int
    page_size: int
    total_pages: int