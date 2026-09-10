import uuid
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

from app.api.v1 import customers
from app.api.v1.customer.router import payment_router, router
from app.domains.booking.models import BookingStatus
from app.domains.booking.presenters import (
    booking_to_create_response,
    booking_to_response,
)
from app.main import app


def test_legacy_customer_module_is_a_compatibility_facade() -> None:
    assert customers.router is router
    assert customers.payment_router is payment_router


def test_customer_routes_remain_registered_after_module_split() -> None:
    paths = app.openapi()["paths"]
    expected = {
        "/api/v1/customer/profile": {"get", "patch"},
        "/api/v1/customer/addresses": {"get", "post"},
        "/api/v1/customer/addresses/{address_id}": {"patch", "delete"},
        "/api/v1/customer/bookings": {"get"},
        "/api/v1/customer/bookings/{booking_id}": {"get"},
        "/api/v1/customer/bookings/{booking_id}/cancel": {"post"},
        "/api/v1/customer/quotes": {"get"},
        "/api/v1/customer/quotes/{quote_id}": {"get"},
        "/api/v1/customer/quotes/{quote_id}/decision": {"post"},
    }
    for path, methods in expected.items():
        assert methods <= set(paths[path])


def test_customer_implementation_no_longer_imports_a_sibling_api_module() -> None:
    api_root = Path(__file__).resolve().parents[1] / "app" / "api" / "v1"
    source = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (api_root / "customer").glob("*.py")
    )
    assert "from app.api.v1.bookings import" not in source


def test_customer_monolith_is_reduced_to_a_small_facade() -> None:
    path = Path(__file__).resolve().parents[1] / "app" / "api" / "v1" / "customers.py"
    assert len(path.read_text(encoding="utf-8").splitlines()) <= 12


def test_customer_booking_views_do_not_expose_creation_credentials() -> None:
    booking = SimpleNamespace(
        id=uuid.uuid4(),
        reference="BR-TEST",
        status=BookingStatus.CONFIRMED,
        total_amount=Decimal("100.00"),
        currency="USD",
        window_start=datetime.now(UTC),
        window_end=datetime.now(UTC),
        guest_confirmation_token="one-time-secret",
    )

    customer_view = booking_to_response(booking)
    create_view = booking_to_create_response(booking)

    assert "guest_confirmation_token" not in customer_view.model_dump()
    assert create_view.guest_confirmation_token == "one-time-secret"
