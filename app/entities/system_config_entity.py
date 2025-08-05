from app.entities.base import BaseDocument
from typing import Dict, Any, Optional
from datetime import datetime
from pydantic import Field
class SystemConfig(BaseDocument):
    key: str  # 配置键
    value: Any  # 配置值
    description: Optional[str] = Field(default="", description="配置描述")
    type: str = "string"  # 值类型：string, number, boolean, json, array
    is_public: bool = False  # 是否公开配置
    updated_by: Optional[str] = Field(default="", description="最后更新人")
    version: int = 1  # 配置版本号

    class Settings:
        name = "system_config"
        indexes = [
            [("key", 1)],  # 键的唯一索引
            [("is_public", 1)],  # 公开配置的索引
            [("updated_at", -1)]  # 更新时间索引
        ]

   