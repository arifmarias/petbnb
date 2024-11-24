# app/core/security.py
from datetime import datetime, timedelta
from typing import Optional, Union, Dict, Tuple
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status, WebSocket, Security
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db
from app.models.user import User
from uuid import UUID
import logging

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Generate a password hash."""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a new access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def decode_jwt_token(token: str) -> Tuple[bool, Optional[Dict], Optional[str]]:
    """
    Decode and validate JWT token.
    Returns: (is_valid, payload, error_message)
    """
    try:
        # Remove 'Bearer ' if present
        token = token.replace('Bearer ', '')
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        return True, payload, None
    except JWTError as e:
        return False, None, f"Invalid token: {str(e)}"
    except Exception as e:
        return False, None, f"Token validation error: {str(e)}"

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """Get current user from token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode token
        is_valid, payload, error = decode_jwt_token(token)
        if not is_valid:
            logger.error(f"Token validation failed: {error}")
            raise credentials_exception

        user_id = payload.get("sub")
        if not user_id:
            raise credentials_exception

        # Try to get user by UUID first
        try:
            uuid_user_id = UUID(user_id)
            user = db.query(User).filter(User.id == uuid_user_id).first()
            if user:
                return user
        except (ValueError, TypeError):
            # If UUID conversion fails, try email (backward compatibility)
            user = db.query(User).filter(User.email == user_id).first()
            if user:
                return user

        raise credentials_exception
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise credentials_exception

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Verify user is active."""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

async def get_current_user_ws(
    websocket: WebSocket,
    token: Optional[str] = None,
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Get current user from WebSocket connection."""
    try:
        # First try query parameter
        if token:
            is_valid, payload, error = decode_jwt_token(token)
            if not is_valid:
                logger.error(f"Token validation failed: {error}")
                await websocket.close(code=4001)
                return None
        else:
            # Fallback to header
            auth_header = websocket.headers.get("authorization")
            if not auth_header:
                logger.error("No authorization provided")
                await websocket.close(code=4000)
                return None
                
            is_valid, payload, error = decode_jwt_token(auth_header)
            if not is_valid:
                logger.error(f"Token validation failed: {error}")
                await websocket.close(code=4001)
                return None

        user_id = payload.get("sub")
        try:
            uuid_user_id = UUID(user_id)
            user = db.query(User).filter(User.id == uuid_user_id).first()
            if not user:
                # Try email as fallback
                user = db.query(User).filter(User.email == user_id).first()
        except (ValueError, TypeError):
            user = db.query(User).filter(User.email == user_id).first()

        if not user:
            logger.error(f"User not found for ID: {user_id}")
            await websocket.close(code=4002)
            return None

        if not user.is_active:
            logger.error(f"Inactive user: {user_id}")
            await websocket.close(code=4003)
            return None

        return user

    except Exception as e:
        logger.error(f"WebSocket authentication error: {str(e)}")
        await websocket.close(code=4004)
        return None

# WebSocket close codes
WS_CLOSE_CODES = {
    4000: "No authorization provided",
    4001: "Invalid token",
    4002: "User not found",
    4003: "Inactive user",
    4004: "Authentication error"
}