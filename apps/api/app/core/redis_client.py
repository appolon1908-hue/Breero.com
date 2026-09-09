"""One pooled Redis client for the whole process.

Every caller previously built its own client with `redis.from_url` and closed it
again, which meant a full TCP connect and AUTH handshake per rate-limited request and
per metrics scrape. `ConnectionPool` reuses connections instead, and holding a single
client lets the lifespan close it once on shutdown.

The accessors take the app rather than reading a global so that tests, the metrics
collector and the rate limiter all resolve the same instance.
"""

import asyncio

import redis.asyncio as redis
from fastapi import FastAPI

from app.config import settings

STATE_ATTRIBUTE = "redis_client"
STATE_LOOP_ATTRIBUTE = "redis_client_loop"


def create_redis_client() -> redis.Redis:
    return redis.from_url(
        settings.redis_url,
        max_connections=settings.redis_max_connections,
        socket_connect_timeout=settings.redis_socket_timeout_seconds,
        socket_timeout=settings.redis_socket_timeout_seconds,
        health_check_interval=30,
        retry_on_timeout=True,
    )


def _running_loop() -> asyncio.AbstractEventLoop | None:
    try:
        return asyncio.get_running_loop()
    except RuntimeError:
        return None


def set_redis_client(app: FastAPI, client: redis.Redis) -> None:
    setattr(app.state, STATE_ATTRIBUTE, client)
    # Remember which loop owns it. An asyncio connection pool binds to the loop that
    # opened it, so a client reused under a different loop fails with "Future attached
    # to a different loop" -- the same class of bug as the Celery worker engine.
    setattr(app.state, STATE_LOOP_ATTRIBUTE, _running_loop())


def get_redis_client(app: FastAPI) -> redis.Redis:
    """Return the pooled client, creating one if the lifespan has not run.

    The fallback exists for tests and for any entry point that mounts the app
    without its lifespan. It is deliberately cached on `app.state` so the fallback
    path cannot become a per-request client by accident.
    """
    client = getattr(app.state, STATE_ATTRIBUTE, None)
    owner = getattr(app.state, STATE_LOOP_ATTRIBUTE, None)
    current = _running_loop()

    # Rebuild only when the client is bound to a *different* live loop. A client
    # created outside any loop has not opened a connection yet, so it is adopted into
    # the current one rather than discarded. In production the lifespan creates it
    # once inside the serving loop and this never triggers; it matters wherever the
    # app outlives a loop, which is every test that mounts it under a fresh client.
    if client is None:
        client = create_redis_client()
        set_redis_client(app, client)
        return client
    if owner is None and current is not None:
        setattr(app.state, STATE_LOOP_ATTRIBUTE, current)
        return client
    if owner is not None and current is not None and owner is not current:
        client = create_redis_client()
        set_redis_client(app, client)
    return client


async def close_redis_client(app: FastAPI) -> None:
    client = getattr(app.state, STATE_ATTRIBUTE, None)
    if client is not None:
        await client.aclose()
        setattr(app.state, STATE_ATTRIBUTE, None)
        setattr(app.state, STATE_LOOP_ATTRIBUTE, None)
