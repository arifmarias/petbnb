# app/api/v1/endpoints/auth.py
from datetime import timedelta, datetime
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.api import deps
from app.core import security
from app.core.config import settings
from app.schemas import user as user_schemas
from app.models.user import User
from app.core.security import get_password_hash, verify_password
from app.utils import email as email_utils
import jwt

router = APIRouter()

@router.post("/register", response_model=user_schemas.User)
async def register_user(
    *,
    db: Session = Depends(deps.get_db),
    user_in: user_schemas.UserCreate,
) -> Any:
    """Register new user and send verification email."""
    user = db.query(User).filter(User.email == user_in.email).first()
    if user:
        raise HTTPException(
            status_code=400,
            detail="A user with this email already exists."
        )
    
    # Create user
    user = User(
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name,
        phone=user_in.phone,
        address=user_in.address,
        user_type=user_in.user_type,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Generate verification token - use user.id (UUID) instead of email
    token = security.create_access_token(
        {"sub": str(user.id), "type": "verification", "email": user.email},
        expires_delta=timedelta(hours=settings.VERIFY_TOKEN_EXPIRE_HOURS)
    )
    user.verification_token = token
    db.commit()
    
    # Send verification email
    await email_utils.send_verification_email(user.email, token)
    
    return user

@router.post("/login", response_model=user_schemas.Token)
def login(
    db: Session = Depends(deps.get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """OAuth2 compatible token login."""
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    elif not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is verified
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email not verified. Please verify your email first.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    # Use UUID instead of email for token
    access_token = security.create_access_token(
        {"sub": str(user.id), "email": user.email},
        expires_delta=access_token_expires
    )
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

@router.post("/verify-email")
def verify_email(
    token: str = Body(...),
    db: Session = Depends(deps.get_db)
) -> Any:
    """Verify user email."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = payload.get("sub")
        email = payload.get("email")
        if not user_id or payload.get("type") != "verification":
            raise HTTPException(status_code=400, detail="Invalid token")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=400, detail="Verification link has expired")
    except jwt.JWTError:
        raise HTTPException(status_code=400, detail="Invalid token")
    
    user = db.query(User).filter(User.id == user_id, User.email == email).first()
    if not user or user.is_verified:
        raise HTTPException(status_code=400, detail="Invalid token or email already verified")
    
    user.is_verified = True
    user.verification_token = None
    db.commit()
    
    return {"message": "Email verified successfully"}

@router.post("/forgot-password")
async def forgot_password(
    email: str = Body(..., embed=True),
    db: Session = Depends(deps.get_db)
) -> Any:
    """Send password reset email."""
    user = db.query(User).filter(User.email == email).first()
    if not user:
        # For security reasons, don't reveal if email exists
        return {"message": "If a user with this email exists, they will receive a password reset link."}
    
    # Generate reset token using UUID
    token = security.create_access_token(
        {"sub": str(user.id), "type": "reset", "email": user.email},
        expires_delta=timedelta(minutes=settings.RESET_TOKEN_EXPIRE_MINUTES)
    )
    user.reset_password_token = token
    db.commit()
    
    # Send reset email
    await email_utils.send_reset_password_email(user.email, token)
    
    return {"message": "If a user with this email exists, they will receive a password reset link."}

@router.post("/reset-password")
def reset_password(
    token: str = Body(...),
    new_password: str = Body(...),
    db: Session = Depends(deps.get_db)
) -> Any:
    """Reset password."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = payload.get("sub")
        email = payload.get("email")
        if not user_id or payload.get("type") != "reset":
            raise HTTPException(status_code=400, detail="Invalid token")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=400, detail="Reset link has expired")
    except jwt.JWTError:
        raise HTTPException(status_code=400, detail="Invalid token")
    
    user = db.query(User).filter(User.id == user_id, User.email == email).first()
    if not user or user.reset_password_token != token:
        raise HTTPException(status_code=400, detail="Invalid token")
    
    # Validate new password
    if len(new_password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters long")
    
    user.hashed_password = get_password_hash(new_password)
    user.reset_password_token = None
    db.commit()
    
    return {"message": "Password reset successfully"}

@router.get("/me", response_model=user_schemas.User)
def read_users_me(
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Get current user."""
    return current_user

@router.put("/me", response_model=user_schemas.User)
def update_user_me(
    *,
    db: Session = Depends(deps.get_db),
    user_in: user_schemas.UserUpdate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Update current user."""
    if user_in.password:
        if len(user_in.password) < 8:
            raise HTTPException(status_code=400, detail="Password must be at least 8 characters long")
        current_user.hashed_password = get_password_hash(user_in.password)
    
    if user_in.full_name:
        current_user.full_name = user_in.full_name
    if user_in.phone:
        current_user.phone = user_in.phone
    if user_in.address:
        current_user.address = user_in.address
    
    db.commit()
    db.refresh(current_user)
    return current_user

@router.get("/users", response_model=list[user_schemas.User])
def list_users(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """List users (admin only)."""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    users = db.query(User).offset(skip).limit(limit).all()
    return users

@router.post("/resend-verification")
async def resend_verification_email(
    email: str = Body(..., embed=True),
    db: Session = Depends(deps.get_db)
) -> Any:
    """Resend verification email."""
    user = db.query(User).filter(User.email == email).first()
    if not user or user.is_verified:
        # Don't reveal if user exists or is already verified
        return {"message": "If a user with this email exists and is not verified, they will receive a verification email."}
    
    # Generate new verification token using UUID
    token = security.create_access_token(
        {"sub": str(user.id), "type": "verification", "email": user.email},
        expires_delta=timedelta(hours=settings.VERIFY_TOKEN_EXPIRE_HOURS)
    )
    user.verification_token = token
    db.commit()
    
    # Send verification email
    await email_utils.send_verification_email(user.email, token)
    
    return {"message": "If a user with this email exists and is not verified, they will receive a verification email."}