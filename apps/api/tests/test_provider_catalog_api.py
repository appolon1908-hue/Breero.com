import uuid

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.api.v1.provider_catalog import _version
from app.core.errors import DomainError
from app.domains.provider_catalog.models import ApprovalStatus
from app.domains.provider_catalog.schemas import (
    ProviderServiceCreate,
    ProviderServiceUpdate,
    ProviderSkillCreate,
)
from app.main import app


def test_provider_catalog_routes_are_registered() -> None:
    paths = app.openapi()["paths"]
    expected = {
        "/api/v1/provider/services": {"get", "post"},
        "/api/v1/provider/services/{provider_service_id}": {
            "patch",
            "delete",
        },
        "/api/v1/provider/skills": {"get", "post"},
        "/api/v1/provider/skills/{provider_skill_id}": {"delete"},
    }
    for path, methods in expected.items():
        assert methods <= set(paths[path])


def test_provider_catalog_is_deny_by_default() -> None:
    client = TestClient(app)
    assert client.get("/api/v1/provider/services").status_code == 401
    assert client.get("/api/v1/provider/skills").status_code == 401


def test_provider_can_select_only_catalog_identifiers() -> None:
    service_id = uuid.uuid4()
    skill_id = uuid.uuid4()
    assert ProviderServiceCreate(service_id=service_id).service_id == service_id
    assert ProviderSkillCreate(skill_id=skill_id).skill_id == skill_id

    with pytest.raises(ValidationError):
        ProviderServiceCreate.model_validate(
            {
                "service_id": str(service_id),
                "service_name": "Provider invented service",
            }
        )
    with pytest.raises(ValidationError):
        ProviderSkillCreate.model_validate(
            {
                "skill_id": str(skill_id),
                "skill_name": "Provider invented qualification",
            }
        )


def test_provider_cannot_mass_assign_approval_or_vendor_scope() -> None:
    for payload in (
        {"active": True, "status": ApprovalStatus.APPROVED.value},
        {"active": True, "vendor_id": str(uuid.uuid4())},
        {"active": True, "reviewed_by": str(uuid.uuid4())},
    ):
        with pytest.raises(ValidationError):
            ProviderServiceUpdate.model_validate(payload)


def test_provider_catalog_patch_requires_a_field_and_valid_version() -> None:
    with pytest.raises(ValidationError):
        ProviderServiceUpdate()
    assert _version('W/"5"') == 5
    with pytest.raises(DomainError):
        _version(None)
    with pytest.raises(DomainError):
        _version("*")
