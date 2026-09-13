import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from redis.exceptions import RedisError
from starlette.requests import Request

from app.api.v1 import public_forms
from app.core.errors import DomainError, install_error_handlers


class FakeRedis:
    def __init__(self, result=None, error: Exception | None = None) -> None:
        self.result = result
        self.error = error
        self.calls: list[tuple] = []
        self.closed = False

    async def eval(self, *args):
        self.calls.append(args)
        if self.error:
            raise self.error
        return self.result

    async def aclose(self) -> None:
        self.closed = True


def request_from(address: str) -> Request:
    return Request({
        "type": "http",
        "method": "POST",
        "path": "/api/v1/contact",
        "headers": [],
        "client": (address, 443),
    })


@pytest.mark.asyncio
async def test_public_form_rate_limit_is_one_atomic_redis_operation(monkeypatch) -> None:
    client = FakeRedis(result=[1, 60])
    monkeypatch.setattr(public_forms.redis, "from_url", lambda *args, **kwargs: client)

    source = await public_forms.enforce_rate_limit(request_from("192.0.2.40"))

    assert source == "192.0.2.40"
    assert len(client.calls) == 1
    assert client.calls[0][1:] == (1, "public-form:192.0.2.40", 60)
    assert client.closed is True


@pytest.mark.asyncio
async def test_public_form_rate_limit_preserves_domain_envelope_metadata(monkeypatch) -> None:
    client = FakeRedis(result=[11, 37])
    monkeypatch.setattr(public_forms.redis, "from_url", lambda *args, **kwargs: client)

    with pytest.raises(DomainError) as raised:
        await public_forms.enforce_rate_limit(request_from("192.0.2.41"))

    assert raised.value.status_code == 429
    assert raised.value.headers == {"Retry-After": "37"}
    assert raised.value.code == "RATE_LIMITED"
    assert raised.value.message == "Too many submissions; try again shortly"
    assert client.closed is True


def test_domain_handler_returns_the_public_v1_error_envelope_and_headers() -> None:
    app = FastAPI()
    install_error_handlers(app)

    @app.get("/rate-limited")
    async def rate_limited() -> None:
        raise DomainError(
            "RATE_LIMITED",
            "Too many submissions; try again shortly",
            429,
            headers={"Retry-After": "37"},
        )

    response = TestClient(app).get("/rate-limited")

    assert response.status_code == 429
    assert response.headers["retry-after"] == "37"
    assert response.json() == {
        "error": {
            "code": "RATE_LIMITED",
            "message": "Too many submissions; try again shortly",
        }
    }


@pytest.mark.asyncio
async def test_public_form_rate_limit_fails_closed_when_redis_is_unavailable(monkeypatch) -> None:
    client = FakeRedis(error=RedisError("offline"))
    monkeypatch.setattr(public_forms.redis, "from_url", lambda *args, **kwargs: client)

    with pytest.raises(DomainError) as raised:
        await public_forms.enforce_rate_limit(request_from("192.0.2.42"))

    assert raised.value.code == "RATE_LIMIT_UNAVAILABLE"
    assert raised.value.status_code == 503
    assert client.closed is True
