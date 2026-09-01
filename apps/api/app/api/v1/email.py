import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.domains.auth.access_service import BRAND_KEY
from app.domains.auth.dependencies import require_any_permission
from app.domains.auth.models import User
from app.domains.tenant_email.schemas import (
    EmailComposeRequest,
    EmailCredentialCreate,
    EmailCredentialRead,
    EmailDomainCreate,
    EmailDomainRead,
    EmailMessageRead,
    EmailOutboxRead,
    EmailSenderCreate,
    EmailSenderRead,
)
from app.domains.tenant_email.service import TenantEmailService

router = APIRouter()


@router.get("/domains", response_model=list[EmailDomainRead])
async def list_domains(
    session: AsyncSession = Depends(get_db),
    user: User = Depends(require_any_permission("email.domain.read", "email.domain.manage")),
) -> list[EmailDomainRead]:
    return [EmailDomainRead.model_validate(item) for item in await TenantEmailService(session).list_domains(user)]


@router.post("/domains", response_model=EmailDomainRead, status_code=201)
async def create_domain(
    data: EmailDomainCreate,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(require_any_permission("email.domain.manage")),
) -> EmailDomainRead:
    return EmailDomainRead.model_validate(await TenantEmailService(session).create_domain(data, user))


@router.post("/domains/{domain_id}/verification", response_model=EmailDomainRead)
async def set_domain_verification(
    domain_id: uuid.UUID,
    verified: bool = Query(...),
    session: AsyncSession = Depends(get_db),
    user: User = Depends(require_any_permission("email.domain.verify")),
) -> EmailDomainRead:
    return EmailDomainRead.model_validate(
        await TenantEmailService(session).set_domain_verification(domain_id, verified, user)
    )


@router.get("/senders", response_model=list[EmailSenderRead])
async def list_senders(
    session: AsyncSession = Depends(get_db),
    user: User = Depends(require_any_permission("email.sender.read", "email.sender.manage")),
) -> list[EmailSenderRead]:
    return [EmailSenderRead.model_validate(item) for item in await TenantEmailService(session).list_senders(user)]


@router.post("/senders", response_model=EmailSenderRead, status_code=201)
async def create_sender(
    data: EmailSenderCreate,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(require_any_permission("email.sender.manage")),
) -> EmailSenderRead:
    return EmailSenderRead.model_validate(await TenantEmailService(session).create_sender(data, user))


@router.get("/credentials", response_model=list[EmailCredentialRead])
async def list_credentials(
    session: AsyncSession = Depends(get_db),
    user: User = Depends(require_any_permission("email.credential.read", "email.credential.manage")),
) -> list[EmailCredentialRead]:
    return await TenantEmailService(session).list_credentials(user)


@router.post("/credentials", response_model=EmailCredentialRead, status_code=201)
async def create_credential(
    data: EmailCredentialCreate,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(require_any_permission("email.credential.manage")),
) -> EmailCredentialRead:
    return await TenantEmailService(session).create_credential(data, user)


@router.post("/messages", response_model=EmailMessageRead, status_code=202)
async def compose_message(
    data: EmailComposeRequest,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(require_any_permission("email.message.compose")),
) -> EmailMessageRead:
    return await TenantEmailService(session).compose(data, user)


@router.get("/messages/{message_id}", response_model=EmailMessageRead)
async def get_message(
    message_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(require_any_permission("email.message.read", "email.message.compose")),
) -> EmailMessageRead:
    return EmailMessageRead.model_validate(await TenantEmailService(session).get_message(message_id, user))


@router.get("/outbox", response_model=list[EmailOutboxRead])
async def list_outbox(
    session: AsyncSession = Depends(get_db),
    user: User = Depends(require_any_permission("email.outbox.read")),
) -> list[EmailOutboxRead]:
    return await TenantEmailService(session).list_outbox(user, BRAND_KEY)


@router.post("/outbox/{event_id}/retry", response_model=EmailOutboxRead)
async def retry_outbox(
    event_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(require_any_permission("email.outbox.retry")),
) -> EmailOutboxRead:
    return await TenantEmailService(session).retry_outbox(event_id, user)
