# app/models/message.py

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Boolean, Table
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import uuid

# Association table for chat room participants
chat_room_participants = Table(
    'chat_room_participants',
    Base.metadata,
    Column('chat_room_id', UUID(as_uuid=True), ForeignKey('chat_rooms.id', ondelete='CASCADE'), primary_key=True),
    Column('user_id', UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
    Column('joined_at', DateTime, server_default=func.current_timestamp(), nullable=False),
    Column('last_read_at', DateTime, nullable=True)
)

class ChatRoom(Base):
    __tablename__ = "chat_rooms"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    booking_id = Column(UUID(as_uuid=True), ForeignKey("bookings.id", ondelete='CASCADE'), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.current_timestamp())
    updated_at = Column(DateTime(timezone=True), server_default=func.current_timestamp(), onupdate=func.current_timestamp())
    
    # Relationships
    messages = relationship("Message", back_populates="chat_room", cascade="all, delete-orphan")
    booking = relationship("Booking", back_populates="chat_room")
    participants = relationship(
        "User",
        secondary=chat_room_participants,
        back_populates="chat_rooms"
    )

class Message(Base):
    __tablename__ = "messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chat_room_id = Column(UUID(as_uuid=True), ForeignKey("chat_rooms.id", ondelete='CASCADE'))
    sender_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete='CASCADE'))
    content = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    is_system_message = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.current_timestamp())
    updated_at = Column(DateTime(timezone=True), server_default=func.current_timestamp(), onupdate=func.current_timestamp())
    
    # Relationships
    chat_room = relationship("ChatRoom", back_populates="messages")
    sender = relationship("User", back_populates="messages_sent")
    read_by = relationship("MessageReadStatus", back_populates="message", cascade="all, delete-orphan")

class MessageReadStatus(Base):
    __tablename__ = "message_read_status"

    message_id = Column(UUID(as_uuid=True), ForeignKey("messages.id", ondelete='CASCADE'), primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete='CASCADE'), primary_key=True)
    read_at = Column(DateTime, server_default=func.current_timestamp(), nullable=False)

    # Relationships
    message = relationship("Message", back_populates="read_by")
    user = relationship("User", back_populates="message_reads")