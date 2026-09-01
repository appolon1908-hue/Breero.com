"""Third-party API: credential handling, scoping and fail-closed behaviour.

The security properties are the point of these tests. An integrator credential is not
a user session, and the ways it can go wrong are different: leaked secrets in
responses, keys that outlive their revocation, scope creep, and cross-tenant reads.
"""

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from app.config import settings
from app.domains.partner_api.models import ApiClient, ApiClientStatus, ApiKey, ApiScope
from app.domains.partner_api.schemas import ApiKeyIssued, ApiKeyRead, WebhookSubscriptionRead
from app.domains.partner_api.service import (
    PartnerApiService,
    hash_secret,
    require_partner_api_enabled,
    sign_payload,
)


def _key(**overrides) -> ApiKey:
    defaults = dict(
        id=uuid.uuid4(),
        client_id=uuid.uuid4(),
        label="test",
        prefix="brk_abcd1234",
        key_hash=hash_secret("brk_abcd1234.secret"),
        scopes=[ApiScope.CATALOG_READ.value],
        expires_at=datetime.now(UTC) + timedelta(days=30),
        revoked_at=None,
        rate_limit_per_minute=60,
    )
    defaults.update(overrides)
    return ApiKey(**defaults)


def _service(key: ApiKey | None, client: ApiClient | None) -> PartnerApiService:
    service = PartnerApiService(AsyncMock())
    service.repo = AsyncMock()
    service.repo.key_by_hash = AsyncMock(return_value=key)
    service.repo.active_client_for_key = AsyncMock(return_value=client)
    service.repo.touch_key = AsyncMock()
    return service


# ---------------------------------------------------------------------------
# Fail-closed
# ---------------------------------------------------------------------------


def test_the_api_is_disabled_by_default() -> None:
    assert settings.third_party_api_enabled is False


def test_disabled_capability_refuses_with_503(monkeypatch) -> None:
    monkeypatch.setattr(settings, "third_party_api_enabled", False)
    with pytest.raises(HTTPException) as error:
        require_partner_api_enabled()
    assert error.value.status_code == 503


def test_production_refuses_to_boot_with_the_api_enabled(tmp_path) -> None:
    """Held to the same release discipline as payments and the marketplace."""
    from pydantic import ValidationError

    from app.config import Settings

    def secret(name: str, value: str) -> str:
        path = tmp_path / name
        path.write_text(value, encoding="ascii")
        return str(path)

    with pytest.raises(ValidationError, match="THIRD_PARTY_API_ENABLED"):
        Settings(
            app_env="production",
            cors_origins="https://breero.com",
            metrics_enabled=False,
            third_party_api_enabled=True,
            database_url_file=secret("db", "postgresql+psycopg://b:strong-password@postgres:5432/b"),
            redis_url_file=secret("redis", "redis://:strong-password@redis:6379/0"),
            jwt_secret_file=secret("jwt", "a" * 40),
            jwt_refresh_secret_file=secret("jwt-refresh", "b" * 40),
        )


# ---------------------------------------------------------------------------
# Credential handling
# ---------------------------------------------------------------------------


def test_the_secret_is_never_stored() -> None:
    # Only the digest is a column. A dump of api_keys must not yield a usable key.
    assert not hasattr(ApiKey, "secret")
    columns = {column.name for column in ApiKey.__table__.columns}
    assert "secret" not in columns
    assert "key_hash" in columns


def test_only_the_issue_response_carries_the_secret() -> None:
    # Listing keys must not leak one, so the read model has no such field.
    assert "secret" in ApiKeyIssued.model_fields
    assert "secret" not in ApiKeyRead.model_fields
    assert "secret" not in WebhookSubscriptionRead.model_fields


@pytest.mark.asyncio
async def test_a_valid_key_authenticates() -> None:
    key = _key()
    client = ApiClient(id=key.client_id, name="c", contact_email="c@x.test", status=ApiClientStatus.ACTIVE)
    resolved_client, resolved_key = await _service(key, client).authenticate("brk_abcd1234.secret")
    assert resolved_client is client
    assert resolved_key is key


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "overrides, reason",
    [
        ({"revoked_at": datetime.now(UTC)}, "revoked"),
        ({"expires_at": datetime.now(UTC) - timedelta(seconds=1)}, "expired"),
    ],
)
async def test_a_revoked_or_expired_key_is_refused(overrides, reason) -> None:
    key = _key(**overrides)
    client = ApiClient(id=key.client_id, name="c", contact_email="c@x.test", status=ApiClientStatus.ACTIVE)
    with pytest.raises(HTTPException) as error:
        await _service(key, client).authenticate("brk_abcd1234.secret")
    assert error.value.status_code == 401, reason


@pytest.mark.asyncio
async def test_a_suspended_client_cannot_authenticate() -> None:
    key = _key()
    # active_client_for_key returns None for a non-active client.
    with pytest.raises(HTTPException) as error:
        await _service(key, None).authenticate("brk_abcd1234.secret")
    assert error.value.status_code == 401


@pytest.mark.asyncio
async def test_an_unknown_key_is_refused() -> None:
    with pytest.raises(HTTPException) as error:
        await _service(None, None).authenticate("brk_unknown.secret")
    assert error.value.status_code == 401


@pytest.mark.asyncio
async def test_every_rejection_is_indistinguishable() -> None:
    """A caller must not be able to tell unknown from revoked, expired or suspended.

    Differentiated messages turn the endpoint into an oracle for probing which keys
    exist and what state they are in.
    """
    messages = set()
    cases = [
        _service(None, None),
        _service(_key(revoked_at=datetime.now(UTC)), MagicMock()),
        _service(_key(expires_at=datetime.now(UTC) - timedelta(seconds=1)), MagicMock()),
        _service(_key(), None),
    ]
    for service in cases:
        with pytest.raises(HTTPException) as error:
            await service.authenticate("brk_abcd1234.secret")
        messages.add((error.value.status_code, error.value.detail))
    assert len(messages) == 1, messages


@pytest.mark.asyncio
async def test_a_malformed_credential_is_refused_without_a_lookup() -> None:
    service = _service(None, None)
    with pytest.raises(HTTPException):
        await service.authenticate("not-a-key")
    service.repo.key_by_hash.assert_not_awaited()


# ---------------------------------------------------------------------------
# Scopes
# ---------------------------------------------------------------------------


def test_a_missing_scope_is_forbidden_not_unauthorised() -> None:
    # The credential is valid; the grant is not. Retrying will never help.
    key = _key(scopes=[ApiScope.CATALOG_READ.value])
    with pytest.raises(HTTPException) as error:
        PartnerApiService.require_scope(key, ApiScope.SERVICE_REQUEST_WRITE)
    assert error.value.status_code == 403
    assert "service_request:write" in error.value.detail


def test_a_held_scope_passes() -> None:
    key = _key(scopes=[ApiScope.CATALOG_READ.value, ApiScope.SERVICE_REQUEST_WRITE.value])
    PartnerApiService.require_scope(key, ApiScope.SERVICE_REQUEST_WRITE)


def test_an_empty_scope_set_grants_nothing() -> None:
    for scope in ApiScope:
        with pytest.raises(HTTPException):
            PartnerApiService.require_scope(_key(scopes=[]), scope)


# ---------------------------------------------------------------------------
# Tenancy
# ---------------------------------------------------------------------------


def test_submission_keys_are_namespaced_per_client() -> None:
    first, second = uuid.uuid4(), uuid.uuid4()
    # Two integrators using the same key must not collide, and neither can replay
    # the other's submission by guessing it.
    assert PartnerApiService.submission_key(first, "order-1") != PartnerApiService.submission_key(
        second, "order-1"
    )
    assert PartnerApiService.submission_key(first, "order-1").startswith(f"partner:{first}:")


@pytest.mark.asyncio
async def test_a_client_cannot_read_another_clients_request() -> None:
    mine, theirs = uuid.uuid4(), uuid.uuid4()
    submission = MagicMock(idempotency_key=f"partner:{theirs}:order-1")
    service = PartnerApiService(AsyncMock())
    service.session.get = AsyncMock(return_value=submission)
    assert await service.owned_submission(uuid.uuid4(), mine) is None


@pytest.mark.asyncio
async def test_a_client_can_read_its_own_request() -> None:
    mine = uuid.uuid4()
    submission = MagicMock(idempotency_key=f"partner:{mine}:order-1")
    service = PartnerApiService(AsyncMock())
    service.session.get = AsyncMock(return_value=submission)
    assert await service.owned_submission(uuid.uuid4(), mine) is submission


# ---------------------------------------------------------------------------
# Webhook signing
# ---------------------------------------------------------------------------


def test_the_signature_covers_the_timestamp() -> None:
    """A captured delivery must not be replayable against a fresh timestamp."""
    body = b'{"a":1}'
    assert sign_payload("s", body, "1000") != sign_payload("s", body, "2000")


def test_the_signature_covers_the_body() -> None:
    assert sign_payload("s", b'{"a":1}', "1000") != sign_payload("s", b'{"a":2}', "1000")


def test_a_different_secret_produces_a_different_signature() -> None:
    assert sign_payload("one", b"{}", "1000") != sign_payload("two", b"{}", "1000")


def test_delivery_headers_are_verifiable_by_a_receiver() -> None:
    payload = {"event": "service_request.received", "id": "abc"}
    headers = PartnerApiService.delivery_headers("shared-secret", payload)
    assert headers["X-Breero-Signature"].startswith("sha256=")

    # What a correct receiver does: recompute over the same canonical body.
    import json

    body = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    expected = sign_payload("shared-secret", body, headers["X-Breero-Timestamp"])
    assert headers["X-Breero-Signature"] == f"sha256={expected}"


def test_webhook_urls_must_be_https() -> None:
    from pydantic import ValidationError

    from app.domains.partner_api.schemas import WebhookSubscriptionCreate

    with pytest.raises(ValidationError, match="https"):
        WebhookSubscriptionCreate(
            url="http://partner.example.test/hook", event_types=["service_request.received"]
        )


def test_unknown_event_types_are_rejected() -> None:
    from app.domains.partner_api.service import WEBHOOK_EVENT_TYPES

    assert "service_request.received" in WEBHOOK_EVENT_TYPES
    assert "payment.captured" not in WEBHOOK_EVENT_TYPES


# ---------------------------------------------------------------------------
# Key issuance
# ---------------------------------------------------------------------------


def test_scopes_must_be_unique() -> None:
    from pydantic import ValidationError

    from app.domains.partner_api.schemas import ApiKeyCreate

    with pytest.raises(ValidationError, match="unique"):
        ApiKeyCreate(label="dup", scopes=[ApiScope.CATALOG_READ, ApiScope.CATALOG_READ])


def test_an_expiry_is_always_bounded() -> None:
    from pydantic import ValidationError

    from app.domains.partner_api.schemas import ApiKeyCreate

    assert ApiKeyCreate(label="key", scopes=[ApiScope.CATALOG_READ]).expires_in_days == 90
    with pytest.raises(ValidationError):
        ApiKeyCreate(label="key", scopes=[ApiScope.CATALOG_READ], expires_in_days=0)
    with pytest.raises(ValidationError):
        ApiKeyCreate(label="key", scopes=[ApiScope.CATALOG_READ], expires_in_days=4000)


def test_unknown_fields_are_rejected() -> None:
    from pydantic import ValidationError

    from app.domains.partner_api.schemas import ApiClientCreate

    with pytest.raises(ValidationError):
        ApiClientCreate(name="client", contact_email="a@b.test", is_admin=True)
