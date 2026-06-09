"""
FinSight AI — Redis Connection Manager
Async Redis client for caching, rate limiting, and pub/sub.
"""

from typing import Any

import redis.asyncio as aioredis
import structlog

from app.config import get_settings

logger = structlog.get_logger()
settings = get_settings()


class RedisManager:
    """Manages Redis connections with async support."""

    def __init__(self) -> None:
        self._client: aioredis.Redis | None = None

    async def connect(self) -> None:
        """Establish Redis connection."""
        self._client = aioredis.from_url(
            settings.effective_redis_url,
            encoding="utf-8",
            decode_responses=True,
            max_connections=20,
        )
        try:
            await self._client.ping()
            logger.info("Redis connection established")
        except Exception as e:
            logger.warning("Redis connection failed, continuing without cache", error=str(e))
            self._client = None

    async def disconnect(self) -> None:
        """Close Redis connection."""
        if self._client:
            await self._client.close()
            logger.info("Redis connection closed")

    @property
    def client(self) -> aioredis.Redis | None:
        return self._client

    async def get(self, key: str) -> str | None:
        """Get a value from Redis."""
        if not self._client:
            return None
        try:
            return await self._client.get(key)
        except Exception:
            return None

    async def set(
        self, key: str, value: str, expire_seconds: int = 3600
    ) -> bool:
        """Set a value in Redis with TTL."""
        if not self._client:
            return False
        try:
            await self._client.set(key, value, ex=expire_seconds)
            return True
        except Exception:
            return False

    async def delete(self, key: str) -> bool:
        """Delete a key from Redis."""
        if not self._client:
            return False
        try:
            await self._client.delete(key)
            return True
        except Exception:
            return False

    async def increment(self, key: str, expire_seconds: int = 60) -> int:
        """Increment a counter (used for rate limiting)."""
        if not self._client:
            return 0
        try:
            pipe = self._client.pipeline()
            pipe.incr(key)
            pipe.expire(key, expire_seconds)
            results = await pipe.execute()
            return results[0]
        except Exception:
            return 0

    async def get_json(self, key: str) -> Any | None:
        """Get a JSON value from Redis."""
        import orjson
        raw = await self.get(key)
        if raw:
            return orjson.loads(raw)
        return None

    async def set_json(
        self, key: str, value: Any, expire_seconds: int = 3600
    ) -> bool:
        """Set a JSON value in Redis."""
        import orjson
        return await self.set(key, orjson.dumps(value).decode(), expire_seconds)


# Singleton instance
redis_manager = RedisManager()
