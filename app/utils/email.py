# app/utils/email.py
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from pydantic import EmailStr
from typing import List, Dict, Any
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

# Authentication related emails
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

# Generic email sender
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

# Booking related emails
async def send_booking_confirmation_email(
    owner_email: str,
    booking_details: dict
) -> None:
    """Send booking confirmation email to owner"""
    html = f"""
        <h3>Booking Confirmation</h3>
        <p>Your booking has been confirmed!</p>
        <p>Details:</p>
        <ul>
            <li>Pet: {booking_details['pet_name']}</li>
            <li>Service: {booking_details['service_type']}</li>
            <li>From: {booking_details['start_date']}</li>
            <li>To: {booking_details['end_date']}</li>
            <li>Caregiver: {booking_details['caregiver_name']}</li>
            <li>Total Price: {booking_details['currency']} {booking_details['total_price']:.2f}</li>
        </ul>
        <p>Special Instructions: {booking_details.get('special_instructions', 'None')}</p>
        <p>Best regards,<br>The PetBnB Team</p>
    """
    
    message = MessageSchema(
        subject="PetBnB Booking Confirmation",
        recipients=[owner_email],
        body=html,
        subtype="html"
    )
    
    fm = FastMail(conf)
    await fm.send_message(message)

async def send_booking_notification_to_caregiver(
    caregiver_email: str,
    booking_details: dict
) -> None:
    """Send booking notification to caregiver"""
    html = f"""
        <h3>New Booking Request</h3>
        <p>You have received a new booking request!</p>
        <p>Details:</p>
        <ul>
            <li>Pet: {booking_details['pet_name']} ({booking_details['pet_type']})</li>
            <li>Service: {booking_details['service_type']}</li>
            <li>From: {booking_details['start_date']}</li>
            <li>To: {booking_details['end_date']}</li>
            <li>Owner: {booking_details['owner_name']}</li>
            <li>Total Price: {booking_details['currency']} {booking_details['total_price']:.2f}</li>
        </ul>
        <p>Special Instructions: {booking_details.get('special_instructions', 'None')}</p>
        <p>Please log in to accept or reject this booking.</p>
        <p>Best regards,<br>The PetBnB Team</p>
    """
    
    message = MessageSchema(
        subject="PetBnB - New Booking Request",
        recipients=[caregiver_email],
        body=html,
        subtype="html"
    )
    
    fm = FastMail(conf)
    await fm.send_message(message)

async def send_booking_status_update(
    email: str,
    booking_details: dict,
    status: str
) -> None:
    """Send booking status update email"""
    html = f"""
        <h3>Booking Status Update</h3>
        <p>Your booking status has been updated to: {status}</p>
        <p>Booking Details:</p>
        <ul>
            <li>Booking ID: {booking_details['id']}</li>
            <li>Pet: {booking_details['pet_name']}</li>
            <li>Service: {booking_details['service_type']}</li>
            <li>From: {booking_details['start_date']}</li>
            <li>To: {booking_details['end_date']}</li>
            <li>Total Price: {booking_details['currency']} {booking_details['total_price']:.2f}</li>
        </ul>
        <p>Best regards,<br>The PetBnB Team</p>
    """
    
    message = MessageSchema(
        subject=f"PetBnB Booking {status.capitalize()}",
        recipients=[email],
        body=html,
        subtype="html"
    )
    
    fm = FastMail(conf)
    await fm.send_message(message)

# Payment related emails
async def send_payment_confirmation(
    email_to: str,
    payment_details: Dict[str, Any]
) -> None:
    """Send payment confirmation email."""
    html = f"""
        <h3>Payment Confirmation</h3>
        <p>Your payment has been successfully processed!</p>
        <p>Details:</p>
        <ul>
            <li>Booking ID: {payment_details['booking_id']}</li>
            <li>Amount: {payment_details['currency']} {payment_details['amount']:.2f}</li>
            <li>Transaction ID: {payment_details.get('transaction_id', 'N/A')}</li>
        </ul>
        <p>Your booking has been confirmed, and you will receive a separate booking confirmation email.</p>
        <p>Thank you for using PetBnB!</p>
        <p>Best regards,<br>The PetBnB Team</p>
    """
    
    message = MessageSchema(
        subject="PetBnB Payment Confirmation",
        recipients=[email_to],
        body=html,
        subtype="html"
    )
    
    fm = FastMail(conf)
    await fm.send_message(message)

async def send_payment_failed(
    email_to: str,
    payment_details: Dict[str, Any]
) -> None:
    """Send payment failed notification."""
    html = f"""
        <h3>Payment Failed</h3>
        <p>Unfortunately, your payment for booking {payment_details['booking_id']} failed.</p>
        <p>Error: {payment_details.get('error', 'Unknown error')}</p>
        <p>Please try again by clicking the link below:</p>
        <p><a href="{payment_details.get('retry_link', '#')}">Retry Payment</a></p>
        <p>If you continue to experience issues, please contact our support team.</p>
        <p>Best regards,<br>The PetBnB Team</p>
    """
    
    message = MessageSchema(
        subject="PetBnB Payment Failed",
        recipients=[email_to],
        body=html,
        subtype="html"
    )
    
    fm = FastMail(conf)
    await fm.send_message(message)

async def send_payment_required(
    email_to: str,
    payment_details: Dict[str, Any]
) -> None:
    """Send payment required notification."""
    html = f"""
        <h3>Payment Required</h3>
        <p>Your booking (ID: {payment_details['booking_id']}) requires payment to be confirmed.</p>
        <p>Amount due: {payment_details['currency']} {payment_details['amount']:.2f}</p>
        <p>Please complete your payment by clicking this link:</p>
        <p><a href="{payment_details['payment_link']}">Complete Payment</a></p>
        <p>This payment request will expire in {settings.PAYMENT_EXPIRATION_MINUTES} minutes.</p>
        <p>Best regards,<br>The PetBnB Team</p>
    """
    
    message = MessageSchema(
        subject="PetBnB Payment Required",
        recipients=[email_to],
        body=html,
        subtype="html"
    )
    
    fm = FastMail(conf)
    await fm.send_message(message)

async def send_refund_confirmation(
    email_to: str,
    refund_details: Dict[str, Any]
) -> None:
    """Send refund confirmation email."""
    html = f"""
        <h3>Refund Confirmation</h3>
        <p>Your refund has been processed successfully!</p>
        <p>Details:</p>
        <ul>
            <li>Booking ID: {refund_details['booking_id']}</li>
            <li>Refund Amount: {refund_details['currency']} {refund_details['amount']:.2f}</li>
            <li>Reason: {refund_details.get('reason', 'Not specified')}</li>
            <li>Reference Number: {refund_details.get('reference_number', 'N/A')}</li>
        </ul>
        <p>The refund should appear in your account within 5-10 business days.</p>
        <p>Best regards,<br>The PetBnB Team</p>
    """
    
    message = MessageSchema(
        subject="PetBnB Refund Confirmation",
        recipients=[email_to],
        body=html,
        subtype="html"
    )
    
    fm = FastMail(conf)
    await fm.send_message(message)

# New function for payout notifications
async def send_payout_notification(
    email_to: str,
    payout_details: Dict[str, Any]
) -> None:
    """Send payout notification to caregiver."""
    html = f"""
        <h3>Payout Processed</h3>
        <p>Your payout has been processed and is on its way to your bank account!</p>
        <p>Details:</p>
        <ul>
            <li>Amount: {payout_details['currency']} {payout_details['amount']:.2f}</li>
            <li>Period: {payout_details['period_start']} to {payout_details['period_end']}</li>
            <li>Number of Bookings: {payout_details['booking_count']}</li>
            <li>Transfer Reference: {payout_details.get('reference', 'N/A')}</li>
        </ul>
        <p>The funds should appear in your bank account within 5-7 business days.</p>
        <p>Best regards,<br>The PetBnB Team</p>
    """
    
    message = MessageSchema(
        subject="PetBnB Payout Processed",
        recipients=[email_to],
        body=html,
        subtype="html"
    )
    
    fm = FastMail(conf)
    await fm.send_message(message)