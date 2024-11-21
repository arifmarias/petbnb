# app/core/email.py
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from pydantic import EmailStr, BaseModel
from typing import List, Dict, Any
from app.core.config import settings
import jwt
from datetime import datetime, timedelta

conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True
)

class EmailSchema(BaseModel):
    email: List[EmailStr]

async def send_verification_email(email: str, token: str):
    """Send verification email"""
    verify_url = f"{settings.FRONTEND_URL}/verify-email?token={token}"
    
    html = f"""
        <p>Hi there,</p>
        <p>Thanks for registering with PetBnB! Please verify your email by clicking the link below:</p>
        <p><a href="{verify_url}">Verify Email</a></p>
        <p>If you didn't register for PetBnB, please ignore this email.</p>
    """
    
    message = MessageSchema(
        subject="Verify your PetBnB email",
        recipients=[email],
        body=html,
        subtype="html"
    )
    
    fm = FastMail(conf)
    await fm.send_message(message)

async def send_reset_password_email(email: str, token: str):
    """Send password reset email"""
    reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token}"
    
    html = f"""
        <p>Hi there,</p>
        <p>You requested to reset your PetBnB password. Click the link below to proceed:</p>
        <p><a href="{reset_url}">Reset Password</a></p>
        <p>If you didn't request this, please ignore this email.</p>
    """
    
    message = MessageSchema(
        subject="Reset your PetBnB password",
        recipients=[email],
        body=html,
        subtype="html"
    )
    
    fm = FastMail(conf)
    await fm.send_message(message)