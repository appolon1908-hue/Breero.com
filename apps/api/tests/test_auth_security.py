import uuid

import pytest
from fastapi import HTTPException

from app.domains.auth.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    hash_token,
    new_opaque_token,
    verify_password,
)


def test_password_hash_round_trip() -> None:
    encoded = hash_password("a long secure password")
    assert encoded != "a long secure password"
    assert encoded.startswith("$argon2")
    assert verify_password("a long secure password", encoded)
    assert not verify_password("wrong password", encoded)


def test_legacy_pbkdf2_passwords_remain_verifiable_during_upgrade() -> None:
    from app.domains.auth import security

    password = "legacy-password"
    salt = bytes.fromhex("00112233445566778899aabbccddeeff")
    digest = security.hashlib.pbkdf2_hmac(
        "sha256", password.encode(), salt, security.PBKDF2_ITERATIONS
    )
    encoded = (
        f"pbkdf2_sha256${security.PBKDF2_ITERATIONS}${salt.hex()}${digest.hex()}"
    )
    assert verify_password(password, encoded)


def test_access_token_round_trip(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JWT_SECRET", "test-secret-that-is-not-for-production")
    user_id = uuid.uuid4()
    claims = decode_access_token(create_access_token(user_id, "operations"))
    assert claims["sub"] == str(user_id)
    assert claims["role"] == "operations"


def test_tampered_access_token_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JWT_SECRET", "test-secret-that-is-not-for-production")
    token = create_access_token(uuid.uuid4(), "customer")
    with pytest.raises(HTTPException) as error:
        decode_access_token(token[:-1] + ("a" if token[-1] != "a" else "b"))
    assert error.value.status_code == 401


def test_opaque_tokens_are_random_and_only_hashes_need_persisting() -> None:
    first, second = new_opaque_token(), new_opaque_token()
    assert first != second
    assert len(first) >= 32
    assert hash_token(first) != first
    assert len(hash_token(first)) == 64


def test_access_token_contains_credential_version(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JWT_SECRET", "test-secret-that-is-not-for-production")
    claims = decode_access_token(
        create_access_token(uuid.uuid4(), "customer", credential_version=7)
    )
    assert claims["cv"] == 7
