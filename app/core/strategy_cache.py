"""Strategy caching system for GTO computations."""

import logging
import time
from typing import Dict, Optional, Any
from collections import OrderedDict

logger = logging.getLogger(__name__)


class StrategyCache:
    """LRU cache for GTO strategy computations."""
    
    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600):
        """
        Initialize strategy cache.
        
        Args:
            max_size: Maximum number of cached entries
            ttl_seconds: Time-to-live for cached entries
        """
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()
        self.access_times: Dict[str, float] = {}
        
        logger.info(f"Strategy cache initialized: max_size={max_size}, ttl={ttl_seconds}s")
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get cached strategy result."""
        try:
            if key not in self.cache:
                return None
            
            # Check TTL
            if self._is_expired(key):
                self._remove_key(key)
                return None
            
            # Update access time and move to end (most recently used)
            self.access_times[key] = time.time()
            self.cache.move_to_end(key)
            
            logger.debug(f"Cache hit for key: {key[:50]}...")
            return self.cache[key]
            
        except Exception as e:
            logger.error(f"Cache get failed for key {key}: {e}")
            return None
    
    def set(self, key: str, value: Dict[str, Any]) -> None:
        """Set cached strategy result."""
        try:
            current_time = time.time()
            
            # If key exists, update it
            if key in self.cache:
                self.cache[key] = value
                self.access_times[key] = current_time
                self.cache.move_to_end(key)
                logger.debug(f"Cache updated for key: {key[:50]}...")
                return
            
            # Check if we need to evict entries
            if len(self.cache) >= self.max_size:
                self._evict_lru()
            
            # Add new entry
            self.cache[key] = value
            self.access_times[key] = current_time
            
            logger.debug(f"Cache set for key: {key[:50]}...")
            
        except Exception as e:
            logger.error(f"Cache set failed for key {key}: {e}")
    
    def _is_expired(self, key: str) -> bool:
        """Check if cache entry is expired."""
        if key not in self.access_times:
            return True
        
        age = time.time() - self.access_times[key]
        return age > self.ttl_seconds
    
    def _remove_key(self, key: str) -> None:
        """Remove key from cache and access times."""
        self.cache.pop(key, None)
        self.access_times.pop(key, None)
    
    def _evict_lru(self) -> None:
        """Evict least recently used entry."""
        if not self.cache:
            return
        
        # Remove oldest entry (at the beginning of OrderedDict)
        oldest_key = next(iter(self.cache))
        self._remove_key(oldest_key)
        logger.debug(f"Evicted LRU entry: {oldest_key[:50]}...")
    
    def cleanup_expired(self) -> int:
        """Remove all expired entries."""
        expired_keys = []
        current_time = time.time()
        
        for key, access_time in self.access_times.items():
            if current_time - access_time > self.ttl_seconds:
                expired_keys.append(key)
        
        for key in expired_keys:
            self._remove_key(key)
        
        if expired_keys:
            logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")
        
        return len(expired_keys)
    
    def clear(self) -> None:
        """Clear all cache entries."""
        self.cache.clear()
        self.access_times.clear()
        logger.info("Cache cleared")
    
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "ttl_seconds": self.ttl_seconds,
            "oldest_entry_age": self._get_oldest_entry_age(),
            "memory_usage_estimate": self._estimate_memory_usage()
        }
    
    def _get_oldest_entry_age(self) -> Optional[float]:
        """Get age of oldest entry in seconds."""
        if not self.access_times:
            return None
        
        oldest_time = min(self.access_times.values())
        return time.time() - oldest_time
    
    def _estimate_memory_usage(self) -> int:
        """Estimate memory usage in bytes (rough approximation)."""
        # Very rough estimation - each entry is approximately:
        # - Key: ~100 bytes average
        # - Value: ~1KB average (decision + metrics)
        return len(self.cache) * 1100
