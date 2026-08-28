import os
import uuid

import pytest
from sqlalchemy import select

from app.core.errors import DomainError
from app.db.session import SessionLocal
from app.domains.auth.models import (
    AccessAssignment,
    AccessProfile,
    AccessRole,
    Department,
    RolePermission,
    TenantScope,
    User,
    UserRole,
)
from app.domains.catalog.models import Service
from app.domains.common.outbox import AuditLog, EventStatus, IntegrationEvent
from app.domains.provider_catalog.models import (
    ApprovalStatus,
    ProviderService,
    ProviderSkill,
    ServiceSkillRequirement,
    SkillDefinition,
)
from app.domains.provider_catalog.schemas import (
    ProviderServiceCreate,
    ProviderServiceUpdate,
    ProviderSkillCreate,
)
from app.domains.provider_catalog.service import ProviderCatalogService
from app.domains.workforce.models import (
    ProviderApplication,
    ProviderApplicationStatus,
    Vendor,
    VendorStatus,
    Worker,
    WorkerStatus,
)
from app.domains.workforce.onboarding_service import ProviderOnboardingService
from app.domains.workforce.schemas import ProviderApplicationDecision

pytestmark = pytest.mark.skipif(
    not os.getenv("DATABASE_URL", "").startswith("postgresql"),
    reason="provider catalog integration requires PostgreSQL",
)


async def _provider_fixture(session, marker: str, suffix: str):
    user = User(
        email=f"provider-{suffix}-{marker}@example.test",
        password_hash="disabled",
        full_name=f"Provider {suffix}",
        role=UserRole.vendor_admin,
        is_active=True,
        email_verified=True,
    )
    session.add(user)
    await session.flush()
    vendor = Vendor(
        legal_name=f"Provider {suffix} LLC",
        display_name=f"Provider {suffix}",
        email=user.email,
        phone="+17135550100",
        owner_user_id=user.id,
        status=VendorStatus.PENDING,
        capabilities=[],
        service_radius_meters=40000,
    )
    session.add(vendor)
    await session.flush()
    worker = Worker(
        vendor_id=vendor.id,
        user_id=user.id,
        first_name="Provider",
        last_name=suffix,
        email=user.email,
        phone="+17135550100",
        status=WorkerStatus.INVITED,
        skills=[],
        available=False,
    )
    session.add(worker)
    session.add(AccessProfile(user_id=user.id, brand_key="breero"))
    session.add(
        AccessAssignment(
            user_id=user.id,
            brand_key="breero",
            role_key=AccessRole.vendor_admin.value,
            department=Department.provider.value,
            tenant_scope=TenantScope.vendor.value,
            vendor_id=vendor.id,
            active=True,
            is_primary=True,
        )
    )
    application = ProviderApplication(
        vendor_id=vendor.id,
        status=ProviderApplicationStatus.DRAFT,
        identity={"full_name": user.full_name},
        business={"legal_name": vendor.legal_name},
        contact_details={"email": user.email, "phone": vendor.phone},
        service_areas=[{"type": "ZIP", "value": "77001"}],
        postal_codes=["77001"],
        availability={"monday": [["08:00", "17:00"]]},
        capacity={"daily_jobs": 4, "daily_minutes": 480},
        licenses=[{"type": "trade", "jurisdiction": "TX"}],
        insurance=[{"type": "general_liability"}],
        compliance_documents=[str(uuid.uuid4())],
        version=1,
    )
    session.add(application)
    await session.flush()
    return user, vendor, worker, application


@pytest.mark.asyncio
async def test_provider_services_and_skills_are_scoped_versioned_and_approved_together() -> None:
    marker = uuid.uuid4().hex
    async with SessionLocal() as session:
        owner, vendor, worker, application = await _provider_fixture(
            session, marker, "one"
        )
        other_owner, other_vendor, _, _ = await _provider_fixture(
            session, marker, "two"
        )
        admin = User(
            email=f"admin-{marker}@example.test",
            password_hash="disabled",
            full_name="BREERO Admin",
            role=UserRole.admin,
            is_active=True,
            email_verified=True,
        )
        service = Service(
            slug=f"catalog-service-{marker}",
            name="Catalog service",
            description="Provider catalog test",
            category="plumbing",
            pricing_model="request_only",
            duration_minutes=60,
            provider_approval_required=True,
            is_active=True,
            is_bookable=False,
        )
        skill = SkillDefinition(
            key=f"licensed-plumber-{marker}",
            name="Licensed plumber",
            category="plumbing",
            provider_approval_required=True,
            active=True,
            version=1,
        )
        session.add_all([admin, service, skill])
        await session.flush()
        session.add(
            ServiceSkillRequirement(
                service_id=service.id,
                skill_id=skill.id,
                required=True,
            )
        )
        await session.commit()
        await session.refresh(owner)
        await session.refresh(vendor)
        await session.refresh(worker)
        await session.refresh(application)
        await session.refresh(admin)
        await session.refresh(service)
        await session.refresh(skill)

        catalog = ProviderCatalogService(session)
        selected_service = await catalog.add_service(
            owner,
            ProviderServiceCreate(service_id=service.id, display_order=5),
            correlation_id=f"provider-catalog-{marker}",
        )
        selected_skill = await catalog.add_skill(
            owner,
            ProviderSkillCreate(skill_id=skill.id),
            correlation_id=f"provider-catalog-{marker}",
        )

        assert selected_service.vendor_id == vendor.id
        assert selected_service.status == ApprovalStatus.PENDING
        assert selected_service.required_skills[0].id == skill.id
        assert selected_skill.worker_id == worker.id
        assert selected_skill.status == ApprovalStatus.PENDING

        await session.refresh(application)
        assert application.services == [str(service.id)]
        assert application.skills == [str(skill.id)]
        await session.refresh(worker)
        assert worker.skills == [skill.key]

        with pytest.raises(DomainError) as hidden:
            await ProviderCatalogService(session).update_service(
                selected_service.id,
                other_owner,
                ProviderServiceUpdate(display_order=10),
                expected_version=selected_service.version,
            )
        assert hidden.value.code == "PROVIDER_SERVICE_NOT_FOUND"
        await session.rollback()

        updated = await catalog.update_service(
            selected_service.id,
            owner,
            ProviderServiceUpdate(display_order=10),
            expected_version=selected_service.version,
        )
        assert updated.display_order == 10
        assert updated.version == selected_service.version + 1
        with pytest.raises(DomainError) as stale:
            await catalog.update_service(
                selected_service.id,
                owner,
                ProviderServiceUpdate(display_order=11),
                expected_version=selected_service.version,
            )
        assert stale.value.code == "VERSION_CONFLICT"
        await session.rollback()

        await session.refresh(application)
        submitted = await ProviderOnboardingService(session).submit(owner)
        assert submitted.status == ProviderApplicationStatus.PENDING
        approved = await ProviderOnboardingService(session).approve(
            application.id,
            admin,
            ProviderApplicationDecision(reason="Verified provider evidence"),
        )
        assert approved.status == ProviderApplicationStatus.APPROVED

        await session.refresh(vendor)
        await session.refresh(worker)
        provider_service = await session.scalar(
            select(ProviderService).where(
                ProviderService.vendor_id == vendor.id,
                ProviderService.service_id == service.id,
            )
        )
        provider_skill = await session.scalar(
            select(ProviderSkill).where(
                ProviderSkill.vendor_id == vendor.id,
                ProviderSkill.skill_id == skill.id,
            )
        )
        assert vendor.status == VendorStatus.ACTIVE
        assert worker.status == WorkerStatus.ACTIVE
        assert worker.available is True
        assert provider_service and provider_service.status == ApprovalStatus.APPROVED
        assert provider_skill and provider_skill.status == ApprovalStatus.APPROVED
        assert other_vendor.status == VendorStatus.PENDING

        audits = set(
            (
                await session.scalars(
                    select(AuditLog.action).where(
                        AuditLog.actor_id.in_({owner.id, admin.id})
                    )
                )
            ).all()
        )
        assert {
            "provider.service.select",
            "provider.skill.select",
            "provider.onboarding.submit",
            "provider.onboarding.approve",
        } <= audits
        events = list(
            (
                await session.scalars(
                    select(IntegrationEvent).where(
                        IntegrationEvent.aggregate_id.in_(
                            {selected_service.id, selected_skill.id}
                        )
                    )
                )
            ).all()
        )
        event_types = {event.event_type for event in events}
        assert "provider_service_selected" in event_types
        assert "provider_skill_selected" in event_types
        # Regression test: these events have no external-adapter dependency, so
        # they must be created PENDING, not PENDING_CONFIGURATION -- the only
        # promoter of that status is never called with a matching aggregate_type
        # (see app/workers/tasks.py), which would leave them permanently stuck.
        assert all(event.status == EventStatus.PENDING for event in events)


@pytest.mark.asyncio
async def test_provider_catalog_permissions_are_seeded_by_migration() -> None:
    async with SessionLocal() as session:
        permissions = set(
            (
                await session.scalars(
                    select(RolePermission.permission).where(
                        RolePermission.role_key == AccessRole.vendor_admin.value
                    )
                )
            ).all()
        )
        assert {
            "provider.services.read",
            "provider.services.manage",
            "provider.skills.read",
            "provider.skills.manage",
        } <= permissions


@pytest.mark.asyncio
async def test_withdrawing_a_selection_survives_catalog_service_deactivation() -> None:
    # Regression test: update_service used to require the underlying catalog
    # Service to still be active before applying ANY patch, including
    # active=False (withdrawal) -- so once BREERO deactivated a service, a
    # provider could no longer withdraw their own selection via PATCH, only
    # DELETE (remove_service, which has no such check).
    marker = uuid.uuid4().hex
    async with SessionLocal() as session:
        owner, vendor, worker, application = await _provider_fixture(
            session, marker, "withdraw"
        )
        service = Service(
            slug=f"catalog-service-withdraw-{marker}",
            name="Withdrawable service",
            description="Provider catalog withdrawal fixture",
            category="plumbing",
            pricing_model="request_only",
            duration_minutes=60,
            provider_approval_required=False,
            is_active=True,
            is_bookable=False,
        )
        session.add(service)
        await session.commit()
        await session.refresh(owner)
        await session.refresh(service)

        catalog = ProviderCatalogService(session)
        selected = await catalog.add_service(
            owner,
            ProviderServiceCreate(service_id=service.id),
            correlation_id=f"withdraw-{marker}",
        )

        service.is_active = False
        await session.commit()

        withdrawn = await catalog.update_service(
            selected.id,
            owner,
            ProviderServiceUpdate(active=False),
            expected_version=selected.version,
        )
        assert withdrawn.active is False
