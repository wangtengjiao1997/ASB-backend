from app.entities.base import BaseDocument
from typing import Dict, Any, Tuple, List
from datetime import datetime
from pydantic import Field
from typing import Optional
class User(BaseDocument):
    auth0_id: str
    name: str
    phone: Optional[str] = Field(default="")
    email: str = ""
    email_verified: bool = False
    password: Optional[str] = Field(default=None)
    picture: Optional[str] = Field(default="")
    status: str = "active"
    bio: str = ""
    following_count: int = 0
    follower_count: int = 0
    fcm_token: Dict[str, Any] = {}
    last_login_date: Optional[datetime] = Field(default=None)
    class Settings:
        name = "user"
        indexes = [
            [("name", 1)],
            [("email", 1)],
            [("auth0_id", 1)],
            # 新增复合索引
            [("status", 1), ("created_at", -1)],  # 状态+创建时间
            [("email_verified", 1), ("status", 1)],  # 验证状态+用户状态
            [("last_login_date", -1)],  # 最后登录时间
            [("is_deleted", 1), ("status", 1)]  # 删除状态+用户状态
        ]