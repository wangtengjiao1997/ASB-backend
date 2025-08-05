from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.schemas.live_card_schema import LiveCardResponse

#######################
# 基础模型定义
#######################

# 点赞过滤条件
class LikeFilter(BaseModel):
    user_id: Optional[str] = None
    target_id: Optional[str] = None
    target_type: Optional[str] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None

#######################
# Like 模型
#######################

# 点赞基础模型
class LikeBase(BaseModel):
    user_id: str
    target_id: str
    target_type: str  # 目标类型: "post", "comment", "agent" 等

class LikeClick(BaseModel):
    is_like: bool
    target_id: str
    target_type: str

# 创建点赞请求模型
class LikeCreate(BaseModel):
    user_id: str
    target_id: str
    target_type: str

# 更新点赞请求模型 (通常不需要更新点赞，但保留以保持API一致性)
class LikeUpdate(BaseModel):
    is_deleted: bool
    deleted_at: Optional[datetime] = None

#######################
# Like response 模型
#######################

# 点赞响应模型
class LikeResponse(BaseModel):
    id: str
    user_id: str
    target_id: str
    target_type: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = {"from_attributes": True}

class LikedLiveCardsResponse(BaseModel):
    live_card: LiveCardResponse
    like : LikeResponse

#######################
# 分页响应模型
#######################

# 增量更新参数
class LikeIncrementalParams(BaseModel):
    last_id: Optional[str] = Field(None, description="最后一条点赞ID，用于增量获取")
    limit: int = Field(default=20, ge=1, le=9999, description="限制数量")
    direction: str = Field(default="before", description="获取方向: after(之后的点赞) 或 before(之前的点赞)")

# 增量响应模型
class LikeIncrementalResponse(BaseModel):
    items: List[LikedLiveCardsResponse]
    has_more: bool = Field(description="是否还有更多点赞")
    last_id: Optional[str] = Field(None, description="本次返回的最后一条点赞ID")
    last_timestamp: Optional[datetime] = Field(None, description="本次返回的最后一条点赞时间")
    total: int = Field(default=0, description="总点赞数")