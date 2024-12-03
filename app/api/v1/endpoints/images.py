# app/api/v1/endpoints/images.py
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.image import Image
from app.models.pet import Pet
from app.models.caregiver import CaregiverProfile
from app.utils.image import CloudinaryService
from app.schemas.image import ImageResponse
from app.core.config import settings
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
    """Upload an image for a user, pet, or caregiver profile."""
    try:
        # Validate entity type
        if entity_type not in ["user", "pet", "caregiver"]:
            raise HTTPException(status_code=400, detail="Invalid entity type")
        
        # Check permissions
        if entity_type == "user":
            if entity_id != current_user.id:
                raise HTTPException(status_code=403, detail="Not authorized")
            max_images = 1
        elif entity_type == "pet":
            entity = db.query(Pet).filter(Pet.id == entity_id).first()
            if not entity or entity.owner_id != current_user.id:
                raise HTTPException(status_code=404, detail="Pet not found")
            max_images = settings.MAX_IMAGES_PER_PET
        else:  # caregiver
            entity = db.query(CaregiverProfile).filter(CaregiverProfile.id == entity_id).first()
            if not entity or entity.user_id != current_user.id:
                raise HTTPException(status_code=404, detail="Caregiver profile not found")
            max_images = settings.MAX_IMAGES_PER_CAREGIVER

        # Check existing images and handle replacement if needed
        existing_images = db.query(Image).filter(
            Image.entity_type == entity_type,
            Image.entity_id == entity_id
        ).all()
        
        if len(existing_images) >= max_images:
            if entity_type == "user" and existing_images:
                # Delete old image from Cloudinary
                old_image = existing_images[0]
                await cloudinary_service.delete_image(old_image.public_id)
                db.delete(old_image)
                db.commit()
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Maximum number of images ({max_images}) reached"
                )

        # Upload to Cloudinary
        result = await cloudinary_service.upload_image(
            file=file,
            folder=f"petbnb/{entity_type}/{entity_id}",
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
            order=1 if entity_type == "user" else (len(existing_images) + 1)
        )
        
        db.add(image)
        db.commit()
        db.refresh(image)

        # Update user's profile picture if it's a user image
        if entity_type == "user":
            current_user.profile_picture = image.url
            db.commit()
        
        return image

    except Exception as e:
        db.rollback()
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@router.delete("/{image_id}")
async def delete_image(
    image_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete an image."""
    try:
        image = db.query(Image).filter(Image.id == image_id).first()
        if not image:
            raise HTTPException(status_code=404, detail="Image not found")

        # Verify ownership
        if image.entity_type == "user" and image.entity_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized")
        elif image.entity_type == "pet":
            pet = db.query(Pet).filter(Pet.id == image.entity_id).first()
            if not pet or pet.owner_id != current_user.id:
                raise HTTPException(status_code=403, detail="Not authorized")
        elif image.entity_type == "caregiver":
            caregiver = db.query(CaregiverProfile).filter(CaregiverProfile.id == image.entity_id).first()
            if not caregiver or caregiver.user_id != current_user.id:
                raise HTTPException(status_code=403, detail="Not authorized")

        # Delete from Cloudinary
        await cloudinary_service.delete_image(image.public_id)

        # Clear user's profile picture if it's a user image
        if image.entity_type == "user":
            current_user.profile_picture = None
            db.commit()

        # Delete from database
        db.delete(image)
        db.commit()

        return {"message": "Image deleted successfully"}

    except Exception as e:
        db.rollback()
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )