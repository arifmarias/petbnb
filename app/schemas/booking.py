# app/schemas/booking.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID
from enum import Enum

class BookingStatus(str, Enum):
    PENDING = "PENDING"
    PAYMENT_REQUIRED = "PAYMENT_REQUIRED"
    CONFIRMED = "CONFIRMED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"

class ServiceType(str, Enum):
    BOARDING = "BOARDING"
    DAYCARE = "DAYCARE"
    WALKING = "WALKING"

class BookingBase(BaseModel):
    pet_id: UUID
    service_type: ServiceType
    start_date: datetime
    end_date: datetime
    special_instructions: Optional[str] = None

class BookingCreate(BookingBase):
    caregiver_id: UUID

class BookingUpdate(BaseModel):
    special_instructions: Optional[str] = None
    status: Optional[BookingStatus] = None

class Booking(BookingBase):
    id: UUID
    owner_id: UUID
    caregiver_id: UUID
    status: BookingStatus
    total_price: float
    created_at: datetime
    updated_at: datetime
    pet_name: str
    owner_name: str
    caregiver_name: str

    class Config:
        from_attributes = True

class BookingResponse(BaseModel):
    id: UUID
    pet_id: UUID
    owner_id: UUID
    caregiver_id: UUID
    service_type: ServiceType
    start_date: datetime
    end_date: datetime
    status: BookingStatus
    total_price: float
    special_instructions: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    pet_name: str
    owner_name: str
    caregiver_name: str
    can_cancel: bool
    can_review: bool

    class Config:
        from_attributes = True