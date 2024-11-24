# app/utils/stripe.py
from fastapi import HTTPException
from stripe.error import StripeError, CardError, InvalidRequestError
import stripe
from app.core.config import settings, ErrorMessage
from typing import Optional, Dict, Any, List
from decimal import Decimal
from datetime import datetime

stripe.api_key = settings.STRIPE_SECRET_KEY

class StripeService:
    @staticmethod
    async def create_payment_intent(
        amount: float,
        currency: str,
        metadata: Optional[Dict[str, str]] = None,
        application_fee_amount: Optional[int] = None,
        transfer_data: Optional[Dict[str, Any]] = None
    ) -> stripe.PaymentIntent:
        """Create a Stripe PaymentIntent."""
        try:
            payment_data = {
                "amount": int(amount * 100),  # Convert to cents
                "currency": currency.lower(),
                "metadata": metadata or {},
                "automatic_payment_methods": {"enabled": True}
            }

            if application_fee_amount:
                payment_data["application_fee_amount"] = application_fee_amount

            if transfer_data:
                payment_data["transfer_data"] = transfer_data

            return stripe.PaymentIntent.create(**payment_data)
        except CardError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Card error: {str(e)}"
            )
        except StripeError as e:
            raise HTTPException(
                status_code=400,
                detail=f"{ErrorMessage.STRIPE_ERROR}: {str(e)}"
            )

    @staticmethod
    async def create_refund(
        payment_intent_id: str,
        amount: Optional[float] = None,
        reason: Optional[str] = None
    ) -> stripe.Refund:
        """Create a refund for a payment."""
        try:
            refund_data = {
                "payment_intent": payment_intent_id,
                "reason": reason or "requested_by_customer"
            }
            if amount:
                refund_data["amount"] = int(amount * 100)
            return stripe.Refund.create(**refund_data)
        except StripeError as e:
            raise HTTPException(
                status_code=400,
                detail=f"{ErrorMessage.REFUND_FAILED}: {str(e)}"
            )

    @staticmethod
    async def verify_webhook_signature(
        payload: bytes,
        sig_header: str,
        webhook_secret: str
    ) -> stripe.Event:
        """Verify Stripe webhook signature."""
        try:
            return stripe.Webhook.construct_event(
                payload,
                sig_header,
                webhook_secret
            )
        except (stripe.error.SignatureVerificationError, ValueError) as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid webhook signature: {str(e)}"
            )

    @staticmethod
    def calculate_application_fee(amount: float) -> int:
        """Calculate platform fee in cents."""
        fee_percentage = float(settings.STRIPE_PLATFORM_FEE_PERCENT)
        fee_amount = amount * (fee_percentage / 100)
        return int(fee_amount * 100)  # Convert to cents

    @staticmethod
    async def create_connect_account(
        email: str,
        country: str,
        business_type: str = "individual",
        business_profile: Optional[Dict[str, Any]] = None
    ) -> stripe.Account:
        """Create a Stripe Connect account for caregivers."""
        try:
            account_data = {
                "type": "express",
                "country": country,
                "email": email,
                "business_type": business_type,
                "capabilities": {
                    "card_payments": {"requested": True},
                    "transfers": {"requested": True}
                }
            }
            
            if business_profile:
                account_data["business_profile"] = business_profile

            return stripe.Account.create(**account_data)
        except StripeError as e:
            raise HTTPException(
                status_code=400,
                detail=f"{ErrorMessage.ACCOUNT_CREATION_FAILED}: {str(e)}"
            )

    @staticmethod
    async def create_account_link(
        account_id: str,
        refresh_url: str,
        return_url: str,
        type: str = "account_onboarding"
    ) -> stripe.AccountLink:
        """Create an account link for Connect onboarding."""
        try:
            return stripe.AccountLink.create(
                account=account_id,
                refresh_url=refresh_url,
                return_url=return_url,
                type=type
            )
        except StripeError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to create account link: {str(e)}"
            )

    @staticmethod
    async def create_transfer(
        amount: float,
        destination: str,
        currency: str = settings.CURRENCY,
        transfer_group: Optional[str] = None
    ) -> stripe.Transfer:
        """Create a transfer to a connected account."""
        try:
            transfer_data = {
                "amount": int(amount * 100),
                "currency": currency.lower(),
                "destination": destination
            }
            
            if transfer_group:
                transfer_data["transfer_group"] = transfer_group

            return stripe.Transfer.create(**transfer_data)
        except StripeError as e:
            raise HTTPException(
                status_code=400,
                detail=f"{ErrorMessage.PAYOUT_FAILED}: {str(e)}"
            )

    @staticmethod
    async def retrieve_balance_transactions(
        limit: int = 100,
        starting_after: Optional[str] = None,
        type: Optional[str] = None
    ) -> List[stripe.BalanceTransaction]:
        """Retrieve balance transactions."""
        try:
            params = {"limit": limit}
            if starting_after:
                params["starting_after"] = starting_after
            if type:
                params["type"] = type

            return stripe.BalanceTransaction.list(**params)
        except StripeError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to retrieve balance transactions: {str(e)}"
            )

    @staticmethod
    async def get_payment_method(payment_method_id: str) -> stripe.PaymentMethod:
        """Retrieve a payment method."""
        try:
            return stripe.PaymentMethod.retrieve(payment_method_id)
        except StripeError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to retrieve payment method: {str(e)}"
            )

    @staticmethod
    async def create_payment_method(
        type: str,
        card: Dict[str, Any],
        billing_details: Optional[Dict[str, Any]] = None
    ) -> stripe.PaymentMethod:
        """Create a payment method."""
        try:
            payment_method_data = {
                "type": type,
                "card": card
            }
            
            if billing_details:
                payment_method_data["billing_details"] = billing_details

            return stripe.PaymentMethod.create(**payment_method_data)
        except StripeError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to create payment method: {str(e)}"
            )

    @staticmethod
    async def verify_microdeposits(
        account_id: str,
        amounts: List[int]
    ) -> Any:
        """Verify bank account microdeposits for Connect accounts."""
        try:
            return stripe.Account.verify_external_account(
                account_id,
                amounts=amounts
            )
        except StripeError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to verify microdeposits: {str(e)}"
            )

    @staticmethod
    def format_stripe_error(error: StripeError) -> str:
        """Format Stripe error messages for consistent error handling."""
        if isinstance(error, CardError):
            return f"Card error: {error.error.message}"
        elif isinstance(error, InvalidRequestError):
            return f"Invalid request: {error.error.message}"
        else:
            return str(error)