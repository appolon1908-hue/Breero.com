from typing import Annotated

import redis.asyncio as redis
from fastapi import APIRouter, Depends, Header, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import DomainError
from app.core.redis_client import get_redis_client
from app.db.session import get_db
from app.domains.public_submissions.models import SubmissionType
from app.domains.public_submissions.schemas import (
    ContactCreate,
    ProviderInterestCreate,
    ServiceRequestCreate,
    SubmissionAccepted,
)
from app.domains.public_submissions.service import PublicSubmissionService

router = APIRouter()


async def enforce_rate_limit(request: Request) -> str:
    """Public-form submission limit.

    Uses the process-wide pooled client rather than opening its own connection per
    submission, and applies the same fail-closed semantics as `app.core.rate_limit`:
    an unreachable limiter must not silently become an open door.
    """
    source = request.client.host if request.client else "unknown"
    client = get_redis_client(request.app)
    key = f"public-form:{source}"
    try:
        async with client.pipeline(transaction=True) as pipeline:
            pipeline.incr(key)
            pipeline.expire(key, 60, nx=True)
            count, _ = await pipeline.execute()
    except redis.RedisError as exc:
        raise DomainError("RATE_LIMITER_UNAVAILABLE", "Submissions are temporarily unavailable", 503) from exc
    if int(count) > 10:
        raise DomainError("RATE_LIMITED", "Too many submissions; try again shortly", 429)
    return source


async def accept(data, submission_type, key, source, session):
    if not key or len(key) > 255:
        raise DomainError("IDEMPOTENCY_KEY_REQUIRED", "A valid Idempotency-Key is required", 400)
    return await PublicSubmissionService(session).accept(submission_type, data, key, source)


@router.post("/service-requests", response_model=SubmissionAccepted, status_code=status.HTTP_202_ACCEPTED)
async def service_request(data: ServiceRequestCreate, session: Annotated[AsyncSession, Depends(get_db)], source: Annotated[str, Depends(enforce_rate_limit)], idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None):
    return await accept(data, SubmissionType.SERVICE_REQUEST, idempotency_key, source, session)


@router.post("/contact", response_model=SubmissionAccepted, status_code=status.HTTP_202_ACCEPTED)
async def contact(data: ContactCreate, session: Annotated[AsyncSession, Depends(get_db)], source: Annotated[str, Depends(enforce_rate_limit)], idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None):
    return await accept(data, SubmissionType.CONTACT, idempotency_key, source, session)


@router.post("/provider-interest", response_model=SubmissionAccepted, status_code=status.HTTP_202_ACCEPTED)
async def provider_interest(data: ProviderInterestCreate, session: Annotated[AsyncSession, Depends(get_db)], source: Annotated[str, Depends(enforce_rate_limit)], idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None):
    return await accept(data, SubmissionType.PROVIDER_INTEREST, idempotency_key, source, session)
