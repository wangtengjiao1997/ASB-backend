from pydantic import BaseModel
from typing import Optional, Any

class SystemConfigBase(BaseModel):
    key: str
    value: Any
    description: Optional[str] = None
    type: str = "string"
    is_public: bool = False

class SystemConfigCreate(BaseModel):
    key: str
    value: Any
    description: Optional[str] = None
    type: str = "string"
    is_public: bool = False

class SystemConfigUpdate(BaseModel):
    key: str
    value: Any
    description: Optional[str] 
    type: Optional[str] 
    is_public: Optional[bool]

class SystemConfigFilter(BaseModel):
    key: Optional[str] = None
    is_public: Optional[bool] = None
    type: Optional[str] = None


    