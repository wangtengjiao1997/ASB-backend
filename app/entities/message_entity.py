from typing import List, Dict, Any, Optional
from pydantic import Field
from datetime import datetime
from enum import Enum
from app.entities.base import BaseDocument

class RoleEnum(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"

class Message(BaseDocument):
    chat_id: str = Field(..., description="聊天ID")
    sender_id: str = Field(..., description="发送者ID")
    role: RoleEnum = Field(..., description="角色")
    type: str = Field(default="text", description="消息类型")
    text: Optional[str] = Field(default="", description="文本内容")
    contents: List[Dict[str, Any]] = Field(default_factory=list, description="媒体内容列表")

    class Settings:
        name = "messages"
        indexes = [
            [("chat_id", 1)],
            [("sender_id", 1)],
            [("_id", 1)],
            [("created_at", -1)]
        ]