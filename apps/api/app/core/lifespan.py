import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI

from app.config import settings
from app.domains.auth.security import maintain_keycloak_jwks


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Own background identity-key refresh for each API worker process."""

    stop = asyncio.Event()
    jwks_task: asyncio.Task[None] | None = None
    if settings.keycloak_enabled:
        jwks_task = asyncio.create_task(
            maintain_keycloak_jwks(stop),
            name="keycloak-jwks-refresh",
        )
    try:
        yield
    finally:
        stop.set()
        if jwks_task is not None:
            with suppress(asyncio.CancelledError):
                await jwks_task
