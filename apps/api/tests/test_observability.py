import time
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from prometheus_client import generate_latest

from app.config import settings
from app.core import metrics
from app.domains.common import observability
from app.domains.common.outbox import EventStatus
from app.main import UNMATCHED_ROUTE, app


def _rendered() -> str:
    return generate_latest(metrics.build_registry()).decode()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


# --------------------------------------------------------------------------
# The scrape endpoint itself
# --------------------------------------------------------------------------


def test_metrics_endpoint_is_served_when_enabled(client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr(settings, "metrics_enabled", True)
    monkeypatch.setattr(settings, "metrics_token", "")
    with patch.object(observability, "collect_database_metrics", AsyncMock()), patch.object(
        observability, "collect_scheduler_metrics", AsyncMock()
    ):
        response = client.get("/metrics")
    assert response.status_code == 200
    assert "breero_http_requests_total" in response.text


def test_metrics_endpoint_is_absent_when_disabled(client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr(settings, "metrics_enabled", False)
    assert client.get("/metrics").status_code == 404


def test_metrics_endpoint_requires_the_token_when_configured(
    client: TestClient, monkeypatch
) -> None:
    monkeypatch.setattr(settings, "metrics_enabled", True)
    monkeypatch.setattr(settings, "metrics_token", "scrape-secret-token")

    assert client.get("/metrics").status_code == 401
    assert client.get("/metrics", headers={"Authorization": "Bearer wrong"}).status_code == 401

    with patch.object(observability, "collect_database_metrics", AsyncMock()), patch.object(
        observability, "collect_scheduler_metrics", AsyncMock()
    ):
        ok = client.get("/metrics", headers={"Authorization": "Bearer scrape-secret-token"})
    assert ok.status_code == 200


def test_scrape_survives_a_database_failure(client: TestClient, monkeypatch) -> None:
    # Prometheus marks a target down on a failed scrape, which would hide the request
    # metrics that are still perfectly good.
    monkeypatch.setattr(settings, "metrics_enabled", True)
    monkeypatch.setattr(settings, "metrics_token", "")
    failing = AsyncMock(side_effect=OSError("postgres is unreachable"))
    with patch.object(observability, "collect_database_metrics", failing), patch.object(
        observability, "collect_scheduler_metrics", AsyncMock()
    ):
        response = client.get("/metrics")
    assert response.status_code == 200
    assert "breero_http_requests_total" in response.text


# --------------------------------------------------------------------------
# Request instrumentation
# --------------------------------------------------------------------------


def test_requests_are_counted_by_route_template(client: TestClient) -> None:
    client.get("/health")
    rendered = _rendered()
    assert 'breero_http_requests_total{method="GET",route="/health",status="200"}' in rendered


def test_unmatched_paths_share_one_label(client: TestClient) -> None:
    # A series per 404 path is how a scrape target becomes a cardinality incident.
    client.get("/wp-login.php")
    client.get("/another-probe-path")
    rendered = _rendered()
    assert f'route="{UNMATCHED_ROUTE}"' in rendered
    assert "wp-login" not in rendered


def test_in_flight_gauge_returns_to_zero(client: TestClient) -> None:
    client.get("/health")
    client.get("/health/live")
    samples = [
        sample.value
        for metric in metrics.build_registry().collect()
        if metric.name == "breero_http_requests_in_flight"
        for sample in metric.samples
    ]
    assert samples and all(value == 0 for value in samples)


# --------------------------------------------------------------------------
# Domain gauges
# --------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_database_metrics_report_every_status_including_zero() -> None:
    # A series that vanishes when a queue drains breaks absence-based alerting.
    now = datetime.now(UTC)
    session = AsyncMock()
    session.execute = AsyncMock(
        side_effect=[
            MagicMock(),  # SET LOCAL statement_timeout
            MagicMock(all=MagicMock(return_value=[(EventStatus.PENDING, 3)])),
            MagicMock(all=MagicMock(return_value=[])),
        ]
    )
    session.scalar = AsyncMock(side_effect=[now - timedelta(seconds=90), 4])

    await observability.collect_database_metrics(session, now=now)

    rendered = _rendered()
    assert 'breero_outbox_events{status="PENDING"} 3.0' in rendered
    assert 'breero_outbox_events{status="DELIVERED"} 0.0' in rendered
    assert "breero_outbox_oldest_undelivered_age_seconds 90.0" in rendered
    assert "breero_booking_holds_overdue 4.0" in rendered


@pytest.mark.asyncio
async def test_oldest_age_is_zero_when_the_outbox_is_empty() -> None:
    session = AsyncMock()
    session.execute = AsyncMock(
        side_effect=[MagicMock(), MagicMock(all=MagicMock(return_value=[])), MagicMock(all=MagicMock(return_value=[]))]
    )
    session.scalar = AsyncMock(side_effect=[None, 0])
    await observability.collect_database_metrics(session)
    assert "breero_outbox_oldest_undelivered_age_seconds 0.0" in _rendered()


# --------------------------------------------------------------------------
# Scheduler heartbeat — the signal that catches a missing beat container
# --------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_a_scheduler_that_never_ran_reports_zero() -> None:
    """The exact failure mode of a production topology with no beat service."""
    client = AsyncMock()
    client.mget = AsyncMock(return_value=[None] * len(observability.PERIODIC_TASKS))
    with patch.object(observability.redis, "from_url", return_value=client):
        await observability.collect_scheduler_metrics(now=1_000_000.0)

    rendered = _rendered()
    assert (
        'breero_scheduled_task_last_success_timestamp_seconds{task="publish_outbox"} 0.0'
        in rendered
    )
    # -1 distinguishes "never ran" from "ran a moment ago", which a plain 0 would not.
    assert 'breero_scheduled_task_last_success_age_seconds{task="publish_outbox"} -1.0' in rendered


@pytest.mark.asyncio
async def test_heartbeat_age_is_measured_from_the_stamp() -> None:
    stamped = 1_000_000.0
    client = AsyncMock()
    client.mget = AsyncMock(
        return_value=[repr(stamped)] + [None] * (len(observability.PERIODIC_TASKS) - 1)
    )
    with patch.object(observability.redis, "from_url", return_value=client):
        await observability.collect_scheduler_metrics(now=stamped + 45.0)
    assert 'breero_scheduled_task_last_success_age_seconds{task="publish_outbox"} 45.0' in _rendered()


@pytest.mark.asyncio
async def test_scheduler_metrics_degrade_when_redis_is_down() -> None:
    client = AsyncMock()
    client.mget = AsyncMock(side_effect=observability.redis.RedisError("down"))
    with patch.object(observability.redis, "from_url", return_value=client):
        await observability.collect_scheduler_metrics()  # must not raise


def test_every_scheduled_task_has_a_heartbeat() -> None:
    """Each beat-scheduled task must stamp, or its absence is invisible."""
    from app.workers.celery_app import celery_app

    scheduled = {
        entry["task"].rsplit(".", 1)[-1] for entry in celery_app.conf.beat_schedule.values()
    }
    assert scheduled == set(observability.PERIODIC_TASKS)


def test_heartbeat_decorator_stamps_only_after_success() -> None:
    from app.workers import tasks

    fake = MagicMock()
    with patch.object(tasks.redis, "from_url", return_value=fake):

        @tasks.heartbeat("publish_outbox")
        def succeeds() -> int:
            return 7

        assert succeeds() == 7
        assert fake.set.call_count == 1
        key, value = fake.set.call_args.args
        assert key == "breero:heartbeat:publish_outbox"
        assert float(value) == pytest.approx(time.time(), abs=10)

        fake.reset_mock()

        @tasks.heartbeat("publish_outbox")
        def fails() -> int:
            raise RuntimeError("delivery failed")

        with pytest.raises(RuntimeError):
            fails()
        # A failing task must not look alive.
        assert fake.set.call_count == 0


def test_heartbeat_write_failure_never_fails_the_task() -> None:
    from app.workers import tasks

    with patch.object(tasks.redis, "from_url", side_effect=tasks.redis.RedisError("down")):

        @tasks.heartbeat("expire_bookings")
        def work() -> str:
            return "done"

        assert work() == "done"


# ---------------------------------------------------------------------------
# Reconciliation guard (OBS-02)
#
# Two observability implementations existed on separate branches and three metric
# names collided. prometheus_client raises "Duplicated timeseries in
# CollectorRegistry" at import when that happens, so merging both would have been a
# hard startup crash rather than a merge conflict anyone would notice in review.
# ---------------------------------------------------------------------------


def test_metric_names_are_defined_exactly_once() -> None:
    import ast
    from pathlib import Path

    api_root = Path(__file__).resolve().parents[1]
    seen: dict[str, str] = {}
    duplicates: list[str] = []
    for path in sorted((api_root / "app").rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id in {"Counter", "Gauge", "Histogram", "Summary"}
                and node.args
                and isinstance(node.args[0], ast.Constant)
                and isinstance(node.args[0].value, str)
            ):
                name = node.args[0].value
                where = f"{path.relative_to(api_root)}:{node.lineno}"
                if name in seen:
                    duplicates.append(f"{name} defined at {seen[name]} and {where}")
                seen[name] = where
    assert duplicates == [], duplicates


def test_the_reconciled_metric_set_is_complete() -> None:
    """Both implementations' series survive the reconciliation."""
    from app.core import metrics as m

    # Contributed by be/analytics-observability-v1.
    assert m.DEPENDENCY_UP is not None
    assert m.WORKER_HEARTBEAT_AGE is not None
    # Contributed by this branch.
    assert m.SCHEDULED_TASK_LAST_SUCCESS is not None
    assert m.BOOKING_HOLDS_OVERDUE is not None
    assert m.PAYMENTS_BY_STATUS is not None
    assert m.REQUESTS_IN_FLIGHT is not None


def test_route_labels_are_bounded() -> None:
    from app.core.metrics import UNMATCHED_ROUTE, safe_route

    assert safe_route("/api/v1/bookings/{booking_id}") == "/api/v1/bookings/{booking_id}"
    assert safe_route(None) == UNMATCHED_ROUTE
    assert safe_route("") == UNMATCHED_ROUTE
    # Anything that is not a route template collapses rather than minting a series.
    assert safe_route("/api/v1/x?q=" + "a" * 400) == UNMATCHED_ROUTE
    assert safe_route("/api/v1/\nheader-injection") == UNMATCHED_ROUTE


def test_dependency_gauge_records_both_states() -> None:
    from prometheus_client import generate_latest

    from app.core import metrics as m

    m.record_dependency("postgres", True)
    m.record_dependency("redis", False)
    rendered = generate_latest(m.build_registry()).decode()
    assert 'breero_dependency_up{dependency="postgres"} 1.0' in rendered
    assert 'breero_dependency_up{dependency="redis"} 0.0' in rendered
