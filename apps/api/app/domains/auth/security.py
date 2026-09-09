import base64
import hashlib
import hmac
import json
import secrets
import time
import uuid
from typing import Any

import jwt
from fastapi import HTTPException, status
from pwdlib import PasswordHash

from app.config import settings

PBKDF2_ITERATIONS = 600_000
TOKEN_TTL_SECONDS = 3600
REFRESH_TOKEN_TTL_SECONDS = 30 * 24 * 3600
PASSWORD_HASH = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return PASSWORD_HASH.hash(password)


def verify_password(password: str, encoded: str) -> bool:
    if encoded.startswith("$argon2"):
        try:
            return PASSWORD_HASH.verify(password, encoded)
        except Exception:  # malformed password hashes must fail closed
            return False
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


def new_opaque_token() -> str:
    return secrets.token_urlsafe(48)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _unb64(data: str) -> bytes:
    return base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))


def _secret() -> bytes:
    value = settings.jwt_secret
    if not value:
        raise RuntimeError("JWT_SECRET must be configured")
    return value.encode()


def create_access_token(
    user_id: uuid.UUID, role: str, ttl: int = TOKEN_TTL_SECONDS, credential_version: int = 1
) -> str:
    now = int(time.time())
    header = _b64(json.dumps({"alg": "HS256", "typ": "JWT"}, separators=(",", ":")).encode())
    payload = _b64(
        json.dumps(
            {
                "sub": str(user_id),
                "role": role,
                "cv": credential_version,
                "iat": now,
                "exp": now + ttl,
            },
            separators=(",", ":"),
        ).encode()
    )
    message = f"{header}.{payload}"
    signature = _b64(hmac.new(_secret(), message.encode(), hashlib.sha256).digest())
    return f"{message}.{signature}"


def decode_access_token(token: str) -> dict[str, Any]:
    error = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    try:
        header, payload, signature = token.split(".")
        message = f"{header}.{payload}"
        expected = _b64(hmac.new(_secret(), message.encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(signature, expected):
            raise error
        claims = json.loads(_unb64(payload))
        if int(claims["exp"]) <= int(time.time()) or not claims.get("sub"):
            raise error
        return claims
    except HTTPException:
        raise
    except (ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        raise error from exc


def decode_keycloak_access_token(token: str) -> dict[str, Any]:
    error = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    try:
        issuer = settings.keycloak_issuer.rstrip("/")
        signing_key = jwt.PyJWKClient(f"{issuer}/protocol/openid-connect/certs").get_signing_key_from_jwt(
            token
        )
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
