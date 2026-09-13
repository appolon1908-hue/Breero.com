import uuid
from typing import Any

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from app.domains.auth.models import User
from app.domains.booking.models import Address, Customer


async def customer_for(session: AsyncSession, user: User) -> Customer:
    customer = await session.scalar(select(Customer).where(Customer.user_id == user.id))
    if not customer:
        raise HTTPException(404, "Customer profile not found; verify your email to link it")
    return customer


async def owned_address(
    session: AsyncSession,
    customer: Customer,
    address_id: uuid.UUID,
) -> Address:
    address = await session.scalar(
        select(Address).where(Address.id == address_id, Address.customer_id == customer.id)
    )
    if not address:
        raise HTTPException(404, "Address not found")
    return address


async def paginate(
    session: AsyncSession,
    statement: Select[Any],
    count_statement: Select[Any],
    page: int,
    page_size: int,
) -> tuple[list[Any], int]:
    items = list(
        (
            await session.scalars(
                statement.offset((page - 1) * page_size).limit(page_size)
            )
        ).all()
    )
    total = int(await session.scalar(count_statement) or 0)
    return items, total
