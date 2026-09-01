"""Operational facts worth alerting on, read fresh at scrape time.

These are deliberately the questions that could not be answered without a psql
session: is the outbox draining, is capacity being released, is the scheduler alive.

Every query is an aggregate over an indexed column and runs under a short statement
timeout -- a scrape must never be the thing that holds a connection open.
"""

import time
from datetime import UTC, datetime

import redis.asyncio as redis
import structlog
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.metrics import (
    BOOKING_HOLDS_OVERDUE,
    HEARTBEAT_PREFIX,
    OUTBOX_EVENTS,
    OUTBOX_OLDEST_AGE,
    PAYMENTS_BY_STATUS,
    SCHEDULED_TASK_AGE,
    SCHEDULED_TASK_LAST_SUCCESS,
)
from app.domains.booking.models import EXPIRING_BOOKING_STATUSES, Booking
from app.domains.common.outbox import EventStatus, IntegrationEvent
from app.domains.payments.models import Payment

logger = structlog.get_logger()

SCRAPE_STATEMENT_TIMEOUT_MS = 2_000

# An event in one of these states is finished with, successfully or not. Everything
# else is still owed a delivery attempt and therefore counts toward backlog age.
TERMINAL_EVENT_STATUSES = (
    EventStatus.DELIVERED,
    EventStatus.FAILED_TERMINAL,
    EventStatus.FAILED,
    EventStatus.DEAD_LETTER,
)

# Named so an alert can assert each one individually; a missing series is the signal.
PERIODIC_TASKS = (
    "publish_outbox",
    "expire_bookings",
    "release_earnings",
    "generate_weekly_payout_candidates",
)


async def collect_database_metrics(session: AsyncSession, *, now: datetime | None = None) -> None:
    moment = now or datetime.now(UTC)
    await session.execute(text(f"SET LOCAL statement_timeout = {SCRAPE_STATEMENT_TIMEOUT_MS}"))

    rows = (
        await session.execute(
            select(IntegrationEvent.status, func.count()).group_by(IntegrationEvent.status)
        )
    ).all()
    depths: dict[EventStatus, int] = {status: count for status, count in rows}
    # Report every status, including the ones at zero. A series that simply vanishes
    # when a queue drains makes `rate()` and absence-based alerts unreliable.
    for status in EventStatus:
        value = depths.get(status, 0)
        OUTBOX_EVENTS.labels(status=status.value).set(value)

    oldest = await session.scalar(
        select(func.min(IntegrationEvent.created_at)).where(
            IntegrationEvent.status.not_in(TERMINAL_EVENT_STATUSES)
        )
    )
    OUTBOX_OLDEST_AGE.set((moment - oldest).total_seconds() if oldest else 0.0)

    overdue = await session.scalar(
        select(func.count())
        .select_from(Booking)
        .where(Booking.status.in_(EXPIRING_BOOKING_STATUSES), Booking.expires_at <= moment)
    )
    BOOKING_HOLDS_OVERDUE.set(int(overdue or 0))

    payment_rows = (
        await session.execute(select(Payment.status, func.count()).group_by(Payment.status))
    ).all()
    for payment_status, count in payment_rows:
        label = getattr(payment_status, "value", str(payment_status))
        PAYMENTS_BY_STATUS.labels(status=label).set(count)


async def collect_scheduler_metrics(
    *, now: float | None = None, client: redis.Redis | None = None
) -> None:
    """Read the heartbeats the Celery workers stamp into Redis.

    A task that has never run leaves no key. That is reported as an explicit zero
    rather than a missing series so `... == 0` alerts on a scheduler that never
    started, which is exactly the failure a missing beat container produces.
    """
    moment = now if now is not None else time.time()
    # The pooled client is injected by the scrape handler. Building one here would
    # reintroduce a connect-and-teardown on every scrape interval.
    owned = client is None
    connection = client if client is not None else redis.from_url(
        settings.redis_url, socket_connect_timeout=1, socket_timeout=1
    )
    try:
        values = await connection.mget([f"{HEARTBEAT_PREFIX}{task}" for task in PERIODIC_TASKS])
    except redis.RedisError as exc:
        # A scrape must degrade, never fail: losing Redis should raise a Redis alert,
        # not blank out every other metric on the page.
        logger.warning("scheduler_metrics_unavailable", error=type(exc).__name__)
        return
    finally:
        if owned:
            await connection.aclose()

    for task, raw in zip(PERIODIC_TASKS, values, strict=True):
        stamp = float(raw) if raw is not None else 0.0
        SCHEDULED_TASK_LAST_SUCCESS.labels(task=task).set(stamp)
        SCHEDULED_TASK_AGE.labels(task=task).set(moment - stamp if stamp else -1.0)
