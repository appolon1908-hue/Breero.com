from pathlib import Path

root = Path(__file__).resolve().parents[1]


def replace_once(relative: str, old: str, new: str) -> None:
    path = root / relative
    content = path.read_text(encoding="utf-8")
    if old not in content:
        if new in content:
            return
        raise RuntimeError(f"expected source block not found in {relative}: {old!r}")
    path.write_text(content.replace(old, new, 1), encoding="utf-8")


# Every password hash executed from an async request path must be awaited so
# pwdlib's Argon2id work stays in Starlette's worker threadpool.
replace_once(
    "apps/api/app/domains/auth/provisioning_service.py",
    "password_hash=hash_password(new_opaque_token()),",
    "password_hash=await hash_password(new_opaque_token()),",
)
replace_once(
    "apps/api/app/domains/workforce/onboarding_service.py",
    "password_hash=hash_password(data.password),",
    "password_hash=await hash_password(data.password),",
)

# Flip a significant signature character. Changing the final base64url
# character is not deterministic because unused trailing bits can decode to
# the same signature bytes.
replace_once(
    "apps/api/tests/test_auth_security.py",
    '''    token = create_access_token(uuid.uuid4(), "customer")
    with pytest.raises(HTTPException) as error:
        await decode_access_token(token[:-1] + ("a" if token[-1] != "a" else "b"))
''',
    '''    token = create_access_token(uuid.uuid4(), "customer")
    header, payload, signature = token.split(".")
    signature = ("A" if signature[0] != "A" else "B") + signature[1:]
    tampered = ".".join((header, payload, signature))
    with pytest.raises(HTTPException) as error:
        await decode_access_token(tampered)
''',
)
replace_once(
    "apps/api/tests/test_auth_security.py",
    "security._LOCAL_TOKEN_COMPATIBILITY_CUTOFF",
    "security._LOCAL_TOKEN_COMPATIBILITY_DEADLINE",
)

# Fail closed if any known synchronous hashing call site survived the repair.
for relative in (
    "apps/api/app/domains/auth/service.py",
    "apps/api/app/domains/auth/provisioning_service.py",
    "apps/api/app/domains/workforce/onboarding_service.py",
):
    content = (root / relative).read_text(encoding="utf-8")
    if "password_hash=hash_password(" in content:
        raise RuntimeError(f"blocking password hashing remains in {relative}")
