"""Guards for the six critical findings of the 2026-09-01 architecture review.

Each test names the failure it prevents. They are cheap, and every one of these
regressed silently once already.
"""

import ast
import inspect
import time
import uuid
from pathlib import Path

import jwt
import pytest
import yaml

from app.config import settings
from app.domains.auth import security

API_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = API_ROOT.parents[1]


# ---------------------------------------------------------------------------
# BE-01 — password hashing must not run on the event loop
# ---------------------------------------------------------------------------


def test_new_passwords_use_argon2id_not_pbkdf2() -> None:
    encoded = security.hash_password_sync("a long secure password")
    assert encoded.startswith("$argon2id$")
    assert not encoded.startswith(security.LEGACY_PBKDF2_PREFIX)


def test_password_helpers_used_by_application_code_are_coroutines() -> None:
    # The blocking variants stay available for tests and scripts, but the names the
    # application calls must be awaitable or the work lands back on the event loop.
    assert inspect.iscoroutinefunction(security.hash_password)
    assert inspect.iscoroutinefunction(security.verify_password)
    assert inspect.iscoroutinefunction(security.decode_access_token)


def test_no_domain_code_calls_the_blocking_password_helpers() -> None:
    """The whole point of BE-01 is that these never run inline in a request."""
    offenders: list[str] = []
    blocking = {"hash_password_sync", "verify_password_sync", "decode_access_token_sync"}
    for path in sorted((API_ROOT / "app").rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id in blocking
            ):
                offenders.append(f"{path.relative_to(API_ROOT)}:{node.lineno} {node.func.id}")
    assert offenders == [], offenders


@pytest.mark.asyncio
async def test_legacy_pbkdf2_credentials_still_verify() -> None:
    # Existing users must not be locked out by the migration.
    import hashlib
    import secrets

    password = "existing-user-password"
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode(), salt, security.PBKDF2_ITERATIONS
    )
    legacy = f"pbkdf2_sha256${security.PBKDF2_ITERATIONS}${salt.hex()}${digest.hex()}"

    assert await security.verify_password(password, legacy)
    assert not await security.verify_password("wrong", legacy)
    assert security.needs_rehash(legacy)
    assert not security.needs_rehash(security.hash_password_sync(password))


@pytest.mark.asyncio
async def test_malformed_hash_is_a_failed_login_not_a_crash() -> None:
    assert not await security.verify_password("anything", "not-a-hash")
    assert not await security.verify_password("anything", "")


# ---------------------------------------------------------------------------
# BE-02 — the Keycloak key client is cached, not rebuilt per request
# ---------------------------------------------------------------------------


def test_keycloak_jwk_client_is_reused_across_calls() -> None:
    security.reset_keycloak_jwk_client()
    try:
        first = security.keycloak_jwk_client(security.CANONICAL_KEYCLOAK_ISSUER)
        second = security.keycloak_jwk_client(security.CANONICAL_KEYCLOAK_ISSUER)
        # A new client per call means a fresh HTTPS round trip to the identity
        # provider on every authenticated request.
        assert first is second
    finally:
        security.reset_keycloak_jwk_client()


def test_keycloak_jwk_client_is_rebuilt_when_the_issuer_changes() -> None:
    security.reset_keycloak_jwk_client()
    try:
        first = security.keycloak_jwk_client(security.CANONICAL_KEYCLOAK_ISSUER)
        second = security.keycloak_jwk_client("https://auth.example.test/realms/other")
        assert first is not second
    finally:
        security.reset_keycloak_jwk_client()


# ---------------------------------------------------------------------------
# BE-03 — tokens are verified by PyJWT, with issuer and audience
# ---------------------------------------------------------------------------


def test_access_token_carries_issuer_and_audience() -> None:
    token = security.create_access_token(uuid.uuid4(), "operations")
    claims = jwt.decode(
        token,
        settings.jwt_secret,
        algorithms=["HS256"],
        issuer=settings.jwt_issuer,
        audience=settings.jwt_audience,
    )
    assert claims["iss"] == settings.jwt_issuer
    assert claims["aud"] == settings.jwt_audience


def test_a_token_from_another_issuer_is_rejected() -> None:
    now = int(time.time())
    foreign = jwt.encode(
        {
            "sub": str(uuid.uuid4()),
            "iat": now,
            "exp": now + 600,
            "iss": "https://evil.example.test",
            "aud": settings.jwt_audience,
        },
        settings.jwt_secret,
        algorithm="HS256",
    )
    with pytest.raises(Exception):
        security.decode_access_token_sync(foreign)


def test_a_token_for_another_audience_is_rejected() -> None:
    now = int(time.time())
    foreign = jwt.encode(
        {
            "sub": str(uuid.uuid4()),
            "iat": now,
            "exp": now + 600,
            "iss": settings.jwt_issuer,
            "aud": "some-other-service",
        },
        settings.jwt_secret,
        algorithm="HS256",
    )
    with pytest.raises(Exception):
        security.decode_access_token_sync(foreign)


def test_an_unsigned_token_is_rejected() -> None:
    """`alg: none` is the classic JWT bypass; PyJWT with a pinned algorithm refuses it."""
    now = int(time.time())
    unsigned = jwt.encode(
        {
            "sub": str(uuid.uuid4()),
            "iat": now,
            "exp": now + 600,
            "iss": settings.jwt_issuer,
            "aud": settings.jwt_audience,
        },
        key="",
        algorithm="none",
    )
    with pytest.raises(Exception):
        security.decode_access_token_sync(unsigned)


def test_an_expired_token_is_rejected() -> None:
    expired = security.create_access_token(uuid.uuid4(), "customer", ttl=-60)
    with pytest.raises(Exception):
        security.decode_access_token_sync(expired)


# ---------------------------------------------------------------------------
# BE-04 — the worker engine cannot outlive an event loop
# ---------------------------------------------------------------------------


def test_worker_engine_uses_nullpool() -> None:
    from sqlalchemy.pool import NullPool

    from app.db.session import worker_engine

    # Celery tasks run under `asyncio.run`, so a pooled connection would be handed to
    # a loop that no longer exists on the next execution.
    assert isinstance(worker_engine.pool, NullPool)


def test_tasks_do_not_use_the_request_scoped_sessionmaker() -> None:
    source = (API_ROOT / "app" / "workers" / "tasks.py").read_text(encoding="utf-8")
    assert "WorkerSessionLocal" in source
    assert "SessionLocal()" not in source.replace("WorkerSessionLocal()", "")


# ---------------------------------------------------------------------------
# OPS-01 — every deployable topology runs the scheduler
# ---------------------------------------------------------------------------


COMPOSE_FILES = [
    "deploy/production/docker-compose.backend.yml",
    "deploy/staging/docker-compose.backend.yml",
    "docker-compose.production.yml",
    "docker-compose.yml",
]


@pytest.mark.parametrize("relative", COMPOSE_FILES)
def test_a_topology_with_a_worker_also_runs_beat(relative: str) -> None:
    """A worker without beat drains nothing and releases no capacity.

    The production file CI validates shipped without a scheduler while the root
    compose file had one, and nothing failed loudly.
    """
    document = yaml.safe_load((REPO_ROOT / relative).read_text(encoding="utf-8"))
    services = document.get("services", {})
    commands = {name: str(service.get("command", "")) for name, service in services.items()}

    has_worker = any("worker" in command and "celery" in command for command in commands.values())
    if not has_worker:
        pytest.skip(f"{relative} defines no Celery worker")

    has_beat = any("beat" in command for command in commands.values())
    assert has_beat, f"{relative} runs a Celery worker but no beat scheduler"


# ---------------------------------------------------------------------------
# OPS-02 — the image default forwards the client address
# ---------------------------------------------------------------------------


def test_dockerfile_default_command_trusts_proxy_headers() -> None:
    dockerfile = (API_ROOT / "Dockerfile").read_text(encoding="utf-8")
    command = next(line for line in dockerfile.splitlines() if line.startswith("CMD "))
    # Without this, request.client.host is the reverse proxy for every caller, which
    # collapses the rate limiter into one shared bucket.
    assert "--proxy-headers" in command
    assert "--forwarded-allow-ips" in command


ASYNC_SECURITY_HELPERS = {"hash_password", "verify_password", "decode_access_token"}


def test_no_test_calls_an_async_security_helper_without_awaiting() -> None:
    """An un-awaited coroutine is truthy, so `assert verify_password(...)` passes
    whatever the password is. One test was doing exactly that."""
    offenders: list[str] = []
    for path in sorted((API_ROOT / "tests").rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        awaited = {
            id(node.value)
            for node in ast.walk(tree)
            if isinstance(node, ast.Await)
        }
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id in ASYNC_SECURITY_HELPERS
                and id(node) not in awaited
            ):
                offenders.append(
                    f"{path.relative_to(API_ROOT)}:{node.lineno} {node.func.id}"
                )
    assert offenders == [], offenders
