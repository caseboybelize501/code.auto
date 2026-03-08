from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List
from config import settings


class RateLimitingService:
    def __init__(self):
        self.requests: Dict[str, List[datetime]] = defaultdict(list)
        
    def is_allowed(self, client_ip: str) -> bool:
        now = datetime.now()
        
        # Remove old requests outside the time window
        self.requests[client_ip] = [
            req_time for req_time in self.requests[client_ip]
            if req_time > now - timedelta(seconds=settings.RATE_LIMIT_WINDOW_SECONDS)
        ]
        
        # Check if request count exceeds limit
        if len(self.requests[client_ip]) >= settings.RATE_LIMIT_MAX_REQUESTS:
            return False
        
        # Add new request
        self.requests[client_ip].append(now)
        return True
        
    def get_remaining_requests(self, client_ip: str) -> int:
        now = datetime.now()
        
        # Remove old requests
        self.requests[client_ip] = [
            req_time for req_time in self.requests[client_ip]
            if req_time > now - timedelta(seconds=settings.RATE_LIMIT_WINDOW_SECONDS)
        ]
        
        return settings.RATE_LIMIT_MAX_REQUESTS - len(self.requests[client_ip])
        
    def reset_client_requests(self, client_ip: str):
        self.requests[client_ip] = []
