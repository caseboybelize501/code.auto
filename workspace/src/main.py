from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="Event Booking API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mock data structures
users = {}
events = {}
bookings = {}

# Pydantic models
class User(BaseModel):
    id: str
    name: str
    email: str
    phone: str

class Event(BaseModel):
    id: str
    name: str
    description: str
    start_time: datetime
    end_time: datetime
    venue: str
    total_capacity: int
    available_seats: int
    is_recurring: bool
    recurrence_pattern: Optional[str] = None
    ticket_price: float
    status: str = "active"

class Booking(BaseModel):
    id: str
    user_id: str
    event_id: str
    seat_numbers: List[str]
    total_amount: float
    booking_time: datetime
    status: str = "confirmed"
    payment_status: str = "pending"

# Mock database functions
def get_user(user_id: str):
    return users.get(user_id)

def get_event(event_id: str):
    return events.get(event_id)

def create_event(event: Event):
    events[event.id] = event
    return event

# API routes
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/users")
async def create_user(user: User):
    users[user.id] = user
    logger.info(f"User created: {user.id}")
    return user

@app.post("/events")
async def create_event_endpoint(event: Event):
    try:
        created_event = create_event(event)
        logger.info(f"Event created: {event.id}")
        return created_event
    except Exception as e:
        logger.error(f"Error creating event: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/events/{event_id}")
async def get_event_endpoint(event_id: str):
    event = get_event(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event

@app.post("/bookings")
async def create_booking(booking: Booking):
    try:
        event = get_event(booking.event_id)
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        
        # Check seat availability
        if len(booking.seat_numbers) > event.available_seats:
            raise HTTPException(status_code=400, detail="Not enough seats available")
        
        # Update event capacity
        event.available_seats -= len(booking.seat_numbers)
        bookings[booking.id] = booking
        
        logger.info(f"Booking created: {booking.id}")
        return booking
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating booking: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/bookings/{booking_id}")
async def get_booking(booking_id: str):
    booking = bookings.get(booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    return booking

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)