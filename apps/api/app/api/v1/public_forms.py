from typing import Annotated

import redis.asyncio as redis
from fastapi import APIRouter, Depends, Header, Request, status
from redis.exceptions import RedisError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.errors import DomainError
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
RATE_LIMIT_MAX_REQUESTS = 10
RATE_LIMIT_WINDOW_SECONDS = 60
RATE_LIMIT_SCRIPT = """
local count = redis.call('INCR', KEYS[1])
if count == 1 then
  redis.call('EXPIRE', KEYS[1], ARGV[1])
end
local ttl = redis.call('TTL', KEYS[1])
return {count, ttl}
"""


async def enforce_rate_limit(request: Request) -> str:
    source = request.client.host if request.client else "unknown"
    client = redis.from_url(
        settings.redis_url,
        socket_connect_timeout=1,
        socket_timeout=1,
    )
    try:
        key = f"public-form:{source}"
        result = await client.eval(
            RATE_LIMIT_SCRIPT,
            1,
            key,
            RATE_LIMIT_WINDOW_SECONDS,
        )
    except RedisError as exc:
        raise DomainError(
            "RATE_LIMIT_UNAVAILABLE",
            "Public request intake is temporarily unavailable",
            503,
        ) from exc
    finally:
        await client.aclose()

    count, ttl = int(result[0]), max(int(result[1]), 1)
    if count > RATE_LIMIT_MAX_REQUESTS:
        raise DomainError(
            "RATE_LIMITED",
            "Too many submissions; try again shortly",
            status.HTTP_429_TOO_MANY_REQUESTS,
            headers={"Retry-After": str(ttl)},
        )
    return source


def validate_channel_contract(data) -> None:
    if (data.transactional_sms_consent or data.marketing_sms_consent) and not getattr(data, "phone", None):
        raise DomainError("PHONE_REQUIRED_FOR_SMS_CONSENT", "A phone number is required for SMS consent", 422)
    if getattr(data, "contact_preference", None) == "text" and not data.transactional_sms_consent:
        raise DomainError("SMS_CONSENT_REQUIRED", "Text contact requires transactional SMS consent", 422)


async def accept(data, submission_type, key, source, session):
    validate_channel_contract(data)
    if not key or len(key) > 255:
        raise DomainError(
            "IDEMPOTENCY_KEY_REQUIRED",
            "A valid Idempotency-Key is required",
            400,
        )
    return await PublicSubmissionService(session).accept(
        submission_type,
        data,
        key,
        source,
    )


@router.post(
    "/service-requests",
    response_model=SubmissionAccepted,
    status_code=status.HTTP_202_ACCEPTED,
)
async def service_request(
    data: ServiceRequestCreate,
    session: Annotated[AsyncSession, Depends(get_db)],
    source: Annotated[str, Depends(enforce_rate_limit)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
):
    return await accept(
        data,
        SubmissionType.SERVICE_REQUEST,
        idempotency_key,
        source,
        session,
    )


@router.post(
    "/contact",
    response_model=SubmissionAccepted,
    status_code=status.HTTP_202_ACCEPTED,
)
async def contact(
    data: ContactCreate,
    session: Annotated[AsyncSession, Depends(get_db)],
    source: Annotated[str, Depends(enforce_rate_limit)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
):
    return await accept(
        data,
        SubmissionType.CONTACT,
        idempotency_key,
        source,
        session,
    )


@router.post(
    "/provider-interest",
    response_model=SubmissionAccepted,
    status_code=status.HTTP_202_ACCEPTED,
)
async def provider_interest(
    data: ProviderInterestCreate,
    session: Annotated[AsyncSession, Depends(get_db)],
    source: Annotated[str, Depends(enforce_rate_limit)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
):
    return await accept(
        data,
        SubmissionType.PROVIDER_INTEREST,
        idempotency_key,
        source,
        session,
    )
