"""
Cache Service - Cost Optimization through Response Caching
Reduces API calls by caching frequent queries
"""

import logging
import time
from typing import Dict, Optional, Any
import hashlib

logger = logging.getLogger(__name__)


class ResponseCache:
    """
    Simple in-memory cache for LLM responses

    Cost Optimization:
    - Caches responses to avoid redundant API calls
    - Reduces LLM token usage significantly
    - Configurable TTL for freshness control
    """

    def __init__(self, ttl_seconds: int = 3600, max_size: int = 1000):
        """
        Initialize cache

        Args:
            ttl_seconds: Time-to-live for cache entries (default: 1 hour)
            max_size: Maximum number of entries to store
        """
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.ttl_seconds = ttl_seconds
        self.max_size = max_size
        self.hits = 0
        self.misses = 0

    def _hash_key(self, key: str) -> str:
        """Generate hash for cache key"""
        return hashlib.md5(key.encode()).hexdigest()

    def get(self, key: str) -> Optional[Dict]:
        """
        Get value from cache

        Args:
            key: Cache key (usually the user query)

        Returns:
            Cached value or None if not found/expired
        """
        hashed_key = self._hash_key(key)

        if hashed_key in self.cache:
            entry = self.cache[hashed_key]

            # Check if entry is expired
            if time.time() - entry["timestamp"] < self.ttl_seconds:
                self.hits += 1
                logger.debug(f"Cache hit for key: {key[:50]}...")
                return entry["value"]
            else:
                # Entry expired, remove it
                del self.cache[hashed_key]

        self.misses += 1
        return None

    def set(self, key: str, value: Dict):
        """
        Set value in cache

        Args:
            key: Cache key
            value: Value to cache
        """
        # Evict old entries if cache is full
        if len(self.cache) >= self.max_size:
            self._evict_oldest()

        hashed_key = self._hash_key(key)
        self.cache[hashed_key] = {
            "value": value,
            "timestamp": time.time(),
            "original_key": key[:100]  # Store truncated key for debugging
        }
        logger.debug(f"Cached response for key: {key[:50]}...")

    def _evict_oldest(self):
        """Remove oldest entries to make room"""
        if not self.cache:
            return

        # Sort by timestamp and remove oldest 10%
        sorted_keys = sorted(
            self.cache.keys(),
            key=lambda k: self.cache[k]["timestamp"]
        )

        num_to_remove = max(1, len(sorted_keys) // 10)
        for key in sorted_keys[:num_to_remove]:
            del self.cache[key]

        logger.info(f"Evicted {num_to_remove} cache entries")

    def clear(self):
        """Clear all cache entries"""
        self.cache.clear()
        self.hits = 0
        self.misses = 0
        logger.info("Cache cleared")

    def get_stats(self) -> Dict:
        """Get cache statistics"""
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0

        return {
            "entries": len(self.cache),
            "max_size": self.max_size,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": f"{hit_rate:.1f}%",
            "ttl_seconds": self.ttl_seconds
        }

    def invalidate(self, key: str):
        """Invalidate a specific cache entry"""
        hashed_key = self._hash_key(key)
        if hashed_key in self.cache:
            del self.cache[hashed_key]
            logger.debug(f"Invalidated cache for key: {key[:50]}...")
