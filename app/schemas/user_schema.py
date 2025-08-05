from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from beanie import PydanticObjectId
#######################
# 基础模型定义
#######################

# 用户过滤条件
class UserFilter(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    status: Optional[str] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    updated_after: Optional[datetime] = None
    updated_before: Optional[datetime] = None

#######################
# User 模型
#######################

# 用户基础模型
class UserBase(BaseModel):
    id: Optional[str] = None
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    picture: str = Field(default="")
    status: Optional[str] = "active"
    bio: Optional[str] = ""
    password: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

class AuthUserInfo(BaseModel):
    auth0_id: str
    email: str
    name: str
    picture: str
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

# 用户创建请求模型
class UserCreate(UserBase):
    auth0_id: str
    pass

# 更新用户请求模型
class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    picture: Optional[str] = None
    status: Optional[str] = None
    bio: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    fcm_token: Optional[Dict[str, Tuple[str, str]]] = None

# 用户登录请求模型
class UserLogin(BaseModel):
    email: str
    password: str

#######################
# User response 模型
#######################

# 用户基础模型
class UserResponse(BaseModel):
    id: str
    agent_id: Optional[str] = None
    name: str
    email: str
    phone: Optional[str] = None
    picture: str = Field(default="")
    status: Optional[str] = "active"
    fcm_token: Optional[Dict[str, Tuple[str, str]]] = None
    bio: Optional[str] = ""
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

class UserProfileResponse(BaseModel):
    id: str
    name: str
    picture: str = Field(default="")
    bio: Optional[str] = ""
    status: Optional[str] = "active"
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = {"from_attributes": True}

#######################
# 分页响应模型
#######################

# 增量更新参数
class UserIncrementalParams(BaseModel):
    last_id: Optional[str] = Field(None, description="最后一条用户ID，用于增量获取")
    limit: int = Field(default=20, ge=1, le=99999, description="限制数量")
    direction: str = Field(default="before", description="获取方向: after(之后的数据) 或 before(之前的数据)")

# 增量响应模型
class UserIncrementalResponse(BaseModel):
    items: List[UserResponse]
    has_more: bool = Field(description="是否还有更多数据")
    last_id: Optional[str] = Field(None, description="本次返回的最后一条用户ID")
    last_timestamp: Optional[datetime] = Field(None, description="本次返回的最后一条时间戳")
    total: int = Field(default=0, description="总数量")