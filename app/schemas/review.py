# app/schemas/review.py
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime
from uuid import UUID

class ReviewBase(BaseModel):
    rating: int = Field(
        ..., 
        ge=1, 
        le=5, 
        description="Rating must be between 1 and 5"
    )
    comment: Optional[str] = Field(
        None,
        max_length=1000,
        description="Optional review comment"
    )

    @field_validator('rating')
    @classmethod
    def validate_rating(cls, v: int) -> int:
        if not 1 <= v <= 5:
            raise ValueError('Rating must be between 1 and 5')
        return v

class ReviewCreate(ReviewBase):
    booking_id: UUID = Field(
        ...,
        description="ID of the booking being reviewed"
    )

class ReviewUpdate(ReviewBase):
    pass

class Review(ReviewBase):
    id: UUID
    booking_id: UUID
    reviewer_id: UUID
    caregiver_id: UUID
    created_at: datetime
    updated_at: datetime
    reviewer_name: str = Field(
        ...,
        description="Name of the user who wrote the review"
    )
    caregiver_name: str = Field(
        ...,
        description="Name of the caregiver being reviewed"
    )

    class Config:
        from_attributes = True