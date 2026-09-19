from app.domains.booking.models import Booking
from app.domains.booking.schemas import BookingCreateResponse, BookingResponse


def booking_to_response(booking: Booking) -> BookingResponse:
    """Map a booking without exposing the creation-only guest credential."""

    return BookingResponse(
        id=booking.id,
        reference=booking.reference,
        status=booking.status,
        total_amount=booking.total_amount,
        currency=booking.currency,
        window_start=booking.window_start,
        window_end=booking.window_end,
        payment_required=False,
    )


def booking_to_create_response(booking: Booking) -> BookingCreateResponse:
    """Map a newly created booking and include its one-time guest credential."""

    return BookingCreateResponse(
        **booking_to_response(booking).model_dump(),
        guest_confirmation_token=getattr(booking, "guest_confirmation_token", None),
    )
