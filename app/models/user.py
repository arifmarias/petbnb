# app/models/user.py
from sqlalchemy import Boolean, Column, String, DateTime, Text, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.message import chat_room_participants  # Import the association table
import uuid
from datetime import datetime
import enum

class UserType(str, enum.Enum):
    OWNER = "owner"
    CAREGIVER = "caregiver"
    ADMIN = "admin"

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    phone = Column(String(50))
    address = Column(Text)
    user_type = Column(Enum(UserType), nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    is_admin = Column(Boolean, default=False)
    verification_token = Column(String(255), nullable=True)
    reset_password_token = Column(String(255), nullable=True)
    profile_picture = Column(String(255), nullable=True)
    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Existing Relationships
    pets = relationship("Pet", back_populates="owner", cascade="all, delete-orphan")
    caregiver_profile = relationship("CaregiverProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    bookings_as_owner = relationship("Booking", foreign_keys="[Booking.owner_id]", back_populates="owner")
    reviews_given = relationship("Review", foreign_keys="[Review.reviewer_id]", back_populates="reviewer")
    
    # Messaging Relationships
    messages_sent = relationship("Message", back_populates="sender")
    message_reads = relationship("MessageReadStatus", back_populates="user")
    chat_rooms = relationship(
        "ChatRoom",
        secondary=chat_room_participants,
        back_populates="participants"
    )
    images = relationship(
    "Image",
    primaryjoin="and_(User.id==Image.entity_id, Image.entity_type=='user')",
    back_populates="user",
    foreign_keys="[Image.entity_id]"
    )

    def __repr__(self):
        return f"<User {self.email}>"