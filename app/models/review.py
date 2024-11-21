# app/models/review.py
from sqlalchemy import Column, ForeignKey, DateTime, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid
from datetime import datetime

class Review(Base):
    __tablename__ = "reviews"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    booking_id = Column(UUID(as_uuid=True), ForeignKey("bookings.id"), unique=True)
    caregiver_id = Column(UUID(as_uuid=True), ForeignKey("caregiver_profiles.id"))
    reviewer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    rating = Column(Integer)
    comment = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    booking = relationship("Booking", back_populates="review")
    caregiver = relationship("CaregiverProfile", back_populates="reviews")
    reviewer = relationship("User", back_populates="reviews_given")

    def __repr__(self):
        return f"<Review {self.id}>"