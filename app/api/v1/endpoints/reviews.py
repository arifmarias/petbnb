# app/api/v1/endpoints/reviews.py
from typing import List, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from app.api import deps
from app.schemas import review as review_schemas
from app.models.user import User
from app.models.review import Review
from app.models.booking import Booking, BookingStatus
from app.models.caregiver import CaregiverProfile
from app.utils import email as email_utils
from datetime import datetime, timedelta
from uuid import UUID

router = APIRouter()

@router.post("/", response_model=review_schemas.Review)
async def create_review(
    *,
    db: Session = Depends(deps.get_db),
    review_in: review_schemas.ReviewCreate,
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """Create a new review for a booking."""
    # Check if booking exists and is completed
    booking = db.query(Booking).filter(
        Booking.id == review_in.booking_id,
        Booking.owner_id == current_user.id,
        Booking.status == BookingStatus.COMPLETED
    ).first()

    if not booking:
        raise HTTPException(
            status_code=404,
            detail="Booking not found or not eligible for review"
        )

    # Check if review already exists
    existing_review = db.query(Review).filter(
        Review.booking_id == review_in.booking_id
    ).first()
    if existing_review:
        raise HTTPException(
            status_code=400,
            detail="Review already exists for this booking"
        )

    # Create review
    review = Review(
        booking_id=review_in.booking_id,
        reviewer_id=current_user.id,
        caregiver_id=booking.caregiver_id,
        rating=review_in.rating,
        comment=review_in.comment
    )
    
    db.add(review)
    db.commit()
    db.refresh(review)

    # Update caregiver rating
    caregiver = db.query(CaregiverProfile).filter(
        CaregiverProfile.id == booking.caregiver_id
    ).first()
    if caregiver:
        reviews = db.query(Review).filter(
            Review.caregiver_id == caregiver.id
        ).all()
        total_ratings = sum(r.rating for r in reviews)
        caregiver.rating = total_ratings / len(reviews)
        caregiver.total_reviews = len(reviews)
        db.commit()

    # Send notification to caregiver
    try:
        await email_utils.send_review_notification(
            booking.caregiver.user.email,
            {
                "booking_id": str(booking.id),
                "pet_name": booking.pet.name,
                "rating": review.rating,
                "comment": review.comment,
                "reviewer_name": current_user.full_name
            }
        )
    except Exception as e:
        print(f"Error sending review notification: {str(e)}")

    return review

@router.get("/caregiver/{caregiver_id}", response_model=List[review_schemas.Review])
async def list_caregiver_reviews(
    *,
    db: Session = Depends(deps.get_db),
    caregiver_id: UUID,
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """List all reviews for a caregiver."""
    reviews = db.query(Review).filter(
        Review.caregiver_id == caregiver_id
    ).options(
        joinedload(Review.reviewer),
        joinedload(Review.caregiver)
    ).offset(skip).limit(limit).all()

    return reviews

@router.get("/booking/{booking_id}", response_model=review_schemas.Review)
async def get_booking_review(
    *,
    db: Session = Depends(deps.get_db),
    booking_id: UUID,
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """Get review for a specific booking."""
    review = db.query(Review).filter(
        Review.booking_id == booking_id
    ).options(
        joinedload(Review.reviewer),
        joinedload(Review.caregiver)
    ).first()

    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    return review

@router.put("/{review_id}", response_model=review_schemas.Review)
async def update_review(
    *,
    db: Session = Depends(deps.get_db),
    review_id: UUID,
    review_in: review_schemas.ReviewUpdate,
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """Update a review."""
    review = db.query(Review).filter(
        Review.id == review_id,
        Review.reviewer_id == current_user.id
    ).first()

    if not review:
        raise HTTPException(
            status_code=404,
            detail="Review not found or not owned by user"
        )

    # Update review
    review.rating = review_in.rating
    review.comment = review_in.comment
    review.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(review)

    # Update caregiver rating
    caregiver = db.query(CaregiverProfile).filter(
        CaregiverProfile.id == review.caregiver_id
    ).first()
    if caregiver:
        reviews = db.query(Review).filter(
            Review.caregiver_id == caregiver.id
        ).all()
        total_ratings = sum(r.rating for r in reviews)
        caregiver.rating = total_ratings / len(reviews)
        db.add(caregiver)
        db.commit()

    return review

@router.delete("/{review_id}")
async def delete_review(
    *,
    db: Session = Depends(deps.get_db),
    review_id: UUID,
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """Delete a review."""
    review = db.query(Review).filter(
        Review.id == review_id,
        Review.reviewer_id == current_user.id
    ).first()

    if not review:
        raise HTTPException(
            status_code=404,
            detail="Review not found or not owned by user"
        )

    db.delete(review)
    db.commit()

    # Update caregiver rating
    caregiver = db.query(CaregiverProfile).filter(
        CaregiverProfile.id == review.caregiver_id
    ).first()
    if caregiver:
        reviews = db.query(Review).filter(
            Review.caregiver_id == caregiver.id
        ).all()
        if reviews:
            total_ratings = sum(r.rating for r in reviews)
            caregiver.rating = total_ratings / len(reviews)
            caregiver.total_reviews = len(reviews)
        else:
            caregiver.rating = 0
            caregiver.total_reviews = 0
        db.add(caregiver)
        db.commit()

    return {"message": "Review deleted successfully"}