import os
import uuid
from datetime import UTC, datetime, time, timedelta

import pytest
from geoalchemy2.elements import WKTElement
from sqlalchemy import select

from app.core.errors import DomainError
from app.db.session import SessionLocal
from app.domains.booking.models import (
    Address,
    Booking,
    BookingStatus,
    Customer,
    LegalEntity,
    ProviderServiceCoverage,
    ProviderWorkingHours,
    ServiceArea,
)
from app.domains.booking.schemas import CustomerInput
from app.domains.booking_intents.models import BookingIntent, BookingIntentStatus
from app.domains.booking_intents.schemas import (
    BookingIntentCreate,
    BookingIntentUpdate,
    SlotSelection,
)
from app.domains.booking_intents.service import BookingIntentService
from app.domains.catalog.models import Service
from app.domains.common.outbox import AuditLog
from app.domains.workforce.models import Vendor, VendorStatus, Worker, WorkerStatus

pytestmark = pytest.mark.skipif(
    not os.getenv("DATABASE_URL", "").startswith("postgresql"),
    reason="booking-intent integration requires PostgreSQL",
)


@pytest.mark.asyncio
async def test_booking_intent_persists_is_session_scoped_and_uses_versions() -> None:
    marker = uuid.uuid4().hex
    owner_session = uuid.uuid4()
    other_session = uuid.uuid4()

    async with SessionLocal() as session:
        catalog_service = Service(
            slug=f"intent-service-{marker}",
            name="Intent service",
            description="Booking intent integration fixture",
            category="test",
            pricing_model="request_only",
            duration_minutes=60,
            is_active=True,
            is_bookable=False,
        )
        session.add(catalog_service)
        await session.commit()
        await session.refresh(catalog_service)

        service = BookingIntentService(session)
        intent = await service.create(
            BookingIntentCreate(service_id=catalog_service.id),
            owner_session,
        )
        assert intent.status == BookingIntentStatus.DRAFT
        assert intent.version == 1
        assert intent.expires_at > datetime.now(UTC) + timedelta(minutes=110)

        persisted = await session.scalar(
            select(BookingIntent).where(BookingIntent.id == intent.id)
        )
        assert persisted and persisted.anonymous_session_id == owner_session

        with pytest.raises(DomainError) as invisible:
            await service.get(intent.id, other_session)
        assert invisible.value.status_code == 404

        requested_date = datetime.now(UTC).date() + timedelta(days=2)
        updated = await service.update(
            intent.id,
            owner_session,
            BookingIntentUpdate(
                timezone_id="America/Chicago",
                requested_date=requested_date,
            ),
            expected_version=1,
        )
        assert updated.timezone_id == "America/Chicago"
        assert updated.requested_date == requested_date
        assert updated.version == 2

        with pytest.raises(DomainError) as conflict:
            await service.update(
                intent.id,
                owner_session,
                BookingIntentUpdate(requested_date=requested_date + timedelta(days=1)),
                expected_version=1,
            )
        assert conflict.value.code == "BOOKING_INTENT_VERSION_CONFLICT"

        await service.abandon(
            intent.id,
            owner_session,
            expected_version=2,
        )
        await session.refresh(intent)
        assert intent.status == BookingIntentStatus.EXPIRED
        assert intent.version == 3

        actions = set(
            (
                await session.scalars(
                    select(AuditLog.action).where(AuditLog.resource_id == intent.id)
                )
            ).all()
        )
        assert {
            "booking_intent.create",
            "booking_intent.update",
            "booking_intent.abandon",
        } <= actions


@pytest.mark.asyncio
async def test_booking_intent_validates_address_coverage_availability_and_submits() -> None:
    marker = uuid.uuid4().hex
    owner_session = uuid.uuid4()
    service_date = (datetime.now(UTC) + timedelta(days=2)).date()

    async with SessionLocal() as session:
        entity = LegalEntity(code=f"BI-{marker[:8]}", name="BI Entity", currency="USD")
        session.add(entity)
        await session.flush()
        area = ServiceArea(legal_entity_id=entity.id, name="BI Area", country_code="US")
        session.add(area)
        await session.flush()

        bookable_service = Service(
            slug=f"bi-bookable-{marker}",
            name="BI Bookable",
            description="Bookable fixture",
            category="test",
            pricing_model="fixed",
            duration_minutes=60,
            is_active=True,
            is_bookable=True,
        )
        unbookable_service = Service(
            slug=f"bi-unbookable-{marker}",
            name="BI Unbookable",
            description="Request-only fixture",
            category="test",
            pricing_model="request_only",
            duration_minutes=60,
            is_active=True,
            is_bookable=False,
        )
        session.add_all([bookable_service, unbookable_service])
        await session.flush()

        vendor = Vendor(
            legal_name="BI Vendor",
            display_name="BI Vendor",
            email=f"vendor-{marker}@example.test",
            phone="+15551234567",
            status=VendorStatus.ACTIVE,
            capabilities=[],
        )
        session.add(vendor)
        await session.flush()
        worker = Worker(
            vendor_id=vendor.id,
            first_name="BI",
            last_name="Tech",
            email=f"worker-{marker}@example.test",
            phone="+15557654321",
            status=WorkerStatus.ACTIVE,
            skills=[],
        )
        session.add(worker)
        await session.flush()
        session.add_all(
            [
                ProviderServiceCoverage(
                    worker_id=worker.id, service_id=bookable_service.id, postal_code="78701"
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

        covered_address = Address(
            formatted_address="1 BI Way, Austin",
            line1="1 BI Way",
            city="Austin",
            postal_code="78701",
            country_code="US",
            location=WKTElement("POINT(-98 30)", srid=4326),
            service_area_id=area.id,
            timezone_name="America/Chicago",
        )
        uncovered_address = Address(
            formatted_address="2 BI Way, Austin",
            line1="2 BI Way",
            city="Austin",
            postal_code="78701",
            country_code="US",
            location=WKTElement("POINT(-98 30)", srid=4326),
            timezone_name="America/Chicago",
        )
        other_customer = Customer(
            first_name="Other",
            last_name="Owner",
            email=f"other-{marker}@example.test",
            phone="+15550001111",
        )
        session.add_all([covered_address, uncovered_address, other_customer])
        await session.flush()
        someone_elses_address = Address(
            formatted_address="3 BI Way, Austin",
            line1="3 BI Way",
            city="Austin",
            postal_code="78701",
            country_code="US",
            location=WKTElement("POINT(-98 30)", srid=4326),
            service_area_id=area.id,
            timezone_name="America/Chicago",
            customer_id=other_customer.id,
        )
        session.add(someone_elses_address)
        await session.commit()

        service = BookingIntentService(session)
        intent = await service.create(
            BookingIntentCreate(service_id=bookable_service.id), owner_session
        )
        version = intent.version

        # An address already linked to another customer must be rejected -- an
        # anonymous session has no identity of its own to check ownership against,
        # so accepting it would let any session attach any known customer's address.
        with pytest.raises(DomainError) as ownership:
            await service.update(
                intent.id,
                owner_session,
                BookingIntentUpdate(address_id=someone_elses_address.id),
                expected_version=version,
            )
        assert ownership.value.code == "ADDRESS_NOT_FOUND"

        # A real, unclaimed address outside any service area is accepted but only
        # reaches ADDRESS_VALIDATED, not COVERAGE_CONFIRMED.
        updated = await service.update(
            intent.id,
            owner_session,
            BookingIntentUpdate(address_id=uncovered_address.id),
            expected_version=version,
        )
        version = updated.version
        assert updated.status == BookingIntentStatus.ADDRESS_VALIDATED

        # Switching to a covered address reaches COVERAGE_CONFIRMED, and the
        # switch itself resets the now-stale timezone/date from the prior address.
        updated = await service.update(
            intent.id,
            owner_session,
            BookingIntentUpdate(
                address_id=covered_address.id,
                timezone_id="America/Chicago",
                requested_date=service_date,
            ),
            expected_version=version,
        )
        version = updated.version
        assert updated.status == BookingIntentStatus.COVERAGE_CONFIRMED
        assert updated.timezone_id == "America/Chicago"
        assert updated.requested_date == service_date

        # A fabricated slot that doesn't match real provider capacity is rejected.
        with pytest.raises(DomainError) as unavailable:
            await service.update(
                intent.id,
                owner_session,
                BookingIntentUpdate(
                    selected_slot=SlotSelection(
                        slot_token="fabricated-slot-token-000000",
                        start_local="03:00",
                        end_local="04:00",
                    )
                ),
                expected_version=version,
            )
        assert unavailable.value.code == "SLOT_UNAVAILABLE"

        # The real available window (07:00-08:00 local, within provider hours) is accepted.
        real_slot = SlotSelection(
            slot_token="real-slot-token-0000000000000",
            start_local="07:00",
            end_local="08:00",
        )
        updated = await service.update(
            intent.id,
            owner_session,
            BookingIntentUpdate(selected_slot=real_slot),
            expected_version=version,
        )
        version = updated.version
        assert updated.status == BookingIntentStatus.AVAILABILITY_FOUND

        # Explicit null clears the slot and falls back to COVERAGE_CONFIRMED --
        # distinct from omitting the field, and distinct from clear_selected_slot.
        updated = await service.update(
            intent.id,
            owner_session,
            BookingIntentUpdate.model_validate({"selected_slot": None}),
            expected_version=version,
        )
        version = updated.version
        assert updated.selected_slot is None
        assert updated.status == BookingIntentStatus.COVERAGE_CONFIRMED

        # Re-select the real slot to reach a submittable state.
        updated = await service.update(
            intent.id,
            owner_session,
            BookingIntentUpdate(selected_slot=real_slot),
            expected_version=version,
        )
        version = updated.version
        assert updated.status == BookingIntentStatus.AVAILABILITY_FOUND

        # A non-bookable service can never reach a real slot selection, even with
        # an otherwise-identical, fully-covered address and real working hours.
        other_intent = await service.create(
            BookingIntentCreate(service_id=unbookable_service.id), owner_session
        )
        other_intent = await service.update(
            other_intent.id,
            owner_session,
            BookingIntentUpdate(
                address_id=covered_address.id,
                timezone_id="America/Chicago",
                requested_date=service_date,
            ),
            expected_version=other_intent.version,
        )
        with pytest.raises(DomainError) as not_bookable:
            await service.update(
                other_intent.id,
                owner_session,
                BookingIntentUpdate(selected_slot=real_slot),
                expected_version=other_intent.version,
            )
        assert not_bookable.value.code == "SERVICE_NOT_BOOKABLE"

        # submit() delegates into the real BookingService.create() and links back.
        booking = await service.submit(
            intent.id,
            owner_session,
            CustomerInput(
                first_name="BI",
                last_name="Customer",
                email=f"customer-{marker}@example.test",
                phone="+15559998888",
            ),
            [],
            expected_version=version,
            idempotency_key=f"bi-submit-{marker}",
        )
        assert isinstance(booking, Booking)
        assert booking.status == BookingStatus.TENTATIVE_HOLD
        assert booking.service_id == bookable_service.id
        assert booking.address_id == covered_address.id

        await session.refresh(intent)
        assert intent.status == BookingIntentStatus.SUBMITTED
        assert intent.booking_id == booking.id

        # A submitted intent cannot be abandoned or edited further.
        with pytest.raises(DomainError):
            await service.abandon(intent.id, owner_session, expected_version=intent.version)
