import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import ApiClient, ApiClientStatus, ApiKey, WebhookSubscription


class PartnerApiRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # -- clients -------------------------------------------------------------

    async def add_client(self, client: ApiClient) -> ApiClient:
        self.session.add(client)
        await self.session.flush()
        return client

    async def get_client(self, client_id: uuid.UUID) -> ApiClient | None:
        return await self.session.get(ApiClient, client_id)

    async def list_clients(self, limit: int, offset: int) -> list[ApiClient]:
        return list(
            await self.session.scalars(
                select(ApiClient).order_by(ApiClient.name).limit(limit).offset(offset)
            )
        )

    # -- keys ----------------------------------------------------------------

    async def add_key(self, key: ApiKey) -> ApiKey:
        self.session.add(key)
        await self.session.flush()
        return key

    async def key_by_hash(self, key_hash: str) -> ApiKey | None:
        """Look a key up by digest, never by secret.

        Indexed on `key_hash`, so verification is a single indexed lookup rather than
        a scan comparing every stored credential.
        """
        return await self.session.scalar(select(ApiKey).where(ApiKey.key_hash == key_hash))

    async def get_key(self, key_id: uuid.UUID) -> ApiKey | None:
        return await self.session.get(ApiKey, key_id)

    async def list_keys(self, client_id: uuid.UUID) -> list[ApiKey]:
        return list(
            await self.session.scalars(
                select(ApiKey).where(ApiKey.client_id == client_id).order_by(ApiKey.created_at)
            )
        )

    async def active_client_for_key(self, key: ApiKey) -> ApiClient | None:
        client = await self.session.get(ApiClient, key.client_id)
        if client is None or client.status is not ApiClientStatus.ACTIVE:
            return None
        return client

    # -- webhooks ------------------------------------------------------------

    async def add_subscription(self, subscription: WebhookSubscription) -> WebhookSubscription:
        self.session.add(subscription)
        await self.session.flush()
        return subscription

    async def get_subscription(self, subscription_id: uuid.UUID) -> WebhookSubscription | None:
        return await self.session.get(WebhookSubscription, subscription_id)

    async def list_subscriptions(self, client_id: uuid.UUID) -> list[WebhookSubscription]:
        return list(
            await self.session.scalars(
                select(WebhookSubscription)
                .where(WebhookSubscription.client_id == client_id)
                .order_by(WebhookSubscription.created_at)
            )
        )

    async def active_subscriptions_for(self, event_type: str) -> list[WebhookSubscription]:
        rows = await self.session.scalars(
            select(WebhookSubscription).where(WebhookSubscription.active.is_(True))
        )
        # Event-type filtering is done in Python: the list is per-client and short, and
        # a JSONB containment query here would be harder to read for no measurable gain.
        return [row for row in rows if event_type in (row.event_types or [])]

    async def touch_key(self, key: ApiKey, *, now: datetime | None = None) -> None:
        key.last_used_at = now or datetime.now(UTC)
