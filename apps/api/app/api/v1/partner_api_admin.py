"""Operator management of third-party API clients, keys and webhooks.

Separate from the public surface: nothing here is reachable with an API key. Managing
integrator credentials is an administrative act and requires an authenticated operator.
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.domains.auth.dependencies import require_permissions
from app.domains.auth.models import User
from app.domains.partner_api.models import ApiClientStatus
from app.domains.partner_api.schemas import (
    ApiClientCreate,
    ApiClientRead,
    ApiKeyCreate,
    ApiKeyIssued,
    ApiKeyRead,
)
from app.domains.partner_api.service import PartnerApiService, require_partner_api_enabled

router = APIRouter()


@router.get("/clients", response_model=list[ApiClientRead])
async def list_clients(
    session: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("admin.access.manage"))],
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
) -> list[ApiClientRead]:
    require_partner_api_enabled()
    clients = await PartnerApiService(session).repo.list_clients(limit, offset)
    return [ApiClientRead.model_validate(client) for client in clients]


@router.post("/clients", response_model=ApiClientRead, status_code=201)
async def create_client(
    data: ApiClientCreate,
    session: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_permissions("admin.access.manage"))],
) -> ApiClientRead:
    require_partner_api_enabled()
    return ApiClientRead.model_validate(
        await PartnerApiService(session).create_client(data, user.id)
    )


@router.post("/clients/{client_id}/suspend", response_model=ApiClientRead)
async def suspend_client(
    client_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_permissions("admin.access.manage"))],
) -> ApiClientRead:
    require_partner_api_enabled()
    return ApiClientRead.model_validate(
        await PartnerApiService(session).set_client_status(
            client_id, ApiClientStatus.SUSPENDED, user.id
        )
    )


@router.get("/clients/{client_id}/keys", response_model=list[ApiKeyRead])
async def list_keys(
    client_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("admin.access.manage"))],
) -> list[ApiKeyRead]:
    require_partner_api_enabled()
    keys = await PartnerApiService(session).repo.list_keys(client_id)
    # ApiKeyRead has no secret field, so a listing cannot leak one.
    return [ApiKeyRead.model_validate(key) for key in keys]


@router.post("/clients/{client_id}/keys", response_model=ApiKeyIssued, status_code=201)
async def issue_key(
    client_id: uuid.UUID,
    data: ApiKeyCreate,
    session: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_permissions("admin.access.manage"))],
) -> ApiKeyIssued:
    """Mint a key. This is the only response that ever contains the secret."""
    require_partner_api_enabled()
    return await PartnerApiService(session).issue_key(client_id, data, user.id)


@router.post("/keys/{key_id}/revoke", response_model=ApiKeyRead)
async def revoke_key(
    key_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_permissions("admin.access.manage"))],
) -> ApiKeyRead:
    require_partner_api_enabled()
    return ApiKeyRead.model_validate(await PartnerApiService(session).revoke_key(key_id, user.id))
