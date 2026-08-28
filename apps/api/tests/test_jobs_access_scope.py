import uuid
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.api.v1 import jobs
from app.domains.auth.models import AccessRole, User, UserRole


def make_user(role: UserRole = UserRole.customer) -> User:
    return User(
        id=uuid.uuid4(),
        email=f"{uuid.uuid4().hex}@example.com",
        password_hash="disabled",
        full_name="Job Viewer",
        role=role,
        is_active=True,
        email_verified=True,
    )


def make_job(**overrides) -> SimpleNamespace:
    defaults = dict(id=uuid.uuid4(), customer_id=uuid.uuid4(), vendor_id=uuid.uuid4(), worker_id=uuid.uuid4())
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


class FakeJobRepository:
    def __init__(self, job) -> None:
        self.job = job

    def __call__(self, _session):
        return self

    async def get(self, _job_id):
        return self.job

    async def list_work_requests(self, _job_id):
        return []


class ScalarSession:
    def __init__(self, value=None) -> None:
        self.value = value

    async def scalar(self, _query):
        return self.value


def patch_roles(monkeypatch, roles: list[AccessRole]) -> None:
    async def fake_effective_roles(_session, _user):
        return set(roles)

    monkeypatch.setattr(jobs, "effective_roles", fake_effective_roles)


@pytest.mark.asyncio
async def test_get_job_denies_vendor_scoped_rbac_grant_for_a_different_vendor(monkeypatch) -> None:
    # Regression test: a user's legacy `user.role` stays UserRole.customer while an
    # admin grants them AccessRole.vendor_admin through the new RBAC endpoint (the
    # decoupling this PR introduces on purpose). Before the fix, get_job's ownership
    # check branched on the legacy role, matched neither `technician` nor
    # `vendor_admin`, and returned the job with no ownership check at all.
    user = make_user(UserRole.customer)
    job = make_job()
    other_vendor = SimpleNamespace(id=uuid.uuid4())

    monkeypatch.setattr(jobs, "JobRepository", FakeJobRepository(job))
    patch_roles(monkeypatch, [AccessRole.vendor_admin])

    with pytest.raises(HTTPException) as exc_info:
        await jobs.get_job(job.id, ScalarSession(other_vendor), user)

    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_get_job_allows_vendor_scoped_rbac_grant_for_the_owning_vendor(monkeypatch) -> None:
    user = make_user(UserRole.customer)
    job = make_job()
    owning_vendor = SimpleNamespace(id=job.vendor_id)

    monkeypatch.setattr(jobs, "JobRepository", FakeJobRepository(job))
    patch_roles(monkeypatch, [AccessRole.vendor_admin])

    result = await jobs.get_job(job.id, ScalarSession(owning_vendor), user)

    assert result is job


@pytest.mark.asyncio
async def test_get_job_denies_when_effective_roles_grant_nothing_recognized(monkeypatch) -> None:
    # Defensive fail-closed branch: require_roles already filters callers, but if
    # effective roles ever come back without any of the roles this route knows how
    # to scope, deny instead of silently returning the job unrestricted.
    user = make_user(UserRole.customer)
    job = make_job()

    monkeypatch.setattr(jobs, "JobRepository", FakeJobRepository(job))
    patch_roles(monkeypatch, [])

    with pytest.raises(HTTPException) as exc_info:
        await jobs.get_job(job.id, ScalarSession(None), user)

    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_list_work_requests_denies_customer_scoped_rbac_grant_for_a_different_customer(
    monkeypatch,
) -> None:
    user = make_user(UserRole.technician)
    job = make_job()
    other_customer = SimpleNamespace(id=uuid.uuid4())

    monkeypatch.setattr(jobs, "JobRepository", FakeJobRepository(job))
    patch_roles(monkeypatch, [AccessRole.customer])

    with pytest.raises(HTTPException) as exc_info:
        await jobs.list_work_requests(job.id, ScalarSession(other_customer), user)

    assert exc_info.value.status_code == 403
