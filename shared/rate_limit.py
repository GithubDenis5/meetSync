"""Redis-backed rate limiting for the API gateway."""

from __future__ import annotations

import logging
from typing import Any, Optional

import redis.asyncio as aioredis

logger = logging.getLogger("shared.rate_limit")

# Default tiers: (limit, window_seconds)
TIERS: dict[str, tuple[int, int]] = {
    "anonymous": (10, 60),        # 10 requests per minute for unauthenticated
    "authenticated": (120, 60),   # 120 requests per minute for authenticated users
    "auth_strict": (5, 60),       # 5 requests per minute for auth endpoints
}


class RedisRateLimiter:
    """Sliding-window rate limiter using Redis sorted sets."""

    def __init__(self, redis_client: aioredis.Redis) -> None:
        self.redis = redis_client

    async def check(
        self,
        key: str,
        limit: int,
        window: int = 60,
    ) -> bool:
        """Check if the request is within the rate limit.

        Returns True if allowed, False if rate-limited.
        """
        now = _now_ms()
        window_start = now - window * 1000

        pipe = self.redis.pipeline()
        pipe.zremrangebyscore(key, 0, window_start)  # Remove old entries
        pipe.zcard(key)  # Count remaining
        pipe.zadd(key, {str(now): now})  # Add current request
        pipe.expire(key, window * 2)  # TTL
        results = await pipe.execute()

        count = results[1]  # zcard result
        return count <= limit

    async def close(self) -> None:
        await self.redis.close()


def _now_ms() -> int:
    import time
    return int(time.time() * 1000)
