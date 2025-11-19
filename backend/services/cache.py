"""
Caching service for API responses
"""
import time
from typing import Dict, Any, Optional


class CacheService:
    """Simple in-memory cache with TTL support"""
    
    def __init__(self, ttl: int = 300):
        """
        Initialize cache service
        
        Args:
            ttl: Time to live in seconds (default: 300s = 5 minutes)
        """
        self.ttl = ttl
        self._cache: Dict[str, Dict[str, Any]] = {}
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache if it exists and is not expired
        
        Args:
            key: Cache key
            
        Returns:
            Cached value if valid, None otherwise
        """
        if key not in self._cache:
            return None
        
        cached = self._cache[key]
        current_time = time.time()
        cache_age = current_time - cached.get("timestamp", 0)
        
        if cache_age < self.ttl:
            return cached.get("data")
        
        # Cache expired, remove it
        del self._cache[key]
        return None
    
    def set(self, key: str, value: Any) -> None:
        """
        Store value in cache with current timestamp
        
        Args:
            key: Cache key
            value: Value to cache
        """
        self._cache[key] = {
            "data": value,
            "timestamp": time.time()
        }
    
    def clear(self) -> None:
        """Clear all cached data"""
        self._cache.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics
        
        Returns:
            Dictionary with cache stats
        """
        current_time = time.time()
        valid_entries = 0
        expired_entries = 0
        
        for cached in self._cache.values():
            cache_age = current_time - cached.get("timestamp", 0)
            if cache_age < self.ttl:
                valid_entries += 1
            else:
                expired_entries += 1
        
        return {
            "total_entries": len(self._cache),
            "valid_entries": valid_entries,
            "expired_entries": expired_entries,
            "ttl_seconds": self.ttl,
            "keys": list(self._cache.keys())
        }


# Global cache instances
CACHE_TTL_COINS = 60  # Cache top 50 coins list for 1 minute
CACHE_TTL_COIN_DETAIL = 300  # Cache individual coin details for 5 minutes

coins_cache = CacheService(ttl=CACHE_TTL_COINS)
coin_detail_cache = CacheService(ttl=CACHE_TTL_COIN_DETAIL)
