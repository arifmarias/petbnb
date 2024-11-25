# app/models/image.py
from sqlalchemy import Column, String, ForeignKey, DateTime, Integer, ForeignKeyConstraint
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
    order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        ForeignKeyConstraint(
            ['entity_id'],
            ['pets.id'],
            name='fk_pet_images',
            use_alter=True
        ),
        ForeignKeyConstraint(
            ['entity_id'],
            ['caregiver_profiles.id'],
            name='fk_caregiver_images',
            use_alter=True
        ),
    )

    # Relationships to Pet and CaregiverProfile
    pet = relationship(
        "Pet",
        foreign_keys=[entity_id],
        primaryjoin="and_(Image.entity_id==Pet.id, Image.entity_type=='pet')",
        back_populates="images"
    )
    
    caregiver = relationship(
        "CaregiverProfile",
        foreign_keys=[entity_id],
        primaryjoin="and_(Image.entity_id==CaregiverProfile.id, Image.entity_type=='caregiver')",
        back_populates="images"
    )
