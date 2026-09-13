import re
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Header, Query, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import DomainError
from app.db.session import get_db
from app.domains.auth.dependencies import require_permissions
from app.domains.auth.models import User
from app.domains.geography.schemas import (
    PostalCodeCreate,
    PostalCodeImportRead,
    PostalCodeImportRequest,
    PostalCodeList,
    PostalCodeRead,
    PostalCodeUpdate,
    ServiceZoneCoverage,
    ServiceZoneCreate,
    ServiceZoneList,
    ServiceZoneRead,
    ServiceZoneUpdate,
    normalize_postal_code,
    normalize_state_code,
)
from app.domains.geography.service import (
    AdminPostalCodeService,
    AdminServiceZoneService,
)

service_zones_router = APIRouter()
postal_codes_router = APIRouter()
admin_geography = require_permissions("admin.access.manage")
IDEMPOTENCY_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{7,127}$")


def _version(if_match: str | None) -> int:
    if if_match is None:
        raise DomainError(
            "PRECONDITION_REQUIRED",
            "If-Match is required for administrative geography changes.",
            428,
        )
    value = if_match.strip()
    if value.startswith("W/"):
        value = value[2:].strip()
    value = value.strip('"')
    if not value.isdigit() or int(value) < 1:
        raise DomainError(
            "INVALID_IF_MATCH",
            "If-Match must contain the current resource version.",
            400,
        )
    return int(value)


def _etag(response: Response, version: int) -> None:
    response.headers["ETag"] = f'"{version}"'


def _correlation_id(request: Request) -> str | None:
    return getattr(request.state, "correlation_id", None)


def _postal_filter(value: str | None) -> str | None:
    if value is None:
        return None
    try:
        return normalize_postal_code(value)
    except ValueError as exc:
        raise DomainError(
            "POSTAL_CODE_INVALID",
            "Postal code must use ZIP or ZIP+4 format.",
            422,
        ) from exc


def _state_filter(value: str | None) -> str | None:
    try:
        return normalize_state_code(value)
    except ValueError as exc:
        raise DomainError(
            "STATE_CODE_INVALID",
            "State code must contain two or three letters.",
            422,
        ) from exc


def _idempotency_key(value: str | None) -> str:
    if value is None or not IDEMPOTENCY_RE.fullmatch(value.strip()):
        raise DomainError(
            "IDEMPOTENCY_KEY_INVALID",
            "Idempotency-Key must be 8-128 safe characters.",
            400,
        )
    return value.strip()


@service_zones_router.get("", response_model=ServiceZoneList)
async def list_service_zones(
    _: Annotated[User, Depends(admin_geography)],
    session: Annotated[AsyncSession, Depends(get_db)],
    active: bool | None = Query(default=None),
    country_code: str | None = Query(default=None, min_length=2, max_length=2),
    state_code: str | None = Query(default=None, min_length=2, max_length=3),
    city: str | None = Query(default=None, min_length=1, max_length=120),
    postal_code: str | None = Query(default=None, min_length=5, max_length=10),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
) -> ServiceZoneList:
    return await AdminServiceZoneService(session).list_zones(
        active=active,
        country_code=country_code.upper() if country_code else None,
        state_code=_state_filter(state_code),
        city=city,
        postal_code=_postal_filter(postal_code),
        page=page,
        page_size=page_size,
    )


@service_zones_router.post(
    "",
    response_model=ServiceZoneRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_service_zone(
    command: ServiceZoneCreate,
    request: Request,
    response: Response,
    actor: Annotated[User, Depends(admin_geography)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> ServiceZoneRead:
    result = await AdminServiceZoneService(session).create_zone(
        actor,
        command,
        correlation_id=_correlation_id(request),
    )
    _etag(response, result.version)
    return result


@service_zones_router.get(
    "/{service_area_id}",
    response_model=ServiceZoneRead,
)
async def get_service_zone(
    service_area_id: uuid.UUID,
    response: Response,
    _: Annotated[User, Depends(admin_geography)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> ServiceZoneRead:
    result = await AdminServiceZoneService(session).get_zone(service_area_id)
    _etag(response, result.version)
    return result


@service_zones_router.patch(
    "/{service_area_id}",
    response_model=ServiceZoneRead,
)
async def update_service_zone(
    service_area_id: uuid.UUID,
    command: ServiceZoneUpdate,
    request: Request,
    response: Response,
    actor: Annotated[User, Depends(admin_geography)],
    session: Annotated[AsyncSession, Depends(get_db)],
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
) -> ServiceZoneRead:
    result = await AdminServiceZoneService(session).update_zone(
        service_area_id,
        actor,
        command,
        expected_version=_version(if_match),
        correlation_id=_correlation_id(request),
    )
    _etag(response, result.version)
    return result


@service_zones_router.delete(
    "/{service_area_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def deactivate_service_zone(
    service_area_id: uuid.UUID,
    request: Request,
    actor: Annotated[User, Depends(admin_geography)],
    session: Annotated[AsyncSession, Depends(get_db)],
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
) -> None:
    await AdminServiceZoneService(session).deactivate_zone(
        service_area_id,
        actor,
        expected_version=_version(if_match),
        correlation_id=_correlation_id(request),
    )


@service_zones_router.get(
    "/{service_area_id}/coverage",
    response_model=ServiceZoneCoverage,
)
async def get_service_zone_coverage(
    service_area_id: uuid.UUID,
    _: Annotated[User, Depends(admin_geography)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> ServiceZoneCoverage:
    return await AdminServiceZoneService(session).coverage(service_area_id)


@postal_codes_router.get("", response_model=PostalCodeList)
async def list_postal_codes(
    _: Annotated[User, Depends(admin_geography)],
    session: Annotated[AsyncSession, Depends(get_db)],
    service_area_id: uuid.UUID | None = Query(default=None),
    postal_code: str | None = Query(default=None, min_length=5, max_length=10),
    state_code: str | None = Query(default=None, min_length=2, max_length=3),
    active: bool | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
) -> PostalCodeList:
    return await AdminPostalCodeService(session).list_postal_codes(
        service_area_id=service_area_id,
        postal_code=_postal_filter(postal_code),
        state_code=_state_filter(state_code),
        active=active,
        page=page,
        page_size=page_size,
    )


@postal_codes_router.post(
    "",
    response_model=PostalCodeRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_postal_code(
    command: PostalCodeCreate,
    request: Request,
    response: Response,
    actor: Annotated[User, Depends(admin_geography)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> PostalCodeRead:
    result = await AdminPostalCodeService(session).create_postal_code(
        actor,
        command,
        correlation_id=_correlation_id(request),
    )
    _etag(response, result.version)
    return result


@postal_codes_router.post(
    "/import",
    response_model=PostalCodeImportRead,
    status_code=status.HTTP_201_CREATED,
)
async def import_postal_codes(
    command: PostalCodeImportRequest,
    request: Request,
    actor: Annotated[User, Depends(admin_geography)],
    session: Annotated[AsyncSession, Depends(get_db)],
    idempotency_key: Annotated[
        str | None,
        Header(alias="Idempotency-Key"),
    ] = None,
) -> PostalCodeImportRead:
    return await AdminPostalCodeService(session).import_postal_codes(
        actor,
        command,
        idempotency_key=_idempotency_key(idempotency_key),
        correlation_id=_correlation_id(request),
    )


@postal_codes_router.get(
    "/imports/{import_id}",
    response_model=PostalCodeImportRead,
)
async def get_postal_code_import(
    import_id: uuid.UUID,
    _: Annotated[User, Depends(admin_geography)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> PostalCodeImportRead:
    return await AdminPostalCodeService(session).get_postal_import(import_id)


@postal_codes_router.patch(
    "/{postal_code_id}",
    response_model=PostalCodeRead,
)
async def update_postal_code(
    postal_code_id: uuid.UUID,
    command: PostalCodeUpdate,
    request: Request,
    response: Response,
    actor: Annotated[User, Depends(admin_geography)],
    session: Annotated[AsyncSession, Depends(get_db)],
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
) -> PostalCodeRead:
    result = await AdminPostalCodeService(session).update_postal_code(
        postal_code_id,
        actor,
        command,
        expected_version=_version(if_match),
        correlation_id=_correlation_id(request),
    )
    _etag(response, result.version)
    return result


@postal_codes_router.delete(
    "/{postal_code_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def deactivate_postal_code(
    postal_code_id: uuid.UUID,
    request: Request,
    actor: Annotated[User, Depends(admin_geography)],
    session: Annotated[AsyncSession, Depends(get_db)],
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
) -> None:
    await AdminPostalCodeService(session).deactivate_postal_code(
        postal_code_id,
        actor,
        expected_version=_version(if_match),
        correlation_id=_correlation_id(request),
    )
