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
    reviewer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    caregiver_id = Column(UUID(as_uuid=True), ForeignKey("caregiver_profiles.id"))
    rating = Column(Integer)  # 1-5 stars
    comment = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    booking = relationship("Booking", back_populates="review")
    reviewer = relationship("User", foreign_keys=[reviewer_id])
    caregiver = relationship("CaregiverProfile", back_populates="reviews")

    def __repr__(self):
        return f"<Review {self.id} Rating={self.rating}>"