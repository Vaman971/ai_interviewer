"""Shared async Redis client for the AI Interviewer backend.

Provides a singleton Redis connection that is opened on app startup
and closed on shutdown via the FastAPI lifespan.
"""

import logging
from redis.asyncio import Redis, from_url
from backend.app.config import get_settings

logger = logging.getLogger(__name__)

_redis: Redis | None = None


async def get_redis() -> Redis:
    """Return the shared Redis client, initialising it on first call.

    Returns:
        The active async Redis client instance.
    """
    global _redis
    if _redis is None:
        settings = get_settings()
        _redis = from_url(settings.redis_url, decode_responses=True)
        logger.info("Redis connection established: %s", settings.redis_url)
    return _redis


async def close_redis() -> None:
    """Close the shared Redis connection gracefully."""
    global _redis
    if _redis is not None:
        await _redis.aclose()
        _redis = None
        logger.info("Redis connection closed.")
