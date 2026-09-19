import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.customer.dependencies import customer_for, paginate
from app.api.v1.customer.schemas import CustomerPaymentRead, Page
from app.db.session import get_db
from app.domains.auth.dependencies import current_user
from app.domains.auth.models import User
from app.domains.booking.models import Booking
from app.domains.jobs.models import Job, WorkRequest
from app.domains.payments.models import Payment, Refund
from app.domains.payments.schemas import PaymentView

router = APIRouter()


def owned_payments_query(customer_id: uuid.UUID):
    return (
        select(Payment)
        .outerjoin(Booking, Booking.id == Payment.booking_id)
        .outerjoin(WorkRequest, WorkRequest.id == Payment.quote_id)
        .outerjoin(Job, Job.id == WorkRequest.job_id)
        .where((Booking.customer_id == customer_id) | (Job.customer_id == customer_id))
    )


async def refunded_amount(session: AsyncSession, payment_id: uuid.UUID) -> int:
    return int(
        await session.scalar(
            select(func.coalesce(func.sum(Refund.amount_minor), 0)).where(
                Refund.payment_id == payment_id
            )
        )
        or 0
    )


@router.get("/payments", response_model=Page)
async def payments(
    user: Annotated[User, Depends(current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> Page:
    customer = await customer_for(session, user)
    owned = owned_payments_query(customer.id)
    items, total = await paginate(
        session,
        owned.order_by(Payment.created_at.desc()),
        select(func.count()).select_from(owned.subquery()),
        page,
        page_size,
    )
    result = []
    for item in items:
        result.append(
            {
                "id": str(item.id),
                "payment_purpose": item.payment_purpose.value,
                "status": item.status.value,
                "amount_minor": item.amount_minor,
                "captured_amount_minor": item.captured_amount_minor,
                "refunded_amount_minor": await refunded_amount(session, item.id),
                "currency": item.currency,
                "created_at": item.created_at.isoformat(),
            }
        )
    return Page(items=result, total=total, page=page, page_size=page_size)


@router.get("/payments/{payment_id}", response_model=CustomerPaymentRead)
async def payment(
    payment_id: uuid.UUID,
    user: Annotated[User, Depends(current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> CustomerPaymentRead:
    customer = await customer_for(session, user)
    item = await session.scalar(
        owned_payments_query(customer.id).where(Payment.id == payment_id)
    )
    if not item:
        raise HTTPException(404, "Payment not found")

    view = PaymentView.model_validate(item).model_dump()
    return CustomerPaymentRead(
        **view,
        refunded_amount_minor=await refunded_amount(session, item.id),
    )
