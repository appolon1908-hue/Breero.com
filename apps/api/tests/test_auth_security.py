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
@pytest.mark.parametrize("segment", [0, 1, 2], ids=["header", "payload", "signature"])
async def test_a_tampered_access_token_is_rejected(segment: int) -> None:
    """Tamper each segment deterministically.

    The previous version flipped the token's final character. In base64url the last
    character can carry fewer than six significant bits, so that edit sometimes
    decodes to the *same* signature bytes and the token still verifies -- the test
    passed or failed depending on which character a given secret happened to produce.
    Mutating a character in the middle of a segment always changes the decoded value.
    """
    token = create_access_token(uuid.uuid4(), "customer")
    parts = token.split(".")
    assert len(parts) == 3

    target = parts[segment]
    middle = len(target) // 2
    swapped = "A" if target[middle] != "A" else "B"
    parts[segment] = target[:middle] + swapped + target[middle + 1 :]

    with pytest.raises(HTTPException) as error:
        await decode_access_token(".".join(parts))
    assert error.value.status_code == 401


@pytest.mark.asyncio
async def test_a_token_signed_with_another_key_is_rejected() -> None:
    import jwt as pyjwt

    forged = pyjwt.encode({"sub": str(uuid.uuid4()), "exp": 9999999999}, "not-the-secret")
    with pytest.raises(HTTPException):
        await decode_access_token(forged)


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
