# app/schemas/payment.py
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from enum import Enum
from decimal import Decimal

class PaymentStatus(str, Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"

class PaymentType(str, Enum):
    BOOKING = "BOOKING"
    REFUND = "REFUND"

class RefundReason(str, Enum):
    DUPLICATE = "duplicate"
    FRAUDULENT = "fraudulent"
    REQUESTED_BY_CUSTOMER = "requested_by_customer"

class PaymentBase(BaseModel):
    amount: float = Field(..., gt=0)
    currency: str = Field(default="MYR")

    @field_validator('amount')
    @classmethod
    def validate_amount(cls, v: float) -> float:
        if v <= 0:
            raise ValueError('Amount must be greater than 0')
        return round(v, 2)

class PaymentCreate(PaymentBase):
    booking_id: UUID
    payment_type: PaymentType = PaymentType.BOOKING

class PaymentUpdate(BaseModel):
    status: PaymentStatus
    stripe_payment_intent_id: Optional[str] = None
    stripe_refund_id: Optional[str] = None

class PaymentResponse(PaymentBase):
    id: UUID
    booking_id: UUID
    payer_id: UUID
    recipient_id: UUID
    status: PaymentStatus
    payment_type: PaymentType
    stripe_payment_intent_id: Optional[str]
    stripe_refund_id: Optional[str]
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True

class PaymentIntent(BaseModel):
    client_secret: str
    payment_id: UUID

class RefundCreate(BaseModel):
    payment_id: UUID
    amount: Optional[float] = None  # If None, full refund
    reason: RefundReason = Field(
        ...,
        description="Reason for refund: duplicate, fraudulent, or requested_by_customer"
    )

    @field_validator('amount')
    @classmethod
    def validate_refund_amount(cls, v: Optional[float]) -> Optional[float]:
        if v is not None:
            if v <= 0:
                raise ValueError('Refund amount must be greater than 0')
            return round(v, 2)
        return v

class RefundResponse(BaseModel):
    id: UUID
    booking_id: UUID
    payment_id: UUID
    amount: float
    currency: str
    status: PaymentStatus
    payment_type: PaymentType = PaymentType.REFUND
    stripe_refund_id: Optional[str]
    reason: RefundReason
    created_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True

class PaymentHistoryResponse(BaseModel):
    id: UUID
    booking_id: UUID
    amount: float
    currency: str
    payment_type: PaymentType
    status: PaymentStatus
    created_at: datetime
    completed_at: Optional[datetime]
    booking_service_type: str
    booking_start_date: datetime
    booking_end_date: datetime
    caregiver_name: str
    pet_name: str

    class Config:
        from_attributes = True

class PaymentSummary(BaseModel):
    total_payments: int
    total_amount: float
    currency: str
    completed_payments: int
    refunded_payments: int
    failed_payments: int
    pending_payments: int

class PaymentListResponse(BaseModel):
    items: List[PaymentResponse]
    total: int
    summary: PaymentSummary

    class Config:
        from_attributes = True

class RefundListResponse(BaseModel):
    items: List[RefundResponse]
    total: int
    total_refunded_amount: float
    currency: str

    class Config:
        from_attributes = True

class TransactionType(str, Enum):
    PAYMENT = "PAYMENT"
    REFUND = "REFUND"
    PAYOUT = "PAYOUT"
    FEE = "FEE"

class TransactionStatus(str, Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    PENDING = "PENDING"
    CANCELLED = "CANCELLED"

class TransactionResponse(BaseModel):
    id: UUID
    booking_id: UUID
    transaction_type: TransactionType
    amount: float
    currency: str
    status: TransactionStatus
    created_at: datetime
    completed_at: Optional[datetime]
    description: Optional[str]
    metadata: Optional[dict]

    class Config:
        from_attributes = True

class TransactionListResponse(BaseModel):
    items: List[TransactionResponse]
    total: int
    total_amount: float
    currency: str

    class Config:
        from_attributes = True

class PaymentReceiptResponse(PaymentResponse):
    receipt_url: Optional[str]
    receipt_number: Optional[str]
    fee_details: Optional[dict]
    payment_method_details: Optional[dict]

    class Config:
        from_attributes = True

class PaymentMethodResponse(BaseModel):
    id: str
    type: str
    last4: Optional[str]
    exp_month: Optional[int]
    exp_year: Optional[int]
    brand: Optional[str]

    class Config:
        from_attributes = True

class PaymentErrorResponse(BaseModel):
    error_code: str
    error_message: str
    created_at: datetime
    payment_id: Optional[UUID]
    booking_id: Optional[UUID]
    detailed_message: Optional[str]

    class Config:
        from_attributes = True