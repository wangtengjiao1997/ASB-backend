from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime

#######################
# 基础模型定义
#######################

# 报告过滤条件
class ReportFilter(BaseModel):
    post_id: Optional[str] = None
    agent_id: Optional[str] = None
    type: Optional[str] = None
    user_id: Optional[str] = None

#######################
# Report 模型
#######################

class ReportBase(BaseModel):
    type: str
    params: Dict[str, Any]
    description: Optional[str] = None
    contact: Optional[str] = None

class ReportCreate(BaseModel):
    type: str
    params: Dict[str, Any]
    description: Optional[str] = None
    contact: Optional[str] = None

class ReportUpdate(BaseModel):
    type: Optional[str] = None
    params: Optional[Dict[str, Any]] = None
    description: Optional[str] = None
    contact: Optional[str] = None

#######################
# Report response 模型
#######################

# 报告响应模型
class ReportResponse(BaseModel):
    id: str
    type: str
    params: Dict[str, Any]
    description: Optional[str] = None
    contact: Optional[str] = None
    created_at: datetime
    
    model_config = {"from_attributes": True}


#######################
# 分页响应模型
#######################

# 增量更新参数
class ReportIncrementalParams(BaseModel):
    last_id: Optional[str] = Field(None, description="最后一条报告ID，用于增量获取")
    limit: int = Field(default=20, ge=1, le=9999, description="限制数量")
    direction: str = Field(default="before", description="获取方向: after(之后的报告) 或 before(之前的报告)")

# 增量响应模型
class ReportIncrementalResponse(BaseModel):
    items: List[ReportResponse]
    has_more: bool = Field(description="是否还有更多报告")
    last_id: Optional[str] = Field(None, description="本次返回的最后一条报告ID")
    last_timestamp: Optional[datetime] = Field(None, description="本次返回的最后一条报告时间")
    total: int = Field(default=0, description="总报告数")