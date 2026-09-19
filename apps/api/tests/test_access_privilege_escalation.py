import uuid
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.api.v1 import access
from app.domains.auth.models import AccessRole, Department, TenantScope, User, UserRole
from app.domains.auth.schemas import AccessAssignmentInput, AccessProfileUpdate


def make_user(role: UserRole = UserRole.admin) -> User:
    return User(
        id=uuid.uuid4(),
        email=f"{uuid.uuid4().hex}@example.com",
        password_hash="disabled",
        full_name="Actor",
        role=role,
        is_active=True,
        email_verified=True,
    )


class FakeAccessService:
    def __init__(self, actor_permissions: list[str], replace_result=None) -> None:
        self.actor_permissions = actor_permissions
        self.replace_result = replace_result
        self.replace_calls = 0

    def __call__(self, _session):
        return self

    async def context(self, _user, _brand_key):
        return SimpleNamespace(permissions=self.actor_permissions)

    async def replace_assignments(self, **_kwargs):
        self.replace_calls += 1
        return self.replace_result


@pytest.mark.asyncio
async def test_regular_admin_cannot_grant_themselves_superadmin(monkeypatch) -> None:
    # Regression test: replace_user_access was gated only by admin.access.manage,
    # with no check on which role the actor was granting or that the target wasn't
    # the actor. A plain admin could self-grant superadmin, which resolves to the
    # "*" wildcard permission and bypasses every check in the app.
    actor = make_user(UserRole.admin)
    fake_service = FakeAccessService(actor_permissions=["admin.access.manage"])
    monkeypatch.setattr(access, "AccessService", fake_service)

    data = AccessProfileUpdate(
        assignments=[
            AccessAssignmentInput(
                role=AccessRole.superadmin,
                department=Department.administration,
                tenant_scope=TenantScope.global_,
            )
        ]
    )

    with pytest.raises(HTTPException) as exc_info:
        await access.replace_user_access(actor.id, data, actor, object())

    assert exc_info.value.status_code == 403
    assert fake_service.replace_calls == 0


@pytest.mark.asyncio
async def test_superadmin_can_grant_superadmin(monkeypatch) -> None:
    actor = make_user(UserRole.admin)
    expected = SimpleNamespace(roles=[AccessRole.superadmin])
    fake_service = FakeAccessService(actor_permissions=["*"], replace_result=expected)
    monkeypatch.setattr(access, "AccessService", fake_service)

    data = AccessProfileUpdate(
        assignments=[
            AccessAssignmentInput(
                role=AccessRole.superadmin,
                department=Department.administration,
                tenant_scope=TenantScope.global_,
            )
        ]
    )

    result = await access.replace_user_access(uuid.uuid4(), data, actor, object())

    assert result is expected
    assert fake_service.replace_calls == 1


@pytest.mark.asyncio
async def test_granting_non_superadmin_roles_does_not_require_wildcard_permission(
    monkeypatch,
) -> None:
    actor = make_user(UserRole.admin)
    expected = SimpleNamespace(roles=[AccessRole.operations])
    fake_service = FakeAccessService(
        actor_permissions=["admin.access.manage"], replace_result=expected
    )
    monkeypatch.setattr(access, "AccessService", fake_service)

    data = AccessProfileUpdate(
        assignments=[
            AccessAssignmentInput(role=AccessRole.operations, department=Department.dispatch)
        ]
    )

    result = await access.replace_user_access(uuid.uuid4(), data, actor, object())

    assert result is expected
    assert fake_service.replace_calls == 1
