import uuid
from decimal import Decimal
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from geoalchemy2.elements import WKTElement
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import DomainError
from app.domains.booking.models import Address, ServiceArea
from app.domains.common.clock import Clock, SystemClock
from app.domains.common.outbox import AuditLog
from app.integrations.geocoding import GeocodingAdapter

from .providers import GeographyProvider
from .repository import GeographyRepository
from .schemas import (
    AddressValidationRequest,
    AddressValidationResult,
    Coordinates,
    ServiceAreaCheckRequest,
    ServiceAreaCheckResult,
    ServiceZoneSummary,
    TimezoneResolveResult,
    ValidatedAddressRead,
    base_postal_code,
)


class GeographyService:
    """Public address, coverage, and service-address timezone workflow."""

    def __init__(
        self,
        session: AsyncSession,
        *,
        provider: GeographyProvider | None = None,
        clock: Clock | None = None,
    ) -> None:
        self.session = session
        self.provider = provider or GeocodingAdapter()
        self.clock = clock or SystemClock()
        self.repository = GeographyRepository(session)

    async def validate_address(
        self,
        command: AddressValidationRequest,
        *,
        correlation_id: str | None = None,
    ) -> AddressValidationResult:
        resolved = await self.provider.geocode(self._address_text(command))
        if (
            resolved.country_code != "US"
            or not resolved.line1
            or not resolved.city
            or not resolved.state_code
            or not resolved.postal_code
            or not resolved.timezone_name
        ):
            raise DomainError(
                "ADDRESS_VALIDATION_INCOMPLETE",
                "Address provider did not return complete U.S. address evidence.",
                422,
            )
        self._validate_input_match(
            command,
            city=resolved.city,
            state_code=resolved.state_code,
            postal_code=resolved.postal_code,
        )
        timezone = self._iana_timezone(resolved.timezone_name)
        zone_match = await self.repository.match_zone(
            latitude=resolved.latitude,
            longitude=resolved.longitude,
            postal_code=resolved.postal_code,
            country_code=resolved.country_code,
            state_code=resolved.state_code,
            city=resolved.city,
            service_id=None,
        )
        zone = zone_match[0] if zone_match else None
        confidence = (
            Decimal(str(resolved.confidence)).quantize(Decimal("0.0001"))
            if resolved.confidence is not None
            else None
        )
        address = Address(
            formatted_address=resolved.formatted_address,
            line1=resolved.line1,
            line2=resolved.line2 or command.address_line_2,
            city=resolved.city,
            county=resolved.county,
            state_code=resolved.state_code,
            postal_code=resolved.postal_code,
            postal_code_plus4=resolved.postal_code_plus4,
            country_code=resolved.country_code,
            location=WKTElement(
                f"POINT({resolved.longitude} {resolved.latitude})",
                srid=4326,
            ),
            service_area_id=zone.id if zone else None,
            geocoding_provider=resolved.provider,
            provider_reference=resolved.provider_reference,
            validation_status="VALID",
            validation_confidence=confidence,
            timezone_name=timezone,
        )
        await self.repository.add_address(address)
        self._audit(
            action="address.validate",
            resource_id=address.id,
            correlation_id=correlation_id,
            metadata={
                "country_code": address.country_code,
                "state_code": address.state_code,
                "postal_code": address.postal_code,
                "service_area_id": str(zone.id) if zone else None,
                "provider": address.geocoding_provider,
            },
        )
        await self.session.commit()
        await self.session.refresh(address)
        return AddressValidationResult(
            address_id=address.id,
            address=ValidatedAddressRead(
                address_line_1=address.line1,
                address_line_2=address.line2,
                city=address.city,
                county=address.county,
                state=address.state_code or "",
                postal_code=address.postal_code,
                postal_code_plus4=address.postal_code_plus4,
                country=address.country_code,
            ),
            coordinates=Coordinates(
                latitude=resolved.latitude,
                longitude=resolved.longitude,
            ),
            timezone=timezone,
            validation_status="VALID",
            validation_source=address.geocoding_provider,
            covered=zone is not None,
            service_zone=self._zone_summary(zone),
        )

    async def check_service_area(
        self,
        command: ServiceAreaCheckRequest,
    ) -> ServiceAreaCheckResult:
        if not await self.repository.active_service(command.service_id):
            raise DomainError("SERVICE_NOT_FOUND", "Service not found.", 404)
        zone_match = await self.repository.match_zone(
            latitude=command.latitude,
            longitude=command.longitude,
            postal_code=command.postal_code,
            country_code=command.country,
            state_code=command.state,
            city=command.city,
            service_id=command.service_id,
        )
        zone = zone_match[0] if zone_match else None
        return ServiceAreaCheckResult(
            covered=zone is not None,
            service_zone=self._zone_summary(zone),
        )

    async def resolve_timezone(
        self,
        latitude: float,
        longitude: float,
    ) -> TimezoneResolveResult:
        timezone = await self.provider.resolve_timezone(latitude, longitude)
        return TimezoneResolveResult(timezone=self._iana_timezone(timezone))

    @staticmethod
    def _address_text(command: AddressValidationRequest) -> str:
        pieces = [
            command.address_line_1,
            command.address_line_2,
            command.city,
            command.state,
            command.postal_code,
            command.country,
        ]
        return ", ".join(piece.strip() for piece in pieces if piece and piece.strip())

    @staticmethod
    def _validate_input_match(
        command: AddressValidationRequest,
        *,
        city: str,
        state_code: str,
        postal_code: str,
    ) -> None:
        mismatches: list[str] = []
        if city.strip().casefold() != command.city.strip().casefold():
            mismatches.append("city")
        if state_code.strip().upper() != command.state:
            mismatches.append("state")
        if base_postal_code(postal_code) != base_postal_code(command.postal_code):
            mismatches.append("postal_code")
        if mismatches:
            raise DomainError(
                "ADDRESS_INPUT_MISMATCH",
                "Validated address does not match the supplied locality.",
                422,
                fields={"mismatched_fields": mismatches},
            )

    @staticmethod
    def _iana_timezone(value: str) -> str:
        timezone = value.strip()
        try:
            ZoneInfo(timezone)
        except ZoneInfoNotFoundError as exc:
            raise DomainError(
                "TIMEZONE_INVALID",
                "Service-address timezone is invalid.",
                422,
            ) from exc
        return timezone

    @staticmethod
    def _zone_summary(zone: ServiceArea | None) -> ServiceZoneSummary | None:
        if not zone:
            return None
        return ServiceZoneSummary(
            id=zone.id,
            name=zone.name,
            emergency_enabled=zone.emergency_enabled,
        )

    def _audit(
        self,
        *,
        action: str,
        resource_id: uuid.UUID,
        correlation_id: str | None,
        metadata: dict[str, Any],
    ) -> None:
        self.session.add(
            AuditLog(
                actor_id=None,
                actor_type="anonymous_session",
                action=action,
                resource_type="address",
                resource_id=resource_id,
                metadata_json={
                    **metadata,
                    "correlation_id": correlation_id,
                },
                created_at=self.clock.now(),
            )
        )
