from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

# ChatSnapshot 模型（用于嵌入）
class ChatSnapshotBase(BaseModel):
    snapshot_id: str = Field(..., description="快照ID")
    id: str = Field(..., description="聊天ID")
    sharing_url: str = Field(..., description="分享URL")
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow, description="创建时间")

class ChatStreamRequest(BaseModel):
    prompt: str = Field(..., description="用户提问")
    chat_id: str = Field(..., description="聊天ID")

class ChatStartRequest(BaseModel):
    live_card_id: str = Field(..., description="Live Card ID")
    chat_id: Optional[str] = Field(default="-1", description="聊天ID")

# 基础聊天模型
class ChatBase(BaseModel):
    participants: Dict[str, str] = Field(default_factory=dict, description="参与者ID列表")
    messages: List[str] = Field(default_factory=list, description="消息ID列表")
    shareable: bool = Field(default=False, description="是否可分享")
    snapshot: Optional[Dict[str, Any]] = Field(default=None, description="聊天快照")

# 创建聊天请求模型
class ChatCreate(ChatBase):
    pass

# 更新聊天请求模型
class ChatUpdate(BaseModel):
    participants: Optional[Dict[str, str]] = None
    messages: Optional[List[str]] = None
    shareable: Optional[bool] = None
    snapshot: Optional[Dict[str, Any]] = None

class ChatStartResponse(BaseModel):
    chat_id: str = Field(..., description="聊天ID")
    live_card_id: str = Field(..., description="Live Card ID")
    topic_title: str = Field(..., description="Live Card 标题")
    topic_description: Optional[str] = Field(default="", description="Live Card 描述")
    topic_image_url: Optional[str] = Field(default="", description="Live Card 图片URL")
    chat_type: str = Field(..., description="聊天类型")
    services: Optional[List[str]] = Field(default_factory=list, description="服务列表")

# 聊天响应模型
class ChatListItemResponse(BaseModel):
    chat_id: Optional[str] = Field(None, description="聊天ID")
    live_card_id: Optional[str] = Field(None, description="Live Card ID")
    topic_title: Optional[str] = Field(None, description="Live Card 标题")
    topic_description: Optional[str] = Field(None, description="Live Card 描述")
    topic_image_url: Optional[str] = Field(None, description="Live Card 图片URL")
    chat_title: Optional[str] = Field(None, description="聊天标题")
    chat_type: Optional[str] = Field(None, description="聊天类型")
    chat_last_id: Optional[str] = Field(None, description="最后一条消息ID")
    chat_last_message_summary: Optional[str] = Field(None, description="最后一条消息摘要")
    chat_last_message_created_at: Optional[datetime] = Field(None, description="最后一条消息创建时间")
    unread_message_count: Optional[int] = Field(None, description="未读消息数量")
    model_config = {"from_attributes": True}

# 聊天过滤器
class ChatFilter(BaseModel):
    id: Optional[str] = None
    participants: Optional[Dict[str, str]] = None
    shareable: Optional[bool] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

# 分页参数
class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=100, ge=1, le=100, description="每页大小")
    sort_by: str = Field(default="created_at", description="排序字段")
    sort_desc: bool = Field(default=True, description="是否降序")

# 分页响应模型
class ChatListPaginatedResponse(BaseModel):
    items: List[ChatListItemResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

# 增量更新参数
class ChatIncrementalParams(BaseModel):
    last_id: Optional[str] = Field(None, description="最后一条聊天ID，用于增量获取")
    limit: int = Field(default=20, ge=1, le=100, description="限制数量")
    direction: str = Field(default="before", description="获取方向: after(之后的聊天) 或 before(之前的聊天)")

# 增量响应模型
class ChatIncrementalResponse(BaseModel):
    items: List[ChatListItemResponse]
    has_more: bool = Field(description="是否还有更多聊天")
    last_id: Optional[str] = Field(None, description="本次返回的最后一条聊天ID")
    last_timestamp: Optional[datetime] = Field(None, description="本次返回的最后一条聊天时间")
    total: int = Field(default=0, description="总聊天数")
