"""
In-memory rate limiter for per-user download limits.
"""
import time
from collections import defaultdict
from typing import Dict, List
from config.settings import MAX_DOWNLOADS_PER_USER, RATE_LIMIT_WINDOW_MINUTES


class RateLimiter:
    """
    Simple in-memory rate limiter using sliding window.
    """
    
    def __init__(
        self,
        max_requests: int = MAX_DOWNLOADS_PER_USER,
        window_minutes: int = RATE_LIMIT_WINDOW_MINUTES
    ):
        """
        Initialize rate limiter.
        
        Args:
            max_requests: Maximum requests per window
            window_minutes: Time window in minutes
        """
        self.max_requests = max_requests
        self.window_seconds = window_minutes * 60
        self._requests: Dict[int, List[float]] = defaultdict(list)
    
    def _cleanup_old_requests(self, user_id: int) -> None:
        """Remove expired timestamps for a user."""
        current_time = time.time()
        cutoff = current_time - self.window_seconds
        self._requests[user_id] = [
            ts for ts in self._requests[user_id]
            if ts > cutoff
        ]
    
    def is_allowed(self, user_id: int) -> bool:
        """
        Check if user is allowed to make a request.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            True if allowed, False if rate limited
        """
        self._cleanup_old_requests(user_id)
        return len(self._requests[user_id]) < self.max_requests
    
    def record_request(self, user_id: int) -> None:
        """
        Record a request for a user.
        
        Args:
            user_id: Telegram user ID
        """
        self._cleanup_old_requests(user_id)
        self._requests[user_id].append(time.time())
    
    def get_remaining(self, user_id: int) -> int:
        """
        Get remaining requests for a user.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            Number of remaining requests in current window
        """
        self._cleanup_old_requests(user_id)
        return max(0, self.max_requests - len(self._requests[user_id]))
    
    def get_reset_time(self, user_id: int) -> int:
        """
        Get seconds until rate limit resets.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            Seconds until oldest request expires (0 if not limited)
        """
        self._cleanup_old_requests(user_id)
        if not self._requests[user_id]:
            return 0
        
        oldest = min(self._requests[user_id])
        reset_at = oldest + self.window_seconds
        remaining = int(reset_at - time.time())
        return max(0, remaining)


# Global rate limiter instance
rate_limiter = RateLimiter()
