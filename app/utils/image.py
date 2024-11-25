from fastapi import UploadFile, HTTPException
import cloudinary
import cloudinary.uploader
from typing import Optional, List
import uuid
from app.core.config import settings, StatusMessage
from datetime import datetime

class CloudinaryService:
    def __init__(self):
        cloudinary.config(
            cloud_name=settings.CLOUDINARY_CLOUD_NAME,
            api_key=settings.CLOUDINARY_API_KEY,
            api_secret=settings.CLOUDINARY_API_SECRET
        )

    async def upload_image(
        self,
        file: UploadFile,
        folder: str,
        entity_type: str,
        entity_id: str
    ) -> dict:
        """Upload image to Cloudinary."""
        if file.content_type not in settings.ALLOWED_IMAGE_TYPES:
            raise HTTPException(
                status_code=400,
                detail=StatusMessage.INVALID_FILE_TYPE
            )

        try:
            # Generate a unique identifier for the image
            unique_id = str(uuid.uuid4())[:8]
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            public_id = f"{folder}/{entity_type}/{entity_id}/{timestamp}_{unique_id}"

            # Upload to Cloudinary
            result = cloudinary.uploader.upload(
                file.file,
                public_id=public_id,
                folder=folder,
                resource_type="image",
                transformation=[
                    {"quality": "auto", "fetch_format": "auto"}
                ]
            )

            # Generate thumbnail transformation URL
            thumbnail_url = cloudinary.CloudinaryImage(result['public_id']).build_url(
                width=150,
                height=150,
                crop="fill",
                quality="auto",
                fetch_format="auto"
            )

            return {
                "public_id": result["public_id"],
                "url": result["secure_url"],
                "thumbnail_url": thumbnail_url
            }

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error uploading image: {str(e)}"
            )

    async def delete_image(self, public_id: str) -> bool:
        """Delete image from Cloudinary."""
        try:
            result = cloudinary.uploader.destroy(public_id)
            return result.get('result') == 'ok'
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error deleting image: {str(e)}"
            )