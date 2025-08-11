from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime

#######################
# 基础模型定义
#######################

# 用户过滤条件
class UserFilter(BaseModel):
    nickname: Optional[str] = None
    gender: Optional[int] = None
    country: Optional[str] = None
    province: Optional[str] = None
    city: Optional[str] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    updated_after: Optional[datetime] = None
    updated_before: Optional[datetime] = None

#######################
# 微信相关模型
#######################

class WechatCode(BaseModel):
    """微信登录请求模型"""
    code: str

class WechatUserInfo(BaseModel):
    """微信用户信息模型"""
    encrypted_data: str
    iv: str
    signature: str
    raw_data: str

class WechatSession(BaseModel):
    """微信会话信息"""
    openid: str
    session_key: str
    unionid: Optional[str] = None

#######################
# User 模型
#######################

# 用户基础模型
class UserBase(BaseModel):
    id: Optional[str] = None
    nickname: Optional[str] = None
    avatar_url: Optional[str] = None
    gender: Optional[int] = None  # 0: 未知, 1: 男, 2: 女
    country: Optional[str] = None
    province: Optional[str] = None
    city: Optional[str] = None
    language: Optional[str] = None
    status: Optional[str] = "active"
    bio: Optional[str] = ""
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

# 用户创建请求模型
class UserCreate(BaseModel):
    nickname: Optional[str] = None
    avatar_url: Optional[str] = None
    gender: Optional[int] = None
    wechat_openid: str
    wechat_unionid: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    created_at: Optional[datetime] = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = Field(default_factory=datetime.now)

# 更新用户请求模型
class UserUpdate(BaseModel):
    nickname: Optional[str] = None
    avatar_url: Optional[str] = None
    gender: Optional[int] = None
    country: Optional[str] = None
    province: Optional[str] = None
    city: Optional[str] = None
    language: Optional[str] = None
    status: Optional[str] = None
    bio: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    fcm_token: Optional[Dict[str, Tuple[str, str]]] = None
    updated_at: Optional[datetime] = Field(default_factory=datetime.now)

#######################
# User response 模型
#######################

# 用户响应基础模型
class UserResponse(BaseModel):
    id: str
    wechat_openid: str
    wechat_unionid: Optional[str] = None
    nickname: Optional[str] = None
    avatar_url: Optional[str] = None
    gender: Optional[int] = None
    country: Optional[str] = None
    province: Optional[str] = None
    city: Optional[str] = None
    language: Optional[str] = None
    status: Optional[str] = "active"
    bio: Optional[str] = ""
    fcm_token: Optional[Dict[str, Tuple[str, str]]] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

class UserProfileResponse(BaseModel):
    id: str
    nickname: Optional[str] = None
    avatar_url: Optional[str] = None
    gender: Optional[int] = None
    country: Optional[str] = None
    province: Optional[str] = None
    city: Optional[str] = None
    bio: Optional[str] = ""
    status: Optional[str] = "active"
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = {"from_attributes": True}

# 微信登录响应模型
class WechatLoginResponse(BaseModel):
    session_info: WechatSession
    token: str
    user: UserResponse

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