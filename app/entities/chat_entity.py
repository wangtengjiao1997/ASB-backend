from typing import List, Dict, Any, Optional
from pydantic import Field
from datetime import datetime
from app.entities.base import BaseDocument

class Chat(BaseDocument):
    participants: Dict[str, str] = Field(default_factory=dict, description="参与者ID列表")
    messages: List[str] = Field(default_factory=list, description="消息ID列表")
    shareable: bool = Field(default=False, description="是否可分享")
    snapshot: Optional[Dict[str, Any]] = Field(default=None, description="聊天快照")
    chat_type: str = Field(default="agent", description="聊天类型")
    class Settings:
        name = "chat"
        indexes = [
            [("_id", 1)],
            [("participants", 1)],
            [("created_at", -1)]
        ]