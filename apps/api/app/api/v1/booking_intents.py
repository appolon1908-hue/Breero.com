import uuid
from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, Header, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.errors import DomainError
from app.core.rate_limit import rate_limit
from app.db.session import get_db
from app.domains.booking.presenters import booking_to_create_response
from app.domains.booking.schemas import BookingCreateResponse
from app.domains.booking_intents.schemas import (
    BookingIntentCreate,
    BookingIntentRead,
    BookingIntentSubmitRequest,
    BookingIntentUpdate,
)
from app.domains.booking_intents.service import BOOKING_INTENT_TTL, BookingIntentService

router = APIRouter()
BOOKING_SESSION_COOKIE = "breero_booking_session"


def _session_id(raw: str | None, *, create: bool) -> uuid.UUID:
    if raw:
        try:
            return uuid.UUID(raw)
        except ValueError:
            if not create:
                raise DomainError(
                    "BOOKING_INTENT_NOT_FOUND",
                    "Booking intent not found.",
                    404,
                ) from None
    if create:
        return uuid.uuid4()
    raise DomainError(
        "BOOKING_INTENT_NOT_FOUND",
        "Booking intent not found.",
        404,
    )


def _set_session_cookie(response: Response, session_id: uuid.UUID) -> None:
    response.set_cookie(
        BOOKING_SESSION_COOKIE,
        str(session_id),
        max_age=int(BOOKING_INTENT_TTL.total_seconds()),
        httponly=True,
        secure=settings.app_env.lower() in {"staging", "production"},
        samesite="lax",
        path="/api/v1/booking",
    )


def _version(if_match: str | None) -> int:
    if if_match is None:
        raise DomainError(
            "PRECONDITION_REQUIRED",
            "If-Match is required for booking-intent changes.",
            428,
        )
    value = if_match.strip()
    if value.startswith("W/"):
        value = value[2:].strip()
    value = value.strip('"')
    if not value.isdigit() or int(value) < 1:
        raise DomainError(
            "INVALID_IF_MATCH",
            "If-Match must contain the current booking-intent version.",
            400,
        )
    return int(value)


def _etag(response: Response, version: int) -> None:
    response.headers["ETag"] = f'"{version}"'


@router.post(
    "/intents",
    response_model=BookingIntentRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_booking_intent(
    command: BookingIntentCreate,
    response: Response,
    session: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[None, Depends(rate_limit("booking-intent-create", 30, 60))],
    booking_session: Annotated[str | None, Cookie(alias=BOOKING_SESSION_COOKIE)] = None,
) -> BookingIntentRead:
    session_id = _session_id(booking_session, create=True)
    intent = await BookingIntentService(session).create(command, session_id)
    _set_session_cookie(response, session_id)
    _etag(response, intent.version)
    return BookingIntentRead.model_validate(intent)


@router.get("/intents/{intent_id}", response_model=BookingIntentRead)
async def get_booking_intent(
    intent_id: uuid.UUID,
    response: Response,
    session: Annotated[AsyncSession, Depends(get_db)],
    booking_session: Annotated[str | None, Cookie(alias=BOOKING_SESSION_COOKIE)] = None,
) -> BookingIntentRead:
    session_id = _session_id(booking_session, create=False)
    intent = await BookingIntentService(session).get(intent_id, session_id)
    _etag(response, intent.version)
    return BookingIntentRead.model_validate(intent)


@router.patch("/intents/{intent_id}", response_model=BookingIntentRead)
async def update_booking_intent(
    intent_id: uuid.UUID,
    command: BookingIntentUpdate,
    response: Response,
    session: Annotated[AsyncSession, Depends(get_db)],
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
    booking_session: Annotated[str | None, Cookie(alias=BOOKING_SESSION_COOKIE)] = None,
) -> BookingIntentRead:
    session_id = _session_id(booking_session, create=False)
    intent = await BookingIntentService(session).update(
        intent_id,
        session_id,
        command,
        expected_version=_version(if_match),
    )
    _etag(response, intent.version)
    return BookingIntentRead.model_validate(intent)


@router.delete(
    "/intents/{intent_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def abandon_booking_intent(
    intent_id: uuid.UUID,
    response: Response,
    session: Annotated[AsyncSession, Depends(get_db)],
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
    booking_session: Annotated[str | None, Cookie(alias=BOOKING_SESSION_COOKIE)] = None,
) -> None:
    session_id = _session_id(booking_session, create=False)
    await BookingIntentService(session).abandon(
        intent_id,
        session_id,
        expected_version=_version(if_match),
    )
    response.delete_cookie(BOOKING_SESSION_COOKIE, path="/api/v1/booking")


@router.post(
    "/intents/{intent_id}/submit",
    response_model=BookingCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def submit_booking_intent(
    intent_id: uuid.UUID,
    payload: BookingIntentSubmitRequest,
    session: Annotated[AsyncSession, Depends(get_db)],
    idempotency_key: Annotated[str, Header(min_length=8, max_length=128, alias="Idempotency-Key")],
    _: Annotated[None, Depends(rate_limit("booking-intent-submit", 10, 60))],
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
    booking_session: Annotated[str | None, Cookie(alias=BOOKING_SESSION_COOKIE)] = None,
) -> BookingCreateResponse:
    session_id = _session_id(booking_session, create=False)
    booking = await BookingIntentService(session).submit(
        intent_id,
        session_id,
        payload.customer,
        payload.answers,
        expected_version=_version(if_match),
        idempotency_key=idempotency_key,
    )
    return booking_to_create_response(booking)
