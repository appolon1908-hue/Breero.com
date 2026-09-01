import uuid
from types import SimpleNamespace
from typing import cast

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.domains.auth.access_service import DEFAULT_PERMISSIONS
from app.domains.auth.models import AccessRole
from app.domains.finance.models import PayoutStatus
from app.domains.finance.repository import FinanceRepository
from app.domains.finance.service import FinanceService
from app.domains.portal.service import PortalReadService
from app.main import app


def test_portal_and_finance_read_contracts_are_present_with_payouts_disabled() -> None:
    assert settings.payout_enabled is False
    paths = app.openapi()["paths"]
    for path in (
        "/api/v1/portal/provider/overview",
        "/api/v1/portal/provider/jobs",
        "/api/v1/portal/provider/workers",
        "/api/v1/portal/provider/credentials",
        "/api/v1/portal/provider/earnings",
        "/api/v1/portal/provider/payout-batches",
        "/api/v1/portal/operations/overview",
        "/api/v1/portal/admin/overview",
        "/api/v1/portal/admin/audit",
        "/api/v1/finance/compensation-plans",
        "/api/v1/finance/earnings",
        "/api/v1/finance/payout-batches",
    ):
        assert "get" in paths[path]


def test_provider_default_access_is_read_scoped_to_its_own_resources() -> None:
    permissions = DEFAULT_PERMISSIONS[AccessRole.vendor_admin]
    assert {
        "provider.services.read",
        "provider.skills.read",
        "provider.jobs.read",
        "provider.workers.read",
        "provider.credentials.read",
        "provider.earnings.read",
        "provider.payouts.read",
    }.issubset(permissions)
    assert "finance.payouts.read" not in permissions
    assert "ops.dispatch.manage" not in permissions


def test_effective_capabilities_report_payouts_disabled() -> None:
    capabilities = PortalReadService.capabilities()
    assert capabilities.payouts is False
    assert capabilities.automatic_assignment is False


class FakeSession:
    def add(self, _value) -> None:
        pass

    async def commit(self) -> None:
        pass

    async def refresh(self, _value) -> None:
        pass


class FakeRepository:
    def __init__(self, batch) -> None:
        self.batch = batch

    async def get_batch(self, _batch_id, lock=False):
        return self.batch


@pytest.mark.asyncio
async def test_batch_reviewer_cannot_approve_same_payout(monkeypatch) -> None:
    actor_id = uuid.uuid4()
    batch = SimpleNamespace(
        id=uuid.uuid4(),
        status=PayoutStatus.PENDING_APPROVAL,
        reviewed_by=actor_id,
    )
    service = FinanceService(cast(AsyncSession, FakeSession()))
    service.repo = cast(FinanceRepository, FakeRepository(batch))
    monkeypatch.setattr(settings, "payout_enabled", True)

    with pytest.raises(HTTPException) as exc_info:
        await service.approve_batch(batch.id, actor_id)

    assert exc_info.value.status_code == 409
    assert "reviewer" in str(exc_info.value.detail).lower()


@pytest.mark.asyncio
async def test_batch_approver_cannot_submit_same_payout(monkeypatch) -> None:
    actor_id = uuid.uuid4()
    batch = SimpleNamespace(
        id=uuid.uuid4(),
        status=PayoutStatus.APPROVED,
        approved_by=actor_id,
        provider_transfer_id=None,
    )
    service = FinanceService(cast(AsyncSession, FakeSession()))
    service.repo = cast(FinanceRepository, FakeRepository(batch))
    monkeypatch.setattr(settings, "payout_enabled", True)

    with pytest.raises(HTTPException) as exc_info:
        await service.submit_batch(batch.id, actor_id)

    assert exc_info.value.status_code == 409
    assert "approver" in str(exc_info.value.detail).lower()
