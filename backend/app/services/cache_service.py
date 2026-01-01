from typing import Optional, Any
import hashlib
import json
import logging
from app.core.redis_client import redis_client
from app.config import settings
from app.utils.exceptions import CacheException

logger = logging.getLogger(__name__)


class CacheService:
    """Service for caching analysis results."""
    
    def __init__(self):
        self.ttl = settings.CACHE_TTL
        self.enabled = settings.CACHE_ENABLED
        self.prefix = "cache:"
    
    def _generate_key(self, repo: str, pr_number: int) -> str:
        """Generate cache key for PR analysis."""
        key_data = f"{repo}:{pr_number}"
        key_hash = hashlib.md5(key_data.encode()).hexdigest()
        return f"{self.prefix}pr:{key_hash}"
    
    async def get_analysis(self, repo: str, pr_number: int) -> Optional[dict]:
        """Get cached analysis results."""
        if not self.enabled:
            return None
        
        try:
            # Check if Redis client is connected
            if not redis_client._client:
                logger.debug(f"Redis not connected, skipping cache lookup for {repo}#{pr_number}")
                return None
            
            key = self._generate_key(repo, pr_number)
            # redis_client.get() already parses JSON, so result is already a dict
            result = await redis_client.get(key)
            
            if result:
                logger.info(f"Cache hit for {repo}#{pr_number}")
                return result  # Already parsed by redis_client.get()
            
            logger.info(f"Cache miss for {repo}#{pr_number}")
            return None
            
        except RuntimeError as e:
            # Redis client not initialized
            logger.debug(f"Redis client not initialized: {e}")
            return None
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None
    
    async def set_analysis(
        self, 
        repo: str, 
        pr_number: int, 
        data: dict,
        ttl: Optional[int] = None
    ) -> bool:
        """Cache analysis results."""
        if not self.enabled:
            return False
        
        try:
            # Check if Redis client is connected
            if not redis_client._client:
                logger.debug(f"Redis not connected, skipping cache set for {repo}#{pr_number}")
                return False
            
            key = self._generate_key(repo, pr_number)
            cache_ttl = ttl or self.ttl
            
            # redis_client.set() already serializes to JSON, so pass dict directly
            success = await redis_client.set(key, data, ttl=cache_ttl)
            
            if success:
                logger.info(f"Cached analysis for {repo}#{pr_number} (TTL: {cache_ttl}s)")
            
            return success
            
        except RuntimeError as e:
            # Redis client not initialized
            logger.debug(f"Redis client not initialized: {e}")
            return False
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    async def invalidate_analysis(self, repo: str, pr_number: int) -> bool:
        """Invalidate cached analysis."""
        try:
            key = self._generate_key(repo, pr_number)
            success = await redis_client.delete(key)
            
            if success:
                logger.info(f"Invalidated cache for {repo}#{pr_number}")
            
            return success
            
        except Exception as e:
            logger.error(f"Cache invalidation error: {e}")
            return False


# Global cache service instance
cache_service = CacheService()