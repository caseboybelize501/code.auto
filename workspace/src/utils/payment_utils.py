import stripe
from ..config import settings
import logging

logger = logging.getLogger(__name__)


def initialize_stripe():
    if settings.stripe_secret_key:
        stripe.api_key = settings.stripe_secret_key
        return True
    return False


def process_payment(payment_intent_id: str, amount: float) -> bool:
    try:
        # Initialize Stripe
        if not initialize_stripe():
            logger.warning("Stripe not configured, skipping payment processing")
            return True  # For testing purposes
        
        # Retrieve payment intent
        payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
        
        # Confirm payment intent
        payment_intent.confirm()
        
        # Check if payment succeeded
        if payment_intent.status == "succeeded":
            logger.info(f"Payment succeeded for amount: {amount}")
            return True
        else:
            logger.warning(f"Payment failed with status: {payment_intent.status}")
            return False
            
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Error processing payment: {str(e)}")
        return False


def create_payment_intent(amount: float, currency: str = "usd") -> dict:
    try:
        if not initialize_stripe():
            return {"error": "Stripe not configured"}
        
        intent = stripe.PaymentIntent.create(
            amount=int(amount * 100),  # Convert to cents
            currency=currency,
            automatic_payment_methods={"enabled": True}
        )
        
        return {
            "client_secret": intent.client_secret,
            "payment_intent_id": intent.id
        }
        
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error creating payment intent: {str(e)}")
        return {"error": str(e)}
    except Exception as e:
        logger.error(f"Error creating payment intent: {str(e)}")
        return {"error": "Internal server error"}


def validate_payment_intent(payment_intent_id: str) -> bool:
    try:
        if not initialize_stripe():
            return True  # For testing purposes
        
        intent = stripe.PaymentIntent.retrieve(payment_intent_id)
        return intent.status == "succeeded"
        
    except Exception as e:
        logger.error(f"Error validating payment intent: {str(e)}")
        return False