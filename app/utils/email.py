# app/utils/email.py
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from pydantic import EmailStr
from typing import List
from app.core.config import settings

conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)

async def send_verification_email(email: str, token: str):
    """Send verification email to user"""
    verify_url = f"{settings.FRONTEND_URL}/verify-email?token={token}"
    
    html = f"""
        <p>Hi there,</p>
        <p>Thanks for signing up with PetBnB! Please verify your email by clicking the link below:</p>
        <p><a href="{verify_url}">Verify Email</a></p>
        <p>If you didn't register for PetBnB, please ignore this email.</p>
        <br>
        <p>For testing purposes, here's your token:</p>
        <p style="background-color: #f0f0f0; padding: 10px; word-break: break-all;">{token}</p>
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
        <p>The link will expire in 30 minutes.</p>
        <br>
        <p>For testing purposes, here's your token:</p>
        <p style="background-color: #f0f0f0; padding: 10px; word-break: break-all;">{token}</p>
    """
    
    message = MessageSchema(
        subject="Reset your PetBnB password",
        recipients=[email],
        body=html,
        subtype="html"
    )
    
    fm = FastMail(conf)
    await fm.send_message(message)

# Helper function for sending any email
async def send_email(
    subject: str,
    recipients: List[str],
    html_content: str
):
    """Generic function to send any email"""
    message = MessageSchema(
        subject=subject,
        recipients=recipients,
        body=html_content,
        subtype="html"
    )
    
    fm = FastMail(conf)
    await fm.send_message(message)