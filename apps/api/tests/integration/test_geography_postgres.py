import os
import uuid

import pytest
from geoalchemy2.elements import WKTElement
from sqlalchemy import select

from app.core.errors import DomainError
from app.db.session import SessionLocal
from app.domains.auth.models import User, UserRole
from app.domains.booking.models import LegalEntity, ServiceArea
from app.domains.catalog.models import Service
from app.domains.common.outbox import AuditLog
from app.domains.geography.models import (
    ServiceZoneOffering,
    ServiceZonePostalCode,
)
from app.domains.geography.schemas import (
    AddressValidationRequest,
    PostalCodeImportRequest,
    PostalCodeUpdate,
    ServiceAreaCheckRequest,
    ServiceZoneCreate,
    ServiceZoneUpdate,
)
from app.domains.geography.service import (
    AdminPostalCodeService,
    AdminServiceZoneService,
    GeographyService,
)
from app.integrations.geocoding import FakeGeocodingAdapter, GeocodedAddress

pytestmark = pytest.mark.skipif(
    not os.getenv("DATABASE_URL", "").startswith("postgresql"),
    reason="geography integration requires PostgreSQL/PostGIS",
)


def _service(marker: str, suffix: str) -> Service:
    return Service(
        slug=f"geo-{suffix}-{marker}",
        name=f"Geography {suffix}",
        description="Geography integration fixture",
        category="test",
        pricing_model="request_only",
        duration_minutes=60,
        is_active=True,
        is_bookable=False,
    )


def _admin(marker: str) -> User:
    return User(
        email=f"geo-admin-{marker}@example.test",
        password_hash="disabled",
        full_name="Geography Admin",
        role=UserRole.admin,
        is_active=True,
        email_verified=True,
    )


@pytest.mark.asyncio
async def test_address_validation_persists_evidence_without_leaking_candidates() -> None:
    marker = uuid.uuid4().hex
    async with SessionLocal() as session:
        entity = LegalEntity(
            code=f"GEO-{marker[:8]}",
            name="Geography Address",
            currency="USD",
            active=True,
        )
        service = _service(marker, "address")
        session.add_all([entity, service])
        await session.flush()
        zone = ServiceArea(
            legal_entity_id=entity.id,
            name="Houston Central",
            country_code="US",
            state_code="TX",
            city="Houston",
            postal_codes=[],
            priority=100,
            emergency_enabled=False,
            version=1,
            active=True,
        )
        session.add(zone)
        await session.flush()
        session.add_all(
            [
                ServiceZoneOffering(
                    service_area_id=zone.id,
                    service_id=service.id,
                    active=True,
                    regular_service_enabled=True,
                    emergency_service_enabled=False,
                ),
                ServiceZonePostalCode(
                    service_area_id=zone.id,
                    postal_code="77001",
                    city="Houston",
                    state_code="TX",
                    active=True,
                    regular_service_enabled=True,
                    emergency_service_enabled=False,
                    priority=100,
                    version=1,
                ),
            ]
        )
        await session.commit()

        provider_result = GeocodedAddress(
            "123 Main St, Houston, TX 77001-1234",
            "123 Main St",
            "Houston",
            "77001",
            "US",
            29.7604,
            -95.3698,
            "fake",
            "address-fixture",
            1.0,
            "exact",
            "TX",
            "America/Chicago",
            "Suite 2",
            "Harris County",
            "1234",
        )
        result = await GeographyService(
            session,
            provider=FakeGeocodingAdapter(provider_result),
        ).validate_address(
            AddressValidationRequest(
                address_line_1="123 Main St",
                address_line_2="Suite 2",
                city="Houston",
                state="TX",
                postal_code="77001-1234",
            ),
            correlation_id=f"geo-{marker}",
        )

        assert result.covered is True
        assert result.service_zone and result.service_zone.id == zone.id
        assert result.timezone == "America/Chicago"
        assert result.address.postal_code_plus4 == "1234"
        assert "provider_id" not in result.model_dump()
        audit = await session.scalar(
            select(AuditLog).where(
                AuditLog.resource_id == result.address_id,
                AuditLog.action == "address.validate",
            )
        )
        assert audit
        assert audit.metadata_json["correlation_id"] == f"geo-{marker}"


@pytest.mark.asyncio
async def test_zip4_priority_inactive_coverage_and_postgis_radius_are_fail_closed() -> None:
    marker = uuid.uuid4().hex
    async with SessionLocal() as session:
        entity = LegalEntity(
            code=f"ROUTE-{marker[:8]}",
            name="Routing Tests",
            currency="USD",
            active=True,
        )
        zip_service = _service(marker, "zip")
        inactive_service = _service(marker, "inactive")
        radius_service = _service(marker, "radius")
        session.add_all([entity, zip_service, inactive_service, radius_service])
        await session.flush()

        base_zone = ServiceArea(
            legal_entity_id=entity.id,
            name="Base ZIP",
            country_code="US",
            state_code="TX",
            city="Houston",
            postal_codes=[],
            priority=10,
            emergency_enabled=False,
            version=1,
            active=True,
        )
        exact_zone = ServiceArea(
            legal_entity_id=entity.id,
            name="Exact ZIP+4",
            country_code="US",
            state_code="TX",
            city="Houston",
            postal_codes=[],
            priority=100,
            emergency_enabled=False,
            version=1,
            active=True,
        )
        inactive_zone = ServiceArea(
            legal_entity_id=entity.id,
            name="Inactive ZIP",
            country_code="US",
            state_code="TX",
            city="Austin",
            postal_codes=[],
            priority=100,
            emergency_enabled=False,
            version=1,
            active=True,
        )
        radius_zone = ServiceArea(
            legal_entity_id=entity.id,
            name="Houston Radius",
            country_code="US",
            state_code="TX",
            city=None,
            postal_codes=[],
            center=WKTElement("POINT(-95.3698 29.7604)", srid=4326),
            radius_meters=16000,
            priority=100,
            emergency_enabled=False,
            version=1,
            active=True,
        )
        session.add_all([base_zone, exact_zone, inactive_zone, radius_zone])
        await session.flush()
        session.add_all(
            [
                ServiceZoneOffering(
                    service_area_id=base_zone.id,
                    service_id=zip_service.id,
                    active=True,
                    regular_service_enabled=True,
                    emergency_service_enabled=False,
                ),
                ServiceZoneOffering(
                    service_area_id=exact_zone.id,
                    service_id=zip_service.id,
                    active=True,
                    regular_service_enabled=True,
                    emergency_service_enabled=False,
                ),
                ServiceZoneOffering(
                    service_area_id=inactive_zone.id,
                    service_id=inactive_service.id,
                    active=True,
                    regular_service_enabled=True,
                    emergency_service_enabled=False,
                ),
                ServiceZoneOffering(
                    service_area_id=radius_zone.id,
                    service_id=radius_service.id,
                    active=True,
                    regular_service_enabled=True,
                    emergency_service_enabled=False,
                ),
                ServiceZonePostalCode(
                    service_area_id=base_zone.id,
                    postal_code="77001",
                    city="Houston",
                    state_code="TX",
                    active=True,
                    regular_service_enabled=True,
                    emergency_service_enabled=False,
                    priority=10,
                    version=1,
                ),
                ServiceZonePostalCode(
                    service_area_id=exact_zone.id,
                    postal_code="77001-1234",
                    city="Houston",
                    state_code="TX",
                    active=True,
                    regular_service_enabled=True,
                    emergency_service_enabled=False,
                    priority=100,
                    version=1,
                ),
                ServiceZonePostalCode(
                    service_area_id=inactive_zone.id,
                    postal_code="78701",
                    city="Austin",
                    state_code="TX",
                    active=False,
                    regular_service_enabled=True,
                    emergency_service_enabled=False,
                    priority=100,
                    version=1,
                ),
            ]
        )
        await session.commit()

        geography = GeographyService(session)
        exact = await geography.check_service_area(
            ServiceAreaCheckRequest(
                latitude=29.7604,
                longitude=-95.3698,
                postal_code="77001-1234",
                service_id=zip_service.id,
                city="Houston",
                state="TX",
            )
        )
        assert exact.covered and exact.service_zone
        assert exact.service_zone.id == exact_zone.id

        inactive = await geography.check_service_area(
            ServiceAreaCheckRequest(
                latitude=30.2672,
                longitude=-97.7431,
                postal_code="78701",
                service_id=inactive_service.id,
                city="Austin",
                state="TX",
            )
        )
        assert inactive.covered is False

        inside = await geography.check_service_area(
            ServiceAreaCheckRequest(
                latitude=29.7604,
                longitude=-95.3698,
                postal_code="99999",
                service_id=radius_service.id,
                state="TX",
            )
        )
        outside = await geography.check_service_area(
            ServiceAreaCheckRequest(
                latitude=32.7767,
                longitude=-96.7970,
                postal_code="99999",
                service_id=radius_service.id,
                state="TX",
            )
        )
        assert inside.covered is True
        assert outside.covered is False


@pytest.mark.asyncio
async def test_admin_zone_and_postal_import_are_versioned_audited_and_idempotent() -> None:
    marker = uuid.uuid4().hex
    async with SessionLocal() as session:
        entity = LegalEntity(
            code=f"ADMIN-{marker[:8]}",
            name="Geography Admin",
            currency="USD",
            active=True,
        )
        service = _service(marker, "admin")
        actor = _admin(marker)
        session.add_all([entity, service, actor])
        await session.commit()
        await session.refresh(entity)
        await session.refresh(service)
        await session.refresh(actor)
        actor_id = actor.id

        zone_service = AdminServiceZoneService(session)
        zone = await zone_service.create_zone(
            actor,
            ServiceZoneCreate(
                legal_entity_id=entity.id,
                name="Administrative Zone",
                state_code="TX",
                city="Houston",
                postal_codes=["77001"],
                service_ids=[service.id],
                priority=50,
            ),
            correlation_id=f"admin-{marker}",
        )
        assert zone.version == 1
        assert zone.postal_codes == ["77001"]

        postal_service = AdminPostalCodeService(session)
        command = PostalCodeImportRequest.model_validate(
            {
                "service_area_id": str(zone.id),
                "rows": [
                    {
                        "postal_code": "77002",
                        "city": "Houston",
                        "state_code": "TX",
                    },
                    {
                        "postal_code": "770031234",
                        "city": "Houston",
                        "state_code": "TX",
                    },
                ],
            }
        )
        key = f"postal-import:{marker}"
        first = await postal_service.import_postal_codes(
            actor,
            command,
            idempotency_key=key,
            correlation_id=f"admin-{marker}",
        )
        replay = await postal_service.import_postal_codes(
            actor,
            command,
            idempotency_key=key,
            correlation_id=f"admin-{marker}",
        )
        assert replay.id == first.id
        assert first.imported_rows == 2
        assert first.rejected_rows == 0

        changed = command.model_copy(
            update={
                "rows": [
                    command.rows[0].model_copy(update={"postal_code": "77004"})
                ]
            }
        )
        with pytest.raises(DomainError) as conflict:
            await postal_service.import_postal_codes(
                actor,
                changed,
                idempotency_key=key,
            )
        assert conflict.value.code == "IDEMPOTENCY_CONFLICT"
        await session.rollback()
        await session.refresh(actor)

        rows = await postal_service.list_postal_codes(
            service_area_id=zone.id,
            postal_code="77002",
            state_code="TX",
            active=True,
            page=1,
            page_size=25,
        )
        assert rows.total == 1
        row = rows.items[0]
        updated = await postal_service.update_postal_code(
            row.id,
            actor,
            PostalCodeUpdate(priority=75),
            expected_version=row.version,
        )
        assert updated.priority == 75
        with pytest.raises(DomainError) as stale:
            await postal_service.update_postal_code(
                row.id,
                actor,
                PostalCodeUpdate(priority=76),
                expected_version=row.version,
            )
        assert stale.value.code == "VERSION_CONFLICT"
        await session.rollback()

        audits = list(
            (
                await session.scalars(
                    select(AuditLog).where(
                        AuditLog.actor_id == actor_id,
                        AuditLog.action.in_(
                            {
                                "service_zone.create",
                                "postal_code.import",
                                "postal_code.update",
                            }
                        ),
                    )
                )
            ).all()
        )
        assert {item.action for item in audits} == {
            "service_zone.create",
            "postal_code.import",
            "postal_code.update",
        }


@pytest.mark.asyncio
async def test_emergency_only_postal_codes_do_not_leak_into_legacy_coverage() -> None:
    # Regression test: sync_legacy_postal_codes used to copy every active postal
    # code into the legacy ServiceArea.postal_codes array regardless of
    # regular_service_enabled. That array is exactly what the existing booking
    # domain (AddressService.validate / AvailabilityService.search) matches
    # against for ordinary bookings, so an emergency-only postal code leaking in
    # would make an address bookable for regular service when it shouldn't be.
    marker = uuid.uuid4().hex
    async with SessionLocal() as session:
        entity = LegalEntity(
            code=f"EMRG-{marker[:8]}", name="Emergency Zone Entity", currency="USD", active=True
        )
        service = _service(marker, "emergency")
        actor = _admin(marker)
        session.add_all([entity, service, actor])
        await session.commit()
        await session.refresh(entity)

        zone_service = AdminServiceZoneService(session)
        zone = await zone_service.create_zone(
            actor,
            ServiceZoneCreate(
                legal_entity_id=entity.id,
                name="Emergency Coverage Zone",
                postal_codes=["77010"],
                service_ids=[service.id],
            ),
            correlation_id=f"emrg-{marker}",
        )
        assert zone.postal_codes == ["77010"]

        postal_service = AdminPostalCodeService(session)
        await postal_service.import_postal_codes(
            actor,
            PostalCodeImportRequest.model_validate(
                {
                    "service_area_id": str(zone.id),
                    "rows": [
                        {
                            "postal_code": "77011",
                            "city": "Houston",
                            "state_code": "TX",
                            "regular_service_enabled": False,
                            "emergency_service_enabled": True,
                        }
                    ],
                }
            ),
            idempotency_key=f"postal-import-emergency:{marker}",
        )

        refreshed = await session.get(ServiceArea, zone.id)
        assert refreshed is not None
        assert refreshed.postal_codes == ["77010"]


@pytest.mark.asyncio
async def test_deactivating_all_postal_codes_fails_coverage_selector_check() -> None:
    # Regression test: _ensure_coverage_selector used to count inactive postal
    # codes as valid coverage, so deactivating a zone's only postal code left an
    # active zone with zero live coverage instead of being rejected.
    marker = uuid.uuid4().hex
    async with SessionLocal() as session:
        entity = LegalEntity(
            code=f"COV-{marker[:8]}", name="Coverage Zone Entity", currency="USD", active=True
        )
        service = _service(marker, "coverage")
        actor = _admin(marker)
        session.add_all([entity, service, actor])
        await session.commit()
        await session.refresh(entity)

        zone_service = AdminServiceZoneService(session)
        zone = await zone_service.create_zone(
            actor,
            ServiceZoneCreate(
                legal_entity_id=entity.id,
                name="Postal-Only Coverage Zone",
                postal_codes=["77020"],
                service_ids=[service.id],
            ),
            correlation_id=f"cov-{marker}",
        )

        postal_service = AdminPostalCodeService(session)
        rows = await postal_service.list_postal_codes(
            service_area_id=zone.id,
            postal_code=None,
            state_code=None,
            active=None,
            page=1,
            page_size=25,
        )
        row = rows.items[0]
        await postal_service.update_postal_code(
            row.id,
            actor,
            PostalCodeUpdate(active=False),
            expected_version=row.version,
        )

        with pytest.raises(DomainError) as coverage_error:
            await zone_service.update_zone(
                zone.id,
                actor,
                ServiceZoneUpdate(priority=60),
                expected_version=zone.version,
            )
        assert coverage_error.value.code == "SERVICE_ZONE_COVERAGE_REQUIRED"
