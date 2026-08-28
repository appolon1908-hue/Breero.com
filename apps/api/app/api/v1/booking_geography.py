from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rate_limit import rate_limit
from app.db.session import get_db
from app.domains.geography.providers import GeographyProvider
from app.domains.geography.schemas import (
    AddressValidationRequest,
    AddressValidationResult,
    ServiceAreaCheckRequest,
    ServiceAreaCheckResult,
    TimezoneResolveRequest,
    TimezoneResolveResult,
)
from app.domains.geography.service import GeographyService
from app.integrations.geocoding import GeocodingAdapter

router = APIRouter()


def get_geography_provider() -> GeographyProvider:
    """FastAPI override point for REAL, FAKE, TEST, and disabled adapters."""

    return GeocodingAdapter()


@router.post(
    "/address/validate",
    response_model=AddressValidationResult,
)
async def validate_booking_address(
    command: AddressValidationRequest,
    request: Request,
    session: Annotated[AsyncSession, Depends(get_db)],
    provider: Annotated[GeographyProvider, Depends(get_geography_provider)],
    _: Annotated[None, Depends(rate_limit("booking-address", 30, 60))],
) -> AddressValidationResult:
    return await GeographyService(
        session,
        provider=provider,
    ).validate_address(
        command,
        correlation_id=getattr(request.state, "correlation_id", None),
    )


@router.post(
    "/service-area/check",
    response_model=ServiceAreaCheckResult,
)
async def check_booking_service_area(
    command: ServiceAreaCheckRequest,
    session: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[None, Depends(rate_limit("booking-service-area", 60, 60))],
) -> ServiceAreaCheckResult:
    return await GeographyService(session).check_service_area(command)


@router.post(
    "/timezone/resolve",
    response_model=TimezoneResolveResult,
)
async def resolve_booking_timezone(
    command: TimezoneResolveRequest,
    session: Annotated[AsyncSession, Depends(get_db)],
    provider: Annotated[GeographyProvider, Depends(get_geography_provider)],
    _: Annotated[None, Depends(rate_limit("booking-timezone", 60, 60))],
) -> TimezoneResolveResult:
    return await GeographyService(
        session,
        provider=provider,
    ).resolve_timezone(
        command.latitude,
        command.longitude,
    )
