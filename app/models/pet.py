# app/models/pet.py
from sqlalchemy import Column, String, Integer, Float, Text, ForeignKey, Boolean, Enum, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.image import Image  # Add this import
import uuid
from datetime import datetime
import enum

class PetType(str, enum.Enum):
    DOG = "dog"
    CAT = "cat"
    BIRD = "bird"
    FISH = "fish"
    OTHER = "other"

class Pet(Base):
    __tablename__ = "pets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name = Column(String(100), nullable=False)
    pet_type = Column(Enum(PetType), nullable=False)
    breed = Column(String(100))
    age = Column(Integer)
    size = Column(String(50))
    weight = Column(Float)
    gender = Column(String(20))
    is_neutered = Column(Boolean, default=False)
    medical_conditions = Column(Text)
    vaccination_status = Column(Text)
    special_requirements = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    owner = relationship("User", back_populates="pets")
    bookings = relationship("Booking", back_populates="pet")
    images = relationship(
        "Image",
        primaryjoin="and_(Pet.id==Image.entity_id, Image.entity_type=='pet')",
        cascade="all, delete-orphan",
        foreign_keys=[Image.entity_id],
        back_populates="pet"
    )

    def __repr__(self):
        return f"<Pet {self.name} ({self.pet_type})>"