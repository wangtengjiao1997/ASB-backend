from app.entities.base import BaseDocument
from typing import Dict, Any
from datetime import datetime

class User(BaseDocument):
    username: str
    phone: str
    email: str
    password: str
    avatar: str | None = None
    status: str = "active"
    bio: str = ""
    followingCount: int = 0
    lastLoginDate: datetime | None = None
    metadata: Dict[str, Any] | None = None

    class Settings:
        name = "user"
        indexes = [
            [("username", 1)],
            [("email", 1)]
        ]