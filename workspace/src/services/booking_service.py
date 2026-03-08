from typing import List, Optional
from datetime import datetime
from ..config import settings
from ..utils.seat_utils import validate_seats, update_seat_availability
from ..utils.payment_utils import process_payment
from ..models import Booking, Event, User

logger = logging.getLogger(__name__)


class BookingService:
    def __init__(self):
        self.bookings = {}
        self.waitlist = []

    def create_booking(
        self,
        user_id: str,
        event_id: str,
        seat_numbers: List[str],
        payment_intent_id: Optional[str] = None
    ) -> Booking:
        try:
            # Validate event exists
            event = self.get_event(event_id)
            if not event:
                raise ValueError("Event not found")
            
            # Validate seats
            if not validate_seats(event_id, seat_numbers):
                raise ValueError("Invalid seat selection")
            
            # Check capacity
            if len(seat_numbers) > event.available_seats:
                # Add to waitlist
                self.add_to_waitlist(user_id, event_id, seat_numbers)
                return self.create_waitlist_booking(user_id, event_id, seat_numbers)
            
            # Process payment
            total_amount = len(seat_numbers) * event.ticket_price
            
            if payment_intent_id:
                payment_status = process_payment(payment_intent_id, total_amount)
                if not payment_status:
                    raise ValueError("Payment failed")
            
            # Create booking
            booking = Booking(
                id=f"booking_{datetime.now().timestamp()}",
                user_id=user_id,
                event_id=event_id,
                seat_numbers=seat_numbers,
                total_amount=total_amount,
                booking_time=datetime.now(),
                payment_status="paid" if payment_intent_id else "pending"
            )
            
            # Update seat availability
            update_seat_availability(event_id, seat_numbers)
            
            self.bookings[booking.id] = booking
            logger.info(f"Booking created: {booking.id}")
            
            return booking
            
        except Exception as e:
            logger.error(f"Error creating booking: {str(e)}")
            raise

    def add_to_waitlist(self, user_id: str, event_id: str, seat_numbers: List[str]):
        waitlist_entry = {
            "user_id": user_id,
            "event_id": event_id,
            "seat_numbers": seat_numbers,
            "timestamp": datetime.now()
        }
        self.waitlist.append(waitlist_entry)
        logger.info(f"User {user_id} added to waitlist for event {event_id}")

    def get_event(self, event_id: str):
        # Mock implementation - in real app, this would fetch from DB
        return None

    def create_waitlist_booking(self, user_id: str, event_id: str, seat_numbers: List[str]) -> Booking:
        return Booking(
            id=f"waitlist_booking_{datetime.now().timestamp()}",
            user_id=user_id,
            event_id=event_id,
            seat_numbers=seat_numbers,
            total_amount=len(seat_numbers) * 50.0,  # Mock price
            booking_time=datetime.now(),
            status="waitlisted"
        )

    def get_bookings_by_user(self, user_id: str) -> List[Booking]:
        return [booking for booking in self.bookings.values() if booking.user_id == user_id]

    def get_bookings_by_event(self, event_id: str) -> List[Booking]:
        return [booking for booking in self.bookings.values() if booking.event_id == event_id]

# Global instance
booking_service = BookingService()