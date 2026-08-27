import uuid

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.auth.models import User, UserRole
from app.domains.booking.models import Customer
from app.domains.jobs.models import Job
from app.domains.workforce.models import Vendor, Worker


async def worker_for_user(session: AsyncSession, user_id: uuid.UUID) -> Worker:
    worker = await session.scalar(select(Worker).where(Worker.user_id == user_id))
    if not worker:
        raise HTTPException(403, "Account is not linked to a worker")
    return worker


async def customer_for_user(session: AsyncSession, user_id: uuid.UUID) -> Customer:
    customer = await session.scalar(select(Customer).where(Customer.user_id == user_id))
    if not customer:
        raise HTTPException(403, "Account is not linked to a customer")
    return customer


async def vendor_for_user(session: AsyncSession, user_id: uuid.UUID) -> Vendor:
    vendor = await session.scalar(select(Vendor).where(Vendor.owner_user_id == user_id))
    if not vendor:
        raise HTTPException(403, "Account is not linked to a vendor")
    return vendor


async def ensure_job_access(
    session: AsyncSession,
    user: User,
    job: Job,
) -> None:
    if user.role == UserRole.technician:
        worker = await worker_for_user(session, user.id)
        if job.worker_id != worker.id:
            raise HTTPException(403, "Technician is not assigned to this job")
    elif user.role == UserRole.vendor_admin:
        vendor = await vendor_for_user(session, user.id)
        if job.vendor_id != vendor.id:
            raise HTTPException(403, "Job belongs to another vendor")
    elif user.role == UserRole.customer:
        customer = await customer_for_user(session, user.id)
        if job.customer_id != customer.id:
            raise HTTPException(403, "Job belongs to another customer")
