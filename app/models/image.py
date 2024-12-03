# app/models/image.py
from sqlalchemy import (
    Column, String, DateTime, Integer, 
    CheckConstraint, ForeignKey
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid
from datetime import datetime

class Image(Base):
    __tablename__ = "images"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    public_id = Column(String, nullable=False)
    url = Column(String, nullable=False)
    thumbnail_url = Column(String)
    entity_type = Column(String, nullable=False)
    entity_id = Column(UUID(as_uuid=True), nullable=False)
    order = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        CheckConstraint(
            entity_type.in_(['user', 'pet', 'caregiver']),
            name='check_valid_entity_type'
        ),
    )

    # Relationships without foreign key constraints
    user = relationship(
        "User",
        primaryjoin="and_(Image.entity_id==User.id, Image.entity_type=='user')",
        back_populates="images",
        foreign_keys=[entity_id]
    )

    pet = relationship(
        "Pet",
        primaryjoin="and_(Image.entity_id==Pet.id, Image.entity_type=='pet')",
        back_populates="images",
        foreign_keys=[entity_id]
    )

    caregiver = relationship(
        "CaregiverProfile",
        primaryjoin="and_(Image.entity_id==CaregiverProfile.id, Image.entity_type=='caregiver')",
        back_populates="images",
        foreign_keys=[entity_id]
    )

    @property
    def entity(self):
        if self.entity_type == 'user':
            return self.user
        elif self.entity_type == 'pet':
            return self.pet
        elif self.entity_type == 'caregiver':
            return self.caregiver
        return None