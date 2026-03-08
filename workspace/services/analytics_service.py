import redis
import json
from datetime import datetime, timedelta
from collections import defaultdict
from config import settings


class AnalyticsService:
    def __init__(self):
        self.redis_client = redis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)
        self.click_prefix = "clicks:"
        self.stats_prefix = "stats:"

    def record_click(self, short_code: str, request):
        """Record a click for a short URL"""
        # Record click timestamp
        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        
        # Store click with timestamp
        self.redis_client.lpush(f"{self.click_prefix}{short_code}", timestamp)
        
        # Keep only last 1000 clicks
        self.redis_client.ltrim(f"{self.click_prefix}{short_code}", 0, 999)
        
        # Update daily/hourly stats
        self._update_stats(short_code, timestamp)

    def _update_stats(self, short_code: str, timestamp: str):
        """Update daily and hourly statistics"""
        dt = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
        
        # Update daily stats
        daily_key = f"{self.stats_prefix}{short_code}:daily:{dt.strftime('%Y-%m-%d')}"
        self.redis_client.incr(daily_key)
        self.redis_client.expire(daily_key, 2592000)  # 30 days
        
        # Update hourly stats
        hourly_key = f"{self.stats_prefix}{short_code}:hourly:{dt.strftime('%Y-%m-%d %H')}"
        self.redis_client.incr(hourly_key)
        self.redis_client.expire(hourly_key, 2592000)  # 30 days

    def get_click_stats(self, short_code: str) -> dict:
        """Get click statistics for a short URL"""
        # Get total clicks
        total_clicks = self.redis_client.llen(f"{self.click_prefix}{short_code}")
        
        # Get daily clicks
        daily_clicks = defaultdict(int)
        
        # Get hourly clicks
        hourly_clicks = defaultdict(int)
        
        # For simplicity, returning placeholder data
        # In a real implementation, you would query Redis for actual data
        return {
            "total_clicks": total_clicks,
            "daily_clicks": dict(daily_clicks),
            "hourly_clicks": dict(hourly_clicks)
        }