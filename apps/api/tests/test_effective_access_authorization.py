import uuid
from types import SimpleNamespace

import pytest
from fastapi import HTTPException, status

from app.domains.auth import dependencies
from app.domains.auth.access_service import NO_ACCESS_DASHBOARD, AccessService
from app.domains.auth.models import AccessProfile, AccessRole, User, UserRole


class EmptyScalarResult:
    def all(self) -> list:
        return []


class ManagedEmptySession:
    async def scalar(self, _query):
        return SimpleNamespace()

    async def scalars(self, _query):
        return EmptyScalarResult()


class ReplaceWithEmptySession:
    def __init__(self, user: User) -> None:
        self.user = user
        self.scalar_calls = 0
        self.added: list[object] = []
        self.commits = 0

    async def scalar(self, _query):
        self.scalar_calls += 1
        if self.scalar_calls == 1:
            return self.user
        if self.scalar_calls == 2:
            return None
        return SimpleNamespace()

    async def scalars(self, _query):
        return EmptyScalarResult()

    def add(self, value: object) -> None:
        self.added.append(value)

    async def flush(self) -> None:
        return None

    async def execute(self, _statement) -> None:
        return None

    async def commit(self) -> None:
        self.commits += 1


def make_user(role: UserRole = UserRole.admin) -> User:
    return User(
        id=uuid.uuid4(),
        email=f"{uuid.uuid4().hex}@example.com",
        password_hash="disabled",
        full_name="Access User",
        role=role,
        is_active=True,
        email_verified=True,
    )


@pytest.mark.asyncio
async def test_managed_profile_with_no_assignments_has_no_access() -> None:
    user = make_user()

    context = await AccessService(ManagedEmptySession()).context(user)  # type: ignore[arg-type]

    assert context.dashboard_path == NO_ACCESS_DASHBOARD
    assert context.roles == []
    assert context.departments == []
    assert context.permissions == []
    assert context.assignments == []


@pytest.mark.asyncio
async def test_replacing_assignments_with_empty_list_persists_revocation_marker() -> None:
    user = make_user()
    session = ReplaceWithEmptySession(user)

    context = await AccessService(session).replace_assignments(  # type: ignore[arg-type]
        user_id=user.id,
        brand_key="breero",
        assignments=[],
    )

    assert any(isinstance(item, AccessProfile) for item in session.added)
    assert session.commits == 1
    assert context.dashboard_path == NO_ACCESS_DASHBOARD
    assert context.permissions == []


@pytest.mark.asyncio
async def test_legacy_role_gate_uses_effective_assignments(monkeypatch) -> None:
    user = make_user(UserRole.admin)

    class DowngradedAccessService:
        def __init__(self, _session) -> None:
            pass

        async def context(self, _user, _brand_key):
            return SimpleNamespace(roles=[AccessRole.support], permissions=[])

    monkeypatch.setattr(dependencies, "AccessService", DowngradedAccessService)
    gate = dependencies.require_roles(UserRole.admin)

    with pytest.raises(HTTPException) as exc_info:
        await gate(user, object())

    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
async def test_permission_gate_honors_deny_and_superadmin_wildcard(monkeypatch) -> None:
    user = make_user(UserRole.admin)
    active_permissions: list[str] = []

    class EffectiveAccessService:
        def __init__(self, _session) -> None:
            pass

        async def context(self, _user, _brand_key):
            return SimpleNamespace(roles=[AccessRole.admin], permissions=active_permissions)

    monkeypatch.setattr(dependencies, "AccessService", EffectiveAccessService)
    gate = dependencies.require_permissions("admin.access.manage")

    with pytest.raises(HTTPException) as exc_info:
        await gate(user, object())
    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    active_permissions.append("*")
    assert await gate(user, object()) is user
