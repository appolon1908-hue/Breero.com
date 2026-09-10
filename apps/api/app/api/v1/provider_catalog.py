import re
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Header, Query, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import DomainError
from app.db.session import get_db
from app.domains.auth.dependencies import require_permissions
from app.domains.auth.models import User
from app.domains.provider_catalog.schemas import (
    ProviderServiceCreate,
    ProviderServiceList,
    ProviderServiceRead,
    ProviderServiceUpdate,
    ProviderSkillCreate,
    ProviderSkillList,
    ProviderSkillRead,
)
from app.domains.provider_catalog.service import ProviderCatalogService

router = APIRouter()
service_read = require_permissions("provider.services.read")
service_manage = require_permissions("provider.services.manage")
skill_read = require_permissions("provider.skills.read")
skill_manage = require_permissions("provider.skills.manage")
ETAG_RE = re.compile(r"^[1-9][0-9]*$")


def _version(value: str | None) -> int:
    if value is None:
        raise DomainError(
            "PRECONDITION_REQUIRED",
            "If-Match is required for provider catalog changes.",
            428,
        )
    token = value.strip()
    if token.startswith("W/"):
        token = token[2:].strip()
    token = token.strip('"')
    if not ETAG_RE.fullmatch(token):
        raise DomainError(
            "INVALID_IF_MATCH",
            "If-Match must contain the current resource version.",
            400,
        )
    return int(token)


def _etag(response: Response, version: int) -> None:
    response.headers["ETag"] = f'"{version}"'


def _correlation_id(request: Request) -> str | None:
    return getattr(request.state, "correlation_id", None)


@router.get("/services", response_model=ProviderServiceList)
async def list_provider_services(
    user: Annotated[User, Depends(service_read)],
    session: Annotated[AsyncSession, Depends(get_db)],
    include_inactive: bool = Query(default=False),
) -> ProviderServiceList:
    return await ProviderCatalogService(session).list_services(
        user,
        include_inactive=include_inactive,
    )


@router.post(
    "/services",
    response_model=ProviderServiceRead,
    status_code=status.HTTP_201_CREATED,
)
async def add_provider_service(
    command: ProviderServiceCreate,
    request: Request,
    response: Response,
    user: Annotated[User, Depends(service_manage)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> ProviderServiceRead:
    result = await ProviderCatalogService(session).add_service(
        user,
        command,
        correlation_id=_correlation_id(request),
    )
    _etag(response, result.version)
    return result


@router.patch(
    "/services/{provider_service_id}",
    response_model=ProviderServiceRead,
)
async def update_provider_service(
    provider_service_id: uuid.UUID,
    command: ProviderServiceUpdate,
    request: Request,
    response: Response,
    user: Annotated[User, Depends(service_manage)],
    session: Annotated[AsyncSession, Depends(get_db)],
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
) -> ProviderServiceRead:
    result = await ProviderCatalogService(session).update_service(
        provider_service_id,
        user,
        command,
        expected_version=_version(if_match),
        correlation_id=_correlation_id(request),
    )
    _etag(response, result.version)
    return result


@router.delete(
    "/services/{provider_service_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_provider_service(
    provider_service_id: uuid.UUID,
    request: Request,
    user: Annotated[User, Depends(service_manage)],
    session: Annotated[AsyncSession, Depends(get_db)],
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
) -> None:
    await ProviderCatalogService(session).remove_service(
        provider_service_id,
        user,
        expected_version=_version(if_match),
        correlation_id=_correlation_id(request),
    )


@router.get("/skills", response_model=ProviderSkillList)
async def list_provider_skills(
    user: Annotated[User, Depends(skill_read)],
    session: Annotated[AsyncSession, Depends(get_db)],
    worker_id: uuid.UUID | None = Query(default=None),
    include_inactive: bool = Query(default=False),
) -> ProviderSkillList:
    return await ProviderCatalogService(session).list_skills(
        user,
        worker_id=worker_id,
        include_inactive=include_inactive,
    )


@router.post(
    "/skills",
    response_model=ProviderSkillRead,
    status_code=status.HTTP_201_CREATED,
)
async def add_provider_skill(
    command: ProviderSkillCreate,
    request: Request,
    response: Response,
    user: Annotated[User, Depends(skill_manage)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> ProviderSkillRead:
    result = await ProviderCatalogService(session).add_skill(
        user,
        command,
        correlation_id=_correlation_id(request),
    )
    _etag(response, result.version)
    return result


@router.delete(
    "/skills/{provider_skill_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_provider_skill(
    provider_skill_id: uuid.UUID,
    request: Request,
    user: Annotated[User, Depends(skill_manage)],
    session: Annotated[AsyncSession, Depends(get_db)],
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
) -> None:
    await ProviderCatalogService(session).remove_skill(
        provider_skill_id,
        user,
        expected_version=_version(if_match),
        correlation_id=_correlation_id(request),
    )
