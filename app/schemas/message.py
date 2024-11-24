# app/schemas/message.py
from pydantic import BaseModel, UUID4
from datetime import datetime
from typing import Optional, List

class MessageBase(BaseModel):
    content: str

class MessageCreate(MessageBase):
    chat_room_id: UUID4

class Message(MessageBase):
    id: UUID4
    sender_id: UUID4
    chat_room_id: UUID4
    is_read: bool
    is_system_message: bool = False
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class ChatRoomBase(BaseModel):
    booking_id: Optional[UUID4] = None

class ChatRoomCreate(ChatRoomBase):
    pass

class ChatRoom(ChatRoomBase):
    id: UUID4
    created_at: datetime
    updated_at: datetime
    messages: List[Message] = []
    
    class Config:
        from_attributes = True

class MessageRead(BaseModel):
    message_id: UUID4
    read_at: datetime

    class Config:
        from_attributes = True