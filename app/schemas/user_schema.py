from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from beanie import PydanticObjectId
# 用户基础模型
class UserBase(BaseModel):
    username: str
    email: str
    phone: str
    avatar: Optional[str] = None
    status: Optional[str] = "active"
    bio: Optional[str] = ""
    password: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

# 更新用户请求模型
class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    password: Optional[str] = None
    avatar: Optional[str] = None
    status: Optional[str] = None
    bio: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
# 用户创建请求模型
class UserCreate(UserBase):
    pass

# 用户过滤条件
class UserFilter(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    status: Optional[str] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    updated_after: Optional[datetime] = None
    updated_before: Optional[datetime] = None

# 分页请求模型
class PaginationParams(BaseModel):
    page: int = 1
    page_size: int = 10
    sort_by: Optional[str] = "updated_at"
    sort_desc: bool = True

# 用户基础模型
class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    phone: str
    avatar: Optional[str] = None
    status: Optional[str] = "active"
    bio: Optional[str] = ""
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

# 分页响应模型
class PaginatedResponse(BaseModel):
    items: List[UserResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
