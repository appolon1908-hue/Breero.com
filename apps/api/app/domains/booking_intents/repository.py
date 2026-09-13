import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import BookingIntent


class BookingIntentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, intent: BookingIntent) -> BookingIntent:
        self.session.add(intent)
        await self.session.flush()
        return intent

    async def owned(
        self,
        intent_id: uuid.UUID,
        anonymous_session_id: uuid.UUID,
        *,
        lock: bool = False,
    ) -> BookingIntent | None:
        query = select(BookingIntent).where(
            BookingIntent.id == intent_id,
            BookingIntent.anonymous_session_id == anonymous_session_id,
        )
        if lock:
            query = query.with_for_update()
        return await self.session.scalar(query)
