# app/core/config.py
from pydantic_settings import BaseSettings
from typing import List, Optional
from functools import lru_cache
from decimal import Decimal

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

    # Stripe Settings
    STRIPE_SECRET_KEY: Optional[str] = None
    STRIPE_PUBLISHABLE_KEY: Optional[str] = None
    STRIPE_WEBHOOK_SECRET: Optional[str] = None
    STRIPE_PLATFORM_FEE_PERCENT: Decimal = Decimal("10.0")
    
    # Payment Settings
    CURRENCY: str = "MYR"
    PAYMENT_EXPIRATION_MINUTES: int = 60
    MIN_PAYOUT_AMOUNT: Decimal = Decimal("50.0")
    
    # Supported Countries
    SUPPORTED_COUNTRIES: List[str] = ["MY", "SG"]

    # WebSocket Settings
    WS_MESSAGE_QUEUE_SIZE: int = 1000
    WS_HEARTBEAT_INTERVAL: int = 30
    WS_PING_TIMEOUT: int = 30
    
    # Chat Settings
    MAX_MESSAGE_LENGTH: int = 2000
    MESSAGE_RETENTION_DAYS: int = 90
    ALLOWED_CONTACT_SHARING_STATUSES: List[str] = ["CONFIRMED", "COMPLETED"]
    
    # Cloudinary Settings
    CLOUDINARY_CLOUD_NAME: Optional[str] = None
    CLOUDINARY_API_KEY: Optional[str] = None
    CLOUDINARY_API_SECRET: Optional[str] = None
    
    # Image Settings
    MAX_IMAGE_SIZE: int = 5 * 1024 * 1024  # 5MB
    ALLOWED_IMAGE_TYPES: List[str] = ["image/jpeg", "image/png", "image/gif"]
    MAX_IMAGES_PER_PET: int = 5
    MAX_IMAGES_PER_CAREGIVER: int = 10

    class Config:
        case_sensitive = True
        env_file = ".env"

    @property
    def cors_origins(self) -> List[str]:
        if self.BACKEND_CORS_ORIGINS:
            return [origin.strip() for origin in self.BACKEND_CORS_ORIGINS]
        return []

@lru_cache
def get_settings():
    return Settings()

settings = get_settings()

# Constants
TEMP_FILE_PATH = "temp"
MAX_UPLOAD_SIZE = 5 * 1024 * 1024  # 5MB

# Status Messages
class StatusMessage:
    INVALID_CREDENTIALS = "Invalid credentials"
    INACTIVE_USER = "Inactive user"
    EMAIL_ALREADY_REGISTERED = "Email already registered"
    VERIFICATION_EMAIL_SENT = "Verification email sent"
    INVALID_VERIFICATION_TOKEN = "Invalid verification token"
    EMAIL_ALREADY_VERIFIED = "Email already verified"
    PASSWORD_RESET_EMAIL_SENT = "Password reset email sent"
    INVALID_RESET_TOKEN = "Invalid reset token"
    PASSWORD_UPDATED = "Password updated successfully"
    INSUFFICIENT_PERMISSIONS = "Insufficient permissions"
    RESOURCE_NOT_FOUND = "Resource not found"
    INVALID_FILE_TYPE = "Invalid file type"
    FILE_TOO_LARGE = "File too large"
    CONTACT_SHARING_NOT_ALLOWED = "Contact sharing is only allowed after booking confirmation"

# Error Messages
class ErrorMessage:
    DATABASE_ERROR = "Database error occurred"
    EMAIL_ERROR = "Error sending email"
    FILE_UPLOAD_ERROR = "Error uploading file"
    STRIPE_ERROR = "Payment processing error"
    INVALID_BOOKING_STATUS = "Invalid booking status"
    BOOKING_NOT_FOUND = "Booking not found"
    PAYMENT_FAILED = "Payment failed"
    REFUND_FAILED = "Refund failed"
    PAYOUT_FAILED = "Payout failed"
    ACCOUNT_CREATION_FAILED = "Account creation failed"
    WEBSOCKET_ERROR = "WebSocket connection error"
    MESSAGE_TOO_LONG = "Message exceeds maximum length"