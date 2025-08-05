from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

#######################
# 基础模型定义
#######################

# 关注过滤条件
class FollowFilter(BaseModel):
    user_id: Optional[str] = None
    target_id: Optional[str] = None
    target_type: Optional[str] = None

#######################
# Follow 模型
#######################

# 关注基础模型
class FollowBase(BaseModel):
    user_id: str
    target_id: str
    target_type: str = "user"

# 创建关注请求模型
class FollowCreate(BaseModel):
    user_id: str
    target_id: str
    target_type: str = "user"

class FollowClick(BaseModel):
    is_follow: bool
    target_id: str
    target_type: str = "user"

# 更新关注请求模型  
class FollowUpdate(BaseModel):
    is_deleted: bool
    deleted_at: Optional[datetime] = None

#######################
# Follow response 模型
#######################

# 关注响应模型
class FollowResponse(BaseModel):
    id: str
    user_id: str
    target_id: str
    target_type: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = {"from_attributes": True}

#######################
# 分页响应模型
#######################

# 分页请求模型
class PaginationParams(BaseModel):
    page: int = 1
    page_size: int = 10
    sort_by: Optional[str] = "created_at"
    sort_desc: bool = True

# 分页响应模型
class PaginatedResponse(BaseModel):
    items: List[FollowResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

# 增量更新参数
class FollowIncrementalParams(BaseModel):
    last_id: Optional[str] = Field(None, description="最后一条关注ID，用于增量获取")
    limit: int = Field(default=20, ge=1, le=9999, description="限制数量")
    direction: str = Field(default="before", description="获取方向: after(之后的关注) 或 before(之前的关注)")

# 增量响应模型
class FollowIncrementalResponse(BaseModel):
    items: List[FollowResponse]
    has_more: bool = Field(description="是否还有更多关注")
    last_id: Optional[str] = Field(None, description="本次返回的最后一条关注ID")
    last_timestamp: Optional[datetime] = Field(None, description="本次返回的最后一条关注时间")
    total: int = Field(default=0, description="总关注数")