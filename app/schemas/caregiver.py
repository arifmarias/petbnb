# app/schemas/caregiver.py
from pydantic import BaseModel, Field, constr
from typing import Optional, List
from datetime import datetime
from uuid import UUID

class CaregiverProfileBase(BaseModel):
    bio: Optional[str] = None
    years_of_experience: Optional[int] = Field(None, ge=0)
    services_offered: List[str] = []  # ['boarding', 'walking', 'daycare']
    accepted_pet_types: List[str] = []  # ['dog', 'cat', etc.]
    price_per_night: Optional[float] = Field(None, gt=0)
    price_per_walk: Optional[float] = Field(None, gt=0)
    price_per_day: Optional[float] = Field(None, gt=0)
    available_from: Optional[datetime] = None
    available_to: Optional[datetime] = None
    maximum_pets: int = Field(1, gt=0)
    home_type: Optional[str] = None
    has_fenced_yard: bool = False
    living_space_size: Optional[int] = Field(None, gt=0)
    emergency_transport: bool = False
    preferred_pet_size: List[str] = []  # ['small', 'medium', 'large']

class CaregiverProfileCreate(CaregiverProfileBase):
    pass

class CaregiverProfileUpdate(CaregiverProfileBase):
    pass

class CaregiverProfile(CaregiverProfileBase):
    id: UUID
    user_id: UUID
    rating: float = 0.0
    total_reviews: int = 0
    is_available: bool = True
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class CaregiverPublicProfile(CaregiverProfileBase):
    id: UUID
    rating: float
    total_reviews: int
    is_available: bool
    user_full_name: str
    user_profile_picture: Optional[str]

    class Config:
        from_attributes = True