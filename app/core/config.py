# app/core/config.py
from pydantic_settings import BaseSettings
from typing import List
from functools import lru_cache

class Settings(BaseSettings):
    PROJECT_NAME: str = "PetBnB"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Frontend URL
    FRONTEND_URL: str = "http://localhost:3000"
    
    # Database
    DATABASE_URL: str

    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # Email
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: str
    MAIL_PORT: int = 587
    MAIL_SERVER: str = "smtp.gmail.com"
    
    # Email Verification
    VERIFY_TOKEN_EXPIRE_HOURS: int = 48
    
    # Password Reset
    RESET_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["*"]

    class Config:
        case_sensitive = True
        env_file = ".env"

@lru_cache
def get_settings():
    return Settings()

settings = get_settings()