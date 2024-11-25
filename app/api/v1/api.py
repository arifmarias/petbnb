# app/api/v1/api.py
from fastapi import APIRouter
from app.api.v1.endpoints import (
    auth, pets, caregivers, bookings, 
    payments, reviews, messages, images  
)

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(pets.router, prefix="/pets", tags=["pets"])
api_router.include_router(caregivers.router, prefix="/caregivers", tags=["caregivers"])
api_router.include_router(bookings.router, prefix="/bookings", tags=["bookings"])
api_router.include_router(reviews.router, prefix="/reviews", tags=["reviews"])
api_router.include_router(payments.router, prefix="/payments", tags=["payments"])
api_router.include_router(messages.router, prefix="/messages", tags=["messages"])
api_router.include_router(images.router, prefix="/images", tags=["images"]) 