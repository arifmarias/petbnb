# app/api/v1/endpoints/caregivers.py
from typing import List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.api import deps
from app.schemas import caregiver as caregiver_schemas
from app.models.user import User, UserType
from app.models.caregiver import CaregiverProfile
from uuid import UUID
from sqlalchemy import or_

router = APIRouter()

@router.post("/profile", response_model=caregiver_schemas.CaregiverProfile)
async def create_caregiver_profile(
    *,
    db: Session = Depends(deps.get_db),
    profile_in: caregiver_schemas.CaregiverProfileCreate,
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Create caregiver profile for current user.
    """
    if current_user.user_type != UserType.CAREGIVER:
        raise HTTPException(
            status_code=400,
            detail="User must be a caregiver to create profile"
        )
    
    if db.query(CaregiverProfile).filter(CaregiverProfile.user_id == current_user.id).first():
        raise HTTPException(
            status_code=400,
            detail="Caregiver profile already exists"
        )
    
    profile = CaregiverProfile(
        user_id=current_user.id,
        **profile_in.model_dump()
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile

@router.get("/search", response_model=List[caregiver_schemas.CaregiverPublicProfile])
async def search_caregivers(
    *,
    db: Session = Depends(deps.get_db),
    service_type: Optional[str] = None,
    pet_type: Optional[str] = None,
    max_price: Optional[float] = None,
    pet_size: Optional[str] = None,
    location: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Search for caregivers with filters.
    """
    query = db.query(CaregiverProfile).filter(CaregiverProfile.is_available == True)
    
    if service_type:
        query = query.filter(CaregiverProfile.services_offered.contains([service_type]))
    if pet_type:
        query = query.filter(CaregiverProfile.accepted_pet_types.contains([pet_type]))
    if max_price:
        query = query.filter(or_(
            CaregiverProfile.price_per_night <= max_price,
            CaregiverProfile.price_per_day <= max_price,
            CaregiverProfile.price_per_walk <= max_price
        ))
    if pet_size:
        query = query.filter(CaregiverProfile.preferred_pet_size.contains([pet_size]))
    if location:
        # Implement location-based search when you add geocoding
        pass
    
    caregivers = query.offset(skip).limit(limit).all()
    return caregivers

@router.get("/profile/me", response_model=caregiver_schemas.CaregiverProfile)
async def get_my_caregiver_profile(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Get current user's caregiver profile.
    """
    if current_user.user_type != UserType.CAREGIVER:
        raise HTTPException(
            status_code=400,
            detail="User is not a caregiver"
        )
    
    profile = db.query(CaregiverProfile).filter(CaregiverProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(
            status_code=404,
            detail="Caregiver profile not found"
        )
    return profile

@router.get("/{caregiver_id}", response_model=caregiver_schemas.CaregiverPublicProfile)
async def get_caregiver_profile(
    caregiver_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Get specific caregiver's public profile.
    """
    profile = db.query(CaregiverProfile).filter(CaregiverProfile.id == caregiver_id).first()
    if not profile:
        raise HTTPException(
            status_code=404,
            detail="Caregiver profile not found"
        )
    return profile

@router.put("/profile", response_model=caregiver_schemas.CaregiverProfile)
async def update_caregiver_profile(
    *,
    db: Session = Depends(deps.get_db),
    profile_in: caregiver_schemas.CaregiverProfileUpdate,
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Update current user's caregiver profile.
    """
    if current_user.user_type != UserType.CAREGIVER:
        raise HTTPException(
            status_code=400,
            detail="User is not a caregiver"
        )
    
    profile = db.query(CaregiverProfile).filter(CaregiverProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(
            status_code=404,
            detail="Caregiver profile not found"
        )
    
    for field, value in profile_in.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)
    
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile

@router.delete("/profile")
async def delete_caregiver_profile(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Delete current user's caregiver profile.
    """
    if current_user.user_type != UserType.CAREGIVER:
        raise HTTPException(
            status_code=400,
            detail="User is not a caregiver"
        )
    
    profile = db.query(CaregiverProfile).filter(CaregiverProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(
            status_code=404,
            detail="Caregiver profile not found"
        )
    
    db.delete(profile)
    db.commit()
    return {"message": "Caregiver profile deleted successfully"}