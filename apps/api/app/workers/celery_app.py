from celery import Celery
from celery.signals import heartbeat_sent, worker_ready

from app.config import settings
from app.observability import configure_worker_observability, record_worker_heartbeat

configure_worker_observability()


@heartbeat_sent.connect
@worker_ready.connect
def _worker_heartbeat(**_kwargs) -> None:
    record_worker_heartbeat()


celery_app = Celery("breero", broker=settings.redis_url, backend=settings.redis_url)
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_acks_late=True,
    task_track_started=True,
    worker_prefetch_multiplier=1,
    worker_send_task_events=True,
    task_send_sent_event=True,
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
