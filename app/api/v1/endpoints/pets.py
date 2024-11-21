# app/api/v1/endpoints/pets.py
from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api import deps
from app.schemas import pet as pet_schemas
from app.models.user import User
from app.models.pet import Pet
from uuid import UUID

router = APIRouter()

@router.post("/", response_model=pet_schemas.Pet)
def create_pet(
    *,
    db: Session = Depends(deps.get_db),
    pet_in: pet_schemas.PetCreate,
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Create new pet for current user.
    """
    pet = Pet(
        owner_id=current_user.id,
        **pet_in.model_dump()
    )
    db.add(pet)
    db.commit()
    db.refresh(pet)
    return pet

@router.get("/", response_model=List[pet_schemas.Pet])
def read_pets(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Retrieve pets.
    """
    # If user is admin, return all pets
    if current_user.is_admin:
        pets = db.query(Pet).offset(skip).limit(limit).all()
    else:
        # Otherwise return only user's pets
        pets = db.query(Pet).filter(Pet.owner_id == current_user.id)\
            .offset(skip).limit(limit).all()
    return pets

@router.get("/{pet_id}", response_model=pet_schemas.Pet)
def read_pet(
    *,
    db: Session = Depends(deps.get_db),
    pet_id: UUID,
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Get pet by ID.
    """
    pet = db.query(Pet).filter(Pet.id == pet_id).first()
    if not pet:
        raise HTTPException(
            status_code=404,
            detail="Pet not found"
        )
    if not current_user.is_admin and pet.owner_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions"
        )
    return pet

@router.put("/{pet_id}", response_model=pet_schemas.Pet)
def update_pet(
    *,
    db: Session = Depends(deps.get_db),
    pet_id: UUID,
    pet_in: pet_schemas.PetUpdate,
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Update pet.
    """
    pet = db.query(Pet).filter(Pet.id == pet_id).first()
    if not pet:
        raise HTTPException(
            status_code=404,
            detail="Pet not found"
        )
    if not current_user.is_admin and pet.owner_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions"
        )
    
    update_data = pet_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(pet, field, value)
    
    db.add(pet)
    db.commit()
    db.refresh(pet)
    return pet

@router.delete("/{pet_id}")
def delete_pet(
    *,
    db: Session = Depends(deps.get_db),
    pet_id: UUID,
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Delete pet.
    """
    pet = db.query(Pet).filter(Pet.id == pet_id).first()
    if not pet:
        raise HTTPException(
            status_code=404,
            detail="Pet not found"
        )
    if not current_user.is_admin and pet.owner_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions"
        )
    
    db.delete(pet)
    db.commit()
    return {"message": "Pet deleted successfully"}