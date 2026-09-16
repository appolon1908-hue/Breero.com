from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.customer.dependencies import customer_for
from app.api.v1.customer.schemas import ProfilePatch, ProfileRead
from app.db.session import get_db
from app.domains.auth.dependencies import current_user
from app.domains.auth.models import User

router = APIRouter()


@router.get("/profile", response_model=ProfileRead)
async def profile(
    user: Annotated[User, Depends(current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> ProfileRead:
    customer = await customer_for(session, user)
    return ProfileRead(
        id=customer.id,
        email=user.email,
        full_name=user.full_name,
        phone=customer.phone,
        email_verified=user.email_verified,
    )


@router.patch("/profile", response_model=ProfileRead)
async def update_profile(
    data: ProfilePatch,
    user: Annotated[User, Depends(current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> ProfileRead:
    customer = await customer_for(session, user)
    if data.full_name is not None:
        user.full_name = data.full_name.strip()
        parts = user.full_name.split(maxsplit=1)
        customer.first_name = parts[0]
        customer.last_name = parts[1] if len(parts) > 1 else ""
    if data.phone is not None:
        customer.phone = data.phone

    await session.commit()
    return ProfileRead(
        id=customer.id,
        email=user.email,
        full_name=user.full_name,
        phone=customer.phone,
        email_verified=user.email_verified,
    )
