import hashlib
import hmac
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rate_limit import rate_limit
from app.db.session import get_db
from app.domains.booking.models import Booking
from app.domains.booking.presenters import booking_to_create_response
from app.domains.booking.schemas import (
    BookingConfirmation,
    BookingCreateRequest,
    BookingCreateResponse,
)
from app.domains.booking.service import BookingService

router = APIRouter()

# Internal compatibility alias. New code should import the domain presenter.
to_response = booking_to_create_response


@router.post("", response_model=BookingCreateResponse, status_code=201)
async def create_booking(
    payload: BookingCreateRequest,
    idempotency_key: str = Header(min_length=8, max_length=128, alias="Idempotency-Key"),
    session: AsyncSession = Depends(get_db),
    _rate_limit: None = Depends(rate_limit("booking-create", 10, 60)),
) -> BookingCreateResponse:
    return booking_to_create_response(
        await BookingService(session).create(payload, idempotency_key)
    )


async def guest_booking(
    session: AsyncSession,
    booking_id: uuid.UUID,
    authorization: str,
) -> Booking:
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Guest confirmation token is required")
    token = authorization.removeprefix("Bearer ").strip()
    if len(token) < 32:
        raise HTTPException(401, "Invalid guest confirmation token")
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    booking = await session.get(Booking, booking_id)
    if (
        not booking
        or not hmac.compare_digest(booking.guest_confirmation_token_hash, token_hash)
        or booking.guest_confirmation_revoked_at is not None
        or booking.guest_confirmation_expires_at <= datetime.now(UTC)
    ):
        raise HTTPException(403, "Guest confirmation token is invalid or expired")
    return booking


@router.get("/{booking_id}/confirmation", response_model=BookingConfirmation)
async def booking_confirmation(
    booking_id: uuid.UUID,
    authorization: str = Header(alias="Authorization"),
    session: AsyncSession = Depends(get_db),
    _rate_limit: None = Depends(rate_limit("guest-booking-confirmation", 30, 60)),
) -> BookingConfirmation:
    booking = await guest_booking(session, booking_id, authorization)
    payment_status = "disabled"
    if booking.status.value == "CONFIRMED":
        next_action = "confirmed"
    elif booking.status.value == "PENDING_PROVIDER_CONFIRMATION":
        next_action = "await_provider_confirmation"
    elif booking.status.value in {"EXPIRED", "CANCELLED"}:
        next_action = "booking_unavailable"
    else:
        next_action = "await_operator_confirmation"
    return BookingConfirmation(
        booking_id=booking.id,
        reference=booking.reference,
        booking_status=booking.status,
        payment_status=payment_status,
        window_start=booking.window_start,
        window_end=booking.window_end,
        amount_minor=0,
        currency=booking.currency,
        next_action=next_action,
    )
