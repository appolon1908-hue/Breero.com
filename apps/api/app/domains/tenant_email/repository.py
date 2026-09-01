import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.common.outbox import IntegrationEvent

from .models import EmailCredential, EmailDomain, EmailMessage, EmailSender

OUTBOX_AGGREGATE_TYPE = "email_message"


class TenantEmailRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_domains(self) -> list[EmailDomain]:
        return list(await self.session.scalars(select(EmailDomain).order_by(EmailDomain.domain)))

    async def get_domain(self, domain_id: uuid.UUID) -> EmailDomain | None:
        return await self.session.get(EmailDomain, domain_id)

    async def list_senders(self) -> list[EmailSender]:
        return list(await self.session.scalars(select(EmailSender).order_by(EmailSender.created_at)))

    async def get_sender(self, sender_id: uuid.UUID) -> EmailSender | None:
        return await self.session.get(EmailSender, sender_id)

    async def list_credentials(self) -> list[EmailCredential]:
        return list(
            await self.session.scalars(select(EmailCredential).order_by(EmailCredential.created_at))
        )

    async def get_credential(self, credential_id: uuid.UUID) -> EmailCredential | None:
        return await self.session.get(EmailCredential, credential_id)

    async def get_message(self, message_id: uuid.UUID) -> EmailMessage | None:
        return await self.session.get(EmailMessage, message_id)

    async def message_by_idempotency_key(self, key: str) -> EmailMessage | None:
        return await self.session.scalar(
            select(EmailMessage).where(EmailMessage.idempotency_key == key)
        )

    async def outbox_page(
        self, vendor_ids: set[uuid.UUID] | None, limit: int
    ) -> list[tuple[IntegrationEvent, EmailMessage]]:
        """Return the newest outbox events, already narrowed to the caller's tenants.

        The vendor filter is applied in SQL before LIMIT on purpose: filtering after
        the fact would let another tenant's more recent events crowd this caller's own
        events out of the page, leaving them with an incomplete or empty outbox.
        ``None`` means unrestricted; an empty set means the caller can see nothing.
        """
        if vendor_ids is not None and not vendor_ids:
            return []
        query = (
            select(IntegrationEvent, EmailMessage)
            .join(EmailMessage, EmailMessage.id == IntegrationEvent.aggregate_id)
            .where(IntegrationEvent.aggregate_type == OUTBOX_AGGREGATE_TYPE)
        )
        if vendor_ids is not None:
            query = query.where(EmailMessage.vendor_id.in_(vendor_ids))
        rows = await self.session.execute(
            query.order_by(IntegrationEvent.created_at.desc()).limit(limit)
        )
        return [(event, message) for event, message in rows.all()]

    async def outbox_event(self, event_id: uuid.UUID) -> IntegrationEvent | None:
        event = await self.session.get(IntegrationEvent, event_id)
        if event is None or event.aggregate_type != OUTBOX_AGGREGATE_TYPE:
            return None
        return event
