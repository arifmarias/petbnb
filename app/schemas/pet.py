# app/schemas/pet.py
from pydantic import BaseModel, constr
from typing import Optional
from datetime import datetime
from uuid import UUID
from enum import Enum

class PetType(str, Enum):
    DOG = "dog"
    CAT = "cat"
    BIRD = "bird"
    FISH = "fish"
    OTHER = "other"

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

class Pet(PetBase):
    id: UUID
    owner_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True