"""Guards for BE-05, BE-06 and BE-07.

Each of these was a per-request cost on the hottest paths in the API. The tests
below assert the cost is paid once, not once per call.
"""

import ast
import uuid
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.config import settings
from app.core import redis_client
from app.core.rate_limit import rate_limit
from app.domains.auth import dependencies

API_ROOT = Path(__file__).resolve().parents[1]


# ---------------------------------------------------------------------------
# BE-06 — pool sizing and lifespan
# ---------------------------------------------------------------------------


def test_engine_pool_is_explicitly_sized() -> None:
    from app.db.session import engine

    pool = engine.pool
    # SQLAlchemy's defaults cap the API at 30 connections across two workers.
    assert pool.size() == settings.db_pool_size
    assert engine.pool._max_overflow == settings.db_max_overflow


def test_engine_recycles_connections() -> None:
    from app.db.session import engine

    # Without recycling, a connection outlives a PostgreSQL restart or an idle proxy
    # timeout and fails on first use instead of being replaced.
    assert engine.pool._recycle == settings.db_pool_recycle_seconds
    assert engine.pool._timeout == settings.db_pool_timeout_seconds


def test_app_declares_a_lifespan() -> None:
    from app.main import app, lifespan

    assert lifespan is not None
    # Starlette wraps the callable; the important part is that one is registered at all.
    assert app.router.lifespan_context is not None


@pytest.mark.asyncio
async def test_lifespan_opens_and_closes_the_shared_client() -> None:
    import app.main as main_module
    from app.main import lifespan

    application = FastAPI()
    created = AsyncMock()
    with patch.object(main_module, "create_redis_client", return_value=created):
        async with lifespan(application):
            assert redis_client.get_redis_client(application) is created
    created.aclose.assert_awaited_once()


@pytest.mark.asyncio
async def test_shutdown_survives_a_dead_dependency() -> None:
    """A shutdown must not hang or raise because Redis has already gone away."""
    import app.main as main_module
    from app.main import lifespan

    application = FastAPI()
    broken = AsyncMock()
    broken.aclose = AsyncMock(side_effect=OSError("connection already closed"))
    with patch.object(main_module, "create_redis_client", return_value=broken):
        async with lifespan(application):
            pass  # exiting the block must not raise


# ---------------------------------------------------------------------------
# BE-05 — the rate limiter reuses one pooled client
# ---------------------------------------------------------------------------


def _pipeline_returning(count: int) -> MagicMock:
    pipeline = MagicMock()
    pipeline.__aenter__ = AsyncMock(return_value=pipeline)
    pipeline.__aexit__ = AsyncMock(return_value=False)
    pipeline.execute = AsyncMock(return_value=[count, True])
    return pipeline


def test_rate_limiter_does_not_open_a_connection_per_request() -> None:
    application = FastAPI()
    client = MagicMock()
    client.pipeline = MagicMock(return_value=_pipeline_returning(1))
    redis_client.set_redis_client(application, client)

    @application.get("/limited")
    async def limited(_: None = pytest.importorskip("fastapi").Depends(rate_limit("t", 100, 60))):
        return {"ok": True}

    with patch.object(redis_client, "create_redis_client") as factory:
        with TestClient(application) as http:
            for _ in range(5):
                assert http.get("/limited").status_code == 200
        # The pooled client was already present, so none should have been built.
        factory.assert_not_called()
    assert client.aclose.call_count == 0, "the shared client must outlive the request"


def test_rate_limiter_still_fails_closed_when_redis_is_down() -> None:
    import redis.asyncio as aioredis

    application = FastAPI()
    client = MagicMock()
    client.pipeline = MagicMock(side_effect=aioredis.RedisError("down"))
    redis_client.set_redis_client(application, client)

    @application.get("/limited")
    async def limited(_: None = pytest.importorskip("fastapi").Depends(rate_limit("t", 100, 60))):
        return {"ok": True}

    with TestClient(application, raise_server_exceptions=False) as http:
        assert http.get("/limited").status_code == 503


def test_rate_limiter_still_rejects_over_the_window() -> None:
    application = FastAPI()
    client = MagicMock()
    client.pipeline = MagicMock(return_value=_pipeline_returning(11))
    redis_client.set_redis_client(application, client)

    @application.get("/limited")
    async def limited(_: None = pytest.importorskip("fastapi").Depends(rate_limit("t", 10, 60))):
        return {"ok": True}

    with TestClient(application, raise_server_exceptions=False) as http:
        response = http.get("/limited")
    assert response.status_code == 429
    assert response.headers["Retry-After"] == "60"


def test_no_module_builds_its_own_redis_client_in_a_request_path() -> None:
    """`redis.from_url` belongs in the client factory, not in a handler."""
    allowed = {
        Path("app/core/redis_client.py"),
        # Falls back to its own client only when none is injected; the scrape handler
        # always injects the pooled one.
        Path("app/domains/common/observability.py"),
        # A Celery worker is a separate process with no FastAPI app to borrow from.
        Path("app/workers/tasks.py"),
    }
    offenders: list[str] = []
    for path in sorted((API_ROOT / "app").rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        relative = path.relative_to(API_ROOT)
        if relative in allowed:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "from_url"
            ):
                offenders.append(f"{relative}:{node.lineno}")
    assert offenders == [], offenders


# ---------------------------------------------------------------------------
# BE-07 — the access context is resolved once per request
# ---------------------------------------------------------------------------


class _Request:
    """Minimal stand-in with the mutable `state` FastAPI provides."""

    def __init__(self) -> None:
        self.state = type("State", (), {})()


@pytest.mark.asyncio
async def test_access_context_is_resolved_once_per_request() -> None:
    user = MagicMock(id=uuid.uuid4())
    request = _Request()
    context = MagicMock(roles={"operations"}, permissions={"jobs.read"})

    service = MagicMock()
    service.context = AsyncMock(return_value=context)
    with patch.object(dependencies, "AccessService", return_value=service):
        first = await dependencies.effective_access_context(request, user, MagicMock())
        second = await dependencies.effective_access_context(request, user, MagicMock())
        third = await dependencies.effective_access_context(request, user, MagicMock())

    assert first is second is third
    # A route with a role guard and a permission guard used to pay for this twice.
    assert service.context.await_count == 1


@pytest.mark.asyncio
async def test_a_different_principal_is_never_served_from_the_cache() -> None:
    request = _Request()
    first_user = MagicMock(id=uuid.uuid4())
    second_user = MagicMock(id=uuid.uuid4())

    service = MagicMock()
    service.context = AsyncMock(side_effect=[MagicMock(), MagicMock()])
    with patch.object(dependencies, "AccessService", return_value=service):
        one = await dependencies.effective_access_context(request, first_user, MagicMock())
        two = await dependencies.effective_access_context(request, second_user, MagicMock())

    assert one is not two
    assert service.context.await_count == 2


@pytest.mark.asyncio
async def test_the_cache_does_not_leak_between_requests() -> None:
    user = MagicMock(id=uuid.uuid4())
    service = MagicMock()
    service.context = AsyncMock(side_effect=[MagicMock(), MagicMock()])
    with patch.object(dependencies, "AccessService", return_value=service):
        await dependencies.effective_access_context(_Request(), user, MagicMock())
        await dependencies.effective_access_context(_Request(), user, MagicMock())
    assert service.context.await_count == 2


def test_guards_resolve_through_the_shared_helper() -> None:
    source = (API_ROOT / "app" / "domains" / "auth" / "dependencies.py").read_text(
        encoding="utf-8"
    )
    # Exactly one direct construction, inside the resolver itself.
    assert source.count("AccessService(session).context") == 1
    assert source.count("await effective_access_context(request, user, session)") == 3
