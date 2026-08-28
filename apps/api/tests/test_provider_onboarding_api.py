import json
import uuid

import pytest
from pydantic import ValidationError

from app.domains.auth.models import User, UserRole
from app.domains.common.outbox import EventStatus
from app.domains.workforce.models import (
    ProviderApplication,
    ProviderApplicationStatus,
    Vendor,
)
from app.domains.workforce.onboarding_service import ProviderOnboardingService
from app.domains.workforce.schemas import (
    ProviderApplicationDecision,
    ProviderOnboardingUpdate,
)
from app.main import app


def make_user(role: UserRole = UserRole.vendor_admin) -> User:
    return User(
        id=uuid.uuid4(),
        email=f"{uuid.uuid4().hex}@example.com",
        password_hash="disabled",
        full_name="Provider Owner",
        role=role,
        is_active=True,
        email_verified=True,
    )


class SequentialScalarSession:
    def __init__(self, values: list) -> None:
        self._values = list(values)
        self.added: list = []
        self.commits = 0

    async def scalar(self, _query):
        return self._values.pop(0)

    def add(self, value) -> None:
        self.added.append(value)

    async def commit(self) -> None:
        self.commits += 1

    async def refresh(self, _obj) -> None:
        return None


def test_provider_onboarding_routes_are_registered() -> None:
    paths = app.openapi()["paths"]
    required = {
        "/api/v1/auth/register/provider": {"post"},
        "/api/v1/provider/profile": {"get", "patch"},
        "/api/v1/provider/onboarding": {"get", "patch"},
        "/api/v1/provider/onboarding/submit": {"post"},
        "/api/v1/admin/provider-applications": {"get"},
        "/api/v1/admin/provider-applications/{application_id}": {"get"},
        "/api/v1/admin/provider-applications/{application_id}/approve": {"post"},
        "/api/v1/admin/provider-applications/{application_id}/reject": {"post"},
        (
            "/api/v1/admin/provider-applications/"
            "{application_id}/request-information"
        ): {"post"},
    }
    for path, methods in required.items():
        assert methods <= set(paths[path])


def test_onboarding_patch_rejects_status_and_vendor_mass_assignment() -> None:
    with pytest.raises(ValidationError):
        ProviderOnboardingUpdate.model_validate({"status": "APPROVED"})
    with pytest.raises(ValidationError):
        ProviderOnboardingUpdate.model_validate(
            {"vendor_id": str(uuid.uuid4())}
        )


def test_postal_codes_validate_zip_and_zip4() -> None:
    payload = ProviderOnboardingUpdate(
        postal_codes=["02108", "02108-1234", "02108"]
    )
    assert payload.postal_codes == ["02108", "02108-1234"]
    with pytest.raises(ValidationError):
        ProviderOnboardingUpdate(postal_codes=["ABC12"])
    with pytest.raises(ValidationError):
        ProviderOnboardingUpdate(postal_codes=["021081234"])


def test_submission_requires_every_mission_domain() -> None:
    application = ProviderApplication(
        id=uuid.uuid4(),
        vendor_id=uuid.uuid4(),
        status=ProviderApplicationStatus.DRAFT,
        identity={"legal_name": "Owner"},
        business={},
        contact_details={},
        services=[],
        skills=[],
        service_areas=[],
        postal_codes=[],
        availability={},
        capacity={},
        licenses=[],
        insurance=[],
        compliance_documents=[],
        version=1,
    )
    assert ProviderOnboardingService.missing_submission_fields(application) == [
        "business",
        "contact_details",
        "services",
        "skills",
        "service_areas",
        "postal_codes",
        "availability",
        "capacity",
        "licenses",
        "insurance",
        "compliance_documents",
    ]


def test_complete_application_has_no_missing_submission_domains() -> None:
    application = ProviderApplication(
        id=uuid.uuid4(),
        vendor_id=uuid.uuid4(),
        status=ProviderApplicationStatus.DRAFT,
        identity={"owner": "Owner"},
        business={"legal_name": "Provider LLC"},
        contact_details={"phone": "+15551234567"},
        services=[str(uuid.uuid4())],
        skills=["plumbing"],
        service_areas=[{"type": "ZIP", "value": "02108"}],
        postal_codes=["02108"],
        availability={"monday": [["07:00", "19:00"]]},
        capacity={"daily_jobs": 4, "daily_minutes": 480},
        licenses=[{"type": "trade", "jurisdiction": "MA"}],
        insurance=[{"type": "general_liability"}],
        compliance_documents=[str(uuid.uuid4())],
        version=1,
    )
    assert not ProviderOnboardingService.missing_submission_fields(application)


def test_provider_application_decision_requires_reason() -> None:
    with pytest.raises(ValidationError):
        ProviderApplicationDecision(reason="no")


@pytest.mark.asyncio
async def test_update_onboarding_serializes_uuid_list_fields_to_strings() -> None:
    # Regression test: `services`/`compliance_documents` are typed list[uuid.UUID] on
    # the request schema, but the ORM column is a plain JSONB list with no custom
    # json_serializer on the engine. Writing raw UUID objects onto it crashes at
    # commit with "TypeError: Object of type UUID is not JSON serializable".
    vendor = Vendor(id=uuid.uuid4())
    application = ProviderApplication(
        id=uuid.uuid4(),
        vendor_id=vendor.id,
        status=ProviderApplicationStatus.DRAFT,
        version=1,
    )
    session = SequentialScalarSession([vendor, application])
    service = ProviderOnboardingService(session)  # type: ignore[arg-type]

    service_id = uuid.uuid4()
    document_id = uuid.uuid4()
    result = await service.update_onboarding(
        make_user(),
        ProviderOnboardingUpdate(services=[service_id], compliance_documents=[document_id]),
    )

    assert result.services == [str(service_id)]
    assert result.compliance_documents == [str(document_id)]
    # Would raise TypeError before the fix if UUID objects had leaked through.
    json.dumps(result.services)
    json.dumps(result.compliance_documents)
    assert session.commits == 1


def test_provider_application_events_are_pending_not_pending_configuration() -> None:
    # Regression test: PENDING_CONFIGURATION is only ever promoted to PENDING by
    # OutboxService.activate_pending_configuration(aggregate_type="public_submission")
    # (see app/workers/tasks.py), which never matches aggregate_type="provider_application".
    # These events have no external-adapter dependency to gate on, so they must be
    # created PENDING directly or they are silently stuck forever.
    added: list = []

    class RecordingSession:
        def add(self, value) -> None:
            added.append(value)

    application = ProviderApplication(
        id=uuid.uuid4(),
        vendor_id=uuid.uuid4(),
        status=ProviderApplicationStatus.DRAFT,
        version=1,
    )
    service = ProviderOnboardingService(RecordingSession())  # type: ignore[arg-type]

    service._event(application, "provider_application_submitted", {})

    assert len(added) == 1
    assert added[0].status == EventStatus.PENDING
