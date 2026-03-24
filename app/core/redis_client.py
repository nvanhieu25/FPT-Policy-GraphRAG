import redis.asyncio as aioredis
from app.core.config import settings

# Module-level connection pool (initialized on first call)
_redis_pool: aioredis.ConnectionPool | None = None


def get_redis_pool() -> aioredis.ConnectionPool:
    """Return the shared Redis connection pool, creating it if necessary."""
    global _redis_pool
    if _redis_pool is None:
        _redis_pool = aioredis.ConnectionPool.from_url(
            f"redis://{settings.redis_host}:{settings.redis_port}/{settings.redis_db}",
            decode_responses=False,  # We store binary (pickled) data
            max_connections=20,
        )
    return _redis_pool


def get_redis_client() -> aioredis.Redis:
    """Return an async Redis client backed by the shared connection pool."""
    return aioredis.Redis(connection_pool=get_redis_pool())


async def close_redis_pool() -> None:
    """Gracefully close the Redis connection pool (call on app shutdown)."""
    global _redis_pool
    if _redis_pool is not None:
        await _redis_pool.disconnect()
        _redis_pool = None
