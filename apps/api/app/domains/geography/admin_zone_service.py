import json
import uuid
from typing import Any

from geoalchemy2.elements import WKTElement
from sqlalchemy import func, select
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import DomainError
from app.domains.auth.models import User
from app.domains.booking.models import ServiceArea
from app.domains.common.clock import Clock, SystemClock
from app.domains.common.outbox import AuditLog

from .models import ServiceZonePostalCode
from .repository import GeographyRepository
from .schemas import (
    Coordinates,
    PostalCodeRead,
    ServiceZoneCoverage,
    ServiceZoneCreate,
    ServiceZoneList,
    ServiceZoneRead,
    ServiceZoneUpdate,
)


class AdminServiceZoneService:
    """Administrative service-zone and normalized postal-routing workflows."""

    def __init__(
        self,
        session: AsyncSession,
        *,
        clock: Clock | None = None,
    ) -> None:
        self.session = session
        self.clock = clock or SystemClock()
        self.repository = GeographyRepository(session)

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
    ) -> ServiceZoneList:
        rows, total = await self.repository.list_zones(
            active=active,
            country_code=country_code,
            state_code=state_code,
            city=city,
            postal_code=postal_code,
            page=page,
            page_size=page_size,
        )
        items = [
            await self._zone_read(area, latitude, longitude)
            for area, latitude, longitude in rows
        ]
        return ServiceZoneList(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
        )

    async def create_zone(
        self,
        actor: User,
        command: ServiceZoneCreate,
        *,
        correlation_id: str | None = None,
    ) -> ServiceZoneRead:
        if not await self.repository.active_legal_entity(command.legal_entity_id):
            raise DomainError(
                "LEGAL_ENTITY_NOT_FOUND",
                "Active legal entity not found.",
                404,
            )
        await self._validate_services(command.service_ids)
        boundary = await self._validated_boundary(command.boundary_geojson)
        zone = ServiceArea(
            legal_entity_id=command.legal_entity_id,
            name=command.name.strip(),
            country_code=command.country_code,
            state_code=command.state_code,
            city=command.city.strip() if command.city else None,
            postal_codes=[],
            center=self._center(
                command.center_latitude,
                command.center_longitude,
            ),
            radius_meters=self._radius_meters(command.radius_miles),
            boundary=boundary,
            priority=command.priority,
            emergency_enabled=command.emergency_enabled,
            version=1,
            active=command.active,
        )
        self.session.add(zone)
        try:
            await self.session.flush()
            await self.repository.replace_offerings(
                zone.id,
                command.service_ids,
                regular_service_enabled=command.regular_service_enabled,
                emergency_service_enabled=command.emergency_enabled,
            )
            for postal_code in command.postal_codes:
                self.session.add(
                    ServiceZonePostalCode(
                        service_area_id=zone.id,
                        postal_code=postal_code,
                        city=zone.city,
                        state_code=zone.state_code,
                        active=True,
                        regular_service_enabled=command.regular_service_enabled,
                        emergency_service_enabled=command.emergency_enabled,
                        priority=zone.priority,
                        version=1,
                    )
                )
            await self.session.flush()
            await self.repository.sync_legacy_postal_codes(zone.id)
            self._audit(
                actor,
                "service_zone.create",
                "service_area",
                zone.id,
                {
                    "service_ids": [str(item) for item in command.service_ids],
                    "postal_code_count": len(command.postal_codes),
                    "priority": zone.priority,
                    "correlation_id": correlation_id,
                },
            )
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise DomainError(
                "SERVICE_ZONE_CONFLICT",
                "Service zone conflicts with existing coverage data.",
                409,
            ) from exc
        return await self.get_zone(zone.id)

    async def get_zone(self, service_area_id: uuid.UUID) -> ServiceZoneRead:
        row = await self.repository.zone_view(service_area_id)
        if not row:
            raise DomainError(
                "SERVICE_ZONE_NOT_FOUND",
                "Service zone not found.",
                404,
            )
        return await self._zone_read(*row)

    async def update_zone(
        self,
        service_area_id: uuid.UUID,
        actor: User,
        command: ServiceZoneUpdate,
        *,
        expected_version: int,
        correlation_id: str | None = None,
    ) -> ServiceZoneRead:
        zone = await self.repository.zone(service_area_id, lock=True)
        if not zone:
            raise DomainError(
                "SERVICE_ZONE_NOT_FOUND",
                "Service zone not found.",
                404,
            )
        self._require_version(zone.version, expected_version, "service zone")
        boundary = (
            await self._validated_boundary(command.boundary_geojson)
            if "boundary_geojson" in command.model_fields_set
            else None
        )
        current_regular = await self._regular_enabled(zone.id)

        values = command.model_dump(
            exclude_unset=True,
            exclude={
                "postal_codes",
                "service_ids",
                "center_latitude",
                "center_longitude",
                "clear_center",
                "radius_miles",
                "clear_radius",
                "boundary_geojson",
                "clear_boundary",
                "regular_service_enabled",
            },
        )
        for field, value in values.items():
            if field == "city" and isinstance(value, str):
                value = value.strip()
            setattr(zone, field, value)

        coordinates = {"center_latitude", "center_longitude"}
        if command.clear_center:
            zone.center = None
            zone.radius_meters = None
        elif coordinates.issubset(command.model_fields_set):
            zone.center = self._center(
                command.center_latitude,
                command.center_longitude,
            )

        if command.clear_radius:
            zone.radius_meters = None
        elif "radius_miles" in command.model_fields_set:
            if command.radius_miles is not None and zone.center is None:
                raise DomainError(
                    "SERVICE_ZONE_CENTER_REQUIRED",
                    "Radius coverage requires a center point.",
                    422,
                )
            zone.radius_meters = self._radius_meters(command.radius_miles)

        if command.clear_boundary:
            zone.boundary = None
        elif "boundary_geojson" in command.model_fields_set:
            zone.boundary = boundary

        regular_enabled = (
            command.regular_service_enabled
            if command.regular_service_enabled is not None
            else current_regular
        )
        if command.service_ids is not None:
            await self._validate_services(command.service_ids)
            await self.repository.replace_offerings(
                zone.id,
                command.service_ids,
                regular_service_enabled=regular_enabled,
                emergency_service_enabled=zone.emergency_enabled,
            )
        elif (
            command.regular_service_enabled is not None
            or command.emergency_enabled is not None
        ):
            offerings = await self.repository.offerings(
                zone.id,
                include_inactive=True,
            )
            for offering in offerings:
                if command.regular_service_enabled is not None:
                    offering.regular_service_enabled = regular_enabled
                if command.emergency_enabled is not None:
                    offering.emergency_service_enabled = zone.emergency_enabled

        if command.postal_codes is not None:
            await self._replace_zone_postal_codes(
                zone,
                command.postal_codes,
                regular_service_enabled=regular_enabled,
            )
        elif (
            command.regular_service_enabled is not None
            or command.emergency_enabled is not None
            or command.priority is not None
        ):
            for row in await self.repository.zone_postal_codes(zone.id):
                if command.regular_service_enabled is not None:
                    row.regular_service_enabled = regular_enabled
                if command.emergency_enabled is not None:
                    row.emergency_service_enabled = zone.emergency_enabled
                if command.priority is not None:
                    row.priority = zone.priority
                row.version += 1

        await self._ensure_coverage_selector(zone)
        zone.version += 1
        await self.repository.sync_legacy_postal_codes(zone.id)
        self._audit(
            actor,
            "service_zone.update",
            "service_area",
            zone.id,
            {
                "version": zone.version,
                "fields": sorted(command.model_fields_set),
                "correlation_id": correlation_id,
            },
        )
        try:
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise DomainError(
                "SERVICE_ZONE_CONFLICT",
                "Service zone conflicts with existing coverage data.",
                409,
            ) from exc
        return await self.get_zone(zone.id)

    async def deactivate_zone(
        self,
        service_area_id: uuid.UUID,
        actor: User,
        *,
        expected_version: int,
        correlation_id: str | None = None,
    ) -> None:
        zone = await self.repository.zone(service_area_id, lock=True)
        if not zone:
            raise DomainError(
                "SERVICE_ZONE_NOT_FOUND",
                "Service zone not found.",
                404,
            )
        self._require_version(zone.version, expected_version, "service zone")
        zone.active = False
        zone.version += 1
        self._audit(
            actor,
            "service_zone.deactivate",
            "service_area",
            zone.id,
            {
                "version": zone.version,
                "correlation_id": correlation_id,
            },
        )
        await self.session.commit()

    async def coverage(
        self,
        service_area_id: uuid.UUID,
    ) -> ServiceZoneCoverage:
        zone = await self.get_zone(service_area_id)
        postal_codes = await self.repository.zone_postal_codes(service_area_id)
        offerings = await self.repository.offerings(service_area_id)
        return ServiceZoneCoverage(
            service_zone=zone,
            postal_codes=[
                PostalCodeRead.model_validate(item) for item in postal_codes
            ],
            service_ids=[item.service_id for item in offerings],
        )

    async def _zone_read(
        self,
        zone: ServiceArea,
        latitude: float | None,
        longitude: float | None,
    ) -> ServiceZoneRead:
        postal_rows = await self.repository.zone_postal_codes(
            zone.id,
            active_only=True,
        )
        offerings = await self.repository.offerings(zone.id)
        regular_enabled = (
            any(item.regular_service_enabled for item in offerings)
            if offerings
            else True
        )
        return ServiceZoneRead(
            id=zone.id,
            legal_entity_id=zone.legal_entity_id,
            name=zone.name,
            country_code=zone.country_code,
            state_code=zone.state_code,
            city=zone.city,
            postal_codes=[item.postal_code for item in postal_rows],
            service_ids=[item.service_id for item in offerings],
            center=(
                Coordinates(latitude=latitude, longitude=longitude)
                if latitude is not None and longitude is not None
                else None
            ),
            radius_miles=(
                round(zone.radius_meters / 1609.344, 3)
                if zone.radius_meters is not None
                else None
            ),
            boundary_configured=zone.boundary is not None,
            priority=zone.priority,
            regular_service_enabled=regular_enabled,
            emergency_enabled=zone.emergency_enabled,
            active=zone.active,
            version=zone.version,
            created_at=zone.created_at,
            updated_at=zone.updated_at,
        )

    async def _validate_services(
        self,
        service_ids: list[uuid.UUID],
    ) -> None:
        services = await self.repository.active_services(service_ids)
        if {service.id for service in services} != set(service_ids):
            raise DomainError(
                "SERVICE_NOT_FOUND",
                "One or more active catalog services were not found.",
                422,
            )

    async def _replace_zone_postal_codes(
        self,
        zone: ServiceArea,
        postal_codes: list[str],
        *,
        regular_service_enabled: bool,
    ) -> None:
        existing = {
            row.postal_code: row
            for row in await self.repository.zone_postal_codes(zone.id)
        }
        requested = set(postal_codes)
        for code, row in existing.items():
            row.active = code in requested
            if row.active:
                row.city = zone.city
                row.state_code = zone.state_code
                row.regular_service_enabled = regular_service_enabled
                row.emergency_service_enabled = zone.emergency_enabled
                row.priority = zone.priority
            row.version += 1
        for code in requested - set(existing):
            self.session.add(
                ServiceZonePostalCode(
                    service_area_id=zone.id,
                    postal_code=code,
                    city=zone.city,
                    state_code=zone.state_code,
                    active=True,
                    regular_service_enabled=regular_service_enabled,
                    emergency_service_enabled=zone.emergency_enabled,
                    priority=zone.priority,
                    version=1,
                )
            )
        await self.session.flush()

    async def _ensure_coverage_selector(self, zone: ServiceArea) -> None:
        postal_codes = await self.repository.zone_postal_codes(zone.id, active_only=True)
        has_radius = zone.center is not None and zone.radius_meters is not None
        if not (
            postal_codes
            or zone.city
            or zone.state_code
            or zone.boundary is not None
            or has_radius
        ):
            raise DomainError(
                "SERVICE_ZONE_COVERAGE_REQUIRED",
                "Service zone requires a geographic coverage selector.",
                422,
            )

    async def _regular_enabled(self, service_area_id: uuid.UUID) -> bool:
        offerings = await self.repository.offerings(service_area_id)
        if offerings:
            return any(item.regular_service_enabled for item in offerings)
        postal_codes = await self.repository.zone_postal_codes(
            service_area_id,
            active_only=True,
        )
        if postal_codes:
            return any(item.regular_service_enabled for item in postal_codes)
        return True

    async def _validated_boundary(
        self,
        boundary_geojson: dict[str, Any] | None,
    ) -> object | None:
        if boundary_geojson is None:
            return None
        if boundary_geojson.get("type") not in {"Polygon", "MultiPolygon"}:
            raise DomainError(
                "SERVICE_ZONE_BOUNDARY_INVALID",
                "Boundary must be Polygon or MultiPolygon GeoJSON.",
                422,
            )
        encoded = json.dumps(boundary_geojson, separators=(",", ":"))
        geometry = func.ST_Multi(
            func.ST_SetSRID(
                func.ST_GeomFromGeoJSON(encoded),
                4326,
            )
        )
        try:
            row = (
                await self.session.execute(
                    select(
                        func.ST_IsValid(geometry),
                        func.ST_IsEmpty(geometry),
                    )
                )
            ).one()
        except DBAPIError as exc:
            await self.session.rollback()
            raise DomainError(
                "SERVICE_ZONE_BOUNDARY_INVALID",
                "Boundary GeoJSON is invalid.",
                422,
            ) from exc
        if not row[0] or row[1]:
            raise DomainError(
                "SERVICE_ZONE_BOUNDARY_INVALID",
                "Boundary GeoJSON is empty or geometrically invalid.",
                422,
            )
        return geometry

    @staticmethod
    def _center(
        latitude: float | None,
        longitude: float | None,
    ) -> object | None:
        if latitude is None or longitude is None:
            return None
        return WKTElement(f"POINT({longitude} {latitude})", srid=4326)

    @staticmethod
    def _radius_meters(radius_miles: float | None) -> int | None:
        if radius_miles is None:
            return None
        return max(1, round(radius_miles * 1609.344))

    @staticmethod
    def _require_version(
        current: int,
        expected: int,
        resource_name: str,
    ) -> None:
        if current != expected:
            raise DomainError(
                "VERSION_CONFLICT",
                f"{resource_name.title()} changed since it was loaded.",
                409,
                fields={"current_version": current},
            )

    def _audit(
        self,
        actor: User,
        action: str,
        resource_type: str,
        resource_id: uuid.UUID,
        metadata: dict[str, Any],
    ) -> None:
        self.session.add(
            AuditLog(
                actor_id=actor.id,
                actor_type="admin",
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                metadata_json=metadata,
                created_at=self.clock.now(),
            )
        )
