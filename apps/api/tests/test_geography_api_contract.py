import uuid

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.api.v1.admin_geography import _idempotency_key, _version
from app.core.errors import DomainError
from app.domains.geography.public_service import GeographyService
from app.domains.geography.schemas import (
    AddressValidationRequest,
    PostalCodeImportRequest,
    ServiceAreaCheckResult,
    ServiceZoneCreate,
    ServiceZoneSummary,
    ServiceZoneUpdate,
    normalize_postal_code,
)
from app.integrations.geocoding import FakeGeocodingAdapter, GeocodedAddress
from app.main import app


def test_geography_admin_routes_are_registered_in_openapi() -> None:
    # Admin zone/postal-code management is unconditional (matching admin_users.py
    # and provider_onboarding.admin_router), unlike the customer-facing
    # booking_geography routes below, which depend on geocoding.
    paths = app.openapi()["paths"]
    expected = {
        "/api/v1/admin/service-zones": {"get", "post"},
        "/api/v1/admin/service-zones/{service_area_id}": {
            "get",
            "patch",
            "delete",
        },
        "/api/v1/admin/service-zones/{service_area_id}/coverage": {"get"},
        "/api/v1/admin/postal-codes": {"get", "post"},
        "/api/v1/admin/postal-codes/{postal_code_id}": {
            "patch",
            "delete",
        },
        "/api/v1/admin/postal-codes/import": {"post"},
        "/api/v1/admin/postal-codes/imports/{import_id}": {"get"},
    }
    for path, methods in expected.items():
        assert methods <= set(paths[path])


def test_booking_geography_routes_are_gated_behind_geocoding_enabled() -> None:
    # Regression test: these three routes used to be mounted unconditionally,
    # bypassing the same settings.geocoding_enabled gate /addresses/validate
    # respects. geocoding_enabled defaults to False, so with default settings
    # none of them should be registered.
    from app.config import settings

    paths = app.openapi()["paths"]
    booking_geography_paths = {
        "/api/v1/booking/address/validate",
        "/api/v1/booking/service-area/check",
        "/api/v1/booking/timezone/resolve",
    }
    if settings.geocoding_enabled:
        assert booking_geography_paths <= set(paths)
    else:
        assert not booking_geography_paths & set(paths)


def test_admin_geography_is_deny_by_default() -> None:
    response = TestClient(app).get("/api/v1/admin/service-zones")
    assert response.status_code == 401


def test_zip_and_state_input_are_normalized_before_validation() -> None:
    request = AddressValidationRequest(
        address_line_1="123 Main St",
        city="Houston",
        state="tx",
        postal_code="770011234",
    )
    assert request.state == "TX"
    assert request.postal_code == "77001-1234"
    assert normalize_postal_code("77001") == "77001"
    with pytest.raises(ValidationError):
        AddressValidationRequest(
            address_line_1="123 Main St",
            city="Houston",
            state="Texas",
            postal_code="ABC12",
        )


def test_service_zone_schema_denies_server_owned_fields_and_bad_shapes() -> None:
    with pytest.raises(ValidationError):
        ServiceZoneCreate.model_validate(
            {
                "legal_entity_id": str(uuid.uuid4()),
                "name": "Unsafe",
                "state_code": "TX",
                "version": 99,
            }
        )
    with pytest.raises(ValidationError):
        ServiceZoneCreate(
            legal_entity_id=uuid.uuid4(),
            name="No geography",
        )
    with pytest.raises(ValidationError):
        ServiceZoneCreate(
            legal_entity_id=uuid.uuid4(),
            name="Radius without center",
            radius_miles=5,
        )
    with pytest.raises(ValidationError):
        ServiceZoneUpdate(
            clear_center=True,
            center_latitude=29.7,
            center_longitude=-95.3,
        )


def test_postal_import_denies_duplicate_rows() -> None:
    with pytest.raises(ValidationError):
        PostalCodeImportRequest.model_validate(
            {
                "service_area_id": str(uuid.uuid4()),
                "rows": [
                    {"postal_code": "77001"},
                    {"postal_code": "77001"},
                ],
            }
        )


def test_public_service_area_shape_cannot_expose_provider_candidates() -> None:
    zone = ServiceZoneSummary(
        id=uuid.uuid4(),
        name="Houston Central",
        emergency_enabled=False,
    )
    result = ServiceAreaCheckResult(covered=True, service_zone=zone)
    data = result.model_dump()
    assert "provider_id" not in data
    assert "professional_id" not in data
    assert "score" not in data
    with pytest.raises(ValidationError):
        ServiceAreaCheckResult.model_validate(
            {
                "covered": True,
                "service_zone": zone.model_dump(),
                "provider_id": str(uuid.uuid4()),
            }
        )


def test_address_locality_mismatch_is_rejected() -> None:
    command = AddressValidationRequest(
        address_line_1="123 Main St",
        city="Houston",
        state="TX",
        postal_code="77001",
    )
    with pytest.raises(DomainError) as exc_info:
        GeographyService._validate_input_match(
            command,
            city="Dallas",
            state_code="TX",
            postal_code="77001",
        )
    assert exc_info.value.code == "ADDRESS_INPUT_MISMATCH"
    assert exc_info.value.fields == {"mismatched_fields": ["city"]}


@pytest.mark.asyncio
async def test_fake_geography_adapter_is_deterministic_and_network_free() -> None:
    expected = GeocodedAddress(
        "123 Main St, Houston, TX 77001",
        "123 Main St",
        "Houston",
        "77001",
        "US",
        29.7604,
        -95.3698,
        "fake",
        timezone_name="America/Chicago",
        state_code="TX",
    )
    adapter = FakeGeocodingAdapter(expected)
    assert await adapter.geocode("anything") == expected
    assert (
        await adapter.resolve_timezone(expected.latitude, expected.longitude)
        == "America/Chicago"
    )


@pytest.mark.asyncio
async def test_public_address_workflow_rejects_incomplete_provider_evidence() -> None:
    incomplete = GeocodedAddress(
        "123 Main St",
        "123 Main St",
        "",
        "77001",
        "US",
        29.7604,
        -95.3698,
        "fake",
        confidence=1.0,
        state_code=None,
        timezone_name=None,
    )
    command = AddressValidationRequest(
        address_line_1="123 Main St",
        city="Houston",
        state="TX",
        postal_code="77001",
    )
    with pytest.raises(DomainError) as exc_info:
        await GeographyService(  # type: ignore[arg-type]
            None,
            provider=FakeGeocodingAdapter(incomplete),
        ).validate_address(command)
    assert exc_info.value.code == "ADDRESS_VALIDATION_INCOMPLETE"


def test_version_and_idempotency_headers_are_strict() -> None:
    assert _version('W/"7"') == 7
    assert _idempotency_key("postal-import:77001") == "postal-import:77001"
    with pytest.raises(DomainError):
        _version(None)
    with pytest.raises(DomainError):
        _version("*")
    with pytest.raises(DomainError):
        _idempotency_key("short")
