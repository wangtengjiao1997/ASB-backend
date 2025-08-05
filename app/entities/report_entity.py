
from app.entities.base import BaseDocument
from typing import Dict, Any
from pydantic import Field
class Report(BaseDocument):

    type: str 
    params: Dict[str, Any]
    description: str 
    contact: str = Field(default="", description="联系人")

    class Settings:
        name = "report"
        indexes = [
            [("created_at", -1)]  # 按创建时间降序索引
        ]