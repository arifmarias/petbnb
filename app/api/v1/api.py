# app/api/v1/api.py
from fastapi import APIRouter
from app.api.v1.endpoints import auth, pets, caregivers

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(pets.router, prefix="/pets", tags=["pets"])
api_router.include_router(caregivers.router, prefix="/caregivers", tags=["caregivers"])