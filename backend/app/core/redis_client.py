import redis.asyncio as aioredis
from redis.asyncio import Redis
from typing import Optional, Any
import json
import logging
import ssl
from app.config import settings

logger = logging.getLogger(__name__)

class RedisClient:
    """Async Redis client for Redis Cloud (SSL enabled)."""

    def __init__(self):
        self._client: Optional[Redis] = None

    async def connect(self) -> None:
        """Connect to Redis Cloud.

        For `rediss://` URLs this will try to provide an SSL context first;
        if the redis driver does not accept the `ssl` kwarg it will try
        `ssl_cert_reqs=ssl.CERT_REQUIRED`. If both attempts fail it will
        attempt an insecure fallback (swap `rediss://` -> `redis://`) and
        otherwise continue without Redis (degraded mode).
        """
        if not settings.REDIS_URL:
            logger.info("Redis URL not provided; skipping Redis initialization")
            return

        # Use the normalized DSN from settings (may include ssl_cert_reqs)
        url = settings.redis_dsn

        # Primary connection attempt
        try:
            if url.startswith("rediss://"):
                # TLS/SSL URL - try with SSL context
                ssl_ctx = ssl.create_default_context()
                ssl_ctx.check_hostname = True
                ssl_ctx.verify_mode = ssl.CERT_REQUIRED
                try:
                    self._client = aioredis.from_url(
                        url,
                        encoding="utf-8",
                        decode_responses=True,
                        max_connections=50,
                        ssl=ssl_ctx,
                    )
                except TypeError as te:
                    # Some redis-py versions don't accept `ssl`; try without SSL context
                    msg = str(te)
                    if "unexpected keyword argument 'ssl'" in msg or "ssl" in msg:
                        self._client = aioredis.from_url(
                            url,
                            encoding="utf-8",
                            decode_responses=True,
                            max_connections=50,
                        )
                    else:
                        raise
            else:
                # Non-TLS URL (redis://) - no SSL
                self._client = aioredis.from_url(
                    url,
                    encoding="utf-8",
                    decode_responses=True,
                    max_connections=50,
                )

            if self._client:
                await self._client.ping()
            logger.info("✅ Redis Cloud connection established successfully")
            return
        except Exception as e:
            logger.error(f"Initial Redis connection attempt failed: {e}")

        # Insecure fallback: convert rediss:// -> redis:// and try again
        try:
            if url.startswith("redis://"):
                fallback = "redis://" + url[len("redis://"):]
                logger.info("Attempting insecure fallback to Redis (redis://)")
                self._client = aioredis.from_url(
                    fallback,
                    encoding="utf-8",
                    decode_responses=True,
                    max_connections=50,
                )
                if self._client:
                    await self._client.ping()
                logger.warning(
                    "Connected to Redis using insecure fallback (redis://). "
                    "This disables TLS and should not be used in production."
                )
                return
        except Exception as e2:
            logger.error(f"Fallback Redis connection failed: {e2}")

        logger.error("❌ Failed to connect to Redis Cloud; continuing without Redis")
        self._client = None

    async def disconnect(self) -> None:
        """Close Redis connection."""
        if self._client:
            await self._client.close()
            logger.info("Redis connection closed")

    @property
    def client(self) -> Redis:
        if not self._client:
            raise RuntimeError("Redis client not initialized. Call connect() first.")
        return self._client

    async def get(self, key: str) -> Optional[Any]:
        try:
            value = await self.client.get(key)
            return json.loads(value) if value else None
        except Exception as e:
            logger.error(f"Error getting key {key}: {e}")
            return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        try:
            serialized = json.dumps(value)
            if ttl:
                await self.client.setex(key, ttl, serialized)
            else:
                await self.client.set(key, serialized)
            return True
        except Exception as e:
            logger.error(f"Error setting key {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        try:
            await self.client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Error deleting key {key}: {e}")
            return False

    async def exists(self, key: str) -> bool:
        try:
            return await self.client.exists(key) > 0
        except Exception as e:
            logger.error(f"Error checking key {key}: {e}")
            return False

    async def set_hash(self, key: str, mapping: dict, ttl: Optional[int] = None) -> bool:
        try:
            await self.client.hset(key, mapping=mapping)
            if ttl:
                await self.client.expire(key, ttl)
            return True
        except Exception as e:
            logger.error(f"Error setting hash {key}: {e}")
            return False

    async def get_hash(self, key: str) -> Optional[dict]:
        try:
            return await self.client.hgetall(key)
        except Exception as e:
            logger.error(f"Error getting hash {key}: {e}")
            return None

    async def increment(self, key: str, amount: int = 1) -> int:
        try:
            return await self.client.incrby(key, amount)
        except Exception as e:
            logger.error(f"Error incrementing key {key}: {e}")
            return 0

# Global instance
redis_client = RedisClient()
