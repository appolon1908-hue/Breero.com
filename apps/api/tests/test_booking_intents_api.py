import uuid

import pytest
from pydantic import ValidationError

from app.api.v1.booking_intents import _session_id, _version
from app.core.errors import DomainError
from app.domains.booking_intents.models import BookingIntentStatus
from app.domains.booking_intents.schemas import BookingIntentUpdate, SlotSelection
from app.main import app


def test_booking_intent_routes_are_registered() -> None:
    paths = app.openapi()["paths"]
    expected = {
        "/api/v1/booking/intents": {"post"},
        "/api/v1/booking/intents/{intent_id}": {"get", "patch", "delete"},
        "/api/v1/booking/intents/{intent_id}/submit": {"post"},
    }
    for path, methods in expected.items():
        assert methods <= set(paths[path])


def test_booking_intent_status_contract_is_separate_from_booking_status() -> None:
    assert {status.value for status in BookingIntentStatus} == {
        "DRAFT",
        "ADDRESS_VALIDATED",
        "COVERAGE_CONFIRMED",
        "AVAILABILITY_FOUND",
        "SUBMITTED",
        "EXPIRED",
    }


def test_patch_denies_server_owned_fields() -> None:
    for field in ("status", "public_reference", "anonymous_session_id", "version"):
        with pytest.raises(ValidationError):
            BookingIntentUpdate.model_validate({field: "forbidden"})


def test_public_slot_shape_cannot_leak_provider_data() -> None:
    selection = SlotSelection(
        slot_token="opaque-slot-token-12345",
        start_local="09:00",
        end_local="11:00",
    )
    assert selection.start_local == "09:00"
    with pytest.raises(ValidationError):
        SlotSelection.model_validate(
            {
                "slot_token": "opaque-slot-token-12345",
                "start_local": "09:00",
                "end_local": "11:00",
                "provider_id": str(uuid.uuid4()),
            }
        )
    with pytest.raises(ValidationError):
        SlotSelection(
            slot_token="opaque-slot-token-12345",
            start_local="11:00",
            end_local="09:00",
        )


def test_if_match_requires_a_positive_version() -> None:
    assert _version('"3"') == 3
    assert _version('W/"4"') == 4
    with pytest.raises(DomainError):
        _version(None)
    with pytest.raises(DomainError):
        _version("*")


def test_invalid_session_cookie_is_not_accepted_for_existing_intent() -> None:
    session_id = uuid.uuid4()
    assert _session_id(str(session_id), create=False) == session_id
    with pytest.raises(DomainError):
        _session_id("not-a-uuid", create=False)


def test_timezone_id_accepts_slash_less_iana_zones() -> None:
    # Regression test: the pattern used to require a "/", rejecting valid zones
    # like "UTC" -- the exact fallback value the service itself uses internally.
    for zone in ("UTC", "GMT", "EST5EDT", "America/Los_Angeles"):
        assert BookingIntentUpdate(timezone_id=zone).timezone_id == zone
    with pytest.raises(ValidationError):
        BookingIntentUpdate(timezone_id="not a zone!")
