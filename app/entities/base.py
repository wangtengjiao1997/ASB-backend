from beanie import Document
from datetime import datetime, UTC
from typing import Optional, Dict, Any
from pydantic import Field, ConfigDict
import uuid

class BaseDocument(Document):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    is_deleted: bool = Field(default=False)
    deleted_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Settings:
        use_state_management = True

    async def save(self, *args, **kwargs):
        self.updated_at = datetime.now(UTC)
        return await super().save(*args, **kwargs)

    async def soft_delete(self):
        self.is_deleted = True
        self.deleted_at = datetime.now(UTC)
        await self.save() 