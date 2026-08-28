import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.domains.auth.access_service import BRAND_KEY, AccessService
from app.domains.auth.dependencies import require_roles
from app.domains.auth.models import AccessRole, User, UserRole
from app.domains.booking.models import Customer
from app.domains.jobs.models import JobStatus
from app.domains.jobs.repository import JobRepository
from app.domains.jobs.schemas import (
    JobRead,
    TechnicianNoteRequest,
    TransitionRequest,
    WorkRequestCreate,
    WorkRequestDecision,
    WorkRequestRead,
)
from app.domains.jobs.service import JobService
from app.domains.workforce.models import Vendor, Worker

router = APIRouter()

PRIVILEGED_JOB_ROLES = {
    AccessRole.operations,
    AccessRole.ops_manager,
    AccessRole.admin,
    AccessRole.superadmin,
}


async def worker_for_user(session: AsyncSession, user_id: uuid.UUID) -> Worker:
    from fastapi import HTTPException

    worker = await session.scalar(select(Worker).where(Worker.user_id == user_id))
    if not worker:
        raise HTTPException(403, "Account is not linked to a worker")
    return worker


async def effective_roles(session: AsyncSession, user: User) -> set[AccessRole]:
    context = await AccessService(session).context(user, BRAND_KEY)
    return set(context.roles)


@router.get("", response_model=list[JobRead])
async def list_jobs(
    status: JobStatus | None = None,
    vendor_id: uuid.UUID | None = None,
    worker_id: uuid.UUID | None = None,
    limit: int = Query(100, ge=1, le=200),
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(UserRole.operations, UserRole.admin)),
):
    return await JobRepository(session).list(
        status=status, vendor_id=vendor_id, worker_id=worker_id, limit=limit
    )


@router.get("/{job_id}", response_model=JobRead)
async def get_job(
    job_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(
        require_roles(
            UserRole.operations, UserRole.admin, UserRole.vendor_admin, UserRole.technician
        )
    ),
):
    from fastapi import HTTPException

    job = await JobRepository(session).get(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    roles = await effective_roles(session, user)
    if not roles & PRIVILEGED_JOB_ROLES:
        if AccessRole.technician in roles:
            worker = await worker_for_user(session, user.id)
            if job.worker_id != worker.id:
                raise HTTPException(403, "Technician is not assigned to this job")
        elif AccessRole.vendor_admin in roles:
            vendor = await session.scalar(select(Vendor).where(Vendor.owner_user_id == user.id))
            if not vendor or job.vendor_id != vendor.id:
                raise HTTPException(403, "Job belongs to another vendor")
        else:
            raise HTTPException(403, "Insufficient permissions")
    return job


@router.post("/{job_id}/transition", response_model=JobRead)
async def transition_job(
    job_id: uuid.UUID,
    payload: TransitionRequest,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(UserRole.operations, UserRole.admin)),
):
    return await JobService(session).transition(
        job_id, payload.status, user.id, user.role.value, payload.reason
    )


@router.post("/{job_id}/technician/{command}", response_model=JobRead)
async def technician_command(
    job_id: uuid.UUID,
    command: str,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(UserRole.technician)),
):
    from fastapi import HTTPException

    worker = await worker_for_user(session, user.id)
    job = await JobRepository(session).get(job_id)
    if not job or job.worker_id != worker.id:
        raise HTTPException(403, "Technician is not assigned to this job")
    targets = {
        "en-route": JobStatus.EN_ROUTE,
        "arrive": JobStatus.ON_SITE,
        "diagnose": JobStatus.DIAGNOSING,
        "start": JobStatus.IN_PROGRESS,
    }
    if command not in targets:
        raise HTTPException(422, "Unknown technician command")
    return await JobService(session).transition(job_id, targets[command], user.id, "worker")


@router.post("/{job_id}/diagnostic", response_model=JobRead)
async def record_diagnostic(
    job_id: uuid.UUID,
    payload: TechnicianNoteRequest,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(UserRole.technician)),
):
    worker = await worker_for_user(session, user.id)
    return await JobService(session).technician_note_transition(
        job_id, worker.id, user.id, "diagnostic_notes", payload.notes, JobStatus.DIAGNOSING
    )


@router.post("/{job_id}/completion", response_model=JobRead)
async def complete_with_notes(
    job_id: uuid.UUID,
    payload: TechnicianNoteRequest,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(UserRole.technician)),
):
    worker = await worker_for_user(session, user.id)
    return await JobService(session).technician_note_transition(
        job_id, worker.id, user.id, "completion_notes", payload.notes, JobStatus.COMPLETED
    )


@router.post("/{job_id}/work-requests", response_model=WorkRequestRead, status_code=201)
async def create_work_request(
    job_id: uuid.UUID,
    payload: WorkRequestCreate,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(UserRole.technician)),
):
    worker = await worker_for_user(session, user.id)
    return await JobService(session).create_work_request(job_id, payload, worker.id)


@router.get("/{job_id}/work-requests", response_model=list[WorkRequestRead])
async def list_work_requests(
    job_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(
        require_roles(
            UserRole.operations,
            UserRole.admin,
            UserRole.vendor_admin,
            UserRole.technician,
            UserRole.customer,
        )
    ),
):
    from fastapi import HTTPException

    job = await JobRepository(session).get(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    roles = await effective_roles(session, user)
    if not roles & PRIVILEGED_JOB_ROLES:
        if AccessRole.customer in roles:
            customer = await session.scalar(select(Customer).where(Customer.user_id == user.id))
            if not customer or job.customer_id != customer.id:
                raise HTTPException(403, "Job belongs to another customer")
        elif AccessRole.technician in roles:
            worker = await worker_for_user(session, user.id)
            if job.worker_id != worker.id:
                raise HTTPException(403, "Technician is not assigned to this job")
        elif AccessRole.vendor_admin in roles:
            vendor = await session.scalar(select(Vendor).where(Vendor.owner_user_id == user.id))
            if not vendor or job.vendor_id != vendor.id:
                raise HTTPException(403, "Job belongs to another vendor")
        else:
            raise HTTPException(403, "Insufficient permissions")
    return await JobRepository(session).list_work_requests(job_id)


@router.post("/work-requests/{request_id}/decision", response_model=WorkRequestRead)
async def decide_work_request(
    request_id: uuid.UUID,
    payload: WorkRequestDecision,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(UserRole.customer)),
):
    from fastapi import HTTPException

    customer = await session.scalar(select(Customer).where(Customer.user_id == user.id))
    if not customer:
        raise HTTPException(403, "Account is not linked to a customer")
    return await JobService(session).decide_work_request(request_id, payload.approve, customer.id)


@router.post("/work-requests/{request_id}/review", response_model=WorkRequestRead)
async def review_work_request(
    request_id: uuid.UUID,
    payload: WorkRequestDecision,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(UserRole.operations, UserRole.admin)),
):
    return await JobService(session).review_work_request(request_id, payload.approve)
