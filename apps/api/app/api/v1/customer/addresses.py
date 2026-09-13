import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from geoalchemy2.elements import WKTElement
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.customer.dependencies import customer_for, owned_address
from app.api.v1.customer.schemas import AddressInput, AddressRead
from app.db.session import get_db
from app.domains.auth.dependencies import current_user
from app.domains.auth.models import User
from app.domains.booking.models import Address, Booking

router = APIRouter()


@router.get("/addresses", response_model=list[AddressRead])
async def addresses(
    user: Annotated[User, Depends(current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> list[Address]:
    customer = await customer_for(session, user)
    return list(
        (
            await session.scalars(
                select(Address)
                .where(Address.customer_id == customer.id)
                .order_by(Address.created_at.desc())
            )
        ).all()
    )


@router.post("/addresses", response_model=AddressRead, status_code=201)
async def add_address(
    data: AddressInput,
    user: Annotated[User, Depends(current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> Address:
    customer = await customer_for(session, user)
    address = Address(
        customer_id=customer.id,
        formatted_address=f"{data.line1}, {data.postal_code} {data.city}",
        line1=data.line1,
        city=data.city,
        postal_code=data.postal_code,
        country_code=data.country_code.upper(),
        location=WKTElement(f"POINT({data.longitude} {data.latitude})", srid=4326),
        geocoding_provider="customer",
    )
    session.add(address)
    await session.commit()
    await session.refresh(address)
    return address


@router.patch("/addresses/{address_id}", response_model=AddressRead)
async def update_address(
    address_id: uuid.UUID,
    data: AddressInput,
    user: Annotated[User, Depends(current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> Address:
    customer = await customer_for(session, user)
    address = await owned_address(session, customer, address_id)
    for field in ("line1", "city", "postal_code"):
        setattr(address, field, getattr(data, field))
    address.country_code = data.country_code.upper()
    address.formatted_address = f"{data.line1}, {data.postal_code} {data.city}"
    address.location = WKTElement(f"POINT({data.longitude} {data.latitude})", srid=4326)
    await session.commit()
    return address


@router.delete("/addresses/{address_id}", status_code=204)
async def delete_address(
    address_id: uuid.UUID,
    user: Annotated[User, Depends(current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    customer = await customer_for(session, user)
    address = await owned_address(session, customer, address_id)
    in_use = await session.scalar(
        select(Booking.id).where(Booking.address_id == address.id).limit(1)
    )
    if in_use:
        raise HTTPException(409, "Address is referenced by a booking")
    await session.delete(address)
    await session.commit()
