"""Compatibility facade for the split customer API package.

New customer endpoints belong in ``app.api.v1.customer`` by resource. Keeping
this facade preserves existing imports while the monolith is removed.
"""

from app.api.v1.customer.bookings import cancel_booking
from app.api.v1.customer.router import payment_router, router

__all__ = ["router", "payment_router", "cancel_booking"]
