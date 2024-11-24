# app/api/deps.py
from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from uuid import UUID
import logging
from app.core.config import settings
from app.core.database import SessionLocal
from app.models.user import User
from app.schemas.user import TokenData
from app.core.security import decode_jwt_token

logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

def get_db() -> Generator:
    """Database session dependency."""
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()

async def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> User:
    """Get current user from token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        is_valid, payload, error = decode_jwt_token(token)
        if not is_valid:
            logger.error(f"Token validation failed: {error}")
            raise credentials_exception

        user_id = payload.get("sub")
        if not user_id:
            raise credentials_exception

        # Try UUID first
        try:
            uuid_obj = UUID(user_id)
            user = db.query(User).filter(User.id == uuid_obj).first()
            if user:
                return user
        except (ValueError, TypeError):
            # Try email as fallback
            user = db.query(User).filter(User.email == user_id).first()
            if user:
                return user

        raise credentials_exception

    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise credentials_exception

async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Check if user is active."""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

async def get_current_admin_user(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """Check if user is admin."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=403,
            detail="The user doesn't have enough privileges"
        )
    return current_user