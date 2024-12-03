# app/schemas/pet.py
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from enum import Enum
from .user import UserInDBBase  # Changed from UserBasic to UserInDBBase

class PetType(str, Enum):
    DOG = "dog"
    CAT = "cat"
    BIRD = "bird"
    FISH = "fish"
    OTHER = "other"

class PetImageBase(BaseModel):
    url: str
    order: int = 0

class PetBase(BaseModel):
    name: str
    pet_type: PetType
    breed: Optional[str] = None
    age: Optional[int] = None
    size: Optional[str] = None
    weight: Optional[float] = None
    gender: Optional[str] = None
    is_neutered: Optional[bool] = False
    medical_conditions: Optional[str] = None
    vaccination_status: Optional[str] = None
    special_requirements: Optional[str] = None

class PetCreate(PetBase):
    pass

class PetUpdate(PetBase):
    name: Optional[str] = None
    pet_type: Optional[PetType] = None

class PetImage(PetImageBase):
    id: UUID
    thumbnail_url: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class Pet(PetBase):
    id: UUID
    owner_id: UUID
    created_at: datetime
    updated_at: datetime
    images: List[PetImage] = []
    image_urls: List[str] = []
    primary_image: Optional[str] = None

    class Config:
        from_attributes = True

class PetWithOwner(Pet):
    owner: UserInDBBase  # Changed from UserBasic to UserInDBBase

    class Config:
        from_attributes = True

class PetBasic(BaseModel):
    id: UUID
    name: str
    pet_type: PetType
    primary_image: Optional[str] = None

    class Config:
        from_attributes = True