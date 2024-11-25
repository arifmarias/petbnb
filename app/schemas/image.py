from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from uuid import UUID

class ImageBase(BaseModel):
    url: str
    thumbnail_url: Optional[str] = None
    order: Optional[int] = 0

class ImageCreate(ImageBase):
    entity_type: str
    entity_id: UUID
    public_id: str

class ImageResponse(ImageBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True