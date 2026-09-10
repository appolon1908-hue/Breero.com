from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app import main


@pytest.mark.parametrize("path", ["/ready", "/health/ready"])
@pytest.mark.parametrize("failure", [None, "postgres", "schema", "redis"])
def test_readiness_routes_preserve_dependency_checks(monkeypatch, path, failure):
    closed = []

    class Connection:
        async def __aenter__(self):
            if failure == "postgres":
                raise ConnectionError("test database unavailable")
            return self

        async def __aexit__(self, *_args):
            return False

        async def scalar(self, _statement):
            return "outdated-revision" if failure == "schema" else main.EXPECTED_SCHEMA_REVISION

    class Redis:
        async def ping(self):
            if failure == "redis":
                raise ConnectionError("test redis unavailable")
            return True

        async def aclose(self):
            closed.append(True)

    monkeypatch.setattr(main, "engine", SimpleNamespace(connect=Connection))
    monkeypatch.setattr(main.redis, "from_url", lambda *_args, **_kwargs: Redis())

    response = TestClient(main.app).get(path)
    assert response.status_code == (503 if failure else 200)
    if failure is None:
        assert response.json() == {
            "status": "ready",
            "postgres": "ok",
            "schema": "ok",
            "redis": "ok",
        }
    if failure != "postgres":
        assert closed == [True]


def test_documented_readiness_route_is_read_only():
    client = TestClient(main.app)
    assert client.post("/ready").status_code == 405
    assert "/ready" in main.app.openapi()["paths"]
