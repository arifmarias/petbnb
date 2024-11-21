# app/models/caregiver.py
from sqlalchemy import Column, String, Integer, Float, Text, ForeignKey, Boolean, DateTime, ARRAY
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid
from datetime import datetime

class CaregiverProfile(Base):
    __tablename__ = "caregiver_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True)
    bio = Column(Text)
    years_of_experience = Column(Integer)
    services_offered = Column(ARRAY(String))
    accepted_pet_types = Column(ARRAY(String))
    price_per_night = Column(Float)
    price_per_walk = Column(Float)
    price_per_day = Column(Float)
    available_from = Column(DateTime)
    available_to = Column(DateTime)
    maximum_pets = Column(Integer, default=1)
    home_type = Column(String(50))
    has_fenced_yard = Column(Boolean, default=False)
    living_space_size = Column(Integer)
    emergency_transport = Column(Boolean, default=False)
    is_available = Column(Boolean, default=True)
    preferred_pet_size = Column(ARRAY(String))
    rating = Column(Float, default=0.0)
    total_reviews = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="caregiver_profile")
    bookings = relationship("Booking", back_populates="caregiver")
    reviews = relationship("Review", back_populates="caregiver")

    def __repr__(self):
        return f"<CaregiverProfile {self.user_id}>"