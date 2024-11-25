# app/api/v1/endpoints/images.py
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.image import Image
from app.models.pet import Pet
from app.models.caregiver import CaregiverProfile
from app.utils.image import CloudinaryService
from app.schemas.image import ImageResponse
from app.core.config import settings, StatusMessage
import uuid

router = APIRouter()
cloudinary_service = CloudinaryService()

@router.post("/{entity_type}/{entity_id}/upload", response_model=ImageResponse)
async def upload_image(
    entity_type: str,
    entity_id: uuid.UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upload an image for a pet or caregiver profile."""
    # Validate entity type
    if entity_type not in ["pet", "caregiver"]:
        raise HTTPException(status_code=400, detail="Invalid entity type")
    
    # Check permissions and get entity
    if entity_type == "pet":
        entity = db.query(Pet).filter(Pet.id == entity_id).first()
        if not entity or entity.owner_id != current_user.id:
            raise HTTPException(status_code=404, detail="Pet not found")
        max_images = settings.MAX_IMAGES_PER_PET
    else:  # caregiver
        entity = db.query(CaregiverProfile).filter(CaregiverProfile.id == entity_id).first()
        if not entity or entity.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Caregiver profile not found")
        max_images = settings.MAX_IMAGES_PER_CAREGIVER

    # Check image count
    existing_images = db.query(Image).filter(
        Image.entity_type == entity_type,
        Image.entity_id == entity_id
    ).count()
    
    if existing_images >= max_images:
        raise HTTPException(
            status_code=400,
            detail=f"Maximum number of images ({max_images}) reached"
        )

    # Upload image to Cloudinary
    result = await cloudinary_service.upload_image(
        file=file,
        folder="petbnb",
        entity_type=entity_type,
        entity_id=str(entity_id)
    )

    # Create image record
    image = Image(
        public_id=result["public_id"],
        url=result["url"],
        thumbnail_url=result["thumbnail_url"],
        entity_type=entity_type,
        entity_id=entity_id,
        order=existing_images + 1
    )
    
    db.add(image)
    db.commit()
    db.refresh(image)
    
    return image

@router.delete("/{image_id}")
async def delete_image(
    image_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete an image."""
    image = db.query(Image).filter(Image.id == image_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    # Verify ownership
    if image.entity_type == "pet":
        entity = db.query(Pet).filter(Pet.id == image.entity_id).first()
        if not entity or entity.owner_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized")
    else:  # caregiver
        entity = db.query(CaregiverProfile).filter(CaregiverProfile.id == image.entity_id).first()
        if not entity or entity.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized")

    # Delete from Cloudinary
    await cloudinary_service.delete_image(image.public_id)

    # Delete from database
    db.delete(image)
    db.commit()

    return {"message": "Image deleted successfully"}

@router.put("/{entity_type}/{entity_id}/reorder")
async def reorder_images(
    entity_type: str,
    entity_id: uuid.UUID,
    image_orders: List[dict],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Reorder images for an entity."""
    # Verify ownership
    if entity_type == "pet":
        entity = db.query(Pet).filter(Pet.id == entity_id).first()
        if not entity or entity.owner_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized")
    else:  # caregiver
        entity = db.query(CaregiverProfile).filter(CaregiverProfile.id == entity_id).first()
        if not entity or entity.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized")

    # Update orders
    for order_data in image_orders:
        image_id = order_data.get("image_id")
        new_order = order_data.get("order")
        
        if image_id and new_order is not None:
            image = db.query(Image).filter(
                Image.id == image_id,
                Image.entity_type == entity_type,
                Image.entity_id == entity_id
            ).first()
            
            if image:
                image.order = new_order

    db.commit()
    return {"message": "Images reordered successfully"}