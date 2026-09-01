"""One pooled Redis client for the whole process.

Every caller previously built its own client with `redis.from_url` and closed it
again, which meant a full TCP connect and AUTH handshake per rate-limited request and
per metrics scrape. `ConnectionPool` reuses connections instead, and holding a single
client lets the lifespan close it once on shutdown.

The accessors take the app rather than reading a global so that tests, the metrics
collector and the rate limiter all resolve the same instance.
"""

import redis.asyncio as redis
from fastapi import FastAPI

from app.config import settings

STATE_ATTRIBUTE = "redis_client"


def create_redis_client() -> redis.Redis:
    return redis.from_url(
        settings.redis_url,
        max_connections=settings.redis_max_connections,
        socket_connect_timeout=settings.redis_socket_timeout_seconds,
        socket_timeout=settings.redis_socket_timeout_seconds,
        health_check_interval=30,
        retry_on_timeout=True,
    )


def set_redis_client(app: FastAPI, client: redis.Redis) -> None:
    setattr(app.state, STATE_ATTRIBUTE, client)


def get_redis_client(app: FastAPI) -> redis.Redis:
    """Return the pooled client, creating one if the lifespan has not run.

    The fallback exists for tests and for any entry point that mounts the app
    without its lifespan. It is deliberately cached on `app.state` so the fallback
    path cannot become a per-request client by accident.
    """
    client = getattr(app.state, STATE_ATTRIBUTE, None)
    if client is None:
        client = create_redis_client()
        set_redis_client(app, client)
    return client


async def close_redis_client(app: FastAPI) -> None:
    client = getattr(app.state, STATE_ATTRIBUTE, None)
    if client is not None:
        await client.aclose()
        setattr(app.state, STATE_ATTRIBUTE, None)
