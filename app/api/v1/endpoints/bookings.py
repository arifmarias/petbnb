# app/api/v1/endpoints/bookings.py
from typing import List, Any, Optional, Dict
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from app.api import deps
from app.schemas import booking as booking_schemas
from app.models.user import User
from app.models.pet import Pet
from app.models.booking import Booking, BookingStatus
from app.models.caregiver import CaregiverProfile
from app.utils import email as email_utils
from datetime import datetime, timedelta
from uuid import UUID

router = APIRouter()

def create_booking_response(booking: Booking, current_user: User) -> Dict:
    """Helper function to create consistent booking responses"""
    return {
        "id": booking.id,
        "pet_id": booking.pet_id,
        "owner_id": booking.owner_id,
        "caregiver_id": booking.caregiver_id,
        "service_type": booking.service_type,
        "start_date": booking.start_date,
        "end_date": booking.end_date,
        "status": booking.status,
        "total_price": booking.total_price,
        "special_instructions": booking.special_instructions,
        "created_at": booking.created_at,
        "updated_at": booking.updated_at,
        "pet_name": booking.pet.name if booking.pet else "",
        "owner_name": booking.owner.full_name if booking.owner else "",
        "caregiver_name": booking.caregiver.user.full_name if booking.caregiver and booking.caregiver.user else "",
        "can_cancel": can_cancel_booking(booking, current_user),
        "can_review": can_review_booking(booking, current_user)
    }

@router.post("/", response_model=booking_schemas.BookingResponse)
async def create_booking(
    *,
    db: Session = Depends(deps.get_db),
    booking_in: booking_schemas.BookingCreate,
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """Create a new booking with email notifications."""
    # Verify pet ownership with eager loading
    pet = db.query(Pet).filter(Pet.id == booking_in.pet_id).first()
    if not pet or pet.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Pet not found or not owned by user")

    # Verify caregiver exists and is available
    caregiver = db.query(CaregiverProfile).options(
        joinedload(CaregiverProfile.user)
    ).filter(
        CaregiverProfile.id == booking_in.caregiver_id,
        CaregiverProfile.is_available == True
    ).first()
    if not caregiver:
        raise HTTPException(status_code=404, detail="Caregiver not found or not available")

    # Calculate total price
    total_price = calculate_booking_price(
        booking_in.service_type,
        booking_in.start_date,
        booking_in.end_date,
        caregiver
    )

    # Create booking
    booking = Booking(
        pet_id=booking_in.pet_id,
        owner_id=current_user.id,
        caregiver_id=booking_in.caregiver_id,
        service_type=booking_in.service_type,
        start_date=booking_in.start_date,
        end_date=booking_in.end_date,
        status=BookingStatus.PENDING,
        total_price=total_price,
        special_instructions=booking_in.special_instructions
    )
    
    db.add(booking)
    db.commit()
    db.refresh(booking)

    # Load relationships for response
    db.refresh(booking, ['pet', 'owner', 'caregiver'])

    # Prepare booking details for emails
    booking_details = {
        "id": str(booking.id),
        "pet_name": pet.name,
        "pet_type": pet.pet_type,
        "service_type": booking.service_type,
        "start_date": booking.start_date.strftime("%Y-%m-%d %H:%M"),
        "end_date": booking.end_date.strftime("%Y-%m-%d %H:%M"),
        "owner_name": current_user.full_name,
        "caregiver_name": caregiver.user.full_name,
        "total_price": total_price,
        "special_instructions": booking.special_instructions
    }

    try:
        # Send email to caregiver
        await email_utils.send_booking_notification_to_caregiver(
            caregiver.user.email,
            booking_details
        )
        
        # Send confirmation email to owner
        await email_utils.send_booking_confirmation_email(
            current_user.email,
            booking_details
        )
    except Exception as e:
        print(f"Error sending booking emails: {str(e)}")

    return create_booking_response(booking, current_user)

@router.get("/", response_model=List[booking_schemas.BookingResponse])
async def list_bookings(
    *,
    db: Session = Depends(deps.get_db),
    status: Optional[BookingStatus] = Query(None),
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """List bookings for current user."""
    query = db.query(Booking).options(
        joinedload(Booking.pet),
        joinedload(Booking.owner),
        joinedload(Booking.caregiver).joinedload(CaregiverProfile.user)
    )

    if current_user.is_admin:
        pass  # Admins can see all bookings
    elif current_user.user_type == "caregiver":
        caregiver = db.query(CaregiverProfile).filter(
            CaregiverProfile.user_id == current_user.id
        ).first()
        if not caregiver:
            raise HTTPException(status_code=404, detail="Caregiver profile not found")
        query = query.filter(Booking.caregiver_id == caregiver.id)
    else:
        query = query.filter(Booking.owner_id == current_user.id)

    if status:
        query = query.filter(Booking.status == status)

    query = query.order_by(Booking.created_at.desc())
    bookings = query.offset(skip).limit(limit).all()

    return [create_booking_response(booking, current_user) for booking in bookings]

@router.get("/{booking_id}", response_model=booking_schemas.BookingResponse)
async def get_booking(
    *,
    db: Session = Depends(deps.get_db),
    booking_id: UUID,
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """Get booking by ID."""
    booking = db.query(Booking).options(
        joinedload(Booking.pet),
        joinedload(Booking.owner),
        joinedload(Booking.caregiver).joinedload(CaregiverProfile.user)
    ).filter(Booking.id == booking_id).first()

    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    if not current_user.is_admin and current_user.id != booking.owner_id:
        caregiver = db.query(CaregiverProfile).filter(
            CaregiverProfile.user_id == current_user.id,
            CaregiverProfile.id == booking.caregiver_id
        ).first()
        if not caregiver:
            raise HTTPException(status_code=403, detail="Not enough permissions")

    return create_booking_response(booking, current_user)

@router.put("/{booking_id}/status", response_model=booking_schemas.BookingResponse)
async def update_booking_status(
    *,
    db: Session = Depends(deps.get_db),
    booking_id: UUID,
    status: BookingStatus,
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """Update booking status."""
    booking = db.query(Booking).options(
        joinedload(Booking.pet),
        joinedload(Booking.owner),
        joinedload(Booking.caregiver).joinedload(CaregiverProfile.user)
    ).filter(Booking.id == booking_id).first()

    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    if not current_user.is_admin:
        caregiver = db.query(CaregiverProfile).filter(
            CaregiverProfile.user_id == current_user.id,
            CaregiverProfile.id == booking.caregiver_id
        ).first()
        if not caregiver:
            raise HTTPException(status_code=403, detail="Not enough permissions")

    booking.status = status
    db.commit()
    db.refresh(booking)

    try:
        await email_utils.send_booking_status_update(
            booking.owner.email,
            {
                "id": str(booking.id),
                "pet_name": booking.pet.name,
                "service_type": booking.service_type,
                "start_date": booking.start_date.strftime("%Y-%m-%d %H:%M"),
                "end_date": booking.end_date.strftime("%Y-%m-%d %H:%M"),
                "owner_name": booking.owner.full_name,
                "caregiver_name": booking.caregiver.user.full_name,
                "total_price": booking.total_price
            },
            status.value
        )
    except Exception as e:
        print(f"Error sending status update email: {str(e)}")

    return create_booking_response(booking, current_user)

@router.post("/{booking_id}/cancel", response_model=booking_schemas.BookingResponse)
async def cancel_booking(
    *,
    db: Session = Depends(deps.get_db),
    booking_id: UUID,
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """Cancel booking."""
    booking = db.query(Booking).options(
        joinedload(Booking.pet),
        joinedload(Booking.owner),
        joinedload(Booking.caregiver).joinedload(CaregiverProfile.user)
    ).filter(Booking.id == booking_id).first()

    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    if not can_cancel_booking(booking, current_user):
        raise HTTPException(status_code=400, detail="Booking cannot be cancelled")

    booking.status = BookingStatus.CANCELLED
    db.commit()
    db.refresh(booking)

    try:
        booking_details = {
            "id": str(booking.id),
            "pet_name": booking.pet.name,
            "service_type": booking.service_type,
            "start_date": booking.start_date.strftime("%Y-%m-%d %H:%M"),
            "end_date": booking.end_date.strftime("%Y-%m-%d %H:%M"),
            "owner_name": booking.owner.full_name,
            "caregiver_name": booking.caregiver.user.full_name,
            "total_price": booking.total_price
        }

        await email_utils.send_booking_status_update(
            booking.owner.email,
            booking_details,
            "cancelled"
        )
        await email_utils.send_booking_status_update(
            booking.caregiver.user.email,
            booking_details,
            "cancelled"
        )
    except Exception as e:
        print(f"Error sending cancellation emails: {str(e)}")

    return create_booking_response(booking, current_user)

def calculate_booking_price(
    service_type: booking_schemas.ServiceType,
    start_date: datetime,
    end_date: datetime,
    caregiver: CaregiverProfile
) -> float:
    """Calculate total price for booking."""
    duration = end_date - start_date
    days = duration.days + (duration.seconds / 86400)

    if service_type == booking_schemas.ServiceType.BOARDING:
        return caregiver.price_per_night * (days + 1)
    elif service_type == booking_schemas.ServiceType.DAYCARE:
        return caregiver.price_per_day * (days + 1)
    elif service_type == booking_schemas.ServiceType.WALKING:
        return caregiver.price_per_walk

    raise ValueError("Invalid service type")

def can_cancel_booking(booking: Booking, user: User) -> bool:
    """Check if booking can be cancelled."""
    if user.is_admin:
        return True
    
    if booking.status not in [BookingStatus.PENDING, BookingStatus.CONFIRMED]:
        return False

    if user.id != booking.owner_id:
        return False

    if booking.start_date - datetime.utcnow() < timedelta(hours=24):
        return False

    return True

def can_review_booking(booking: Booking, user: User) -> bool:
    """Check if user can review the booking."""
    if user.id != booking.owner_id:
        return False

    if booking.status != BookingStatus.COMPLETED:
        return False

    if datetime.utcnow() - booking.end_date > timedelta(days=7):
        return False

    return True