# app/api/v1/endpoints/pets.py
from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.api import deps
from app.schemas import pet as pet_schemas
from app.models.user import User
from app.models.pet import Pet
from app.models.image import Image
from uuid import UUID
import logging
from fastapi.responses import Response

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/debug", response_model=dict)
async def debug_auth(
    request: Request,
    current_user: User = Depends(deps.get_current_active_user)
) -> dict:
    """Debug endpoint to verify auth."""
    headers = dict(request.headers)
    auth_header = headers.get('authorization', '')
    
    logger.info(f"=== Debug Auth Request ===")
    logger.info(f"User ID: {current_user.id}")
    logger.info(f"Platform: {headers.get('x-platform', 'unknown')}")
    logger.info(f"Auth present: {bool(auth_header)}")
    
    return {
        "authenticated": True,
        "user_id": str(current_user.id),
        "email": current_user.email,
        "platform": headers.get('x-platform', 'unknown')
    }

@router.get("/token-debug")
async def token_debug(request: Request):
    """Debug endpoint to check token handling."""
    auth_header = request.headers.get('authorization', '')
    platform = request.headers.get('x-platform', 'unknown')
    
    logger.info(f"=== Token Debug ===")
    logger.info(f"Platform: {platform}")
    logger.info(f"Auth present: {bool(auth_header)}")
    logger.info(f"Headers: {dict(request.headers)}")
    
    try:
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            is_valid, payload, error = security.decode_jwt_token(token)
            return {
                "valid": is_valid,
                "error": error,
                "platform": platform,
                "payload": payload if is_valid else None
            }
    except Exception as e:
        logger.error(f"Token debug error: {str(e)}")
        return {
            "valid": False,
            "error": str(e),
            "platform": platform
        }
    
    return {
        "valid": False,
        "error": "No token provided",
        "platform": platform
    }

@router.post("/", response_model=pet_schemas.Pet)
def create_pet(
    *,
    db: Session = Depends(deps.get_db),
    pet_in: pet_schemas.PetCreate,
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """Create new pet for current user."""
    try:
        pet = Pet(
            owner_id=current_user.id,
            **pet_in.model_dump()
        )
        db.add(pet)
        db.commit()
        db.refresh(pet)
        return pet
    except Exception as e:
        logger.error(f"Error creating pet: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating pet"
        )

@router.get("/", response_model=List[pet_schemas.Pet])
async def read_pets(
    request: Request,
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """Retrieve all pets."""
    try:
        logger.info(f"Fetching pets for user: {current_user.id}")
        if current_user.is_admin:
            pets = db.query(Pet).offset(skip).limit(limit).all()
        else:
            pets = (
                db.query(Pet)
                .filter(Pet.owner_id == current_user.id)
                .offset(skip)
                .limit(limit)
                .all()
            )
        return pets
    except Exception as e:
        logger.error(f"Error fetching pets: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/{pet_id}", response_model=pet_schemas.Pet)
async def read_pet(
    pet_id: UUID,
    request: Request,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """Get specific pet by ID."""
    try:
        logger.info(f"Fetching pet {pet_id} for user: {current_user.id}")
        pet = db.query(Pet).filter(Pet.id == pet_id).first()
        
        if not pet:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pet not found"
            )
            
        if not current_user.is_admin and pet.owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
            
        return pet
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching pet {pet_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.put("/{pet_id}", response_model=pet_schemas.Pet)
def update_pet(
    *,
    db: Session = Depends(deps.get_db),
    pet_id: UUID,
    pet_in: pet_schemas.PetUpdate,
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """Update pet."""
    try:
        pet = db.query(Pet).filter(Pet.id == pet_id).first()
        if not pet:
            raise HTTPException(status_code=404, detail="Pet not found")
        if not current_user.is_admin and pet.owner_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not enough permissions")
        
        update_data = pet_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(pet, field, value)
        
        db.add(pet)
        db.commit()
        db.refresh(pet)
        return pet
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating pet: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating pet"
        )

@router.delete("/{pet_id}")
async def delete_pet(
    *,
    db: Session = Depends(deps.get_db),
    pet_id: UUID,
    current_user: User = Depends(deps.get_current_active_user)
):
    """Delete pet."""
    try:
        pet = db.query(Pet).filter(Pet.id == pet_id).first()
        if not pet:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pet not found"
            )
        if not current_user.is_admin and pet.owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )

        db.delete(pet)
        db.commit()
        
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting pet: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting pet"
        )