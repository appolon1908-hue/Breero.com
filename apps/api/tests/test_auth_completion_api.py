import uuid
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.domains.auth.models import (
    AccessAssignment,
    AccessProfile,
    AccountInvitationToken,
    User,
    UserRole,
)
from app.domains.auth.provisioning_service import (
    ROLE_BINDINGS,
    InternalUserProvisioningService,
)
from app.domains.auth.schemas import (
    AccessAssignmentRead,
    InternalAccountRole,
    InternalUserProvisionRequest,
    PortalContext,
    UserRead,
)
from app.domains.common.outbox import AuditLog, EventStatus, IntegrationEvent
from app.main import app


def test_first_completion_api_routes_are_registered() -> None:
    paths = app.openapi()["paths"]
    required = {
        "/api/v1/auth/register/client": {"post"},
        "/api/v1/auth/register": {"post"},
        "/api/v1/auth/login": {"post"},
        "/api/v1/auth/logout": {"post"},
        "/api/v1/auth/refresh": {"post"},
        "/api/v1/auth/me": {"get"},
        "/api/v1/auth/password/set": {"post"},
        "/api/v1/auth/password/change": {"post"},
        "/api/v1/auth/password/forgot": {"post"},
        "/api/v1/auth/password/reset": {"post"},
        "/api/v1/auth/email/verify": {"post"},
        "/api/v1/auth/email/resend": {"post"},
        "/api/v1/admin/users": {"post"},
    }
    for path, methods in required.items():
        assert methods <= set(paths[path])
    assert "/api/v1/admin/register" not in paths


def test_internal_provisioning_role_contract_is_closed() -> None:
    assert {role.value for role in InternalAccountRole} == {
        "BREERO_SUPPORT",
        "BREERO_DISPATCH",
        "BREERO_ADMIN",
    }
    with pytest.raises(ValidationError):
        InternalUserProvisionRequest(
            email="client@example.com",
            full_name="Client",
            role="CLIENT",
        )
    with pytest.raises(ValidationError):
        InternalUserProvisionRequest(
            email="provider@example.com",
            full_name="Provider",
            role="PROVIDER",
        )


def test_internal_roles_map_to_deny_by_default_access_profiles() -> None:
    assert set(ROLE_BINDINGS) == set(InternalAccountRole)
    support = ROLE_BINDINGS[InternalAccountRole.BREERO_SUPPORT]
    dispatch = ROLE_BINDINGS[InternalAccountRole.BREERO_DISPATCH]
    admin = ROLE_BINDINGS[InternalAccountRole.BREERO_ADMIN]

    assert support[0] == UserRole.finance
    assert support[1].value == "support"
    assert support[2].value == "customer_support"

    assert dispatch[0] == UserRole.operations
    assert dispatch[1].value == "operations"
    assert dispatch[2].value == "dispatch"

    assert admin[0] == UserRole.admin
    assert admin[1].value == "admin"
    assert admin[2].value == "administration"
    assert admin[3].value == "global"


class FakeSession:
    def __init__(self) -> None:
        self.added: list[object] = []
        self.commits = 0
        self.rollbacks = 0

    def add(self, item: object) -> None:
        self.added.append(item)

    async def commit(self) -> None:
        self.commits += 1

    async def rollback(self) -> None:
        self.rollbacks += 1

    async def refresh(self, _item: object) -> None:
        return None


class FakeRepository:
    def __init__(self, _session: FakeSession) -> None:
        self.existing: User | None = None

    async def by_email(self, _email: str) -> User | None:
        return self.existing

    async def add(self, user: User) -> User:
        user.id = uuid.uuid4()
        return user


class FakeAccessService:
    def __init__(self, session: FakeSession) -> None:
        self.session = session

    async def context(
        self,
        user: User,
        brand_key: str,
    ) -> PortalContext:
        assignment = next(
            item
            for item in self.session.added
            if isinstance(item, AccessAssignment)
        )
        return PortalContext(
            user=UserRead.model_validate(user),
            brand_key=brand_key,
            dashboard_path="/admin",
            roles=[assignment.role_key],
            departments=[assignment.department],
            permissions=["admin.access.manage"],
            assignments=[
                AccessAssignmentRead(
                    role=assignment.role_key,
                    department=assignment.department,
                    tenant_scope=assignment.tenant_scope,
                    vendor_id=None,
                    is_primary=True,
                )
            ],
            identity_mode="local",
        )


@pytest.mark.asyncio
async def test_local_internal_provisioning_is_invitation_only_and_audited(
    monkeypatch,
) -> None:
    from app.domains.auth import provisioning_service as module

    session = FakeSession()
    repository = FakeRepository(session)
    monkeypatch.setattr(module, "UserRepository", lambda _session: repository)
    monkeypatch.setattr(module, "AccessService", FakeAccessService)
    monkeypatch.setattr(
        module,
        "settings",
        SimpleNamespace(
            keycloak_enabled=False,
            email_enabled=False,
            transactional_email_mode="disabled",
        ),
    )

    actor = User(
        id=uuid.uuid4(),
        email="admin@example.com",
        password_hash="disabled",
        full_name="Admin",
        role=UserRole.admin,
        is_active=True,
        email_verified=True,
    )
    result = await InternalUserProvisioningService(session).provision(
        actor=actor,
        data=InternalUserProvisionRequest(
            email="dispatch@example.com",
            full_name="Dispatch User",
            role=InternalAccountRole.BREERO_DISPATCH,
        ),
    )

    assert result.credential_mode == "invitation"
    assert result.invitation_state == "pending_configuration"
    assert result.user.email == "dispatch@example.com"
    assert session.commits == 1
    assert any(isinstance(item, AccessProfile) for item in session.added)
    assert any(
        isinstance(item, AccountInvitationToken)
        and item.created_by == actor.id
        and item.expires_at > datetime.now(UTC) + timedelta(hours=23)
        for item in session.added
    )
    event = next(
        item
        for item in session.added
        if isinstance(item, IntegrationEvent)
    )
    assert event.status == EventStatus.PENDING_CONFIGURATION
    assert event.event_type == "internal_user_invitation_requested"
    assert event.payload["role"] == "BREERO_DISPATCH"
    audit = next(
        item
        for item in session.added
        if isinstance(item, AuditLog)
    )
    assert audit.actor_id == actor.id
    assert audit.action == "admin.user.provision"
    assert audit.metadata_json["role"] == "BREERO_DISPATCH"


@pytest.mark.asyncio
async def test_duplicate_internal_email_is_rejected_before_writes(
    monkeypatch,
) -> None:
    from app.domains.auth import provisioning_service as module

    session = FakeSession()
    repository = FakeRepository(session)
    repository.existing = User(
        id=uuid.uuid4(),
        email="existing@example.com",
        password_hash="disabled",
        full_name="Existing",
        role=UserRole.admin,
        is_active=True,
        email_verified=True,
    )
    monkeypatch.setattr(module, "UserRepository", lambda _session: repository)

    actor = User(
        id=uuid.uuid4(),
        email="admin@example.com",
        password_hash="disabled",
        full_name="Admin",
        role=UserRole.admin,
        is_active=True,
        email_verified=True,
    )
    with pytest.raises(HTTPException) as exc_info:
        await InternalUserProvisioningService(session).provision(
            actor=actor,
            data=InternalUserProvisionRequest(
                email="existing@example.com",
                full_name="Existing",
                role=InternalAccountRole.BREERO_SUPPORT,
            ),
        )

    assert exc_info.value.status_code == 409
    assert not session.added
    assert session.commits == 0
