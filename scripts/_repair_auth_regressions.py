from pathlib import Path

root = Path(__file__).resolve().parents[1]
lifecycle_path = root / "apps/api/tests/test_auth_lifecycle.py"
lifecycle = lifecycle_path.read_text()
old = '''    result = await service.login(
        LoginRequest(email=account.email, password="old-password-123"),
        user_agent="test-agent",
        ip="127.0.0.1",
    )
'''
new = '''    result = await service.login(
        LoginRequest(email=account.email, password="old-password-123")
    )
'''
if old in lifecycle:
    lifecycle = lifecycle.replace(old, new, 1)
elif new not in lifecycle:
    raise RuntimeError("successful legacy-login test block not found")
lifecycle_path.write_text(lifecycle)

security_path = root / "apps/api/tests/test_auth_security.py"
security = security_path.read_text()
old = '''    token = security.create_access_token(uuid.uuid4(), "customer")
    with pytest.raises(HTTPException) as error:
        await security.decode_access_token(token[:-1] + ("a" if token[-1] != "a" else "b"))
'''
new = '''    token = security.create_access_token(uuid.uuid4(), "customer")
    header, payload, signature = token.split(".")
    signature = ("A" if signature[0] != "A" else "B") + signature[1:]
    tampered = ".".join((header, payload, signature))
    with pytest.raises(HTTPException) as error:
        await security.decode_access_token(tampered)
'''
if old in security:
    security = security.replace(old, new, 1)
elif new not in security:
    raise RuntimeError("tampered-token test block not found")
security_path.write_text(security)
