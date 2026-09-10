import asyncio
from contextlib import asynccontextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from app import main


@pytest.fixture
def dependencies(monkeypatch):
    connection = SimpleNamespace(scalar=AsyncMock(return_value=main.EXPECTED_SCHEMA_REVISION))
    client = SimpleNamespace(ping=AsyncMock(return_value=True), aclose=AsyncMock())
    released = []

    @asynccontextmanager
    async def connect():
        try:
            yield connection
        finally:
            released.append(True)

    monkeypatch.setattr(main, "engine", SimpleNamespace(connect=connect))
    monkeypatch.setattr(main.redis, "from_url", lambda *args, **kwargs: client)
    monkeypatch.setattr(main, "READINESS_TIMEOUT_SECONDS", 0.02)
    return connection, client, released


@pytest.mark.asyncio
@pytest.mark.parametrize("dependency", ["postgres", "redis"])
async def test_stalled_dependency_returns_503_and_releases_resources(dependencies, dependency):
    connection, client, released = dependencies

    async def stall(*args):
        await asyncio.Event().wait()

    if dependency == "postgres":
        connection.scalar.side_effect = stall
    else:
        client.ping.side_effect = stall

    with pytest.raises(HTTPException) as error:
        await asyncio.wait_for(main.ready(), timeout=1)

    assert error.value.status_code == 503
    assert error.value.detail == "dependency unavailable"
    assert released == [True]
    if dependency == "redis":
        client.aclose.assert_awaited_once()
    else:
        client.ping.assert_not_awaited()


@pytest.mark.asyncio
async def test_healthy_dependencies_preserve_readiness_response(dependencies):
    _, client, released = dependencies
    assert await main.ready() == {
        "status": "ready", "postgres": "ok", "schema": "ok", "redis": "ok"
    }
    assert released == [True]
    client.aclose.assert_awaited_once()


@pytest.mark.asyncio
async def test_outdated_schema_still_returns_not_ready(dependencies):
    connection, _, _ = dependencies
    connection.scalar.return_value = "outdated"
    with pytest.raises(HTTPException) as error:
        await main.ready()
    assert error.value.status_code == 503
    assert error.value.detail["checks"]["schema"] == "outdated"
