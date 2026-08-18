from fastapi import APIRouter

from app.api.v1 import (
    addresses,
    admin,
    admin_dispatch,
    auth,
    availability,
    bookings,
    compliance,
    customers,
    finance,
    integrations,
    jobs,
    operations,
    payments,
    provider,
    provider_leads,
    public_booking,
    public_forms,
    services,
    vendors,
)
from app.config import settings

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(services.router, prefix="/services", tags=["services"])
api_router.include_router(customers.router, prefix="/customer", tags=["customer"])
api_router.include_router(customers.router, prefix="/client", tags=["client"])
api_router.include_router(compliance.router, tags=["compliance"])
if settings.geocoding_enabled:
    api_router.include_router(addresses.router, prefix="/addresses", tags=["addresses"])
if settings.scheduling_enabled:
    api_router.include_router(availability.router, prefix="/availability", tags=["availability"])
    api_router.include_router(bookings.router, prefix="/bookings", tags=["bookings"])
api_router.include_router(public_booking.router, prefix="/booking", tags=["public-booking"])
if settings.payments_enabled and settings.stripe_enabled:
    api_router.include_router(payments.router, prefix="/payments", tags=["payments"])
    api_router.include_router(
        customers.payment_router, prefix="/customer", tags=["customer-payments"]
    )
api_router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
api_router.include_router(vendors.router, prefix="/vendors", tags=["vendors"])
api_router.include_router(provider.router, prefix="/provider", tags=["provider"])
api_router.include_router(operations.router, prefix="/operations", tags=["operations"])
api_router.include_router(admin_dispatch.router, prefix="/admin", tags=["admin-dispatch"])
api_router.include_router(admin.router, prefix="/admin", tags=["administration"])
if settings.payout_enabled:
    api_router.include_router(finance.router, prefix="/finance", tags=["finance"])
api_router.include_router(integrations.router, prefix="/integrations", tags=["integrations"])
api_router.include_router(public_forms.router, tags=["public-forms"])
if settings.paid_leads_enabled and settings.payments_enabled and settings.stripe_enabled:
    api_router.include_router(provider_leads.router, prefix="/provider/leads", tags=["provider-leads"])
