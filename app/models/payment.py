# app/models/payment.py
from sqlalchemy import Column, ForeignKey, DateTime, Float, String, Enum, Text, ForeignKeyConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, foreign, remote
from app.core.database import Base
import uuid
from datetime import datetime
import enum

class PaymentStatus(str, enum.Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"

class PaymentType(str, enum.Enum):
    BOOKING = "BOOKING"
    REFUND = "REFUND"

class Payment(Base):
    __tablename__ = "payments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    booking_id = Column(UUID(as_uuid=True), ForeignKey("bookings.id"))
    payer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    recipient_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # Reference to original payment (for refunds)
    payment_id = Column(UUID(as_uuid=True), ForeignKey("payments.id"), nullable=True)
    
    amount = Column(Float, nullable=False)
    currency = Column(String, default="MYR")
    payment_type = Column(Enum(PaymentType), default=PaymentType.BOOKING)
    status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    
    # Stripe identifiers
    stripe_payment_intent_id = Column(String)
    stripe_refund_id = Column(String)
    
    # Additional fields for refunds
    reason = Column(Text, nullable=True)
    refund_metadata = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime)

    # Relationships
    booking = relationship("Booking", back_populates="payments")
    payer = relationship("User", foreign_keys=[payer_id])
    recipient = relationship("User", foreign_keys=[recipient_id])
    
    # Self-referential relationship for refunds
    refunds = relationship(
        "Payment",
        backref="original_payment",
        foreign_keys=[payment_id],
        remote_side=[id]
    )

    def __repr__(self):
        return f"<Payment {self.id} Amount={self.amount} Status={self.status}>"

    @property
    def is_refund(self):
        """Check if this payment is a refund."""
        return self.payment_type == PaymentType.REFUND

    @property
    def is_refundable(self):
        """Check if this payment can be refunded."""
        return (
            self.payment_type == PaymentType.BOOKING and 
            self.status == PaymentStatus.COMPLETED and 
            not any(refund.status == PaymentStatus.COMPLETED for refund in self.refunds)
        )

    @property
    def refunded_amount(self):
        """Get total refunded amount."""
        if not self.refunds:
            return 0.0
        return sum(refund.amount for refund in self.refunds if refund.status == PaymentStatus.COMPLETED)

    @property
    def remaining_refundable_amount(self):
        """Get amount that can still be refunded."""
        return self.amount - self.refunded_amount if self.is_refundable else 0.0

    def can_refund_amount(self, amount: float) -> bool:
        """Check if a specific amount can be refunded."""
        if not self.is_refundable:
            return False
        return amount <= self.remaining_refundable_amount

    def validate_refund(self, amount: float = None) -> bool:
        """Validate if payment can be refunded."""
        if not self.is_refundable:
            return False
        if amount is not None and not self.can_refund_amount(amount):
            return False
        return True