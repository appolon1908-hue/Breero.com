import uuid
from typing import Any

from geoalchemy2 import Geography
from sqlalchemy import and_, cast, exists, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.booking.models import Address, LegalEntity, ServiceArea
from app.domains.catalog.models import Service

from .models import PostalCodeImport, ServiceZoneOffering, ServiceZonePostalCode
from .schemas import base_postal_code, normalize_postal_code


class GeographyRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def active_service(self, service_id: uuid.UUID) -> Service | None:
        return await self.session.scalar(
            select(Service).where(
                Service.id == service_id,
                Service.is_active.is_(True),
            )
        )

    async def active_services(
        self,
        service_ids: list[uuid.UUID],
    ) -> list[Service]:
        if not service_ids:
            return []
        return list(
            (
                await self.session.scalars(
                    select(Service).where(
                        Service.id.in_(service_ids),
                        Service.is_active.is_(True),
                    )
                )
            ).all()
        )

    async def active_legal_entity(
        self,
        legal_entity_id: uuid.UUID,
    ) -> LegalEntity | None:
        return await self.session.scalar(
            select(LegalEntity).where(
                LegalEntity.id == legal_entity_id,
                LegalEntity.active.is_(True),
            )
        )

    async def zone(
        self,
        service_area_id: uuid.UUID,
        *,
        lock: bool = False,
    ) -> ServiceArea | None:
        query = select(ServiceArea).where(ServiceArea.id == service_area_id)
        if lock:
            query = query.with_for_update()
        return await self.session.scalar(query)

    async def zone_view(
        self,
        service_area_id: uuid.UUID,
    ) -> tuple[ServiceArea, float | None, float | None] | None:
        row = (
            await self.session.execute(
                select(
                    ServiceArea,
                    func.ST_Y(ServiceArea.center),
                    func.ST_X(ServiceArea.center),
                ).where(ServiceArea.id == service_area_id)
            )
        ).first()
        if not row:
            return None
        return row[0], row[1], row[2]

    async def list_zones(
        self,
        *,
        active: bool | None,
        country_code: str | None,
        state_code: str | None,
        city: str | None,
        postal_code: str | None,
        page: int,
        page_size: int,
    ) -> tuple[list[tuple[ServiceArea, float | None, float | None]], int]:
        conditions: list[Any] = []
        if active is not None:
            conditions.append(ServiceArea.active.is_(active))
        if country_code:
            conditions.append(ServiceArea.country_code == country_code)
        if state_code:
            conditions.append(ServiceArea.state_code == state_code)
        if city:
            conditions.append(func.lower(ServiceArea.city) == city.lower())
        if postal_code:
            normalized = normalize_postal_code(postal_code)
            candidates = list(
                dict.fromkeys([normalized, base_postal_code(normalized)])
            )
            conditions.append(
                exists(
                    select(ServiceZonePostalCode.id).where(
                        ServiceZonePostalCode.service_area_id == ServiceArea.id,
                        ServiceZonePostalCode.postal_code.in_(candidates),
                    )
                )
            )

        query = (
            select(
                ServiceArea,
                func.ST_Y(ServiceArea.center),
                func.ST_X(ServiceArea.center),
            )
            .where(*conditions)
            .order_by(
                ServiceArea.priority.desc(),
                ServiceArea.name,
                ServiceArea.id,
            )
            .limit(page_size)
            .offset((page - 1) * page_size)
        )
        count_query = select(func.count()).select_from(ServiceArea).where(*conditions)
        rows = list((await self.session.execute(query)).all())
        total = int(await self.session.scalar(count_query) or 0)
        return [(row[0], row[1], row[2]) for row in rows], total

    async def match_zone(
        self,
        *,
        latitude: float,
        longitude: float,
        postal_code: str,
        country_code: str,
        state_code: str | None,
        city: str | None,
        service_id: uuid.UUID | None,
    ) -> tuple[ServiceArea, LegalEntity] | None:
        normalized = normalize_postal_code(postal_code)
        candidates = list(
            dict.fromkeys([normalized, base_postal_code(normalized)])
        )
        point = func.ST_SetSRID(func.ST_MakePoint(longitude, latitude), 4326)

        configured_postal = exists(
            select(ServiceZonePostalCode.id).where(
                ServiceZonePostalCode.service_area_id == ServiceArea.id
            )
        )
        matching_postal = exists(
            select(ServiceZonePostalCode.id).where(
                ServiceZonePostalCode.service_area_id == ServiceArea.id,
                ServiceZonePostalCode.active.is_(True),
                ServiceZonePostalCode.regular_service_enabled.is_(True),
                ServiceZonePostalCode.postal_code.in_(candidates),
            )
        )
        boundary_match = and_(
            ServiceArea.boundary.is_not(None),
            func.ST_Covers(ServiceArea.boundary, point),
        )
        radius_match = and_(
            ServiceArea.center.is_not(None),
            ServiceArea.radius_meters.is_not(None),
            func.ST_DWithin(
                cast(
                    ServiceArea.center,
                    Geography(geometry_type="POINT", srid=4326),
                ),
                cast(
                    point,
                    Geography(geometry_type="POINT", srid=4326),
                ),
                ServiceArea.radius_meters,
            ),
        )
        coarse_only = and_(
            ~configured_postal,
            ServiceArea.boundary.is_(None),
            or_(
                ServiceArea.center.is_(None),
                ServiceArea.radius_meters.is_(None),
            ),
            or_(
                ServiceArea.city.is_not(None),
                ServiceArea.state_code.is_not(None),
            ),
        )

        conditions: list[Any] = [
            ServiceArea.active.is_(True),
            LegalEntity.active.is_(True),
            or_(
                ServiceArea.country_code.is_(None),
                ServiceArea.country_code == country_code,
            ),
            or_(
                ServiceArea.state_code.is_(None),
                ServiceArea.state_code == state_code,
            ),
            or_(matching_postal, boundary_match, radius_match, coarse_only),
        ]
        if city:
            conditions.append(
                or_(
                    ServiceArea.city.is_(None),
                    func.lower(ServiceArea.city) == city.lower(),
                )
            )
        else:
            conditions.append(ServiceArea.city.is_(None))
        if service_id:
            conditions.append(
                exists(
                    select(ServiceZoneOffering.id).where(
                        ServiceZoneOffering.service_area_id == ServiceArea.id,
                        ServiceZoneOffering.service_id == service_id,
                        ServiceZoneOffering.active.is_(True),
                        ServiceZoneOffering.regular_service_enabled.is_(True),
                    )
                )
            )

        row = (
            await self.session.execute(
                select(ServiceArea, LegalEntity)
                .join(
                    LegalEntity,
                    LegalEntity.id == ServiceArea.legal_entity_id,
                )
                .where(*conditions)
                .order_by(
                    ServiceArea.priority.desc(),
                    ServiceArea.name,
                    ServiceArea.id,
                )
                .limit(1)
            )
        ).first()
        return (row[0], row[1]) if row else None

    async def add_address(self, address: Address) -> Address:
        self.session.add(address)
        await self.session.flush()
        return address

    async def offerings(
        self,
        service_area_id: uuid.UUID,
        *,
        include_inactive: bool = False,
    ) -> list[ServiceZoneOffering]:
        query = select(ServiceZoneOffering).where(
            ServiceZoneOffering.service_area_id == service_area_id
        )
        if not include_inactive:
            query = query.where(ServiceZoneOffering.active.is_(True))
        return list(
            (
                await self.session.scalars(
                    query.order_by(ServiceZoneOffering.service_id)
                )
            ).all()
        )

    async def replace_offerings(
        self,
        service_area_id: uuid.UUID,
        service_ids: list[uuid.UUID],
        *,
        regular_service_enabled: bool,
        emergency_service_enabled: bool,
    ) -> None:
        existing = {
            item.service_id: item
            for item in (
                await self.session.scalars(
                    select(ServiceZoneOffering)
                    .where(ServiceZoneOffering.service_area_id == service_area_id)
                    .with_for_update()
                )
            ).all()
        }
        requested = set(service_ids)
        for service_id, offering in existing.items():
            offering.active = service_id in requested
            if offering.active:
                offering.regular_service_enabled = regular_service_enabled
                offering.emergency_service_enabled = emergency_service_enabled
        for service_id in requested - set(existing):
            self.session.add(
                ServiceZoneOffering(
                    service_area_id=service_area_id,
                    service_id=service_id,
                    active=True,
                    regular_service_enabled=regular_service_enabled,
                    emergency_service_enabled=emergency_service_enabled,
                )
            )
        await self.session.flush()

    async def postal_codes_by_zone(
        self,
        service_area_id: uuid.UUID,
        postal_codes: list[str],
        *,
        lock: bool = False,
    ) -> list[ServiceZonePostalCode]:
        normalized = [normalize_postal_code(value) for value in postal_codes]
        if not normalized:
            return []
        query = select(ServiceZonePostalCode).where(
            ServiceZonePostalCode.service_area_id == service_area_id,
            ServiceZonePostalCode.postal_code.in_(normalized),
        )
        if lock:
            query = query.with_for_update()
        return list((await self.session.scalars(query)).all())

    async def postal_code(
        self,
        postal_code_id: uuid.UUID,
        *,
        lock: bool = False,
    ) -> ServiceZonePostalCode | None:
        query = select(ServiceZonePostalCode).where(
            ServiceZonePostalCode.id == postal_code_id
        )
        if lock:
            query = query.with_for_update()
        return await self.session.scalar(query)

    async def postal_by_zone_and_code(
        self,
        service_area_id: uuid.UUID,
        postal_code: str,
        *,
        lock: bool = False,
    ) -> ServiceZonePostalCode | None:
        query = select(ServiceZonePostalCode).where(
            ServiceZonePostalCode.service_area_id == service_area_id,
            ServiceZonePostalCode.postal_code
            == normalize_postal_code(postal_code),
        )
        if lock:
            query = query.with_for_update()
        return await self.session.scalar(query)

    async def list_postal_codes(
        self,
        *,
        service_area_id: uuid.UUID | None,
        postal_code: str | None,
        state_code: str | None,
        active: bool | None,
        page: int,
        page_size: int,
    ) -> tuple[list[ServiceZonePostalCode], int]:
        conditions: list[Any] = []
        if service_area_id:
            conditions.append(
                ServiceZonePostalCode.service_area_id == service_area_id
            )
        if postal_code:
            conditions.append(
                ServiceZonePostalCode.postal_code
                == normalize_postal_code(postal_code)
            )
        if state_code:
            conditions.append(ServiceZonePostalCode.state_code == state_code)
        if active is not None:
            conditions.append(ServiceZonePostalCode.active.is_(active))
        query = (
            select(ServiceZonePostalCode)
            .where(*conditions)
            .order_by(
                ServiceZonePostalCode.priority.desc(),
                ServiceZonePostalCode.postal_code,
                ServiceZonePostalCode.id,
            )
            .limit(page_size)
            .offset((page - 1) * page_size)
        )
        count_query = (
            select(func.count())
            .select_from(ServiceZonePostalCode)
            .where(*conditions)
        )
        items = list((await self.session.scalars(query)).all())
        total = int(await self.session.scalar(count_query) or 0)
        return items, total

    async def zone_postal_codes(
        self,
        service_area_id: uuid.UUID,
        *,
        active_only: bool = False,
    ) -> list[ServiceZonePostalCode]:
        query = select(ServiceZonePostalCode).where(
            ServiceZonePostalCode.service_area_id == service_area_id
        )
        if active_only:
            query = query.where(ServiceZonePostalCode.active.is_(True))
        return list(
            (
                await self.session.scalars(
                    query.order_by(
                        ServiceZonePostalCode.priority.desc(),
                        ServiceZonePostalCode.postal_code,
                    )
                )
            ).all()
        )

    async def sync_legacy_postal_codes(
        self,
        service_area_id: uuid.UUID,
    ) -> None:
        zone = await self.zone(service_area_id, lock=True)
        if not zone:
            return
        rows = await self.zone_postal_codes(service_area_id, active_only=True)
        # The legacy ServiceArea.postal_codes array is what the existing booking
        # domain (AddressService.validate / AvailabilityService.search) matches
        # against for ordinary bookings. An emergency-only row here must not leak
        # into it, or an address that should only accept emergency dispatch would
        # be treated as fully serviceable for regular bookings too.
        zone.postal_codes = list(
            dict.fromkeys(
                base_postal_code(row.postal_code)
                for row in rows
                if row.regular_service_enabled
            )
        )
        await self.session.flush()

    async def postal_import_by_key(
        self,
        idempotency_key: str,
    ) -> PostalCodeImport | None:
        return await self.session.scalar(
            select(PostalCodeImport).where(
                PostalCodeImport.idempotency_key == idempotency_key
            )
        )

    async def postal_import(
        self,
        import_id: uuid.UUID,
    ) -> PostalCodeImport | None:
        return await self.session.get(PostalCodeImport, import_id)
