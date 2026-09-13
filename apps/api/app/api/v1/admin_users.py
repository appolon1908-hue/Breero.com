from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.domains.auth.dependencies import require_permissions
from app.domains.auth.models import User
from app.domains.auth.provisioning_service import (
    InternalUserProvisioningService,
)
from app.domains.auth.schemas import (
    InternalUserProvisionRequest,
    InternalUserProvisionResponse,
)

router = APIRouter()
can_provision_internal_user = require_permissions("admin.access.manage")


@router.post(
    "",
    response_model=InternalUserProvisionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def provision_internal_user(
    data: InternalUserProvisionRequest,
    actor: Annotated[User, Depends(can_provision_internal_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> InternalUserProvisionResponse:
    return await InternalUserProvisioningService(session).provision(
        actor=actor,
        data=data,
    )
