import asyncio

import pytest
from fastapi import FastAPI

from app.config import settings
from app.core import lifespan as lifespan_module


@pytest.mark.asyncio
async def test_lifespan_owns_keycloak_refresh_task(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    started = asyncio.Event()
    stopped = asyncio.Event()

    async def fake_maintain(stop: asyncio.Event) -> None:
        started.set()
        await stop.wait()
        stopped.set()

    monkeypatch.setattr(settings, "keycloak_enabled", True)
    monkeypatch.setattr(lifespan_module, "maintain_keycloak_jwks", fake_maintain)

    async with lifespan_module.lifespan(FastAPI()):
        await asyncio.wait_for(started.wait(), timeout=1)

    assert stopped.is_set()
