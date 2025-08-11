from typing import Optional, Dict, Any, Tuple
from pydantic import Field
from datetime import datetime
from app.entities.base import BaseDocument

class User(BaseDocument):

    wechat_openid: str = Field(default="")
    wechat_unionid: str = Field(default="")
    nickname: str = Field(default="")
    avatar_url: str = Field(default="")
    gender: int = Field(default=0)  # 0: 未知, 1: 男, 2: 女
    country: str = Field(default="")
    province: str = Field(default="")
    city: str = Field(default="")
    
    name: str = Field(default="")
    bio: str = Field(default="")
    status: str = Field(default="")
    
    fcm_token: Dict[str, Tuple[str, str]] = Field(default={})
    metadata: Dict[str, Any] = Field(default={})

    class Settings:
        name = "users"
        indexes = [
            [("wechat_openid", 1)],
            [("wechat_unionid", 1)],
            [("nickname", "text"), ("name", "text")]
        ]