"""Customer-facing API modules.

The legacy ``app.api.v1.customers`` module remains a compatibility facade while
the implementation is split by resource.
"""

from app.api.v1.customer.router import payment_router, router

__all__ = ["router", "payment_router"]
