import redis
import uuid
import json
from datetime import datetime, timedelta
from config import settings


class URLService:
    def __init__(self):
        self.redis_client = redis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)
        self.url_prefix = "url:"
        self.alias_prefix = "alias:"
        self.expiry_prefix = "expiry:"

    def generate_short_code(self, custom_alias: str = None) -> str:
        """Generate a unique short code for a URL"""
        if custom_alias:
            # Check if alias already exists
            if self.redis_client.exists(f"{self.alias_prefix}{custom_alias}"):
                raise Exception("Alias already exists")
            return custom_alias
        
        # Generate random code
        while True:
            code = str(uuid.uuid4())[:8]
            if not self.redis_client.exists(f"{self.url_prefix}{code}"):
                return code

    def create_short_url(self, short_code: str, original_url: str, alias: str = None, expires_at: datetime = None):
        """Create a new short URL entry"""
        url_data = {
            "original_url": original_url,
            "created_at": str(datetime.utcnow()),
            "alias": alias,
            "expires_at": str(expires_at) if expires_at else None
        }
        
        # Store URL
        self.redis_client.setex(
            f"{self.url_prefix}{short_code}",
            2592000,  # 30 days expiry
            json.dumps(url_data)
        )
        
        # Store alias mapping if provided
        if alias:
            self.redis_client.setex(
                f"{self.alias_prefix}{alias}",
                2592000,
                short_code
            )
        
        # Store expiry if set
        if expires_at:
            self.redis_client.setex(
                f"{self.expiry_prefix}{short_code}",
                int((expires_at - datetime.utcnow()).total_seconds()),
                "1"
            )

    def get_url_info(self, short_code: str) -> dict:
        """Get URL information by short code"""
        url_data = self.redis_client.get(f"{self.url_prefix}{short_code}")
        if not url_data:
            return None
        
        return json.loads(url_data)

    def get_short_url_by_original(self, original_url: str) -> str:
        """Get existing short URL for an original URL"""
        # This is a simplified implementation
        # In a real system, you might want to store a mapping of original URLs to short codes
        return None

    def delete_short_url(self, short_code: str):
        """Delete a short URL"""
        url_data = self.get_url_info(short_code)
        if url_data and url_data.get('alias'):
            self.redis_client.delete(f"{self.alias_prefix}{url_data['alias']}")
        
        self.redis_client.delete(f"{self.url_prefix}{short_code}")
        self.redis_client.delete(f"{self.expiry_prefix}{short_code}")