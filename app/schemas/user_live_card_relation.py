from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class UserLiveCardRelationCreate(BaseModel):
    """创建用户直播卡片关系"""
    user_id: str = Field(..., description="用户ID")
    live_card_id: str = Field(..., description="直播卡片ID")
    last_read_at: Optional[datetime] = Field(default=None, description="最近阅读时间")

class UserLiveCardRelationUpdate(BaseModel):
    """更新用户直播卡片关系"""
    user_id: str = Field(..., description="用户ID")
    live_card_id: str = Field(..., description="直播卡片ID")
    last_read_at: Optional[datetime] = Field(None, description="最近阅读时间")

class UserLiveCardRelationResponse(BaseModel):
    """用户直播卡片关系响应"""
    id: str
    user_id: str
    live_card_id: str
    last_read_at: Optional[datetime] = None
    
    model_config = {"from_attributes": True}