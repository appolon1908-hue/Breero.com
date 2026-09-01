"""Prometheus instrumentation.

Two kinds of series live here and they are collected differently.

*Request* counters and histograms are incremented per worker process. The API runs
under ``uvicorn --workers 2``, so a scrape reaches one worker at random; without
aggregation Prometheus would see two independent counters interleaved and read the
difference as repeated resets. ``prometheus_client``'s multiprocess mode fixes that by
having every worker write to a shared directory that the scrape reads back. It needs
``PROMETHEUS_MULTIPROC_DIR`` to be writable, which is why it points at ``/tmp`` -- the
production container runs ``read_only: true`` with only ``/tmp`` mounted read-write.

*Domain* gauges are absolute facts about the system ("how many events are waiting"),
not per-worker tallies. Summing them across workers would multiply them by the worker
count, so they are declared ``multiprocess_mode="livemostrecent"``: the scrape reports
the value most recently written by any process, which is the true value because each
one is read straight from Postgres or Redis at scrape time.
"""

import os
import re
import time
from pathlib import Path

from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram, multiprocess

MULTIPROC_ENV = "PROMETHEUS_MULTIPROC_DIR"

# Requests that never reach a route share one label rather than minting a series
# per path, which is the classic way a scrape target becomes a cardinality incident.
UNMATCHED_ROUTE = "<unmatched>"

# Buckets tuned for an API whose slowest normal work is a PostGIS coverage lookup.
# The 0.005-0.05 range is dense because that is where a healthy read should land, and
# the tail is long enough to show a payment provider round trip without clipping.
LATENCY_BUCKETS = (0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)

REQUESTS = Counter(
    "breero_http_requests_total",
    "HTTP requests completed, by route template and status.",
    ("method", "route", "status"),
)
REQUEST_DURATION = Histogram(
    "breero_http_request_duration_seconds",
    "HTTP request duration by route template.",
    ("method", "route"),
    buckets=LATENCY_BUCKETS,
)
REQUESTS_IN_FLIGHT = Gauge(
    "breero_http_requests_in_flight",
    "Requests currently being served.",
    multiprocess_mode="livesum",
)

DEPENDENCY_UP = Gauge(
    "breero_dependency_up",
    "Whether a required dependency answered its last health probe.",
    ("dependency",),
    # `max` rather than `livemostrecent`: readiness is probed per worker, and one
    # healthy worker is enough to say the dependency itself is reachable.
    multiprocess_mode="max",
)
WORKER_HEARTBEAT_AGE = Gauge(
    "breero_worker_heartbeat_age_seconds",
    "Seconds since any Celery worker last reported itself alive. Distinct from the "
    "per-task scheduler heartbeats: a worker can be running while beat is dead, and "
    "beat can be scheduling into a queue no worker is draining.",
    multiprocess_mode="livemostrecent",
)
OUTBOX_EVENTS = Gauge(
    "breero_outbox_events",
    "Integration events in the outbox, by status.",
    ("status",),
    multiprocess_mode="livemostrecent",
)
OUTBOX_OLDEST_AGE = Gauge(
    "breero_outbox_oldest_undelivered_age_seconds",
    "Age of the oldest event still waiting for delivery. Grows without bound if the "
    "scheduler is not running.",
    multiprocess_mode="livemostrecent",
)
BOOKING_HOLDS_OVERDUE = Gauge(
    "breero_booking_holds_overdue",
    "Bookings past expires_at that the expiry task has not yet released. Capacity "
    "queries already ignore these, but a rising number means the scheduler is stalled.",
    multiprocess_mode="livemostrecent",
)
PAYMENTS_BY_STATUS = Gauge(
    "breero_payments",
    "Payments by status.",
    ("status",),
    multiprocess_mode="livemostrecent",
)
SCHEDULED_TASK_LAST_SUCCESS = Gauge(
    "breero_scheduled_task_last_success_timestamp_seconds",
    "Unix time each periodic task last completed. Absent or stale means Celery beat "
    "is not running -- the failure this metric exists to catch.",
    ("task",),
    multiprocess_mode="livemostrecent",
)
SCHEDULED_TASK_AGE = Gauge(
    "breero_scheduled_task_last_success_age_seconds",
    "Seconds since each periodic task last completed.",
    ("task",),
    multiprocess_mode="livemostrecent",
)

# Redis keys the workers stamp and the API reads back. The worker and the API are
# separate containers, so the heartbeat cannot be an in-process gauge.
HEARTBEAT_PREFIX = "breero:heartbeat:"
# Written by every worker process, independently of which task ran.
WORKER_HEARTBEAT_KEY = "breero:heartbeat:worker"
HEARTBEAT_TTL_SECONDS = 7 * 24 * 3600


def heartbeat_key(task_name: str) -> str:
    return f"{HEARTBEAT_PREFIX}{task_name.rsplit('.', 1)[-1]}"


def enable_multiprocess_mode() -> None:
    """Point prometheus_client at a writable shared directory before workers fork.

    Safe to call when the variable is already set by the environment; the directory is
    created if missing so a fresh container does not need an init step.
    """
    directory = os.environ.get(MULTIPROC_ENV)
    if not directory:
        return
    Path(directory).mkdir(parents=True, exist_ok=True)


def build_registry() -> CollectorRegistry:
    """Return the registry a scrape should render.

    In multiprocess mode this is a fresh registry fed by every worker's shared files.
    Outside it (tests, a single-process run) the default registry already holds
    everything, so it is returned as-is.
    """
    if not os.environ.get(MULTIPROC_ENV):
        from prometheus_client import REGISTRY

        return REGISTRY
    registry = CollectorRegistry()
    multiprocess.MultiProcessCollector(registry)
    return registry


# A second line of defence on cardinality. Even if a route template were ever to
# carry an interpolated value, anything outside this shape collapses to the shared
# unmatched label rather than minting a series.
SAFE_ROUTE = re.compile(r"^/[A-Za-z0-9_{}./:-]{0,255}$")


def safe_route(route: str | None) -> str:
    if route and SAFE_ROUTE.fullmatch(route):
        return route
    return UNMATCHED_ROUTE


def record_request(method: str, route: str, status: int, duration_seconds: float) -> None:
    label = safe_route(route)
    REQUESTS.labels(method=method, route=label, status=str(status)).inc()
    REQUEST_DURATION.labels(method=method, route=label).observe(duration_seconds)


def record_dependency(name: str, healthy: bool) -> None:
    DEPENDENCY_UP.labels(dependency=name).set(1 if healthy else 0)


def stamp_task_success(task_name: str, *, now: float | None = None) -> float:
    """Value a worker writes to Redis after a periodic task completes."""
    return now if now is not None else time.time()
