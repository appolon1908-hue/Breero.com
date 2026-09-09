"""The third-party surface.

Authenticated by API key, never by session. Every route is scope-gated and the write
side is deliberately narrow: an integrator can submit a service request, which enters
manual dispatch and promises no appointment, and can read back what it submitted.

Nothing here exposes provider candidates, capacity, worker identities or pricing
internals. A partner sees the catalog, whether an address is covered, and the state of
its own requests.
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.domains.catalog.repository import CatalogRepository
from app.domains.partner_api.dependencies import PartnerPrincipal, require_api_scope
from app.domains.partner_api.models import ApiScope
from app.domains.partner_api.schemas import (
    WebhookSubscriptionCreate,
    WebhookSubscriptionIssued,
    WebhookSubscriptionRead,
)
from app.domains.partner_api.service import PartnerApiService
from app.domains.public_submissions.models import SubmissionType
from app.domains.public_submissions.schemas import ServiceRequestCreate
from app.domains.public_submissions.service import PublicSubmissionService

router = APIRouter()


@router.get("/catalog")
async def partner_catalog(
    session: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[PartnerPrincipal, Depends(require_api_scope(ApiScope.CATALOG_READ))],
) -> list[dict]:
    """Bookable services, as a partner may present them."""
    services = await CatalogRepository(session).list_active()
    return [
        {
            "id": str(service.id),
            "slug": service.slug,
            "name": service.name,
            "description": service.description,
        }
        for service in services
    ]


@router.post("/service-requests", status_code=202)
async def submit_service_request(
    data: ServiceRequestCreate,
    session: Annotated[AsyncSession, Depends(get_db)],
    principal: Annotated[
        PartnerPrincipal, Depends(require_api_scope(ApiScope.SERVICE_REQUEST_WRITE))
    ],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> dict:
    """Submit a request for manual dispatch.

    202, never 201: this is an intake, not a booking. It promises no appointment, and
    the response says so rather than letting an integrator infer one.

    The idempotency key is required and namespaced per client, so two integrators
    cannot collide on the same key and one cannot replay another's submission.
    """
    if not idempotency_key or len(idempotency_key) > 200:
        raise HTTPException(400, "A valid Idempotency-Key header is required")

    partner = PartnerApiService(session)
    accepted = await PublicSubmissionService(session).accept(
        SubmissionType.SERVICE_REQUEST,
        data,
        partner.submission_key(principal.client.id, idempotency_key),
        f"partner-api:{principal.key.prefix}",
    )
    await partner.enqueue_event(
        "service_request.received",
        accepted.request_id,
        {
            "request_id": str(accepted.request_id),
            "downstream_status": accepted.downstream_status,
        },
    )
    await session.commit()
    return {
        "request_id": str(accepted.request_id),
        "downstream_status": accepted.downstream_status,
        "message": "Received for manual dispatch. This does not confirm an appointment.",
    }


@router.get("/service-requests/{request_id}")
async def read_service_request(
    request_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_db)],
    principal: Annotated[
        PartnerPrincipal, Depends(require_api_scope(ApiScope.SERVICE_REQUEST_READ))
    ],
) -> dict:
    """Read back a request this client submitted.

    Ownership is enforced by the submission source, so a client cannot read another
    integrator's request by guessing an identifier.
    """
    submission = await PartnerApiService(session).owned_submission(
        request_id, principal.client.id
    )
    if submission is None:
        # 404 rather than 403: an integrator must not be able to confirm that an
        # identifier exists under someone else's account.
        raise HTTPException(404, "Service request not found")
    return {
        "request_id": str(submission.id),
        "submission_type": submission.submission_type.value,
        "downstream_status": submission.downstream_status.value,
        "created_at": submission.created_at.isoformat(),
    }


@router.get("/webhooks", response_model=list[WebhookSubscriptionRead])
async def list_webhooks(
    session: Annotated[AsyncSession, Depends(get_db)],
    principal: Annotated[PartnerPrincipal, Depends(require_api_scope(ApiScope.WEBHOOK_MANAGE))],
) -> list[WebhookSubscriptionRead]:
    subscriptions = await PartnerApiService(session).repo.list_subscriptions(principal.client.id)
    # The read model has no secret field, so a listing cannot leak a signing key.
    return [WebhookSubscriptionRead.model_validate(item) for item in subscriptions]


@router.post("/webhooks", response_model=WebhookSubscriptionIssued, status_code=201)
async def create_webhook(
    data: WebhookSubscriptionCreate,
    session: Annotated[AsyncSession, Depends(get_db)],
    principal: Annotated[PartnerPrincipal, Depends(require_api_scope(ApiScope.WEBHOOK_MANAGE))],
) -> WebhookSubscriptionIssued:
    """Register a delivery endpoint. The signing secret is returned once, here."""
    return await PartnerApiService(session).create_subscription(principal.client.id, data)
