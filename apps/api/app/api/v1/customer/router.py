from fastapi import APIRouter

from app.api.v1.customer.addresses import router as addresses_router
from app.api.v1.customer.bookings import router as bookings_router
from app.api.v1.customer.payments import router as payments_router
from app.api.v1.customer.profile import router as profile_router
from app.api.v1.customer.quotes import router as quotes_router

router = APIRouter()
router.include_router(profile_router)
router.include_router(addresses_router)
router.include_router(bookings_router)
router.include_router(quotes_router)

payment_router = APIRouter()
payment_router.include_router(payments_router)
