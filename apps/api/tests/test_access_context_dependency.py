import uuid
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.domains.auth import dependencies
from app.domains.auth.models import AccessRole, UserRole


class FakeAccessService:
    calls: list[tuple[object, object, str]] = []
    result: object

    def __init__(self, session: object) -> None:
        self.session = session

    async def context(self, user: object, brand_key: str) -> object:
        self.calls.append((self.session, user, brand_key))
        return self.result


@pytest.fixture(autouse=True)
def reset_fake_service() -> None:
    FakeAccessService.calls = []


@pytest.mark.asyncio
async def test_access_context_is_resolved_once_per_request_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = SimpleNamespace(
        roles=[AccessRole.operations],
        permissions=["ops.dispatch.read"],
    )
    FakeAccessService.result = context
    monkeypatch.setattr(dependencies, "AccessService", FakeAccessService)
    request = SimpleNamespace(state=SimpleNamespace())
    session = object()
    user = SimpleNamespace(id=uuid.uuid4(), credential_version=4)

    first = await dependencies.resolve_access_context(request, user, session)
    second = await dependencies.resolve_access_context(request, user, session)

    assert first is context
    assert second is context
    assert FakeAccessService.calls == [(session, user, dependencies.BRAND_KEY)]


@pytest.mark.asyncio
async def test_access_context_cache_key_includes_credential_version_and_brand(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = SimpleNamespace(roles=[], permissions=[])
    FakeAccessService.result = context
    monkeypatch.setattr(dependencies, "AccessService", FakeAccessService)
    request = SimpleNamespace(state=SimpleNamespace())
    session = object()
    user = SimpleNamespace(id=uuid.uuid4(), credential_version=1)

    await dependencies.resolve_access_context(request, user, session)
    user.credential_version = 2
    await dependencies.resolve_access_context(request, user, session)
    await dependencies.resolve_access_context(request, user, session, "other-brand")

    assert len(FakeAccessService.calls) == 3


@pytest.mark.asyncio
async def test_role_and_permission_guards_share_pre_resolved_context() -> None:
    user = object()
    context = SimpleNamespace(
        roles=[AccessRole.operations],
        permissions=["ops.dispatch.read", "ops.bookings.read"],
    )

    assert await dependencies.require_roles(UserRole.operations)(user, context) is user
    assert (
        await dependencies.require_permissions(
            "ops.dispatch.read",
            "ops.bookings.read",
        )(user, context)
        is user
    )
    assert (
        await dependencies.require_any_permission(
            "ops.providers.manage",
            "ops.bookings.read",
        )(user, context)
        is user
    )


@pytest.mark.asyncio
async def test_permission_guards_reject_missing_access_and_accept_wildcard() -> None:
    user = object()
    denied = SimpleNamespace(roles=[AccessRole.customer], permissions=[])
    wildcard = SimpleNamespace(roles=[AccessRole.superadmin], permissions=["*"])

    with pytest.raises(HTTPException) as role_error:
        await dependencies.require_roles(UserRole.operations)(user, denied)
    assert role_error.value.status_code == 403

    with pytest.raises(HTTPException) as all_error:
        await dependencies.require_permissions("ops.dispatch.read")(user, denied)
    assert all_error.value.status_code == 403

    with pytest.raises(HTTPException) as any_error:
        await dependencies.require_any_permission("ops.dispatch.read")(user, denied)
    assert any_error.value.status_code == 403

    assert await dependencies.require_permissions("anything")(user, wildcard) is user
    assert await dependencies.require_any_permission("anything")(user, wildcard) is user


def test_permission_guards_require_at_least_one_nonblank_permission() -> None:
    with pytest.raises(ValueError, match="At least one permission"):
        dependencies.require_permissions("", "   ")
    with pytest.raises(ValueError, match="At least one permission"):
        dependencies.require_any_permission()
