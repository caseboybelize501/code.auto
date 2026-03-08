from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

# Mock seat availability data
seat_availability = {}


def validate_seats(event_id: str, seat_numbers: List[str]) -> bool:
    try:
        # Get event's available seats
        event_seats = seat_availability.get(event_id, [])
        
        # Validate seat numbers
        for seat in seat_numbers:
            if seat not in event_seats:
                logger.warning(f"Invalid seat number: {seat} for event {event_id}")
                return False
        
        logger.info(f"All seats validated for event {event_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error validating seats: {str(e)}")
        return False


def update_seat_availability(event_id: str, seat_numbers: List[str]) -> bool:
    try:
        # Get current available seats
        available_seats = seat_availability.get(event_id, [])
        
        # Remove booked seats
        for seat in seat_numbers:
            if seat in available_seats:
                available_seats.remove(seat)
            else:
                logger.warning(f"Seat {seat} not available for event {event_id}")
                
        # Update availability
        seat_availability[event_id] = available_seats
        
        logger.info(f"Updated seat availability for event {event_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error updating seat availability: {str(e)}")
        return False


def get_available_seats(event_id: str) -> List[str]:
    return seat_availability.get(event_id, [])


def initialize_seats(event_id: str, total_seats: List[str]) -> None:
    seat_availability[event_id] = total_seats
    logger.info(f"Initialized seats for event {event_id}")