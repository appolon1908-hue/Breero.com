import asyncio
import functools
import time
from collections.abc import Callable
from datetime import UTC, datetime
from typing import ParamSpec, TypeVar

import redis
import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.metrics import HEARTBEAT_TTL_SECONDS, heartbeat_key
from app.db.session import WorkerSessionLocal
from app.domains.booking.models import EXPIRING_BOOKING_STATUSES, Booking, BookingStatus
from app.domains.common.outbox_service import OutboxService
from app.domains.finance.service import FinanceService
from app.domains.public_submissions.models import DownstreamStatus, PublicSubmission
from app.domains.tenant_email.delivery import TenantEmailDeliveryService
from app.integrations.email import EmailAdapter
from app.integrations.middleware import MiddlewareAdapter
from app.workers.celery_app import celery_app

logger = structlog.get_logger()
P = ParamSpec("P")
R = TypeVar("R")


def heartbeat(task_name: str) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Stamp Redis after a periodic task succeeds.

    This is what makes a missing Celery beat container detectable. The worker and the
    API are separate containers, so the signal has to live somewhere both can reach;
    the API reads these keys back on every /metrics scrape.

    Only success stamps. A task that raises leaves the previous timestamp in place and
    lets its age keep climbing, which is the behaviour an alert needs -- a failing task
    must not look alive.

    A heartbeat write must never fail the task that did the real work, so a Redis
    error here is logged and swallowed.
    """

    def decorate(function: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(function)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            result = function(*args, **kwargs)
            try:
                client = redis.from_url(
                    settings.redis_url, socket_connect_timeout=1, socket_timeout=1
                )
                try:
                    client.set(
                        heartbeat_key(task_name), repr(time.time()), ex=HEARTBEAT_TTL_SECONDS
                    )
                finally:
                    client.close()
            except redis.RedisError as exc:
                logger.warning(
                    "heartbeat_write_failed", task=task_name, error=type(exc).__name__
                )
            return result

        return wrapper

    return decorate


async def expire_booking_holds(session: AsyncSession, *, now: datetime) -> int:
    """Expire only currently expirable booking states at or before ``now``.

    Capacity queries independently ignore expired holds by ``expires_at`` so delayed
    worker execution cannot consume capacity. This cleanup is intentionally idempotent:
    once a booking becomes ``EXPIRED`` it is no longer selected on later runs.
    """
    rows = list(
        (
            await session.scalars(
                select(Booking)
                .where(
                    Booking.status.in_(EXPIRING_BOOKING_STATUSES),
                    Booking.expires_at <= now,
                )
                .with_for_update(skip_locked=True)
            )
        ).all()
    )
    for booking in rows:
        booking.status = BookingStatus.EXPIRED
    await session.commit()
    return len(rows)


@celery_app.task(name="app.workers.tasks.expire_bookings")
@heartbeat("expire_bookings")
def expire_bookings() -> int:
    async def run() -> int:
        async with WorkerSessionLocal() as session:
            return await expire_booking_holds(session, now=datetime.now(UTC))

    return asyncio.run(run())


@celery_app.task(
    name="app.workers.tasks.publish_outbox",
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=5,
)
@heartbeat("publish_outbox")
def publish_outbox() -> int:
    async def run() -> int:
        async with WorkerSessionLocal() as session:
            adapter = MiddlewareAdapter()
            email = EmailAdapter()
            tenant_email = TenantEmailDeliveryService(session)
            notification_events = {
                "email_verification_requested",
                "password_reset_requested",
                "password_changed",
                "payment_captured",
                "refund_created",
            }

            async def deliver(event):
                if event.aggregate_type == "email_message" and event.event_type == "email.message.queued":
                    return await tenant_email.deliver(event)
                if event.event_type in notification_events:
                    await email.send(event.event_type, event.payload)
                    return None
                if event.event_type.startswith("breero."):
                    result = await adapter.deliver(event)
                    if event.aggregate_type == "public_submission":
                        submission = await session.get(PublicSubmission, event.aggregate_id)
                        if submission:
                            submission.downstream_status = DownstreamStatus.DELIVERED
                    return result
                return None

            outbox = OutboxService(session)
            if settings.middleware_enabled:
                await outbox.activate_pending_configuration()
            else:
                await outbox.park_unconfigured()
            if settings.email_enabled and settings.transactional_email_mode != "disabled":
                await outbox.activate_pending_configuration(
                    event_prefix="email.message.", aggregate_type="email_message"
                )
            else:
                await outbox.park_unconfigured(
                    event_prefix="email.message.", aggregate_type="email_message"
                )
            return await outbox.process(deliver)

    return asyncio.run(run())


@celery_app.task(name="app.workers.tasks.release_earnings")
@heartbeat("release_earnings")
def release_earnings() -> int:
    async def run() -> int:
        async with WorkerSessionLocal() as session:
            return await FinanceService(session).release_eligible()

    return asyncio.run(run())


@celery_app.task(name="app.workers.tasks.generate_weekly_payout_candidates")
@heartbeat("generate_weekly_payout_candidates")
def generate_weekly_payout_candidates() -> str:
    if not settings.payout_enabled:
        return "disabled"

    async def run() -> str:
        async with WorkerSessionLocal() as session:
            try:
                batch = await FinanceService(session).create_batch("USD")
                return str(batch.id)
            except Exception as exc:
                if getattr(exc, "status_code", None) == 409:
                    return "no_candidates"
                raise

    return asyncio.run(run())
