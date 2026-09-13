import os
import uuid
from datetime import UTC, datetime, time, timedelta
from decimal import Decimal

import pytest
from geoalchemy2.elements import WKTElement

from app.core.errors import DomainError
from app.db.session import SessionLocal
from app.domains.booking.models import (
    Address,
    LegalEntity,
    ProviderServiceCoverage,
    ProviderWorkingHours,
    ServiceArea,
)
from app.domains.booking.schemas import AvailabilitySearchRequest
from app.domains.booking.service import AvailabilityService
from app.domains.catalog.models import Service
from app.domains.geography.models import ServiceZoneOffering
from app.domains.provider_catalog.models import ApprovalStatus, ProviderService
from app.domains.workforce.models import Vendor, VendorStatus, Worker, WorkerStatus

pytestmark = pytest.mark.skipif(
    not os.getenv("DATABASE_URL", "").startswith("postgresql"),
    reason="capacity-wiring integration requires PostgreSQL/PostGIS",
)


async def _fixture(session, marker: str):
    entity = LegalEntity(code=f"CAP-{marker[:8]}", name="Capacity Wiring Entity", currency="USD")
    session.add(entity)
    await session.flush()
    area = ServiceArea(
        legal_entity_id=entity.id, name="Capacity Wiring Area", country_code="US", active=True
    )
    session.add(area)
    await session.flush()
    address = Address(
        formatted_address="1 Capacity Way, Austin",
        line1="1 Capacity Way",
        city="Austin",
        postal_code="78701",
        country_code="US",
        location=WKTElement("POINT(-98 30)", srid=4326),
        service_area_id=area.id,
        timezone_name="America/Chicago",
    )
    service = Service(
        slug=f"capacity-service-{marker}",
        name="Capacity Wiring Service",
        description="Capacity wiring fixture",
        category="test",
        pricing_model="fixed",
        duration_minutes=60,
        base_price=Decimal("100.00"),
        is_active=True,
        is_bookable=True,
    )
    vendor = Vendor(
        legal_name="Capacity Vendor",
        display_name="Capacity Vendor",
        email=f"vendor-{marker}@example.test",
        phone="+15551230000",
        status=VendorStatus.ACTIVE,
        capabilities=[],
    )
    session.add_all([address, service, vendor])
    await session.flush()
    worker = Worker(
        vendor_id=vendor.id,
        first_name="Capacity",
        last_name="Tech",
        email=f"worker-{marker}@example.test",
        phone="+15559990000",
        status=WorkerStatus.ACTIVE,
        skills=[],
        available=True,
    )
    session.add(worker)
    await session.flush()
    service_date = (datetime.now(UTC) + timedelta(days=2)).date()
    session.add_all(
        [
            ProviderServiceCoverage(
                worker_id=worker.id, service_id=service.id, postal_code="78701"
            ),
            ProviderWorkingHours(
                worker_id=worker.id,
                weekday=service_date.weekday(),
                start_time=time(7),
                end_time=time(19),
                capacity=1,
            ),
        ]
    )
    await session.commit()
    await session.refresh(address)
    await session.refresh(service)
    await session.refresh(vendor)
    return area, address, service, vendor, service_date


@pytest.mark.asyncio
async def test_search_excludes_worker_whose_vendor_service_is_pending() -> None:
    # Regression test: an unapproved (or absent-in-approval-yet) self-service
    # catalog selection must not be treated as if it were approved. A vendor
    # with a PENDING ProviderService for this service must be excluded from
    # search results even though ProviderServiceCoverage (the ops-managed
    # table) still lists their worker.
    marker = uuid.uuid4().hex
    async with SessionLocal() as session:
        area, address, service, vendor, service_date = await _fixture(session, marker)

        session.add(
            ProviderService(
                vendor_id=vendor.id,
                service_id=service.id,
                status=ApprovalStatus.PENDING,
                active=True,
            )
        )
        await session.commit()

        slots = await AvailabilityService(session).search(
            AvailabilitySearchRequest(
                service_id=service.id,
                address_id=address.id,
                date_from=service_date,
                date_to=service_date,
            )
        )
        assert slots == []


@pytest.mark.asyncio
async def test_search_includes_worker_whose_vendor_service_is_approved() -> None:
    marker = uuid.uuid4().hex
    async with SessionLocal() as session:
        area, address, service, vendor, service_date = await _fixture(session, marker)

        session.add(
            ProviderService(
                vendor_id=vendor.id,
                service_id=service.id,
                status=ApprovalStatus.APPROVED,
                active=True,
            )
        )
        await session.commit()

        slots = await AvailabilityService(session).search(
            AvailabilitySearchRequest(
                service_id=service.id,
                address_id=address.id,
                date_from=service_date,
                date_to=service_date,
            )
        )
        assert len(slots) > 0


@pytest.mark.asyncio
async def test_search_includes_worker_with_no_provider_service_row_at_all() -> None:
    # A vendor that never used the self-service catalog (no ProviderService row
    # for this service) must keep working exactly as before -- ops-managed
    # ProviderServiceCoverage alone is still sufficient.
    marker = uuid.uuid4().hex
    async with SessionLocal() as session:
        area, address, service, vendor, service_date = await _fixture(session, marker)

        slots = await AvailabilityService(session).search(
            AvailabilitySearchRequest(
                service_id=service.id,
                address_id=address.id,
                date_from=service_date,
                date_to=service_date,
            )
        )
        assert len(slots) > 0


@pytest.mark.asyncio
async def test_search_rejects_service_disabled_in_zone_offering() -> None:
    # Regression test: a zone with an explicit ServiceZoneOffering disabling
    # regular service for this service_id must actually block availability
    # search, not just be admin-visible metadata with no effect.
    marker = uuid.uuid4().hex
    async with SessionLocal() as session:
        area, address, service, vendor, service_date = await _fixture(session, marker)

        session.add(
            ServiceZoneOffering(
                service_area_id=area.id,
                service_id=service.id,
                active=True,
                regular_service_enabled=False,
                emergency_service_enabled=True,
            )
        )
        await session.commit()

        with pytest.raises(DomainError) as exc_info:
            await AvailabilityService(session).search(
                AvailabilitySearchRequest(
                    service_id=service.id,
                    address_id=address.id,
                    date_from=service_date,
                    date_to=service_date,
                )
            )
        assert exc_info.value.code == "SERVICE_NOT_OFFERED_IN_ZONE"


@pytest.mark.asyncio
async def test_search_allows_service_enabled_in_zone_offering() -> None:
    marker = uuid.uuid4().hex
    async with SessionLocal() as session:
        area, address, service, vendor, service_date = await _fixture(session, marker)

        session.add(
            ServiceZoneOffering(
                service_area_id=area.id,
                service_id=service.id,
                active=True,
                regular_service_enabled=True,
                emergency_service_enabled=False,
            )
        )
        await session.commit()

        slots = await AvailabilityService(session).search(
            AvailabilitySearchRequest(
                service_id=service.id,
                address_id=address.id,
                date_from=service_date,
                date_to=service_date,
            )
        )
        assert len(slots) > 0


@pytest.mark.asyncio
async def test_search_allows_service_with_no_zone_offering_row_at_all() -> None:
    # A zone that hasn't been configured with per-service offerings must keep
    # working exactly as before -- zone-level coverage alone is still enough.
    marker = uuid.uuid4().hex
    async with SessionLocal() as session:
        area, address, service, vendor, service_date = await _fixture(session, marker)

        slots = await AvailabilityService(session).search(
            AvailabilitySearchRequest(
                service_id=service.id,
                address_id=address.id,
                date_from=service_date,
                date_to=service_date,
            )
        )
        assert len(slots) > 0
