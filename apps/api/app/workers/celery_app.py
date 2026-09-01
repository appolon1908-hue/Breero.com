from celery import Celery
from celery.signals import worker_process_init

from app.config import settings
from app.core.tracing import configure_logging, configure_tracing

celery_app = Celery("breero", broker=settings.redis_url, backend=settings.redis_url)
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    timezone="UTC",
    beat_schedule={
        "publish-outbox": {"task": "app.workers.tasks.publish_outbox", "schedule": 10.0},
        "expire-bookings": {"task": "app.workers.tasks.expire_bookings", "schedule": 60.0},
        "release-earnings": {"task": "app.workers.tasks.release_earnings", "schedule": 3600.0},
        "weekly-payout-candidates": {
            "task": "app.workers.tasks.generate_weekly_payout_candidates",
            "schedule": 604800.0,
        },
    },
)
celery_app.autodiscover_tasks(["app.workers"])


@worker_process_init.connect
def _configure_worker_tracing(**_: object) -> None:
    """Instrument per forked worker process, not at import.

    Celery forks after the module is loaded, and a tracer provider created before the
    fork does not survive it intact -- the batch span processor's exporter thread is
    left behind in the parent.
    """
    configure_logging()
    configure_tracing()
