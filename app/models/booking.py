# app/models/booking.py
from sqlalchemy import Column, ForeignKey, DateTime, String, Float, Text, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid
from datetime import datetime
import enum

class BookingStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    REJECTED = "rejected"

class ServiceType(str, enum.Enum):
    BOARDING = "boarding"
    DAYCARE = "daycare"
    WALKING = "walking"

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

    # Relationships
    pet = relationship("Pet", back_populates="bookings")
    owner = relationship("User", foreign_keys=[owner_id], back_populates="bookings_as_owner")
    caregiver = relationship("CaregiverProfile", back_populates="bookings")
    review = relationship("Review", back_populates="booking", uselist=False)

    def __repr__(self):
        return f"<Booking {self.id}>"