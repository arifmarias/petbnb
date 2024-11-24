# app/api/v1/endpoints/payments.py
from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from sqlalchemy.orm import Session
from app.api import deps
from app.utils.stripe import StripeService
from app.core.config import settings, ErrorMessage
from app.models.payment import Payment, PaymentStatus, PaymentType
from app.models.booking import Booking, BookingStatus
from app.models.user import User
from app.schemas import payment as payment_schemas
from app.utils import email as email_utils
from typing import Any, Dict, List
from datetime import datetime
from uuid import UUID

router = APIRouter()

@router.post("/create-payment-intent", response_model=payment_schemas.PaymentIntent)
async def create_payment_intent(
    *,
    db: Session = Depends(deps.get_db),
    booking_id: UUID,
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """Create a payment intent for a booking."""
    booking = db.query(Booking).filter(
        Booking.id == booking_id,
        Booking.owner_id == current_user.id
    ).first()
    
    if not booking:
        raise HTTPException(
            status_code=404,
            detail=ErrorMessage.BOOKING_NOT_FOUND
        )

    # Handle booking status transition
    if booking.status == BookingStatus.PENDING:
        booking.status = BookingStatus.PAYMENT_REQUIRED
        db.commit()
        db.refresh(booking)
    elif booking.status != BookingStatus.PAYMENT_REQUIRED:
        raise HTTPException(
            status_code=400,
            detail=f"Booking is in {booking.status} status and cannot be paid for"
        )

    # Check for existing pending payment
    existing_payment = db.query(Payment).filter(
        Payment.booking_id == booking_id,
        Payment.status == PaymentStatus.PENDING
    ).first()
    
    if existing_payment:
        return {
            "client_secret": existing_payment.stripe_payment_intent_id,
            "payment_id": str(existing_payment.id)
        }

    try:
        # Create payment record
        payment = Payment(
            booking_id=booking_id,
            payer_id=current_user.id,
            recipient_id=booking.caregiver.user_id,
            amount=booking.total_price,
            currency=settings.CURRENCY,
            payment_type=PaymentType.BOOKING
        )
        
        db.add(payment)
        db.commit()
        db.refresh(payment)

        # Calculate platform fee
        platform_fee = StripeService.calculate_application_fee(booking.total_price)

        # Create Stripe PaymentIntent
        intent = await StripeService.create_payment_intent(
            amount=booking.total_price,
            currency=settings.CURRENCY,
            metadata={
                "booking_id": str(booking_id),
                "payment_id": str(payment.id),
                "platform_fee": str(platform_fee)
            }
        )
        
        payment.stripe_payment_intent_id = intent.id
        db.commit()

        return {
            "client_secret": intent.client_secret,
            "payment_id": payment.id
        }
        
    except Exception as e:
        db.delete(payment)
        db.commit()
        raise HTTPException(
            status_code=400,
            detail=f"{ErrorMessage.PAYMENT_FAILED}: {str(e)}"
        )

@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(deps.get_db)
) -> Dict[str, str]:
    """Handle Stripe webhooks."""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    
    try:
        event = await StripeService.verify_webhook_signature(
            payload,
            sig_header,
            settings.STRIPE_WEBHOOK_SECRET
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    print(f"Webhook Event Type: {event.type}")  # Debug log

    if event.type == "payment_intent.succeeded":
        payment_intent = event.data.object
        print(f"Payment Intent ID: {payment_intent.id}")  # Debug log
        
        # Get the payment record
        payment = db.query(Payment).filter(
            Payment.stripe_payment_intent_id == payment_intent.id
        ).first()
        
        print(f"Payment Record Found: {payment is not None}")  # Debug log
        
        if payment:
            try:
                # Start transaction
                payment.status = PaymentStatus.COMPLETED
                payment.completed_at = datetime.utcnow()
                
                # Update booking status
                booking = db.query(Booking).filter(
                    Booking.id == payment.booking_id
                ).first()
                
                if booking:
                    print(f"Current Booking Status: {booking.status}")  # Debug log
                    booking.status = BookingStatus.CONFIRMED
                    print(f"New Booking Status: {booking.status}")  # Debug log
                    
                # Commit changes
                db.commit()
                
                # Send notifications
                try:
                    await email_utils.send_payment_confirmation(
                        payment.payer.email,
                        {
                            "booking_id": str(booking.id),
                            "amount": payment.amount,
                            "currency": payment.currency,
                            "transaction_id": payment_intent.id
                        }
                    )
                    
                    await email_utils.send_booking_confirmation(
                        payment.recipient.email,
                        {
                            "booking_id": str(booking.id),
                            "amount": payment.amount,
                            "currency": payment.currency,
                            "payment_id": str(payment.id)
                        }
                    )
                except Exception as e:
                    print(f"Error sending payment notification emails: {str(e)}")
                    
            except Exception as e:
                db.rollback()
                print(f"Error processing payment success: {str(e)}")
                return {"status": "error", "message": str(e)}
    
    elif event.type == "payment_intent.payment_failed":
        payment_intent = event.data.object
        print(f"Failed Payment Intent ID: {payment_intent.id}")  # Debug log
        
        payment = db.query(Payment).filter(
            Payment.stripe_payment_intent_id == payment_intent.id
        ).first()
        
        if payment:
            try:
                payment.status = PaymentStatus.FAILED
                db.commit()
                
                # Send failure notification
                try:
                    await email_utils.send_payment_failed(
                        payment.payer.email,
                        {
                            "booking_id": str(payment.booking_id),
                            "error": payment_intent.last_payment_error.message if payment_intent.last_payment_error else "Payment failed"
                        }
                    )
                except Exception as e:
                    print(f"Error sending payment failed notification: {str(e)}")
                    
            except Exception as e:
                db.rollback()
                print(f"Error processing payment failure: {str(e)}")

    return {"status": "success"}

@router.post("/refund", response_model=payment_schemas.RefundResponse)
async def create_refund(
    *,
    db: Session = Depends(deps.get_db),
    refund_data: payment_schemas.RefundCreate,
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """Create a refund for a payment."""
    # Get the original payment
    original_payment = db.query(Payment).filter(Payment.id == refund_data.payment_id).first()
    if not original_payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    # Check permissions
    if not current_user.is_admin:
        booking = original_payment.booking
        if current_user.id not in [booking.owner_id, booking.caregiver.user_id]:
            raise HTTPException(status_code=403, detail="Not enough permissions")

    # Verify payment status
    if original_payment.status != PaymentStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail="Only completed payments can be refunded"
        )

    # Check if payment is already refunded
    if original_payment.status == PaymentStatus.REFUNDED:
        raise HTTPException(
            status_code=400,
            detail="Payment has already been refunded"
        )

    try:
        # Create Stripe refund
        refund_amount = refund_data.amount or original_payment.amount
        stripe_refund = await StripeService.create_refund(
            payment_intent_id=original_payment.stripe_payment_intent_id,
            amount=refund_amount,
            reason=refund_data.reason.value  # Use enum value
        )

        # Create refund record
        refund = Payment(
            booking_id=original_payment.booking_id,
            payer_id=original_payment.recipient_id,
            recipient_id=original_payment.payer_id,
            amount=refund_amount,
            currency=original_payment.currency,
            payment_type=PaymentType.REFUND,
            status=PaymentStatus.COMPLETED,
            stripe_refund_id=stripe_refund.id,
            completed_at=datetime.utcnow(),
            payment_id=original_payment.id,
            reason=refund_data.reason.value,
            stripe_payment_intent_id=original_payment.stripe_payment_intent_id
        )

        # Update original payment and booking
        original_payment.status = PaymentStatus.REFUNDED
        original_payment.booking.status = BookingStatus.CANCELLED

        db.add(refund)
        db.commit()
        db.refresh(refund)

        # Send notifications
        try:
            await email_utils.send_refund_confirmation(
                original_payment.payer.email,
                {
                    "booking_id": str(original_payment.booking_id),
                    "amount": refund_amount,
                    "currency": original_payment.currency,
                    "reason": refund_data.reason.value,
                    "reference_number": str(refund.id)
                }
            )
        except Exception as e:
            print(f"Error sending refund confirmation email: {str(e)}")

        return payment_schemas.RefundResponse(
            id=refund.id,
            booking_id=refund.booking_id,
            payment_id=original_payment.id,
            amount=refund.amount,
            currency=refund.currency,
            status=refund.status,
            payment_type=refund.payment_type,
            stripe_refund_id=refund.stripe_refund_id,
            reason=refund_data.reason,  # Use the enum directly
            created_at=refund.created_at,
            completed_at=refund.completed_at
        )

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"{ErrorMessage.REFUND_FAILED}: {str(e)}"
        )
@router.get("/refunds/{booking_id}", response_model=List[payment_schemas.RefundResponse])
async def list_refunds(
    *,
    db: Session = Depends(deps.get_db),
    booking_id: UUID,
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """List all refunds for a booking."""
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    # Check permissions
    if not current_user.is_admin and current_user.id not in [
        booking.owner_id, 
        booking.caregiver.user_id
    ]:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    refunds = db.query(Payment).filter(
        Payment.booking_id == booking_id,
        Payment.payment_type == PaymentType.REFUND
    ).all()

    return [payment_schemas.RefundResponse(
        id=refund.id,
        booking_id=refund.booking_id,
        payment_id=refund.payment_id,
        amount=refund.amount,
        currency=refund.currency,
        status=refund.status,
        payment_type=refund.payment_type,
        stripe_refund_id=refund.stripe_refund_id,
        reason=refund.reason,  # This will be converted to enum
        created_at=refund.created_at,
        completed_at=refund.completed_at
    ) for refund in refunds]

@router.get("/history", response_model=payment_schemas.PaymentListResponse)
async def get_payment_history(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    skip: int = 0,
    limit: int = 20
) -> Any:
    """Get payment history for current user."""
    # Build base query
    query = db.query(Payment)
    
    # Filter based on user role
    if not current_user.is_admin:
        query = query.filter(
            (Payment.payer_id == current_user.id) | 
            (Payment.recipient_id == current_user.id)
        )
    
    # Get total count and items
    total = query.count()
    items = query.order_by(Payment.created_at.desc()).offset(skip).limit(limit).all()
    
    # Calculate summary
    summary = {
        "total_payments": total,
        "total_amount": sum(item.amount for item in items),
        "currency": settings.CURRENCY,
        "completed_payments": sum(1 for item in items if item.status == PaymentStatus.COMPLETED),
        "refunded_payments": sum(1 for item in items if item.status == PaymentStatus.REFUNDED),
        "failed_payments": sum(1 for item in items if item.status == PaymentStatus.FAILED),
        "pending_payments": sum(1 for item in items if item.status == PaymentStatus.PENDING)
    }
    
    return {
        "items": items,
        "total": total,
        "summary": payment_schemas.PaymentSummary(**summary)
    }

@router.get("/booking/{booking_id}", response_model=payment_schemas.PaymentResponse)
async def get_booking_payment(
    *,
    db: Session = Depends(deps.get_db),
    booking_id: UUID,
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """Get payment details for a booking."""
    # First check if booking exists
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    # Check permissions
    if not current_user.is_admin and current_user.id not in [
        booking.owner_id, 
        booking.caregiver.user_id
    ]:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    # Get the latest payment for this booking
    payment = db.query(Payment).filter(
        Payment.booking_id == booking_id
    ).order_by(Payment.created_at.desc()).first()

    if not payment:
        raise HTTPException(status_code=404, detail="No payment found for this booking")

    return payment