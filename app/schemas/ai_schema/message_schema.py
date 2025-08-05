from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum
from uuid import uuid4
class RoleEnum(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"

class MimeTypeEnum(str, Enum):
    TEXT = "text/plain"
    IMAGE = "image/jpeg"
    VIDEO = "video/mp4"
    AUDIO = "audio/mp3"

# Media 模型（用于嵌入）
class MediaBase(BaseModel):
    mime_type: MimeTypeEnum = Field(..., description="媒体类型")
    text: Optional[str] = Field(None, description="文本内容")
    url: Optional[str] = Field(None, description="URL地址")

# 基础消息模型
class MessageBase(BaseModel):
    chat_id: str = Field(..., description="聊天ID")
    sender_id: str = Field(..., description="发送者ID") 
    role: RoleEnum = Field(..., description="角色")
    text: Optional[str] = Field(None, description="文本内容")
    contents: List[Dict[str, Any]] = Field(default_factory=list, description="媒体内容列表")

# 创建消息请求模型
class MessageCreate(MessageBase):
    id: Optional[str] = Field(default=str(uuid4()), description="消息ID")

# 更新消息请求模型
class MessageUpdate(BaseModel):
    chat_id: Optional[str] = None
    sender_id: Optional[str] = None
    role: Optional[RoleEnum] = None
    text: Optional[str] = None
    contents: Optional[List[Dict[str, Any]]] = None

# 消息响应模型
class MessageResponse(BaseModel):
    message_id: Optional[str] = Field(default="", description="消息ID")
    message_type: Optional[str] = Field(default="", description="消息类型")
    message_status: Optional[str] = Field(default="", description="消息状态")
    role: Optional[str] = Field(default="", description="角色")
    message_content: Optional[str] = Field(default="", description="消息内容")
    message_images: Optional[List[str]] = Field(default_factory=list, description="消息图片")
    delta: Optional[str] = Field(default="", description="增量消息")
    created_at: Optional[datetime] = Field(..., description="创建时间")

# 消息过滤器
class MessageFilter(BaseModel):
    chat_id: Optional[str] = None
    sender_id: Optional[str] = None
    role: Optional[RoleEnum] = None

# 增量更新参数
class IncrementalParams(BaseModel):
    last_id: Optional[str] = Field(None, description="最后一条消息ID，用于增量获取")
    limit: int = Field(default=20, ge=1, le=100, description="限制数量")
    direction: str = Field(default="before", description="获取方向: after(之后的消息) 或 before(之前的消息)")

# 增量响应模型
class MessageIncrementalResponse(BaseModel):
    items: List[MessageResponse]
    has_more: bool = Field(description="是否还有更多消息")
    last_id: Optional[str] = Field(default="", description="本次返回的最后一条消息ID")
    last_timestamp: Optional[datetime] = Field(default="", description="本次返回的最后一条消息时间")
