from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List

#######################
# 基础模型定义
#######################

# 订阅过滤条件
class SubscribeFilter(BaseModel):
    user_id: Optional[str] = None
    target_id: Optional[str] = None
    target_type: Optional[str] = None

#######################
# Subscribe 模型
#######################

class SubscribeClick(BaseModel):
    is_subscribe: bool
    target_id: str
    target_type: str

class SubscribeCreate(BaseModel):
    user_id: str
    target_id: str
    target_type: str

class SubscribeUpdate(BaseModel):
    is_deleted: Optional[bool] = None
    deleted_at: Optional[datetime] = None

#######################
# Subscribe response 模型
#######################

class SubscribeResponse(BaseModel):
    id: str
    user_id: str
    target_id: str
    target_type: str
    is_deleted: bool
    created_at: datetime
    deleted_at: Optional[datetime] = None

#######################
# 分页响应模型
#######################

# 增量更新参数
class SubscribeIncrementalParams(BaseModel):
    last_id: Optional[str] = Field(None, description="最后一条订阅ID，用于增量获取")
    limit: int = Field(default=20, ge=1, le=99999, description="限制数量")
    direction: str = Field(default="before", description="获取方向: after(之后的数据) 或 before(之前的数据)")

# 增量响应模型
class SubscribeIncrementalResponse(BaseModel):
    items: List[SubscribeResponse]
    has_more: bool = Field(description="是否还有更多数据")
    last_id: Optional[str] = Field(None, description="本次返回的最后一条Live Card ID")
    last_timestamp: Optional[datetime] = Field(None, description="本次返回的最后一条时间戳")
    total: int = Field(default=0, description="总数量")