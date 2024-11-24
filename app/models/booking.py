# app/models/booking.py
from sqlalchemy import Column, ForeignKey, DateTime, String, Float, Text, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid
from datetime import datetime
import enum

class BookingStatus(str, enum.Enum):
    PENDING = "PENDING"
    PAYMENT_REQUIRED = "PAYMENT_REQUIRED"
    CONFIRMED = "CONFIRMED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"

class ServiceType(str, enum.Enum):
    BOARDING = "BOARDING"
    DAYCARE = "DAYCARE"
    WALKING = "WALKING"

class Booking(Base):
    __tablename__ = "bookings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pet_id = Column(UUID(as_uuid=True), ForeignKey("pets.id"), nullable=False)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    caregiver_id = Column(UUID(as_uuid=True), ForeignKey("caregiver_profiles.id"), nullable=False)
    service_type = Column(Enum(ServiceType), nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    status = Column(Enum(BookingStatus), default=BookingStatus.PENDING)
    total_price = Column(Float, nullable=False)
    special_instructions = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Existing Relationships
    pet = relationship("Pet", back_populates="bookings")
    owner = relationship("User", foreign_keys=[owner_id])
    caregiver = relationship("CaregiverProfile", back_populates="bookings")
    review = relationship("Review", back_populates="booking", uselist=False)
    payments = relationship("Payment", back_populates="booking", lazy="dynamic")
    
    # New Relationship for Chat
    chat_room = relationship("ChatRoom", back_populates="booking", uselist=False)

    @property
    def pet_name(self) -> str:
        return self.pet.name if self.pet else ""

    @property
    def owner_name(self) -> str:
        return self.owner.full_name if self.owner else ""

    @property
    def caregiver_name(self) -> str:
        return self.caregiver.user.full_name if self.caregiver and self.caregiver.user else ""

    def __repr__(self):
        return f"<Booking {self.id}>"