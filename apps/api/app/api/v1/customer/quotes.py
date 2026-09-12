import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.customer.dependencies import customer_for, paginate
from app.api.v1.customer.schemas import Page
from app.db.session import get_db
from app.domains.auth.dependencies import current_user
from app.domains.auth.models import User
from app.domains.jobs.models import Job, WorkRequest
from app.domains.jobs.schemas import WorkRequestDecision, WorkRequestRead
from app.domains.jobs.service import JobService

router = APIRouter()


@router.get("/quotes", response_model=Page)
async def quotes(
    user: Annotated[User, Depends(current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> Page:
    customer = await customer_for(session, user)
    base = (
        select(WorkRequest)
        .join(Job, Job.id == WorkRequest.job_id)
        .where(Job.customer_id == customer.id)
    )
    items, total = await paginate(
        session,
        base.order_by(WorkRequest.created_at.desc()),
        select(func.count())
        .select_from(WorkRequest)
        .join(Job)
        .where(Job.customer_id == customer.id),
        page,
        page_size,
    )
    return Page(
        items=[WorkRequestRead.model_validate(item).model_dump() for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/quotes/{quote_id}", response_model=WorkRequestRead)
async def quote(
    quote_id: uuid.UUID,
    user: Annotated[User, Depends(current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> WorkRequest:
    customer = await customer_for(session, user)
    item = await session.scalar(
        select(WorkRequest)
        .join(Job)
        .where(WorkRequest.id == quote_id, Job.customer_id == customer.id)
    )
    if not item:
        raise HTTPException(404, "Quote not found")
    return item


@router.post("/quotes/{quote_id}/decision", response_model=WorkRequestRead)
async def decide_quote(
    quote_id: uuid.UUID,
    payload: WorkRequestDecision,
    user: Annotated[User, Depends(current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> WorkRequest:
    customer = await customer_for(session, user)
    return await JobService(session).decide_work_request(
        quote_id,
        payload.approve,
        customer.id,
    )
