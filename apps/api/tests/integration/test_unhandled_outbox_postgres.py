import os
import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.config import settings
from app.domains.common.outbox import AuditLog, EventStatus, IntegrationEvent
from app.domains.common.outbox_service import OutboxService
from app.workers.tasks import deliver_outbox_event

pytestmark = pytest.mark.skipif(
    not os.getenv("DATABASE_URL", "").startswith("postgresql"), reason="requires isolated PostgreSQL",
)


async def test_unhandled_event_is_retained_then_explicitly_replayed():
    engine = create_async_engine(settings.database_url, poolclass=NullPool)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    event_id, actor_id = uuid.uuid4(), uuid.uuid4()
    middleware, email = AsyncMock(), AsyncMock()
    try:
        async with factory() as session:
            event = IntegrationEvent(
                id=event_id, aggregate_id=uuid.uuid4(), aggregate_type="job",
                event_type="job.completed", payload={"fixture": "retained"},
                status=EventStatus.PENDING, attempt_count=0,
                created_at=datetime(1970, 1, 1, tzinfo=UTC), next_attempt_at=datetime.now(UTC),
            )
            session.add(event)
            await session.commit()

            async def dispatch(item):
                return await deliver_outbox_event(item, session, middleware, email)

            outbox = OutboxService(session)
            assert await outbox.process(dispatch, limit=1) == 1
        # Verify durable failure using a fresh session, not only the identity map.
        async with factory() as session:
            event = await session.get(IntegrationEvent, event_id)
            assert event.status == EventStatus.FAILED_TERMINAL
            assert event.last_error_code == "UNHANDLED_EVENT_TYPE"
            assert event.attempt_count == 1
            assert event.claim_token is None and event.lease_expires_at is None
            assert event.payload == {"fixture": "retained"}
            assert event.external_record_id is None
            assert middleware.mock_calls == email.mock_calls == []
            outbox = OutboxService(session)
            await outbox.retry(event_id, actor_id)
            delivered = []

            async def approved_test_handler(item):
                delivered.append(item.id)

            assert await outbox.process(approved_test_handler, limit=1) == 1
            await session.refresh(event)
            assert event.status == EventStatus.DELIVERED
            assert delivered == [event_id]
            audit = await session.scalar(select(AuditLog).where(
                AuditLog.resource_id == event_id, AuditLog.action == "integration.retry",
            ))
            assert audit.actor_id == actor_id
    finally:
        async with factory() as session:
            await session.execute(delete(AuditLog).where(AuditLog.resource_id == event_id))
            await session.execute(delete(IntegrationEvent).where(IntegrationEvent.id == event_id))
            await session.commit()
        await engine.dispose()
