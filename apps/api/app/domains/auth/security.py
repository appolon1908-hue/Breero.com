import hashlib
import hmac
import secrets
import time
import uuid
from typing import Any

import jwt
from fastapi import HTTPException, status
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher
from starlette.concurrency import run_in_threadpool

from app.config import settings

# Retained only to verify credentials created before the move to Argon2id. Nothing
# new is ever hashed with it.
LEGACY_PBKDF2_PREFIX = "pbkdf2_sha256$"
PBKDF2_ITERATIONS = 600_000

TOKEN_TTL_SECONDS = 3600
REFRESH_TOKEN_TTL_SECONDS = 30 * 24 * 3600
CANONICAL_KEYCLOAK_ISSUER = "https://auth.codestra.co/realms/codestra"

# Keycloak signing keys are cached in one long-lived client. Building a client per
# request means a fresh HTTPS round trip to the identity provider on every
# authenticated call, and an identity-provider blip becomes a full API outage.
JWKS_CACHE_SECONDS = 300
JWKS_TIMEOUT_SECONDS = 5

_password_hash = PasswordHash((Argon2Hasher(),))
_jwk_client: jwt.PyJWKClient | None = None
_jwk_client_issuer: str | None = None


# ---------------------------------------------------------------------------
# Passwords
#
# Hashing is deliberately expensive, which makes it CPU-bound work that must not
# run on the event loop: the API serves under `uvicorn --workers 2`, so one inline
# hash stalls every other request on that worker for its whole duration. The async
# functions below are the ones application code calls.
# ---------------------------------------------------------------------------


def hash_password_sync(password: str) -> str:
    """Blocking Argon2id hash. Prefer `hash_password` outside of tests."""
    return _password_hash.hash(password)


def _verify_legacy_pbkdf2(password: str, encoded: str) -> bool:
    try:
        algorithm, iterations, salt, expected = encoded.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        digest = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), bytes.fromhex(salt), int(iterations)
        )
        return hmac.compare_digest(digest.hex(), expected)
    except (ValueError, TypeError):
        return False


def verify_password_sync(password: str, encoded: str) -> bool:
    """Blocking verification. Prefer `verify_password` outside of tests."""
    if encoded.startswith(LEGACY_PBKDF2_PREFIX):
        return _verify_legacy_pbkdf2(password, encoded)
    try:
        return _password_hash.verify(password, encoded)
    except Exception:
        # A malformed or unknown hash is a failed login, never a 500.
        return False


async def hash_password(password: str) -> str:
    return await run_in_threadpool(hash_password_sync, password)


async def verify_password(password: str, encoded: str) -> bool:
    return await run_in_threadpool(verify_password_sync, password, encoded)


def needs_rehash(encoded: str) -> bool:
    """True for credentials still stored under the superseded PBKDF2 scheme.

    Login upgrades these in place on the next successful sign-in, so the migration
    completes without anyone having to reset a password.
    """
    return encoded.startswith(LEGACY_PBKDF2_PREFIX)


# ---------------------------------------------------------------------------
# Tokens
# ---------------------------------------------------------------------------


def new_opaque_token() -> str:
    return secrets.token_urlsafe(48)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _secret() -> str:
    value = settings.jwt_secret
    if not value:
        raise RuntimeError("JWT_SECRET must be configured")
    return value


def create_access_token(
    user_id: uuid.UUID, role: str, ttl: int = TOKEN_TTL_SECONDS, credential_version: int = 1
) -> str:
    now = int(time.time())
    return jwt.encode(
        {
            "sub": str(user_id),
            "role": role,
            "cv": credential_version,
            "iat": now,
            "exp": now + ttl,
            "iss": settings.jwt_issuer,
            "aud": settings.jwt_audience,
        },
        _secret(),
        algorithm="HS256",
    )


def decode_access_token_sync(token: str) -> dict[str, Any]:
    """Verify a first-party access token.

    PyJWT rather than a hand-rolled verifier: the algorithm is pinned, and issuer,
    audience and the required claims are checked -- none of which the previous
    hand-written implementation did.
    """
    error = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    try:
        return jwt.decode(
            token,
            _secret(),
            algorithms=["HS256"],
            issuer=settings.jwt_issuer,
            audience=settings.jwt_audience,
            options={"require": ["exp", "iat", "sub"]},
        )
    except jwt.PyJWTError as exc:
        raise error from exc


def _validated_keycloak_issuer() -> str:
    issuer = settings.keycloak_issuer.rstrip("/")
    if issuer != CANONICAL_KEYCLOAK_ISSUER:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid identity issuer configuration",
        )
    return issuer


def keycloak_jwk_client(issuer: str) -> jwt.PyJWKClient:
    """One cached client per issuer, built once and reused.

    `cache_jwk_set` with a lifespan fetches the key set roughly every five minutes
    rather than on every request, and the timeout stops a slow identity provider from
    holding a worker thread indefinitely.
    """
    global _jwk_client, _jwk_client_issuer
    if _jwk_client is None or _jwk_client_issuer != issuer:
        _jwk_client = jwt.PyJWKClient(
            f"{issuer}/protocol/openid-connect/certs",
            cache_jwk_set=True,
            lifespan=JWKS_CACHE_SECONDS,
            timeout=JWKS_TIMEOUT_SECONDS,
        )
        _jwk_client_issuer = issuer
    return _jwk_client


def reset_keycloak_jwk_client() -> None:
    """Drop the cached client. Used by tests and on a deliberate issuer change."""
    global _jwk_client, _jwk_client_issuer
    _jwk_client = None
    _jwk_client_issuer = None


def decode_keycloak_access_token_sync(token: str) -> dict[str, Any]:
    error = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    issuer = _validated_keycloak_issuer()
    try:
        signing_key = keycloak_jwk_client(issuer).get_signing_key_from_jwt(token)
        return jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=settings.keycloak_audience,
            issuer=issuer,
            options={"require": ["exp", "iat", "sub"]},
        )
    except jwt.PyJWTError as exc:
        raise error from exc


async def decode_access_token(token: str) -> dict[str, Any]:
    """Verify a bearer token, off the event loop.

    The Keycloak path makes a network call when the key cache is cold, and even a
    cached RS256 verification is CPU work. Neither belongs inline in a handler that is
    also serving every other request on the same worker.
    """
    if settings.keycloak_enabled:
        return await run_in_threadpool(decode_keycloak_access_token_sync, token)
    return await run_in_threadpool(decode_access_token_sync, token)
