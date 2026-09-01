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


@pytest.mark.asyncio
async def test_password_hash_round_trip() -> None:
    encoded = await hash_password("a long secure password")
    assert encoded != "a long secure password"
    assert await verify_password("a long secure password", encoded)
    assert not await verify_password("wrong password", encoded)


@pytest.mark.asyncio
async def test_password_hashes_are_salted() -> None:
    # Two hashes of the same password must differ, or the store leaks which accounts
    # share a password.
    first = await hash_password("a long secure password")
    second = await hash_password("a long secure password")
    assert first != second


@pytest.mark.asyncio
async def test_access_token_round_trip() -> None:
    user_id = uuid.uuid4()
    claims = await decode_access_token(create_access_token(user_id, "operations"))
    assert claims["sub"] == str(user_id)
    assert claims["role"] == "operations"


@pytest.mark.asyncio
async def test_tampered_access_token_is_rejected() -> None:
    token = create_access_token(uuid.uuid4(), "customer")
    with pytest.raises(HTTPException) as error:
        await decode_access_token(token[:-1] + ("a" if token[-1] != "a" else "b"))
    assert error.value.status_code == 401


def test_opaque_tokens_are_random_and_only_hashes_need_persisting() -> None:
    first, second = new_opaque_token(), new_opaque_token()
    assert first != second
    assert len(first) >= 32
    assert hash_token(first) != first
    assert len(hash_token(first)) == 64


@pytest.mark.asyncio
async def test_access_token_contains_credential_version() -> None:
    claims = await decode_access_token(
        create_access_token(uuid.uuid4(), "customer", credential_version=7)
    )
    assert claims["cv"] == 7
